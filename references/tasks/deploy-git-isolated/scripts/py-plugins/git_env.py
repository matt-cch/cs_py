#!/usr/bin/env python3
r"""
插件：Git 环境基础检测（Git Env）
标签：git, core
依赖：constants

职责：提供 Git 环境的基础检测能力，包括 exe 存在性、
      身份配置、当前分支、工作区状态等。被 git_preflight 插件编排调用，
      也可被同层其他 git 相关插件直接 import。

用法（同层插件直接 import）：
    from git_env import detect_git_env
    result = detect_git_env(Path(r"D:\pjt\cursor\cs_py"))
    if result.ok:
        print(result.git_exe, result.user_name, result.current_branch)
"""
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

__plugin_registry__ = None  # 由 py_lib.py 注入


@dataclass
class GitEnvResult:
    """Git 环境检测结果。"""
    ok: bool = False
    git_exe: Path = None
    user_name: str = ""
    user_email: str = ""
    current_branch: str = ""
    is_clean: bool = False  # working tree clean?
    has_repo: bool = False  # devroot 下是否有 .git/
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def _run_git(git_exe: Path, args: list, cwd: Path = None) -> subprocess.CompletedProcess:
    """调用 git.exe，可选指定工作目录。"""
    cmd = [str(git_exe)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd) if cwd else None,
    )


def detect_git_env(devroot: Path) -> GitEnvResult:
    """
    检测 Git 环境基础状态。

    参数:
        devroot: 开发根目录绝对路径

    返回:
        GitEnvResult: 检测结果，ok=True 表示全部通过
    """
    result = GitEnvResult()

    # 1. 检查 git.exe
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        result.errors.append(f"git.exe 不存在: {git_exe}")
        return result
    result.git_exe = git_exe

    # 2. 验证 git --version
    r = _run_git(git_exe, ["--version"])
    if r.returncode != 0:
        result.errors.append(f"git --version 执行失败: {r.stderr.strip()}")
        return result

    # 3. 检测是否有仓库
    git_dir = devroot / ".git"
    result.has_repo = git_dir.exists()

    if result.has_repo:
        # 4a. 读取身份（不指定 scope，Git 按 local > global > system 解析）
        r_name = _run_git(git_exe, ["-C", str(devroot), "config", "user.name"])
        r_email = _run_git(git_exe, ["-C", str(devroot), "config", "user.email"])
        result.user_name = r_name.stdout.strip() if r_name.returncode == 0 else ""
        result.user_email = r_email.stdout.strip() if r_email.returncode == 0 else ""

        if not result.user_name:
            result.errors.append("git user.name 未配置")
        if not result.user_email:
            result.errors.append("git user.email 未配置")

        # 4b. 当前分支
        r = _run_git(git_exe, ["-C", str(devroot), "branch", "--show-current"])
        result.current_branch = r.stdout.strip() if r.returncode == 0 else ""

        # 4c. working tree 是否 clean
        r = _run_git(git_exe, ["-C", str(devroot), "status", "--porcelain"])
        result.is_clean = r.returncode == 0 and not r.stdout.strip()
    else:
        result.warnings.append("devroot 下无 .git/，跳过分支、身份和工作区检测")

    result.ok = len(result.errors) == 0
    return result


def check_git_exe(devroot: Path) -> bool:
    """仅检查 git.exe 是否存在。"""
    return (devroot / "venv" / "git" / "cmd" / "git.exe").exists()
