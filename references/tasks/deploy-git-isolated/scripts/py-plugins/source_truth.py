#!/usr/bin/env python3
r"""
插件：仓库真源验证（Source Truth Verification）
标签：github, git, source-truth, polyrepo
依赖：gh_preflight, git_url_utils

职责：在 polyrepo 场景下，从用户意图层出发，建立本地 worktree 与远程 GitHub 仓库
      之间的物理不可伪造绑定。输出经过验证的 owner_repo 和完整的审计记录，
      供下游 atomic 脚本作为唯一真源引用。

【真源推理链：L1-L5】
  L1 本地实测推断层：从 devroot + target 的物理状态（.git/ 数据库）推断仓库身份
  L2 用户声明审计层：读取 target/git-security.json（用户意图真源起点）
  L3 交叉验证层：L1 实测推断 vs L2 用户声明 vs .git/config 佐证对碰
  L4 远程物理绑定层：本地 HEAD commit SHA 必须存在于远程仓库（核心防线）
  L5 远程对象绑定层：分支 ↔ PR / Issue 的物理对应验证

【与 gh_preflight 的职责边界】
  - gh_preflight：只验证 gh CLI 工具链可用性（gh.exe、PAT、认证状态）
  - source_truth：在 gh_preflight 通过的基础上，执行 L1-L5 真源推理链
  - gh_preflight 不解析 owner_repo；source_truth 从 git-security.json 读取并验证

【owner_repo 来源优先级】
  1. git-security.json 中的 owner_repo（用户意图层，优先）
  2. 本地 .git/config 推断的 owner_repo（降级，标记 warning）
  3. 两者冲突时：以 git-security.json 为准，记录冲突到 manifest

【URL 规范：.git 后缀一致性】
  1. git-security.json 中的 repo_url 必须带 .git 后缀
     例: "https://github.com/owner/repo.git"
     这是 GitHub 官方 clone URL 的标准格式，也是 gh API 返回 clone_url 的格式。
  2. .git/config 中的 remote URL 可能不带 .git（历史遗留 create/clone 操作不规范）
     该值仅作为 L3 交叉验证的佐证，不参与硬逻辑链。
  3. 后续 gh repo create / gh repo clone 等操作必须设置带 .git 的 remote URL
  4. manifest 中原始记录（raw）保留 .git，规范化比对（canonical）才去 .git

【URL 规范化规范（仅用于比对）】
  所有 repo URL 的比较统一使用 git_url_utils.canonicalize_url：
    - 去除尾部空白和尾部斜杠
    - 去除尾部 .git（不区分大小写）
    - 统一转为小写
  manifest 中同时记录原始 URL（raw）和规范化 URL（canonical）。
  注意：canonicalize_url 只用于比对，不用于原始记录。

【默认分支规范】
  - git-security.json 中的 default_branch 优先
  - 缺失时回退到 "main"
  - 历史遗留仓库（如 cs_py 的 master）通过 git-security.json 显式声明

【调用方式】
    import sys
    sys.path.insert(0, r"...\scripts\py-plugins")
    from source_truth import verify, SourceTruthContext

    gh_ctx = gh_preflight.verify(devroot, target)
    stx = verify(devroot, target, gh_ctx)
    if not stx.ok:
        print(stx.errors)
    print(stx.owner_repo)  # 下游唯一真源引用

【返回 SourceTruthContext 关键字段】
    - ok: bool                      全部验证是否通过
    - owner_repo: str               经过验证的 owner/repo（下游唯一真源引用）
    - owner_repo_source: str        来源标记（git-security.json / local_inference）
    - owner_repo_source_path: Path  git-security.json 的完整绝对路径
    - local_head_sha: str           本地 HEAD commit SHA
    - remote_head_sha: str          远程 origin/current_branch HEAD SHA
    - current_branch: str           当前分支名
    - physical_binding_verified: bool   L4 物理绑定验证结果
    - pr_number: int                关联的 PR 编号（L5 验证后）
    - pr_binding_verified: bool     PR head SHA 与本地 HEAD 是否一致
    - manifest_data: dict           完整的 L1-L5 记录，可直接落盘
"""
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# =============================================================================
# 导入共享 URL 规范化工具（假设与当前文件同目录）
# =============================================================================
_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    from git_url_utils import canonicalize_url
except ImportError:
    # 降级：内联 canonicalize_url，避免循环依赖
    def canonicalize_url(url: str) -> str:
        if not url:
            return ""
        url = url.strip().rstrip("/")
        if url.lower().endswith(".git"):
            url = url[:-4]
        return url.lower()


