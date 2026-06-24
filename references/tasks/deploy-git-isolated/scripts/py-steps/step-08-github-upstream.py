#!/usr/bin/env python3
"""
step-08-github-upstream.py — Step 8: Set Upstream
标签：py-steps

职责：设置本地分支跟踪 origin，简化后续 push。
与 PS1 版对齐：获取当前分支后，git push -u origin <branch>。

用法：
    python step-08-github-upstream.py --devroot "D:/pjt/cursor/cs_py"
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def main():
    parser = argparse.ArgumentParser(description="Step 8: Set Upstream")
    parser.add_argument("--devroot", default=None, help="Devroot 路径")
    args = parser.parse_args()

    registry = load_plugins(devroot=args.devroot, tags=["core"])
    devroot = Path(registry.devroot)
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    if not git_exe.exists():
        print(f"[ERROR] 隔离 Git 未找到: {git_exe}")
        sys.exit(1)

    print("")
    print("=" * 40)
    print("Step 8: 设置 upstream")
    print("=" * 40)

    # 获取当前分支
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "branch", "--show-current"],
        capture_output=True, text=True, encoding="utf-8"
    )
    branch = result.stdout.strip()
    if not branch:
        print("[ERROR] 无法获取当前分支名")
        sys.exit(1)

    # 设置 upstream（复用 Step 7 的 GCM 阻断）
    subprocess.run(
        [str(git_exe), "-C", str(devroot), "config", "--local", "credential.helper", ""],
        capture_output=True
    )
    env = os.environ.copy()
    env["GCM_INTERACTIVE"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "push", "-u", "origin", branch],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")

    if result.returncode != 0:
        print(f"[FAIL] upstream 设置失败 (exit {result.returncode})")
        sys.exit(1)

    print(f"[OK] upstream 设置完成: origin/{branch}")


if __name__ == "__main__":
    main()
