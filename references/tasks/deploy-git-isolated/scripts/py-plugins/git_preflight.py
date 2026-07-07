#!/usr/bin/env python3
r"""
插件：Git Preflight 编排（Git Preflight）
标签：git, preflight
依赖：git_env, git_security, constants, env_config

职责：为所有 Git 业务脚本提供统一的前置验证，整合环境检测 + 安全扫描。
      提供 verify()（仅验证不退出）和 check()（验证失败自动退出）两种入口。
      返回 GitContext（含 run_git 方法，自动使用隔离 git.exe）。

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["git"])
    ctx = registry.git_preflight.check()
    r = ctx.run_git(["status"])
"""
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

__plugin_registry__ = None  # 由 py_lib.py 注入


@dataclass
class GitContext:
    """Git 运行上下文，preflight 验证通过后返回给业务脚本使用。"""
    ok: bool = False
    git_exe: Path = None
    devroot: Path = None
    user_name: str = ""
    user_email: str = ""
    current_branch: str = ""
    is_clean: bool = False
    has_repo: bool = False
    env: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def run_git(self, args: list, cwd: Path = None, check: bool = False) -> subprocess.CompletedProcess:
        """
        在已验证的隔离环境下调用 git.exe。
        自动使用 devroot 作为工作目录（除非显式覆盖）。

        参数:
            args: git 子命令参数列表，如 ["status", "--short"]
            cwd: 可选，覆盖工作目录。默认使用 self.devroot
            check: 是否启用 subprocess.run(check=check)
            **kwargs: 其他 subprocess.run 参数

        返回:
            subprocess.CompletedProcess
        """
        target_cwd = cwd if cwd else self.devroot
        cmd = [str(self.git_exe)] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(target_cwd),
            check=check,
        )


def _print_banner(title: str, width: int = 50):
    print(f"\n{'='*width}")
    print(f"[Git Preflight] {title}")
    print(f"{'='*width}")


def verify(devroot: Path = None, run_security: bool = True) -> GitContext:
    """
    执行 Git 前置验证，返回 GitContext（不自动退出）。

    参数:
        devroot: 开发根目录。如未传入，尝试从 registry 或环境变量获取。
        run_security: 是否执行安全扫描（默认 True）

    返回:
        GitContext: 验证结果。ok=True 表示全部通过。
    """
    ctx = GitContext()

    # 1. 确定 devroot
    if devroot is None:
        if __plugin_registry__ is not None and hasattr(__plugin_registry__, "devroot"):
            devroot = Path(__plugin_registry__.devroot)
        else:
            devroot_str = os.environ.get("DEVROOT", r"D:\pjt\cursor\cs_py")
            devroot = Path(devroot_str)
    else:
        devroot = Path(devroot)
    ctx.devroot = devroot

    # 2. 加载 env_config 插件读取 .env
    try:
        from env_config import read_env
        ctx.env = read_env(str(devroot / ".env"))
    except Exception as e:
        ctx.errors.append(f".env 读取失败: {e}")
        return ctx

    # 3. 调用 git_env 插件检测环境
    try:
        from git_env import detect_git_env
        env_result = detect_git_env(devroot)
    except Exception as e:
        ctx.errors.append(f"git_env 检测异常: {e}")
        return ctx

    if not env_result.ok:
        ctx.errors.extend(env_result.errors)
        ctx.warnings.extend(env_result.warnings)
        return ctx

    ctx.git_exe = env_result.git_exe
    ctx.user_name = env_result.user_name
    ctx.user_email = env_result.user_email
    ctx.current_branch = env_result.current_branch
    ctx.is_clean = env_result.is_clean
    ctx.has_repo = env_result.has_repo
    ctx.warnings.extend(env_result.warnings)

    # 4. 检查 .env 中必要变量
    required_env = ["GIT_USER_NAME", "GIT_USER_EMAIL"]
    for key in required_env:
        if not ctx.env.get(key, "").strip():
            ctx.errors.append(f".env 中 {key} 未配置")

    # 5. 安全扫描（可选）
    if run_security:
        try:
            from git_security import scan_git_security
            sec_result = scan_git_security(devroot, git_exe=ctx.git_exe)
        except Exception as e:
            ctx.errors.append(f"git_security 扫描异常: {e}")
            return ctx

        if not sec_result.ok:
            ctx.errors.extend(sec_result.violations)
        ctx.warnings.extend(sec_result.warnings)

    ctx.ok = len(ctx.errors) == 0
    return ctx


def check(devroot: Path = None, run_security: bool = True, exit_on_fail: bool = True) -> GitContext:
    """
    执行 Git 前置验证，打印状态，可选失败时自动退出。

    这是业务脚本的推荐入口——直接调用，验证通过即获得可用上下文。

    参数:
        devroot: 开发根目录
        run_security: 是否执行安全扫描（默认 True）
        exit_on_fail: 验证失败时是否 sys.exit(1)

    返回:
        GitContext: 验证通过的上下文（含 run_git 方法）
    """
    _print_banner("前置验证")

    ctx = verify(devroot, run_security=run_security)

    # 打印结果
    print(f"[{'OK' if ctx.ok else 'FAIL'}] git.exe: {ctx.git_exe}")
    print(f"[{'OK' if ctx.ok else 'FAIL'}] devroot: {ctx.devroot}")
    if ctx.user_name:
        print(f"[OK] user.name: {ctx.user_name}")
    if ctx.user_email:
        print(f"[OK] user.email: {ctx.user_email}")
    if ctx.has_repo:
        print(f"[OK] 当前分支: {ctx.current_branch or '(无分支)'}")
        print(f"[OK] working tree: {'clean' if ctx.is_clean else 'dirty'}")
    else:
        print("[WARN] 无 git 仓库")
    for w in ctx.warnings:
        print(f"[WARN] {w}")
    for e in ctx.errors:
        print(f"[FAIL] {e}")

    if not ctx.ok:
        print("\n[Git Preflight] 验证失败，终止执行\n")
        if exit_on_fail:
            sys.exit(1)
    else:
        print("[Git Preflight] 全部通过\n")

    return ctx
