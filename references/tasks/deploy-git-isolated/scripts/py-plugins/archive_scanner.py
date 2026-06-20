#!/usr/bin/env python3
"""
插件：归档扫描器（Archive Scanner）
标签：archive

职责：扫描磁盘文件系统，应用黑白名单过滤，检测空目录并创建 .emptydir 占位文件，
      输出 CSV manifest 和 7z listfile。

用法：
    from archive_scanner import scan_group
    result = scan_group(cfg)
    print(result["file_count"], result["total_size"])
"""
import csv
import fnmatch
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PLACEHOLDER = ".emptydir"


def match_blacklist(path: str, patterns: list) -> bool:
    """
    判断路径是否匹配黑名单模式。

    模式语法（对齐 scan-for-backup.py）：
    - dir/     : 排除 dir 及其所有子孙
    - dir/*    : 同 dir/
    - a/b/*.x  : 严格路径匹配（* 不匹配 /）
    - *.x      : basename 匹配（任何层级）
    """
    for pat in patterns:
        if pat.endswith("/"):
            dir_pat = pat[:-1]
            if (
                path == dir_pat
                or path.startswith(dir_pat + "/")
                or ("/" + dir_pat + "/") in (path + "/")
            ):
                return True
        elif pat.endswith("/*"):
            dir_pat = pat[:-2]
            if (
                path == dir_pat
                or path.startswith(dir_pat + "/")
                or ("/" + dir_pat + "/") in (path + "/")
            ):
                return True
        elif "/" in pat:
            pat_parts = pat.split("/")
            path_parts = path.split("/")
            if len(pat_parts) != len(path_parts):
                continue
            matched = True
            for pp, pt in zip(path_parts, pat_parts):
                if not fnmatch.fnmatch(pp, pt):
                    matched = False
                    break
            if matched:
                return True
        else:
            if fnmatch.fnmatch(os.path.basename(path), pat):
                return True
    return False


def scan(src_dir: Path, arcname: str, whitelist: list, blacklist: list):
    """
    扫描源目录，返回 entries 字典。

    参数:
        src_dir: 源目录绝对路径
        arcname: 归档前缀（如 "cs_py" 或 "venv"）
        whitelist: 白名单子目录列表（相对 src_dir）
        blacklist: 黑名单模式列表

    返回:
        dict: {archive_path: entry_dict}
    """
    src = src_dir.resolve()
    entries = {}
    count = 0

    # 决定顶层扫描范围
    if whitelist:
        top_dirs = []
        for w in whitelist:
            disk_path = src / w
            if disk_path.exists():
                top_dirs.append((disk_path, f"{arcname}/{w}"))
    else:
        top_dirs = [(src, arcname)]

    for top_root, top_arcname in top_dirs:
        for dirpath, dirnames, filenames in os.walk(top_root):
            current = Path(dirpath)
            rel = current.relative_to(top_root)
            rel_str = str(rel).replace("\\", "/")
            if rel_str == ".":
                rel_str = ""

            path_prefix = f"{top_arcname}/{rel_str}" if rel_str else top_arcname

            # 过滤子目录（黑名单）
            dirnames[:] = [
                d for d in dirnames
                if not match_blacklist(f"{path_prefix}/{d}", blacklist)
            ]

            # 目录条目
            for d in sorted(dirnames):
                path = f"{path_prefix}/{d}"
                if match_blacklist(path, blacklist):
                    continue
                full = current / d
                try:
                    stat = full.stat()
                    entries[path] = {
                        "path": path,
                        "type": "DIR",
                        "size": 0,
                        "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "mtime_ts": int(stat.st_mtime),
                    }
                except OSError:
                    pass

            # 文件条目
            for f in sorted(filenames):
                path = f"{path_prefix}/{f}"
                if match_blacklist(path, blacklist):
                    continue
                full = current / f
                try:
                    stat = full.stat()
                    entries[path] = {
                        "path": path,
                        "type": "FILE",
                        "size": stat.st_size,
                        "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "mtime_ts": int(stat.st_mtime),
                    }
                    count += 1
                    if count % 5000 == 0:
                        print(f"[scan] 已扫描 {count} 个文件...")
                except OSError:
                    pass

    return entries


def find_empty_dirs(entries: dict) -> list:
    """找出空目录（自身及所有子孙下都没有 FILE 条目）"""
    dirs = set(k for k, v in entries.items() if v["type"] == "DIR")
    files = set(k for k, v in entries.items() if v["type"] == "FILE")

    empty = []
    for d in sorted(dirs):
        prefix = d + "/"
        has_files = any(f.startswith(prefix) for f in files)
        if not has_files:
            empty.append(d)
    return empty


