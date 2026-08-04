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
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins
from git_url_utils import canonicalize_url


def _print_banner(title: str, width: int = 50):
    print(f"\n{'='*width}")
    print(f"[Deploy Preflight] {title}")
    print(f"{'='*width}")



def _save_manifest(devroot: Path, data: dict, output_path: str = None) -> Path:
    """保存 manifest 到 venv/tmp/ 或指定路径，供追踪审计。"""
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"deploy-preflight-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="部署特有前置验证")
    parser.add_argument("--devroot", default=None, help="工具链根路径（默认使用当前工作目录）")
    parser.add_argument("--target", required=True, help="操作目标仓库路径（polyrepo 调用契约要求，必须显式传入，即使与 --devroot 相同）")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/deploy-preflight-manifest-{timestamp}.json）")
    args = parser.parse_args()

    devroot = Path(args.devroot) if args.devroot else Path.cwd()
    target = Path(args.target)
    started_at = datetime.now(timezone.utc).isoformat()

    manifest = {
        "atomic_tool": "atomic-deploy-preflight",
        "version": "1.1.0",
        "devroot": str(devroot),
        "target": str(target),
        "repo_url_audit": {},
        "git_security": {},
        "current_branch": "",
        "working_tree": "",
        "exit_code": None,
        "started_at": started_at,
        "exit_at": None,
    }

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

    pat = env.get("GITHUB_PAT", "").strip()

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

    # 3. 解析 repo_url（本地状态 + 预期声明 + 远程真源 三方验证）
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    security_url = sec_cfg.get("repo_url", "").strip()
    local_remote_url = ""
    if git_exe.exists():
        result = subprocess.run(
            [str(git_exe), "-C", str(target), "remote", "get-url", "origin"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode == 0 and result.stdout.strip():
            local_remote_url = result.stdout.strip()

    # 从 security_url 提取 owner/repo，用于调用 GitHub API
    import re
    match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", security_url)
    github_clone_url = ""
    github_html_url = ""
    audit_method = "local_only"
    if match and pat:
        owner, repo_name = match.group(1), match.group(2)
        try:
            registry_api = load_plugins(devroot=str(devroot), tags=["github", "api"])
            gh_data = registry_api.github_api.fetch_repo_metadata(owner, repo_name, pat)
            github_clone_url = gh_data.get("clone_url", "")
            github_html_url = gh_data.get("html_url", "")
            audit_method = "github_api.fetch_repo_metadata"
            print(f"[OK] GitHub 远程真源获取成功: {github_html_url}")
        except Exception as e:
            print(f"[WARN] GitHub API 真源获取失败（将降级到本地规范化比对）: {e}")
    else:
        print("[WARN] 无法提取 owner/repo 或无 PAT，跳过 GitHub 远程真源验证")

    # 规范化后三方比对
    canonical_security = canonicalize_url(security_url)
    canonical_local = canonicalize_url(local_remote_url)
    canonical_github = canonicalize_url(github_clone_url) if github_clone_url else ""

    manifest["repo_url_audit"] = {
        "security_url": security_url,
        "local_remote_url": local_remote_url,
        "github_clone_url": github_clone_url,
        "github_html_url": github_html_url,
        "canonical_security": canonical_security,
        "canonical_local": canonical_local,
        "canonical_github": canonical_github,
        "method": audit_method,
    }

    repo_url = ""
    if security_url and local_remote_url:
        if canonical_security == canonical_local:
            if canonical_github and canonical_security == canonical_github:
                audit_result = "pass"
                print(f"[OK] repo_url 审计通过: git-remote、git-security、GitHub 真源三方一致 ({security_url})")
            elif canonical_github:
                audit_result = "pass_with_warning"
                print(f"[WARN] repo_url 规范化比对通过，但 GitHub 真源存在差异")
                print(f"  git-security: {security_url}")
                print(f"  git-remote: {local_remote_url}")
                print(f"  GitHub clone_url: {github_clone_url}")
            else:
                audit_result = "pass"
                print(f"[OK] repo_url 审计通过: git-remote 与 git-security 一致 ({security_url})")
        else:
            audit_result = "fail"
            print("[FAIL] repo_url 审计失败: git-remote 与 git-security 不匹配")
            print(f"  git-remote: {local_remote_url}")
            print(f"  git-security: {security_url}")
            print(f"  canonical_local: {canonical_local}")
            print(f"  canonical_security: {canonical_security}")
            print("[HINT] 请检查是否操作了错误仓库，或更新 git-security.json")
            manifest["repo_url_audit"]["audit_result"] = audit_result
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
    elif security_url:
        repo_url = security_url
        audit_result = "pass_from_security"
        print(f"[OK] repo_url 来自 git-security（origin 未设置）: {repo_url}")
        print("[HINT] 建议执行: git remote add origin <url>")
    elif local_remote_url:
        repo_url = local_remote_url
        audit_result = "pass_from_remote"
        print(f"[OK] repo_url 来自 git-remote: {repo_url}")
    else:
        repo_url = env.get("GITHUB_REPO_URL", "").strip()
        if repo_url:
            audit_result = "pass_from_env"
            print(f"[WARN] repo_url 来自 .env（已淘汰）: {repo_url}")
        else:
            audit_result = "fail"
            print("[FAIL] 无法确定 repo_url（git-remote 无 origin、git-security 无配置、.env 无 GITHUB_REPO_URL）")
            manifest["repo_url_audit"]["audit_result"] = audit_result
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)

    manifest["repo_url_audit"]["audit_result"] = audit_result

    if not pat or pat == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("[FAIL] .env 中 GITHUB_PAT 未配置或仍是占位符")
        sys.exit(1)
    print("[OK] .env 部署配置完整")

    # 4. 分支保护检测（从 git-security.json 读取策略，不再硬编码 master）
    default_branch = sec_cfg.get("default_branch", "main").strip()
    allow_direct_push = sec_cfg.get("allow_direct_push_to", [])
    security_level = sec_cfg.get("security_level", "normal").strip()
    current_branch = ""
    working_tree = ""

    if git_exe.exists():
        # 当前分支
        result = subprocess.run(
            [str(git_exe), "-C", str(target), "branch", "--show-current"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        current_branch = result.stdout.strip()

        # 工作区状态
        r_status = subprocess.run(
            [str(git_exe), "-C", str(target), "status", "--porcelain"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        working_tree = "clean" if (r_status.returncode == 0 and not r_status.stdout.strip()) else "dirty"

        manifest["git_security"] = {
            "default_branch": default_branch,
            "security_level": security_level,
            "allow_direct_push_to": allow_direct_push,
        }
        manifest["current_branch"] = current_branch
        manifest["working_tree"] = working_tree

        if current_branch in allow_direct_push:
            print(f"[OK] 当前分支 '{current_branch}' 在 allow_direct_push_to 白名单中，允许直接 push")
        elif current_branch == default_branch and not allow_direct_push:
            print(f"[WARN] 当前在默认分支 '{current_branch}'，且 allow_direct_push_to 为空")
            print("[WARN] 直接 push 将被拒绝，请使用 feature 分支 + PR merge 流程")
            print("[FAIL] Preflight 终止")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
        elif current_branch == default_branch and allow_direct_push and current_branch not in allow_direct_push:
            print(f"[WARN] 当前在默认分支 '{current_branch}'，但不在 allow_direct_push_to 白名单中")
            print("[WARN] 直接 push 将被拒绝，请使用 feature 分支 + PR merge 流程")
            print("[FAIL] Preflight 终止")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
        else:
            print(f"[OK] 当前分支: {current_branch}（默认分支: {default_branch}, 安全级别: {security_level}）")

    # 5. 验证 agent 插件体系（AI 摘要需要）
    try:
        registry = load_plugins(devroot=str(devroot), profile="agent")
        _ = registry.agent_core
        provider_cfg = registry.provider_config.get_provider(source="config_json")
        model = provider_cfg.get("model", "(未知)")
        api_key = provider_cfg.get("api_key", "")
        if not api_key:
            print("[FAIL] config.json 中未配置 api_key，Agent 摘要功能不可用")
            manifest["exit_code"] = 1
            manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
            mp = _save_manifest(devroot, manifest, args.output)
            print(f"[Manifest] 已落盘: {mp}")
            sys.exit(1)
        print(f"[OK] agent 插件体系加载成功，model={model}")
    except Exception as e:
        print(f"[FAIL] agent 插件验证失败: {e}")
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 6. Git 空目录保留（在 target 仓库执行）
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

    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest, args.output)
    print(f"[Manifest] 已落盘: {mp}")
    print("[Deploy Preflight] 全部通过，开始执行部署\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
