#!/usr/bin/env python3
"""
get-timestamp.py — 时间戳生成 Workflow CLI（v1.1.0）
标签：py-tools

职责：通过 py_lib 加载 timestamp + time_source 插件，输出格式化时间字符串。
供 Agent 写入 .md / .json 等文件时调用，避免内嵌时间生成逻辑。

用法：
    # 默认输出当前时间的 local_iso
    python get-timestamp.py

    # 指定格式
    python get-timestamp.py --format utc_iso

    # 指定时间来源
    python get-timestamp.py --source "2026-06-21"
    python get-timestamp.py --source "2026-06-21T14:30:00" --format utc_long

    # 输出全部格式
    python get-timestamp.py --all

    # 以 JSON 输出（供脚本解析）
    python get-timestamp.py --json
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


def _get_plugins():
    """获取 timestamp 和 time_source 插件实例"""
    if HAS_PY_LIB:
        devroot = str(_SCRIPTS_DIR.parent.parent.parent.parent.resolve())
        registry = load_plugins(devroot=devroot)
        return registry.timestamp, registry.time_source
    else:
        import timestamp, time_source
        return timestamp, time_source


def main():
    parser = argparse.ArgumentParser(description="时间戳生成 Workflow CLI")
    parser.add_argument(
        "--format",
        default="local_iso",
        help="输出格式（默认: local_iso）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="输出全部格式",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="指定时间来源（默认: 当前时间）。支持 ISO 8601 格式，如 2026-06-21 或 2026-06-21T14:30:00",
    )
    args = parser.parse_args()

    ts_plugin, src_plugin = _get_plugins()

    # 解析时间来源
    dt_local, dt_utc = src_plugin.parse_time(args.source)

    # 格式化
    if args.source:
        ts = ts_plugin.format_timestamp(dt_local, dt_utc)
    else:
        ts = ts_plugin.get_now()

    if args.json:
        print(json.dumps(ts, ensure_ascii=False))
    elif args.all:
        for key, value in ts.items():
            print(f"{key}={value}")
    else:
        if args.format in ts:
            print(ts[args.format])
        else:
            print(f"[ERROR] 未知格式: {args.format}", file=sys.stderr)
            print(f"可用格式: {', '.join(ts.keys())}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
