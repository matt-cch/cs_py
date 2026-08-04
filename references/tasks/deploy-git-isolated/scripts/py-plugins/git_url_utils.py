#!/usr/bin/env python3
r"""
插件：Git URL 规范化工具（git_url_utils）
标签：core, git

职责：提供 Git Remote URL 的规范化（canonicalize）函数，供所有需要比较/匹配
      git URL 的脚本和插件统一使用。消除 .git 后缀、尾部斜杠、大小写差异
      导致的字符串比较失败。

用法（同层插件直接 import）：
    from git_url_utils import canonicalize_url
    if canonicalize_url(a) == canonicalize_url(b):
        print("URL 匹配")
"""


def canonicalize_url(url: str) -> str:
    """URL 规范化：去掉尾部斜杠和 .git 后缀，统一小写。

    规则：
      1. 去除尾部空白和尾部斜杠（/）
      2. 去除尾部 .git（不区分大小写）
      3. 统一转为小写

    示例：
      - "https://github.com/user/repo.git" -> "https://github.com/user/repo"
      - "https://github.com/user/repo/"    -> "https://github.com/user/repo"
      - "HTTPS://GITHUB.COM/USER/REPO.GIT" -> "https://github.com/user/repo"
    """
    if not url:
        return ""
    url = url.strip().rstrip("/")
    if url.lower().endswith(".git"):
        url = url[:-4]
    return url.lower()
