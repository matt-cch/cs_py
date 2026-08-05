#!/usr/bin/env python3
r"""
py-tools/atomic-gh-pr-merge.py — GitHub Pull Request 合并原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-08-04

【意图】
在 polyrepo worktree 开发模式下，feature 分支的 PR 已创建并通过 review 后，
需要将其 squash merge 到 default_branch（如 main）。本工具在 worktree 目录中通过
GH CLI 合并 GitHub Pull Request。

【真实意图：消除 gh CLI 的 CWD 依赖陷阱 + 真源分支读取】
gh CLI（如 `gh pr merge`）默认从当前工作目录（CWD）推断要操作的仓库。
在 polyrepo 工作区中，CWD 是 devroot（cs_py），而 --target 指向另一个仓库
（jywl-settlement）。如果不显式指定仓库，gh CLI 会在错误仓库上执行。

此外，default_branch 不能硬编码为 "main"——cs_py 的 default_branch 是 "master"，
jywl-settlement 的 default_branch 是 "main"。必须从 target 的 git-security.json
读取真源 default_branch。

解法：
  1. 调用 gh_preflight.verify(devroot, target) 时传入 target
  2. preflight 从 target 的 git remote 解析 owner/repo，并向 GitHub 验证真源
  3. 从 target/git-security.json 读取 default_branch（消除硬编码）
  4. 所有 gh CLI 命令（pr merge / pr view / pr list）显式传 `--repo ctx.owner_repo`
  5. 彻底消除 CWD 依赖，确保操作对象与 --target 语义一致

【职责】
  1. 通过 GH CLI 合并指定 worktree 分支对应的 GitHub Pull Request
  2. 支持 --strategy 选择（squash/merge/rebase，默认 squash）
  3. 支持 --admin 绕过分支保护
  4. 支持 --delete-branch 合并后删除远程 feature 分支
  5. 从 target/git-security.json 读取真源 default_branch（用于日志/审计，不用于本地操作）
  6. stdout 中所有 PAT 出现处自动替换为 ***
  7. 生成 manifest 落盘到 venv/tmp/ 供追踪审计
  8. Post-Audit：merge 后通过 gh pr view 验证 PR 状态变为 merged（纯远程验证）

【重要边界】
  - 本脚本仅执行远程 GitHub 操作（gh pr merge），绝不修改本地任何分支状态。
  - 不执行 git checkout、git pull、git fetch 等本地操作。
  - 不猜测用户后续意图（如"merge 完应该切到 main"）。
  - 本地工作区同步由用户自行决定，或通过独立的 workflow 脚本编排。

【依赖】
底层能力（py-plugins/）：
  - gh_preflight（验证 gh CLI 可用性 + 认证状态 + 提供 run_gh 方法）
外部工具：
  - ${devroot}/venv/gh/bin/gh.exe
  - ${devroot}/venv/git/cmd/git.exe
环境变量：
  - GITHUB_PAT（devroot/.env）

【预检】
执行本脚本前必须满足的前置条件：
  - 文件存在性: devroot/.env 存在且含 GITHUB_PAT
  - 外部工具: ${devroot}/venv/gh/bin/gh.exe 可执行
  - 外部工具: ${devroot}/venv/git/cmd/git.exe 可执行
  - 网络可达: GitHub API（api.github.com）可访问
  - 目标目录: --target 指向的 worktree 目录存在且是 git 仓库
  - PR 存在: 当前分支有对应的 open PR
  - 合并权限: gh auth 用户有 merge 权限（或 --admin 绕过分支保护）

【调用参数】
  --devroot       <str, 必填>                工具链根目录绝对路径
  --target        <str, 必填>                操作目标 worktree 路径（polyrepo 调用契约）
  --strategy      <str, 可选, 默认=squash>    merge 策略（squash/merge/rebase）
  --admin         <flag, 可选>               使用管理员权限绕过分支保护
  --delete-branch <flag, 可选>               merge 后删除远程 feature 分支
  --pr-number     <int, 可选>                指定 PR 编号（不指定则自动查找当前分支的 open PR）
  --output        <str, 可选>                产物输出路径
  --dry-run       <flag, 可选>               预演模式：构造并打印命令，不实际 merge
  --show-progress <flag, 可选>               实时打印执行步骤

【用法示例】
    # 标准合并（squash，自动查找当前分支的 PR）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-merge.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo" `
        --strategy squash

    # 指定 PR 编号 + admin 绕过保护 + 删除分支
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-merge.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo" `
        --pr-number 2 `
        --admin `
        --delete-branch

    # 预演模式
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-merge.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo" `
        --dry-run

【返回】
    exit 0 = 成功（PR 已 merge）
    exit 1 = 失败（gh CLI 错误、预检失败、PR 不存在或无权限）

【审计产物】
    ${devroot}/venv/tmp/atomic-gh-pr-merge-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-gh-pr-merge",
        "version": "1.0.0",
        "devroot": "...",
        "target": "...",
        "pr_number": 2,
        "strategy": "squash",
        "admin": false,
        "delete_branch": false,
        "default_branch": "main",
        "owner_repo": "matt-cch/jywl-settlement",
        "exit_code": 0,
        "exit_at": "...",
        "post_audit": {
          "verified": true,
          "method": "gh_pr_view",
          "state": "merged",
          "errors": []
        },
        "errors": []
      }

【关联】
    - workflow: 被 workflow-git-pr-poly.py 在 Step 2 调用
    - 上游消费: atomic-gh-pr-create.py（创建的 PR）
    - 对比脚本: gh-pr-merge.py（legacy，无 --target，不支持 polyrepo）
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


# =============================================================================
# 路径解析：优先从当前文件位置推导 py-plugins 目录
# =============================================================================
_SCRIPT_DIR = Path(__file__).parent.resolve()
if _SCRIPT_DIR.name == "py-tools":
    _PY_PLUGINS_DIR = _SCRIPT_DIR.parent / "py-plugins"
elif _SCRIPT_DIR.name == "tmp":
    _PY_PLUGINS_DIR = Path(__file__).parent.parent.parent / "references" / "tasks" / "deploy-git-isolated" / "scripts" / "py-plugins"
else:
    _PY_PLUGINS_DIR = _SCRIPT_DIR.parent / "py-plugins"

if str(_PY_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PY_PLUGINS_DIR))


# =============================================================================
# 脱敏工具（内联，避免新增 plugin）
# =============================================================================
def _mask_pat(text: str) -> str:
    """将命令行/URL 中的 GitHub PAT 替换为 ***。"""
    if not text:
        return text
    text = re.sub(r"(https?://[^:]+:)([^@]+)(@github\.com)", r"\1***\3", text)
    text = re.sub(r"(token\s+)(ghp_[a-zA-Z0-9_]+)", r"\1***", text)
    text = re.sub(r"(GH_TOKEN=)([^\s]+)", r"\1***", text)
    return text


def _print_cmd(cmd: list) -> None:
    """打印命令，自动脱敏。"""
    print(f"[EXEC] {_mask_pat(' '.join(cmd))}")


def _progress(msg: str, show: bool) -> None:
    """条件打印进度信息。"""
    if show:
        print(f"[PROGRESS] {msg}")


# =============================================================================
# Manifest 生成（内联，不依赖 polyrepo_context）
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str = None) -> Path:
    """保存 manifest 到 venv/tmp/，供追踪审计。"""
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"atomic-gh-pr-merge-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 真源读取：从 target 的 git-security.json 读取 default_branch
# =============================================================================
def _get_default_branch(target: Path) -> str:
    """从 target/git-security.json 读取 default_branch，失败时回退到 main。"""
    sec_path = target / "git-security.json"
    if sec_path.exists():
        try:
            data = json.loads(sec_path.read_text(encoding="utf-8"))
            db = data.get("default_branch", "").strip()
            if db:
                return db
        except Exception:
            pass
    return "main"


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="合并 GitHub Pull Request（polyrepo worktree 场景）")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径")
    parser.add_argument("--target", required=True, help="操作目标 worktree 路径（polyrepo 调用契约）")
    parser.add_argument("--strategy", choices=["merge", "squash", "rebase"], default="squash", help="Merge 策略（默认 squash）")
    parser.add_argument("--admin", action="store_true", help="使用管理员权限绕过分支保护")
    parser.add_argument("--delete-branch", action="store_true", help="Merge 后删除远程 feature 分支")
    parser.add_argument("--pr-number", type=int, default=None, help="指定 PR 编号（不指定则自动查找当前分支的 open PR）")
    parser.add_argument("--output", default=None, help="产物输出路径")
    parser.add_argument("--dry-run", action="store_true", help="预演模式：构造并打印命令，不实际 merge")
    parser.add_argument("--show-progress", action="store_true", help="实时打印执行步骤")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    target = Path(args.target)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        sys.exit(1)
    if not target.exists():
        print(f"[ERROR] target 不存在: {target}", file=sys.stderr)
        sys.exit(1)

    show = args.show_progress
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    # 导入 gh_preflight
    try:
        import gh_preflight
    except ImportError as e:
        print(f"[ERROR] 无法导入 gh_preflight: {e}", file=sys.stderr)
        print(f"[HINT] 请确认 py-plugins 目录存在: {_PY_PLUGINS_DIR}", file=sys.stderr)
        sys.exit(1)

    # 从 git-security.json 读取真源 default_branch
    default_branch = _get_default_branch(target)

    # Manifest 数据收集
    manifest = {
        "atomic_tool": "atomic-gh-pr-merge",
        "version": "1.0.0",
        "devroot": str(devroot),
        "target": str(target),
        "strategy": args.strategy,
        "admin": args.admin,
        "delete_branch": args.delete_branch,
        "default_branch": default_branch,
        "pr_number": args.pr_number,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "gh_exe": None,
        "gh_username": None,
        "owner_repo": None,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    # Step 1: GH Preflight 验证
    _progress("Step 1: GH CLI 前置验证", show)
    print("\n" + "=" * 50)
    print("[Step 1] GH CLI 前置验证")
    print("=" * 50)
    ctx = gh_preflight.verify(devroot, target)
    if not ctx.ok:
        for e in ctx.errors:
            print(f"[FAIL] {e}")
        manifest["errors"].extend(ctx.errors)
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    print(f"[OK] gh.exe: {ctx.gh_exe}")
    print(f"[OK] 认证用户: {ctx.username}")
    print(f"[OK] GITHUB_PAT: 已读取（长度 {len(ctx.token)}）")
    if ctx.owner_repo:
        print(f"[OK] 目标仓库（真源）: {ctx.owner_repo}")
    print(f"[OK] default_branch（来自 git-security.json）: {default_branch}")

    manifest["gh_exe"] = str(ctx.gh_exe)
    manifest["gh_username"] = ctx.username
    manifest["owner_repo"] = ctx.owner_repo

    # Step 2: Git 预检（在 target 目录下执行）
    _progress("Step 2: Git 预检", show)
    print("\n" + "=" * 50)
    print("[Step 2] Git 预检")
    print("=" * 50)

    if not git_exe.exists():
        print(f"[FAIL] git.exe 不存在: {git_exe}")
        manifest["errors"].append(f"git.exe 不存在: {git_exe}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 2a. 获取当前分支
    r = subprocess.run(
        [str(git_exe), "-C", str(target), "branch", "--show-current"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if r.returncode != 0:
        print(f"[FAIL] 无法获取当前分支: {r.stderr.strip()}")
        manifest["errors"].append(f"无法获取当前分支: {r.stderr.strip()}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    current_branch = r.stdout.strip()
    print(f"[OK] 当前分支: {current_branch}")

    # Step 3: 查找要 merge 的 PR
    _progress("Step 3: 查找 PR", show)
    print("\n" + "=" * 50)
    print("[Step 3] 查找要 merge 的 PR")
    print("=" * 50)

    pr_number = args.pr_number
    pr_url = None

    if pr_number:
        print(f"[INFO] 使用指定 PR: #{pr_number}")
    else:
        # 自动查找当前分支的 open PR
        list_args = ["pr", "list", "--repo", ctx.owner_repo, "--head", current_branch, "--state", "open", "--json", "number,url"]
        list_result = ctx.run_gh(list_args, check=False)
        if list_result.returncode == 0 and list_result.stdout.strip():
            try:
                prs = json.loads(list_result.stdout)
                if prs:
                    pr_number = prs[0].get("number")
                    pr_url = prs[0].get("url")
                    print(f"[OK] 找到 PR #{pr_number}: {pr_url}")
                else:
                    print(f"[FAIL] 当前分支 ({current_branch}) 没有 open PR")
                    manifest["errors"].append(f"当前分支无 open PR: {current_branch}")
                    manifest["exit_code"] = 1
                    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
                    mp = _save_manifest(devroot, manifest, args.output)
                    print(f"[Manifest] 已落盘: {mp}")
                    sys.exit(1)
            except Exception as e:
                print(f"[FAIL] 解析 PR list 失败: {e}")
                manifest["errors"].append(f"解析 PR list 失败: {e}")
                manifest["exit_code"] = 1
                manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
                mp = _save_manifest(devroot, manifest, args.output)
                print(f"[Manifest] 已落盘: {mp}")
                sys.exit(1)
        else:
            print(f"[FAIL] 无法查找 PR: {list_result.stderr.strip()}")
            manifest["errors"].append(f"无法查找 PR: {list_result.stderr.strip()}")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)

    manifest["pr_number"] = pr_number

    # Step 4: gh pr merge
    _progress("Step 4: 调用 gh CLI merge PR", show)
    print("\n" + "=" * 50)
    print("[Step 4] Merge Pull Request")
    print("=" * 50)

    merge_args = ["pr", "merge", str(pr_number), "--repo", ctx.owner_repo, f"--{args.strategy}"]
    if args.admin:
        merge_args.append("--admin")
    if args.delete_branch:
        merge_args.append("--delete-branch")

    print(f"[INFO] PR: #{pr_number}")
    print(f"[INFO] 策略: {args.strategy}")
    if args.admin:
        print(f"[INFO] Admin: 已启用（绕过分支保护）")
    if args.delete_branch:
        print(f"[INFO] Delete branch: merge 后删除远程分支")

    if args.dry_run:
        _progress("DRY-RUN 模式，仅打印命令", show)
        print("\n[DRY-RUN] 以下命令将被执行（不实际调用 gh CLI）：")
        _print_cmd([str(ctx.gh_exe)] + merge_args)
        manifest["exit_code"] = 0
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"\n[DRY-RUN] 预演完成，未实际 merge")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(0)

    _print_cmd([str(ctx.gh_exe)] + merge_args)
    sys.stdout.flush()

    result = ctx.run_gh(merge_args, check=False)

    if result.stdout:
        print(_mask_pat(result.stdout), end="")
    if result.stderr:
        print(_mask_pat(result.stderr), end="", file=sys.stderr)

    if result.returncode != 0:
        print(f"[FAIL] gh pr merge 失败 (exit {result.returncode})")
        manifest["errors"].append(f"gh pr merge 失败: exit {result.returncode}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    print(f"\n[OK] PR #{pr_number} merge 成功")

    # Step 5: Post-Audit — 通过 gh pr view 验证 PR 状态变为 merged（纯远程验证）
    print("\n" + "=" * 50)
    print("[Step 5] Post-Audit: 验证 PR 状态")
    print("=" * 50)

    audit_result = {"verified": False, "method": "gh_pr_view", "state": None, "errors": []}

    view_args = ["pr", "view", str(pr_number), "--repo", ctx.owner_repo, "--json", "state"]
    view_result = ctx.run_gh(view_args, check=False)
    if view_result.returncode == 0 and view_result.stdout.strip():
        try:
            pr_info = json.loads(view_result.stdout)
            state = pr_info.get("state", "").lower()
            audit_result["state"] = state
            if state == "merged":
                audit_result["verified"] = True
                print(f"[OK] Post-audit 通过: PR #{pr_number} 状态 = {state}")
            else:
                audit_result["errors"].append(f"PR 状态异常: {state}")
                print(f"[WARN] Post-audit 失败: PR #{pr_number} 状态 = {state}（期望 merged）")
        except Exception as e:
            audit_result["errors"].append(f"解析 PR view 失败: {e}")
            print(f"[WARN] Post-audit 失败: {e}")
    else:
        audit_result["errors"].append(f"gh pr view 失败: {view_result.stderr.strip()}")
        print(f"[WARN] Post-audit 失败: 无法获取 PR 状态")

    manifest["post_audit"] = audit_result
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest, args.output)
    print(f"[Manifest] 已落盘: {mp}")

    print(f"\n[SUCCESS] PR #{pr_number} 已 merge")
    sys.exit(0)


if __name__ == "__main__":
    main()
