#!/usr/bin/env python3
r"""
atomic-deploy-preflight.py — 部署特有前置验证原子工具
标签：py-tools

职责：在 workflow-deploy-full 中，通用 git preflight 之后执行。
      验证部署特有的前置条件：PAT、分支保护、agent 插件、空目录保留。
      任何失败直接 exit，不执行后续部署步骤。

用法：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-deploy-preflight.py" [--devroot "<目标仓库绝对路径>"]

返回：
    exit 0 = 验证通过
    exit 1 = 验证失败
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


def _print_banner(title: str, width: int = 50):
    print(f"\n{'='*width}")
    print(f"[Deploy Preflight] {title}")
    print(f"{'='*width}")


def main():
    parser = argparse.ArgumentParser(description="部署特有前置验证")
    parser.add_argument("--devroot", default=None, help="Devroot 路径（默认使用当前工作目录）")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()

    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
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

    # 2. 检查必填项
    pat = env.get("GITHUB_PAT", "").strip()
    repo_url = env.get("GITHUB_REPO_URL", "").strip()

    if not repo_url:
        print("[FAIL] .env 中 GITHUB_REPO_URL 未配置")
        sys.exit(1)
    if not pat or pat == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("[FAIL] .env 中 GITHUB_PAT 未配置或仍是占位符")
        sys.exit(1)
    print("[OK] .env 部署配置完整")

    # 3. 分支保护检测
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if git_exe.exists():
        result = subprocess.run(
            [str(git_exe), "-C", str(devroot), "branch", "--show-current"],
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

    # 5. Git 空目录保留
    try:
        registry_git = load_plugins(devroot=str(devroot), tags=["git"])
        keep_result = registry_git.git_keep_emptydir.ensure_empty_dirs(
            devroot,
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
