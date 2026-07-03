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
import re
import sys
import atexit
from pathlib import Path

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
    "chromium_stable": {
        "url": "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json",
        "parser_type": "json_field",
        "parser_config": {"field_path": "channels.Stable.version"},
        "version_transform": "none",
        "source_name": "Google Chrome for Testing (Stable)",
        "url_template": "https://registry.npmmirror.com/-/binary/chrome-for-testing/{version}/win64/chrome-win64.zip",
        "asset_name_template": "chrome-win64-{version}.zip",
    },
}


# =============================================================================
# 通用列表查询（走 plugin）
# =============================================================================

def _parse_ver(v: str) -> tuple:
    """语义版本解析，用于约束比较"""
    clean = re.sub(r'^[vV]', '', v)
    parts = clean.split('.')
    nums = [int(p) if p.isdigit() else 0 for p in parts[:4]]
    while len(nums) < 4:
        nums.append(0)
    return tuple(nums)


def _ver_gt(a: str, b: str) -> bool:
    return _parse_ver(a) > _parse_ver(b)


def _apply_constraint(versions: list, constraint: dict, target_version: str = "") -> tuple:
    """
    应用版本约束过滤。
    返回 (effective_versions, constraint_applied, constraint_msg)
    """
    if not constraint:
        return versions, False, ""

    ctype = constraint.get("type", "")
    cvalue = constraint.get("value", "")
    creason = constraint.get("reason", "")

    if ctype == "pin":
        # 固定版本：只保留等于 pin 值的版本
        filtered = [v for v in versions if v == cvalue]
        msg = f"pin约束: {cvalue} ({creason})"
        return filtered, True, msg

    elif ctype == "max":
        # 最大版本：过滤掉超过 max 的版本
        filtered = [v for v in versions if not _ver_gt(v, cvalue)]
        msg = f"max约束: <= {cvalue} ({creason})"
        return filtered, True, msg

    return versions, True, f"未知约束类型: {ctype}"