def create_placeholders(entries: dict, empty_dirs: list, src_dir: Path, arcname: str):
    """
    在磁盘上创建 .emptydir 占位文件，并更新 entries。

    参数:
        entries: 当前 entries 字典（会被修改）
        empty_dirs: 空目录路径列表（archive 路径，如 "cs_py/subdir"）
        src_dir: 源目录绝对路径
        arcname: 归档前缀

    返回:
        int: 新建占位文件数量
    """
    src = src_dir.resolve()
    created = 0

    for path in empty_dirs:
        # 从 archive 路径提取磁盘相对路径
        # path 形如 "cs_py/sub/..." 或 "venv/.opencode/..."
        if "/" in path:
            rel = path.split("/", 1)[1]
        else:
            rel = ""

        disk_path = src / rel.replace("/", "\\") / PLACEHOLDER
        if not disk_path.exists():
            disk_path.write_text("", encoding="utf-8")
            created += 1

        # 添加占位文件条目
        ph_path = path + "/" + PLACEHOLDER
        stat = disk_path.stat()
        entries[ph_path] = {
            "path": ph_path,
            "type": "FILE",
            "size": 0,
            "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "mtime_ts": int(stat.st_mtime),
        }

    return created


def write_csv(entries: dict, csv_path: Path):
    """将 entries 写入 CSV 文件"""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["path", "type", "size", "mtime_iso", "mtime_ts"]
        )
        writer.writeheader()
        for e in sorted(entries.values(), key=lambda x: x["path"]):
            writer.writerow(e)


def write_listfile(entries: dict, listfile_path: Path):
    """将文件路径写入 listfile（Win 反斜杠，相对于 cwd）"""
    file_paths = sorted(
        path.replace("/", "\\")
        for path, entry in entries.items()
        if entry["type"] == "FILE"
    )
    listfile_path.parent.mkdir(parents=True, exist_ok=True)
    with open(listfile_path, "w", encoding="utf-8") as f:
        f.write("\n".join(file_paths))
        if file_paths:
            f.write("\n")
    return len(file_paths)


def scan_group(cfg: dict) -> dict:
    """
    扫描指定分组，生成 CSV + listfile。

    参数:
        cfg: archive_config.get_group_config 返回的配置字典

    返回:
        dict: {
            "csv": csv_path,
            "listfile": listfile_path,
            "file_count": int,
            "dir_count": int,
            "total_size": int,
            "empty_dirs": int,
            "placeholders_created": int,
        }
    """
    src = cfg["src"]
    arcname = cfg["arcname"]
    whitelist = cfg.get("whitelist", [])
    blacklist = cfg.get("blacklist", [])
    csv_path = cfg["csv"]
    listfile_path = cfg["listfile"]

    print(f"[scan] src 实际路径: {src}")
    print(f"[scan] arcname: {arcname}")
    print(f"[scan] whitelist: {whitelist}")
    print(f"[scan] blacklist: {blacklist}")

    start = time.time()
    entries = scan(src, arcname, whitelist, blacklist)

    # 补齐根目录条目（scan 不记录 top_root 自身）
    if whitelist:
        for w in whitelist:
            d = f"{arcname}/{w}"
            if d not in entries:
                disk_path = src / w
                if disk_path.exists():
                    try:
                        stat = disk_path.stat()
                        entries[d] = {
                            "path": d,
                            "type": "DIR",
                            "size": 0,
                            "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "mtime_ts": int(stat.st_mtime),
                        }
                    except OSError:
                        pass
        if arcname not in entries:
            if src.exists():
                try:
                    stat = src.stat()
                    entries[arcname] = {
                        "path": arcname,
                        "type": "DIR",
                        "size": 0,
                        "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "mtime_ts": int(stat.st_mtime),
                    }
                except OSError:
                    pass
    else:
        if arcname not in entries:
            if src.exists():
                try:
                    stat = src.stat()
                    entries[arcname] = {
                        "path": arcname,
                        "type": "DIR",
                        "size": 0,
                        "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "mtime_ts": int(stat.st_mtime),
                    }
                except OSError:
                    pass

    # 空目录检测与占位
    empty_dirs = find_empty_dirs(entries)
    placeholders_created = 0
    if empty_dirs:
        print(f"[scan] 发现 {len(empty_dirs)} 个空目录，创建占位文件...")
        placeholders_created = create_placeholders(entries, empty_dirs, src, arcname)
        print(f"[scan] 新建占位文件: {placeholders_created} 个")

    # 写 CSV
    write_csv(entries, csv_path)

    # 写 listfile
    file_count = write_listfile(entries, listfile_path)

    dir_count = sum(1 for e in entries.values() if e["type"] == "DIR")
    total_size = sum(int(e["size"]) for e in entries.values() if e["type"] == "FILE")
    elapsed = time.time() - start

    print(f"[scan] CSV: {file_count} 文件, {dir_count} 目录, 共 {len(entries)} 条")
    print(f"[scan] 原始大小: {total_size / 1024 / 1024:.1f} MB")
    print(f"[scan] listfile: {file_count} 行")
    print(f"[scan] 输出 CSV: {csv_path}")
    print(f"[scan] 输出 listfile: {listfile_path}")
    print(f"[scan] 耗时: {elapsed:.2f}s")

    return {
        "csv": csv_path,
        "listfile": listfile_path,
        "file_count": file_count,
        "dir_count": dir_count,
        "total_size": total_size,
        "empty_dirs": len(empty_dirs),
        "placeholders_created": placeholders_created,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    # 自检：需要 cfg，通常由 archive_config 提供
    print("archive_scanner 模块已加载")
    print("用法: from archive_scanner import scan_group")
