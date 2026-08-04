#!/usr/bin/env python3
r"""
atomic-git-worktree-add.py -- Git Worktree 创建原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-08-03

【意图】
git worktree add 是创建并行开发工作区的标准操作，但手敲命令易遗漏 preflight
检查（repo 状态、分支存在性、目录冲突），且后续 pipeline 需要消费 worktree
路径等上下文。本工具将 worktree 创建封装为原子操作，含 preflight、进度输出、
post-audit、manifest 落盘，支持 --dry-run 模拟执行。

【职责】
  1. Main Repo Preflight：验证 repo/.git/branch/git.exe
  2. 计算 worktree 路径（显式 dir 或 name 拼接）
  3. Git Worktree Add：执行 `git worktree add [-b] <path> <branch>`
  4. Worktree Post-Audit：验证目录/.git/HEAD
  5. Manifest 落盘到 venv/tmp/ 供下游 pipeline 消费

【用法】
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-worktree-add.py" `
        --repo "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --worktree-name "feat-demo" `
        --new-branch "feat/demo"

【示例】
    # 标准调用（基于 main 创建新分支）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-worktree-add.py" `
        --repo "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --worktree-name "feat-demo" `
        --new-branch "feat/demo"

    # 基于已有分支创建 worktree
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-worktree-add.py" `
        --repo "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --worktree-name "hotfix-login" `
        --branch "hotfix/login"

    # Dry-run 模拟
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-worktree-add.py" `
        --repo "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --worktree-name "feat-demo" `
        --dry-run
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def _run_cmd(cmd: list, cwd: Path = None) -> subprocess.CompletedProcess:
    kwargs = {"capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}
    if cwd:
        kwargs["cwd"] = str(cwd)
    return subprocess.run(cmd, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="Git Worktree Add Atomic Tool")
    parser.add_argument("--devroot", help="Toolchain root (default: Path.cwd())")
    parser.add_argument("--repo", required=True, help="Absolute path to the main repository")
    parser.add_argument("--branch", default="main", help="Base branch (default: main)")
    parser.add_argument("--new-branch", help="Create a new branch for the worktree")
    parser.add_argument("--worktree-name", help="Worktree name (e.g., feat-demo). Mutually exclusive with --worktree-dir")
    parser.add_argument("--worktree-dir", help="Absolute path to the worktree directory. Mutually exclusive with --worktree-name")
    parser.add_argument("--output", help="Manifest output path (default: auto-generated in venv/tmp/)")
    parser.add_argument("--show-progress", action="store_true", help="Print progress for each step")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without creating worktree")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()
    repo_path = Path(args.repo).resolve()
    branch = args.branch
    new_branch = args.new_branch
    worktree_name = args.worktree_name
    worktree_dir = args.worktree_dir
    dry_run = args.dry_run
    show_progress = args.show_progress

    manifest = {
        "atomic_tool": "atomic-git-worktree-add",
        "version": "1.0.0",
        "dry_run": dry_run,
        "repo": str(repo_path),
        "branch": branch,
        "new_branch": new_branch,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    def progress(msg: str):
        if show_progress:
            print(f"[PROGRESS] {msg}")

    # --- Step 0: Validate parameters ---
    progress("Step 0: Validating parameters")

    if worktree_dir and worktree_name:
        print("[ERROR] --worktree-dir and --worktree-name are mutually exclusive. Provide one, not both.")
        manifest["exit_code"] = 1
        manifest["error"] = "mutually_exclusive_params"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    if not worktree_dir and not worktree_name:
        print("[ERROR] Must provide either --worktree-dir or --worktree-name. Explicit naming is required.")
        manifest["exit_code"] = 1
        manifest["error"] = "missing_worktree_identity"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    # --- Step 1: Main Repo Preflight ---
    progress("Step 1: Main repo preflight")

    if not repo_path.exists():
        print(f"[ERROR] Repo does not exist: {repo_path}")
        manifest["exit_code"] = 1
        manifest["error"] = "repo_not_found"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    git_dir = repo_path / ".git"
    if not git_dir.exists():
        print(f"[ERROR] Not a git repository: {repo_path}")
        manifest["exit_code"] = 1
        manifest["error"] = "not_git_repo"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        print(f"[ERROR] Isolated git.exe not found: {git_exe}")
        manifest["exit_code"] = 1
        manifest["error"] = "git_exe_not_found"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    # Verify branch exists
    result = _run_cmd([str(git_exe), "-C", str(repo_path), "rev-parse", "--verify", branch])
    if result.returncode != 0:
        print(f"[ERROR] Branch '{branch}' does not exist in repo: {repo_path}")
        manifest["exit_code"] = 1
        manifest["error"] = "branch_not_found"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    print(f"[OK] Preflight passed: repo={repo_path}, branch={branch}, git={git_exe}")

    # --- Step 2: Compute worktree path ---
    progress("Step 2: Computing worktree path")

    if worktree_dir:
        worktree_path = Path(worktree_dir).resolve()
    else:
        worktree_path = (repo_path.parent / f"{repo_path.name}.wt" / worktree_name).resolve()

    manifest["worktree"] = str(worktree_path)
    print(f"[INFO] Worktree path: {worktree_path}")

    # Verify target directory is empty or does not exist
    if worktree_path.exists():
        try:
            contents = list(worktree_path.iterdir())
            if contents:
                print(f"[ERROR] Target directory exists and is not empty: {worktree_path}")
                manifest["exit_code"] = 1
                manifest["error"] = "directory_not_empty"
                _write_manifest(manifest, args.output, devroot)
                sys.exit(1)
        except PermissionError:
            print(f"[ERROR] Cannot access target directory: {worktree_path}")
            manifest["exit_code"] = 1
            manifest["error"] = "directory_access_denied"
            _write_manifest(manifest, args.output, devroot)
            sys.exit(1)

    # --- Step 3: Git Worktree Add ---
    progress("Step 3: Git worktree add")

    if dry_run:
        cmd_parts = [str(git_exe), "-C", str(repo_path), "worktree", "add"]
        if new_branch:
            cmd_parts.extend(["-b", new_branch])
        cmd_parts.extend([str(worktree_path)])
        if new_branch:
            cmd_parts.append(branch)
        print(f"[DRY-RUN] Would execute: {' '.join(cmd_parts)}")
        manifest["exit_code"] = 0
        manifest["dry_run_cmd"] = " ".join(cmd_parts)
        _write_manifest(manifest, args.output, devroot)
        print("[DRY-RUN] Complete. No changes made.")
        sys.exit(0)

    # Ensure parent directory exists
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [str(git_exe), "-C", str(repo_path), "worktree", "add"]
    if new_branch:
        cmd.extend(["-b", new_branch])
    cmd.append(str(worktree_path))
    if not new_branch:
        cmd.append(branch)

    result = _run_cmd(cmd)
    if result.returncode != 0:
        print(f"[ERROR] git worktree add failed: {result.stderr.strip()}")
        manifest["exit_code"] = 1
        manifest["error"] = "worktree_add_failed"
        manifest["stderr"] = result.stderr.strip()
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    print(f"[OK] Worktree created: {worktree_path}")

    # --- Step 4: Worktree Post-Audit ---
    progress("Step 4: Worktree post-audit")

    if not worktree_path.exists():
        print(f"[ERROR] Worktree directory not created: {worktree_path}")
        manifest["exit_code"] = 1
        manifest["error"] = "worktree_not_created"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    git_file = worktree_path / ".git"
    if not git_file.exists():
        print(f"[ERROR] .git file not found in worktree: {git_file}")
        manifest["exit_code"] = 1
        manifest["error"] = "git_file_missing"
        _write_manifest(manifest, args.output, devroot)
        sys.exit(1)

    # Verify HEAD points to correct branch
    result = _run_cmd([str(git_exe), "-C", str(worktree_path), "rev-parse", "--abbrev-ref", "HEAD"])
    actual_branch = result.stdout.strip()
    expected_branch = new_branch if new_branch else branch
    if actual_branch != expected_branch:
        print(f"[WARN] HEAD mismatch: expected '{expected_branch}', got '{actual_branch}'")
        manifest["head_mismatch"] = {"expected": expected_branch, "actual": actual_branch}
    else:
        print(f"[OK] HEAD verified: {actual_branch}")

    # --- Step 5: Manifest & Exit ---
    progress("Step 5: Generating manifest")

    manifest["exit_code"] = 0
    manifest["head"] = actual_branch
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    output_path = _write_manifest(manifest, args.output, devroot)
    print(f"\n[Manifest] 已落盘: {output_path}")
    print("[DONE] 全部通过")
    sys.exit(0)


def _write_manifest(manifest: dict, output: str, devroot: Path) -> Path:
    if output:
        path = Path(output)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = devroot / "venv" / "tmp" / f"worktree-add-{ts}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    main()