def _query_list(param: str, target_version: str = "", constraint: dict = None, stable_only: bool = False) -> dict:
    # stable_only 映射：chromium → chromium_stable
    if stable_only and param == "chromium":
        param = "chromium_stable"
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

    # 应用约束过滤
    filtered_versions, constrained, constraint_msg = _apply_constraint(versions, constraint, target_version)

    latest = filtered_versions[0] if filtered_versions else ""
    version = target_version if (target_version and result.get("target_exists")) else latest

    return {
        "upstream_version": version,
        "upstream_source": cfg["source_name"],
        "asset_url": cfg["url_template"].replace("{version}", version) if version else "",
        "asset_name": cfg["asset_name_template"].replace("{version}", version) if version else "",
        "constrained": constrained,
        "constraint_msg": constraint_msg,
        "error": None if version else "约束过滤后无可用版本",
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
            lower = name.lower()
            if "windows" in lower and "x64" in lower and name.endswith(".zip"):
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

    def _find_stable_release(self, owner: str, repo: str) -> dict:
        """
        遍历 releases 列表，返回第一个 prerelease=false 的稳定版。
        兜底：如果列表中没有 stable，返回列表第一项。
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/releases"
        r = self._get(url)
        if not r["ok"]:
            return {"error": r["error"]}

        releases = json.loads(r["text"])
        if not isinstance(releases, list):
            return {"error": "releases 返回格式非列表"}

        for rel in releases:
            if isinstance(rel, dict) and not rel.get("prerelease", True):
                return {"ok": True, "data": rel}

        # 兜底：全列表都是 prerelease，取第一项
        if releases:
            return {"ok": True, "data": releases[0], "fallback": "未找到 stable，取第一项"}
        return {"error": "releases 列表为空"}

    def query_github_release(self, owner: str, repo: str, target_version: str = "",
                             asset_filter: callable = None, source_name: str = "",
                             stable_only: bool = False) -> dict:
        """
        通用 GitHub Release 查询。
        默认查询 latest release，支持 target_version 指定标签。
        stable_only=True 时，遍历 releases 列表找第一个非 prerelease 的稳定版。
        """
        if target_version:
            url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/v{target_version}"
            r = self._get(url)
        elif stable_only:
            r = self._find_stable_release(owner, repo)
            if r.get("error"):
                return {"error": r["error"]}
            data = r["data"]
            tag = data.get("tag_name", "").lstrip("v")
            version = tag
            asset_url = ""
            asset_name = ""
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if asset_filter and asset_filter(name):
                    asset_url = asset.get("browser_download_url", "")
                    asset_name = name
                    break
            result = {
                "upstream_version": version,
                "upstream_source": source_name or f"GitHub Release {owner}/{repo}",
                "asset_url": asset_url,
                "asset_name": asset_name,
                "error": None,
            }
            if r.get("fallback"):
                result["fallback"] = r["fallback"]
            return result
        else:
            url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
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
            if asset_filter and asset_filter(name):
                asset_url = asset.get("browser_download_url", "")
                asset_name = name
                break

        return {
            "upstream_version": version,
            "upstream_source": source_name or f"GitHub Release {owner}/{repo}",
            "asset_url": asset_url,
            "asset_name": asset_name,
            "error": None,
        }


# =============================================================================
# 主入口
# =============================================================================

def query(tool_name: str, query_param: str, target_version: str = "", constraint: dict = None, stable_only: bool = False) -> dict:
    result = {"upstream_version": None, "upstream_source": None, "asset_url": "", "asset_name": "", "error": None}

    # 1. 优先走列表查询 plugin
    list_result = _query_list(query_param, target_version, constraint, stable_only=stable_only)
    if list_result is not None:
        return list_result

    # 2. GitHub Release 类工具
    checker = _GitHubReleaseChecker()
    try:
        if query_param == "opencode_cli":
            result = checker.query_opencode(target_version)
        elif query_param == "llama_cpp_python":
            result = checker.query_llama_cpp_python(target_version)
        elif query_param == "git":
            result = checker.query_github_release(
                "git-for-windows", "git", target_version,
                asset_filter=lambda n: "MinGit" in n and "64-bit" in n and n.endswith(".zip") or "PortableGit" in n,
                source_name="GitHub Release git-for-windows/git",
                stable_only=stable_only
            )
        elif query_param == "gh_cli":
            result = checker.query_github_release(
                "cli", "cli", target_version,
                asset_filter=lambda n: "windows_amd64" in n and n.endswith(".zip"),
                source_name="GitHub Release cli/cli",
                stable_only=stable_only
            )
        else:
            result["error"] = f"未知查询参数: {query_param}"
    except Exception as e:
        result["error"] = str(e)

    # 3. 应用约束（GitHub Release 类）
    if constraint and result.get("upstream_version"):
        ctype = constraint.get("type", "")
        cvalue = constraint.get("value", "")
        creason = constraint.get("reason", "")
        upstream_ver = result["upstream_version"]

        if ctype == "pin":
            result["constrained"] = True
            if upstream_ver != cvalue:
                result["upstream_version"] = cvalue
                result["constraint_msg"] = f"pin约束: {cvalue} ({creason})"
            else:
                result["constraint_msg"] = f"pin约束: {cvalue} ({creason}, 当前版本已固定)"
        elif ctype == "max":
            result["constrained"] = True
            if _ver_gt(upstream_ver, cvalue):
                result["upstream_version"] = cvalue
                result["constraint_msg"] = f"max约束: <= {cvalue} ({creason})"
            else:
                result["constraint_msg"] = f"max约束: <= {cvalue} ({creason}, 当前版本符合)"

    return result


def main():
    parser = argparse.ArgumentParser(description="上游版本查询原子")
    parser.add_argument("--tool-name", required=True)
    parser.add_argument("--query-param", required=True)
    parser.add_argument("--target-version", default="")
    parser.add_argument("--constraint-json", default="", help="版本约束 JSON，如 {type:max,value:3.13.99}")
    parser.add_argument("--stable-only", action="store_true", help="仅取 GitHub Release 的非 prerelease 稳定版")
    args = parser.parse_args()

    constraint = json.loads(args.constraint_json) if args.constraint_json else None
    result = query(args.tool_name, args.query_param, args.target_version, constraint, stable_only=args.stable_only)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if not result.get("error") else 1)


if __name__ == "__main__":
    sys.exit(main())
