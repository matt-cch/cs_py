#!/usr/bin/env python3
r"""
py-tools/atomic-git-push-smoke.py — 无弹窗安全 smoke push 原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-07-21

【意图】
在自动化部署流程中，直接 `git push` 会触发 Git Credential Manager (GCM)
弹窗阻塞流程。本工具通过构造 PAT 认证 URL、阻断 GCM 交互环境变量、
双路 preflight 检查（staged 文件 + 未 push 的 commit），实现无弹窗的
安全 push。
源于 env-migration 中的踩坑记录：
  - GCM 弹窗陷阱：裸 https URL 会弹出 "Select an account" 窗口
  - preflight 遗漏：commit 后 staged 被清空，导致 "nothing to push" 误判

【职责】
  1. 从 devroot/.env 读取 PAT，构造认证 URL（https://username:PAT@github.com/...）
  2. 阻断 GCM 弹窗（GCM_INTERACTIVE=0, GIT_TERMINAL_PROMPT=0, credential.helper=""）
  3. 双路 preflight：检查 staged 文件 + 检查未 push 的 commit
  4. 执行 git push 到指定 remote/branch
  5. 生成 manifest 落盘到 venv/tmp/ 供追踪审计

【依赖】
底层能力（py-plugins/）：
  - env_config（读取 .env 中的 GITHUB_PAT/GITHUB_USERNAME）
  - process_runner（执行 git config 等命令）
外部工具：
  - ${devroot}/venv/git/cmd/git.exe
环境变量：
  - GITHUB_PAT（devroot/.env，构造认证 URL）
  - GITHUB_USERNAME（devroot/.env，构造认证 URL）

【预检】
执行本脚本前必须满足的前置条件：
  - 文件存在性: devroot/.env 存在且含 GITHUB_PAT、GITHUB_USERNAME
  - 目录状态: --target 存在且包含 .git/
  - 外部工具: ${devroot}/venv/git/cmd/git.exe 可执行
  - 内容检查: 有 staged 文件或未 push 的 commit（双路 preflight）

【调用参数】
  --devroot   <str, 必填>                工具链根目录绝对路径
  --target    <str, 必填>                本地仓库目录绝对路径
  --remote    <str, 可选, 默认=origin>    remote 名称
  --branch    <str, 可选, 默认=main>      分支名
  --output    <str, 可选>                产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-git-push-smoke-manifest-{timestamp}.json）

【用法示例】
    # 单仓库 smoke push
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-push-smoke.py" `
        --devroot "${devroot}" `
        --target "${devroot}" `
        --remote "origin" `
        --branch "main"

    # Polyrepo smoke push
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-push-smoke.py" `
        --devroot "${devroot}" `
        --target "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --remote "origin" `
        --branch "main"

【返回】
    exit 0 = push 成功
    exit 1 = 失败（无可 push 内容、push 失败、超时、异常）

【审计产物】
    ${devroot}/venv/tmp/smoke-push-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-git-push-smoke",
        "version": "1.0.0",
        "devroot": "...",
        "target": "...",
        "remote": "origin",
        "branch": "main",
        "repo_url": "https://github.com/...",
        "has_staged": true|false,
        "has_unpushed": true|false,
        "exit_code": 0|1,
        "exit_at": "...",
        "errors": []
      }

【关联】
    - workflow: 被 workflow-git-deploy-full-poly.py 的 Step 7（push）调用
    - env-migration: references/env-migrations/env-migration-jywl-settlement-polyrepo-init-2026-07-21-173210.md
    - 上游依赖: atomic-git-repo-clone.py（clone 后执行 smoke push 验证链路）
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
# 路径解析
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
# 脱敏
# =============================================================================
def _mask_pat(text: str) -> str:
    """将 URL 中的 PAT 替换为 ***。"""
    if not text:
        return text
    text = re.sub(r"(https?://[^:]+:)([^@]+)(@github\.com)", r"\1***\3", text)
    return text


def _print_cmd(cmd: list) -> None:
    print(f"[EXEC] {_mask_pat(' '.join(cmd))}")


# =============================================================================
# Manifest
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str = None) -> Path:
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"smoke-push-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="无弹窗安全 smoke push")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径")
    parser.add_argument("--target", required=True, help="本地仓库目录绝对路径")
    parser.add_argument("--remote", default="origin", help="remote 名称（默认 origin）")
    parser.add_argument("--branch", default="main", help="分支名（默认 main）")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/smoke-push-manifest-{timestamp}.json）")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    target = Path(args.target)

    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        sys.exit(1)
    if not target.exists():
        print(f"[ERROR] target 不存在: {target}", file=sys.stderr)
        sys.exit(1)
    if not (target / ".git").exists():
        print(f"[ERROR] target 下无 .git/: {target}", file=sys.stderr)
        sys.exit(1)

    # 导入 env_config
    try:
        import env_config
    except ImportError as e:
        print(f"[ERROR] 无法导入 env_config: {e}", file=sys.stderr)
        sys.exit(1)

    # 导入 process_runner
    try:
        import process_runner
    except ImportError as e:
        print(f"[ERROR] 无法导入 process_runner: {e}", file=sys.stderr)
        sys.exit(1)

    # 读取 .env
    env_data = env_config.read_env(str(devroot / ".env"))
    pat = env_data.get("GITHUB_PAT", "").strip()
    username = env_data.get("GITHUB_USERNAME", "").strip()

    if not pat:
        print(f"[ERROR] .env 中 GITHUB_PAT 未配置", file=sys.stderr)
        sys.exit(1)
    if not username:
        print(f"[ERROR] .env 中 GITHUB_USERNAME 未配置", file=sys.stderr)
        sys.exit(1)

    # git.exe
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        print(f"[ERROR] git.exe 不存在: {git_exe}", file=sys.stderr)
        sys.exit(1)

    # 获取 repo_url（从 target 的 git remote）
    r = subprocess.run(
        [str(git_exe), "-C", str(target), "remote", "get-url", args.remote],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0 or not r.stdout.strip():
        print(f"[ERROR] 无法获取 remote URL: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    repo_url = r.stdout.strip()

    # 构造认证 URL: https://username:PAT@github.com/owner/repo
    repo_path = re.sub(r"^https://github.com/", "", repo_url)
    auth_url = f"https://{username}:{pat}@github.com/{repo_path}"

    # Manifest
    manifest = {
        "atomic_tool": "atomic-git-push-smoke",
        "version": "1.0.0",
        "devroot": str(devroot),
        "target": str(target),
        "remote": args.remote,
        "branch": args.branch,
        "repo_url": repo_url,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "has_staged": False,
        "has_unpushed": False,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    # Step 1: 阻断 GCM 弹窗
    print("\n" + "=" * 50)
    print("[Step 1] 阻断 GCM 弹窗")
    print("=" * 50)

    cmd = [str(git_exe), "-C", str(target), "config", "--local", "credential.helper", ""]
    _print_cmd(cmd)
    sys.stdout.flush()
    try:
        process_runner.run_streaming(cmd, label="git config credential.helper", timeout=30)
        print("[OK] GCM 弹窗已阻断")
    except Exception as e:
        print(f"[WARN] credential.helper 设置失败: {e}")

    # Step 1.5: Preflight — 检查可 push 内容（staged 或未 push 的 commit）
    print("\n" + "=" * 50)
    print("[Step 1.5] Preflight — 检查可 push 内容")
    print("=" * 50)

    # 1.5a: 检查 staged 文件
    cmd = [str(git_exe), "-C", str(target), "diff", "--cached", "--quiet"]
    _print_cmd(cmd)
    sys.stdout.flush()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    has_staged = r.returncode != 0

    if has_staged:
        cmd_list = [str(git_exe), "-C", str(target), "diff", "--cached", "--name-only"]
        r_list = subprocess.run(cmd_list, capture_output=True, text=True, encoding="utf-8", errors="replace")
        staged_files = [f.strip() for f in r_list.stdout.strip().splitlines() if f.strip()]
        print(f"[OK] 发现 {len(staged_files)} 个 staged 文件")
        for f in staged_files:
            print(f"  - {f}")
    else:
        print("[INFO] 无 staged 文件")

    manifest["has_staged"] = has_staged

    # 1.5b: 检查未 push 的 commit
    cmd = [str(git_exe), "-C", str(target), "log", f"{args.remote}/{args.branch}..{args.branch}", "--oneline"]
    _print_cmd(cmd)
    sys.stdout.flush()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    unpushed_commits = [c.strip() for c in r.stdout.strip().splitlines() if c.strip()]
    has_unpushed = len(unpushed_commits) > 0

    if has_unpushed:
        print(f"[OK] 发现 {len(unpushed_commits)} 个未 push 的 commit:")
        for c in unpushed_commits:
            print(f"  - {c}")
    else:
        print("[INFO] 无未 push 的 commit")

    manifest["has_unpushed"] = has_unpushed

    # 综合判断
    if not has_staged and not has_unpushed:
        print("[FAIL] 无可 push 内容（无 staged 文件且无未 push 的 commit）")
        print("[HINT] 请先执行: git add <files> && git commit -m \"...\"")
        manifest["errors"].append("nothing to push")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # Step 2: 执行 git push（注入环境变量）
    print("\n" + "=" * 50)
    print("[Step 2] git push")
    print("=" * 50)
    print(f"[INFO] target: {target}")
    print(f"[INFO] remote: {args.remote}")
    print(f"[INFO] branch: {args.branch}")

    cmd = [str(git_exe), "-C", str(target), "push", auth_url, args.branch]
    _print_cmd(cmd)
    sys.stdout.flush()

    # 注入环境变量阻断弹窗
    push_env = os.environ.copy()
    push_env["GCM_INTERACTIVE"] = "0"
    push_env["GIT_TERMINAL_PROMPT"] = "0"

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=push_env,
        )
        for line in proc.stdout:
            line = line.rstrip("\n")
            print(_mask_pat(line), flush=True)
        proc.wait(timeout=120)

        if proc.returncode != 0:
            print(f"[FAIL] git push 失败 (exit {proc.returncode})")
            manifest["errors"].append(f"git push failed: exit {proc.returncode}")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)

        print("[OK] push 成功")

    except subprocess.TimeoutExpired:
        print("[FAIL] git push 超时")
        manifest["errors"].append("git push timeout")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] git push 异常: {e}")
        manifest["errors"].append(f"git push exception: {e}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 成功
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest)
    print(f"[Manifest] 已落盘: {mp}")

    print(f"\n[SUCCESS] smoke push 完成: {repo_url} [{args.branch}]")
    sys.exit(0)


if __name__ == "__main__":
    main()
