#!/usr/bin/env python3
"""
step-04-github-deploy-add.py — Step 4: deploy 阶段 add（git add -A）
标签：py-steps

职责：add 所有变更文件到 staged 区域，用于后续 deploy 提交。

用法：
    python step-04-github-deploy-add.py --devroot "D:/pjt/cursor/cs_py"
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 定位 py_lib
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def main():
    parser = argparse.ArgumentParser(description="Step 4: deploy 阶段 add")
    parser.add_argument("--devroot", default=None, help="Devroot 路径（默认自动探测）")
    args = parser.parse_args()

    # 加载 core 插件获取 git 路径和 devroot
    registry = load_plugins(devroot=args.devroot, tags=["core"])
    devroot = Path(registry.devroot)
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    if not git_exe.exists():
        print(f"[ERROR] 隔离 Git 未找到: {git_exe}")
        sys.exit(1)

    print("=" * 50)
    print("Step 4: deploy 阶段 add")
    print("=" * 50)
    print(f"[OK] 隔离 Git: {git_exe}")

    # git add -A
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "add", "-A"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"[FAIL] git add -A 失败: {result.stderr}")
        sys.exit(1)

    # git status --short
    print("\n--- Staged 文件 ---")
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "status", "--short"],
        capture_output=True, text=True, encoding="utf-8"
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    print("-" * 36)

    # git diff --cached --name-only
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", "--cached", "--name-only"],
        capture_output=True, text=True, encoding="utf-8"
    )
    staged = result.stdout.strip().splitlines()

    print(f"\n本次将提交的文件: {len(staged)} 个")
    for f in staged:
        print(f"  - {f}")

    print("\n[OK] Step 4 deploy-add 完成")


if __name__ == "__main__":
    main()
