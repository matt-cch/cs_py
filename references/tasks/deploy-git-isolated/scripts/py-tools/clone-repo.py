#!/usr/bin/env python3
r"""
clone-repo.py — 隔离环境 Git Clone + Local 身份配置

职责：
  1. 使用 venv/git 隔离工具链 clone 远程仓库到指定路径
  2. 自动为新 repo 设置 --local user.name / user.email
  3. 所有操作使用绝对路径，不依赖 Terminal CWD

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\clone-repo.py" `
        --url "https://github.com/jywl-team/jywl-lab.git" `
        --target "${devroot}\apps\repos\jywl-team\jywl-lab" `
        --user-name "matt-cch" `
        --user-email "chorefie@139.com"

参数：
    --url       远程仓库 HTTPS URL
    --target    本地 clone 目标绝对路径（父目录自动创建）
    --user-name 新 repo 的 git local user.name（可选，默认从 devroot .git/config 读取）
    --user-email 新 repo 的 git local user.email（可选，默认从 devroot .git/config 读取）
"""
import argparse
import configparser
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


DEVROOT = Path(r"D:\pjt\cursor\cs_py")
GIT_EXE = DEVROOT / "venv" / "git" / "cmd" / "git.exe"
DEVROOT_GIT_CONFIG = DEVROOT / ".git" / "config"


def _read_devroot_identity() -> tuple[str, str]:
    """从 devroot .git/config 读取 local user.name / user.email 作为默认值。"""
    name = email = ""
    if DEVROOT_GIT_CONFIG.exists():
        cp = configparser.ConfigParser()
        cp.read(DEVROOT_GIT_CONFIG, encoding="utf-8")
        if "user" in cp.sections():
            name = cp.get("user", "name", fallback="")
            email = cp.get("user", "email", fallback="")
    return name, email


def _run_git(args: list, check: bool = True, **kwargs) -> subprocess.CompletedProcess:
    """使用隔离 git 执行命令，stdout 编码 utf-8。"""
    cmd = [str(GIT_EXE)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=check,
        **kwargs,
    )


def main():
    parser = argparse.ArgumentParser(description="隔离环境 Git Clone + Local 身份配置")
    parser.add_argument("--url", required=True, help="远程仓库 HTTPS URL")
    parser.add_argument("--target", required=True, help="本地 clone 目标绝对路径")
    parser.add_argument("--user-name", default=None, help="新 repo 的 git local user.name")
    parser.add_argument("--user-email", default=None, help="新 repo 的 git local user.email")
    args = parser.parse_args()

    target = Path(args.target)
    default_name, default_email = _read_devroot_identity()
    user_name = args.user_name or default_name or ""
    user_email = args.user_email or default_email or ""

    if not user_name or not user_email:
        print("[FAIL] 未提供 user-name/user-email，且无法从 devroot .git/config 读取", file=sys.stderr)
        sys.exit(1)

    # 1. 确保父目录存在
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"[OK] 父目录就绪: {target.parent}")

    # 2. Clone（直接指定目标绝对路径，不需要 -C）
    print(f"[INFO] Clone {args.url} -> {target}")
    r = _run_git(["clone", args.url, str(target)], check=False)
    if r.returncode != 0:
        print(f"[FAIL] git clone 失败:\n{r.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"[OK] Clone 完成: {target}")

    # 3. 设置 --local 身份（使用 -C 方案，不改变当前进程目录）
    print(f"[INFO] 配置 local identity: {user_name} <{user_email}>")
    for key, val in [("user.name", user_name), ("user.email", user_email)]:
        r = _run_git(["-C", str(target), "config", "--local", key, val], check=False)
        if r.returncode != 0:
            print(f"[FAIL] git config --local {key} 失败:\n{r.stderr}", file=sys.stderr)
            sys.exit(1)
    print("[OK] Local identity 配置完成")

    # 4. 验证
    r = _run_git(["-C", str(target), "config", "--local", "user.name"], check=False)
    verified_name = r.stdout.strip() if r.returncode == 0 else ""
    r = _run_git(["-C", str(target), "config", "--local", "user.email"], check=False)
    verified_email = r.stdout.strip() if r.returncode == 0 else ""

    print("=" * 50)
    print("Clone 结果验证")
    print("=" * 50)
    print(f"  目标路径: {target}")
    print(f"  .git 存在: {(target / '.git').exists()}")
    print(f"  user.name:  {verified_name}")
    print(f"  user.email: {verified_email}")
    print("=" * 50)

    if not verified_name or not verified_email:
        print("[WARN] 身份验证失败，请手动检查", file=sys.stderr)
        sys.exit(1)

    print("[OK] 全部完成")


if __name__ == "__main__":
    main()
