#!/usr/bin/env python3
r"""
atomic-git-worktree-link-config.py -- Git Worktree 配置文件硬链接原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-08-03

【意图】
git worktree add 创建的工作树不会自动带出未追踪的配置文件（.gitignore、
.gitattributes、git-security.json）。本工具在主仓库与 worktree 之间建立
硬链接，确保配置变更在两端实时同步，避免 worktree 中因缺少配置而导致
的格式混乱或安全策略失效。

【职责】
  1. 验证主仓库存在且包含目标配置文件
  2. 验证 worktree 目录存在
  3. 在 worktree 中为每个目标文件创建硬链接（Windows mklink /H）
  4. 验证链接可访问且内容与源文件一致
  5. 生成 manifest 落盘到 venv/tmp/ 供审计追踪

【用法】
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-worktree-link-config.py" `
        --repo "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --worktree "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo"

【示例】
    # 标准调用（链接默认三件套）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-worktree-link-config.py" `
        --repo "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --worktree "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo"

    # 自定义文件列表
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-worktree-link-config.py" `
        --repo "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --worktree "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo" `
        --files ".gitignore,.gitattributes"
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
    parser = argparse.ArgumentParser(description="Git Worktree Config File Hard Link")
    parser.add_argument("--repo", required=True, help="Absolute path to the main repository")
    parser.add_argument("--worktree", required=True, help="Absolute path to the worktree directory")
    parser.add_argument(
        "--files",
        default=".gitignore,.gitattributes,git-security.json",
        help="Comma-separated list of config files to link (default: .gitignore,.gitattributes,git-security.json)",
    )
    parser.add_argument("--output", help="Manifest output path (default: auto-generated in venv/tmp/)")
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    worktree_path = Path(args.worktree).resolve()
    target_files = [f.strip() for f in args.files.split(",") if f.strip()]

    # Step 1: Validate repo
    if not repo_path.exists():
        print(f"[ERROR] Repo does not exist: {repo_path}")
        sys.exit(1)

    git_dir = repo_path / ".git"
    if git_dir.exists():
        print(f"[OK] Repo validated: {repo_path}")
    else:
        print(f"[WARN] .git not found at {git_dir}, proceeding anyway")

    # Step 2: Validate worktree
    if not worktree_path.exists():
        print(f"[ERROR] Worktree does not exist: {worktree_path}")
        sys.exit(1)

    git_file = worktree_path / ".git"
    if git_file.exists():
        print(f"[OK] Worktree validated: {worktree_path}")
    else:
        print(f"[WARN] .git file not found at {git_file}, proceeding anyway")

    # Step 3: Verify source files exist
    links_created = []
    errors = []

    for filename in target_files:
        src = repo_path / filename
        dst = worktree_path / filename

        if not src.exists():
            print(f"[SKIP] Source file missing: {src}")
            errors.append({"file": filename, "status": "source_missing", "path": str(src)})
            continue

        if dst.exists():
            print(f"[SKIP] Destination already exists: {dst}")
            errors.append({"file": filename, "status": "dest_exists", "path": str(dst)})
            continue

        # Create hard link via cmd /c mklink /H
        cmd = ["cmd", "/c", "mklink", "/H", str(dst), str(src)]
        result = _run_cmd(cmd)

        if result.returncode != 0:
            print(f"[FAIL] mklink failed for {filename}: {result.stderr.strip()}")
            errors.append({"file": filename, "status": "mklink_failed", "stderr": result.stderr.strip()})
            continue

        # Verify link exists and is accessible
        if not dst.exists():
            print(f"[FAIL] Link verification failed: {dst} does not exist after mklink")
            errors.append({"file": filename, "status": "verify_failed"})
            continue

        # Verify content match (read both files)
        try:
            src_content = src.read_text(encoding="utf-8")
            dst_content = dst.read_text(encoding="utf-8")
            if src_content == dst_content:
                print(f"[OK] Linked {filename}")
                links_created.append({"file": filename, "src": str(src), "dst": str(dst)})
            else:
                print(f"[WARN] Content mismatch for {filename}")
                errors.append({"file": filename, "status": "content_mismatch"})
        except Exception as e:
            print(f"[WARN] Content read error for {filename}: {e}")
            links_created.append({"file": filename, "src": str(src), "dst": str(dst), "verify": "read_error"})

    # Step 4: Generate manifest
    manifest = {
        "atomic_tool": "atomic-git-worktree-link-config",
        "version": "1.0.0",
        "repo": str(repo_path),
        "worktree": str(worktree_path),
        "files_requested": target_files,
        "links_created": links_created,
        "errors": errors,
        "exit_code": 0 if not errors else 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        devroot = Path.cwd()
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        output_path = devroot / "venv" / "tmp" / f"worktree-link-config-{ts}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[Manifest] 已落盘: {output_path}")

    if errors:
        print(f"[DONE] 完成，但有 {len(errors)} 个错误")
        sys.exit(1)
    else:
        print("[DONE] 全部通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