__plugin_registry__ = None  # 由 py_lib.py 注入


# =============================================================================
# SourceTruthContext：真源验证结果上下文
# =============================================================================
@dataclass
class SourceTruthContext:
    """真源验证结果，包含 L1-L5 全部层的输出，供下游脚本和 manifest 消费。"""

    ok: bool = False
    owner_repo: str = ""
    owner_repo_source: str = ""           # "git-security.json" / "local_inference" / "user_override"
    owner_repo_source_path: Path = None   # git-security.json 的完整绝对路径

    local_head_sha: str = ""
    local_head_sha_source: str = ""       # 获取命令的完整描述

    remote_head_sha: str = ""
    remote_head_sha_source: str = ""      # 获取命令的完整描述

    current_branch: str = ""
    current_branch_source: str = ""       # 获取命令的完整描述

    latest_commit_message: str = ""
    latest_commit_message_source: str = ""

    declared_owner_repo: str = ""
    declared_remote_url: str = ""
    declared_remote_url_raw: str = ""
    declared_remote_url_canonical: str = ""
    declared_default_branch: str = ""
    declared_linked_issues: list = field(default_factory=list)
    declared_source_path: Path = None     # git-security.json 完整绝对路径

    remote_url_from_config: str = ""
    remote_url_from_config_raw: str = ""
    remote_url_from_config_canonical: str = ""
    remote_url_from_config_source: str = ""  # 获取命令的完整描述

    inferred_owner_repo: str = ""         # 从 .git/config 推断的 owner_repo
    inferred_owner_repo_source: str = ""

    physical_binding_verified: bool = False
    physical_binding_status: str = ""     # "verified" / "skipped_no_commits" / "broken"
    physical_binding_method: str = ""     # "gh_api_commit_existence"

    state_aligned: bool = False
    state_alignment_status: str = ""      # "aligned" / "diverged" / "no_remote_ref"

    pr_found: bool = False
    pr_number: int = None
    pr_state: str = ""               # "OPEN" / "MERGED" / "CLOSED"
    pr_head_sha: str = ""
    pr_base_branch: str = ""         # PR 合入目标分支（如 main）
    pr_merge_commit: str = ""        # merge 后在 main 上的 commit SHA
    pr_merged_at: str = ""           # merge 时间戳 ISO
    pr_commits_count: int = 0        # PR 包含 commit 数
    pr_url: str = ""                 # PR 永久链接
    pr_total_matched: int = 0        # --state all 返回的 PR 总数
    pr_binding_verified: bool = False
    pr_binding_status: str = ""       # "verified" / "head_mismatch" / "not_found" / "multiple_found"

    linked_issues_status: list = field(default_factory=list)

    conflicts: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    infos: list = field(default_factory=list)

    manifest_data: dict = field(default_factory=dict)


# =============================================================================
# 内部工具函数
# =============================================================================
def _parse_owner_repo(remote_url: str) -> str:
    """从 git remote URL 解析 owner/repo，使用 canonicalize_url 规范化后解析。"""
    url = canonicalize_url(remote_url)
    if not url:
        return ""
    # 去除协议前缀，只保留路径部分
    url = url.replace("https://", "").replace("http://", "")
    # 去除可能的 auth 部分（如 user:pass@host）
    if "@" in url:
        url = url.split("@", 1)[1]
    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return ""


def _run_git(git_exe: Path, args: list, cwd: Path) -> subprocess.CompletedProcess:
    """执行 git 命令，固定 UTF-8 编码。"""
    cmd = [str(git_exe)] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
    )


def _run_gh(gh_exe: Path, args: list, token: str, **kwargs) -> subprocess.CompletedProcess:
    """执行 gh CLI 命令，自动注入 GH_TOKEN。"""
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    cmd = [str(gh_exe)] + args
    return subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        **kwargs,
    )


