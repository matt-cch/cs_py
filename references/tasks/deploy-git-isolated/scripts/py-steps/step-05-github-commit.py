#!/usr/bin/env python3
"""
step-05-github-commit.py — Step 5: Commit
标签：py-steps

职责：提交 staged 文件，使用标准 init commit message。
与 PS1 版对齐：直接 commit，不检查 staged 文件是否存在，不配置 git identity。

用法：
    python step-05-github-commit.py --devroot "D:/pjt/cursor/cs_py" --message "init: empty scaffold with safety gitignore"
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


def _read_env(devroot: Path) -> dict:
    env = {}
    env_path = devroot / ".env"
    if not env_path.exists():
        return env
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env[key] = val
    return env


def main():
    parser = argparse.ArgumentParser(description="Step 5: Commit")
    parser.add_argument("--devroot", default=None, help="Devroot 路径")
    parser.add_argument(
        "--message",
        default="init: empty scaffold with safety gitignore",
        help="Commit message"
    )
    args = parser.parse_args()

    registry = load_plugins(devroot=args.devroot, tags=["core"])
    devroot = Path(registry.devroot)
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    if not git_exe.exists():
        print(f"[ERROR] 隔离 Git 未找到: {git_exe}")
        sys.exit(1)

    print("")
    print("=" * 40)
    print("Step 5: git commit")
    print("=" * 40)
    print(f"[OK] 隔离 Git: {git_exe}")

    # 与 PS1 对齐：直接 commit，不检查 staged，不配置 identity
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "commit", "-m", args.message],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")

    if result.returncode != 0:
        print(f"[FAIL] git commit 失败 (exit {result.returncode})")
        sys.exit(1)

    print(f"[OK] commit 完成: {args.message}")


if __name__ == "__main__":
    main()
