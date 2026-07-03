#!/usr/bin/env python3
r"""
download-runtime/atomic-05-cleanup-temp.py — 清理临时文件原子（v1.0.0）
标签：atomic, runtime
职责：清理解压临时目录和/或 ZIP 文件

用法：
    python atomic-05-cleanup-temp.py --extract-dir "...\\node-extracted" --zip-file "...\\node.zip" --keep-zip

输出（stdout JSON）：
    {"extract_removed":true,"zip_removed":false,"error":null}
"""
import argparse
import json
import os
import shutil
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


def cleanup(extract_dir: str, zip_file: str, keep_zip: bool = False) -> dict:
    result = {"extract_removed": False, "zip_removed": False, "error": None}

    if extract_dir and os.path.exists(extract_dir):
        try:
            shutil.rmtree(extract_dir)
            result["extract_removed"] = True
        except Exception as e:
            result["error"] = f"清理解压目录失败: {e}"

    if zip_file and os.path.exists(zip_file) and not keep_zip:
        try:
            os.remove(zip_file)
            result["zip_removed"] = True
        except Exception as e:
            result["error"] = f"清理 ZIP 失败: {e}"

    return result


def main():
    parser = argparse.ArgumentParser(description="清理临时文件原子")
    parser.add_argument("--extract-dir", default="", help="解压临时目录")
    parser.add_argument("--zip-file", default="", help="ZIP 文件路径")
    parser.add_argument("--keep-zip", action="store_true", help="保留 ZIP 文件")
    args = parser.parse_args()

    result = cleanup(args.extract_dir, args.zip_file, args.keep_zip)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
