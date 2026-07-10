#!/usr/bin/env python3
r"""
workflow-gh-pr.py — GitHub PR 自闭环 Workflow（gh CLI 编排）
标签：py-tools
版本：v1.2.0（title + body 双生成）
v1.1.1→v1.2.0 更新意图：新增 --auto 模式下 body 的 AI 双生成（title 概括主题 + body 含变更概述/commits/统计/审查事项）；
                      补强与 workflow-deploy-full[-poly].py 的衔接说明；--no-pull 默认同步 master 提升本地一致性。

职责：编排 gh-pr-create.py → gh-pr-merge.py → 本地同步，一键完成远端 PR 闭环（create→merge→cleanup→pull）。
      前提：当前在 feature 分支，且已 push 到 origin（remote 分支存在）。
      与部署 workflow 衔接：
        - workflow-deploy-full.py / workflow-git-deploy-full-poly.py 负责 git add/commit/push（含安全扫描、AI 摘要、Issue 同步）；
        - 本 workflow 接过已 push 的 feature 分支，负责 PR create / merge / 分支清理 / 本地 master 同步。
      注意：PR 合并发生在 GitHub 远端服务器（gh pr merge 本质是 REST API 封装），merge 后本地 master 需 pull 才同步。

执行顺序：
  1. Preflight：验证 git.exe（隔离 MinGit）、当前在 feature 分支（非 base）、remote 分支存在、gh CLI 可用
  2. 确定 PR title/body（workflow 层决策）：
     - --auto：AI 聚合 feature 分支全部 commits + diff --stat，生成 title（≤72 字符 conventional commits 中文）+ body（概述/commits/统计/审查事项）
     - --title：使用指定标题，body 用默认模板
  3. Step 1 PR Create：调用 gh-pr-create.py（--title/--body/--base）
  4. Step 2 PR Merge：调用 gh-pr-merge.py（--strategy/--admin/--delete-branch）
  5. Step 3 本地同步：checkout base + pull origin base（除非 --no-pull）

认证与隔离机制（gh CLI headless）：
  - gh CLI 隔离部署于 venv/gh/bin/gh.exe，配置隔离于 venv/data-gh（GH_CONFIG_DIR）。
  - 自动化调用无需 `gh auth login`：直接注入环境变量即可 headless 运行：
      $env:GH_TOKEN = $env:GITHUB_PAT        # 复用 .env 的 PAT
      $env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"
  - 底层 gh_preflight 插件（py-plugins/gh_preflight.py）验证 gh.exe + PAT + 认证状态，返回 GhContext（含 run_gh 封装）。

审计产物与追踪路径：
  - PR Create 成功：stdout 末行输出 PR URL（https://github.com/owner/repo/pull/123）
  - PR Merge 成功：exit code 0；失败时提示可在网页端手动处理（PR 分支名已打印）

参数：
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --devroot | str | 否 | D:\pjt\cursor\cs_py | devroot 绝对路径（用于定位 git.exe / gh.exe / .env） |
| --base | str | 否 | master | 目标分支（PR 合入目标） |
| --title | str | 条件 | — | PR 标题（与 --auto 互斥；二者必选其一） |
| --auto | flag | 否 | False | AI 自动生成 PR title + body（基于 feature 分支全部 commits 聚合） |
| --admin | flag | 否 | False | 使用管理员权限绕过分支保护（仓库开启 Require reviews 时必需） |
| --keep-branch | flag | 否 | False | merge 后保留分支（默认删除 remote + 本地分支） |
| --strategy | str | 否 | squash | merge/squash/rebase（默认 squash 复用 PR title 为 squash message） |
| --no-pull | flag | 否 | False | merge 后不自动切回 base 分支 pull（默认同步本地 master） |

调用示例：

  # 全自动（推荐）：AI 生成 title+body + admin 绕过分支保护 + 删除分支 + 同步 master
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-pr.py" --auto --admin

  # 指定 title（body 用默认模板）
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-pr.py" --title "feat: xxx"

  # 指定目标分支 + merge 策略 + 保留分支（不删）
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-pr.py" --auto --base develop --strategy merge --keep-branch

  # 仅创建 PR（不自动 merge），用于需要人工 review 的场景
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\gh-pr-create.py" --auto --base master

  # 仅合并（PR 已存在），rebase 策略 + 不删分支
  & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\gh-pr-merge.py" --strategy rebase --admin

  # 新建 GitHub 仓库（gh CLI 独立使用，headless 认证，补齐 deploy 主流程未覆盖的 repo create）
  $env:GH_TOKEN = $env:GITHUB_PAT
  $env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"
  & "${devroot}\venv\gh\bin\gh.exe" repo create my-new-project --private --source . --push
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
_PY_TOOLS_DIR = Path(__file__).parent.resolve()
_PY_EXE = Path(__file__).parent.parent.parent.parent.parent.parent / "venv" / "py" / "python.exe"


def _preflight(devroot: Path, base: str) -> str:
    """返回当前分支名；失败时打印错误并 exit(1)"""
    print(f"\n{'='*50}")
    print("[Preflight] 前置验证")
    print(f"{'='*50}")

    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    if not git_exe.exists():
        print(f"[FAIL] git.exe 不存在: {git_exe}")
        sys.exit(1)

    # 1. 当前分支
    r = subprocess.run(
        [str(git_exe), "-C", str(devroot), "branch", "--show-current"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if r.returncode != 0:
        print(f"[FAIL] 无法获取当前分支: {r.stderr.strip()}")
        sys.exit(1)
    current = r.stdout.strip()
    if current == base:
        print(f"[FAIL] 当前在 {base} 分支，无法对自身创建 PR")
        sys.exit(1)
    print(f"[OK] 当前分支: {current}")

    # 2. 远程分支存在
    r2 = subprocess.run(
        [str(git_exe), "-C", str(devroot), "ls-remote", "--heads", "origin", current],
        capture_output=True, text=True, encoding="utf-8"
    )
    if not r2.stdout.strip():
        print(f"[FAIL] 远程不存在分支 origin/{current}，请先 push")
        sys.exit(1)
    print(f"[OK] 远程分支存在: origin/{current}")

    # 3. gh CLI 存在
    gh_exe = devroot / "venv" / "gh" / "bin" / "gh.exe"
    if not gh_exe.exists():
        print(f"[FAIL] gh.exe 不存在: {gh_exe}")
        sys.exit(1)
    r3 = subprocess.run([str(gh_exe), "--version"], capture_output=True, text=True, encoding="utf-8")
    if r3.returncode != 0:
        print("[FAIL] gh CLI 不可用")
        sys.exit(1)
    print(f"[OK] gh CLI: {r3.stdout.strip().splitlines()[0]}")

    print("[Preflight] 全部通过\n")
    return current


def _get_commits(devroot: Path, current_branch: str, base: str) -> tuple[list[str], str]:
    """获取 feature 分支相对 base 的所有 commits 和变更统计。"""
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    r = subprocess.run(
        [str(git_exe), "-C", str(devroot), "log", f"{base}..{current_branch}", "--oneline", "--reverse"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    commits = [ln.strip() for ln in r.stdout.strip().splitlines() if ln.strip()]

    r2 = subprocess.run(
        [str(git_exe), "-C", str(devroot), "diff", f"{base}..{current_branch}", "--stat"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    stat = r2.stdout.strip()

    return commits, stat


def _run_agent(devroot: Path, prompt: str, system: str) -> str:
    """调用 AI Agent 生成文本，返回原始输出。"""
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
    from py_lib import load_plugins
    registry = load_plugins(devroot=str(devroot), profile="agent")
    provider_cfg = registry.provider_config.get_provider(source="config_json")
    agent = registry.agent_core.AgentCore(
        enable_tools=False,
        provider_cfg=provider_cfg,
    )
    return agent.run(prompt=prompt, system=system, max_turns=1)


def _generate_pr_content(devroot: Path, current_branch: str, base: str) -> tuple[str, str]:
    """
    调用 AI 根据 feature 分支全部 commits 生成 PR title 和 body。
    返回 (title, body)。
    """
    commits, stat = _get_commits(devroot, current_branch, base)
    if not commits:
        print("[WARN] 无 commits 可分析，使用 fallback")
        fallback_title = f"feat: changes from {current_branch}"
        fallback_body = f"Auto-generated PR from branch `{current_branch}`."
        return fallback_title, fallback_body

    commits_text = "\n".join(f"- {c}" for c in commits)

    # 1. 生成 title
    title_prompt = f"""你是一位资深产品经理。请根据以下 feature 分支的 commits，生成一个简洁的 GitHub PR title。

