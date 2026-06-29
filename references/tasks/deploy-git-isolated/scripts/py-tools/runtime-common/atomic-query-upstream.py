#!/usr/bin/env python3
r"""
runtime-common/atomic-query-upstream.py — 上游版本查询原子（v1.0.0）
标签：atomic, runtime
职责：查询指定工具的上游最新版本

用法：
    python atomic-query-upstream.py --tool-name python --query-param python
    python atomic-query-upstream.py --tool-name opencode_cli --query-param opencode_cli --target-version 1.17.0

输出（stdout JSON）：
    {"upstream_version":"3.13.14","upstream_source":"阿里云 python-release","asset_url":"...","asset_name":"...","error":null}
"""
import argparse
import json
import re
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")


# =============================================================================
# Upstream Checker（纯 Python，requests 实现）
# =============================================================================

class UpstreamChecker:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "atomic-query-upstream/1.0 (Python requests)"})

    def _get(self, url: str) -> dict:
        start = time.time()
        try:
            resp = self.session.get(url, timeout=self.timeout)
            elapsed = time.time() - start
            if resp.status_code == 200:
                return {"ok": True, "text": resp.text, "elapsed": elapsed}
            return {"ok": False, "error": f"HTTP {resp.status_code}", "elapsed": elapsed}
        except requests.Timeout:
            return {"ok": False, "error": f"超时 (> {self.timeout}s)", "elapsed": self.timeout}
        except Exception as e:
            return {"ok": False, "error": str(e), "elapsed": 0}

    def query(self, tool_name: str, query_param: str, target_version: str = "") -> dict:
        result = {"upstream_version": None, "upstream_source": None, "asset_url": "", "asset_name": "", "error": None}
        try:
            if query_param == "python":
                result = self._query_python(target_version)
            elif query_param == "node":
                result = self._query_node()
            elif query_param == "opencode_cli":
                result = self._query_opencode(target_version)
            elif query_param == "llama_cpp_python":
                result = self._query_llama_cpp_python(target_version)
            elif query_param == "chromium":
                result = self._query_chromium()
            else:
                result["error"] = f"未知查询参数: {query_param}"
        except Exception as e:
            result["error"] = str(e)
        return result

    # -------------------------------------------------------------------------
    # Python
    # -------------------------------------------------------------------------
    def _query_python(self, target_version: str = "") -> dict:
        url = "https://mirrors.aliyun.com/python-release/windows/"
        r = self._get(url)
        if not r["ok"]:
            return {"error": r["error"]}
        versions = re.findall(r'python-(\d+\.\d+\.\d+)-embed-amd64\.zip', r["text"])
        if not versions:
            return {"error": "未解析到版本"}
        sorted_versions = self._sort_versions(versions)
        latest = sorted_versions[0]
        if target_version and target_version in sorted_versions:
            latest = target_version
        return {
            "upstream_version": latest,
            "upstream_source": "阿里云 python-release",
            "asset_url": f"https://mirrors.aliyun.com/python-release/windows/python-{latest}-embed-amd64.zip",
            "asset_name": f"python-{latest}-embed-amd64.zip",
        }

    # -------------------------------------------------------------------------
    # Node.js
    # -------------------------------------------------------------------------
    def _query_node(self) -> dict:
        url = "https://mirrors.aliyun.com/nodejs-release/"
        r = self._get(url)
        if not r["ok"]:
            return {"error": r["error"]}
        versions = re.findall(r'href="(v\d+\.\d+\.\d+)/"', r["text"])
        if not versions:
            return {"error": "未解析到版本"}
        latest = self._sort_versions([v.lstrip("v") for v in versions])[0]
        return {
            "upstream_version": latest,
            "upstream_source": "阿里云 nodejs-release",
            "asset_url": f"https://mirrors.aliyun.com/nodejs-release/v{latest}/node-v{latest}-win-x64.zip",
            "asset_name": f"node-v{latest}-win-x64.zip",
        }

    # -------------------------------------------------------------------------
    # OpenCode CLI
    # -------------------------------------------------------------------------
    def _query_opencode(self, target_version: str = "") -> dict:
        url = "https://api.github.com/repos/anomalyco/opencode/releases/latest"
        r = self._get(url)
        if not r["ok"]:
            return {"error": r["error"]}
        data = json.loads(r["text"])
        tag = data.get("tag_name", "").lstrip("v")
        asset_url = ""
        asset_name = ""
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if "windows" in name.lower() and name.endswith(".zip"):
                asset_url = asset.get("browser_download_url", "")
                asset_name = name
                break
        return {
            "upstream_version": target_version or tag,
            "upstream_source": "GitHub Release anomalyco/opencode",
            "asset_url": asset_url,
            "asset_name": asset_name,
        }

    # -------------------------------------------------------------------------
    # llama.cpp Python
    # -------------------------------------------------------------------------
    def _query_llama_cpp_python(self, target_version: str = "") -> dict:
        version = target_version or "0.3.22"
        url = f"https://api.github.com/repos/abetlen/llama-cpp-python/releases/tags/v{version}"
        r = self._get(url)
        if not r["ok"]:
            return {"error": r["error"]}
        data = json.loads(r["text"])
        asset_url = ""
        asset_name = ""
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if "win_amd64" in name and name.endswith(".whl"):
                asset_url = asset.get("browser_download_url", "")
                asset_name = name
                break
        return {
            "upstream_version": version,
            "upstream_source": "GitHub Release abetlen/llama-cpp-python",
            "asset_url": asset_url,
            "asset_name": asset_name,
        }

    # -------------------------------------------------------------------------
    # Chromium
    # -------------------------------------------------------------------------
    def _query_chromium(self) -> dict:
        url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        r = self._get(url)
        if not r["ok"]:
            return {"error": r["error"]}
        data = json.loads(r["text"])
        versions = data.get("versions", [])
        if not versions:
            return {"error": "未解析到版本"}
        latest = versions[-1]
        version = latest.get("version", "")
        downloads = latest.get("downloads", {}).get("chrome", {})
        asset_url = downloads.get("url", "") if isinstance(downloads, dict) else ""
        asset_name = f"chrome-win64-{version}.zip"
        return {
            "upstream_version": version,
            "upstream_source": "Google Chrome for Testing",
            "asset_url": asset_url,
            "asset_name": asset_name,
        }

    # -------------------------------------------------------------------------
    # 工具方法
    # -------------------------------------------------------------------------
    @staticmethod
    def _sort_versions(versions: list) -> list:
        def key(v):
            clean = re.sub(r'[a-zA-Z].*$', '', v)
            parts = clean.split('.')
            nums = [int(p) if p.isdigit() else 0 for p in parts[:4]]
            while len(nums) < 4:
                nums.append(0)
            return tuple(nums)
        return sorted(versions, key=key, reverse=True)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="上游版本查询原子")
    parser.add_argument("--tool-name", required=True, help="工具名")
    parser.add_argument("--query-param", required=True, help="查询参数（python/node/opencode_cli/llama_cpp_python/chromium）")
    parser.add_argument("--target-version", default="", help="指定目标版本（可选，用于锁定）")
    args = parser.parse_args()

    checker = UpstreamChecker()
    result = checker.query(args.tool_name, args.query_param, args.target_version)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if not result.get("error") else 1)


if __name__ == "__main__":
    sys.exit(main())
