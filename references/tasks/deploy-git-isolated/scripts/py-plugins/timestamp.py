#!/usr/bin/env python3
"""
插件：时间戳格式化器（v1.1.0）
标签：core, utility
依赖：time_source

职责：接收统一时间来源（time_source）输出的 datetime 对象，格式化为多种字符串格式。
本身不生成时间，只做格式化——时间来源由 time_source 统一管控。

支持格式：
┌──────────────┬──────────────────────┬─────────────────────────┐
│ 键名          │ 说明                 │ 示例                     │
├──────────────┼──────────────────────┼─────────────────────────┤
│ local_short   │ 本地日期（短）        │ 2026-06-21              │
│ local_long    │ 本地时间（长，紧凑）  │ 2026-06-21T143218       │
│ local_iso     │ 本地时间（ISO 扩展）  │ 2026-06-21T14:32:18     │
│ utc_short     │ UTC 日期（短）        │ 2026-06-21              │
│ utc_long      │ UTC 时间（长，紧凑）  │ 2026-06-21T063218Z      │
│ utc_iso       │ UTC 时间（ISO 扩展）  │ 2026-06-21T06:32:18Z    │
│ filename_safe │ 文件名安全格式        │ 2026-06-21-143218       │
└──────────────┴──────────────────────┴─────────────────────────┘

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["utility"])

    # 默认当前时间
    ts = registry.timestamp.get_now()
    print(ts["local_iso"])

    # 指定时间来源（通过 time_source 解析后传入）
    dt_local, dt_utc = registry.time_source.parse_time("2026-06-21T14:30:00")
    ts = registry.timestamp.format_timestamp(dt_local, dt_utc)
    print(ts["local_iso"])   # 2026-06-21T14:30:00

用法（CLI 直接执行）：
    python timestamp.py --format local_iso
    python timestamp.py --all
    python timestamp.py --source "2026-06-21" --format utc_short
"""
import argparse
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None


def format_timestamp(dt_local: datetime, dt_utc: datetime) -> dict:
    """
    将本地和 UTC datetime 对象格式化为多种字符串格式。

    参数:
        dt_local: 本地时间 datetime 对象
        dt_utc: UTC 时间 datetime 对象

    返回:
        dict，键见模块文档字符串中的格式表
    """
    return {
        "local_short": dt_local.strftime("%Y-%m-%d"),
        "local_long": dt_local.strftime("%Y-%m-%dT%H%M%S"),
        "local_iso": dt_local.strftime("%Y-%m-%dT%H:%M:%S"),
        "utc_short": dt_utc.strftime("%Y-%m-%d"),
        "utc_long": dt_utc.strftime("%Y-%m-%dT%H%M%SZ"),
        "utc_iso": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "filename_safe": dt_local.strftime("%Y-%m-%d-%H%M%S"),
    }


def get_now() -> dict:
    """
    【兼容方法】获取当前时间的多种格式化字符串。

    内部通过 time_source.parse_time() 获取统一时间来源后格式化。
    保留此方法以兼容现有调用代码。
    """
    # 通过 time_source 获取当前时间
    import time_source as _ts
    dt_local, dt_utc = _ts.parse_time()
    return format_timestamp(dt_local, dt_utc)


def _get_time_source():
    """获取 time_source 模块（优先通过 registry，fallback 直接 import）"""
    if __plugin_registry__ is not None:
        return __plugin_registry__.time_source
    import time_source as _ts
    return _ts


def _output_all(dt_local: datetime = None, dt_utc: datetime = None):
    """输出全部格式"""
    if dt_local is None or dt_utc is None:
        ts = get_now()
    else:
        ts = format_timestamp(dt_local, dt_utc)
    for key, value in ts.items():
        print(f"{key}={value}")


def _output_single(fmt: str, dt_local: datetime = None, dt_utc: datetime = None):
    """输出单一格式"""
    if dt_local is None or dt_utc is None:
        ts = get_now()
    else:
        ts = format_timestamp(dt_local, dt_utc)
    if fmt in ts:
        print(ts[fmt])
    else:
        print(f"[ERROR] 未知格式: {fmt}", file=sys.stderr)
        print(f"可用格式: {', '.join(ts.keys())}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="时间戳格式化器")
    parser.add_argument(
        "--format",
        default="local_iso",
        help="输出格式（默认: local_iso）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="输出全部格式（key=value 形式）",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="指定时间来源（默认: 当前时间）。支持 ISO 8601 格式",
    )
    args = parser.parse_args()

    # 解析时间来源
    ts_module = _get_time_source()
    dt_local, dt_utc = ts_module.parse_time(args.source)

    if args.all:
        _output_all(dt_local, dt_utc)
    else:
        _output_single(args.format, dt_local, dt_utc)


if __name__ == "__main__":
    main()
