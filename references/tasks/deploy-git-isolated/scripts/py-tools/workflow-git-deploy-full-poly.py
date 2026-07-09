#!/usr/bin/env python3
r"""
workflow-git-deploy-full-poly.py — deploy-git-isolated Polyrepo 全链条部署 workflow
标签：py-tools
版本：v1.1.0

职责：纯编排器，支持单仓库与 polyrepo 两种场景的自动部署。
      工具链根固定为 Path.cwd()，--devroot 仅用于验证一致性。
      操作目标通过 --target 显式指定，省略时默认等于工具链根（单仓库场景）。

执行顺序：
  1. Step 0a: atomic-git-preflight-general（通用 git 环境验证，支持 --target）
  2. Step 0b: atomic-deploy-preflight（部署特有验证：PAT/分支/agent/git-security 审计）
  3. Step 0c: atomic-polyrepo-context-manifest（生成 PolyrepoContext manifest，记录 repo_url/branch 等）
  4. Step 4: git -C <target> add -A
  5. Step 4.5: git_security 扫描（target 仓库，工具链 git.exe）
  6. AI 摘要 + meta 生成
  7. Step 5: git -C <target> commit
  8. 更新 meta commit hash
  9. Step 6-9: remote → push → upstream → issue sync
  10. Step 10: 获取 remote 最新 comment 落盘

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
    """调用 generate-ai-summary.py 生成 AI 语义摘要。"""
    script = _PY_TOOLS_DIR / "generate-ai-summary.py"
    cmd = [str(_PY_EXE), str(script), "--devroot", str(toolchain_root), "--target", str(target), "--message", message]
    if cached:
        cmd.append("--cached")

    print("[AI Summary] 正在生成语义摘要...")
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        elapsed = time.time() - start
        if result.returncode != 0:
            print(f"[AI Summary] 生成失败 (耗时 {elapsed:.2f}s)")
            print(f"[AI Summary] stderr: {result.stderr[:500]}", file=sys.stderr)
            return ""

        summary_text = ""
        for line in result.stdout.splitlines():
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
        print(f"[AI Summary] 超时 (>300s)")
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

    start = time.time()
    try:
        sys.stdout.flush()
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
    parser.add_argument("--target", default=None, help="操作目标仓库（默认等于 --devroot）")
    parser.add_argument("--message", default=None, help="Commit message（如未传入，自动从 staged 文件生成）")
    parser.add_argument("--auto", action="store_true", help="[已废弃] 自动生成 commit message（现默认行为，无需显式指定）")
    parser.add_argument("--step", choices=["0", "4", "5", "6", "7", "8", "9", "10", "all"], default="all")
    parser.add_argument("--issue", type=int, default=1)
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
    result = subprocess.run(
        [str(_PY_EXE), str(_ATOMIC_GIT_PREFLIGHT_GENERAL), "--target", str(target)],
        capture_output=False, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0a: atomic-git-preflight-general 失败，终止部署")
        sys.exit(1)

    # ========== Step 0b: 部署特有 preflight ==========
    if not _ATOMIC_DEPLOY_PREFLIGHT.exists():
        print(f"[ERROR] atomic-deploy-preflight 不存在: {_ATOMIC_DEPLOY_PREFLIGHT}")
        sys.exit(1)
    result = subprocess.run(
        [str(_PY_EXE), str(_ATOMIC_DEPLOY_PREFLIGHT), "--devroot", str(toolchain_root), "--target", str(target)],
        capture_output=False, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0b: atomic-deploy-preflight 失败，终止部署")
        sys.exit(1)

    # ========== Step 0c: 产生 PolyrepoContext manifest ==========
    if not _ATOMIC_POLYREPO_CONTEXT.exists():
        print(f"[ERROR] atomic-polyrepo-context-manifest 不存在: {_ATOMIC_POLYREPO_CONTEXT}")
        sys.exit(1)
    result = subprocess.run(
        [str(_PY_EXE), str(_ATOMIC_POLYREPO_CONTEXT), "--devroot", str(toolchain_root), "--target", str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0c: atomic-polyrepo-context-manifest 失败，终止部署")
        if result.stderr:
            print(f"  stderr: {result.stderr.strip()}")
        sys.exit(1)
    manifest_path = Path(result.stdout.strip())
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
            sys.path.insert(0, str(_SCRIPTS_DIR))
            from py_lib import load_plugins
            registry = load_plugins(devroot=str(toolchain_root), tags=["git"])
            sec_result = registry.git_security.scan_git_security(devroot=target, git_exe=_GIT_EXE)
            if not sec_result.ok:
                print(f"[FAIL] 安全扫描发现 {len(sec_result.violations)} 处违规:")
                for v in sec_result.violations:
                    print(f"  ! {v}")
                all_ok = False
                break
            print("[OK] 安全扫描通过")

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

            # repo_url 优先从 manifest 读取（polyrepo 场景），fallback 到 .env
            repo_url = ""
            if manifest_path and manifest_path.exists():
                try:
                    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    repo_url = manifest_data.get("repo_url", "").strip()
                    print(f"[OK] repo_url 来自 manifest: {repo_url}")
                except Exception as e:
                    print(f"[WARN] manifest 读取失败: {e}，fallback 到 .env")

            if not repo_url:
                repo_url = env.get("GITHUB_REPO_URL", "").strip()
                if repo_url:
                    print(f"[OK] repo_url 来自 .env: {repo_url}")

            if not repo_url or not pat or not username:
                print("[FAIL] GITHUB_PAT/REPO_URL/USERNAME 未配置")
                all_ok = False
                break

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
            subprocess.run([str(_GIT_EXE), "-C", str(target), "config", "--local", "credential.helper", ""], capture_output=True)
            env_push = os.environ.copy()
            env_push["GCM_INTERACTIVE"] = "0"
            env_push["GIT_TERMINAL_PROMPT"] = "0"

            print("正在 push 到 GitHub ...")
            result = subprocess.run(
                [str(_GIT_EXE), "-C", str(target), "push", auth_url, branch],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=env_push
            )
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="")
            if result.returncode != 0:
                stderr_lower = result.stderr.lower() if result.stderr else ""
                if "rejected" in stderr_lower or "protected" in stderr_lower:
                    print("[FAIL] git push 被远程拒绝（分支保护规则）")
                    print(f"[HINT] 当前分支 '{branch}' 可能受保护，请使用 feature 分支 + PR merge 流程")
                else:
                    print("[FAIL] git push 失败")
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
            if branch:
                result = _run_git(target, ["push", "-u", "origin", branch], check=False)
                if result.returncode == 0:
                    print(f"[OK] upstream 设置完成: origin/{branch}")
                else:
                    print(f"[WARN] upstream 设置跳过（可能已存在）")
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
