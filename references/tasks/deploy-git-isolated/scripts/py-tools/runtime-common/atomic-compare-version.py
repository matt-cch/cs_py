#!/usr/bin/env python3
r"""
runtime-common/atomic-compare-version.py — 版本对比原子（v1.0.0）
标签：atomic, runtime
职责：比较本地版本与上游版本，输出可更新状态

用法：
    python atomic-compare-version.py --local-ver "26.3.1" --upstream-ver "26.4.0"
    python atomic-compare-version.py --local-ver "3.13.14" --upstream-ver "3.13.14"

输出（stdout JSON）：
    {"status":"outdated","local":"26.3.1","upstream":"26.4.0","message":"可更新: 26.3.1 → 26.4.0","need_update":true}
"""
import argparse
import json
import re
import sys
import atexit

# 编码处理闭环：保存原始编码 → 切换 UTF-8 → 退出时恢复
_original_stdout_encoding = sys.stdout.encoding
_original_stderr_encoding = sys.stderr.encoding

def _restore_encoding():
    try:
        if sys.stdout.encoding != _original_stdout_encoding:
            sys.stdout.reconfigure(encoding=_original_stdout_encoding)
    except Exception:
        pass
    try:
        if sys.stderr.encoding != _original_stderr_encoding:
            sys.stderr.reconfigure(encoding=_original_stderr_encoding)
    except Exception:
        pass

atexit.register(_restore_encoding)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# =============================================================================
# 版本对比
# =============================================================================

def normalize_version(ver: str) -> str:
    if not ver:
        return ""
    return ver.lstrip("v").strip()


def _to_sortable(ver: str):
    try:
        # 将字母序列替换为 .，保留字母前后的数字（如 2.55.0.windows.2 → 2.55.0.2）
        clean = re.sub(r'[a-zA-Z]+', '.', ver)
        # 合并连续的点并去掉首尾点
        clean = re.sub(r'\.+', '.', clean).strip('.')
        parts = clean.split('.')
        return tuple(int(p) for p in parts if p.isdigit())
    except Exception:
        return None


def compare_versions(local_ver: str, upstream_ver: str) -> dict:
    local = normalize_version(local_ver)
    upstream = normalize_version(upstream_ver)

    if not local and not upstream:
        return {"status": "unknown", "local": local_ver, "upstream": upstream_ver,
                "message": "本地和上游版本均未知", "need_update": False}
    if not upstream:
        return {"status": "unknown", "local": local_ver, "upstream": upstream_ver,
                "message": "上游查询失败，无法比较", "need_update": False}
    if not local:
        return {"status": "unknown", "local": local_ver, "upstream": upstream_ver,
                "message": "本地版本检测失败", "need_update": True}

    if local == upstream:
        return {"status": "up_to_date", "local": local, "upstream": upstream,
                "message": "已是最新版", "need_update": False}

    local_sort = _to_sortable(local)
    upstream_sort = _to_sortable(upstream)

    if upstream_sort and local_sort:
        if upstream_sort > local_sort:
            return {"status": "outdated", "local": local, "upstream": upstream,
                    "message": f"可更新: {local} → {upstream}", "need_update": True}
        else:
            return {"status": "local_newer", "local": local, "upstream": upstream,
                    "message": f"本地版本({local})高于上游({upstream})", "need_update": False}

    return {"status": "unknown", "local": local, "upstream": upstream,
            "message": f"版本格式不支持比较: {local} vs {upstream}", "need_update": False}


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="版本对比原子")
    parser.add_argument("--local-ver", default="", help="本地版本")
    parser.add_argument("--upstream-ver", default="", help="上游版本")
    args = parser.parse_args()

    result = compare_versions(args.local_ver, args.upstream_ver)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
