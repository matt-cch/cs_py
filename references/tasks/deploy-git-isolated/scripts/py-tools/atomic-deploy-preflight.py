#!/usr/bin/env python3
r"""
atomic-deploy-preflight.py — 部署特有前置验证原子工具
标签：py-tools

职责：在 workflow-deploy-full 中，通用 git preflight 之后执行。
      验证部署特有的前置条件：PAT、分支保护、agent 插件、空目录保留。
      任何失败直接 exit，不执行后续部署步骤。

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-deploy-preflight.py" [--devroot "<工具链根绝对路径>"] [--target "<操作目标仓库绝对路径>"]

返回：
    exit 0 = 验证通过
    exit 1 = 验证失败
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def _print_banner(title: str, width: int = 50):
    print(f"\n{'='*width}")
    print(f"[Deploy Preflight] {title}")
    print(f"{'='*width}")


def main():
    parser = argparse.ArgumentParser(description="部署特有前置验证")
    parser.add_argument("--devroot", default=None, help="工具链根路径（默认使用当前工作目录）")
    parser.add_argument("--target", required=True, help="操作目标仓库路径（polyrepo 调用契约要求，必须显式传入，即使与 --devroot 相同）")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()
    target = Path(args.target)

    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)
    if not target.exists():
        print(f"[ERROR] target 不存在: {target}")
        sys.exit(1)

    _print_banner("部署前置验证")

    # 1. 读取 .env
    env_path = devroot / ".env"
    if not env_path.exists():
        print("[FAIL] .env 文件不存在")
        sys.exit(1)

    env = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env[key] = val

    # 2. 读取 git-security.json（Repo 身份卡）
    sec_cfg = {}
    security_json = target / "git-security.json"
    if security_json.exists():
        try:
            sec_cfg = json.loads(security_json.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[WARN] git-security.json 解析失败: {e}")
    else:
        print("[WARN] target 下无 git-security.json")

    # 3. 解析 repo_url（基准 vs 实测对碰）
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    security_url = sec_cfg.get("repo_url", "").strip()
    remote_url = ""
    if git_exe.exists():
        result = subprocess.run(
            [str(git_exe), "-C", str(target), "remote", "get-url", "origin"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode == 0 and result.stdout.strip():
            remote_url = result.stdout.strip()

    # 对碰
    repo_url = ""
    if security_url and remote_url:
        if security_url == remote_url:
            repo_url = remote_url
            print(f"[OK] repo_url 审计通过: git-remote 与 git-security 一致 ({repo_url})")
        else:
            print("[FAIL] repo_url 审计失败: git-remote 与 git-security 不匹配")
            print(f"  git-remote: {remote_url}")
            print(f"  git-security: {security_url}")
            print("[HINT] 请检查是否操作了错误仓库，或更新 git-security.json")
            sys.exit(1)
    elif security_url:
        repo_url = security_url
        print(f"[OK] repo_url 来自 git-security（origin 未设置）: {repo_url}")
        print("[HINT] 建议执行: git remote add origin <url>")
    elif remote_url:
        repo_url = remote_url
        print(f"[OK] repo_url 来自 git-remote: {repo_url}")
    else:
        # fallback 到 .env（已淘汰的 anti-pattern）
        repo_url = env.get("GITHUB_REPO_URL", "").strip()
        if repo_url:
            print(f"[WARN] repo_url 来自 .env（已淘汰）: {repo_url}")
        else:
            print("[FAIL] 无法确定 repo_url（git-remote 无 origin、git-security 无配置、.env 无 GITHUB_REPO_URL）")
            sys.exit(1)

    pat = env.get("GITHUB_PAT", "").strip()
    if not pat or pat == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("[FAIL] .env 中 GITHUB_PAT 未配置或仍是占位符")
        sys.exit(1)
    print("[OK] .env 部署配置完整")

    # 4. 分支保护检测（从 git-security.json 读取策略，不再硬编码 master）
    default_branch = sec_cfg.get("default_branch", "main").strip()
    allow_direct_push = sec_cfg.get("allow_direct_push_to", [])
    security_level = sec_cfg.get("security_level", "normal").strip()

    if git_exe.exists():
        result = subprocess.run(
            [str(git_exe), "-C", str(target), "branch", "--show-current"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        current_branch = result.stdout.strip()

        if current_branch in allow_direct_push:
            print(f"[OK] 当前分支 '{current_branch}' 在 allow_direct_push_to 白名单中，允许直接 push")
        elif current_branch == default_branch and not allow_direct_push:
            print(f"[WARN] 当前在默认分支 '{current_branch}'，且 allow_direct_push_to 为空")
            print("[WARN] 直接 push 将被拒绝，请使用 feature 分支 + PR merge 流程")
            print("[FAIL] Preflight 终止")
            sys.exit(1)
        elif current_branch == default_branch and allow_direct_push and current_branch not in allow_direct_push:
            print(f"[WARN] 当前在默认分支 '{current_branch}'，但不在 allow_direct_push_to 白名单中")
            print("[WARN] 直接 push 将被拒绝，请使用 feature 分支 + PR merge 流程")
            print("[FAIL] Preflight 终止")
            sys.exit(1)
        else:
            print(f"[OK] 当前分支: {current_branch}（默认分支: {default_branch}, 安全级别: {security_level}）")

    # 4. 验证 agent 插件体系（AI 摘要需要）
    try:
        registry = load_plugins(devroot=str(devroot), profile="agent")
        _ = registry.agent_core
        provider_cfg = registry.provider_config.get_provider(source="config_json")
        model = provider_cfg.get("model", "(未知)")
        api_key = provider_cfg.get("api_key", "")
        if not api_key:
            print("[FAIL] config.json 中未配置 api_key，Agent 摘要功能不可用")
            sys.exit(1)
        print(f"[OK] agent 插件体系加载成功，model={model}")
    except Exception as e:
        print(f"[FAIL] agent 插件验证失败: {e}")
        sys.exit(1)

    # 5. Git 空目录保留（在 target 仓库执行）
    try:
        registry_git = load_plugins(devroot=str(devroot), tags=["git"])
        keep_result = registry_git.git_keep_emptydir.ensure_empty_dirs(
            target,
            ["references/env-migrations", "references/tasks/deploy-git-isolated"]
        )
        if keep_result.get("created"):
            print(f"[OK] 已创建 {len(keep_result['created'])} 个 .gitkeep")
        else:
            print("[OK] 无空目录需要处理")
    except Exception as e:
        print(f"[WARN] git_keep_emptydir 执行异常: {e}")

    print("[Deploy Preflight] 全部通过，开始执行部署\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