# =============================================================================
# Layer 1: 本地实测推断层（从 .git/ 数据库读取物理状态）
# =============================================================================
def _layer1_infer_from_local_state(git_exe: Path, target: Path) -> dict:
    """
    从本地 git 仓库的物理状态推断身份。
    所有命令都在 target 目录下执行，读取 .git/ 数据库的实测信息。
    """
    result = {
        "is_git_repo": False,
        "git_dir_path": str(target / ".git"),
        "current_branch": "",
        "current_branch_source": "",
        "local_head_sha": "",
        "local_head_sha_source": "",
        "latest_commit_message": "",
        "latest_commit_message_source": "",
        "remote_url_from_config_raw": "",
        "remote_url_from_config_canonical": "",
        "remote_url_from_config_source": "",
        "inferred_owner_repo": "",
        "inferred_owner_repo_source": "",
        "errors": [],
    }

    # A. 确认是 git 仓库（检测 .git/ 存在性）
    git_dir = target / ".git"
    r = _run_git(git_exe, ["rev-parse", "--git-dir"], target)
    if r.returncode != 0:
        result["errors"].append(f"target 不是 git 仓库: {target}")
        return result
    result["is_git_repo"] = True
    result["git_dir_path"] = str(git_dir.resolve())

    # B. 当前分支（读取 .git/HEAD 或 .git/refs/heads/）
    r = _run_git(git_exe, ["branch", "--show-current"], target)
    result["current_branch"] = r.stdout.strip()
    result["current_branch_source"] = f"git branch --show-current @ {target}"

    # C. 本地 HEAD SHA（读取 .git/refs/heads/{branch}）
    r = _run_git(git_exe, ["rev-parse", "HEAD"], target)
    result["local_head_sha"] = r.stdout.strip()
    result["local_head_sha_source"] = f"git rev-parse HEAD @ {target}"

    # D. 最新 commit message（读取 .git/objects/ 中的 commit 对象）
    r = _run_git(git_exe, ["log", "--oneline", "-1"], target)
    result["latest_commit_message"] = r.stdout.strip()
    result["latest_commit_message_source"] = f"git log --oneline -1 @ {target}"

    # E. .git/config 中的 remote URL（读取 .git/config [remote \"origin\"]）
    r = _run_git(git_exe, ["remote", "get-url", "origin"], target)
    if r.returncode == 0 and r.stdout.strip():
        raw_url = r.stdout.strip()
        result["remote_url_from_config_raw"] = raw_url
        result["remote_url_from_config_canonical"] = canonicalize_url(raw_url)
        result["remote_url_from_config_source"] = f"git remote get-url origin @ {target}"
        # F. 推断 owner/repo
        result["inferred_owner_repo"] = _parse_owner_repo(raw_url)
        result["inferred_owner_repo_source"] = f"_parse_owner_repo({raw_url}) @ {target}"

    return result


# =============================================================================
# Layer 2: 用户声明审计层（读取 git-security.json）
# =============================================================================
def _layer2_read_user_declaration(target: Path) -> dict:
    """
    读取用户显式声明的 git-security.json。
    记录文件的完整绝对路径，作为审计基准点。
    """
    result = {
        "security_json_exists": False,
        "security_json_path": str(target / "git-security.json"),
        "declared_owner_repo": "",
        "declared_remote_url_raw": "",
        "declared_remote_url_canonical": "",
        "declared_default_branch": "",
        "declared_linked_issues": [],
        "self_consistent": False,
        "errors": [],
    }

    sec_path = target / "git-security.json"
    result["security_json_path"] = str(sec_path.resolve())

    if not sec_path.exists():
        result["errors"].append(f"git-security.json 不存在: {sec_path}")
        return result

    result["security_json_exists"] = True
    try:
        data = json.loads(sec_path.read_text(encoding="utf-8"))
    except Exception as e:
        result["errors"].append(f"git-security.json 解析失败: {e}")
        return result

    result["declared_owner_repo"] = data.get("owner_repo", "").strip()
    # 兼容现有 schema：优先 repo_url，fallback remote_url
    raw_url = data.get("repo_url", "").strip() or data.get("remote_url", "").strip()
    result["declared_remote_url_raw"] = raw_url
    result["declared_remote_url_canonical"] = canonicalize_url(raw_url)
    result["declared_default_branch"] = data.get("default_branch", "").strip()
    result["declared_linked_issues"] = data.get("linked_issues", [])

    # owner_repo 缺失时，从 repo_url 推断（兼容旧格式，记录降级）
    if not result["declared_owner_repo"] and raw_url:
        result["declared_owner_repo"] = _parse_owner_repo(raw_url)
        result["owner_repo_inferred_from_repo_url"] = True
    else:
        result["owner_repo_inferred_from_repo_url"] = False

    # 自洽性验证: declared_owner_repo 与 declared_remote_url 必须指向同一逻辑仓库
    inferred_from_remote = _parse_owner_repo(raw_url)
    if inferred_from_remote and inferred_from_remote != result["declared_owner_repo"]:
        result["errors"].append(
            f"git-security.json 不自洽: "
            f"owner_repo={result['declared_owner_repo']}, "
            f"但 remote_url 推断出 {inferred_from_remote}"
        )
    else:
        result["self_consistent"] = True

    return result


