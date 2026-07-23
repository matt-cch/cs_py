#!/usr/bin/env python3
r"""
py-tools/atomic-git-repo-clone.py — 本地仓库 clone 与身份配置原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-07-21

【意图】
polyrepo 初始化时，远程仓库创建后需要自动 clone 到本地指定目录，并配置
local git identity（user.name / user.email）。避免手敲 `git clone` 和
`git config` 命令，统一通过隔离 git.exe 完成，确保环境隔离、可复现。
源于 env-migration 中 jywl-settlement 仓库初始化的实践：手动 clone 易
遗漏 git config，导致后续 commit 身份混乱。

【职责】
  1. 使用隔离 git.exe clone 远程仓库到指定目录
  2. 设置 local git config（user.name / user.email）
  3. 验证 remote / branch / git status
  4. 生成 manifest 落盘到 venv/tmp/ 供追踪审计

【依赖】
底层能力（py-plugins/）：
  - process_runner（执行 git clone / config 等命令，含超时与流式输出）
  - env_config（读取 .env 获取 GITHUB_USERNAME / GIT_USER_EMAIL 默认值）
外部工具：
  - ${devroot}/venv/git/cmd/git.exe
环境变量：
  - GITHUB_USERNAME（devroot/.env，--git-user-name 的默认值）
  - GIT_USER_EMAIL（devroot/.env，--git-user-email 的默认值）

【预检】
执行本脚本前必须满足的前置条件：
  - 文件存在性: devroot/.env 存在（用于读取默认 identity）
  - 外部工具: ${devroot}/venv/git/cmd/git.exe 可执行
  - 目录状态: --target-dir 不存在，或已存在且包含 .git/
  - 网络可达: repo-url 可访问

【调用参数】
  --devroot         <str, 必填>                工具链根目录绝对路径
  --repo-url        <str, 必填>                远程仓库 URL
  --target-dir      <str, 必填>                本地 clone 目标目录绝对路径
  --git-user-name   <str, 可选>                git config user.name（默认从 .env GITHUB_USERNAME）
  --git-user-email  <str, 可选>                git config user.email（默认从 .env GIT_USER_EMAIL）
  --branch          <str, 可选, 默认=main>      默认分支名
  --output          <str, 可选>                产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-git-repo-clone-manifest-{timestamp}.json）

【用法示例】
    # 单仓库 clone（identity 从 .env 读取）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-repo-clone.py" `
        --devroot "${devroot}" `
        --repo-url "https://github.com/matt-cch/jywl-settlement" `
        --target-dir "${devroot}\apps\repos\matt-cch\jywl-settlement"

    # Polyrepo clone（显式指定 identity）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-repo-clone.py" `
        --devroot "${devroot}" `
        --repo-url "https://github.com/matt-cch/jywl-settlement" `
        --target-dir "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --git-user-name "matt-cch" `
        --git-user-email "chorefie@139.com"

【返回】
    exit 0 = 成功（或目标目录已存在且含 .git/）
    exit 1 = 失败（clone 失败、目录冲突、config 失败等）

【审计产物】
    ${devroot}/venv/tmp/repo-clone-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-git-repo-clone",
        "version": "1.0.0",
        "devroot": "...",
        "repo_url": "https://github.com/...",
        "target_dir": "...",
        "git_user_name": "...",
        "git_user_email": "...",
        "git_exe": "...",
        "cloned": true|false,
        "default_branch": "main",
        "exit_code": 0|1,
        "exit_at": "...",
        "errors": []
      }

【关联】
    - workflow: 被 polyrepo 初始化 workflow 在创建远程仓库后调用
    - env-migration: references/env-migrations/env-migration-jywl-settlement-polyrepo-init-2026-07-21-173210.md
    - 上游依赖: atomic-gh-repo-create.py（先生成远程仓库，再由本脚本 clone）
    - 下游消费: atomic-git-push-smoke.py（clone 后执行 smoke push）
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
# 脱敏工具（内联）
# =============================================================================
def _mask_pat(text: str) -> str:
    """将 URL 中的 PAT 替换为 ***。"""
    if not text:
        return text
    text = re.sub(r"(https?://[^:]+:)([^@]+)(@github\.com)", r"\1***\3", text)
    return text


def _print_cmd(cmd: list) -> None:
    """打印命令，自动脱敏。"""
    print(f"[EXEC] {_mask_pat(' '.join(cmd))}")


# =============================================================================
# Manifest 生成（内联）
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str = None) -> Path:
    """保存 manifest 到 venv/tmp/，供追踪审计。"""
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"repo-clone-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="本地 clone 仓库并配置 git identity")
    parser.add_argument("--devroot", required=True, help="工具链根目录绝对路径")
    parser.add_argument("--repo-url", required=True, help="远程仓库 URL")
    parser.add_argument("--target-dir", required=True, help="本地 clone 目标目录绝对路径")
    parser.add_argument("--git-user-name", default=None, help="git config user.name（默认从 .env GITHUB_USERNAME）")
    parser.add_argument("--git-user-email", default=None, help="git config user.email（默认从 .env GIT_USER_EMAIL）")
    parser.add_argument("--branch", default="main", help="默认分支名（默认 main）")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/repo-clone-manifest-{timestamp}.json）")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}", file=sys.stderr)
        sys.exit(1)

    repo_url = args.repo_url.strip()
    target_dir = Path(args.target_dir)

    # 导入 process_runner
    try:
        import process_runner
    except ImportError as e:
        print(f"[ERROR] 无法导入 process_runner: {e}", file=sys.stderr)
        print(f"[HINT] 请确认 py-plugins 目录存在: {_PY_PLUGINS_DIR}", file=sys.stderr)
        sys.exit(1)

    # 导入 env_config 读取默认值
    try:
        import env_config
    except ImportError:
        env_config = None

    # 从 .env 读取默认值
    git_user_name = args.git_user_name
    git_user_email = args.git_user_email
    if env_config:
        env_data = env_config.read_env(str(devroot / ".env"))
        if not git_user_name:
            git_user_name = env_data.get("GITHUB_USERNAME", "").strip()
        if not git_user_email:
            git_user_email = env_data.get("GIT_USER_EMAIL", "").strip()

    if not git_user_name:
        print(f"[ERROR] 未提供 --git-user-name，且 .env 中无 GITHUB_USERNAME", file=sys.stderr)
        sys.exit(1)

    # git.exe 绝对路径
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        print(f"[ERROR] git.exe 不存在: {git_exe}", file=sys.stderr)
        sys.exit(1)

    # Manifest 数据收集
    manifest = {
        "atomic_tool": "atomic-git-repo-clone",
        "version": "1.0.0",
        "devroot": str(devroot),
        "repo_url": repo_url,
        "target_dir": str(target_dir),
        "git_user_name": git_user_name,
        "git_user_email": git_user_email,
        "git_exe": str(git_exe),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "cloned": False,
        "default_branch": None,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    # Step 1: 检查目标目录
    print("\n" + "=" * 50)
    print("[Step 1] 检查目标目录")
    print("=" * 50)
    if target_dir.exists():
        if (target_dir / ".git").exists():
            print(f"[WARN] 目标目录已存在且包含 .git/，跳过 clone")
            print(f"[INFO] 现有仓库: {target_dir}")
            manifest["cloned"] = False
            manifest["skipped_reason"] = "target_dir already exists with .git"
        else:
            print(f"[ERROR] 目标目录已存在但不含 .git/: {target_dir}", file=sys.stderr)
            print(f"[HINT] 请删除或更换 --target-dir", file=sys.stderr)
            manifest["errors"].append("target_dir exists but no .git/")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
    else:
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        print(f"[OK] 父目录就绪: {target_dir.parent}")

    # Step 2: git clone
    if not (target_dir / ".git").exists():
        print("\n" + "=" * 50)
        print("[Step 2] git clone")
        print("=" * 50)
        print(f"[INFO] 远程: {repo_url}")
        print(f"[INFO] 本地: {target_dir}")

        cmd = [str(git_exe), "clone", repo_url, str(target_dir)]
        _print_cmd(cmd)
        sys.stdout.flush()

        try:
            process_runner.run_streaming(cmd, label="git clone", timeout=120)
            manifest["cloned"] = True
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] git clone 失败: {e}")
            manifest["errors"].append(f"git clone failed: {e}")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print(f"[FAIL] git clone 超时")
            manifest["errors"].append("git clone timeout")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
    else:
        print(f"[SKIP] clone 步骤（目录已存在）")

    # Step 3: 设置 local git config
    print("\n" + "=" * 50)
    print("[Step 3] 设置 local git config")
    print("=" * 50)

    configs = [
        ("user.name", git_user_name),
        ("user.email", git_user_email),
    ]
    for key, value in configs:
        if not value:
            print(f"[SKIP] git config {key}（未提供值）")
            continue
        cmd = [str(git_exe), "-C", str(target_dir), "config", "--local", key, value]
        _print_cmd(cmd)
        sys.stdout.flush()
        try:
            process_runner.run_streaming(cmd, label=f"git config {key}", timeout=30)
        except Exception as e:
            print(f"[WARN] git config {key} 失败: {e}")
            manifest["errors"].append(f"git config {key} failed: {e}")

    # Step 4: 验证
    print("\n" + "=" * 50)
    print("[Step 4] 验证仓库状态")
    print("=" * 50)

    # 4.1 remote
    cmd = [str(git_exe), "-C", str(target_dir), "remote", "-v"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        print("[OK] git remote:")
        for line in result.stdout.strip().splitlines():
            print(f"  {_mask_pat(line)}")
    else:
        print(f"[FAIL] git remote 失败: {result.stderr.strip()}")
        manifest["errors"].append("git remote failed")

    # 4.2 branch
    cmd = [str(git_exe), "-C", str(target_dir), "branch", "--show-current"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        branch = result.stdout.strip()
        print(f"[OK] 当前分支: {branch}")
        manifest["default_branch"] = branch
    else:
        print(f"[WARN] 无法获取当前分支")

    # 4.3 log
    cmd = [str(git_exe), "-C", str(target_dir), "log", "--oneline", "-3"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0 and result.stdout.strip():
        print("[OK] 最近提交:")
        for line in result.stdout.strip().splitlines():
            print(f"  {line}")
    else:
        print(f"[INFO] 无提交记录（空仓库或初始化中）")

    # 4.4 status
    cmd = [str(git_exe), "-C", str(target_dir), "status", "--short"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode == 0:
        if result.stdout.strip():
            print(f"[INFO] 工作区状态:")
            for line in result.stdout.strip().splitlines():
                print(f"  {line}")
        else:
            print(f"[OK] 工作区干净")

    # 成功收尾
    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest)
    print(f"[Manifest] 已落盘: {mp}")

    print(f"\n[SUCCESS] 本地仓库就绪: {target_dir}")
    sys.exit(0)


if __name__ == "__main__":
    main()
