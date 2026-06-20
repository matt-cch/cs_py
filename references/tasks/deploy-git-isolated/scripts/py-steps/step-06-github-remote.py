#!/usr/bin/env python3
"""
step-06-github-remote.py — Step 6: Remote Configuration
标签：py-steps

职责：从 .env 读取 GITHUB_REPO_URL，添加为 origin remote。
与 PS1 版对齐：Read-EnvConfig 严格校验；remote 存在则 SKIP。

用法：
    python step-06-github-remote.py --devroot "D:/pjt/cursor/cs_py"
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


def _read_env_config(devroot: Path) -> dict:
    """与 PS1 Read-EnvConfig 对齐：严格校验必填项"""
    env = {}
    env_path = devroot / ".env"
    if not env_path.exists():
        print("[ERROR] .env 文件不存在")
        sys.exit(1)

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env[key] = val

    # 严格校验（与 PS1 Read-EnvConfig 对齐）
    for key in ["GITHUB_USERNAME", "GITHUB_REPO_URL", "GIT_USER_NAME", "GIT_USER_EMAIL"]:
        if not env.get(key, "").strip():
            print(f"[ERROR] {key} 未在 .env 中配置")
            sys.exit(1)

    return env


def main():
    parser = argparse.ArgumentParser(description="Step 6: Remote Configuration")
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
    print("Step 6: 添加 remote")
    print("=" * 40)

    cfg = _read_env_config(devroot)
    repo_url = cfg["GITHUB_REPO_URL"].strip()

    # 检查是否已有 remote（与 PS1 对齐）
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "remote", "-v"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.stdout.strip():
        print("[SKIP] remote 已存在:")
        print(result.stdout, end="")
    else:
        result = subprocess.run(
            [str(git_exe), "-C", str(devroot), "remote", "add", "origin", repo_url],
            capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode != 0:
            print(f"[FAIL] remote add 失败: {result.stderr}")
            sys.exit(1)
        print(f"[OK] remote add origin {repo_url}")


if __name__ == "__main__":
    main()