# =============================================================================
# Layer 3: 交叉验证层
# =============================================================================
def _layer3_cross_validate(layer1: dict, layer2: dict) -> dict:
    """
    交叉验证: L1 实测推断 vs L2 用户声明 vs .git/config 佐证。
    冲突时以用户声明为准，记录到 manifest。
    """
    result = {
        "passed": True,
        "owner_repo_source": "",
        "owner_repo_value": "",
        "owner_repo_source_path": layer2.get("security_json_path", ""),
        "conflicts": [],
        "warnings": [],
        "infos": [],
    }

    l1_owner = layer1.get("inferred_owner_repo", "")
    l2_owner = layer2.get("declared_owner_repo", "")
    l1_remote_raw = layer1.get("remote_url_from_config_raw", "")
    l2_remote_raw = layer2.get("declared_remote_url_raw", "")
    l1_remote_canon = layer1.get("remote_url_from_config_canonical", "")
    l2_remote_canon = layer2.get("declared_remote_url_canonical", "")

    # 3a. 实测推断 vs 用户声明（owner_repo）
    if l1_owner and l2_owner:
        if l1_owner == l2_owner:
            result["owner_repo_source"] = "git-security.json (confirmed by local inference)"
            result["owner_repo_value"] = l2_owner
            result["infos"].append("实测推断与用户声明一致")
        else:
            # 冲突！以用户声明为准（用户意图层优先）
            result["owner_repo_source"] = "git-security.json (OVERRIDE: conflicts with local inference)"
            result["owner_repo_value"] = l2_owner
            result["conflicts"].append({
                "type": "owner_repo_mismatch",
                "local_inference": l1_owner,
                "user_declaration": l2_owner,
                "resolution": "user_declaration_wins",
                "reason": "用户意图层优先于技术推断层",
            })
    elif l2_owner:
        result["owner_repo_source"] = "git-security.json (no local inference available)"
        result["owner_repo_value"] = l2_owner
        result["warnings"].append("无本地 .git/config 佐证，纯依赖用户声明")
    elif l1_owner:
        result["owner_repo_source"] = "local_inference (git-security.json missing)"
        result["owner_repo_value"] = l1_owner
        result["warnings"].append("git-security.json 缺失，降级到 .git/config 推断")
    else:
        result["passed"] = False
        result["conflicts"].append({
            "type": "no_owner_repo_available",
            "reason": "既无 git-security.json，也无法从 .git/config 推断",
        })
        return result

    # 3b. .git/config remote_url 与 declared_remote_url 规范化比对
    if l1_remote_canon and l2_remote_canon:
        if l1_remote_canon == l2_remote_canon:
            result["infos"].append(
                ".git/config remote_url 与 git-security.json 一致（佐证通过）"
            )
        else:
            result["conflicts"].append({
                "type": "remote_url_mismatch",
                "git_config_raw": l1_remote_raw,
                "git_config_canonical": l1_remote_canon,
                "git_security_raw": l2_remote_raw,
                "git_security_canonical": l2_remote_canon,
                "resolution": "git_security_wins",
                "reason": ".git/config 仅作佐证，用户声明优先",
            })

    return result


