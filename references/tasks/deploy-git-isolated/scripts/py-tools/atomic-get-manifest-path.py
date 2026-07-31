#!/usr/bin/env python3
r"""
atomic-get-manifest-path.py — 产物落盘路径查询原子 CLI（v1.0.0）
标签：py-tools

职责：通过 py_lib 加载 manifest_path 插件，查询产物应写入的目录或组装完整路径。
供 Agent/外部脚本直接调用，避免内嵌路径推算逻辑。

用法：
    # 查询目录（纯文本）
    python atomic-get-manifest-path.py --devroot "D:\pjt\cursor\cs_py"

    # 组装完整路径（纯文本）
    python atomic-get-manifest-path.py --devroot "D:\pjt\cursor\cs_py" --tool-name "workflow-download-article"

    # JSON 输出（供脚本解析）
    python atomic-get-manifest-path.py --devroot "D:\pjt\cursor\cs_py" --tool-name "foo" --json

    # 指定文件名参数
    python atomic-get-manifest-path.py --devroot "D:\pjt\cursor\cs_py" --tool-name "bar" --suffix "report" --ext "md" --json
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 优先通过 py_lib 加载插件
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from py_lib import load_plugins
    HAS_PY_LIB = True
except Exception as e:
    HAS_PY_LIB = False
    print(f"[WARN] py_lib 加载失败: {e}", file=sys.stderr)

# Fallback：直接 import 插件模块
if not HAS_PY_LIB:
    _PLUGINS_DIR = _SCRIPTS_DIR / "py-plugins"
    if str(_PLUGINS_DIR) not in sys.path:
        sys.path.insert(0, str(_PLUGINS_DIR))


def _get_plugin():
    """获取 manifest_path 插件实例"""
    if HAS_PY_LIB:
        devroot = str(_SCRIPTS_DIR.parent.parent.parent.parent.resolve())
        registry = load_plugins(devroot=devroot)
        return registry.manifest_path
    else:
        import manifest_path as _mp
        return _mp


def _resolve_devroot(devroot: str | None) -> Path:
    """解析 devroot 路径（默认从脚本位置向上推导 4 层）。"""
    if devroot:
        return Path(devroot).resolve()
    script_dir = Path(__file__).resolve().parent
    return script_dir.parents[3]


def main():
    parser = argparse.ArgumentParser(
        description="产物落盘路径查询原子 CLI"
    )
    parser.add_argument(
        "--devroot",
        default=None,
        help="devroot 路径（默认自动探测）",
    )
    parser.add_argument(
        "--tool-name",
        default=None,
        help="工具名（用于文件名，如 workflow-download-article）",
    )
    parser.add_argument(
        "--suffix",
        default="manifest",
        help="文件名中间段（默认: manifest）",
    )
    parser.add_argument(
        "--ext",
        default="json",
        help="扩展名（默认: json）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出（供脚本解析）",
    )
    args = parser.parse_args()

    devroot = _resolve_devroot(args.devroot)
    mp = _get_plugin()

    if args.tool_name:
        manifest_path = mp.build_manifest_path(
            devroot,
            tool_name=args.tool_name,
            suffix=args.suffix,
            ext=args.ext,
        )
        if args.json:
            print(
                json.dumps(
                    {
                        "dir": str(manifest_path.parent),
                        "path": str(manifest_path),
                        "filename": manifest_path.name,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(str(manifest_path))
    else:
        manifest_dir = mp.get_manifest_dir(devroot)
        if args.json:
            print(json.dumps({"dir": str(manifest_dir)}, ensure_ascii=False))
        else:
            print(str(manifest_dir))


if __name__ == "__main__":
    main()
