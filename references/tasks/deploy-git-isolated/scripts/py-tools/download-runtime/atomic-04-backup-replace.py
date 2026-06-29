#!/usr/bin/env python3
r"""
download-runtime/atomic-04-backup-replace.py — 备份与替换原子（v1.0.0）
标签：atomic, runtime
职责：检测进程占用 → 备份旧目录 → 替换为新目录

用法：
    python atomic-04-backup-replace.py --tool-dir "...\\venv\\node" --source-dir "...\\node-extracted" --exe-path "...\\node.exe"

输出（stdout JSON）：
    {"backup_dir":"...\\node-backup-20260626213900","replaced":true,"error":null}
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")


def get_running_process_info(exe_path: str) -> str:
    try:
        result = subprocess.run(
            ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command",
             f"Get-Process | Where-Object {{$_.Path -eq '{exe_path}'}} | Select-Object -First 1 | Format-List"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def backup_and_replace(tool_dir: str, source_dir: str, exe_path: str) -> dict:
    result = {"backup_dir": "", "replaced": False, "error": None}

    # 先检查源目录是否存在
    if not os.path.exists(source_dir):
        result["error"] = f"源目录不存在: {source_dir}"
        return result

    # 检测进程占用
    proc_info = get_running_process_info(exe_path)
    if proc_info:
        result["error"] = f"检测到进程占用:\n{proc_info}"
        return result

    # 备份
    if os.path.exists(tool_dir):
        backup_name = f"{tool_dir}-backup-{time.strftime('%Y%m%d%H%M%S')}"
        shutil.move(tool_dir, backup_name)
        result["backup_dir"] = backup_name

    # 替换
    if os.path.normpath(source_dir) == os.path.normpath(tool_dir):
        result["replaced"] = True
    elif os.path.normpath(os.path.dirname(source_dir)) == os.path.normpath(os.path.dirname(tool_dir)):
        shutil.move(source_dir, tool_dir)
        result["replaced"] = True
    else:
        os.makedirs(tool_dir, exist_ok=True)
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(tool_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        result["replaced"] = True

    return result


def main():
    parser = argparse.ArgumentParser(description="备份与替换原子")
    parser.add_argument("--tool-dir", required=True, help="目标工具目录")
    parser.add_argument("--source-dir", required=True, help="新版本的源目录")
    parser.add_argument("--exe-path", required=True, help="可执行文件路径（用于进程检测）")
    args = parser.parse_args()

    result = backup_and_replace(args.tool_dir, args.source_dir, args.exe_path)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["replaced"] else 1)


if __name__ == "__main__":
    sys.exit(main())
