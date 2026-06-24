#!/usr/bin/env python3
"""
step-07-github-push.py — Step 7: Push to GitHub
标签：py-steps

职责：从 .env 读取 PAT，构造认证 URL 后 push 到 GitHub。
与 PS1 版对齐：直接 push 完整认证 URL，不修改 remote origin。

用法：
    python step-07-github-push.py --devroot "D:/pjt/cursor/cs_py"
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def _read_env_config(devroot: Path, require_pat: bool = False) -> dict:
    """与 PS1 Read-EnvConfig 对齐"""
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

    for key in ["GITHUB_USERNAME", "GITHUB_REPO_URL", "GIT_USER_NAME", "GIT_USER_EMAIL"]:
        if not env.get(key, "").strip():
            print(f"[ERROR] {key} 未在 .env 中配置")
            sys.exit(1)

    if require_pat:
        pat = env.get("GITHUB_PAT", "").strip()
        if not pat or pat == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
            print("[ERROR] GITHUB_PAT 未配置或仍是占位符。请填入真实 PAT。")
            sys.exit(1)

    return env


def main():
    parser = argparse.ArgumentParser(description="Step 7: Push to GitHub")
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
    print("Step 7: git push")
    print("=" * 40)

    cfg = _read_env_config(devroot, require_pat=True)
    repo_url = cfg["GITHUB_REPO_URL"].strip()
    username = cfg["GITHUB_USERNAME"].strip()
    pat = cfg["GITHUB_PAT"].strip()

    # 获取当前分支
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "branch", "--show-current"],
        capture_output=True, text=True, encoding="utf-8"
    )
    branch = result.stdout.strip()
    if not branch:
        print("[ERROR] 无法获取当前分支名")
        sys.exit(1)
    print(f"[OK] 当前分支: {branch}")

    # 构造认证 URL（与 PS1 对齐）
    # $repoPath = $cfg.RepoUrl -replace '^https://github.com/', ''
    # $authUrl = "https://$($cfg.Username):$($cfg.Pat)@github.com/$repoPath"
    repo_path = re.sub(r"^https://github.com/", "", repo_url)
    auth_url = f"https://{username}:{pat}@github.com/{repo_path}"

    print("正在 push 到 GitHub ...")
    # 【自动部署关键】阻止 Git Credential Manager (GCM) 弹窗
    # GCM_INTERACTIVE=0: 彻底禁用所有 GUI / TTY 交互
    # GCM_GUI_PROMPT=0: 禁用 GUI 弹窗（辅助）
    # GCM_PROVIDER=github: 跳过 provider 探测（加速）
    # GIT_TERMINAL_PROMPT=0: 禁用 Git 终端密码提示
    env = os.environ.copy()
    env["GCM_INTERACTIVE"] = "0"
    env["GCM_GUI_PROMPT"] = "0"
    env["GCM_PROVIDER"] = "github"
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "-c", "credential.helper=", "push", auth_url, branch],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")

    if result.returncode != 0:
        print(f"[FAIL] git push 失败 (exit {result.returncode})")
        sys.exit(1)

    print(f"[OK] push 成功: {repo_url} [{branch}]")


if __name__ == "__main__":
    main()
