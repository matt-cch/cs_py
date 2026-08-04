#!/usr/bin/env python3
r"""
py-tools/atomic-gh-issue-create.py — GitHub Issue 创建原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-08-03

【意图】
在 polyrepo 部署流程中，workflow-poly 的 Step 9（issue sync）需要向已有 issue
追加评论。若目标 issue 不存在（如首次部署的新仓库），Step 9 会 404 失败。
本工具填补这一缺口：在 Step 9 之前独立调用，自动创建追踪 issue，使后续
workflow 能成功同步变更记录。

【职责】
  1. 通过 GH CLI 在指定仓库创建 GitHub Issue
  2. 支持 --dry-run 预演（输出构造的命令，不实际创建）
  3. 支持 --show-progress 实时打印执行步骤
  4. 从 devroot/.env 读取 GITHUB_PAT，注入 GH_TOKEN 环境变量
  5. stdout 中所有 PAT 出现处自动替换为 ***
  6. 生成 manifest 落盘到 venv/tmp/ 供追踪审计

【依赖】
底层能力（py-plugins/）：
  - gh_preflight（验证 gh CLI 可用性 + 认证状态 + 提供 run_gh 方法）
外部工具：
  - ${devroot}/venv/gh/bin/gh.exe
环境变量：
  - GITHUB_PAT（devroot/.env）
  - GITHUB_USERNAME（devroot/.env）

【预检】
执行本脚本前必须满足的前置条件：
  - 文件存在性: devroot/.env 存在且含 GITHUB_PAT、GITHUB_USERNAME
  - 外部工具: ${devroot}/venv/gh/bin/gh.exe 可执行
  - 网络可达: GitHub API（api.github.com）可访问
  - 仓库存在: 目标仓库已在 GitHub 上创建

【调用参数】
  --devroot       <str, 必填>                工具链根目录绝对路径
  --repo          <str, 必填>                目标仓库（owner/repo 格式，如 matt-cch/jywl-settlement）
  --title         <str, 必填>                Issue 标题
  --body          <str, 可选, 默认="">       Issue 描述正文（支持 \n 换行）
  --label         <str, 可选>                Issue 标签（可多次传入）
  --output        <str, 可选>                产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-gh-issue-create-manifest-{timestamp}.json）
  --dry-run       <flag, 可选>               预演模式：构造并打印命令，不实际创建 issue
  --show-progress <flag, 可选>               实时打印执行步骤

【用法示例】
    # 创建 issue（标准模式）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-issue-create.py" `
        --devroot "${devroot}" `
        --repo "matt-cch/jywl-settlement" `
        --title "Feature Demo 开发追踪" `
        --body "追踪 feat/demo 分支的迭代进度"

    # 预演模式（不实际创建）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-issue-create.py" `
        --devroot "${devroot}" `
        --repo "matt-cch/jywl-settlement" `
        --title "Feature Demo 开发追踪" `
        --dry-run

    # 含标签 + 进度打印
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-issue-create.py" `
        --devroot "${devroot}" `
        --repo "matt-cch/jywl-settlement" `
        --title "Feature Demo 开发追踪" `
        --body "追踪 feat/demo 分支的迭代进度" `
        --label "feature" `
        --label "tracking" `
        --show-progress

【返回】
    exit 0 = 成功（stdout 最后一行为 issue_url）
    exit 1 = 失败（gh CLI 错误或创建失败）

【审计产物】
    ${devroot}/venv/tmp/atomic-gh-issue-create-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-gh-issue-create",
        "version": "1.0.0",
        "devroot": "...",
        "repo": "owner/repo",
        "title": "...",
        "body": "...",
        "labels": ["..."],
        "issue_number": 1,
        "issue_url": "https://github.com/owner/repo/issues/1",
        "gh_username": "...",
        "gh_exe": "...",
        "dry_run": true|false,
        "exit_code": 0|1,
        "exit_at": "...",
        "errors": []
      }

【关联】
    - workflow: 被 workflow-git-deploy-full-poly.py 在 Step 9 前独立调用
    - 上游消费: atomic-gh-repo-create.py（先创建仓库，再创建 issue）
    - 下游消费: step-09-github-sync-issue.py（向本脚本创建的 issue 追加评论）
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
        manifest_path = manifest_dir / f"atomic-gh-issue-create-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="创建 GitHub Issue")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径")
    parser.add_argument("--repo", required=True, help="目标仓库（owner/repo 格式）")
    parser.add_argument("--title", required=True, help="Issue 标题")
    parser.add_argument("--body", default="", help="Issue 描述正文")
    parser.add_argument("--label", action="append", default=[], help="Issue 标签（可多次传入）")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-gh-issue-create-manifest-{timestamp}.json）")
    parser.add_argument("--dry-run", action="store_true", help="预演模式：构造并打印命令，不实际创建")
    parser.add_argument("--show-progress", action="store_true", help="实时打印执行步骤")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        sys.exit(1)

    show = args.show_progress

    # 导入 gh_preflight
    try:
        import gh_preflight
    except ImportError as e:
        print(f"[ERROR] 无法导入 gh_preflight: {e}", file=sys.stderr)
        print(f"[HINT] 请确认 py-plugins 目录存在: {_PY_PLUGINS_DIR}", file=sys.stderr)
        sys.exit(1)

    # Manifest 数据收集
    manifest = {
        "atomic_tool": "atomic-gh-issue-create",
        "version": "1.0.0",
        "devroot": str(devroot),
        "repo": args.repo,
        "title": args.title,
        "body": args.body,
        "labels": args.label,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "gh_exe": None,
        "gh_username": None,
        "issue_number": None,
        "issue_url": None,
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

    # Step 2: 构造 gh issue create 命令
    _progress("Step 2: 构造 gh issue create 命令", show)
    print("\n" + "=" * 50)
    print("[Step 2] 创建 GitHub Issue")
    print("=" * 50)

    gh_args = ["issue", "create", "--repo", args.repo, "--title", args.title]
    if args.body:
        gh_args.extend(["--body", args.body])
    for lbl in args.label:
        gh_args.extend(["--label", lbl])

    print(f"[INFO] 目标仓库: {args.repo}")
    print(f"[INFO] 标题: {args.title}")
    if args.body:
        print(f"[INFO] 正文: {args.body[:80]}...")
    if args.label:
        print(f"[INFO] 标签: {', '.join(args.label)}")

    # Step 3: dry-run 或实际执行
    if args.dry_run:
        _progress("Step 3: DRY-RUN 模式，仅打印命令", show)
        print("\n[DRY-RUN] 以下命令将被执行（不实际调用 gh CLI）：")
        _print_cmd([str(ctx.gh_exe)] + gh_args)
        manifest["exit_code"] = 0
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"\n[DRY-RUN] 预演完成，未实际创建 issue")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(0)

    _progress("Step 3: 调用 gh CLI 创建 issue", show)
    _print_cmd([str(ctx.gh_exe)] + gh_args)
    sys.stdout.flush()

    result = ctx.run_gh(gh_args, check=False)

    if result.stdout:
        print(_mask_pat(result.stdout), end="")
    if result.stderr:
        print(_mask_pat(result.stderr), end="", file=sys.stderr)

    if result.returncode != 0:
        print(f"[FAIL] gh issue create 失败 (exit {result.returncode})")
        manifest["errors"].append(f"gh issue create 失败: exit {result.returncode}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 解析 stdout 获取 issue URL
    issue_url = result.stdout.strip()
    issue_number = None
    if issue_url:
        # 典型输出: https://github.com/matt-cch/jywl-settlement/issues/1
        m = re.search(r"/issues/(\d+)$", issue_url)
        if m:
            issue_number = int(m.group(1))

    print(f"\n[OK] Issue 创建成功")
    if issue_number:
        print(f"  Issue Number: #{issue_number}")
    if issue_url:
        print(f"  URL: {issue_url}")

    manifest["issue_number"] = issue_number
    manifest["issue_url"] = issue_url
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest, args.output)
    print(f"[Manifest] 已落盘: {mp}")

    print(f"\n[SUCCESS] Issue 就绪: {issue_url}")
    print(issue_url)
    sys.exit(0)


if __name__ == "__main__":
    main()
