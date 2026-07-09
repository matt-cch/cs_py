#!/usr/bin/env python3
"""
插件：Session ID 检测（Session ID Detector）
标签：core

职责：从 OpenCode 日志文件名中提取当前 Agent Chat Session 的唯一标识（时间戳）。
      扫描 venv/data-opencode/opencode/log/*.log，取时间戳最大的文件名作为当前 session-id。

用法（同层插件直接 import）：
    from session_id import detect_session_id
    sid = detect_session_id(Path("${devroot}"))

用法（CLI 直接执行）：
    python session_id.py --devroot "D:/pjt/cursor/cs_py"
"""
import argparse
import re
import sys
from pathlib import Path


def detect_session_id(toolchain_root: Path) -> str:
    """
    检测当前 OpenCode session 的 session-id。

    扫描 toolchain_root/venv/data-opencode/opencode/log/*.log，
    提取文件名中的时间戳（YYYY-MM-DDTHHMMSS），返回最大值。

    参数:
        toolchain_root: 工具链根目录绝对路径

    返回:
        str: session-id（如 "2026-07-08T143052"）

    异常:
        RuntimeError: 未找到日志文件
    """
    log_dir = toolchain_root / "venv" / "data-opencode" / "opencode" / "log"
    if not log_dir.exists():
        raise RuntimeError(f"OpenCode 日志目录不存在: {log_dir}")

    # 只匹配 YYYY-MM-DDTHHMMSS.log 格式
    _SESSION_LOG_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{6}$")
    log_files = [
        f for f in log_dir.iterdir()
        if f.is_file() and f.suffix == ".log" and _SESSION_LOG_PATTERN.match(f.stem)
    ]
    if not log_files:
        raise RuntimeError(f"OpenCode 日志目录中无有效 session 日志: {log_dir}")

    # 按文件名排序（时间戳格式 YYYY-MM-DDTHHMMSS 可字典序比较）
    latest = max(log_files, key=lambda f: f.stem)
    session_id = latest.stem
    return session_id


def main() -> int:
    parser = argparse.ArgumentParser(description="检测当前 OpenCode Session ID")
    parser.add_argument("--devroot", default=None, help="工具链根目录（默认使用当前工作目录）")
    args = parser.parse_args()

    toolchain_root = Path(args.devroot) if args.devroot else Path.cwd()
    if not toolchain_root.exists():
        print(f"[ERROR] 目录不存在: {toolchain_root}", file=sys.stderr)
        return 1

    try:
        sid = detect_session_id(toolchain_root)
        print(sid)
        return 0
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
