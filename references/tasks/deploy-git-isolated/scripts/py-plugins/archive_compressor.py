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


def heartbeat(stop_event: threading.Event, prefix: str, progress: dict, total: int):
    """每 1 秒打印一次心跳，带文件处理进度"""
    count = 0
    while not stop_event.is_set():
        time.sleep(1)
        count += 1
        if not stop_event.is_set():
            processed = progress.get("processed", 0)
            pct = processed / total * 100 if total else 0
            last = progress.get("last_file", "")
            if len(last) > 50:
                last = "..." + last[-47:]
            print(
                f"{prefix} 已运行 {count}s... "
                f"已处理 {processed}/{total} ({pct:.1f}%) {last}",
                flush=True,
            )


def stdout_consumer(pipe, stop_event: threading.Event, progress: dict, stdout_lines: list):
    """实时消费 7z stdout，解析 -bb1 输出的 + filename 行"""
    try:
        for line in iter(pipe.readline, ""):
            if stop_event.is_set():
                break
            stdout_lines.append(line)
            stripped = line.strip()
            if stripped.startswith("+ "):
                progress["processed"] = progress.get("processed", 0) + 1
                progress["last_file"] = stripped[2:]
    finally:
        pipe.close()


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


def compress_group(cfg: dict, seven_zip: Path, fmt: str = "zip", force: bool = False, timeout: int = 0) -> dict:
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

    # 读取文件数 + 大小统计
    file_count = 0
    total_size = 0
    file_sizes = []
    if listfile_path.exists():
        with open(listfile_path, "r", encoding="utf-8") as f:
            for line in f:
                path_str = line.strip()
                if not path_str:
                    continue
                file_count += 1
                p = Path(cwd) / path_str
                if p.exists():
                    try:
                        s = p.stat().st_size
                        total_size += s
                        file_sizes.append((str(p), s))
                    except OSError:
                        pass

    # 大小排序，取 TOP 20 大文件（卡点判断）
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    top_n = 20
    top_files = file_sizes[:top_n]
    median_size = 0.0
    avg_size = 0.0
    if file_sizes:
        sizes_only = [s for _, s in file_sizes]
        sizes_only.sort()
        avg_size = sum(sizes_only) / len(sizes_only)
        mid = len(sizes_only) // 2
        if len(sizes_only) % 2 == 0:
            median_size = (sizes_only[mid - 1] + sizes_only[mid]) / 2
        else:
            median_size = sizes_only[mid]

    # 7z 类型参数
    type_flag = "-tzip" if fmt == "zip" else "-t7z"

    cmd = [
        str(seven_zip),
        "a",
        type_flag,
        "-scsUTF-8",
        "-mx=5",
        "-bb1",
        str(zip_path),
        f"@{listfile_path}",
    ]

    print(f"[compress] 7z 实际路径: {seven_zip}")
    print(f"[compress] CWD: {cwd}")
    print(f"[compress] 输出文件: {zip_path}")
    print(f"[compress] listfile: {listfile_path}")
    print(f"[compress] 文件数: {file_count}")
    print(f"[compress] 总原始大小: {total_size / 1024 / 1024:.1f} MB")
    print(f"[compress] 平均文件大小: {avg_size / 1024:.1f} KB")
    print(f"[compress] 中位数文件大小: {median_size / 1024:.1f} KB")
    print(f"[compress] 最大文件 TOP {top_n}（潜在卡点）:")
    for idx, (fp, fs) in enumerate(top_files, 1):
        size_str = f"{fs / 1024 / 1024:.1f} MB" if fs >= 1024 * 1024 else f"{fs / 1024:.1f} KB"
        print(f"[compress]   {idx}. {size_str:>10}  {fp}")
    print(f"[compress] 格式: {fmt}")
    print(f"[compress] 命令: {' '.join(str(c) for c in cmd)}")
    print(f"[compress] 开始压缩（请勿中断）...")

    progress = {"processed": 0, "last_file": ""}
    stdout_lines = []

    stop_event = threading.Event()
    hb = threading.Thread(target=heartbeat, args=(stop_event, "[compress]", progress, file_count), daemon=True)
    hb.start()

    start = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    consumer = threading.Thread(target=stdout_consumer, args=(proc.stdout, stop_event, progress, stdout_lines), daemon=True)
    consumer.start()

    try:
        returncode = proc.wait(timeout=timeout if timeout > 0 else None)
    except subprocess.TimeoutExpired:
        proc.kill()
        returncode = proc.wait()
        print(f"[compress] 超时({timeout}s)，已终止7z进程")
    consumer.join(timeout=5)
    elapsed = time.time() - start

    stop_event.set()
    hb.join(timeout=2)

    stderr_text = proc.stderr.read() if proc.stderr else ""
    stdout_text = "".join(stdout_lines)

    print(f"[compress] returncode: {returncode}")

    stats = parse_7z_stdout(stdout_text)
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
    for line in stdout_text.splitlines():
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

    if returncode != 0:
        print("[compress] WARNINGS:")
        for line in stdout_text.splitlines():
            if "WARNING" in line or "Cannot open" in line or "Error" in line:
                print(f"  {line.strip()}")
        for line in stderr_text.splitlines():
            if line.strip():
                print(f"  [stderr] {line.strip()}")

    return {
        "zip": zip_path,
        "format": fmt,
        "returncode": returncode,
        "zip_size_mb": size_mb,
        "elapsed": elapsed,
        "stats": stats,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("archive_compressor 模块已加载")
    print("用法: from archive_compressor import compress_group")
