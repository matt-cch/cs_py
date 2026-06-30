#!/usr/bin/env python3
r"""
gh-branch-protect.py — 设置 GitHub 分支保护规则（独立脚本）
标签：py-tools
版本：v1.0.0

职责：为指定分支开启 "Require pull request reviews before merging" 保护规则，
      模拟 team mode 开发环境。可独立执行，执行一次即可长期生效。

参数：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --devroot | str | 否 | D:\pjt\cursor\cs_py | devroot 绝对路径 |
| --branch | str | 否 | master | 要保护的分支名 |
| --required-reviewers | int | 否 | 1 | 要求的审批人数 |
| --dismiss-stale-reviews | flag | 否 | True | 新 commit 后是否驳回旧审批 |
| --include-admin | flag | 否 | False | 保护规则是否也限制 admin |

调用示例：
  # 开启 master 分支保护（默认配置）
  & "D:\pjt\cursor\cs_py\venv\py\python.exe" "...\gh-branch-protect.py"

  # 开启保护，且 admin 也受限（测试 --admin 绕过场景用）
  & "D:\pjt\cursor\cs_py\venv\py\python.exe" "...\gh-branch-protect.py" --include-admin

返回：
  成功时 exit code 0
  失败时 exit code 非 0

注意：
  设置保护后，直接 push 到该分支将被拒绝，必须通过 PR merge。
  如需关闭保护，请在 GitHub Web 端 Settings -> Branches 中手动删除。
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def main():
    parser = argparse.ArgumentParser(description="设置 GitHub 分支保护规则")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径")
    parser.add_argument("--branch", default="master", help="要保护的分支名（默认 master）")
    parser.add_argument("--required-reviewers", type=int, default=1, help="要求的审批人数（默认 1）")
    parser.add_argument("--dismiss-stale-reviews", action="store_true", default=True, help="新 commit 后驳回旧审批")
    parser.add_argument("--include-admin", action="store_true", help="保护规则也限制 admin")
    args = parser.parse_args()

    devroot = Path(args.devroot)

    # Step 0: gh preflight
    from py_lib import load_plugins
    registry = load_plugins(devroot=str(devroot), tags=["gh"])
    ctx = registry.gh_preflight.check()

    # Step 1: 检测当前保护状态
    print(f"\n{'='*50}")
    print(f"[Step] 检测 {args.branch} 分支保护状态")
    print(f"{'='*50}")

    r = ctx.run_gh(["api", f"repos/{ctx.repo}/branches/{args.branch}/protection"], check=False)
    if r.returncode == 0 and r.stdout.strip():
        try:
            current = json.loads(r.stdout.strip())
            has_reviews = current.get("required_pull_request_reviews")
            if has_reviews:
                print(f"[INFO] {args.branch} 已开启分支保护")
                print(f"[INFO] 当前审批要求: {has_reviews.get('required_approving_review_count', 0)} 人")
                print(f"[INFO] 如需重新设置，请先关闭现有保护后再执行")
                sys.exit(0)
        except json.JSONDecodeError:
            pass
    elif r.returncode == 404:
        print(f"[OK] {args.branch} 当前无保护规则，准备设置...")
    else:
        print(f"[WARN] 无法读取保护状态: {r.stderr.strip() if r.stderr else 'unknown'}")
        print(f"[WARN] 继续尝试设置...")

    # Step 2: 设置分支保护（通过 GitHub REST API）
    print(f"\n{'='*50}")
    print(f"[Step] 设置 {args.branch} 分支保护")
    print(f"{'='*50}")

    payload = {
        "required_status_checks": None,
        "enforce_admins": args.include_admin,
        "required_pull_request_reviews": {
            "required_approving_review_count": args.required_reviewers,
            "dismiss_stale_reviews": args.dismiss_stale_reviews,
            "require_code_owner_reviews": False,
        },
        "restrictions": None,
    }

    # 通过 gh api 发送 PUT 请求（需要 stdin 传入 JSON payload）
    env = os.environ.copy()
    env["GH_TOKEN"] = ctx.token
    env["GH_CONFIG_DIR"] = str(ctx.gh_config_dir)
    r = subprocess.run(
        [str(ctx.gh_exe), "api", "--method", "PUT",
         f"repos/{ctx.repo}/branches/{args.branch}/protection",
         "--input", "-"],
        env=env,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if r.returncode != 0:
        print(f"[FAIL] 设置保护规则失败:\n{r.stderr.strip()}")
        sys.exit(1)

    print(f"[OK] {args.branch} 分支保护已设置")
    print(f"[OK] 要求审批: {args.required_reviewers} 人")
    print(f"[OK] 驳回旧审批: {args.dismiss_stale_reviews}")
    print(f"[OK] 限制 admin: {args.include_admin}")
    print(f"\n[IMPORTANT] 从现在起，直接 push 到 {args.branch} 将被拒绝，必须通过 PR merge")


if __name__ == "__main__":
    main()
