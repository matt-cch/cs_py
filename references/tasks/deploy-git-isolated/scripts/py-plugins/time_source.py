#!/usr/bin/env python3
"""
插件：统一时间来源（v1.0.0）
标签：core, utility
依赖：无

职责：作为所有时间相关插件的单一时间来源。
- 默认返回当前本地时间与 UTC 时间
- 支持接收外部时间字符串（ISO 8601 或常见格式），解析后统一输出

解析规则：
1. source 为 None / 空字符串 → 返回 datetime.now() / datetime.now(timezone.utc)
2. source 为 ISO 8601 字符串 → 用 datetime.fromisoformat 解析
3. source 无时区信息 → 视为本地时间，自动推导 UTC
4. source 有时区信息 → 统一转换为本地 + UTC 两种表示

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["utility"])
    dt_local, dt_utc = registry.time_source.parse_time("2026-06-21T14:30:00")

用法（CLI 直接执行）：
    python time_source.py                    # 输出当前时间
    python time_source.py --source "2026-06-21"
    python time_source.py --source "2026-06-21T14:30:00"
"""
import argparse
import sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None


def parse_time(source: str = None):
    """
    解析时间来源字符串，返回 (dt_local, dt_utc) 二元组。

    参数:
        source: 时间字符串。None/空 → 当前时间；否则按 ISO 8601 或常见格式解析。

    返回:
        (datetime, datetime) — (本地时间, UTC 时间)

    异常:
        ValueError: 无法解析 source 时抛出
    """
    if source is None or (isinstance(source, str) and source.strip() == ""):
        now_local = datetime.now()
        now_utc = datetime.now(timezone.utc)
        return now_local, now_utc

    source = source.strip()

    # 1. 优先用 fromisoformat（Python 3.13 支持范围最广）
    try:
        dt = datetime.fromisoformat(source)
        if dt.tzinfo is None:
            # 无时区 → 视为本地时间
            dt_local = dt
            dt_utc = dt.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
        else:
            # 有时区 → 统一转换为本地 + UTC
            dt_utc = dt.astimezone(timezone.utc)
            dt_local = dt.astimezone()
        return dt_local, dt_utc
    except ValueError:
        pass

    # 2. fallback：逐格式尝试
    fallback_formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y/%m/%d %H:%M:%S",
    ]
    for fmt in fallback_formats:
        try:
            dt_local = datetime.strptime(source, fmt)
            dt_utc = dt_local.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
            return dt_local, dt_utc
        except ValueError:
            continue

    raise ValueError(
        f"无法解析时间字符串: {source!r}。"
        f"支持格式: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, "
        f"YYYY-MM-DD HH:MM:SS 等 ISO 8601 变体。"
    )


def main():
    parser = argparse.ArgumentParser(description="统一时间来源")
    parser.add_argument(
        "--source",
        default=None,
        help="时间来源字符串（默认: 当前时间）。支持 ISO 8601 格式",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出",
    )
    args = parser.parse_args()

    dt_local, dt_utc = parse_time(args.source)

    result = {
        "local_iso": dt_local.strftime("%Y-%m-%dT%H:%M:%S"),
        "utc_iso": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": args.source or "now",
    }

    if args.json:
        import json
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"local_iso={result['local_iso']}")
        print(f"utc_iso={result['utc_iso']}")
        print(f"source={result['source']}")


if __name__ == "__main__":
    main()
