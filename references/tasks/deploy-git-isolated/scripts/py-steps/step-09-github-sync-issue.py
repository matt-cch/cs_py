#!/usr/bin/env python3
"""
step-09-github-sync-issue.py — Step 9: Issue Sync
标签：py-steps

职责：commit/push 后，将提交记录同步到 GitHub Issue（追加评论）。
与 PS1 版对齐：读取 .env 获取 PAT，构造 API 请求追加 comment。

用法：
    python step-09-github-sync-issue.py --devroot "D:/pjt/cursor/cs_py" --issue 1
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def _read_env_config(devroot: Path) -> dict:
    """与 PS1 Read-EnvConfig 对齐"""
    env = {}
    env_path = devroot / ".env"
    if not env_path.exists():
        print("[ERROR] .env 文件不存在")
        sys.exit(1)

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env[key] = val

    for key in ["GITHUB_USERNAME", "GITHUB_REPO_URL"]:
        if not env.get(key, "").strip():
            print(f"[ERROR] {key} 未在 .env 中配置")
            sys.exit(1)

    pat = env.get("GITHUB_PAT", "").strip()
    if not pat or pat == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("[ERROR] GITHUB_PAT 未配置或仍是占位符")
        sys.exit(1)

    return env


def _get_commit_info(git_exe: Path, devroot: Path) -> dict:
    """获取当前 commit 信息及变更文件列表"""
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, encoding="utf-8"
    )
    commit_hash = result.stdout.strip()

    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "log", "-1", "--pretty=format:%s"],
        capture_output=True, text=True, encoding="utf-8"
    )
    commit_msg = result.stdout.strip()

    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, encoding="utf-8"
    )
    branch = result.stdout.strip()

    # 获取变更文件列表（--name-status 格式：A/M/D + 路径）
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", "--name-status", "HEAD~1..HEAD"],
        capture_output=True, text=True, encoding="utf-8"
    )
    changes = {"A": [], "M": [], "D": [], "R": []}
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0][0]  # 取第一个字符（A/M/D/R）
        path = parts[-1]
        if status in changes:
            changes[status].append(path)
        else:
            changes["M"].append(path)  # fallback

    # 获取统计数字
    result = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", "--shortstat", "HEAD~1..HEAD"],
        capture_output=True, text=True, encoding="utf-8"
    )
    stat = result.stdout.strip()

    return {
        "hash": commit_hash,
        "msg": commit_msg,
        "branch": branch,
        "changes": changes,
        "stat": stat,
    }


def main():
    parser = argparse.ArgumentParser(description="Step 9: Issue Sync")
    parser.add_argument("--devroot", default=None, help="Devroot 路径")
    parser.add_argument("--issue", type=int, default=1, help="Issue 编号 (默认 1)")
    parser.add_argument("--body", default=None, help="自定义评论内容（覆盖全部自动生成）")
    parser.add_argument("--summary", default=None, help="变更摘要（语义化描述，支持 \\n 换行）。如未传入，优先从 --meta 文件读取，最后 fallback 到 commit message")
    parser.add_argument("--meta", default=None, help="外部 JSON 配置文件路径（默认使用 schema/json/issue-comment-meta-template.json）")
    args = parser.parse_args()

    registry = load_plugins(devroot=args.devroot, tags=["core"])
    devroot = Path(registry.devroot)
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    if not git_exe.exists():
        print(f"[ERROR] 隔离 Git 未找到: {git_exe}")
        sys.exit(1)

    print("")
    print("=" * 40)
    print("Step 9: Issue Sync")
    print("=" * 40)

    cfg = _read_env_config(devroot)
    pat = cfg["GITHUB_PAT"].strip()

    # 提取 owner/repo
    repo_url = cfg["GITHUB_REPO_URL"].strip()
    import re
    m = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$', repo_url)
    if not m:
        print(f"[ERROR] 无法从 GITHUB_REPO_URL 提取 owner/repo: {repo_url}")
        sys.exit(1)
    owner, repo = m.group(1), m.group(2)

    # 读取 meta 配置（模板 + 实时摘要）
    meta_data = {"summary": "", "categories": []}
    if args.meta:
        meta_path = Path(args.meta)
    else:
        # 默认模板路径
        meta_path = devroot / "references" / "tasks" / "deploy-git-isolated" / "schema" / "json" / "issue-comment-meta-template.json"

    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
        except Exception as e:
            print(f"[WARN] 读取 meta 文件失败: {e}")

    # 构造评论内容
    if args.body:
        body = args.body
    else:
        from datetime import datetime, timezone
        info = _get_commit_info(git_exe, devroot)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        lines = []
        lines.append(f"## 变更记录 — {now}")
        lines.append("")
        lines.append("| Commit | Branch | Message | Date |")
        lines.append("|--------|--------|---------|------|")
        lines.append(f"| `{info['hash']}` | `{info['branch']}` | {info['msg']} | {now[:10]} |")
        lines.append("")

        # 变更摘要（优先级: --summary > meta.summary > commit message）
        lines.append("### 变更摘要")
        lines.append("")
        summary_text = ""
        if args.summary:
            summary_text = args.summary.replace("\\n", "\n")
        elif meta_data.get("summary"):
            summary_text = meta_data.get("summary", "")
        else:
            summary_text = info['msg']

        for sline in summary_text.splitlines():
            lines.append(sline)
        lines.append("")

        # AI 语义摘要（来自 meta.ai_summary）
        ai_summary = meta_data.get("ai_summary", "")
        if ai_summary:
            lines.append("### AI 语义摘要")
            lines.append("")
            for sline in ai_summary.splitlines():
                lines.append(sline)
            lines.append("")

        # 语义分类（来自 meta.categories）
        categories = meta_data.get("categories", [])
        if categories:
            for cat in categories:
                cat_name = cat.get("name", "")
                items = cat.get("items", [])
                if cat_name and items:
                    lines.append(f"**{cat_name}**:")
                    for item in items:
                        lines.append(f"- {item}")
                    lines.append("")

        if info["stat"]:
            lines.append(f"**文件统计**: {info['stat']}")
            lines.append("")

        changes = info["changes"]
        total = sum(len(v) for v in changes.values())
        if total > 0:
            lines.append(f"### 变更文件 ({total} 个)")
            lines.append("")
            if changes["A"]:
                lines.append(f"**新增 ({len(changes['A'])}):**")
                for p in changes["A"]:
                    lines.append(f"- `{p}`")
                lines.append("")
            if changes["M"]:
                lines.append(f"**修改 ({len(changes['M'])}):**")
                for p in changes["M"]:
                    lines.append(f"- `{p}`")
                lines.append("")
            if changes["D"]:
                lines.append(f"**删除 ({len(changes['D'])}):**")
                for p in changes["D"]:
                    lines.append(f"- `{p}`")
                lines.append("")
            if changes["R"]:
                lines.append(f"**重命名 ({len(changes['R'])}):**")
                for p in changes["R"]:
                    lines.append(f"- `{p}`")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"> **关联**: #{args.issue}")
        body = "\n".join(lines)

    print(f"[OK] 目标 Issue: #{args.issue}")
    print(f"[OK] 仓库: {owner}/{repo}")
    print(f"[OK] 评论内容预览 ({len(body)} 字符):")
    preview = body.replace("\n", " ")[:120]
    print(f"  {preview}...")

    # 走 py_lib 加载 github_api 插件（如果可用）
    try:
        registry = load_plugins(devroot=str(devroot), tags=["github"])
        if hasattr(registry, 'github_api'):
            api = registry.github_api
            result = api.new_issue_comment(owner=owner, repo=repo, number=args.issue, pat=pat, body=body)
            print(f"\n[OK] 评论追加成功!")
            print(f"  Comment ID: {result.get('id')}")
            print(f"  URL: {result.get('html_url')}")
            return
    except Exception:
        pass  # fallback 到 urllib

    # Fallback: 直接 urllib 请求（与 PS1 Invoke-RestMethod 对齐）
    import urllib.request
    uri = f"https://api.github.com/repos/{owner}/{repo}/issues/{args.issue}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(uri, data=payload, method="POST")
    req.add_header("Authorization", f"token {pat}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "deploy-git-isolated/1.0")
    req.add_header("Content-Type", "application/json; charset=utf-8")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        print(f"\n[OK] 评论追加成功!")
        print(f"  Comment ID: {result.get('id')}")
        print(f"  URL: {result.get('html_url')}")
    except Exception as e:
        print(f"[FAIL] 评论追加失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
