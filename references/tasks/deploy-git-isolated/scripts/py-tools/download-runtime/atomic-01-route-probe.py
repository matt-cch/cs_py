#!/usr/bin/env python3
r"""
download-runtime/atomic-01-route-probe.py — 路由探测原子（v1.0.0）
标签：atomic, runtime
职责：HEAD 探测直连和代理，返回最优路由

用法：
    python atomic-01-route-probe.py --url "https://github.com/.../release.zip"

    输出（stdout JSON）：
    {"route":"proxy","proxy":"gh.llkk.cc","reason":"GitHub Release 默认走代理: gh.llkk.cc (延迟 800ms)"}
"""
import argparse
import concurrent.futures
import json
import sys
import atexit
import time

import requests

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

GITHUB_PROXIES = [
    "gh-proxy.com", "gh.llkk.cc", "ghproxy.net",
    "ghfast.top", "ghproxy.com", "github.moeyy.xyz", "mirror.ghproxy.com",
]


def _probe_one(proxy: str, url: str, timeout: int) -> tuple:
    """探测单个代理，返回 (proxy, latency_ms, ok)"""
    proxy_url = f"https://{proxy}/{url}"
    try:
        t0 = time.time()
        resp = requests.head(proxy_url, timeout=timeout, allow_redirects=True)
        latency = (time.time() - t0) * 1000
        ok = resp.status_code in (200, 302)
        return (proxy, latency, ok)
    except Exception:
        return (proxy, float("inf"), False)


def _probe_speed(url: str, chunk_bytes: int = 1048576, timeout: int = 15) -> tuple:
    """
    Range GET 测速。下载 chunk_bytes 字节，返回 (speed_mbps, ok)。
    speed_mbps 单位 MB/s（不是 Mbps）。
    """
    headers = {"Range": f"bytes=0-{chunk_bytes - 1}"}
    try:
        t0 = time.time()
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        if resp.status_code not in (200, 206):
            return (0.0, False)
        downloaded = 0
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                downloaded += len(chunk)
            if downloaded >= chunk_bytes:
                break
        elapsed = time.time() - t0
        speed = (downloaded / 1024 / 1024) / elapsed if elapsed > 0 else 0.0
        return (speed, True)
    except Exception as e:
        print(f"[probe]   测速失败: {e}", flush=True)
        return (0.0, False)


def probe_route(url: str, preferred_proxy: str = "", timeout: int = 5,
                prefer_direct: bool = False, min_speed_mbps: float = 0.1) -> dict:
    print(f"[probe] 目标: {url[:80]}...", flush=True)
    if not url.startswith("https://github.com/"):
        print("[probe] 非 GitHub 链接，直接走直连", flush=True)
        return {"route": "direct", "proxy": "", "reason": "非 GitHub 链接，使用直连"}

    # 用户显式指定代理：优先探测，不探测直连
    if preferred_proxy:
        print(f"[probe] 探测指定代理: {preferred_proxy} ...", flush=True)
        _, latency, ok = _probe_one(preferred_proxy, url, timeout)
        status = f"{'OK' if ok else 'FAIL'} {latency:.0f}ms" if latency != float("inf") else "FAIL"
        print(f"[probe]   结果: {status}", flush=True)
        if ok:
            return {"route": "proxy", "proxy": preferred_proxy,
                    "reason": f"使用指定代理: {preferred_proxy} (延迟 {latency:.0f}ms)"}
        return {"route": "none", "proxy": "", "reason": f"指定代理不可用: {preferred_proxy}"}

    # GitHub 链接：先 HEAD 快速排除不可达，再 Range GET 测速
    is_release_download = "/releases/download/" in url

    print("[probe] HEAD 探测直连 ...", flush=True)
    try:
        t0 = time.time()
        resp = requests.head(url, timeout=5, allow_redirects=True)
        head_latency = (time.time() - t0) * 1000
        print(f"[probe]   HEAD 结果: {resp.status_code} {head_latency:.0f}ms", flush=True)
        if resp.status_code not in (200, 302):
            print("[probe]   HEAD 不可达，跳过测速", flush=True)
            direct_ok = False
        else:
            direct_ok = True
    except Exception as e:
        print(f"[probe]   HEAD 失败: {e}", flush=True)
        direct_ok = False

    if direct_ok:
        print("[probe] Range GET 测速 (1MB) ...", flush=True)
        speed, speed_ok = _probe_speed(url)
        if speed_ok:
            print(f"[probe]   测速结果: {speed:.2f} MB/s", flush=True)
            if prefer_direct or speed >= min_speed_mbps:
                reason = f"直连可用，速度 {speed:.2f} MB/s"
                if prefer_direct and speed < min_speed_mbps:
                    reason += " (prefer-direct 强制覆盖低速度)"
                return {"route": "direct", "proxy": "", "reason": reason}
            else:
                print(f"[probe]   速度过低 ({speed:.2f} < {min_speed_mbps} MB/s)，fallback 到代理", flush=True)
        else:
            print("[probe]   测速失败，fallback 到代理", flush=True)

    # 直连不可用或速度不达标：并发探测代理
    print(f"[probe] 并发探测 {len(GITHUB_PROXIES)} 个代理 ...", flush=True)
    best_proxy = None
    best_latency = float("inf")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(GITHUB_PROXIES)) as executor:
        futures = {executor.submit(_probe_one, proxy, url, timeout): proxy for proxy in GITHUB_PROXIES}
        for future in concurrent.futures.as_completed(futures):
            proxy, latency, ok = future.result()
            status = f"{('OK' if ok else 'FAIL')} {latency:.0f}ms" if latency != float("inf") else "FAIL"
            print(f"[probe]   {proxy}: {status}", flush=True)
            if ok and latency < best_latency:
                best_latency = latency
                best_proxy = proxy

    if best_proxy:
        print(f"[probe] 最优代理: {best_proxy} ({best_latency:.0f}ms)", flush=True)
        return {"route": "proxy", "proxy": best_proxy,
                "reason": f"直连不可用，自动选择代理: {best_proxy} (延迟 {best_latency:.0f}ms)"}

    print("[probe] 所有路由均不可用", flush=True)
    return {"route": "none", "proxy": "", "reason": "直连和所有代理均不可用"}


def main():
    parser = argparse.ArgumentParser(description="路由探测原子")
    parser.add_argument("--url", required=True, help="目标 URL")
    parser.add_argument("--proxy", default="", help="指定代理域名")
    parser.add_argument("--prefer-direct", action="store_true",
                        help="即使直连速度低于阈值也强制使用直连")
    parser.add_argument("--min-speed-mbps", type=float, default=0.05,
                        help="直连最小可用速度阈值（MB/s），默认 0.1")
    args = parser.parse_args()

    result = probe_route(args.url, args.proxy, prefer_direct=args.prefer_direct,
                         min_speed_mbps=args.min_speed_mbps)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["route"] != "none" else 1)


if __name__ == "__main__":
    sys.exit(main())
