#!/usr/bin/env python3
r"""
download-runtime/atomic-02-download-file.py — 文件下载原子（v1.0.0）
标签：atomic, runtime
职责：流式下载文件，支持代理和进度条

用法：
    python atomic-02-download-file.py --url "..." --out-file "D:\\download\\node.zip" --show-progress

输出（stdout JSON）：
    {"success":true,"out_file":"D:\\download\\node.zip","size_mb":45.2,"elapsed_sec":12.3,"speed_kbps":3800.0}
"""
import argparse
import json
import os
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")


def download_file(url: str, out_file: str, proxy: str = "", show_progress: bool = False) -> dict:
    actual_url = url
    if proxy:
        actual_url = f"https://{proxy}/{url}"

    if proxy:
        conn_timeout, read_timeout = 60, 900
    else:
        conn_timeout, read_timeout = 30, 300

    try:
        start = time.time()
        resp = requests.get(actual_url, stream=True, timeout=(conn_timeout, read_timeout),
                            headers={"User-Agent": "atomic-download-file/1.0"})
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        last_percent = -1
        hash_count = 0
        hash_per_percent = 2

        with open(out_file, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if show_progress and total > 0:
                        percent = (downloaded * 100) // total
                        if percent != last_percent:
                            last_percent = percent
                            down_mb = downloaded / (1024 * 1024)
                            total_mb = total / (1024 * 1024)
                            sys.stderr.write(f"\r  {percent}% ({down_mb:.2f} MB / {total_mb:.2f} MB)")
                            sys.stderr.flush()

        if show_progress and total > 0:
            sys.stderr.write("\n")
            sys.stderr.flush()

        elapsed = time.time() - start
        file_size = os.path.getsize(out_file)
        avg_speed = (file_size / 1024 / elapsed) if elapsed > 0 else 0
        return {
            "success": True,
            "out_file": out_file,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "elapsed_sec": round(elapsed, 1),
            "speed_kbps": round(avg_speed, 1),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="文件下载原子")
    parser.add_argument("--url", required=True, help="下载 URL")
    parser.add_argument("--out-file", required=True, help="保存路径")
    parser.add_argument("--proxy", default="", help="代理域名")
    parser.add_argument("--show-progress", action="store_true", help="显示进度条")
    args = parser.parse_args()

    result = download_file(args.url, args.out_file, args.proxy, args.show_progress)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    sys.exit(main())