# =============================================================================
# Layer 4: 远程物理绑定层（本地代码 ↔ 远程仓库 的唯一不可伪造连接）
# =============================================================================
def _layer4_verify_physical_binding(
    gh_exe: Path,
    git_exe: Path,
    owner_repo: str,
    local_head_sha: str,
    current_branch: str,
    target: Path,
    token: str,
) -> dict:
    """
    L4 物理绑定验证：
    4a. 本地 HEAD commit SHA 必须存在于远程仓库
    4b. 本地分支 HEAD 与远程 origin/分支 HEAD 状态对齐
    """
    result = {
        "physical_binding_verified": False,
        "physical_binding_status": "",
        "physical_binding_method": "",
        "local_head_sha": local_head_sha,
        "local_head_sha_source": f"git rev-parse HEAD @ {target}",
        "remote_head_sha": "",
        "remote_head_sha_source": "",
        "state_aligned": False,
        "state_alignment_status": "",
        "errors": [],
    }

    # 无本地 commit 时降级
    if not local_head_sha:
        result["physical_binding_status"] = "skipped_no_commits"
        result["physical_binding_method"] = "none"
        result["state_alignment_status"] = "skipped_no_commits"
        result["errors"].append("本地仓库无 commit，无法执行 SHA 存在性验证")
        return result

    # 4a. commit SHA 存在于远程仓库（GitHub API）
    r = _run_gh(
        gh_exe,
        ["api", f"repos/{owner_repo}/commits/{local_head_sha}", "--jq", ".sha"],
        token,
    )

    if r.returncode == 0 and r.stdout.strip() == local_head_sha:
        result["physical_binding_verified"] = True
        result["physical_binding_status"] = "verified"
        result["physical_binding_method"] = "gh_api_commit_existence"
    else:
        result["physical_binding_status"] = "broken"
        result["physical_binding_method"] = "gh_api_commit_existence"
        result["errors"].append(
            f"物理绑定断裂: commit {local_head_sha} 不存在于远程仓库 {owner_repo}"
        )
        return result  # 物理绑定断裂，立即停止 L4

    # 4b. 状态对齐（git ls-remote）
    r = _run_git(git_exe, ["ls-remote", "--heads", "origin", current_branch], target)
    if r.returncode == 0 and r.stdout.strip():
        parts = r.stdout.strip().split()
        if len(parts) >= 1:
            result["remote_head_sha"] = parts[0]
            result["remote_head_sha_source"] = (
                f"git ls-remote --heads origin {current_branch} @ {target}"
            )
            result["state_aligned"] = (parts[0] == local_head_sha)
            result["state_alignment_status"] = (
                "aligned" if result["state_aligned"] else "diverged"
            )
            if not result["state_aligned"]:
                result["errors"].append(
                    f"状态未对齐: 本地 HEAD={local_head_sha}, "
                    f"远程 origin/{current_branch}={parts[0]}"
                )
    else:
        result["state_alignment_status"] = "no_remote_ref"
        result["errors"].append(
            f"远程无 {current_branch} 分支引用: {r.stderr.strip()}"
        )

    return result


