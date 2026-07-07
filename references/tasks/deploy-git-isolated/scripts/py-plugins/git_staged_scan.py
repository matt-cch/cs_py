#!/usr/bin/env python3
r"""
插件：Git Staged 扫描（Git Staged Scan）
标签：git, validation
依赖：constants

职责：扫描已 staged 文件内容中的敏感模式（API key、PAT、私钥等）。
      必须在 git add 后执行，否则无 staged 文件可扫描。

用法（同层插件直接 import）：
    from git_staged_scan import scan_staged_content
    result = scan_staged_content(Path(r"D:\pjt\cursor\cs_py"), git_exe)
    if result.violations:
        print("staged 文件包含敏感内容，禁止 commit")
"""
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

__plugin_registry__ = None  # 由 py_lib.py 注入


@dataclass
class StagedScanResult:
    """staged 扫描结果。"""
    ok: bool = False
    violations: list = field(default_factory=list)
    staged_files: list = field(default_factory=list)


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


def scan_staged_content(devroot: Path, git_exe: Path = None) -> StagedScanResult:
    """
    扫描 staged 文件内容中的敏感模式。

    参数:
        devroot: 开发根目录绝对路径
        git_exe: 可选，git 可执行文件路径

    返回:
        StagedScanResult
    """
    result = StagedScanResult()

    if git_exe is None:
        git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        result.violations.append(f"git.exe 不存在: {git_exe}")
        return result

    # 获取 staged 文件列表
    r = _run_git(git_exe, ["diff", "--cached", "--name-only"], devroot)
    staged = [f.strip() for f in r.stdout.splitlines() if f.strip()]
    result.staged_files = staged

    if not staged:
        # 无 staged 文件时返回 ok=True（这不是违规，只是无事可做）
        result.ok = True
        return result

    # 扫描每个 staged 文件内容
        for filepath in staged:
            fpath = devroot / filepath
            if not fpath.exists():
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # 通过 constants 唯一真源扫描
            from constants import scan_sensitive_content
            result.violations.extend(scan_sensitive_content(content, filepath))

    result.ok = len(result.violations) == 0
    return result
