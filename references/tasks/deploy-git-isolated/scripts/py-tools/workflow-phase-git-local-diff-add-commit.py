#!/usr/bin/env python3
r"""
py-tools/workflow-phase-git-local-diff-add-commit.py — 本地 diff + add + commit Phase 脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-07-22

【意图】
将本地变更的「审阅（diff）→ 暂存（add）→ 提交（commit）」三步封装为可独立执行的
workflow phase。解决昨天 jywl-settlement 初始化时手敲 `git add` + `git commit` 的
问题：手动操作无统一审计、无 diff 审阅、commit message 随意。
本 phase 执行完毕后，工作目录进入「已 commit 未 push」状态，下游应接
atomic-git-push-smoke.py 完成 push。

【职责】
  1. 输出工作区 diff（git diff），供人工/Agent 审阅变更内容
  2. 执行 git add（默认 -A，或按 --files 指定文件）
  3. 执行 git commit（支持 --message；未传时按 staged 文件自动生成）
  4. 生成 manifest 落盘到 venv/tmp/ 供追踪审计

【依赖】
底层能力（py-plugins/）：
  无（纯 git CLI 调用，不依赖 py-plugins，降低耦合）
外部工具：
  - ${devroot}/venv/git/cmd/git.exe
环境变量：
  - GIT_USER_NAME（devroot/.env 或 git config，用于 commit 身份）
  - GIT_USER_EMAIL（devroot/.env 或 git config，用于 commit 身份）

【预检】
执行本脚本前必须满足的前置条件：
  - 目录状态: --target 存在且包含 .git/
  - 外部工具: ${devroot}/venv/git/cmd/git.exe 可执行
  - 身份配置: git config user.name / user.email 已配置（或 .env 中有）
  - 变更存在: git diff / git status 显示有变更（无变更时 --allow-empty 可强制提交）

【调用参数】
  --devroot       <str, 可选, 默认=Path.cwd()>  工具链根路径
  --target        <str, 可选, 默认=devroot>     操作目标仓库路径（polyrepo 场景）
  --git-exe       <str, 可选>                   隔离 git.exe 绝对路径（默认从 devroot 推导）
  --message       <str, 可选>                   commit message（未传时自动生成）
  --files         <str, 可选>                   指定 add 的文件路径（空格分隔，默认 -A）
  --dry-run       <flag, 可选>                  仅输出 diff，不执行 add/commit
  --allow-empty   <flag, 可选>                  允许空提交（无变更时也执行 commit）
  --output        <str, 可选>                   产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/workflow-phase-git-local-diff-add-commit-manifest-{timestamp}.json）

【用法示例】
    # 单仓库：diff → add -A → commit（自动生成 message）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-phase-git-local-diff-add-commit.py" `
        --devroot "${devroot}" `
        --target "${devroot}"

    # Polyrepo：diff → add -A → commit（指定 message）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-phase-git-local-diff-add-commit.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --message "init: add .emptydir and GOAL.md"

    # 仅 diff 审阅（不执行 add/commit）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-phase-git-local-diff-add-commit.py" `
        --devroot "${devroot}" `
        --target "${devroot}" `
        --dry-run

    # 指定文件 add（非 -A）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-phase-git-local-diff-add-commit.py" `
        --devroot "${devroot}" `
        --target "${devroot}" `
        --files ".emptydir GOAL.md"

【返回】
    exit 0 = diff/add/commit 全部成功（或 --dry-run 成功输出 diff）
    exit 1 = 失败（git 命令错误、目标目录无效、commit 失败等）

【审计产物】
    ${devroot}/venv/tmp/local-diff-add-commit-manifest-{timestamp}.json:
      {
        "atomic_tool": "workflow-phase-git-local-diff-add-commit",
        "version": "1.0.0",
        "devroot": "...",
        "target": "...",
        "git_exe": "...",
        "dry_run": false,
        "files_added": ["..."],
        "commit_message": "...",
        "commit_hash": "abc1234",
        "diff_length_chars": 1234,
        "exit_code": 0,
        "exit_at": "...",
        "errors": []
      }

【关联】
    - workflow: 被 polyrepo 全链条部署 workflow 在 push 前调用（Step 4→5 的独立 phase 形态）
    - 上游消费: 人类终端或 workflow 编排器直接调用
    - 下游衔接: atomic-git-push-smoke.py（本 phase 执行完后，接 smoke push 到 remote）
    - env-migration: references/env-migrations/env-migration-jywl-settlement-polyrepo-init-2026-07-21-173210.md
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


# =============================================================================
# Manifest 生成
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str = None) -> Path:
    """保存 manifest 到 venv/tmp/，供追踪审计。"""
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"local-diff-add-commit-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def _run_git(git_exe: Path, args: list, cwd: Path) -> subprocess.CompletedProcess:
    """在目标仓库执行隔离 git 命令。"""
    cmd = [str(git_exe), "-C", str(cwd)] + args
    print(f"[EXEC] {' '.join(cmd)}")
    sys.stdout.flush()
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _generate_commit_message(git_exe: Path, target: Path) -> str:
    """从 staged 文件自动生成 commit message。"""
    r = _run_git(git_exe, ["diff", "--cached", "--name-only"], target)
    files = [f.strip() for f in r.stdout.strip().splitlines() if f.strip()]

    if not files:
        return "chore: empty commit"

    if len(files) == 1:
        return f"chore: update {files[0]}"

    # 按扩展名分类
    exts = {}
    for f in files:
        ext = Path(f).suffix or "(no ext)"
        exts.setdefault(ext, []).append(f)

    if len(exts) == 1:
        ext = list(exts.keys())[0]
        return f"chore: update {len(files)} files ({ext})"

    return f"chore: update {len(files)} files"


def main():
    parser = argparse.ArgumentParser(description="本地 diff + add + commit Phase")
    parser.add_argument("--devroot", default=None, help="Devroot 路径（默认使用当前工作目录）")
    parser.add_argument("--target", default=None, help="操作目标仓库路径（polyrepo 场景，默认等于 --devroot）")
    parser.add_argument("--git-exe", default=None, help="隔离 git.exe 绝对路径（默认从 devroot 推导）")
    parser.add_argument("--message", default=None, help="Commit message（未传时从 staged 文件自动生成）")
    parser.add_argument("--files", default=None, help="指定 add 的文件路径（空格分隔，默认 -A）")
    parser.add_argument("--dry-run", action="store_true", help="仅输出 diff，不执行 add/commit")
    parser.add_argument("--allow-empty", action="store_true", help="允许空提交")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/local-diff-add-commit-manifest-{timestamp}.json）")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()
    target = Path(args.target) if args.target else devroot
    git_exe = Path(args.git_exe) if args.git_exe else (devroot / "venv" / "git" / "cmd" / "git.exe")

    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        sys.exit(1)
    if not target.exists():
        print(f"[ERROR] target 不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not git_exe.exists():
        print(f"[ERROR] git.exe 不存在: {git_exe}", file=sys.stderr)
        sys.exit(1)
    if not (target / ".git").exists():
        print(f"[ERROR] target 下无 .git/: {target}", file=sys.stderr)
        sys.exit(1)

    # Manifest 初始化
    manifest = {
        "atomic_tool": "workflow-phase-git-local-diff-add-commit",
        "version": "1.0.0",
        "devroot": str(devroot),
        "target": str(target),
        "git_exe": str(git_exe),
        "dry_run": args.dry_run,
        "files_added": [],
        "commit_message": None,
        "commit_hash": None,
        "diff_length_chars": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    # Step 1: Diff（工作区 vs HEAD）
    print("\n" + "=" * 50)
    print("[Step 1] 工作区 Diff")
    print("=" * 50)

    r = _run_git(git_exe, ["diff", "HEAD"], target)
    diff_text = r.stdout or ""
    manifest["diff_length_chars"] = len(diff_text)

    if diff_text.strip():
        print(diff_text)
        print(f"[INFO] Diff 长度: {len(diff_text)} 字符")
    else:
        print("[INFO] 无变更（工作区与 HEAD 一致）")

    # --dry-run 模式：到此结束
    if args.dry_run:
        print("\n[DRY-RUN] 已输出 diff，不执行 add/commit")
        manifest["exit_code"] = 0
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(0)

    # 检查是否有变更（diff HEAD 或 untracked）
    r_status = _run_git(git_exe, ["status", "--short"], target)
    has_changes = bool(r_status.stdout.strip())

    if not has_changes and not args.allow_empty:
        print("[FAIL] 无变更可提交（工作区干净且无 untracked 文件）")
        print("[HINT] 如需空提交，请添加 --allow-empty")
        manifest["errors"].append("no changes to commit")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # Step 2: Add
    print("\n" + "=" * 50)
    print("[Step 2] Git Add")
    print("=" * 50)

    if args.files:
        file_list = args.files.split()
        add_args = ["add"] + file_list
        print(f"[INFO] 指定文件: {file_list}")
    else:
        add_args = ["add", "-A"]
        print("[INFO] 模式: add -A（全部）")

    r = _run_git(git_exe, add_args, target)
    if r.returncode != 0:
        print(f"[FAIL] git add 失败: {r.stderr.strip()}")
        manifest["errors"].append(f"git add failed: {r.stderr.strip()}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 获取实际 add 的文件列表
    r = _run_git(git_exe, ["diff", "--cached", "--name-only"], target)
    added_files = [f.strip() for f in r.stdout.strip().splitlines() if f.strip()]
    manifest["files_added"] = added_files
    print(f"[OK] Staged {len(added_files)} 个文件")
    for f in added_files:
        print(f"  + {f}")

    # Step 3: Commit
    print("\n" + "=" * 50)
    print("[Step 3] Git Commit")
    print("=" * 50)

    commit_message = args.message
    if not commit_message:
        commit_message = _generate_commit_message(git_exe, target)
        print(f"[INFO] 自动生成 message: {commit_message}")
    else:
        print(f"[INFO] 指定 message: {commit_message}")

    manifest["commit_message"] = commit_message

    commit_args = ["commit", "-m", commit_message]
    if args.allow_empty:
        commit_args.append("--allow-empty")

    r = _run_git(git_exe, commit_args, target)
    if r.stdout:
        print(r.stdout.strip())
    if r.returncode != 0:
        stderr = r.stderr.strip() if r.stderr else ""
        # 检查是否因为无变更
        if "nothing to commit" in stderr.lower() or "no changes added" in stderr.lower():
            if args.allow_empty:
                print(f"[FAIL] git commit 失败（即使是 --allow-empty）: {stderr}")
            else:
                print(f"[FAIL] git commit 失败: {stderr}")
                print("[HINT] 若需空提交，请添加 --allow-empty")
        else:
            print(f"[FAIL] git commit 失败: {stderr}")
        manifest["errors"].append(f"git commit failed: {stderr}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 获取 commit hash
    r = _run_git(git_exe, ["rev-parse", "--short", "HEAD"], target)
    commit_hash = r.stdout.strip()
    manifest["commit_hash"] = commit_hash
    print(f"[OK] Commit 成功: {commit_hash}")

    # 成功收尾
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest)
    print(f"[Manifest] 已落盘: {mp}")

    print(f"\n[SUCCESS] 本地 diff/add/commit 完成")
    print(f"  target: {target}")
    print(f"  commit: {commit_hash}")
    print(f"  message: {commit_message}")
    print(f"  下一步: 执行 atomic-git-push-smoke.py 完成 push")
    sys.exit(0)


if __name__ == "__main__":
    main()
