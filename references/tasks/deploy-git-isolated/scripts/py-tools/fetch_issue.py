#!/usr/bin/env python3
"""
fetch_issue.py — 获取 GitHub Issue 完整内容（含评论）
标签：py-tools

职责：通过 py_lib 加载 github_api 插件，获取指定 Issue 的完整 body 和全部评论。
      输出格式与 PS 版 fetch-issue-full.ps1 对齐。

用法：
    python fetch_issue.py --issue-number 1
    python fetch_issue.py --devroot "D:/pjt/cursor/cs_py" --issue-number 2
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 确保 py_lib 可导入
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def main():
    parser = argparse.ArgumentParser(description="获取 GitHub Issue 完整内容")
    parser.add_argument(
        "--devroot",
        help="Devroot 路径（如未传入，由 py_lib 自动探测）"
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        default=1,
        help="Issue 编号（默认: 1）"
    )
    args = parser.parse_args()

    # 加载 github_api 插件
    registry = load_plugins(devroot=args.devroot, tags=["github", "api"])
    api = registry.github_api

    # 读取认证
    creds = api.get_credentials()

    # 获取 Issue 详情
    issue = api.get_issue(
        owner=creds["owner"],
        repo=creds["repo"],
        number=args.issue_number,
        pat=creds["pat"]
    )

    print(f"========== ISSUE #{args.issue_number} BODY ==========")
    print(issue.get("body", ""))
    print()
    print("========== COMMENTS ==========")

    # 获取评论列表
    comments = api.list_comments(
        owner=creds["owner"],
        repo=creds["repo"],
        number=args.issue_number,
        pat=creds["pat"]
    )

    for i, c in enumerate(comments, 1):
        user = c.get("user", {}).get("login", "unknown")
        created = c.get("created_at", "")
        body = c.get("body", "")
        print(f"----- Comment #{i} by {user} at {created} -----")
        print(body)
        print()


if __name__ == "__main__":
    main()
