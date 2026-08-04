#!/usr/bin/env python3
r"""
py-tools/atomic-gh-pr-create.py — GitHub Pull Request 创建原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-08-03

【意图】
在 polyrepo worktree 开发模式下，feature 分支的代码已 push 到 origin 后，
需要将其合并到 main（或指定 base 分支）。本工具在 worktree 目录中通过 GH CLI
创建 GitHub Pull Request，填补 workflow-poly 部署后缺少 PR 创建步骤的缺口。
与 legacy 的 gh-pr-create.py 不同：本脚本遵循 atomic 命名规范，支持 --target
指向 worktree 目录，满足 polyrepo 契约。

【职责】
  1. 通过 GH CLI 在指定 worktree 中创建 GitHub Pull Request
  2. 支持 --dry-run 预演（输出构造的命令，不实际创建）
  3. 支持 --show-progress 实时打印执行步骤
  4. 从 devroot/.env 读取 GITHUB_PAT，注入 GH_TOKEN 环境变量
  5. stdout 中所有 PAT 出现处自动替换为 ***
  6. 生成 manifest 落盘到 venv/tmp/ 供追踪审计
  7. 预检：当前分支 ≠ base、远程分支已存在

【依赖】
底层能力（py-plugins/）：
  - gh_preflight（验证 gh CLI 可用性 + 认证状态 + 提供 run_gh 方法）
外部工具：
  - ${devroot}/venv/gh/bin/gh.exe
  - ${devroot}/venv/git/cmd/git.exe
环境变量：
  - GITHUB_PAT（devroot/.env）
  - GITHUB_USERNAME（devroot/.env）

【预检】
执行本脚本前必须满足的前置条件：
  - 文件存在性: devroot/.env 存在且含 GITHUB_PAT、GITHUB_USERNAME
  - 外部工具: ${devroot}/venv/gh/bin/gh.exe 可执行
  - 外部工具: ${devroot}/venv/git/cmd/git.exe 可执行
  - 网络可达: GitHub API（api.github.com）可访问
  - 目标目录: --target 指向的 worktree 目录存在且是 git 仓库
  - 分支状态: 当前分支 ≠ base 分支
  - 远程分支: origin/<当前分支> 已存在（已 push）

【调用参数】
  --devroot       <str, 必填>                工具链根目录绝对路径
  --target        <str, 必填>                操作目标 worktree 路径（polyrepo 调用契约）
  --title         <str, 必填>                PR 标题
  --body          <str, 可选, 默认="">       PR 描述正文（支持 \n 换行）
  --base          <str, 可选, 默认=main>     目标分支（PR 合入目标）
  --draft         <flag, 可选>               创建为 Draft PR
  --output        <str, 可选>                产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-gh-pr-create-manifest-{timestamp}.json）
  --dry-run       <flag, 可选>               预演模式：构造并打印命令，不实际创建 PR
  --show-progress <flag, 可选>               实时打印执行步骤

【用法示例】
    # 创建 PR（标准模式）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-create.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo" `
        --title "feat: 三方物流结算 Feature Demo" `
        --body "实现三方物流结算模块的 Feature Demo，包含设计文档。" `
        --base main

    # 预演模式（不实际创建）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-create.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo" `
        --title "feat: 三方物流结算 Feature Demo" `
        --base main `
        --dry-run

    # Draft PR + 进度打印
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-create.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo" `
        --title "feat: 三方物流结算 Feature Demo" `
        --body "WIP: 设计文档初稿" `
        --base main `
        --draft `
        --show-progress

【返回】
    exit 0 = 成功（stdout 最后一行为 pr_url）
    exit 1 = 失败（gh CLI 错误、预检失败或远程分支不存在）

【审计产物】
    ${devroot}/venv/tmp/atomic-gh-pr-create-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-gh-pr-create",
        "version": "1.0.0",
        "devroot": "...",
        "target": "...",
        "title": "...",
        "body": "...",
        "base": "main",
        "draft": false,
        "pr_number": 2,
        "pr_url": "https://github.com/owner/repo/pull/2",
        "current_branch": "feat/demo",
        "gh_username": "...",
        "gh_exe": "...",
        "dry_run": true|false,
        "exit_code": 0|1,
        "exit_at": "...",
        "errors": []
      }

【关联】
    - workflow: 被 workflow-git-pr-poly.py 在 Step 1 调用
    - 上游消费: workflow-git-deploy-full-poly.py（push 后的 feature 分支）
    - 下游消费: atomic-gh-pr-merge.py（合并本脚本创建的 PR）
    - 对比脚本: gh-pr-create.py（legacy，无 --target，不支持 polyrepo）
"""
import argparse
import json
import os
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
        manifest_path = manifest_dir / f"atomic-gh-pr-create-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="创建 GitHub Pull Request（polyrepo worktree 场景）")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径")
    parser.add_argument("--target", required=True, help="操作目标 worktree 路径（polyrepo 调用契约）")
    parser.add_argument("--title", required=True, help="PR 标题")
    parser.add_argument("--body", default="", help="PR 描述正文")
    parser.add_argument("--base", default="main", help="目标分支（默认 main）")
    parser.add_argument("--draft", action="store_true", help="创建为 Draft PR")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-gh-pr-create-manifest-{timestamp}.json）")
    parser.add_argument("--dry-run", action="store_true", help="预演模式：构造并打印命令，不实际创建 PR")
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

    # Manifest 数据收集
    manifest = {
        "atomic_tool": "atomic-gh-pr-create",
        "version": "1.0.0",
        "devroot": str(devroot),
        "target": str(target),
        "title": args.title,
        "body": args.body,
        "base": args.base,
        "draft": args.draft,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "gh_exe": None,
        "gh_username": None,
        "current_branch": None,
        "pr_number": None,
        "pr_url": None,
        "dry_run": args.dry_run,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    # Step 1: GH Preflight 验证
    _progress("Step 1: GH CLI 前置验证", show)
    print("\n" + "=" * 50)
    print("[Step 1] GH CLI 前置验证")
    print("=" * 50)
    ctx = gh_preflight.verify(devroot)
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

    manifest["gh_exe"] = str(ctx.gh_exe)
    manifest["gh_username"] = ctx.username

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
    manifest["current_branch"] = current_branch
    print(f"[OK] 当前分支: {current_branch}")

    # 2b. 检查当前分支 ≠ base
    if current_branch == args.base:
        print(f"[FAIL] 当前分支 ({current_branch}) 与目标分支 ({args.base}) 相同，无法创建 PR")
        manifest["errors"].append(f"当前分支与目标分支相同: {current_branch}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 2c. 检查远程分支存在
    r = subprocess.run(
        [str(git_exe), "-C", str(target), "ls-remote", "--heads", "origin", current_branch],
        capture_output=True, text=True, encoding="utf-8"
    )
    if not r.stdout.strip():
        print(f"[FAIL] 远程不存在分支 origin/{current_branch}，请先 push")
        manifest["errors"].append(f"远程不存在分支 origin/{current_branch}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)
    print(f"[OK] 远程分支存在: origin/{current_branch}")

    # Step 3: 构造 gh pr create 命令
    _progress("Step 3: 构造 gh pr create 命令", show)
    print("\n" + "=" * 50)
    print("[Step 3] 创建 GitHub Pull Request")
    print("=" * 50)

    gh_args = ["pr", "create", "--title", args.title, "--base", args.base]
    if args.body:
        gh_args.extend(["--body", args.body])
    if args.draft:
        gh_args.append("--draft")

    print(f"[INFO] 目标仓库: {target}")
    print(f"[INFO] 当前分支: {current_branch} -> 目标分支: {args.base}")
    print(f"[INFO] 标题: {args.title}")
    if args.body:
        print(f"[INFO] 正文: {args.body[:80]}...")
    if args.draft:
        print(f"[INFO] Draft: 是")

    # Step 4: dry-run 或实际执行
    if args.dry_run:
        _progress("Step 4: DRY-RUN 模式，仅打印命令", show)
        print("\n[DRY-RUN] 以下命令将被执行（不实际调用 gh CLI）：")
        _print_cmd([str(ctx.gh_exe)] + gh_args)
        manifest["exit_code"] = 0
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"\n[DRY-RUN] 预演完成，未实际创建 PR")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(0)

    _progress("Step 4: 调用 gh CLI 创建 PR", show)
    _print_cmd([str(ctx.gh_exe)] + gh_args)
    sys.stdout.flush()

    result = ctx.run_gh(gh_args, check=False)

    if result.stdout:
        print(_mask_pat(result.stdout), end="")
    if result.stderr:
        print(_mask_pat(result.stderr), end="", file=sys.stderr)

    if result.returncode != 0:
        print(f"[FAIL] gh pr create 失败 (exit {result.returncode})")
        manifest["errors"].append(f"gh pr create 失败: exit {result.returncode}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 解析 stdout 获取 PR URL
    pr_url = ""
    pr_number = None
    output_lines = [ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()]
    if output_lines:
        pr_url = output_lines[-1]
        m = re.search(r"/pull/(\d+)$", pr_url)
        if m:
            pr_number = int(m.group(1))

    print(f"\n[OK] PR 创建成功")
    if pr_number:
        print(f"  PR Number: #{pr_number}")
    if pr_url:
        print(f"  URL: {pr_url}")

    manifest["pr_number"] = pr_number
    manifest["pr_url"] = pr_url
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest, args.output)
    print(f"[Manifest] 已落盘: {mp}")

    print(f"\n[SUCCESS] PR 就绪: {pr_url}")
    print(pr_url)
    sys.exit(0)


if __name__ == "__main__":
    main()
