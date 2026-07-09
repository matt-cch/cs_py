#!/usr/bin/env python3
r"""
atomic-polyrepo-context-manifest.py — Polyrepo 上下文 manifest 生成原子工具
标签：py-tools

职责：从 toolchain_root + target 构造 PolyrepoContext，序列化到 manifest 文件。
      被 workflow-git-deploy-full-poly 在 Step 0c 调用，workflow 本身不感知 plugin。

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-polyrepo-context-manifest.py" --devroot "<工具链根>" [--target "<操作目标>"]

输出：
    stdout: manifest 文件绝对路径
    exit 0 = 成功
    exit 1 = 失败
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# polyrepo_context 在 py-plugins/ 下，需要确保 plugins 目录在 path 中
_PY_PLUGINS_DIR = _SCRIPTS_DIR / "py-plugins"
if str(_PY_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PY_PLUGINS_DIR))


def main():
    parser = argparse.ArgumentParser(description="Polyrepo 上下文 manifest 生成")
    parser.add_argument("--devroot", default=None, help="工具链根路径（默认使用当前工作目录）")
    parser.add_argument("--target", default=None, help="操作目标仓库路径（默认等于 --devroot）")
    args = parser.parse_args()

    toolchain_root = Path(args.devroot) if args.devroot else Path.cwd()
    target = Path(args.target) if args.target else toolchain_root

    if not toolchain_root.exists():
        print(f"[ERROR] devroot 不存在: {toolchain_root}", file=sys.stderr)
        sys.exit(1)
    if not target.exists():
        print(f"[ERROR] target 不存在: {target}", file=sys.stderr)
        sys.exit(1)

    try:
        # 只有 atomic 内部才允许 import plugin
        from polyrepo_context import PolyrepoContext
        ctx = PolyrepoContext.from_args(toolchain_root=toolchain_root, target=target)
        manifest_path = ctx.persist()
        print(manifest_path)
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] manifest 生成失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
