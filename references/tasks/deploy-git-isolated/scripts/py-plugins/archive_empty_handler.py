#!/usr/bin/env python3
"""
插件：空目录与零字节文件处理器（Archive Empty Handler）
标签：archive, core

职责：
    - 检测空目录并输出明细
    - 检测零字节文件并输出明细
    - 在空目录下创建 .emptydir 占位文件
    - 递归清理所有 .emptydir 文件

用法：
    from archive_empty_handler import detect_empty_dirs, detect_zero_byte_files
    from archive_empty_handler import write_detail_list, fill_emptydirs, cleanup_emptydirs
"""
import os
from pathlib import Path

PLACEHOLDER = ".emptydir"


def detect_empty_dirs(entries: dict) -> list:
    """
    从 entries 中找出空目录（自身及所有子孙下都没有 FILE 条目）。

    参数:
        entries: 扫描结果字典

    返回:
        list: 空目录 archive 路径列表（已排序）
    """
    dirs = set(k for k, v in entries.items() if v["type"] == "DIR")
    files = set(k for k, v in entries.items() if v["type"] == "FILE")

    empty = []
    for d in sorted(dirs):
        prefix = d + "/"
        has_files = any(f.startswith(prefix) for f in files)
        if not has_files:
            empty.append(d)
    return empty


def detect_zero_byte_files(entries: dict) -> list:
    """
    从 entries 中找出零字节文件。

    参数:
        entries: 扫描结果字典

    返回:
        list: 零字节文件 archive 路径列表（已排序）
    """
    zero = [
        k for k, v in entries.items()
        if v["type"] == "FILE" and int(v.get("size", 0)) == 0
    ]
    return sorted(zero)


def write_detail_list(paths: list, out_path: Path) -> int:
    """
    将路径列表写入明细文件（一行一个）。

    参数:
        paths: 路径列表
        out_path: 输出文件路径

    返回:
        int: 写入行数
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        if paths:
            f.write("\n".join(paths))
            f.write("\n")
    return len(paths)


def fill_emptydirs(empty_dirs: list, src_dir: Path, arcname: str) -> int:
    """
    在空目录下创建 .emptydir 占位文件。

    参数:
        empty_dirs: 空目录 archive 路径列表
        src_dir: 源目录绝对路径
        arcname: 归档前缀

    返回:
        int: 新建占位文件数量
    """
    src = src_dir.resolve()
    created = 0

    for path in empty_dirs:
        # 从 archive 路径提取磁盘相对路径
        if "/" in path:
            rel = path.split("/", 1)[1]
        else:
            rel = ""

        disk_path = src / rel.replace("/", os.sep) / PLACEHOLDER
        if not disk_path.exists():
            disk_path.write_text("", encoding="utf-8")
            created += 1

    return created


def cleanup_emptydirs(src_dir: Path) -> int:
    """
    递归清理 src_dir 下所有 .emptydir 文件。

    参数:
        src_dir: 源目录绝对路径

    返回:
        int: 删除的 .emptydir 数量
    """
    src = src_dir.resolve()
    removed = 0
    for root, dirs, files in os.walk(src):
        for f in files:
            if f == PLACEHOLDER:
                p = Path(root) / f
                try:
                    p.unlink()
                    removed += 1
                except OSError:
                    pass
    return removed


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("archive_empty_handler 模块已加载")
    print("用法: from archive_empty_handler import detect_empty_dirs, detect_zero_byte_files")
    print("       from archive_empty_handler import write_detail_list, fill_emptydirs, cleanup_emptydirs")
