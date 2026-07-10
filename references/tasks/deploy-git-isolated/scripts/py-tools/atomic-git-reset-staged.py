#!/usr/bin/env python3
r"""
atomic-git-reset-staged.py — deploy-git-isolated Git Staged 回滚原子 CLI
标签：py-tools
版本：v1.0.0

v1.0.0 设计意图：
  作为 git_reset.py 插件的 CLI 封装层，提供标准化的 staged 回滚入口。
  与 poly.py 的调用契约对齐：--devroot / --target / --git-exe 三参数化，
  支持单仓库与 polyrepo 两种场景。
  
  核心约束（与 baseline-principles.md §0.8.5 对齐）：
    - 禁止任何场景下现写 `git reset HEAD` 命令
    - 所有 staged 回滚必须通过本原子脚本执行
    - 操作前必须输出 staged 文件列表供审计
    - 操作后必须验证 staged 区是否真正清空
  
  调用链：
    workflow / 人类终端 → 本脚本（Layer 3）
      → py_lib.load_plugins()（Layer 2）
        → git_reset.reset_staged()（Layer 1）
          → _run_git("reset HEAD") → 审计 → 验证

职责：
  安全取消暂存区的全部 staged 文件（git reset HEAD）。
  仅取消暂存，不丢弃工作区修改。
  操作前输出 staged 文件列表供审计，操作后验证状态。
  可作为独立 CLI 执行，也可被 workflow 编排调用。

用法：
    # 单仓库
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-reset-staged.py" --devroot "${devroot}"

    # Polyrepo（target 与 devroot 不同，git-exe 在 devroot）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-reset-staged.py" --devroot "${devroot}" --target "${target}" --git-exe "${devroot}\venv\git\cmd\git.exe"

返回：
    exit 0 = 成功（或暂存区原本为空）
    exit 1 = 失败（git 命令错误或 reset 后仍有残留）
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
    parser = argparse.ArgumentParser(description="Git Staged 回滚（取消全部暂存，不丢弃工作区修改）")
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
    print("[Git Reset] 取消全部 staged 文件")
    print(f"{'='*50}")
    print(f"[Config] target: {target}")
    print(f"[Config] git.exe: {git_exe}")

    # 通过 py_lib 加载 git_reset 插件
    registry = load_plugins(devroot=str(devroot), tags=["git"])

    result = registry.git_reset.reset_staged(target, git_exe)

    if result.staged_files_before:
        print(f"[Audit] Reset 前 staged 文件 ({len(result.staged_files_before)} 个):")
        for f in result.staged_files_before:
            print(f"  - {f}")
    else:
        print("[Audit] Reset 前暂存区为空")

    if result.ok:
        print(f"[OK] {result.message}")
        sys.exit(0)
    else:
        print(f"[FAIL] {result.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
