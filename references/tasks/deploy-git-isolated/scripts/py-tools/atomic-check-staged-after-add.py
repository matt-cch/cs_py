#!/usr/bin/env python3
r"""
atomic-check-staged-after-add.py — Staged 内容安全扫描原子工具
标签：py-tools

职责：在 git add 之后执行，强制扫描 staged 文件内容中的敏感模式。
      无 staged 文件时报错（说明 add 未生效或无可提交文件）。
      可作为独立 CLI 执行，也可被 workflow 编排调用。

用法：
    # 单仓库（默认 devroot=target=git-exe 推导）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-staged-after-add.py" --devroot "${devroot}"

    # Polyrepo（target 与 devroot 不同，git-exe 在 devroot）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-staged-after-add.py" --devroot "${devroot}" --target "${target}" --git-exe "${devroot}\venv\git\cmd\git.exe"

返回：
    exit 0 = 无敏感内容
    exit 1 = 无 staged 文件 或 发现敏感内容
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def main():
    parser = argparse.ArgumentParser(description="Staged 内容安全扫描（必须在 git add 后执行）")
    parser.add_argument("--devroot", default=None, help="Devroot 路径（默认使用当前工作目录）")
    parser.add_argument("--target", default=None, help="操作目标仓库路径（polyrepo 场景，默认等于 --devroot）")
    parser.add_argument("--git-exe", default=None, help="隔离 git.exe 绝对路径（默认从 devroot 推导）")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()
    target = Path(args.target) if args.target else devroot
    git_exe = Path(args.git_exe) if args.git_exe else (devroot / "venv" / "git" / "cmd" / "git.exe")

    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)
    if not target.exists():
        print(f"[ERROR] target 不存在: {target}")
        sys.exit(1)
    if not git_exe.exists():
        print(f"[ERROR] git.exe 不存在: {git_exe}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print("[Check Staged] 扫描 staged 文件敏感内容")
    print(f"{'='*50}")
    print(f"[Config] target: {target}")
    print(f"[Config] git.exe: {git_exe}")

    # 通过 py_lib 加载 git_staged_scan 插件
    registry = load_plugins(devroot=str(devroot), tags=["git"])

    result = registry.git_staged_scan.scan_staged_content(target, git_exe)

    if not result.staged_files:
        print("[FAIL] 无 staged 文件")
        print("[HINT] 请确认已执行 git add，或无可提交文件")
        sys.exit(1)

    print(f"[OK] 发现 {len(result.staged_files)} 个 staged 文件")
    for f in result.staged_files:
        print(f"  - {f}")

    if result.violations:
        print(f"\n[FAIL] 发现 {len(result.violations)} 处敏感内容:")
        for v in result.violations:
            print(f"  ! {v}")
        print("\n[Check Staged] 扫描失败，禁止 commit\n")
        sys.exit(1)

    print("[Check Staged] 无敏感内容，允许 commit\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
