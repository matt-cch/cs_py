#!/usr/bin/env python3
r"""
workflow-git-deploy-full-poly.py — deploy-git-isolated Polyrepo 全链条部署 workflow
标签：py-tools
版本：v1.2.0（由 v1.1.1 升级）
v1.1.1→v1.2.0 更新意图：Step 8 upstream 重构为 `branch --set-upstream-to` 以彻底消除 PAT 持久化泄露；集成 `atomic-agent-preflight.py` LLM 探活预检；`_generate_ai_summary` 改为 Popen 实时透传；新增 diff 审计落盘。

  职责：纯编排器，支持单仓库与 polyrepo 两种场景的自动部署。
      工具链根固定为 Path.cwd()，--devroot 仅用于验证一致性。
      操作目标通过 --target 显式指定，必须传入（即使与 --devroot 相同）。

执行顺序：
  1. Step 0a: atomic-git-preflight-general（通用 git 环境验证，支持 --target）
  2. Step 0b: atomic-deploy-preflight（部署特有验证：PAT/分支/agent/git-security 审计）
  3. Step 0c: atomic-polyrepo-context-manifest（生成 PolyrepoContext manifest，记录 repo_url/branch 等）
  4. Step 4: git -C <target> add -A
  5. Step 4.5: git_security 扫描（target 仓库，工具链 git.exe）
  6. AI 摘要 + meta 生成（generate-ai-summary.py）
     6a. diff 审计落盘（--diff-output，原始 diff 持久化供事后分析）
     6b. Agent Preflight（atomic-agent-preflight.py，确认 LLM 可达后再进入长耗时生成）
     6c. LLM 语义摘要生成
  7. Step 5: git -C <target> commit
  8. 更新 meta commit hash
  9. Step 6-9: remote → push → upstream → issue sync
  10. Step 10: 获取 remote 最新 comment 落盘

安全与审计机制：
  - Step 4.5 对 staged 文件执行 git_security 安全扫描，发现敏感信息即阻断提交。
  - push / upstream 操作时通过环境变量阻断 GCM 弹窗（GCM_INTERACTIVE=0、GIT_TERMINAL_PROMPT=0）。
  - 支持分支保护检测：push 被远程拒绝时自动提示使用 feature 分支 + PR merge 流程。
  - PAT 从工具链根 .env 读取，不在代码或日志中暴露。

AI 集成：
  - 未传入 --message 时，自动从 staged 文件名生成 commit message（单文件 / 多文件 / 计数三种模式）。
  - Step 4 后调用 generate-ai-summary.py 生成 AI 语义摘要，注入部署 meta。
  - AI 摘要生成失败时自动终止并提示回滚（git reset HEAD）。

认证信息缓存：
  - Step 7 将 repo_url / PAT / username 缓存为模块变量，供 Step 8 upstream 设置复用，
    避免重复读取 .env 或 manifest。

审计产物与追踪路径（按执行顺序）：
  - Step 0c  PolyrepoContext manifest:
      `${devroot}/venv/tmp/polyrepo-context-wf-{timestamp}.json`
      记录 repo_url、branch、is_polyrepo、git_security 路径等运行时上下文。
  - Step 4.5 git_security 扫描:
      stdout 实时输出 violations 列表，不单独落盘；发现敏感信息即阻断提交。
  - Step 6a  diff 审计:
      `${devroot}/venv/tmp/diff-audit-for-ai-summary-{timestamp}.json`
      原始完整 diff + diff_stats（length_chars、line_count、is_truncated_for_prompt）。
      用于事后分析「diff 过大导致摘要异常」的根因。
  - Step 6b  Agent Preflight manifest:
      `${devroot}/venv/tmp/agent-preflight-for-ai-summary-{timestamp}.json`
      记录 LLM 探活结果（model、base_url、response_time_ms、response_preview、error）。
  - Step 6c  AI Summary 输出:
      `${devroot}/venv/tmp/ai-summary-{timestamp}.json`
      生成的 ai_summary、changed_files、commit_message 等。
  - Step 5   Workflow meta:
      `${devroot}/venv/tmp/workflow-meta-{timestamp}.json`
      部署实时配置：commit_message、categories、ai_summary、commit_hash（commit 后更新）。
  - Step 9   Issue comment:
      远程落盘到 GitHub Issue #N，本地可通过 Step 10 回读验证。
  - Step 10  最新 comment 获取:
      stdout 输出 Issue body + 评论列表，不额外落盘；如需持久化可配合 `--output`。

参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --devroot | str | ✅ | 无 | 工具链根绝对路径（必须与 CWD 一致） |
| --target | str | ❌ | --devroot | 操作目标仓库（polyrepo 时传入） |
| --message | str | 否 | None | commit message（如未传入，自动从 staged 文件生成） |
| --auto | flag | 否 | False | [已废弃] 现默认自动从 staged 文件生成 commit message，无需显式指定 |
| --step | str | 否 | all | 执行单步：0(仅preflight+manifest)/4/5/6/7/8/9/10/all |
| --issue | int | 否 | 1 | Issue 编号 |

调用示例：

  # 单仓库完整部署（cs_py 自身）
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}"

  # Polyrepo 完整部署（jywl-lab）
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}\apps\repos\jywl-team\jywl-lab"

  # 显式指定 commit message
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --message "feat: xxx"
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 工具链根：CWD 是唯一可信参照物
_TOOLCHAIN_ROOT = Path.cwd()

# 路径常量（基于工具链根）
_GIT_EXE = _TOOLCHAIN_ROOT / "venv" / "git" / "cmd" / "git.exe"
_PY_EXE = _TOOLCHAIN_ROOT / "venv" / "py" / "python.exe"
_SCRIPTS_DIR = _TOOLCHAIN_ROOT / "references" / "tasks" / "deploy-git-isolated" / "scripts"
_PY_STEPS_DIR = _SCRIPTS_DIR / "py-steps"
_PY_TOOLS_DIR = _SCRIPTS_DIR / "py-tools"

# atomic 脚本路径
_ATOMIC_GIT_PREFLIGHT_GENERAL = _PY_TOOLS_DIR / "atomic-git-preflight-general.py"
_ATOMIC_DEPLOY_PREFLIGHT = _PY_TOOLS_DIR / "atomic-deploy-preflight.py"
_ATOMIC_POLYREPO_CONTEXT = _PY_TOOLS_DIR / "atomic-polyrepo-context-manifest.py"


def _verify_devroot(args_devroot: str) -> Path:
    """验证 --devroot 与 CWD 一致，返回工具链根 Path。"""
    devroot = Path(args_devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)
    # 验证：--devroot 必须与 CWD 一致
    cwd = Path.cwd()
    if devroot.resolve() != cwd.resolve():
        print(f"[ERROR] --devroot 与 CWD 不一致")
        print(f"  --devroot: {devroot.resolve()}")
        print(f"  CWD:       {cwd.resolve()}")
        print(f"[HINT] 请在工具链根目录下执行，或检查 --devroot 传入路径")
        sys.exit(1)
    return devroot


def _run_git(target: Path, args: list, check: bool = True) -> subprocess.CompletedProcess:
    """在目标仓库执行隔离 git 命令。"""
    cmd = [str(_GIT_EXE), "-C", str(target)] + args
    print(f"[{datetime.now().isoformat()}] [GIT] {' '.join(cmd)}")
    sys.stdout.flush()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        print(f"[FAIL] git {' '.join(args)} 失败")
        if result.stderr:
            print(f"  stderr: {result.stderr.strip()}")
    return result


def _mask_pat(text: str) -> str:
    """将命令行/URL 中的 GitHub PAT 替换为 ***，防止泄露到 stdout。"""
    return re.sub(r"(https?://[^:]+:)([^@]+)(@)", r"\1***\3", text)


def _auto_generate_message(target: Path) -> str:
    """从 staged 文件自动生成 commit message。"""
    result = _run_git(target, ["diff", "--cached", "--name-only"])
    files = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]
    if not files:
        return "auto: no changes"
    if len(files) == 1:
        return f"auto: update {files[0]}"
    elif len(files) <= 3:
        return f"auto: update {', '.join(files)}"
    else:
        return f"auto: update {len(files)} files"


def _generate_ai_summary(toolchain_root: Path, target: Path, message: str, cached: bool = False) -> str:
    """调用 generate-ai-summary.py 生成 AI 语义摘要。实时透传子进程输出，避免进度信息被吞。"""
    script = _PY_TOOLS_DIR / "generate-ai-summary.py"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    diff_output = toolchain_root / "venv" / "tmp" / f"diff-audit-for-ai-summary-{ts}.json"
    cmd = [
        str(_PY_EXE), str(script),
        "--devroot", str(toolchain_root),
        "--target", str(target),
        "--message", message,
        "--diff-output", str(diff_output),
    ]
    if cached:
        cmd.append("--cached")

    print("[AI Summary] 正在生成语义摘要...")
    print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd)}")
    sys.stdout.flush()
    start = time.time()
    try:
        # Popen 实时读取并透传，避免 capture_output=True 导致进度信息被吞
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output_lines = []
        for line in process.stdout:
            line = line.rstrip("\n")
            print(line, flush=True)
            output_lines.append(line)
        process.wait(timeout=300)
        elapsed = time.time() - start

        if process.returncode != 0:
            print(f"[AI Summary] 生成失败 (耗时 {elapsed:.2f}s)")
            return ""

        summary_text = ""
        for line in output_lines:
            if line.startswith("[Output] 已落盘:"):
                output_path = Path(line.split("已落盘:", 1)[1].strip())
                if output_path.exists():
                    data = json.loads(output_path.read_text(encoding="utf-8"))
                    summary_text = data.get("ai_summary", "")
                break

        if summary_text:
            print(f"[AI Summary] 生成完成 (耗时 {elapsed:.2f}s), 长度: {len(summary_text)} 字符")
        else:
            print(f"[AI Summary] 摘要为空 (耗时 {elapsed:.2f}s)")
        return summary_text
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"[AI Summary] 超时 (>300s, 实际 {elapsed:.2f}s)")
        return ""
    except Exception as e:
        elapsed = time.time() - start
        print(f"[AI Summary] 异常 (耗时 {elapsed:.2f}s): {e}", file=sys.stderr)
        return ""


def _generate_meta(toolchain_root: Path, target: Path, message: str) -> Path:
    """生成部署 meta 文件。"""
    import json
    from datetime import datetime, timezone

    # 获取 staged 变更
    result = _run_git(target, ["diff", "--cached", "--name-status"])
    changes = {"A": [], "M": [], "D": [], "R": []}
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0][0]
        path = parts[-1]
        if status in changes:
            changes[status].append(path)
        else:
            changes["M"].append(path)

    # 自动分类
    cats = {"脚本改造": [], "规范与模板": [], "文档更新": [], "其他": []}
    for status, paths in changes.items():
        for p in paths:
            if p.endswith(".md") or p.endswith(".mdc") or p.endswith(".txt") or p.endswith(".rst"):
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["文档更新"].append(f"{label}: {p}")
            elif "scripts/" in p or "py-steps/" in p or "py-tools/" in p:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["脚本改造"].append(f"{label}: {p}")
            elif "schema/" in p or "json/" in p:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["规范与模板"].append(f"{label}: {p}")
            elif "docs/" in p or "README" in p:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["文档更新"].append(f"{label}: {p}")
            else:
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["其他"].append(f"{label}: {p}")

    categories = []
    for name, items in cats.items():
        if items:
            categories.append({"name": name, "items": items})

    total_changed = sum(len(v) for v in changes.values())
    print(f"[Meta] 变更文件: {total_changed} 个, 分类: {len(categories)} 组")

    # AI 摘要
    ai_summary = _generate_ai_summary(toolchain_root, target, message, cached=True)
    if not ai_summary:
        print(f"\n{'='*50}")
        print("[FAIL] AI 摘要生成失败")
        print("[FAIL] 已执行至 Step 4 (git add)，文件已暂存但未提交")
        print("[FAIL] 如需回滚请执行: git reset HEAD")
        print(f"{'='*50}\n")
        sys.exit(1)

    print("[Mode] AI 语义层就绪 — 将生成含语义摘要的 Issue comment")

    meta = {
        "version": "1.2.0",
        "commit_message": message,
        "summary": message,
        "categories": categories,
        "ai_summary": ai_summary,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    meta_path = toolchain_root / "venv" / "tmp" / f"workflow-meta-{ts}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Meta] 已生成实时配置: {meta_path}")
    return meta_path


def _update_meta_commit_hash(meta_path: Path, target: Path) -> None:
    """commit 后更新 meta 中的 commit hash。"""
    result = _run_git(target, ["rev-parse", "--short", "HEAD"])
    commit_hash = result.stdout.strip()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["commit_hash"] = commit_hash
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Meta] commit hash 已更新: {commit_hash}")


def _run_py_step(name: str, script_path: Path, extra_args: list = None) -> tuple[bool, float]:
    """执行 Python step 脚本，实时输出，返回 (成功?, 耗时秒)。"""
    print(f"\n{'='*50}")
    print(f"[Step] {name}")
    print(f"{'='*50}")

    cmd = [str(_PY_EXE), str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd)}")
    sys.stdout.flush()
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        elapsed = time.time() - start

        if result.returncode != 0:
            print(f"[FAIL] {name} 失败 (耗时 {elapsed:.2f}s)")
            return False, elapsed

        print(f"[OK] {name} 完成 (耗时 {elapsed:.2f}s)")
        return True, elapsed

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"[FAIL] {name} 超时 (>30s)")
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"[FAIL] {name} 异常: {e} (耗时 {elapsed:.2f}s)")
        return False, elapsed


def main():
    parser = argparse.ArgumentParser(description="deploy-git-isolated Polyrepo 全链条部署")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径（必须与 CWD 一致）")
    parser.add_argument("--target", required=True, help="操作目标仓库绝对路径（polyrepo 调用契约要求，必须显式传入，即使与 --devroot 相同）")
    parser.add_argument("--message", default=None, help="Commit message（如未传入，自动从 staged 文件生成）")
    parser.add_argument("--auto", action="store_true", help="[已废弃] 自动生成 commit message（现默认行为，无需显式指定）")
    parser.add_argument("--step", choices=["0", "4", "5", "6", "7", "8", "9", "10", "all"], default="all")
    parser.add_argument("--issue", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300, help="网络操作超时秒数（默认 300s，Step 7/9/10 使用）")
    args = parser.parse_args()

    # 验证 devroot
    toolchain_root = _verify_devroot(args.devroot)

    # 确定操作目标
    target = Path(args.target) if args.target else toolchain_root
    if not target.exists():
        print(f"[ERROR] target 不存在: {target}")
        sys.exit(1)

    # 验证隔离 git
    if not _GIT_EXE.exists():
        print(f"[ERROR] 隔离 Git 未找到: {_GIT_EXE}")
        sys.exit(1)

    # 验证目标仓库
    if not (target / ".git").exists():
        print(f"[ERROR] target 下无 .git/ 目录: {target}")
        sys.exit(1)

    auto_mode = args.auto
    user_message = args.message

    total_start = time.time()
    print(f"\n{'#'*50}")
    print("# deploy-git-isolated Polyrepo 全链条部署")
    print(f"# 工具链根: {toolchain_root}")
    print(f"# 操作目标: {target}")
    print(f"# git.exe:  {_GIT_EXE}")
    if auto_mode:
        print("# 模式: --auto")
    elif user_message:
        print(f"# message: {user_message}")
    print(f"{'#'*50}")
    sys.stdout.flush()

    # ========== Step 0a: 通用 git preflight（polyrepo 通用版）==========
    if not _ATOMIC_GIT_PREFLIGHT_GENERAL.exists():
        print(f"[ERROR] atomic-git-preflight-general 不存在: {_ATOMIC_GIT_PREFLIGHT_GENERAL}")
        sys.exit(1)
    cmd_0a = [str(_PY_EXE), str(_ATOMIC_GIT_PREFLIGHT_GENERAL), "--target", str(target)]
    print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd_0a)}")
    sys.stdout.flush()
    result = subprocess.run(
        cmd_0a,
        capture_output=False, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0a: atomic-git-preflight-general 失败，终止部署")
        sys.exit(1)

    # ========== Step 0b: 部署特有 preflight ==========
    if not _ATOMIC_DEPLOY_PREFLIGHT.exists():
        print(f"[ERROR] atomic-deploy-preflight 不存在: {_ATOMIC_DEPLOY_PREFLIGHT}")
        sys.exit(1)
    cmd_0b = [str(_PY_EXE), str(_ATOMIC_DEPLOY_PREFLIGHT), "--devroot", str(toolchain_root), "--target", str(target)]
    print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd_0b)}")
    sys.stdout.flush()
    result = subprocess.run(
        cmd_0b,
        capture_output=False, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0b: atomic-deploy-preflight 失败，终止部署")
        sys.exit(1)

    # ========== Step 0c: 产生 PolyrepoContext manifest ==========
    if not _ATOMIC_POLYREPO_CONTEXT.exists():
        print(f"[ERROR] atomic-polyrepo-context-manifest 不存在: {_ATOMIC_POLYREPO_CONTEXT}")
        sys.exit(1)

    manifest_path = toolchain_root / "venv" / "tmp" / f"polyrepo-context-wf-{int(time.time())}.json"
    cmd_0c = [str(_PY_EXE), str(_ATOMIC_POLYREPO_CONTEXT), "--devroot", str(toolchain_root), "--target", str(target), "--output", str(manifest_path)]
    print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd_0c)}")
    sys.stdout.flush()
    result = subprocess.run(
        cmd_0c,
        capture_output=False, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0c: atomic-polyrepo-context-manifest 失败，终止部署")
        sys.exit(1)
    if not manifest_path.exists():
        print(f"[FAIL] Step 0c: manifest 文件未生成: {manifest_path}")
        sys.exit(1)
    print(f"\n[Step 0c] PolyrepoContext manifest 已生成: {manifest_path}")
    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"  toolchain_root: {manifest_data.get('toolchain_root')}")
        print(f"  target:         {manifest_data.get('target')}")
        print(f"  is_polyrepo:    {manifest_data.get('is_polyrepo')}")
        print(f"  repo_url:       {manifest_data.get('repo_url')}")
        print(f"  branch:         {manifest_data.get('branch')}")
    except Exception as e:
        print(f"[WARN] manifest 内容读取失败: {e}")

    # 仅审计 preflight + manifest，不执行后续部署步骤
    if args.step == "0":
        print(f"\n{'#'*50}")
        print("# [SUCCESS] Preflight + Manifest 审计完成")
        print(f"{'#'*50}\n")
        sys.exit(0)

    # ========== 构建步骤列表 ==========
    steps = []
    if args.step in ("4", "all"):
        steps.append("step4")
    if args.step in ("5", "all"):
        steps.append("step5")
    if args.step in ("6", "all"):
        steps.append("step6")
    if args.step in ("7", "all"):
        steps.append("step7")
    if args.step in ("8", "all"):
        steps.append("step8")
    if args.step in ("9", "all"):
        steps.append("step9")
    if args.step in ("10", "all"):
        steps.append("step10")

    all_ok = True
    meta_path = None
    manifest_path = None
    commit_executed = False
    summary_path = None
    remote_comment_path = None
    step5_message = None
    # 认证信息缓存（Step 7/8 共享）
    auth_repo_url = None
    auth_pat = None
    auth_username = None
    auth_url = None

    for step in steps:
        # Step 4: git add
        if step == "step4":
            print(f"\n{'='*50}")
            print("[Step] Step 4: git add -A")
            print(f"{'='*50}")
            result = _run_git(target, ["add", "-A"])
            if result.returncode != 0:
                print("[FAIL] git add -A 失败")
                all_ok = False
                break
            print("[OK] git add -A 完成")

            # git status --short
            result = _run_git(target, ["status", "--short"], check=False)
            if result.stdout.strip():
                print("\n--- Staged 文件 ---")
                print(result.stdout.strip())
                print("-" * 36)

            # 确定 commit message
            if user_message:
                step5_message = user_message
                print(f"[Message] 使用传入的 commit message: {step5_message}")
            else:
                step5_message = _auto_generate_message(target)
                print(f"[Auto] 自动生成 commit message: {step5_message}")

            # Step 4.5: staged 内容安全扫描
            print(f"\n{'='*50}")
            print("[Step] Step 4.5: staged 内容安全扫描")
            print(f"{'='*50}")
            script_45 = _PY_TOOLS_DIR / "atomic-check-staged-after-add.py"
            cmd_45 = [
                str(_PY_EXE), str(script_45),
                "--devroot", str(toolchain_root),
                "--target", str(target),
                "--git-exe", str(_GIT_EXE),
            ]
            print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd_45)}")
            sys.stdout.flush()
            result = subprocess.run(
                cmd_45,
                capture_output=False,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                print("[FAIL] Step 4.5: staged 内容安全扫描失败")
                all_ok = False
                break

            # 生成 meta
            meta_path = _generate_meta(toolchain_root, target, step5_message)
            continue

        # Step 5: git commit
        if step == "step5":
            if step5_message is None:
                if user_message:
                    step5_message = user_message
                else:
                    step5_message = _auto_generate_message(target)

            print(f"\n{'='*50}")
            print("[Step] Step 5: git commit")
            print(f"{'='*50}")
            result = _run_git(target, ["commit", "-m", step5_message], check=False)
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="")
            if result.returncode != 0:
                print("[FAIL] git commit 失败")
                all_ok = False
                break
            print(f"[OK] commit 完成: {step5_message}")
            commit_executed = True

            # 更新 meta commit hash
            if meta_path and meta_path.exists():
                _update_meta_commit_hash(meta_path, target)
            continue

        # Step 6: remote
        if step == "step6":
            print(f"\n{'='*50}")
            print("[Step] Step 6: git remote")
            print(f"{'='*50}")
            result = _run_git(target, ["remote", "-v"], check=False)
            if result.stdout.strip():
                print(result.stdout.strip())
            print("[OK] remote 检查完成")
            continue

        # Step 7: push
        if step == "step7":
            print(f"\n{'='*50}")
            print("[Step] Step 7: git push")
            print(f"{'='*50}")

            # 读取 .env（PAT/username 仍从工具链根 .env 读取）
            env_path = toolchain_root / ".env"
            if not env_path.exists():
                print("[FAIL] .env 文件不存在")
                all_ok = False
                break

            env = {}
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    env[key] = val

            pat = env.get("GITHUB_PAT", "").strip()
            username = env.get("GITHUB_USERNAME", "").strip()

            # repo_url 从 manifest 读取（manifest 生成时已做对碰审计）
            repo_url = ""
            default_branch = "main"
            allow_direct_push = []
            if manifest_path and manifest_path.exists():
                try:
                    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    repo_url = manifest_data.get("repo_url", "").strip()
                    default_branch = manifest_data.get("default_branch", "main")
                    allow_direct_push = manifest_data.get("allow_direct_push_to", [])
                    if repo_url:
                        print(f"[OK] repo_url 来自 manifest: {repo_url}")
                except Exception as e:
                    print(f"[WARN] manifest 读取失败: {e}")

            # manifest 无 repo_url 时的兜底（不应发生，但保留容错）
            if not repo_url:
                repo_url = env.get("GITHUB_REPO_URL", "").strip()
                if repo_url:
                    print(f"[WARN] repo_url 来自 .env（已淘汰）: {repo_url}")

            if not repo_url or not pat or not username:
                print("[FAIL] GITHUB_PAT/REPO_URL/USERNAME 未配置")
                all_ok = False
                break

            # 缓存认证信息供 Step 8 复用
            auth_repo_url = repo_url
            auth_pat = pat
            auth_username = username

            # 获取当前分支
            result = _run_git(target, ["branch", "--show-current"])
            branch = result.stdout.strip()
            if not branch:
                print("[FAIL] 无法获取当前分支名")
                all_ok = False
                break
            print(f"[OK] 当前分支: {branch}")

            # 构造认证 URL
            repo_path = re.sub(r"^https://github.com/", "", repo_url)
            auth_url = f"https://{username}:{pat}@github.com/{repo_path}"

            # 阻断 GCM 弹窗
            cmd_gcm = [str(_GIT_EXE), "-C", str(target), "config", "--local", "credential.helper", ""]
            print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd_gcm)}")
            sys.stdout.flush()
            subprocess.run(cmd_gcm, capture_output=True)
            env_push = os.environ.copy()
            env_push["GCM_INTERACTIVE"] = "0"
            env_push["GIT_TERMINAL_PROMPT"] = "0"

            print("正在 push 到 GitHub ...")
            cmd_push = [str(_GIT_EXE), "-C", str(target), "push", auth_url, branch]
            print(f"[{datetime.now().isoformat()}] [EXEC] {_mask_pat(' '.join(cmd_push))}")
            sys.stdout.flush()
            result = subprocess.run(
                cmd_push,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env_push
            )
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="")
            if result.returncode != 0:
                stderr_lower = result.stderr.lower() if result.stderr else ""
                is_protected = "rejected" in stderr_lower or "protected" in stderr_lower

                if branch in allow_direct_push:
                    # 本地白名单允许，但仍失败 → 非策略原因
                    print(f"[FAIL] git push 失败（分支 '{branch}' 在 allow_direct_push_to 白名单中，但远程仍拒绝）")
                    if is_protected:
                        print("[HINT] 远程 GitHub 可能额外配置了分支保护，请检查 Web 端 Settings → Branches")
                    else:
                        print("[HINT] 请检查网络、PAT 有效性、或远程仓库状态")
                elif branch == default_branch and not allow_direct_push:
                    # 严格模式：默认分支禁止直接 push
                    print(f"[FAIL] git push 被远程拒绝（严格模式：默认分支 '{default_branch}' 禁止直接 push）")
                    print("[HINT] 本仓库 security_level=strict，必须走 feature 分支 + PR merge 流程")
                    print(f"  git checkout -b feat/xxx")
                    print(f"  git push origin feat/xxx")
                    print(f"  gh pr create --base {default_branch}")
                else:
                    # 一般保护
                    print(f"[FAIL] git push 被远程拒绝（分支保护规则）")
                    print(f"[HINT] 当前分支 '{branch}' 不在 allow_direct_push_to 白名单中")
                    print("[HINT] 请使用 feature 分支 + PR merge 流程")
                all_ok = False
                break
            print(f"[OK] push 成功: {repo_url} [{branch}]")
            continue

        # Step 8: upstream
        if step == "step8":
            print(f"\n{'='*50}")
            print("[Step] Step 8: upstream 设置")
            print(f"{'='*50}")
            result = _run_git(target, ["branch", "--show-current"])
            branch = result.stdout.strip()
            if not branch:
                print("[WARN] 无法获取当前分支名，跳过 upstream 设置")
                continue

            # 前置检查：origin remote 是否存在
            result_origin = _run_git(target, ["remote", "get-url", "origin"], check=False)
            if result_origin.returncode != 0:
                print("[WARN] origin remote 不存在，跳过 upstream 设置")
                print("[HINT] 如需手动设置: git remote add origin <url>")
                continue

            # 检查远程分支是否已存在（Step 7 应已推送）
            result_fetch = _run_git(target, ["fetch", "origin", branch], check=False)
            if result_fetch.returncode != 0:
                print(f"[WARN] 无法 fetch origin/{branch}，跳过 upstream 设置")
                continue

            cmd_upstream = [str(_GIT_EXE), "-C", str(target), "branch", "--set-upstream-to", f"origin/{branch}", branch]
            print(f"[{datetime.now().isoformat()}] [EXEC] {' '.join(cmd_upstream)}")
            sys.stdout.flush()
            result = subprocess.run(
                cmd_upstream,
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="")
            if result.returncode == 0:
                print(f"[OK] upstream 设置完成: {branch} -> origin/{branch}")
            else:
                stderr_lower = result.stderr.lower() if result.stderr else ""
                if "already exists" in stderr_lower or "already tracking" in stderr_lower:
                    print(f"[OK] upstream 已存在: {branch}")
                else:
                    print(f"[WARN] upstream 设置返回非 0: {result.stderr.strip()[:200]}")
            continue

        # Step 9: issue sync
        if step == "step9":
            print(f"\n{'='*50}")
            print("[Step] Step 9: issue sync")
            print(f"{'='*50}")
            script = _PY_STEPS_DIR / "step-09-github-sync-issue.py"
            if not script.exists():
                print(f"[ERROR] step-09-github-sync-issue.py 不存在")
                all_ok = False
                break
            extra = ["--devroot", str(toolchain_root), "--target", str(target), "--issue", str(args.issue)]
            if manifest_path and manifest_path.exists():
                try:
                    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    repo_url = manifest_data.get("repo_url", "").strip()
                    if repo_url:
                        extra.extend(["--repo-url", repo_url])
                        print(f"[Step 9] repo_url 来自 manifest: {repo_url}")
                except Exception as e:
                    print(f"[WARN] manifest 读取失败: {e}")
            if meta_path and meta_path.exists():
                extra.extend(["--meta", str(meta_path)])
            ok, _ = _run_py_step("Step 9: issue sync", script, extra)
            if not ok:
                all_ok = False
                break
            continue

        # Step 10: fetch latest comment
        if step == "step10":
            print(f"\n{'='*50}")
            print("[Step] Step 10: fetch latest comment")
            print(f"{'='*50}")
            script = _PY_TOOLS_DIR / "fetch_issue.py"
            if not script.exists():
                print(f"[ERROR] fetch_issue.py 不存在")
                all_ok = False
                break
            extra = ["--devroot", str(toolchain_root), "--issue-number", str(args.issue), "--latest"]
            if manifest_path and manifest_path.exists():
                try:
                    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    repo_url = manifest_data.get("repo_url", "").strip()
                    if repo_url:
                        extra.extend(["--repo-url", repo_url])
                        print(f"[Step 10] repo_url 来自 manifest: {repo_url}")
                except Exception as e:
                    print(f"[WARN] manifest 读取失败: {e}")
            ok, _ = _run_py_step("Step 10: fetch latest comment", script, extra)
            if not ok:
                all_ok = False
                break
            continue

    total_elapsed = time.time() - total_start
    print(f"\n{'#'*50}")
    if all_ok:
        print(f"# [SUCCESS] 部署完成 (总耗时 {total_elapsed:.2f}s)")
    else:
        print(f"# [FAILURE] 部署中断 (总耗时 {total_elapsed:.2f}s)")
    print(f"{'#'*50}\n")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
