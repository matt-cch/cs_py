#!/usr/bin/env python3
r"""
atomic-git-preflight-general.py -- General Git Preflight Verification Atomic Tool

Design Intent:
  - Toolchain is anchored at Path.cwd() (reads .env, venv/git, task/ plugins).
  - Operation target is explicitly specified via --target (detects .git/,
    .gitignore, executes git commands).
  - Supports multi-polyrepo scenarios: one toolchain verifies any independent
    repository.

Usage:
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-preflight-general.py" --target "${devroot}\apps\repos\jywl-team\jywl-lab"

Arguments:
    --target       Absolute path to the target repository (required).
    --no-security  Skip security scan (executed by default).
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def _run_git(git_exe: Path, args: list, cwd: Path = None) -> subprocess.CompletedProcess:
    cmd = [str(git_exe)] + args
    kwargs = {}
    if cwd:
        kwargs["cwd"] = str(cwd)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )


def main():
    parser = argparse.ArgumentParser(
        description="General Git Preflight Verification"
    )
    parser.add_argument(
        "--target", required=True, help="Absolute path to the target repository"
    )
    parser.add_argument(
        "--security", action="store_true",
        help="Enable security scan (shorthand for --security-level=basic)"
    )
    parser.add_argument(
        "--security-level",
        choices=["off", "minimal", "basic", "full"],
        default=None,
        help="Security scan level: off=none, minimal=tracked files only, basic=tracked+staged+content, full=includes .gitignore strictness (default: off unless --security is set)"
    )
    args = parser.parse_args()

    toolchain_root = Path.cwd()
    target_repo = Path(args.target)

    if not target_repo.exists():
        print(f"[ERROR] Target repository does not exist: {target_repo}")
        sys.exit(1)

    git_exe = toolchain_root / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        print(f"[ERROR] Isolated git.exe not found: {git_exe}")
        sys.exit(1)

    # Load plugins via py_lib (toolchain anchored at Path.cwd()).
    registry = load_plugins(
        devroot=str(toolchain_root), tags=["git", "core"]
    )

    # 1. Read toolchain .env (optional, failures become warnings).
    env = {}
    try:
        env = registry.env_config.read_env(str(toolchain_root / ".env"))
    except Exception as e:
        print(f"[WARN] Toolchain .env read failed: {e}")

    # 2. Detect target repository git environment.
    print("=" * 50)
    print("Git Environment Detection")
    print("=" * 50)
    print(f"Toolchain root: {toolchain_root}")
    print(f"Target repo:    {target_repo}")
    print(f"git.exe:        {git_exe}")

    has_repo = (target_repo / ".git").exists()
    print(f"Repo exists:    {has_repo}")

    if has_repo:
        # Identity
        r_name = _run_git(
            git_exe, ["-C", str(target_repo), "config", "user.name"]
        )
        r_email = _run_git(
            git_exe, ["-C", str(target_repo), "config", "user.email"]
        )
        user_name = r_name.stdout.strip() if r_name.returncode == 0 else ""
        user_email = r_email.stdout.strip() if r_email.returncode == 0 else ""
        print(f"user.name:      {user_name or '(not configured)'}")
        print(f"user.email:     {user_email or '(not configured)'}")

        # Branch
        r = _run_git(
            git_exe, ["-C", str(target_repo), "branch", "--show-current"]
        )
        branch = r.stdout.strip() if r.returncode == 0 else ""
        print(f"Current branch: {branch or '(none)'}")
        if not branch:
            print("[WARN] No current branch (possible detached HEAD)")

        # Working tree clean
        r = _run_git(
            git_exe, ["-C", str(target_repo), "status", "--porcelain"]
        )
        is_clean = r.returncode == 0 and not r.stdout.strip()
        print(f"Working tree:   {'clean' if is_clean else 'dirty'}")

        # Remote
        r = _run_git(
            git_exe, ["-C", str(target_repo), "remote", "-v"]
        )
        if r.returncode == 0 and r.stdout.strip():
            print("Remote:")
            for line in r.stdout.strip().splitlines():
                print(f"  {line}")
        else:
            print("Remote:         (none)")
    else:
        print("[WARN] No .git/ under target path; skipping branch/identity checks")

    # 3. Security scan (executed in target repo with isolated git.exe).
    effective_level = args.security_level
    if args.security and effective_level is None:
        effective_level = "basic"
    if effective_level is None:
        effective_level = "off"

    if effective_level != "off" and has_repo:
        print("\n" + "=" * 50)
        print(f"Security Scan (level: {effective_level})")
        print("=" * 50)
        try:
            sec = registry.git_security.scan_git_security(
                target_repo, git_exe=git_exe
            )
            if effective_level in ("minimal", "basic", "full"):
                if sec.tracked_files:
                    print(f"[1] Tracked files: {len(sec.tracked_files)}")
            if effective_level in ("basic", "full"):
                if sec.staged_files:
                    print(f"[2] Staged files:  {len(sec.staged_files)}")
                    for f in sec.staged_files:
                        print(f"    - {f}")
                if sec.untracked_files:
                    print(f"[3] Untracked files: {len(sec.untracked_files)}")
            if sec.violations:
                print("[4] Violations:")
                for v in sec.violations:
                    print(f"    [FAIL] {v}")
            else:
                print("[4] Security check passed")
            if sec.warnings:
                for w in sec.warnings:
                    print(f"    [WARN] {w}")
        except Exception as e:
            print(f"[ERROR] Security scan exception: {e}")

    print("\n[OK] atomic-git-preflight-general completed")


if __name__ == "__main__":
    main()
