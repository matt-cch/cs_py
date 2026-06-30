#!/usr/bin/env python3
r"""
workflow-gh-preflight-demo.py — gh CLI preflight 验证 demo
标签：py-tools

职责：演示 gh_preflight 插件的使用方式。任何 gh 业务脚本都应以此为模板开头。

用法：
    & "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-preflight-demo.py"
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# py_lib 统一入口
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def main():
    # 1. 加载 gh_preflight 插件
    from py_lib import load_plugins
    registry = load_plugins(devroot=r"D:\pjt\cursor\cs_py", tags=["gh"])

    # 2. 执行 preflight（验证 gh.exe + PAT + 认证状态）
    ctx = registry.gh_preflight.check()

    # 3. preflight 通过后，ctx 包含所有需要的上下文
    print("=" * 50)
    print("gh CLI 业务逻辑演示")
    print("=" * 50)
    print(f"gh.exe: {ctx.gh_exe}")
    print(f"用户: {ctx.username}")
    print(f"仓库: {ctx.repo}")
    print()

    # 4. 使用 ctx.run_gh() 调用 gh CLI（自动注入 GH_TOKEN + GH_CONFIG_DIR）
    print("--- 查询最近 5 条 PR ---")
    r = ctx.run_gh(["pr", "list", "-L", "5"])
    print(r.stdout.strip() if r.stdout.strip() else "（无 open PR）")
    print()

    print("--- 查询最近 5 条 Issue ---")
    r = ctx.run_gh(["issue", "list", "-L", "5"])
    print(r.stdout.strip() if r.stdout.strip() else "（无 open Issue）")
    print()

    print("=" * 50)
    print("演示完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
