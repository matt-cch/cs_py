#!/usr/bin/env python3
r"""
download-runtime/atomic-01-route-probe.py — 路由探测原子（v1.0.0）
标签：atomic, runtime
职责：HEAD 探测直连和代理，返回最优路由

用法：
    python atomic-01-route-probe.py --url "https://github.com/.../release.zip"

输出（stdout JSON）：
    {"route":"proxy","proxy":"gh.llkk.cc","reason":"直连不可用，自动选择代理: gh.llkk.cc (延迟 800ms)"}
"""
import argparse
import concurrent.futures
import json
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")

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


def probe_route(url: str, preferred_proxy: str = "", timeout: int = 5) -> dict:
    print(f"[probe] 目标: {url[:80]}...", flush=True)
    if not url.startswith("https://github.com/"):
        print("[probe] 非 GitHub 链接，直接走直连", flush=True)
        return {"route": "direct", "proxy": "", "reason": "非 GitHub 链接，使用直连"}

    # GitHub Release 文件下载：跳过直连，直接探测代理
    is_release_download = "/releases/download/" in url

    if preferred_proxy:
        print(f"[probe] 探测指定代理: {preferred_proxy} ...", flush=True)
        _, latency, ok = _probe_one(preferred_proxy, url, timeout)
        status = f"{'OK' if ok else 'FAIL'} {latency:.0f}ms" if latency != float("inf") else "FAIL"
        print(f"[probe]   结果: {status}", flush=True)
        if ok:
            return {"route": "proxy", "proxy": preferred_proxy,
                    "reason": f"使用指定代理: {preferred_proxy} (延迟 {latency:.0f}ms)"}
        return {"route": "none", "proxy": "", "reason": f"指定代理不可用: {preferred_proxy}"}

    if not is_release_download:
        print("[probe] 探测直连 ...", flush=True)
        try:
            t0 = time.time()
            resp = requests.head(url, timeout=5, allow_redirects=True)
            latency = (time.time() - t0) * 1000
            status = f"{resp.status_code} {latency:.0f}ms"
            print(f"[probe]   直连结果: {status}", flush=True)
            if resp.status_code in (200, 302):
                return {"route": "direct", "proxy": "", "reason": f"直连可用，延迟 {latency:.0f}ms"}
        except Exception as e:
            print(f"[probe]   直连失败: {e}", flush=True)
    else:
        print("[probe] GitHub Release 下载跳过直连，直接探测代理", flush=True)

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
    args = parser.parse_args()

    result = probe_route(args.url, args.proxy)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["route"] != "none" else 1)


if __name__ == "__main__":
    sys.exit(main())
