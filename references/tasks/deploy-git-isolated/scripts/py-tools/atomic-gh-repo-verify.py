#!/usr/bin/env python3
r"""
py-tools/atomic-gh-repo-verify.py — GitHub 仓库真源验证原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-08-05

【意图】
在 polyrepo worktree 开发模式下，验证本地 worktree 与远程 GitHub 仓库之间的
物理不可伪造绑定。执行完整的 L1-L5 真源推理链，输出经过验证的 owner_repo
和完整的审计 manifest，供下游 atomic 脚本作为唯一真源引用。

本脚本是"调用者构造和传参"原则的标准实现：
  - 调用者负责构造所有入参（--devroot、--target 等）
  - 本脚本负责执行验证、输出 manifest，不猜测调用者意图
  - 下游脚本消费 manifest 中的 owner_repo 执行实际操作

【真源推理链】
  L1 本地实测推断层：从 .git/ 数据库读取物理状态（分支、HEAD SHA、remote URL）
  L2 用户声明审计层：读取 target/git-security.json（用户意图真源起点）
  L3 交叉验证层：L1 实测 vs L2 声明 vs .git/config 佐证对碰
  L4 远程物理绑定层：本地 HEAD commit SHA 必须存在于远程仓库（核心防线）
  L5 远程对象绑定层：分支 ↔ PR / Issue 的物理对应验证

【URL 规范化规范】
  所有 repo URL 比较统一使用 canonicalize_url：
    - 去除尾部空白、尾部斜杠、尾部 .git（不区分大小写）
    - 统一转为小写
  manifest 中同时记录原始 URL（raw）和规范化 URL（canonical）。

【默认分支规范】
  - git-security.json 中的 default_branch 优先
  - 缺失时回退到 "main"
  - 历史遗留仓库（如 cs_py 的 master）通过 git-security.json 显式声明

【调用者构造参数规则模板】

调用者（workflow 或人工）必须显式构造以下参数：

  必填参数：
    --devroot  <str>  工具链根目录绝对路径
                      例: "D:\pjt\cursor\cs_py"
    --target   <str>  操作目标 worktree 路径（polyrepo 调用契约）
                      例: "D:\pjt\cursor\cs_py\apps\repos\matt-cch\jywl-settlement.wt\feat-demo"

  可选参数：
    --verify-pr-binding      <flag>  是否验证 PR 绑定（默认启用）
    --no-verify-pr-binding   <flag>  跳过 PR 绑定验证
    --verify-linked-issues   <flag>  是否验证 linked_issues（默认启用）
    --no-verify-linked-issues <flag> 跳过 linked_issues 验证
    --output                 <str>   manifest 输出路径（默认 venv/tmp/）
    --dry-run                <flag>  预演模式：构造并打印命令，不实际调用 gh API
    --show-progress          <flag>  实时打印执行步骤（推荐人工调用时启用）

【调用者义务】
  1. 必须显式传入 --devroot 和 --target，禁止依赖 CWD 隐式推断
  2. 必须检查 exit code，exit 1 时表示验证失败，不得继续执行下游操作
  3. 若指定 --output，必须检查输出文件是否存在且可读
  4. 未指定 --output 时，manifest 落盘到 venv/tmp/，调用者应读取脚本 stdout
     最后一行的 "[Manifest] 已落盘: <path>" 获取路径
  5. 消费 manifest 时，必须以 manifest.source_truth.owner_repo 作为 --repo 参数

【下游消费示例】
    # 1. 调用验证
    & "${devroot}\venv\py\python.exe" "${devroot}\references\...\atomic-gh-repo-verify.py" `
        --devroot "${devroot}" `
        --target "${target}" `
        --show-progress

    # 2. 从 stdout 提取 manifest 路径
    # 3. 读取 manifest，获取 owner_repo
    # 4. 使用 owner_repo 执行下游操作
    gh pr create --repo {owner_repo} --title "..."

【返回】
    exit 0 = 验证通过（ok=True，owner_repo 可用）
    exit 1 = 验证失败（有 errors，owner_repo 不可用）
    exit 2 = 验证降级（ok=True，但有 warnings/conflicts，需调用者判断）

【审计产物】
    ${devroot}/venv/tmp/atomic-gh-repo-verify-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-gh-repo-verify",
        "version": "1.0.0",
        "devroot": "...",
        "target": "...",
        "owner_repo": "matt-cch/jywl-settlement",
        "owner_repo_source": "git-security.json (confirmed by local inference)",
        "owner_repo_source_path": ".../feat-demo/git-security.json",
        "local_head_sha": "abc123...",
        "remote_head_sha": "abc123...",
        "current_branch": "feat-demo",
        "physical_binding_verified": true,
        "state_aligned": true,
        "pr_number": 2,
        "pr_binding_verified": true,
        "layer1_local_inference": { ... },
        "layer2_user_declaration": { ... },
        "layer3_cross_validation": { ... },
        "layer4_physical_binding": { ... },
        "layer5_remote_object_binding": { ... },
        "source_truth": { "ok": true, ... },
        "exit_code": 0,
        "started_at": "...",
        "exit_at": "..."
      }

【关联】
    - 上游依赖: gh_preflight.py（工具链验证）
    - 核心插件: source_truth.py（L1-L5 推理链）
    - 下游消费: atomic-gh-pr-create.py、atomic-gh-pr-merge.py 等
    - URL 工具: git_url_utils.py（canonicalize_url）
"""
import argparse
import json
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
# Manifest 生成（内联，不依赖 polyrepo_context）
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str = None) -> Path:
    """保存 manifest 到 venv/tmp/ 或指定路径，供追踪审计。"""
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"atomic-gh-repo-verify-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def _progress(msg: str, show: bool) -> None:
    """条件打印进度信息。"""
    if show:
        print(f"[PROGRESS] {msg}")


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="GitHub 仓库真源验证（polyrepo worktree 场景）"
    )
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径")
    parser.add_argument(
        "--target", required=True,
        help="操作目标 worktree 路径（polyrepo 调用契约）"
    )
    parser.add_argument(
        "--verify-pr-binding", action="store_true", default=True,
        help="验证 PR 绑定（默认启用）"
    )
    parser.add_argument(
        "--no-verify-pr-binding", action="store_true",
        help="跳过 PR 绑定验证"
    )
    parser.add_argument(
        "--verify-linked-issues", action="store_true", default=True,
        help="验证 linked_issues（默认启用）"
    )
    parser.add_argument(
        "--no-verify-linked-issues", action="store_true",
        help="跳过 linked_issues 验证"
    )
    parser.add_argument(
        "--output", default=None,
        help="产物输出路径（workflow 调用时必须显式传入；"
             "未传时回退到 devroot/venv/tmp/atomic-gh-repo-verify-manifest-{timestamp}.json）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="预演模式：构造并打印命令，不实际调用 gh API"
    )
    parser.add_argument(
        "--show-progress", action="store_true",
        help="实时打印执行步骤"
    )
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
    verify_pr = args.verify_pr_binding and not args.no_verify_pr_binding
    verify_issues = args.verify_linked_issues and not args.no_verify_linked_issues

    started_at = datetime.now(timezone.utc).isoformat()

    # Manifest 数据收集
    manifest = {
        "atomic_tool": "atomic-gh-repo-verify",
        "version": "1.0.0",
        "devroot": str(devroot),
        "target": str(target),
        "verify_pr_binding": verify_pr,
        "verify_linked_issues": verify_issues,
        "dry_run": args.dry_run,
        "started_at": started_at,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    # -------------------------------------------------------------------------
    # Step 1: GH Preflight（工具链验证）
    # -------------------------------------------------------------------------
    _progress("Step 1: GH CLI 工具链验证", show)
    print("\n" + "=" * 50)
    print("[Step 1] GH CLI 工具链验证")
    print("=" * 50)

    try:
        import gh_preflight
    except ImportError as e:
        print(f"[ERROR] 无法导入 gh_preflight: {e}", file=sys.stderr)
        print(f"[HINT] 请确认 py-plugins 目录存在: {_PY_PLUGINS_DIR}", file=sys.stderr)
        sys.exit(1)

    gh_ctx = gh_preflight.verify(devroot, target=None)
    if not gh_ctx.ok:
        for e in gh_ctx.errors:
            print(f"[FAIL] {e}")
        manifest["errors"].extend(gh_ctx.errors)
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    print(f"[OK] gh.exe: {gh_ctx.gh_exe}")
    print(f"[OK] 认证用户: {gh_ctx.username}")
    print(f"[OK] GITHUB_PAT: 已读取（长度 {len(gh_ctx.token)}）")

    manifest["gh_exe"] = str(gh_ctx.gh_exe)
    manifest["gh_username"] = gh_ctx.username

    # DRY-RUN：仅打印，不执行 L1-L5
    if args.dry_run:
        _progress("DRY-RUN 模式，跳过 L1-L5 真源验证", show)
        print("\n[DRY-RUN] 以下验证将被执行（不实际调用 gh API）：")
        print(f"  - L1: 本地实测推断 @ {target}")
        print(f"  - L2: 读取 git-security.json")
        print(f"  - L3: 交叉验证")
        print(f"  - L4: 远程物理绑定验证（gh api repos/{'{owner_repo}'}/commits/{'{sha}'}）")
        if verify_pr:
            print("  - L5: PR 绑定验证（gh pr list --repo {owner_repo} --head {branch}）")
        if verify_issues:
            print(f"  - L5: linked_issues 验证")
        manifest["exit_code"] = 0
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"\n[DRY-RUN] 预演完成")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(0)

    # -------------------------------------------------------------------------
    # Step 2: L1-L5 真源推理链
    # -------------------------------------------------------------------------
    _progress("Step 2: L1-L5 真源推理链", show)
    print("\n" + "=" * 50)
    print("[Step 2] L1-L5 真源推理链")
    print("=" * 50)

    try:
        from source_truth import verify as source_truth_verify
    except ImportError as e:
        print(f"[ERROR] 无法导入 source_truth: {e}", file=sys.stderr)
        manifest["errors"].append(f"无法导入 source_truth: {e}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    stx = source_truth_verify(
        devroot=devroot,
        target=target,
        gh_ctx=gh_ctx,
        verify_pr_binding=verify_pr,
        verify_linked_issues=verify_issues,
    )

    # 打印各层结果
    print(f"\n[L1] 本地实测推断")
    print(f"  git_dir: {stx.local_head_sha_source}")
    print(f"  current_branch: {stx.current_branch}")
    print(f"  local_head_sha: {stx.local_head_sha}")
    print(f"  inferred_owner_repo: {stx.inferred_owner_repo}")
    print(f"  remote_url_from_config: {stx.remote_url_from_config_raw}")

    print(f"\n[L2] 用户声明审计")
    print(f"  git-security.json: {stx.declared_source_path}")
    print(f"  declared_owner_repo: {stx.declared_owner_repo}")
    print(f"  declared_remote_url: {stx.declared_remote_url_raw}")
    print(f"  declared_default_branch: {stx.declared_default_branch}")

    print(f"\n[L3] 交叉验证")
    print(f"  owner_repo_source: {stx.owner_repo_source}")
    print(f"  owner_repo_value: {stx.owner_repo}")
    if stx.infos:
        for info in stx.infos:
            print(f"  [INFO] {info}")
    if stx.conflicts:
        for c in stx.conflicts:
            print(f"  [CONFLICT] {c['type']}: {c.get('reason', '')}")
    if stx.warnings:
        for w in stx.warnings:
            print(f"  [WARN] {w}")

    print(f"\n[L4] 远程物理绑定")
    print(f"  physical_binding_verified: {stx.physical_binding_verified}")
    print(f"  physical_binding_status: {stx.physical_binding_status}")
    print(f"  remote_head_sha: {stx.remote_head_sha}")
    print(f"  state_aligned: {stx.state_aligned}")
    print(f"  state_alignment_status: {stx.state_alignment_status}")

    print(f"\n[L5] 远程对象绑定")
    print(f"  pr_found: {stx.pr_found}")
    print(f"  pr_number: {stx.pr_number}")
    print(f"  pr_state: {stx.pr_state}")
    print(f"  pr_head_sha: {stx.pr_head_sha}")
    print(f"  pr_base_branch: {stx.pr_base_branch}")
    print(f"  pr_merge_commit: {stx.pr_merge_commit}")
    print(f"  pr_merged_at: {stx.pr_merged_at}")
    print(f"  pr_commits_count: {stx.pr_commits_count}")
    print(f"  pr_url: {stx.pr_url}")
    print(f"  pr_total_matched: {stx.pr_total_matched}")
    print(f"  pr_binding_verified: {stx.pr_binding_verified}")
    print(f"  pr_binding_status: {stx.pr_binding_status}")
    if stx.linked_issues_status:
        for li in stx.linked_issues_status:
            status = "✓" if li["exists"] else "✗"
            print(f"  linked_issue #{li['number']}: {status} {li.get('state', 'N/A')}")

    # 汇总
    print(f"\n[SOURCE TRUTH] ok={stx.ok}, owner_repo={stx.owner_repo}")
    if stx.errors:
        for e in stx.errors:
            print(f"  [ERROR] {e}")

    # 组装完整 manifest
    manifest.update(stx.manifest_data)
    manifest["owner_repo"] = stx.owner_repo
    manifest["owner_repo_source"] = stx.owner_repo_source
    manifest["owner_repo_source_path"] = str(stx.owner_repo_source_path) if stx.owner_repo_source_path else None
    manifest["local_head_sha"] = stx.local_head_sha
    manifest["remote_head_sha"] = stx.remote_head_sha
    manifest["current_branch"] = stx.current_branch
    manifest["physical_binding_verified"] = stx.physical_binding_verified
    manifest["state_aligned"] = stx.state_aligned
    manifest["pr_number"] = stx.pr_number
    manifest["pr_state"] = stx.pr_state
    manifest["pr_head_sha"] = stx.pr_head_sha
    manifest["pr_base_branch"] = stx.pr_base_branch
    manifest["pr_merge_commit"] = stx.pr_merge_commit
    manifest["pr_merged_at"] = stx.pr_merged_at
    manifest["pr_commits_count"] = stx.pr_commits_count
    manifest["pr_url"] = stx.pr_url
    manifest["pr_total_matched"] = stx.pr_total_matched
    manifest["pr_binding_verified"] = stx.pr_binding_verified

    if not stx.ok:
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"\n[FAIL] 真源验证失败")
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 有冲突但不阻断时（exit 2）
    has_conflicts = bool(stx.conflicts)
    exit_code = 2 if has_conflicts else 0

    manifest["exit_code"] = exit_code
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest, args.output)

    if has_conflicts:
        print(f"\n[WARN] 真源验证通过，但存在冲突（exit 2）")
    else:
        print(f"\n[OK] 真源验证全部通过")
    print(f"[Manifest] 已落盘: {mp}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
