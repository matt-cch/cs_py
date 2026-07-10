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

    # 2. 解析 repo_url（仅从 target 的 git remote 读取，不 fallback 到 .env）
    repo_url = ""
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if git_exe.exists():
        result = subprocess.run(
            [str(git_exe), "-C", str(target), "remote", "get-url", "origin"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode == 0 and result.stdout.strip():
            repo_url = result.stdout.strip()

    if not repo_url:
        print("[FAIL] target 仓库无 origin remote，无法确定 repo_url")
        print("[HINT] 请在 target 仓库执行: git remote add origin <url>")
        sys.exit(1)
    print(f"[OK] repo_url (来自 target git remote): {repo_url}")

    # 2b. 审计比对：实测 repo_url vs git-security.json 预置值
    security_json = target / "git-security.json"
    if security_json.exists():
        try:
            sec_cfg = json.loads(security_json.read_text(encoding="utf-8"))
            expected_url = sec_cfg.get("repo_url", "").strip()
            if expected_url:
                if repo_url == expected_url:
                    print(f"[OK] git-security.json 审计通过: repo_url 与预置值一致")
                else:
                    print(f"[FAIL] git-security.json 审计失败: repo_url 不匹配")
                    print(f"  实测值: {repo_url}")
                    print(f"  预置值: {expected_url}")
                    print(f"[HINT] 请检查是否操作了错误的仓库，或更新 git-security.json")
                    sys.exit(1)
            else:
                print(f"[WARN] git-security.json 中未配置 repo_url，跳过审计比对")
        except Exception as e:
            print(f"[WARN] git-security.json 解析失败: {e}，跳过审计比对")
    else:
        print(f"[WARN] target 下无 git-security.json，跳过 repo_url 审计比对")

    pat = env.get("GITHUB_PAT", "").strip()
    if not pat or pat == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("[FAIL] .env 中 GITHUB_PAT 未配置或仍是占位符")
        sys.exit(1)
    print("[OK] .env 部署配置完整")

    # 3. 分支保护检测（在 target 仓库执行）
    if git_exe.exists():
        result = subprocess.run(
            [str(git_exe), "-C", str(target), "branch", "--show-current"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        current_branch = result.stdout.strip()
        if current_branch == "master":
            print("[WARN] 当前在 master 分支，直接 push 将被分支保护规则拒绝")
            print("[WARN] 建议：git checkout -b feat/xxx 后重新执行 workflow")
            print("[FAIL] Preflight 终止")
            sys.exit(1)
        else:
            print(f"[OK] 当前分支: {current_branch}（非受保护分支）")

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
