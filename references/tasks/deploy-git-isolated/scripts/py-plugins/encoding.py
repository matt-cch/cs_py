#!/usr/bin/env python3
"""
插件：编码处理（Encoding）
标签：core

职责：处理 Python 脚本在 Agent bash 调用时的 stdout 编码问题，
      提供编码切换与恢复机制（对称于 PS 的 Switch-ToUtf8 / Restore-Encoding）。

用法：
    from plugins.encoding import EncodingGuard
    
    with EncodingGuard():
        print("中文正常输出")
    # 退出 with 块后自动恢复原始编码
"""
import sys


class EncodingGuard:
    """
    编码上下文管理器。
    
    进入时强制 stdout 为 UTF-8，退出时恢复原始编码。
    类似 PS 的 $originalConsoleEncoding / Restore-Encoding 机制。
    """

    def __init__(self, encoding="utf-8"):
        self.target_encoding = encoding
        self._original_encoding = None
        self._original_stdout = None

    def __enter__(self):
        try:
            self._original_encoding = sys.stdout.encoding
            self._original_stdout = sys.stdout
            sys.stdout.reconfigure(encoding=self.target_encoding)
        except (AttributeError, OSError):
            # 某些环境不支持 reconfigure，尝试 buffer 直接写
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._original_encoding and self._original_stdout:
            try:
                sys.stdout.reconfigure(encoding=self._original_encoding)
            except (AttributeError, OSError):
                pass
        # 不吞异常，让异常正常抛出
        return False


def ensure_utf8_stdout():
    """
    非上下文方式：直接强制 stdout 为 UTF-8（不自动恢复）。
    适用于脚本顶层一次性设置。
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def write_utf8(text: str):
    """
    直接写 UTF-8 字节到 stdout buffer，不依赖 sys.stdout.encoding。
    最可靠的跨环境方式。
    """
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
