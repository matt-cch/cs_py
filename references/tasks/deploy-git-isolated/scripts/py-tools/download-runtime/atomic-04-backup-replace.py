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
import atexit
import time
from pathlib import Path

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


def derive_tool_dir(exe_path: str) -> str:
    """从 exe_path 推导工具根目录：优先取 venv 后的第一级，否则取父目录"""
    p = Path(exe_path)
    parts = list(p.parts)
    for i, part in enumerate(parts):
        if part.lower() == "venv" and i + 1 < len(parts):
            return str(Path(*parts[:i + 2]))
    return str(p.parent)


def derive_source_dir(exe_path: str, found_exe: str) -> str:
    """
    按 exe_path 去掉 venv 后的目录层级深度，从 found_exe 的父目录
    往上回溯同样深度，推导 download 下的解压根目录。

    例：venv/node/node.exe（1 层）→ found_exe 父目录即 source_dir
        venv/git/cmd/git.exe（2 层）→ found_exe 父目录往上 1 层
    """
    exe_p = Path(exe_path)
    parts = list(exe_p.parts)

    venv_idx = -1
    for i, p in enumerate(parts):
        if p.lower() == "venv":
            venv_idx = i
            break

    if venv_idx == -1 or venv_idx + 1 >= len(parts):
        return str(Path(found_exe).parent)

    # venv 后的相对路径，如 ["node", "node.exe"] 或 ["git", "cmd", "git.exe"]
    rel_parts = parts[venv_idx + 1:]
    # exe 以上的目录层数（node\node.exe → 1，git\cmd\git.exe → 2）
    dir_depth = len(rel_parts) - 1

    source = Path(found_exe).parent
    for _ in range(dir_depth - 1):
        source = source.parent

    return str(source)


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


def backup_and_replace(exe_path: str, found_exe: str) -> dict:
    result = {"backup_dir": "", "replaced": False, "error": None, "tool_dir": "", "source_dir": ""}

    tool_dir = derive_tool_dir(exe_path)
    source_dir = derive_source_dir(exe_path, found_exe)
    result["tool_dir"] = tool_dir
    result["source_dir"] = source_dir

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

    # 替换：完整目录覆盖
    try:
        shutil.copytree(source_dir, tool_dir)
        result["replaced"] = True
    except Exception as e:
        result["error"] = f"替换失败: {e}"

    return result


def main():
    parser = argparse.ArgumentParser(description="备份与替换原子")
    parser.add_argument("--exe-path", required=True, help="venv 中当前工具的可执行文件路径")
    parser.add_argument("--found-exe", required=True, help="下载解压后检测到的可执行文件路径")
    args = parser.parse_args()

    result = backup_and_replace(args.exe_path, args.found_exe)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["replaced"] else 1)


if __name__ == "__main__":
    sys.exit(main())