# =============================================================================
# Layer 5: 远程对象绑定层（分支 ↔ PR / Issue 物理对应）
# =============================================================================
def _layer5_verify_remote_object_binding(
    gh_exe: Path,
    owner_repo: str,
    current_branch: str,
    local_head_sha: str,
    linked_issues: list,
    token: str,
) -> dict:
    """
    L5 远程对象绑定：
    5a. 找到当前分支对应的 open PR，验证 PR head SHA == 本地 HEAD SHA
    5b. 验证 linked_issues 的存在性
    """
    result = {
        "pr_found": False,
        "pr_number": None,
        "pr_state": "",
        "pr_head_sha": "",
        "pr_base_branch": "",
        "pr_merge_commit": "",
        "pr_merged_at": "",
        "pr_commits_count": 0,
        "pr_url": "",
        "pr_total_matched": 0,
        "pr_binding_verified": False,
        "pr_binding_status": "",
        "linked_issues_status": [],
        "info": "",
        "errors": [],
    }

    # 5a. 查找 PR（查全部状态，不只是 open）
    r = _run_gh(
        gh_exe,
        [
            "pr", "list",
            "--repo", owner_repo,
            "--head", current_branch,
            "--state", "all",
            "--json", "number,state,headRefOid,url,title",
        ],
        token,
    )

    if r.returncode != 0 or not r.stdout.strip():
        result["pr_binding_status"] = "not_found"
        result["info"] = f"无法查找 PR: {r.stderr.strip()}"
        # 继续到 linked_issues 验证
    else:
        try:
            prs = json.loads(r.stdout)
        except json.JSONDecodeError as e:
            result["pr_binding_status"] = "parse_error"
            result["errors"].append(f"解析 PR list 失败: {e}")
            prs = []

        if not prs:
            result["pr_binding_status"] = "not_found"
            result["info"] = f"分支 {current_branch} 无 PR 记录"
        else:
            result["pr_total_matched"] = len(prs)

            # 优先找 headRefOid == local_head_sha 的 PR
            matched_pr = None
            for pr in prs:
                if pr.get("headRefOid", "") == local_head_sha:
                    matched_pr = pr
                    break

            if matched_pr is None:
                # 没有匹配的，按状态优先级取最新：OPEN > MERGED > CLOSED
                def _state_priority(pr_item: dict) -> int:
                    s = pr_item.get("state", "").upper()
                    if s == "OPEN":
                        return 0
                    if s == "MERGED":
                        return 1
                    return 2  # CLOSED / other
                prs_sorted = sorted(prs, key=_state_priority)
                matched_pr = prs_sorted[0]
                result["pr_found"] = True
                result["pr_number"] = matched_pr.get("number")
                result["pr_state"] = matched_pr.get("state", "")
                result["pr_head_sha"] = matched_pr.get("headRefOid", "")
                result["pr_url"] = matched_pr.get("url", "")
                result["pr_binding_verified"] = False
                result["pr_binding_status"] = "head_mismatch"
                result["errors"].append(
                    f"PR head 不匹配: PR #{result['pr_number']} "
                    f"head={result['pr_head_sha']}, 本地 HEAD={local_head_sha} "
                    f"(共 {len(prs)} 个 PR)"
                )
            else:
                result["pr_found"] = True
                result["pr_number"] = matched_pr.get("number")
                result["pr_state"] = matched_pr.get("state", "")
                result["pr_head_sha"] = matched_pr.get("headRefOid", "")
                result["pr_url"] = matched_pr.get("url", "")
                result["pr_binding_verified"] = True
                result["pr_binding_status"] = "verified"

            # 对选中的 PR 执行 gh pr view 获取详细信息
            if result["pr_number"] is not None:
                vr = _run_gh(
                    gh_exe,
                    [
                        "pr", "view", str(result["pr_number"]),
                        "--repo", owner_repo,
                        "--json", "baseRefName,mergeCommit,mergedAt,commits,url",
                    ],
                    token,
                )
                if vr.returncode == 0 and vr.stdout.strip():
                    try:
                        vdata = json.loads(vr.stdout)
                        result["pr_base_branch"] = vdata.get("baseRefName", "")
                        result["pr_merged_at"] = vdata.get("mergedAt", "")
                        result["pr_url"] = vdata.get("url", result["pr_url"])
                        mc = vdata.get("mergeCommit")
                        if isinstance(mc, dict):
                            result["pr_merge_commit"] = mc.get("oid", "")
                        commits = vdata.get("commits", [])
                        if isinstance(commits, list):
                            result["pr_commits_count"] = len(commits)
                    except json.JSONDecodeError:
                        pass

    # 5b. linked_issues 验证
    for issue_number in linked_issues:
        issue_status = {
            "number": issue_number,
            "exists": False,
            "state": None,
            "title": None,
            "error": None,
        }
        r = _run_gh(
            gh_exe,
            ["issue", "view", str(issue_number), "--repo", owner_repo, "--json", "number,state,title"],
            token,
        )
        if r.returncode == 0 and r.stdout.strip():
            try:
                issue_data = json.loads(r.stdout)
                issue_status["exists"] = True
                issue_status["state"] = issue_data.get("state")
                issue_status["title"] = issue_data.get("title")
            except json.JSONDecodeError as e:
                issue_status["error"] = f"解析失败: {e}"
        else:
            issue_status["error"] = f"查询失败: {r.stderr.strip()}"
        result["linked_issues_status"].append(issue_status)

    return result


