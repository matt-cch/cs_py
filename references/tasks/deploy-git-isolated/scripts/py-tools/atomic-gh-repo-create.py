#!/usr/bin/env python3
r"""
py-tools/atomic-gh-repo-create.py — GitHub 远程仓库创建原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-07-21

【意图】
在 polyrepo 初始化过程中，需要自动化创建 GitHub 远程空仓库，避免手敲
`gh repo create` 命令。统一通过 GH CLI 完成创建，同时自动注入 PAT、
脱敏 stdout 输出、生成 manifest 供审计追踪。
源于 env-migration 中 jywl-settlement 仓库从 0 到 1 的初始化踩坑：
手动创建仓库易遗漏 README、描述、权限配置，且 PAT 暴露风险高。

【职责】
  1. 通过 GH CLI 在 GitHub 上创建远程仓库（public/private）
  2. 支持 --add-readme、--description 等初始化选项
  3. 从 devroot/.env 读取 GITHUB_PAT，注入 GH_TOKEN 环境变量
  4. stdout 中所有 PAT 出现处自动替换为 ***
  5. 生成 manifest 落盘到 venv/tmp/ 供追踪审计

【依赖】
底层能力（py-plugins/）：
  - gh_preflight（验证 gh CLI 可用性 + 认证状态 + 提供 run_gh 方法）
  - env_config（读取 .env 中的 GITHUB_PAT/GITHUB_USERNAME）
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

【调用参数】
  --devroot       <str, 必填>                工具链根目录绝对路径
  --owner         <str, 必填>                GitHub 仓库所有者
  --repo-name     <str, 必填>                仓库名称
  --public        <flag, 可选, 默认>          公开仓库（默认）
  --private       <flag, 可选>               私有仓库
  --add-readme    <flag, 可选, 默认=False>    添加 README.md
  --description   <str, 可选, 默认="">        仓库描述
  --output        <str, 可选>                产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-gh-repo-create-manifest-{timestamp}.json）

【用法示例】
    # 创建公开仓库（含 README）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-create.py" `
        --devroot "${devroot}" `
        --owner "matt-cch" `
        --repo-name "jywl-settlement" `
        --public `
        --add-readme `
        --description "三方物流企业结算模块"

    # 创建私有仓库（无 README）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-create.py" `
        --devroot "${devroot}" `
        --owner "matt-cch" `
        --repo-name "private-repo" `
        --private

【返回】
    exit 0 = 成功（或仓库已存在，stdout 最后一行为 repo_url）
    exit 1 = 失败（gh CLI 错误或创建失败）

【审计产物】
    ${devroot}/venv/tmp/repo-create-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-gh-repo-create",
        "version": "1.0.0",
        "devroot": "...",
        "owner": "...",
        "repo_name": "...",
        "visibility": "public|private",
        "add_readme": true|false,
        "description": "...",
        "repo_url": "https://github.com/owner/repo",
        "default_branch": "main",
        "gh_username": "...",
        "gh_exe": "...",
        "exit_code": 0|1,
        "exit_at": "...",
        "errors": []
      }

【关联】
    - workflow: 被 polyrepo 初始化 workflow 在 Step 0 前独立调用
    - env-migration: references/env-migrations/env-migration-jywl-settlement-polyrepo-init-2026-07-21-173210.md
    - 下游消费: atomic-git-repo-clone.py（clone 本脚本创建的远程仓库）
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
        manifest_path = manifest_dir / f"repo-create-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="创建 GitHub 远程空仓库")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径")
    parser.add_argument("--owner", required=True, help="GitHub 仓库所有者")
    parser.add_argument("--repo-name", required=True, help="仓库名称")
    parser.add_argument("--public", action="store_true", default=True, help="公开仓库（默认）")
    parser.add_argument("--private", action="store_true", help="私有仓库")
    parser.add_argument("--add-readme", action="store_true", default=False, help="添加 README.md")
    parser.add_argument("--description", default="", help="仓库描述")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/repo-create-manifest-{timestamp}.json）")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        sys.exit(1)

    # 导入 gh_preflight
    try:
        import gh_preflight
    except ImportError as e:
        print(f"[ERROR] 无法导入 gh_preflight: {e}", file=sys.stderr)
        print(f"[HINT] 请确认 py-plugins 目录存在: {_PY_PLUGINS_DIR}", file=sys.stderr)
        sys.exit(1)

    # Manifest 数据收集
    manifest = {
        "atomic_tool": "atomic-gh-repo-create",
        "version": "1.0.0",
        "devroot": str(devroot),
        "owner": args.owner,
        "repo_name": args.repo_name,
        "visibility": "private" if args.private else "public",
        "add_readme": args.add_readme,
        "description": args.description,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "gh_exe": None,
        "gh_username": None,
        "repo_url": None,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    # Step 1: GH Preflight 验证
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

    # Step 2: 构造 gh repo create 命令
    print("\n" + "=" * 50)
    print("[Step 2] 创建远程仓库")
    print("=" * 50)

    visibility = "private" if args.private else "public"
    full_name = f"{args.owner}/{args.repo_name}"
    repo_url = f"https://github.com/{full_name}.git"
    manifest["repo_url"] = repo_url

    gh_args = ["repo", "create", full_name, f"--{visibility}"]
    if args.add_readme:
        gh_args.append("--add-readme")
    if args.description:
        gh_args.extend(["--description", args.description])

    print(f"[INFO] 创建仓库: {full_name} ({visibility})")
    if args.description:
        print(f"[INFO] 描述: {args.description}")
    if args.add_readme:
        print(f"[INFO] 添加 README: 是")

    _print_cmd([str(ctx.gh_exe)] + gh_args)
    sys.stdout.flush()

    result = ctx.run_gh(gh_args, check=False)

    if result.stdout:
        print(_mask_pat(result.stdout), end="")
    if result.stderr:
        print(_mask_pat(result.stderr), end="", file=sys.stderr)

    if result.returncode != 0:
        stderr_lower = (result.stderr or "").lower()
        if "already exists" in stderr_lower or "name already exists" in stderr_lower:
            print(f"[WARN] 仓库已存在: {full_name}")
            print(f"[OK] 使用已有仓库: {repo_url}")
        else:
            print(f"[FAIL] gh repo create 失败 (exit {result.returncode})")
            manifest["errors"].append(f"gh repo create 失败: exit {result.returncode}")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
    else:
        print(f"[OK] 仓库创建成功: {repo_url}")

    # Step 3: 验证仓库可访问
    print("\n" + "=" * 50)
    print("[Step 3] 验证仓库可访问")
    print("=" * 50)

    verify_args = ["repo", "view", full_name, "--json", "nameWithOwner,defaultBranchRef,url"]
    _print_cmd([str(ctx.gh_exe)] + verify_args)
    sys.stdout.flush()

    result = ctx.run_gh(verify_args, check=False)
    if result.returncode == 0 and result.stdout.strip():
        try:
            info = json.loads(result.stdout.strip())
            name = info.get("nameWithOwner", full_name)
            url = info.get("url", repo_url)
            default_branch = info.get("defaultBranchRef", {}).get("name", "main")
            print(f"[OK] 仓库验证通过")
            print(f"  nameWithOwner: {name}")
            print(f"  url: {url}")
            print(f"  defaultBranch: {default_branch}")
            manifest["default_branch"] = default_branch
        except json.JSONDecodeError:
            print(f"[OK] 仓库可访问（JSON 解析失败，但请求成功）")
    else:
        print(f"[WARN] 仓库验证请求失败，但创建命令已返回成功")

    # 成功收尾
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest)
    print(f"[Manifest] 已落盘: {mp}")

    print(f"\n[SUCCESS] 远程仓库就绪: {repo_url}")
    print(repo_url)
    sys.exit(0)


if __name__ == "__main__":
    main()
