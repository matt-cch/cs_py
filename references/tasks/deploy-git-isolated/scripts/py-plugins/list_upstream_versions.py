#!/usr/bin/env python3
r"""
Plugin: list_upstream_versions
标签：runtime, upstream
职责：根据传入的 JSON 配置查询上游可用版本列表，支持 target_version 存在性验证。

配置 JSON 格式：
{
    "url": "https://mirrors.aliyun.com/python-release/windows/",
    "parser_type": "html_regex" | "json_array",
    "parser_config": {
        "pattern": "regex_with_capture_group"        // html_regex
        // 或
        "field_path": "versions.version"              // json_array
    },
    "version_transform": "none" | "strip_v_prefix"
}

输出 JSON：
{
    "versions": ["3.13.14", "3.13.13", ...],
    "target_exists": true | false | null,
    "error": null | "..."
}
"""
import argparse
import json
import re
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")


def fetch(url: str, timeout: int = 15) -> dict:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "list-upstream-versions/1.0"})
        if resp.status_code == 200:
            return {"ok": True, "text": resp.text}
        return {"ok": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def parse_html_regex(text: str, pattern: str) -> list:
    matches = re.findall(pattern, text)
    seen = set()
    result = []
    for m in matches:
        ver = m
        if ver not in seen:
            seen.add(ver)
            result.append(ver)
    return result


def parse_json_array(text: str, field_path: str) -> list:
    data = json.loads(text)
    parts = field_path.split(".")
    current = data
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current.get(part, [])
        elif isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        else:
            return []
    last = parts[-1]
    if isinstance(current, dict):
        current = current.get(last, [])
    elif isinstance(current, list) and last.isdigit():
        current = current[int(last)]
    if not isinstance(current, list):
        return []
    if current and isinstance(current[0], dict):
        versions = [item.get(last, "") for item in current if isinstance(item, dict)]
    else:
        versions = current
    return [str(v) for v in versions if v]


def transform_versions(versions: list, transform: str) -> list:
    if transform == "strip_v_prefix":
        return [v.lstrip("v") for v in versions]
    return versions


def sort_versions(versions: list) -> list:
    def key(v):
        clean = re.sub(r'[a-zA-Z].*$', '', v)
        parts = clean.split('.')
        nums = [int(p) if p.isdigit() else 0 for p in parts[:4]]
        while len(nums) < 4:
            nums.append(0)
        return tuple(nums)
    return sorted(versions, key=key, reverse=True)


def query(config: dict, target_version: str = "") -> dict:
    url = config["url"]
    parser_type = config.get("parser_type", "html_regex")
    parser_config = config.get("parser_config", {})
    transform = config.get("version_transform", "none")

    fetched = fetch(url)
    if not fetched["ok"]:
        return {"versions": [], "error": fetched["error"]}

    if parser_type == "html_regex":
        versions = parse_html_regex(fetched["text"], parser_config.get("pattern", ""))
    elif parser_type == "json_array":
        versions = parse_json_array(fetched["text"], parser_config.get("field_path", ""))
    else:
        return {"versions": [], "error": f"未知 parser_type: {parser_type}"}

    versions = transform_versions(versions, transform)
    versions = sort_versions(versions)

    result = {"versions": versions, "error": None}
    if target_version:
        if target_version in versions:
            result["target_exists"] = True
            result["target_index"] = versions.index(target_version)
        else:
            result["target_exists"] = False
            result["error"] = f"版本 {target_version} 不在可用列表中"
            result["available_top10"] = versions[:10]

    return result


def main():
    parser = argparse.ArgumentParser(description="上游版本列表查询 Plugin")
    parser.add_argument("--config-json", required=True, help="查询配置 JSON 字符串")
    parser.add_argument("--target-version", default="", help="要验证的目标版本")
    args = parser.parse_args()

    config = json.loads(args.config_json)
    result = query(config, args.target_version)

    print(json.dumps(result, ensure_ascii=False))
    return 0 if not result.get("error") or result.get("versions") else 1


if __name__ == "__main__":
    sys.exit(main())
