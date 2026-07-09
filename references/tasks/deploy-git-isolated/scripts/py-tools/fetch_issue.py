#!/usr/bin/env python3
"""
fetch_issue.py — 获取 GitHub Issue 完整内容（含评论）
标签：py-tools

职责：通过 py_lib 加载 github_api 插件，获取指定 Issue 的完整 body 和全部评论。
      输出格式与 PS 版 fetch-issue-full.ps1 对齐。

用法：
    python fetch_issue.py --issue-number 1
    python fetch_issue.py --devroot "D:/pjt/cursor/cs_py" --issue-number 2
    python fetch_issue.py --devroot "D:/pjt/cursor/cs_py" --repo-url "https://github.com/jywl-team/jywl-lab.git" --issue-number 1
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
        "--repo-url",
        default=None,
        help="仓库 URL（polyrepo 场景从 manifest 传入，覆盖 .env 中的 GITHUB_REPO_URL）"
    )
    parser.add_argument(
        "--issue-number",
        type=int,
        default=1,
        help="Issue 编号（默认: 1）"
    )
    parser.add_argument(
        "--output",
        help="输出文件路径（直接写入 UTF-8，避免 stdout 编码问题）"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="获取所有评论（自动遍历分页，默认只返回最新 100 条）"
    )
    parser.add_argument(
        "--since",
        help="只获取该时间之后的评论（ISO 8601 格式，如 2026-07-03T00:00:00Z）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="限制返回的评论数量（取最后 N 条，与 --all 或默认列表配合使用）"
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="只获取最新一条评论（快捷方式，等效于 --all --limit 1）"
    )
    parser.add_argument(
        "--comment-id",
        type=int,
        help="通过评论 ID 精准获取单条评论"
    )
    args = parser.parse_args()

    # 加载 github_api 插件
    registry = load_plugins(devroot=args.devroot, tags=["github", "api"])
    api = registry.github_api

    # 读取认证
    creds = api.get_credentials()

    # polyrepo 场景：外部传入 --repo-url 时覆盖
    if args.repo_url:
        import re
        m = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$', args.repo_url)
        if m:
            creds["owner"] = m.group(1)
            creds["repo"] = m.group(2)
            print(f"[OK] repo_url 来自参数覆盖: {args.repo_url}")
        else:
            print(f"[WARN] --repo-url 格式无法解析: {args.repo_url}")

    # 获取 Issue 详情
    issue = api.get_issue(
        owner=creds["owner"],
        repo=creds["repo"],
        number=args.issue_number,
        pat=creds["pat"]
    )

    lines = []
    lines.append(f"========== ISSUE #{args.issue_number} BODY ==========")
    lines.append(issue.get("body", ""))
    lines.append("")
    lines.append("========== COMMENTS ==========")

    # 精准单条模式
    if args.comment_id:
        comment = api.get_comment(creds["owner"], creds["repo"], args.comment_id, creds["pat"])
        comments = [comment] if comment else []
        lines.append(f"[模式] 精准单条查询 (comment_id={args.comment_id})")
    else:
        # 快捷模式：--latest 等效于 --all --limit 1
        if args.latest:
            args.all = True
            args.limit = 1

        if args.all:
            comments = api.list_comments_all(creds["owner"], creds["repo"], args.issue_number, creds["pat"])
            lines.append(f"[模式] 全量遍历 (共 {len(comments)} 条)")
        elif args.since:
            comments = api.list_comments(
                creds["owner"], creds["repo"], args.issue_number, creds["pat"],
                per_page=100, since=args.since
            )
            lines.append(f"[模式] since 筛选 (since={args.since}, 返回 {len(comments)} 条)")
        else:
            comments = api.list_comments(
                creds["owner"], creds["repo"], args.issue_number, creds["pat"],
                per_page=100
            )
            lines.append(f"[模式] 默认最新 100 条 (返回 {len(comments)} 条)")

        if args.limit and comments:
            comments = comments[-args.limit:]
            lines.append(f"[限制] 取最后 {len(comments)} 条")

    for i, c in enumerate(comments, 1):
        user = c.get("user", {}).get("login", "unknown")
        created = c.get("created_at", "")
        body = c.get("body", "")
        cid = c.get("id", "")
        lines.append(f"----- Comment #{i} (ID: {cid}) by {user} at {created} -----")
        lines.append(body)
        lines.append("")

    text = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(text, encoding="utf-8")
        print(f"[OK] 已写入 {out_path} ({len(text)} 字符)")
    else:
        print(text)


if __name__ == "__main__":
    main()