# =============================================================================
# 主入口：执行完整的 L1-L5 真源推理链
# =============================================================================
def verify(
    devroot: Path,
    target: Path,
    gh_ctx,
    verify_pr_binding: bool = True,
    verify_linked_issues: bool = True,
) -> SourceTruthContext:
    """
    执行完整的 L1-L5 真源推理链。

    参数:
        devroot: 开发根目录绝对路径
        target: 操作目标 worktree 路径
        gh_ctx: GhContext（来自 gh_preflight.verify，含 gh_exe、token 等）
        verify_pr_binding: 是否执行 L5 PR 绑定验证（默认 True）
        verify_linked_issues: 是否验证 git-security.json 中的 linked_issues（默认 True）

    返回:
        SourceTruthContext: 验证结果。ok=True 表示全部通过。
        owner_repo 字段是经过验证的，可直接用于所有 gh CLI 命令的 --repo 参数。
        manifest_data 可直接序列化到 manifest JSON。
    """
    stx = SourceTruthContext()
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    # -------------------------------------------------------------------------
    # Layer 1: 本地实测推断
    # -------------------------------------------------------------------------
    l1 = _layer1_infer_from_local_state(git_exe, target)
    stx.current_branch = l1["current_branch"]
    stx.current_branch_source = l1["current_branch_source"]
    stx.local_head_sha = l1["local_head_sha"]
    stx.local_head_sha_source = l1["local_head_sha_source"]
    stx.latest_commit_message = l1["latest_commit_message"]
    stx.latest_commit_message_source = l1["latest_commit_message_source"]
    stx.remote_url_from_config_raw = l1["remote_url_from_config_raw"]
    stx.remote_url_from_config_canonical = l1["remote_url_from_config_canonical"]
    stx.remote_url_from_config_source = l1["remote_url_from_config_source"]
    stx.inferred_owner_repo = l1["inferred_owner_repo"]
    stx.inferred_owner_repo_source = l1["inferred_owner_repo_source"]

    # -------------------------------------------------------------------------
    # Layer 2: 用户声明审计
    # -------------------------------------------------------------------------
    l2 = _layer2_read_user_declaration(target)
    stx.declared_source_path = Path(l2["security_json_path"]) if l2["security_json_path"] else None
    stx.declared_owner_repo = l2["declared_owner_repo"]
    stx.declared_remote_url_raw = l2["declared_remote_url_raw"]
    stx.declared_remote_url_canonical = l2["declared_remote_url_canonical"]
    stx.declared_default_branch = l2["declared_default_branch"] or "main"
    stx.declared_linked_issues = l2["declared_linked_issues"]
    stx.owner_repo_source_path = stx.declared_source_path

    # L2 自洽性错误直接阻断
    if l2["errors"] and not l2["self_consistent"]:
        stx.errors.extend(l2["errors"])
        stx.ok = False
        stx.manifest_data = _build_manifest_data(stx, l1, l2, None, None, None)
        return stx

    # -------------------------------------------------------------------------
    # Layer 3: 交叉验证
    # -------------------------------------------------------------------------
    l3 = _layer3_cross_validate(l1, l2)
    stx.owner_repo = l3["owner_repo_value"]
    stx.owner_repo_source = l3["owner_repo_source"]
    stx.owner_repo_source_path = Path(l3["owner_repo_source_path"]) if l3["owner_repo_source_path"] else None
    stx.conflicts.extend(l3["conflicts"])
    stx.warnings.extend(l3["warnings"])
    stx.infos.extend(l3.get("infos", []))

    if not l3["passed"]:
        stx.errors.append("L3 交叉验证失败: 无法确定 owner_repo")
        stx.ok = False
        stx.manifest_data = _build_manifest_data(stx, l1, l2, l3, None, None)
        return stx

    # -------------------------------------------------------------------------
    # Layer 4: 远程物理绑定
    # -------------------------------------------------------------------------
    l4 = _layer4_verify_physical_binding(
        gh_ctx.gh_exe,
        git_exe,
        stx.owner_repo,
        stx.local_head_sha,
        stx.current_branch,
        target,
        gh_ctx.token,
    )
    stx.physical_binding_verified = l4["physical_binding_verified"]
    stx.physical_binding_status = l4["physical_binding_status"]
    stx.physical_binding_method = l4["physical_binding_method"]
    stx.remote_head_sha = l4["remote_head_sha"]
    stx.remote_head_sha_source = l4["remote_head_sha_source"]
    stx.state_aligned = l4["state_aligned"]
    stx.state_alignment_status = l4["state_alignment_status"]
    stx.errors.extend(l4["errors"])

    # 物理绑定断裂时阻断
    if stx.physical_binding_status == "broken":
        stx.ok = False
        stx.manifest_data = _build_manifest_data(stx, l1, l2, l3, l4, None)
        return stx

    # -------------------------------------------------------------------------
    # Layer 5: 远程对象绑定（可选）
    # -------------------------------------------------------------------------
    if verify_pr_binding and stx.current_branch and stx.owner_repo:
        l5 = _layer5_verify_remote_object_binding(
            gh_ctx.gh_exe,
            stx.owner_repo,
            stx.current_branch,
            stx.local_head_sha,
            stx.declared_linked_issues if verify_linked_issues else [],
            gh_ctx.token,
        )
        stx.pr_found = l5["pr_found"]
        stx.pr_number = l5["pr_number"]
        stx.pr_state = l5["pr_state"]
        stx.pr_head_sha = l5["pr_head_sha"]
        stx.pr_base_branch = l5["pr_base_branch"]
        stx.pr_merge_commit = l5["pr_merge_commit"]
        stx.pr_merged_at = l5["pr_merged_at"]
        stx.pr_commits_count = l5["pr_commits_count"]
        stx.pr_url = l5["pr_url"]
        stx.pr_total_matched = l5["pr_total_matched"]
        stx.pr_binding_verified = l5["pr_binding_verified"]
        stx.pr_binding_status = l5["pr_binding_status"]
        stx.linked_issues_status = l5["linked_issues_status"]
        # L5 的 info 和 errors 不影响 ok，只作为远程对象绑定信息
        if l5["info"]:
            stx.warnings.append(f"[L5] {l5['info']}")
        for e in l5["errors"]:
            stx.warnings.append(f"[L5] {e}")
    else:
        l5 = None

    # -------------------------------------------------------------------------
    # 最终状态
    # -------------------------------------------------------------------------
    stx.ok = len(stx.errors) == 0
    stx.manifest_data = _build_manifest_data(stx, l1, l2, l3, l4, l5)
    return stx


