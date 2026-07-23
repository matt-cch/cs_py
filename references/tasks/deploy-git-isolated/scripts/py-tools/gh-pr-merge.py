#!/usr/bin/env python3
r"""
gh-pr-merge.py — 合并 GitHub Pull Request（独立脚本，模块化）
标签：py-tools
版本：v1.1.0（默认 --squash，支持自动读取 PR title）

职责：合并当前分支（或指定 PR）的 Pull Request。
      默认 --squash 策略，复用 PR title 作为 squash commit message。
      如指定 --merge 策略且未传 --subject，自动读取 PR title 填充。
      支持 --admin 绕过分支保护。
      复用 gh_preflight 插件做前置验证，可独立执行，也可被上层 workflow 编排调用。

参数：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --devroot | str | 否 | D:\pjt\cursor\cs_py | devroot 绝对路径 |
| --strategy | str | 否 | squash | merge/squash/rebase（默认 squash 复用 PR title） |
| --delete-branch | flag | 否 | False | merge 后删除分支 |
| --admin | flag | 否 | False | 使用管理员权限绕过保护规则 |
| --auto | flag | 否 | False | 仅当检查通过时自动 merge |
| --subject | str | 否 | None | 自定义 merge commit 标题（--merge 策略时有效） |
| --pr-url | str | 否 | None | 指定 PR URL（不指定则自动查找当前分支的 PR）|

调用示例：
  # 默认 squash（PR title 自动成为 squash message）
  & "D:\pjt\cursor\cs_py\venv\py\python.exe" "...\gh-pr-merge.py" --admin --delete-branch

  # merge 策略 + 自定义 subject
  & "D:\pjt\cursor\cs_py\venv\py\python.exe" "...\gh-pr-merge.py" --strategy merge --subject "feat: xxx"

返回：
  成功时 exit code 0
  失败时 exit code 非 0
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


def _get_pr_title(ctx, pr_identifier: str) -> str:
    """
    通过 gh pr view 获取 PR title。
    """
    r = ctx.run_gh(["pr", "view", pr_identifier, "--json", "title"], check=False)
    if r.returncode == 0 and r.stdout.strip():
        try:
            data = json.loads(r.stdout.strip())
            return data.get("title", "")
        except json.JSONDecodeError:
            pass
    return ""


def main():
    parser = argparse.ArgumentParser(description="合并 GitHub Pull Request")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径")
    parser.add_argument("--strategy", choices=["merge", "squash", "rebase"], default="squash", help="Merge 策略（默认 squash 复用 PR title）")
    parser.add_argument("--delete-branch", action="store_true", help="Merge 后删除分支")
    parser.add_argument("--admin", action="store_true", help="使用管理员权限绕过保护规则")
    parser.add_argument("--auto", action="store_true", help="仅当检查通过时自动 merge")
    parser.add_argument("--subject", default=None, help="自定义 merge commit 标题（--merge 策略时有效）")
    parser.add_argument("--pr-url", default=None, help="指定 PR URL（不指定则自动查找当前分支）")
    args = parser.parse_args()

    devroot = Path(args.devroot)

    # Step 0: gh preflight
    from py_lib import load_plugins
    registry = load_plugins(devroot=str(devroot), tags=["gh"])
    ctx = registry.gh_preflight.check()

    # Step 1: 确定要 merge 的 PR
    pr_identifier = None
    if args.pr_url:
        pr_identifier = args.pr_url
        print(f"[OK] 指定 PR: {pr_identifier}")
    else:
        # 获取当前分支名，查找对应 PR
        git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
        r = subprocess.run(
            [str(git_exe), "-C", str(devroot), "branch", "--show-current"],
            capture_output=True, text=True, encoding="utf-8"
        )
        if r.returncode != 0:
            print(f"[FAIL] 无法获取当前分支: {r.stderr.strip()}")
            sys.exit(1)
        current_branch = r.stdout.strip()
        pr_identifier = current_branch
        print(f"[OK] 当前分支: {current_branch}，将查找对应 PR")

    # Step 2: 确定 merge message（--merge 策略且未传 --subject 时）
    subject = args.subject
    if args.strategy == "merge" and not subject:
        print("[INFO] --merge 策略且未指定 --subject，尝试读取 PR title...")
        pr_title = _get_pr_title(ctx, pr_identifier)
        if pr_title:
            subject = pr_title
            print(f"[OK] 使用 PR title 作为 merge subject: {subject}")
        else:
            print("[WARN] 无法读取 PR title，将使用 gh CLI 默认 merge message")

    # Step 3: gh pr merge
    print(f"\n{'='*50}")
    print("[Step] gh pr merge")
    print(f"{'='*50}")

    cmd = ["pr", "merge", pr_identifier, f"--{args.strategy}"]
    if args.delete_branch:
        cmd.append("--delete-branch")
    if args.admin:
        cmd.append("--admin")
        print("[Mode] --admin 已启用（绕过分支保护）")
    if args.auto:
        cmd.append("--auto")
    if subject:
        cmd.extend(["--subject", subject])

    r = ctx.run_gh(cmd)
    if r.returncode != 0:
        print(f"[FAIL] gh pr merge 失败:\n{r.stderr.strip()}")
        sys.exit(1)

    print(f"[OK] PR 合并成功")
    if r.stdout.strip():
        print(r.stdout.strip())

    # Step 4: 本地同步（可选提示）
    # 读取默认分支用于提示
    sec_path = devroot / "git-security.json"
    default_branch = "main"
    if sec_path.exists():
        try:
            data = json.loads(sec_path.read_text(encoding="utf-8"))
            db = data.get("default_branch", "").strip()
            if db:
                default_branch = db
        except Exception:
            pass
    print(f"\n[Tip] 如需本地同步最新代码，请执行:")
    print(f"      git -C {devroot} checkout {default_branch} && git -C {devroot} pull")


if __name__ == "__main__":
    main()
