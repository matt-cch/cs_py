#!/usr/bin/env python3
r"""
workflow-git-security-demo.py — Git Security 本地配置改造验证
标签：py-tools

职责：验证 git_security.py 改造后，能正确读取各仓库根级的 git-security.json。
      扫描 cs_py 和 jywl-lab 两个仓库，输出配置来源和扫描结果。

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-security-demo.py" --devroot "${devroot}"
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 工具链根：CWD 入参确定后不再改变，Path.cwd() 是唯一可信参照物
_TOOLCHAIN_ROOT = Path.cwd()

_SCRIPTS_DIR = _TOOLCHAIN_ROOT / "references" / "tasks" / "deploy-git-isolated" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def scan_repo(path: Path, name: str, git_exe: Path = None):
    print(f"\n{'='*60}")
    print(f"[扫描] {name}")
    print(f"[路径] {path}")
    if git_exe:
        print(f"[git]  {git_exe}")
    print(f"{'='*60}")

    registry = load_plugins(devroot=str(path), tags=["git"])
    result = registry.git_security.scan_git_security(devroot=path, git_exe=git_exe)

    print(f"[结果] ok={result.ok}")
    print(f"[统计] violations={len(result.violations)}  warnings={len(result.warnings)}")

    if result.violations:
        print("[违规项]")
        for v in result.violations:
            print(f"  ! {v}")
    else:
        print("[违规项] 无")

    if result.warnings:
        print("[警告]")
        for w in result.warnings:
            print(f"  ~ {w}")


def main():
    parser = argparse.ArgumentParser(description="Git Security 本地配置改造验证")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径（必须显式传入）")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)

    # 工具链的隔离 git.exe
    toolchain_git = devroot / "venv" / "git" / "cmd" / "git.exe"

    # 扫描主仓库 cs_py（单仓库场景，工具链根与操作目标为同一目录）
    scan_repo(devroot, "cs_py (主仓库)")

    # 扫描嵌套 polyrepo jywl-lab（多仓库场景，工具链根与操作目标为不同目录）
    jywl_lab = devroot / "apps" / "repos" / "jywl-team" / "jywl-lab"
    if jywl_lab.exists():
        scan_repo(jywl_lab, "jywl-lab (嵌套 polyrepo)", git_exe=toolchain_git)
    else:
        print(f"\n[WARN] jywl-lab 不存在: {jywl_lab}")

    print(f"\n{'='*60}")
    print("[验证完成]")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
