#!/usr/bin/env python3
"""
插件：归档压缩器（Archive Compressor）
标签：archive

职责：调用 7z 压缩扫描阶段生成的 listfile，支持 zip/7z 两种输出格式，
      带心跳进度输出，解析 7z stdout 统计信息。

用法：
    from archive_compressor import compress_group
    result = compress_group(cfg, fmt="zip")
    print(result["zip_size_mb"])
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path


def heartbeat(stop_event: threading.Event, prefix: str):
    """每 1 秒打印一次心跳，让用户知道没卡住"""
    count = 0
    while not stop_event.is_set():
        time.sleep(1)
        count += 1
        if not stop_event.is_set():
            print(f"{prefix} 已运行 {count}s...", flush=True)


def parse_7z_stdout(stdout: str) -> dict:
    """解析 7z stdout，提取关键统计行"""
    stats = {}
    for line in stdout.splitlines():
        line = line.strip()
        if "Files read" in line:
            stats["files_read"] = line
        elif "Archive size" in line:
            stats["archive_size"] = line
        elif "Folders" in line:
            stats["folders"] = line
        elif "Everything is Ok" in line:
            stats["ok"] = True
    return stats


def compress_group(cfg: dict, seven_zip: Path, fmt: str = "zip", force: bool = False) -> dict:
    """
    使用 7z 压缩指定分组的 listfile。

    参数:
        cfg: archive_config.get_group_config 返回的配置字典
        seven_zip: 7z.exe 绝对路径
        fmt: "zip" 或 "7z"
        force: 是否强制覆盖已存在的输出文件

    返回:
        dict: {
            "zip": zip_path,
            "format": fmt,
            "returncode": int,
            "zip_size_mb": float,
            "elapsed": float,
            "stats": dict,
        }
    """
    zip_path = cfg["zip"]
    listfile_path = cfg["listfile"]
    cwd = cfg["cwd"]

    # 根据格式调整后缀
    if fmt == "7z":
        zip_path = zip_path.with_suffix(".7z")
    else:
        zip_path = zip_path.with_suffix(".zip")

    # 检测另一种格式的旧包
    alt_suffix = ".zip" if fmt == "7z" else ".7z"
    alt_path = zip_path.with_suffix(alt_suffix)

    # 删除旧包（当前格式 + 另一种格式）
    # 原因：黑名单已排除 *.zip / *.7z，输出文件不在压缩范围内；
    #       旧包是基于上一次 scan 的结果，和当前文件系统可能不一致，
    #       必须删除后重新压缩，不能跳过。
    if zip_path.exists():
        os.remove(zip_path)
        print(f"[compress] 删除旧包: {zip_path}")
    if alt_path.exists():
        os.remove(alt_path)
        print(f"[compress] 删除旧包: {alt_path}")

    # 读取文件数
    file_count = 0
    if listfile_path.exists():
        with open(listfile_path, "r", encoding="utf-8") as f:
            file_count = sum(1 for _ in f)

    # 7z 类型参数
    type_flag = "-tzip" if fmt == "zip" else "-t7z"

    cmd = [
        str(seven_zip),
        "a",
        type_flag,
        "-scsUTF-8",
        "-mx=5",
        str(zip_path),
        f"@{listfile_path}",
    ]

    print(f"[compress] 7z 实际路径: {seven_zip}")
    print(f"[compress] CWD: {cwd}")
    print(f"[compress] 输出文件: {zip_path}")
    print(f"[compress] listfile: {listfile_path}")
    print(f"[compress] 文件数: {file_count}")
    print(f"[compress] 格式: {fmt}")
    print(f"[compress] 命令: {' '.join(str(c) for c in cmd)}")
    print(f"[compress] 开始压缩（请勿中断）...")

    stop_event = threading.Event()
    hb = threading.Thread(target=heartbeat, args=(stop_event, "[compress]"), daemon=True)
    hb.start()

    start = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - start

    stop_event.set()
    hb.join(timeout=2)

    print(f"[compress] returncode: {result.returncode}")

    stats = parse_7z_stdout(result.stdout)
    for k, v in stats.items():
        if k != "ok":
            print(f"[compress] {v}")
    if stats.get("ok"):
        print("[compress] Everything is Ok")

    size_mb = 0.0
    if zip_path.exists():
        size_mb = zip_path.stat().st_size / 1024 / 1024
        print(f"[compress] 输出大小: {size_mb:.1f} MB")

    # 审计：listfile - 0字节文件 = 7z_files_read
    # 注意：0字节文件包含原始0字节 + .emptydir（scan阶段先填充再检测）
    listfile_count = 0
    if listfile_path.exists():
        with open(listfile_path, "r", encoding="utf-8") as f:
            listfile_count = sum(1 for _ in f if _.strip())

    zero_byte_count = 0
    zero_byte_path = listfile_path.parent / f"zero-byte-files-{cfg.get('name', 'unknown')}.txt"
    if zero_byte_path.exists():
        with open(zero_byte_path, "r", encoding="utf-8") as f:
            zero_byte_count = sum(1 for _ in f if _.strip())

    files_read = 0
    for line in result.stdout.splitlines():
        m = __import__("re").search(r"Files read from disk:\s+(\d+)", line)
        if m:
            files_read = int(m.group(1))
            break

    expected = listfile_count - zero_byte_count
    print(f"[compress] 审计: listfile={listfile_count}, 0字节={zero_byte_count}, 预期={expected}, 实际={files_read}")
    if expected == files_read:
        print("[compress] 审计: PASS")
    else:
        print(f"[compress] 审计: FAIL (差异: {files_read - expected})")

    print(f"[compress] 耗时: {elapsed:.2f}s")

    if result.returncode != 0:
        print("[compress] WARNINGS:")
        for line in result.stdout.splitlines():
            if "WARNING" in line or "Cannot open" in line or "Error" in line:
                print(f"  {line.strip()}")
        for line in result.stderr.splitlines():
            if line.strip():
                print(f"  [stderr] {line.strip()}")

    return {
        "zip": zip_path,
        "format": fmt,
        "returncode": result.returncode,
        "zip_size_mb": size_mb,
        "elapsed": elapsed,
        "stats": stats,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("archive_compressor 模块已加载")
    print("用法: from archive_compressor import compress_group")
