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
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from pathlib import Path

__plugin_registry__ = None

PLACEHOLDER = ".emptydir"


def match_blacklist(path: str, patterns: list) -> bool:
    """
    判断路径是否匹配黑名单模式。

    模式语法（对齐 .gitignore + 根级锚点）：
    - dir/        : 排除 dir 及其所有子孙
    - dir/*       : 同 dir/
    - a/b/*.x     : 严格路径匹配（* 不匹配 /）
    - /*.x        : 根级匹配（仅该目录下直接文件，不递归）
    - *.x         : basename 匹配（递归所有层级）
    """
    for pat in patterns:
        if pat.startswith("/*"):
            # 根级匹配：path 恰好两段（arcname/filename），且第二段匹配 pat[1:]
            path_parts = path.split("/")
            if len(path_parts) == 2 and fnmatch.fnmatch(path_parts[1], pat[1:]):
                return True
        elif pat.endswith("/"):
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
            # 完整路径匹配（段数一致）
            if len(pat_parts) == len(path_parts):
                matched = True
                for pp, pt in zip(path_parts, pat_parts):
                    if not fnmatch.fnmatch(pp, pt):
                        matched = False
                        break
                if matched:
                    return True
            # 子路径匹配：pat 作为 path 的连续子序列
            pat_len = len(pat_parts)
            for i in range(len(path_parts) - pat_len + 1):
                matched = True
                for j in range(pat_len):
                    if not fnmatch.fnmatch(path_parts[i + j], pat_parts[j]):
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
            w_clean = w.rstrip("/")
            disk_path = src / w_clean
            if disk_path.exists():
                top_dirs.append((disk_path, f"{arcname}/{w_clean}"))
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


def write_listfile(entries: dict, listfile_path: Path, arcname: str = "", src: Path = None, cwd: Path = None):
    """将文件路径写入 listfile（Win 反斜杠，相对于 cwd），同时保留历史版本"""
    # 计算磁盘真实前缀（解决 arcname 与磁盘目录名不一致问题）
    if src and cwd:
        try:
            real_prefix = str(src.relative_to(cwd)).replace("/", "\\")
        except ValueError:
            real_prefix = str(src).replace("/", "\\")
    else:
        real_prefix = arcname

    file_paths = []
    for path, entry in sorted(entries.items()):
        if entry["type"] != "FILE":
            continue
        # 将 arcname 前缀替换为真实磁盘路径前缀
        if arcname and path.startswith(arcname + "/"):
            path = real_prefix + path[len(arcname):]
        file_paths.append(path.replace("/", "\\"))

    listfile_path.parent.mkdir(parents=True, exist_ok=True)
    with open(listfile_path, "w", encoding="utf-8") as f:
        f.write("\n".join(file_paths))
        if file_paths:
            f.write("\n")

    # 保留历史版本（带时间戳），用于下次 diff
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    history_path = listfile_path.parent / f"{listfile_path.stem}-{ts}{listfile_path.suffix}"
    with open(history_path, "w", encoding="utf-8") as f:
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
    group_name = cfg.get("name", arcname)
    whitelist = cfg.get("whitelist", [])
    blacklist = cfg.get("blacklist", [])
    csv_path = cfg["csv"]
    listfile_path = cfg["listfile"]

    print(f"[scan] src 实际路径: {src}")
    print(f"[scan] arcname: {arcname}")
    print(f"[scan] whitelist: {whitelist}")
    print(f"[scan] blacklist: {blacklist}")

    start = time.time()

    # 1. 清理旧的 .emptydir（避免上一次 run 的残留影响本次 scan）
    removed = __plugin_registry__.archive_empty_handler.cleanup_emptydirs(src)
    if removed:
        print(f"[scan] 清理旧占位文件: {removed} 个")

    # 2. 第一次扫描
    entries = scan(src, arcname, whitelist, blacklist)

    # 补齐根目录条目（scan 不记录 top_root 自身）
    if whitelist:
        for w in whitelist:
            w_clean = w.rstrip("/")
            d = f"{arcname}/{w_clean}"
            if d not in entries:
                disk_path = src / w_clean
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

    # 3. 检测空目录
    empty_dirs = __plugin_registry__.archive_empty_handler.detect_empty_dirs(entries)
    empty_dirs_path = listfile_path.parent / f"empty-dirs-{group_name}.txt"
    __plugin_registry__.archive_empty_handler.write_detail_list(empty_dirs, empty_dirs_path)
    print(f"[scan] 空目录: {len(empty_dirs)} 个 → {empty_dirs_path}")

    # 4. 填充 .emptydir 到空目录
    placeholders_created = 0
    if empty_dirs:
        # 去掉 arcname 前缀，转为相对于 src 的路径后传给 fill_emptydirs
        empty_dirs_rel = [path.split("/", 1)[1] if "/" in path else "" for path in empty_dirs]
        placeholders_created = __plugin_registry__.archive_empty_handler.fill_emptydirs(empty_dirs_rel, src)
        print(f"[scan] 新建占位文件: {placeholders_created} 个")

    # 5. 手动把 .emptydir 添加到 entries
    for path in empty_dirs:
        ph_path = path + "/" + PLACEHOLDER
        rel = path.split("/", 1)[1] if "/" in path else ""
        disk_path = src / rel.replace("/", os.sep) / PLACEHOLDER
        if disk_path.exists():
            try:
                stat = disk_path.stat()
                entries[ph_path] = {
                    "path": ph_path,
                    "type": "FILE",
                    "size": 0,
                    "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "mtime_ts": int(stat.st_mtime),
                }
            except OSError:
                pass

    # 6. 检测 0 字节文件（此时包含 .emptydir）
    zero_byte_files = __plugin_registry__.archive_empty_handler.detect_zero_byte_files(entries)
    zero_byte_path = listfile_path.parent / f"zero-byte-files-{group_name}.txt"
    __plugin_registry__.archive_empty_handler.write_detail_list(zero_byte_files, zero_byte_path)
    print(f"[scan] 0 字节文件: {len(zero_byte_files)} 个 → {zero_byte_path}")

    # 7. 写 CSV
    write_csv(entries, csv_path)

    # 8. 写 listfile
    file_count = write_listfile(entries, listfile_path, arcname=arcname, src=src, cwd=cfg.get("cwd"))

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
        "zero_byte_files": len(zero_byte_files),
    }


