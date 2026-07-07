#!/usr/bin/env python3
r"""
workflow-deploy-full.py — deploy-git-isolated 全链条部署 workflow
标签：py-tools
版本：v1.3.0 (纯编排器：preflight 抽离为 atomic 脚本)

职责：纯编排器，按序调用 atomic 工具与 py-steps 脚本，自身不内嵌业务逻辑。

执行顺序：
  1. Step 0a: atomic-git-preflight（通用 git 环境验证）
  2. Step 0b: atomic-deploy-preflight（部署特有验证：PAT/分支/agent）
  3. Step 4: git add
  4. Step 4.5: atomic-check-staged-after-add（staged 内容安全扫描）
  5. AI 摘要 + meta 生成
  6. Step 5: git commit
  7. 更新 meta commit hash
  8. Step 6-9: remote → push → upstream → issue sync

参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --devroot | str | 否 | 当前工作目录 | devroot 绝对路径（推荐显式传入） |
| --message | str | 否 | None | commit message；与 --auto 互斥 |
| --auto | flag | 否 | False | 自动生成 commit message；与 --message 互斥 |
| --step | str | 否 | all | 执行单步：4/5/6/7/8/9/all |
| --issue | int | 否 | 1 | Step 9 Issue 编号 |

调用示例（Agent 格式，绝对路径，显式传 --devroot）：

  # 全自动模式（推荐）：自动生成 commit message + AI 摘要
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --auto

  # 指定 commit message
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx"

  # 仅执行单步（调试用）
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --step 7 --message "feat: xxx"

  # 指定 Issue 编号
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx" --issue 1

回滚说明：
  - Step 4 之后、Step 5 之前 AI 摘要失败：文件已 staged，执行 `git reset HEAD` 回滚
  - Step 5 commit 后：执行 `git reset --soft HEAD~1` 撤销 commit（保留 staged）
  - Step 7 push 后：需谨慎，可通过 GitHub Web 删除提交或强制推送回滚
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 路径常量
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
_PY_STEPS_DIR = _SCRIPTS_DIR / "py-steps"
_PY_TOOLS_DIR = _SCRIPTS_DIR / "py-tools"
_PY_EXE = Path(__file__).parent.parent.parent.parent.parent.parent / "venv" / "py" / "python.exe"

# atomic 脚本路径
_ATOMIC_GIT_PREFLIGHT = _PY_TOOLS_DIR / "atomic-git-preflight.py"
_ATOMIC_DEPLOY_PREFLIGHT = _PY_TOOLS_DIR / "atomic-deploy-preflight.py"
_ATOMIC_CHECK_STAGED = _PY_TOOLS_DIR / "atomic-check-staged-after-add.py"

# py_lib 统一入口（workflow 通过它加载插件）
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# py_lib 统一入口（workflow 通过它加载插件）
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def _auto_generate_message(devroot: Path) -> str:
    """从 staged 文件自动生成 commit message（--auto 模式使用）。"""
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", "--cached", "--name-only"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    files = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]
    if not files:
        return "auto: no changes"
    if len(files) == 1:
        return f"auto: update {files[0]}"
    elif len(files) <= 3:
        return f"auto: update {', '.join(files)}"
    else:
        return f"auto: update {len(files)} files"


def _generate_ai_summary(devroot: Path, message: str, cached: bool = False) -> str:
    """调用 generate-ai-summary.py 生成 AI 语义摘要。
    失败时返回空字符串并打印错误原因（调用方决定是否终止）。
    """
    import json

    script = Path(__file__).parent / "generate-ai-summary.py"
    cmd = [str(_PY_EXE), str(script), "--devroot", str(devroot), "--message", message]
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
        print(f"[AI Summary] 超时 (>{300}s)")
        return ""
    except Exception as e:
        elapsed = time.time() - start
        print(f"[AI Summary] 异常 (耗时 {elapsed:.2f}s): {e}", file=sys.stderr)
        return ""


def _generate_meta_before_commit(devroot: Path, message: str) -> Path:
    """Step 4 之后、Step 5 之前生成 meta。
    使用 git diff --cached 获取 staged 变更，生成 AI 摘要。
    失败时直接 exit（此时只有 Step 4 执行，可 git reset HEAD 回滚）。
    """
    import json
    from datetime import datetime, timezone

    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    # 1. 获取 staged 文件列表（--name-status）
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", "--cached", "--name-status"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
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

    # 2. 自动分类
    cats = {
        "脚本改造": [],
        "规范与模板": [],
        "文档更新": [],
        "其他": [],
    }
    for status, paths in changes.items():
        for p in paths:
            # 优先按扩展名判断文档类型（.md/.mdc 无论放在哪个目录都是文档）
            if p.endswith(".md") or p.endswith(".mdc") or p.endswith(".txt") or p.endswith(".rst"):
                label = "新增" if status == "A" else ("删除" if status == "D" else "修改")
                cats["文档更新"].append(f"{label}: {p}")
            elif "scripts/" in p or "py-steps/" in p or "py-tools/" in p or "ps-steps/" in p or "ps-tools/" in p:
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

    # 3. 生成 AI 语义摘要（使用 --cached）
    ai_summary = _generate_ai_summary(devroot, message, cached=True)
    if not ai_summary:
        print(f"\n{'='*50}")
        print("[FAIL] AI 摘要生成失败")
        print("[FAIL] 已执行至 Step 4 (git add)，文件已暂存但未提交")
        print("[FAIL] 如需回滚请执行: git reset HEAD")
        print(f"{'='*50}\n")
        sys.exit(1)

    print(f"[Mode] 🧠 AI 语义层就绪 — 将生成含语义摘要的 Issue comment")

    # 4. 构造 meta（不含 commit hash，commit 后补充）
    meta = {
        "version": "1.2.0",
        "commit_message": message,
        "summary": message,
        "categories": categories,
        "ai_summary": ai_summary,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    meta_path = devroot / "venv" / "tmp" / f"workflow-meta-{ts}.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[Meta] 已生成实时配置: {meta_path}")
    return meta_path


def _update_meta_commit_hash(devroot: Path, meta_path: Path) -> None:
    """commit 后更新 meta 中的 commit hash。"""
    import json

    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
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
        # 强制刷新父进程 stdout，避免子进程输出先于父进程 print
        sys.stdout.flush()
        # 不 capture_output，子进程 stdout/stderr 直接继承父进程终端
        # 优点：实时输出 + 无 PIPE 死锁（无 _readerthread）
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
    parser = argparse.ArgumentParser(description="deploy-git-isolated 全链条部署 workflow")
    parser.add_argument("--devroot", default=None, help="Devroot 路径（默认使用当前工作目录）")
    parser.add_argument("--message", default=None, help="Commit message（不传时使用默认消息，--auto 模式下自动生成）")
    parser.add_argument(
        "--auto", action="store_true",
        help="全自动模式：自动从 staged 文件生成 commit message，无需手动指定 --message"
    )
    parser.add_argument(
        "--step",
        choices=["4", "5", "6", "7", "8", "9", "all"],
        default="all",
        help="执行单步或全部 (默认 all)"
    )
    parser.add_argument("--issue", type=int, default=1, help="Issue 编号 (Step 9 用, 默认 1)")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)

    # 显式切换进程 CWD 到目标目录，确保所有相对路径和 . 指向 devroot
    import os
    os.chdir(devroot)
    print(f"[OK] 工作目录已切换: {devroot}")

    # --auto 模式：忽略 --message，后续自动生成
    auto_mode = args.auto
    user_message = args.message  # None 表示未传

    total_start = time.time()
    print(f"\n{'#'*50}")
    print("# deploy-git-isolated 全链条部署")
    print(f"# devroot: {devroot}")
    if auto_mode:
        print("# 模式: --auto（commit message 自动生成）")
    elif user_message:
        print(f"# message: {user_message}")
    else:
        print("# 模式: 默认消息（未指定 --message 也非 --auto）")
    print(f"{'#'*50}")
    sys.stdout.flush()

    # ========== Step 0a: 通用 git preflight ==========
    if not _ATOMIC_GIT_PREFLIGHT.exists():
        print(f"[ERROR] atomic-git-preflight 不存在: {_ATOMIC_GIT_PREFLIGHT}")
        sys.exit(1)
    result = subprocess.run(
        [str(_PY_EXE), str(_ATOMIC_GIT_PREFLIGHT), "--devroot", str(devroot)],
        capture_output=False, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0a: atomic-git-preflight 失败，终止部署")
        sys.exit(1)

    # ========== Step 0b: 部署特有 preflight ==========
    if not _ATOMIC_DEPLOY_PREFLIGHT.exists():
        print(f"[ERROR] atomic-deploy-preflight 不存在: {_ATOMIC_DEPLOY_PREFLIGHT}")
        sys.exit(1)
    result = subprocess.run(
        [str(_PY_EXE), str(_ATOMIC_DEPLOY_PREFLIGHT), "--devroot", str(devroot)],
        capture_output=False, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print("[FAIL] Step 0b: atomic-deploy-preflight 失败，终止部署")
        sys.exit(1)

    # ========== 构建步骤列表 ==========
    steps = []
    if args.step in ("4", "all"):
        steps.append(("Step 4: git add", _PY_STEPS_DIR / "step-04-github-deploy-add.py", ["--devroot", str(devroot)]))

    # Step 5 的 message 在 meta 生成后确定（auto 自动生成，或用户提供的 --message）
    step5_message = None  # 待定
    steps_for_meta = list(steps)  # 当前已确定的步骤

    if args.step in ("5", "all"):
        # 先占位，message 待 meta 后确定
        steps.append(("Step 5: git commit", _PY_STEPS_DIR / "step-05-github-commit.py", None))

    has_step5 = any(s[0].startswith("Step 5:") for s in steps)

    if args.step in ("6", "all"):
        steps.append(("Step 6: remote", _PY_STEPS_DIR / "step-06-github-remote.py", ["--devroot", str(devroot)]))
    if args.step in ("7", "all"):
        steps.append(("Step 7: push", _PY_STEPS_DIR / "step-07-github-push.py", ["--devroot", str(devroot)]))
    if args.step in ("8", "all"):
        steps.append(("Step 8: upstream", _PY_STEPS_DIR / "step-08-github-upstream.py", ["--devroot", str(devroot)]))
    if args.step in ("9", "all"):
        steps.append(("Step 9: issue sync", _PY_STEPS_DIR / "step-09-github-sync-issue.py", ["--devroot", str(devroot), "--issue", str(args.issue)]))

    # ========== 顺序执行 ==========
    all_ok = True
    meta_path = None
    commit_executed = False

    for idx, (name, script, extra) in enumerate(steps):
        # Step 4 执行后、Step 5 之前：生成 meta + AI 摘要
        if name.startswith("Step 4:") and has_step5:
            ok, _ = _run_py_step(name, script, extra)
            if not ok:
                all_ok = False
                break

            # 确定 commit message
            if auto_mode:
                step5_message = _auto_generate_message(devroot)
                print(f"[Auto] 自动生成 commit message: {step5_message}")
            elif user_message:
                step5_message = user_message
            else:
                step5_message = "init: empty scaffold with safety gitignore"

            # Step 4.5: staged 内容安全扫描（必须在 add 后、commit 前）
            if not _ATOMIC_CHECK_STAGED.exists():
                print(f"[ERROR] atomic-check-staged-after-add 不存在: {_ATOMIC_CHECK_STAGED}")
                all_ok = False
                break
            result = subprocess.run(
                [str(_PY_EXE), str(_ATOMIC_CHECK_STAGED), "--devroot", str(devroot)],
                capture_output=False, text=True, encoding="utf-8", errors="replace"
            )
            if result.returncode != 0:
                print("[FAIL] Step 4.5: staged 内容安全扫描失败，终止部署")
                all_ok = False
                break

            # Step 4 完成后立即生成 meta（使用 staged diff）
            meta_path = _generate_meta_before_commit(devroot, step5_message)
            # meta 生成成功后更新 Step 5 的参数
            for j in range(idx + 1, len(steps)):
                if steps[j][0].startswith("Step 5:"):
                    steps[j] = (steps[j][0], steps[j][1], ["--devroot", str(devroot), "--message", step5_message])
                    break
            continue

        # Step 5：git commit
        if name.startswith("Step 5:"):
            # 如果 Step 4 未执行（单步模式），需要单独确定 message
            if extra is None:
                if auto_mode:
                    step5_message = _auto_generate_message(devroot)
                elif user_message:
                    step5_message = user_message
                else:
                    step5_message = "init: empty scaffold with safety gitignore"
                extra = ["--devroot", str(devroot), "--message", step5_message]

            ok, _ = _run_py_step(name, script, extra)
            if not ok:
                all_ok = False
                break
            commit_executed = True

            # commit 后更新 meta 的 commit hash
            has_step9 = any(s[0].startswith("Step 9:") for s in steps[idx + 1:])
            if has_step9 and meta_path is not None:
                _update_meta_commit_hash(devroot, meta_path)
                # 动态更新 Step 9 的 --meta 参数
                for j in range(idx + 1, len(steps)):
                    if steps[j][0].startswith("Step 9:"):
                        new_extra = list(steps[j][2])
                        new_extra.extend(["--meta", str(meta_path)])
                        steps[j] = (steps[j][0], steps[j][1], new_extra)
                        break
            continue

        ok, _ = _run_py_step(name, script, extra)
        if not ok:
            all_ok = False
            break

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
