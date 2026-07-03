#!/usr/bin/env python3
"""
插件：GitHub REST API 封装（GitHub API）
标签：github, api
依赖：env_config

职责：提供 GitHub REST API 调用封装，自动处理 UTF-8 encoding、认证头、错误解析。
      被 py-tools/fetch_issue.py 等工具通过 py_lib 加载。

用法：
    import sys
    sys.path.insert(0, r"...\\scripts")
    from py_lib import load_plugins
    registry = load_plugins(devroot="D:/pjt/cursor/cs_py", tags=["github", "api"])

    creds = registry.github_api.get_credentials()
    issue = registry.github_api.get_issue(owner=creds["owner"], repo=creds["repo"],
                                          number=1, pat=creds["pat"])
    comments = registry.github_api.list_comments(owner=creds["owner"], repo=creds["repo"],
                                                 number=1, pat=creds["pat"])
"""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# 插件注册表注入点（由 py_lib 在加载时注入）
__plugin_registry__ = None


def _get_devroot() -> Optional[Path]:
    """从 registry 或环境变量获取 devroot"""
    if __plugin_registry__ is not None and hasattr(__plugin_registry__, "devroot"):
        return Path(__plugin_registry__.devroot)
    devroot_env = os.environ.get("DEVROOT", "")
    if devroot_env:
        return Path(devroot_env)
    return None


def get_credentials(env_file: Optional[str] = None) -> Dict[str, str]:
    """
    从 .env 读取 GitHub 认证信息。

    返回:
        dict: {pat, username, repo_url, owner, repo}

    异常:
        ValueError: 必填项缺失
    """
    devroot = _get_devroot()
    if env_file is None and devroot is not None:
        env_file = devroot / ".env"

    config: Dict[str, str] = {}
    env_path = Path(env_file) if env_file else Path(".env")
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")

    pat = config.get("GITHUB_PAT", "")
    username = config.get("GITHUB_USERNAME", "")
    repo_url = config.get("GITHUB_REPO_URL", "")

    if not pat:
        raise ValueError("GITHUB_PAT 未在 .env 中配置")
    if not username:
        raise ValueError("GITHUB_USERNAME 未在 .env 中配置")
    if not repo_url:
        raise ValueError("GITHUB_REPO_URL 未在 .env 中配置")

    match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
    if not match:
        raise ValueError(f"无法从 GITHUB_REPO_URL 提取 owner/repo: {repo_url}")

    return {
        "pat": pat,
        "username": username,
        "repo_url": repo_url,
        "owner": match.group(1),
        "repo": match.group(2),
    }


def build_headers(pat: str) -> Dict[str, str]:
    """构造 GitHub API 请求头。"""
    return {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "deploy-git-isolated/1.0",
    }


def invoke_api(
    method: str,
    uri: str,
    pat: str,
    body: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    return_headers: bool = False,
) -> Any:
    """
    通用 GitHub API 调用，自动处理 UTF-8 encoding。

    参数:
        method: HTTP 方法 GET / POST / PATCH / DELETE
        uri: 完整 API URL
        pat: GitHub PAT
        body: 请求体（dict），自动转为 UTF-8 JSON
        timeout: 超时秒数，默认 30
        return_headers: 是否同时返回响应头（用于分页 Link 解析）

    返回:
        API 响应对象（已解析 JSON），或 (响应对象, headers) 当 return_headers=True

    异常:
        urllib.error.HTTPError: HTTP 错误
        urllib.error.URLError: 网络错误
    """
    headers = build_headers(pat)

    data: Optional[bytes] = None
    if body is not None:
        body_json = json.dumps(body, ensure_ascii=False)
        data = body_json.encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(
        uri, data=data, headers=headers, method=method.upper()
    )

    print(f"[GitHub API] {method.upper()} {uri}")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8")
            result = json.loads(resp_body) if resp_body else {}
            if return_headers:
                return result, dict(resp.headers)
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        raise urllib.error.HTTPError(
            e.url, e.code, f"{e.reason} | Response: {error_body}", e.headers, e.fp
        )


def get_issue(owner: str, repo: str, number: int, pat: str) -> Dict[str, Any]:
    """获取 Issue 详情。"""
    uri = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    return invoke_api("GET", uri, pat)


def list_comments(
    owner: str, repo: str, number: int, pat: str,
    per_page: int = 100, since: Optional[str] = None, page: Optional[int] = None
) -> List[Dict[str, Any]]:
    """列出 Issue 下的评论。支持分页、时间筛选。"""
    params = []
    if per_page:
        params.append(f"per_page={per_page}")
    if since:
        params.append(f"since={since}")
    if page:
        params.append(f"page={page}")

    uri = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    if params:
        uri += "?" + "&".join(params)

    result = invoke_api("GET", uri, pat)
    return result if isinstance(result, list) else []


def _parse_next_link(link_header: str) -> Optional[str]:
    """从 Link header 中提取 next 页面的 URL。"""
    if not link_header:
        return None
    for part in link_header.split(","):
        match = re.search(r'<([^>]+)>;\s*rel="next"', part.strip())
        if match:
            return match.group(1)
    return None


def list_comments_all(owner: str, repo: str, number: int, pat: str) -> List[Dict[str, Any]]:
    """列出 Issue 下的所有评论（自动遍历分页）。"""
    all_comments: List[Dict[str, Any]] = []
    uri = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments?per_page=100"

    while uri:
        result, headers = invoke_api("GET", uri, pat, return_headers=True)
        if isinstance(result, list):
            all_comments.extend(result)

        link_header = headers.get("Link", "")
        uri = _parse_next_link(link_header)

    return all_comments


def get_comment(owner: str, repo: str, comment_id: int, pat: str) -> Dict[str, Any]:
    """通过 comment_id 精准获取单条评论。"""
    uri = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"
    result = invoke_api("GET", uri, pat)
    return result if isinstance(result, dict) else {}


def create_issue(
    owner: str, repo: str, pat: str, title: str, body: str = "", labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """创建 GitHub Issue。"""
    uri = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload: Dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    return invoke_api("POST", uri, pat, body=payload)


def update_issue(
    owner: str, repo: str, number: int, pat: str, title: Optional[str] = None,
    body: Optional[str] = None, labels: Optional[List[str]] = None, state: Optional[str] = None
) -> Dict[str, Any]:
    """更新 GitHub Issue。"""
    uri = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
    payload: Dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if body is not None:
        payload["body"] = body
    if labels is not None:
        payload["labels"] = labels
    if state is not None:
        payload["state"] = state
    return invoke_api("PATCH", uri, pat, body=payload)


def create_comment(owner: str, repo: str, number: int, pat: str, body: str) -> Dict[str, Any]:
    """在 Issue 下追加评论。"""
    uri = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    return invoke_api("POST", uri, pat, body={"body": body})