Commits:
{commits_text}

变更统计：
{stat}

要求：
1. 用 conventional commits 格式（如 feat:/fix:/refactor:）
2. 一行，不超过 72 个字符
3. 概括整个 feature 的主题，不是罗列每个 commit
4. 使用中文

请直接输出 title，不要添加任何前言或解释。
"""
    print("[AI] 正在生成 PR title...")
    start = time.time()
    try:
        title_raw = _run_agent(devroot, title_prompt, "你是资深产品经理，擅长用中文一句话概括功能变更的主题。")
        title = title_raw.strip().strip('"').strip("'").splitlines()[0].strip()
        if len(title) > 72:
            title = title[:72]
        print(f"[AI] PR title 生成完成 (耗时 {time.time() - start:.2f}s): {title}")
    except Exception as e:
        print(f"[AI] PR title 生成失败: {e}")
        title = f"feat: changes from {current_branch}"
        print(f"[AI] fallback title: {title}")

    # 2. 生成 body
    body_prompt = f"""你是一位资深技术负责人。请基于以下 feature 分支的 commits 和变更统计，生成一份 PR 正文（body），用于帮助 reviewer 理解变更内容和 merge 理由。

PR Title: {title}

Commits:
{commits_text}

变更统计：
{stat}

要求：
1. 第一段：2-3 句话概括这个 feature 解决了什么问题、达成了什么目标
2. 第二段：Commits 列表（用 markdown 无序列表）
3. 第三段：变更统计（直接粘贴上面的统计）
4. 第四段：审查注意事项（如有破坏性变更、配置变更、依赖变更、特殊部署步骤等请特别说明；如无则写"无特殊注意事项"）
5. 使用中文
6. 不要添加任何前言或结语，直接输出正文内容
"""
    print("[AI] 正在生成 PR body...")
    start = time.time()
    try:
        body = _run_agent(devroot, body_prompt, "你是资深技术负责人，擅长撰写清晰的技术文档和代码审查说明。")
        body = body.strip()
        print(f"[AI] PR body 生成完成 (耗时 {time.time() - start:.2f}s), 长度: {len(body)} 字符")
    except Exception as e:
        print(f"[AI] PR body 生成失败: {e}")
        body = f"Auto-generated PR from branch `{current_branch}`.\n\nCommits:\n{commits_text}\n\n变更统计:\n{stat}"
        print(f"[AI] fallback body: 使用基础模板")

    return title, body


def _run_py_tool(name: str, script: Path, args: list) -> bool:
    """调用 py-tools 脚本，实时输出，返回是否成功"""
    print(f"\n{'='*50}")
    print(f"[Step] {name}")
    print(f"{'='*50}")

    cmd = [str(_PY_EXE), str(script)] + args
    start = time.time()
    try:
        sys.stdout.flush()
        result = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        elapsed = time.time() - start
        if result.returncode != 0:
            print(f"[FAIL] {name} 失败 (耗时 {elapsed:.2f}s)")
            return False
        print(f"[OK] {name} 完成 (耗时 {elapsed:.2f}s)")
        return True
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"[FAIL] {name} 超时 (>300s)")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"[FAIL] {name} 异常: {e} (耗时 {elapsed:.2f}s)")
        return False


def main():
    parser = argparse.ArgumentParser(description="GitHub PR 自闭环 Workflow")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径")
    parser.add_argument("--base", default="master", help="目标分支")
    parser.add_argument("--title", default=None, help="PR 标题（与 --auto 互斥）")
    parser.add_argument("--auto", action="store_true", help="AI 自动生成 PR title + body（基于 feature 分支全部 commits 聚合）")
    parser.add_argument("--admin", action="store_true", help="使用管理员权限绕过分支保护")
    parser.add_argument("--keep-branch", action="store_true", help="merge 后保留分支（默认删除）")
    parser.add_argument("--strategy", choices=["merge", "squash", "rebase"], default="squash")
    parser.add_argument("--no-pull", action="store_true", help="merge 后不自动切回 base 分支 pull")
    args = parser.parse_args()

    if args.title and args.auto:
        print("[FAIL] --title 与 --auto 互斥")
        sys.exit(1)
    if not args.title and not args.auto:
        print("[FAIL] 必须指定 --title 或 --auto")
        sys.exit(1)

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[ERROR] devroot 不存在: {devroot}")
        sys.exit(1)

    # 显式切换进程 CWD 到目标目录，确保所有相对路径和 . 指向 devroot
    import os
    os.chdir(devroot)
    print(f"[OK] 工作目录已切换: {devroot}")

    total_start = time.time()
    print(f"\n{'#'*50}")
    print("# GitHub PR 自闭环 Workflow")
    print(f"# devroot: {devroot}")
    print(f"# base: {args.base}")
    print(f"{'#'*50}")
    sys.stdout.flush()

    # Preflight
    current_branch = _preflight(devroot, args.base)

    # 确定 PR title 和 body（workflow 层决策）
    if args.auto:
        pr_title, pr_body = _generate_pr_content(devroot, current_branch, args.base)
    else:
        pr_title = args.title
        pr_body = f"Auto-generated PR from branch `{current_branch}`."
    print(f"[OK] PR title 确定: {pr_title}")
    print(f"[OK] PR body 长度: {len(pr_body)} 字符")

    # Step 1: PR Create（传确定的 --title 和 --body）
    create_args = ["--devroot", str(devroot), "--title", pr_title, "--body", pr_body, "--base", args.base]
    create_ok = _run_py_tool("PR Create", _PY_TOOLS_DIR / "gh-pr-create.py", create_args)
    if not create_ok:
        print(f"\n{'#'*50}")
        print("# [FAILURE] PR Create 失败，workflow 中断")
        print(f"{'#'*50}\n")
        sys.exit(1)

    # Step 2: PR Merge
    merge_args = ["--devroot", str(devroot), "--strategy", args.strategy]
    if args.admin:
        merge_args.append("--admin")
    if not args.keep_branch:
        merge_args.append("--delete-branch")

    merge_ok = _run_py_tool("PR Merge", _PY_TOOLS_DIR / "gh-pr-merge.py", merge_args)
    if not merge_ok:
        print(f"\n{'#'*50}")
        print("# [FAILURE] PR Merge 失败")
        print(f"# [HINT] 如需手动在网页端处理，PR 分支为: {current_branch}")
        print(f"{'#'*50}\n")
        sys.exit(1)

    # Step 3: 本地同步（可选）
    if not args.no_pull:
        print(f"\n{'='*50}")
        print("[Step] 本地同步")
        print(f"{'='*50}")
        git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
        for sub_cmd in [
            [str(git_exe), "-C", str(devroot), "checkout", args.base],
            [str(git_exe), "-C", str(devroot), "pull", "origin", args.base],
        ]:
            r = subprocess.run(sub_cmd, text=True, encoding="utf-8")
            if r.returncode != 0:
                print(f"[WARN] {' '.join(sub_cmd[3:])} 失败，请手动处理")
                break
        else:
            print(f"[OK] 本地已同步到 {args.base}")

    total_elapsed = time.time() - total_start
    print(f"\n{'#'*50}")
    print(f"# [SUCCESS] PR 闭环完成 (总耗时 {total_elapsed:.2f}s)")
    print(f"{'#'*50}\n")


if __name__ == "__main__":
    main()
