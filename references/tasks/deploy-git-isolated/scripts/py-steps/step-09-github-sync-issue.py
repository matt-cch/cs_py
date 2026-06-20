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
    """获取当前 commit 信息"""
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

    return {"hash": commit_hash, "msg": commit_msg, "branch": branch}


def main():
    parser = argparse.ArgumentParser(description="Step 9: Issue Sync")
    parser.add_argument("--devroot", default=None, help="Devroot 路径")
    parser.add_argument("--issue", type=int, default=1, help="Issue 编号 (默认 1)")
    parser.add_argument("--body", default=None, help="自定义评论内容（默认自动生成）")
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

    # 构造评论内容
    if args.body:
        body = args.body
    else:
        info = _get_commit_info(git_exe, devroot)
        body = f"commit {info['hash']}: {info['msg']} [{info['branch']}]"

    print(f"[OK] 目标 Issue: #{args.issue}")
    print(f"[OK] 仓库: {owner}/{repo}")
    print(f"[OK] 评论内容: {body}")

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
