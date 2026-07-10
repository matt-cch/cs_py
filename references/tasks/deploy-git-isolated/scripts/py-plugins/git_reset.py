#!/usr/bin/env python3
r"""
git_reset.py — deploy-git-isolated Git Reset 封装插件
标签：py-plugins
dependencies: none
tags: ["git", "core"]
版本：v1.0.0

v1.0.0 设计意图：
  Git 的 `reset` 命令是高风险操作族（`--hard` 可瞬间丢弃工作区修改）。
  本项目在多次 session 中反复出现"现写 `git reset HEAD` 命令"的临时操作，
  存在以下系统性风险：
    1. 参数偏差：Agent 或人类手误写成 `git reset --hard HEAD`，工作区修改全部丢失
    2. 目标错配：polyrepo 场景下在错误仓库执行 reset，导致不相关的 staged 被清空
    3. 无审计：现写命令不输出 reset 前的 staged 文件列表，事后无法追溯
    4. 无验证：reset 后不做二次确认，残留 staged 文件未被察觉
  
  本插件通过三层封装彻底消除上述风险：
    - Layer 1（本插件）：锁定 `reset HEAD`（无 `--hard`），操作前审计、操作后验证
    - Layer 2（py_lib）：统一入口加载，确保 registry 隔离
    - Layer 3（atomic-git-reset-staged.py）：CLI 参数化，支持 --target/--git-exe polyrepo 契约
  
  铁律：任何 staged 回滚操作必须通过 atomic-git-reset-staged.py 执行，
        禁止任何场景下现写 `git reset` 命令。

职责：
  提供 git reset HEAD 的底层封装，取消暂存区的全部 staged 文件。
  操作前记录 staged 文件列表，操作后验证状态。
  仅取消暂存（unstage），不丢弃工作区修改。

用法（同层插件直接 import）：
    from git_reset import reset_staged
    result = reset_staged(Path(r"D:\pjt\cursor\cs_py"), git_exe)
    if result.ok:
        print(f"已取消 {len(result.staged_files_before)} 个文件的暂存")
"""
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

__plugin_registry__ = None  # 由 py_lib.py 注入


@dataclass
class ResetResult:
    """reset 操作结果。"""
    ok: bool = False
    staged_files_before: list = field(default_factory=list)
    staged_files_after: list = field(default_factory=list)
    message: str = ""


def _run_git(git_exe: Path, args: list, cwd: Path) -> subprocess.CompletedProcess:
    """执行 git 命令。"""
    cmd = [str(git_exe)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
    )


def reset_staged(devroot: Path, git_exe: Path = None) -> ResetResult:
    """
    执行 git reset HEAD，取消全部 staged 文件。

    参数:
        devroot: 开发根目录绝对路径
        git_exe: 可选，git 可执行文件路径

    返回:
        ResetResult
    """
    result = ResetResult()

    if git_exe is None:
        git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        result.message = f"git.exe 不存在: {git_exe}"
        return result

    # 1. 记录 reset 前的 staged 文件
    r = _run_git(git_exe, ["diff", "--cached", "--name-only"], devroot)
    result.staged_files_before = [f.strip() for f in r.stdout.splitlines() if f.strip()]

    if not result.staged_files_before:
        result.ok = True
        result.message = "暂存区为空，无需 reset"
        return result

    # 2. 执行 reset HEAD（取消暂存，不丢弃工作区修改）
    r = _run_git(git_exe, ["reset", "HEAD"], devroot)
    if r.returncode != 0:
        result.message = f"git reset HEAD 失败: {r.stderr.strip()[:200]}"
        return result

    # 3. 验证 reset 后的状态
    r = _run_git(git_exe, ["diff", "--cached", "--name-only"], devroot)
    result.staged_files_after = [f.strip() for f in r.stdout.splitlines() if f.strip()]

    result.ok = len(result.staged_files_after) == 0
    if result.ok:
        result.message = f"已取消 {len(result.staged_files_before)} 个文件的暂存"
    else:
        result.message = f"reset 后仍有 {len(result.staged_files_after)} 个 staged 文件"

    return result
