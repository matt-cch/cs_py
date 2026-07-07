#!/usr/bin/env python3
r"""
atomic-check-staged-after-add.py — Staged 内容安全扫描原子工具
标签：py-tools

职责：在 git add 之后执行，强制扫描 staged 文件内容中的敏感模式。
      无 staged 文件时报错（说明 add 未生效或无可提交文件）。
      可作为独立 CLI 执行，也可被 workflow 编排调用。

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-staged-after-add.py" [--devroot "<目标仓库绝对路径>"]

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
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()

    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print("[Check Staged] 扫描 staged 文件敏感内容")
    print(f"{'='*50}")

    # 通过 py_lib 加载 git_staged_scan 插件
    registry = load_plugins(devroot=str(devroot), tags=["git"])

    result = registry.git_staged_scan.scan_staged_content(devroot)

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

    print("[Check Staged] ✅ 无敏感内容，允许 commit\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
