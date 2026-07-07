#!/usr/bin/env python3
r"""
atomic-git-preflight.py — Git Preflight 验证原子工具
标签：py-tools

职责：通过 py_lib 加载 git_preflight 插件，执行统一前置验证。
      可作为独立 CLI 执行，也可被上层 workflow 通过 subprocess 调用。

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-preflight.py" [--devroot "<目标仓库绝对路径>"] [--no-security]
    
    示例（检测其他仓库）：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-preflight.py" --devroot "D:\workspace\other-project"

返回：
    exit 0 = 验证通过
    exit 1 = 验证失败（含错误输出）
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
    parser = argparse.ArgumentParser(description="Git Preflight 验证")
    parser.add_argument("--devroot", default=None, help="Devroot 路径（默认使用当前工作目录）")
    parser.add_argument("--no-security", action="store_true", help="跳过安全扫描（仅检测环境）")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()

    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)

    # 通过 py_lib 加载 git_preflight 插件
    registry = load_plugins(devroot=str(devroot), tags=["git"])

    # 执行 check（验证失败自动 exit，但这里我们自己处理）
    ctx = registry.git_preflight.check(
        devroot=devroot,
        run_security=not args.no_security,
        exit_on_fail=False,
    )

    if not ctx.ok:
        sys.exit(1)

    # 演示 run_git 用法
    print("=" * 50)
    print("Git Preflight 通过，演示 run_git 调用")
    print("=" * 50)

    r = ctx.run_git(["status", "--short"])
    if r.stdout.strip():
        print("Git 状态（--short）:")
        print(r.stdout.strip())
    else:
        print("Working tree clean")

    print("\n[OK] atomic-git-preflight 完成")


if __name__ == "__main__":
    main()