def cleanup_placeholders(src_dir) -> int:
    """
    清理 scan_group 创建的 .emptydir 占位文件。
    供 workflow 层在 compress 后调用，避免污染源目录。

    参数:
        src_dir: 源目录绝对路径（str 或 Path）

    返回:
        int: 删除的 .emptydir 数量
    """
    removed = __plugin_registry__.archive_empty_handler.cleanup_emptydirs(Path(src_dir))
    if removed:
        print(f"[cleanup] 删除占位文件: {removed} 个")
    return removed


def verify_group(cfg: dict, zip_path: Path, seven_zip: Path) -> dict:
    """
    解压压缩包并与 listfile 交叉验证。

    参数:
        cfg: archive_config.get_group_config 返回的配置字典
        zip_path: 压缩包绝对路径
        seven_zip: 7z.exe 绝对路径

    返回:
        dict: {
            "pass": bool,
            "expected": int,
            "actual": int,
            "missing": list,
            "extra": list,
        }
    """
    listfile_path = cfg["listfile"]
    group_name = cfg.get("name", "unknown")
    extract_dir = cfg["out_dir"] / f"verify-extract-{group_name}"

    # 清理旧临时目录
    if extract_dir.exists():
        shutil.rmtree(extract_dir, ignore_errors=True)
    extract_dir.mkdir(parents=True, exist_ok=True)

    # 解压
    print(f"[verify] 解压到: {extract_dir}")
    proc = subprocess.run(
        [str(seven_zip), "x", str(zip_path), f"-o{extract_dir}", "-y"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        print(f"[verify] 解压失败: returncode={proc.returncode}")
        return {"pass": False, "expected": 0, "actual": 0, "missing": [], "extra": []}

    # 收集解压后的文件路径
    actual_files = set()
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            full = Path(root) / f
            rel = full.relative_to(extract_dir)
            rel_str = str(rel).replace("/", "\\")
            actual_files.add(rel_str)

    # 读取 listfile
    expected_files = set()
    if listfile_path.exists():
        with open(listfile_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    expected_files.add(line)

    # 交叉比对
    missing = sorted(expected_files - actual_files)
    extra = sorted(actual_files - expected_files)

    print(f"[verify] 预期文件数: {len(expected_files)}")
    print(f"[verify] 实际文件数: {len(actual_files)}")

    if missing:
        print(f"[verify] 缺失文件: {len(missing)} 个")
        for p in missing[:10]:
            print(f"  - {p}")
        if len(missing) > 10:
            print(f"  ... 还有 {len(missing) - 10} 个")
    if extra:
        print(f"[verify] 多余文件: {len(extra)} 个")
        for p in extra[:10]:
            print(f"  + {p}")
        if len(extra) > 10:
            print(f"  ... 还有 {len(extra) - 10} 个")

    # 清理临时目录
    shutil.rmtree(extract_dir, ignore_errors=True)

    passed = len(missing) == 0 and len(extra) == 0
    if passed:
        print("[verify] PASS: 文件一一匹配")
    else:
        print(f"[verify] FAIL: 缺失 {len(missing)} 个, 多余 {len(extra)} 个")

    return {
        "pass": passed,
        "expected": len(expected_files),
        "actual": len(actual_files),
        "missing": missing,
        "extra": extra,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    # 自检：需要 cfg，通常由 archive_config 提供
    print("archive_scanner 模块已加载")
    print("用法: from archive_scanner import scan_group, cleanup_placeholders, verify_group")
