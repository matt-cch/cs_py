#!/usr/bin/env python3
"""
workflow-deploy-full.py — deploy-git-isolated 全链条部署 workflow
标签：py-tools

职责：编排 Step 4-8，调用 Python step 脚本，分步输出并计时。
与 PS1 版对齐：按顺序执行 add → commit → remote → push → upstream，
任何一步失败立即停止。

用法：
    python workflow-deploy-full.py --message "feat: xxx"
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 路径常量
_PY_STEPS_DIR = Path(__file__).parent.parent / "py-steps"
_PY_EXE = Path(__file__).parent.parent.parent.parent.parent.parent / "venv" / "py" / "python.exe"


def _run_py_step(name: str, script_path: Path, extra_args: list = None) -> tuple[bool, float]:
    """
    执行 Python step 脚本，实时输出，返回 (成功?, 耗时秒)。
    """
    print(f"\n{'='*50}")
    print(f"[Step] {name}")
    print(f"{'='*50}")

    cmd = [str(_PY_EXE), str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    start = time.time()
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()

        proc.wait()
        elapsed = time.time() - start

        if proc.returncode != 0:
            print(f"[FAIL] {name} 失败 (耗时 {elapsed:.2f}s)")
            return False, elapsed

        print(f"[OK] {name} 完成 (耗时 {elapsed:.2f}s)")
        return True, elapsed

    except Exception as e:
        elapsed = time.time() - start
        print(f"[FAIL] {name} 异常: {e} (耗时 {elapsed:.2f}s)")
        return False, elapsed


def main():
    parser = argparse.ArgumentParser(description="deploy-git-isolated 全链条部署 workflow")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径")
    parser.add_argument("--message", default="init: empty scaffold with safety gitignore", help="Commit message")
    parser.add_argument(
        "--step",
        choices=["4", "5", "6", "7", "8", "all"],
        default="all",
        help="执行单步或全部 (默认 all)"
    )
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)

    total_start = time.time()
    print(f"\n{'#'*50}")
    print("# deploy-git-isolated 全链条部署")
    print(f"# devroot: {devroot}")
    print(f"# message: {args.message}")
    print(f"{'#'*50}")

    steps = []
    if args.step in ("4", "all"):
        steps.append(("Step 4: git add", _PY_STEPS_DIR / "step-04-github-deploy-add.py", ["--devroot", str(devroot)]))
    if args.step in ("5", "all"):
        steps.append(("Step 5: git commit", _PY_STEPS_DIR / "step-05-github-commit.py", ["--devroot", str(devroot), "--message", args.message]))
    if args.step in ("6", "all"):
        steps.append(("Step 6: remote", _PY_STEPS_DIR / "step-06-github-remote.py", ["--devroot", str(devroot)]))
    if args.step in ("7", "all"):
        steps.append(("Step 7: push", _PY_STEPS_DIR / "step-07-github-push.py", ["--devroot", str(devroot)]))
    if args.step in ("8", "all"):
        steps.append(("Step 8: upstream", _PY_STEPS_DIR / "step-08-github-upstream.py", ["--devroot", str(devroot)]))

    all_ok = True
    for name, script, extra in steps:
        ok, elapsed = _run_py_step(name, script, extra)
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