# =============================================================================
# Manifest 数据构建
# =============================================================================
def _build_manifest_data(stx: SourceTruthContext, l1: dict, l2: dict, l3: dict, l4: dict, l5: dict) -> dict:
    """将 SourceTruthContext 和 L1-L5 中间结果汇总为 manifest_data。"""
    data = {
        "layer1_local_inference": {
            "is_git_repo": l1.get("is_git_repo"),
            "git_dir_path": l1.get("git_dir_path"),
            "current_branch": stx.current_branch,
            "current_branch_source": stx.current_branch_source,
            "local_head_sha": stx.local_head_sha,
            "local_head_sha_source": stx.local_head_sha_source,
            "latest_commit_message": stx.latest_commit_message,
            "latest_commit_message_source": stx.latest_commit_message_source,
            "remote_url_from_config_raw": stx.remote_url_from_config_raw,
            "remote_url_from_config_canonical": stx.remote_url_from_config_canonical,
            "remote_url_from_config_source": stx.remote_url_from_config_source,
            "inferred_owner_repo": stx.inferred_owner_repo,
            "inferred_owner_repo_source": stx.inferred_owner_repo_source,
        },
        "layer2_user_declaration": {
            "security_json_exists": l2.get("security_json_exists"),
            "security_json_path": str(stx.declared_source_path) if stx.declared_source_path else None,
            "declared_owner_repo": stx.declared_owner_repo,
            "declared_remote_url_raw": stx.declared_remote_url_raw,
            "declared_remote_url_canonical": stx.declared_remote_url_canonical,
            "declared_default_branch": stx.declared_default_branch,
            "declared_linked_issues": stx.declared_linked_issues,
            "self_consistent": l2.get("self_consistent"),
        },
        "layer3_cross_validation": {
            "passed": l3.get("passed") if l3 else None,
            "owner_repo_source": stx.owner_repo_source,
            "owner_repo_value": stx.owner_repo,
            "owner_repo_source_path": str(stx.owner_repo_source_path) if stx.owner_repo_source_path else None,
            "conflicts": stx.conflicts,
            "warnings": stx.warnings,
        },
        "layer4_physical_binding": {
            "physical_binding_verified": stx.physical_binding_verified,
            "physical_binding_status": stx.physical_binding_status,
            "physical_binding_method": stx.physical_binding_method,
            "local_head_sha": stx.local_head_sha,
            "local_head_sha_source": stx.local_head_sha_source,
            "remote_head_sha": stx.remote_head_sha,
            "remote_head_sha_source": stx.remote_head_sha_source,
            "state_aligned": stx.state_aligned,
            "state_alignment_status": stx.state_alignment_status,
        },
        "layer5_remote_object_binding": {
            "pr_found": stx.pr_found,
            "pr_number": stx.pr_number,
            "pr_state": stx.pr_state,
            "pr_head_sha": stx.pr_head_sha,
            "pr_base_branch": stx.pr_base_branch,
            "pr_merge_commit": stx.pr_merge_commit,
            "pr_merged_at": stx.pr_merged_at,
            "pr_commits_count": stx.pr_commits_count,
            "pr_url": stx.pr_url,
            "pr_total_matched": stx.pr_total_matched,
            "pr_binding_verified": stx.pr_binding_verified,
            "pr_binding_status": stx.pr_binding_status,
            "linked_issues_status": stx.linked_issues_status,
        },
        "source_truth": {
            "ok": stx.ok,
            "owner_repo": stx.owner_repo,
            "owner_repo_source": stx.owner_repo_source,
            "errors": stx.errors,
        },
    }
    return data
