#!/usr/bin/env python3
r"""
runtime-common/atomic-query-upstream.py — 上游版本查询原子（v2.0.0）
标签：atomic, runtime
职责：根据 query_param 选择工具配置 → 调用 list_upstream_versions plugin 获取版本列表 →
      验证 target_version 存在性 → 组装 asset_url/asset_name 返回。

版本列表查询全部走 list_upstream_versions plugin（JSON 传参），
只有 GitHub Release 类工具（OpenCode/llama）保留直接 API 查询。
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 加载 plugin
_PLUGINS_DIR = Path(__file__).parent.parent.parent / "py-plugins"
if str(_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGINS_DIR))
import list_upstream_versions


# =============================================================================
# 工具查询配置（JSON 传参）
# =============================================================================

_LIST_CONFIGS = {
    "python": {
        "url": "https://mirrors.aliyun.com/python-release/windows/",
        "parser_type": "html_regex",
        "parser_config": {"pattern": r'python-(\d+\.\d+\.\d+)-embed-amd64\.zip'},
        "version_transform": "none",
        "source_name": "阿里云 python-release",
        "url_template": "https://mirrors.aliyun.com/python-release/windows/python-{version}-embed-amd64.zip",
        "asset_name_template": "python-{version}-embed-amd64.zip",
    },
    "node": {
        "url": "https://mirrors.aliyun.com/nodejs-release/",
        "parser_type": "html_regex",
        "parser_config": {"pattern": r'href="(v\d+\.\d+\.\d+)/"'},
        "version_transform": "strip_v_prefix",
        "source_name": "阿里云 nodejs-release",
        "url_template": "https://mirrors.aliyun.com/nodejs-release/v{version}/node-v{version}-win-x64.zip",
        "asset_name_template": "node-v{version}-win-x64.zip",
    },
    "chromium": {
        "url": "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json",
        "parser_type": "json_array",
        "parser_config": {"field_path": "versions.version"},
        "version_transform": "none",
        "source_name": "Google Chrome for Testing",
        "url_template": "https://registry.npmmirror.com/-/binary/chrome-for-testing/{version}/win64/chrome-win64.zip",
        "asset_name_template": "chrome-win64-{version}.zip",
    },
}


# =============================================================================
# 通用列表查询（走 plugin）
# =============================================================================

def _query_list(param: str, target_version: str = "") -> dict:
    cfg = _LIST_CONFIGS.get(param)
    if not cfg:
        return None  # 非列表查询工具，fallback 到直接 API

    list_config = {
        "url": cfg["url"],
        "parser_type": cfg["parser_type"],
        "parser_config": cfg["parser_config"],
        "version_transform": cfg.get("version_transform", "none"),
    }

    result = list_upstream_versions.query(list_config, target_version)
    if result.get("error"):
        return {
            "error": result["error"],
            "available_top10": result.get("available_top10", []),
        }

    versions = result["versions"]
    latest = versions[0] if versions else ""
    version = target_version if (target_version and result.get("target_exists")) else latest

    return {
        "upstream_version": version,
        "upstream_source": cfg["source_name"],
        "asset_url": cfg["url_template"].replace("{version}", version),
        "asset_name": cfg["asset_name_template"].replace("{version}", version),
        "error": None,
    }


# =============================================================================
# GitHub Release 直接查询（无版本列表页）
# =============================================================================

import requests


class _GitHubReleaseChecker:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "atomic-query-upstream/2.0"})

    def _get(self, url: str) -> dict:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                return {"ok": True, "text": resp.text}
            return {"ok": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def query_opencode(self, target_version: str = "") -> dict:
        url = "https://api.github.com/repos/anomalyco/opencode/releases/latest"
        r = self._get(url)
        if not r["ok"]:
            return {"error": r["error"]}
        data = json.loads(r["text"])
        tag = data.get("tag_name", "").lstrip("v")
        version = target_version or tag
        asset_url = ""
        asset_name = ""
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if "windows" in name.lower() and name.endswith(".zip"):
                asset_url = asset.get("browser_download_url", "")
                asset_name = name
                break
        return {
            "upstream_version": version,
            "upstream_source": "GitHub Release anomalyco/opencode",
            "asset_url": asset_url,
            "asset_name": asset_name,
            "error": None,
        }

    def query_llama_cpp_python(self, target_version: str = "") -> dict:
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
            "error": None,
        }


# =============================================================================
# 主入口
# =============================================================================

def query(tool_name: str, query_param: str, target_version: str = "") -> dict:
    result = {"upstream_version": None, "upstream_source": None, "asset_url": "", "asset_name": "", "error": None}

    # 1. 优先走列表查询 plugin
    list_result = _query_list(query_param, target_version)
    if list_result is not None:
        return list_result

    # 2. GitHub Release 类工具
    checker = _GitHubReleaseChecker()
    try:
        if query_param == "opencode_cli":
            result = checker.query_opencode(target_version)
        elif query_param == "llama_cpp_python":
            result = checker.query_llama_cpp_python(target_version)
        else:
            result["error"] = f"未知查询参数: {query_param}"
    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="上游版本查询原子")
    parser.add_argument("--tool-name", required=True)
    parser.add_argument("--query-param", required=True)
    parser.add_argument("--target-version", default="")
    args = parser.parse_args()

    result = query(args.tool_name, args.query_param, args.target_version)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if not result.get("error") else 1)


if __name__ == "__main__":
    sys.exit(main())
