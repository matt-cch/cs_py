#!/usr/bin/env python3
"""
generate-ai-summary.py — AI 语义摘要生成器（示范脚本）
标签：py-tools

职责：读取 git diff，调用自研 Agent 底层能力生成中文语义摘要，并落盘到 venv/tmp/。
      用于验证 nanobot Agent 插件体系在 workflow 场景下的可用性。

用法：
    python generate-ai-summary.py --devroot "D:/pjt/cursor/cs_py"
    python generate-ai-summary.py --devroot "D:/pjt/cursor/cs_py" --target "D:/pjt/cursor/cs_py/apps/repos/jywl-team/jywl-lab"
    python generate-ai-summary.py --cached --message "feat: xxx"
    python generate-ai-summary.py --commit-range "HEAD~1..HEAD" --message "feat: xxx"

输出：
    - stdout: 生成的中文摘要
    - 落盘: venv/tmp/ai-summary-{timestamp}.json
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def _load_tools_config(devroot: Path) -> dict:
    """读取 tools_config.json，返回 ai_summary 配置节。失败时返回空 dict。"""
    config_path = devroot / "references" / "runtime" / "runtime_config" / "tools_config.json"
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return data.get("ai_summary", {})
    except Exception:
        return {}


# 确保 scripts/ 在 path 中
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def get_git_diff(git_exe: Path, target: Path, commit_range: str = "HEAD~1..HEAD", cached: bool = False) -> str:
    """获取 git diff 文本。commit_range 仅当 cached=False 时使用。"""
    cmd = [str(git_exe), "-C", str(target), "diff"]
    if cached:
        cmd.append("--cached")
    else:
        cmd.append(commit_range)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"[warn] git diff 失败: {result.stderr}", file=sys.stderr)
        return ""
    diff_len = len(result.stdout)
    print(f"[Diag] git diff 原始长度: {diff_len} 字符")
    sys.stdout.flush()
    return result.stdout


def get_changed_files(git_exe: Path, target: Path, commit_range: str = "HEAD~1..HEAD", cached: bool = False) -> list[str]:
    """获取变更文件列表"""
    cmd = [str(git_exe), "-C", str(target), "diff", "--name-only"]
    if cached:
        cmd.append("--cached")
    else:
        cmd.append(commit_range)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]


def generate_summary(devroot: Path, diff_text: str, commit_message: str, changed_files: list[str], max_diff_chars: int = 80000) -> str:
    """
    调用 Agent 底层能力生成中文语义摘要。

    依赖 py_lib 加载 agent 插件体系。
    调试阶段使用 source="config_json" 命中 OpenCode config.json 分支。
    """
    print(f"[{datetime.now().isoformat()}] [Progress] 进入 generate_summary，准备加载 agent 插件体系...")
    sys.stdout.flush()
    step_start = time.time()

    from py_lib import load_plugins
    registry = load_plugins(devroot=str(devroot), profile="agent")
    print(f"[{datetime.now().isoformat()}] [Progress] agent 插件体系加载完成 (耗时 {time.time() - step_start:.2f}s)")
    sys.stdout.flush()

    # 显式从 config.json 读取 provider 配置（调试：确保命中 config.json 分支）
    provider_cfg = registry.provider_config.get_provider(source="config_json")
    print(f"[{datetime.now().isoformat()}] [Progress] Provider 配置读取完成: model={provider_cfg.get('model')} | base_url={provider_cfg.get('base_url')}")
    sys.stdout.flush()

    # 构造 prompt
    file_list_text = "\n".join(f"- {f}" for f in changed_files) if changed_files else "（无文件变更）"

    # 截断 diff 防止超出上下文窗口（max_diff_chars 由 CLI > tools_config > 默认值 80000 决定）
    diff_len = len(diff_text)
    effective_max = max_diff_chars if max_diff_chars > 0 else diff_len
    diff_truncated = diff_text[:effective_max] if diff_len > effective_max else diff_text
    if diff_len > effective_max and max_diff_chars > 0:
        diff_truncated += f"\n\n... (diff 已截断，原始长度 {diff_len} 字符，阈值 {max_diff_chars})"
    print(f"[Diag] diff 截断前: {diff_len} 字符, 截断后: {len(diff_truncated)} 字符, 阈值: {max_diff_chars}")
    sys.stdout.flush()

    prompt = f"""你是一位资深代码审查员。请阅读以下 git diff，用中文总结本次变更的核心内容。

要求：
1. 用 3-5 个 bullet point 概括「改了什么逻辑」「为什么改」「有什么影响」
2. 不要罗列文件路径（已有结构化摘要）
3. 关注业务语义，而非代码细节
4. 如果变更引入潜在风险，请明确标注

Commit message: {commit_message}

变更文件：
{file_list_text}

Diff：
```diff
{diff_truncated}
```

请直接输出 bullet points，不要添加标题或前言。
"""

    prompt_len = len(prompt)
    print(f"[{datetime.now().isoformat()}] [Progress] Prompt 构造完成，长度 {prompt_len} 字符")
    sys.stdout.flush()

    # Agent Preflight: 调用 atomic-agent-preflight.py 确认 LLM 可达
    preflight_script = devroot / "references" / "tasks" / "deploy-git-isolated" / "scripts" / "py-tools" / "atomic-agent-preflight.py"
    preflight_manifest = devroot / "venv" / "tmp" / f"agent-preflight-for-ai-summary-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    preflight_cmd = [str(devroot / "venv" / "py" / "python.exe"), str(preflight_script), "--devroot", str(devroot), "--output", str(preflight_manifest)]

    print(f"[{datetime.now().isoformat()}] [Progress] Agent Preflight: 调用 atomic-agent-preflight.py...")
    sys.stdout.flush()
    preflight_lines = []
    try:
        process = subprocess.Popen(
            preflight_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in process.stdout:
            line = line.rstrip("\n")
            print(line, flush=True)
            preflight_lines.append(line)
        process.wait(timeout=60)
        if process.returncode != 0:
            raise RuntimeError(f"atomic-agent-preflight 返回非 0 (exit {process.returncode})")

        # 解析最后一行 JSON
        if not preflight_lines:
            raise RuntimeError("atomic-agent-preflight 无输出")
        preflight_result = json.loads(preflight_lines[-1])
        if not preflight_result.get("success"):
            raise RuntimeError(f"atomic-agent-preflight 失败: {preflight_result.get('error')}")

        print(f"[{datetime.now().isoformat()}] [Progress] Agent Preflight 通过，manifest: {preflight_result.get('manifest')}")
        sys.stdout.flush()
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] [Progress] Agent Preflight 失败: {e}")
        sys.stdout.flush()
        raise

    print(f"[{datetime.now().isoformat()}] [Progress] AgentCore 初始化开始...")
    start = time.time()
    try:
        # 显式构造 AgentCore，传入 config.json 的 provider_cfg
        # 【原则】generate-ai-summary 不创造/修改任何参数，全部从 config.json 照搬
        print(f"[Diag] AgentCore 初始化开始...")
        sys.stdout.flush()
        agent = registry.agent_core.AgentCore(
            enable_tools=False,
            provider_cfg=provider_cfg,
        )
        print(f"[{datetime.now().isoformat()}] [Progress] AgentCore 初始化完成 (耗时 {time.time() - start:.2f}s)")
        sys.stdout.flush()

        print(f"[{datetime.now().isoformat()}] [Progress] 开始调用 LLM 生成摘要（预计耗时 30-120s，视 diff 大小而定）...")
        sys.stdout.flush()
        llm_start = time.time()
        summary = agent.run(
            prompt=prompt,
            system="你是资深代码审查员，擅长用中文提炼代码变更的业务语义。",
            max_turns=1,
        )
        llm_elapsed = time.time() - llm_start
        total_elapsed = time.time() - start
        print(f"[{datetime.now().isoformat()}] [Progress] LLM 生成完成（LLM 耗时 {llm_elapsed:.2f}s，generate_summary 总耗时 {total_elapsed:.2f}s）")
        sys.stdout.flush()
        return summary
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{datetime.now().isoformat()}] [Progress] 摘要生成失败 (耗时 {elapsed:.2f}s): {e}", file=sys.stderr)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="AI 语义摘要生成器（nanobot Agent 示范）")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径（用于加载 agent 插件体系）")
    parser.add_argument("--target", required=True, help="操作目标仓库路径（polyrepo 调用契约要求，必须显式传入，即使与 --devroot 相同）")
    parser.add_argument("--commit-range", default="HEAD~1..HEAD", help="Git diff 范围（仅当未传 --cached 时使用）")
    parser.add_argument("--cached", action="store_true", help="使用 staged diff（git diff --cached），替代 --commit-range")
    parser.add_argument("--message", default="", help="Commit message（覆盖自动读取）")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认 devroot/venv/tmp）")
    parser.add_argument("--diff-output", default=None, help="diff 审计文件输出路径。由上游 workflow 显式命名传入，便于审计追踪。未传入时回退到 devroot/venv/tmp/diff-audit-{ts}.json")
    parser.add_argument("--max-diff-chars", type=int, default=None, help="diff 截断阈值（字符数）。覆盖 tools_config.json 的 ai_summary.max_diff_chars。设为 0 表示不截断。")
    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] [Progress] ========== AI Summary 全流程开始 ==========")
    sys.stdout.flush()
    total_start = time.time()

    devroot = Path(args.devroot)
    target = Path(args.target)
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"

    # 0. 解析 diff 截断阈值：CLI > tools_config.json > 默认值 80000
    if args.max_diff_chars is not None:
        max_diff_chars = args.max_diff_chars
        threshold_source = "cli"
    else:
        ai_summary_cfg = _load_tools_config(devroot)
        max_diff_chars = ai_summary_cfg.get("max_diff_chars", 80000)
        threshold_source = "tools_config" if "max_diff_chars" in ai_summary_cfg else "default"
    print(f"[Config] diff 截断阈值: {max_diff_chars} (来源: {threshold_source})")
    sys.stdout.flush()

    if not devroot.exists():
        print(f"[error] devroot 不存在: {devroot}", file=sys.stderr)
        return 1
    if not target.exists():
        print(f"[error] target 不存在: {target}", file=sys.stderr)
        return 1

    # 1. 获取 commit message（如未传入，从 target git log 读取）
    commit_message = args.message
    if not commit_message:
        result = subprocess.run(
            [str(git_exe), "-C", str(target), "log", "-1", "--pretty=%s"],
            capture_output=True, text=True, encoding="utf-8"
        )
        commit_message = result.stdout.strip() or "（无 commit message）"

    # 2. 获取 diff 和变更文件（在 target 执行）
    if args.cached:
        diff_source = "staged (--cached)"
        diff_text = get_git_diff(git_exe, target, cached=True)
        changed_files = get_changed_files(git_exe, target, cached=True)
    else:
        diff_source = args.commit_range
        diff_text = get_git_diff(git_exe, target, args.commit_range)
        changed_files = get_changed_files(git_exe, target, args.commit_range)
    print(f"[Diff] 读取范围: {diff_source}")
    print(f"[Diff] 变更文件: {len(changed_files)} 个")

    if not diff_text.strip():
        print("[warn] diff 为空，可能无变更或范围错误", file=sys.stderr)
        return 0

    # 2.5: diff 审计落盘（原始完整 diff，供后续分析为什么过大）
    diff_audit = {
        "meta": {
            "script": str(Path(__file__).resolve()),
            "version": "1.0.0",
            "tag": "py-tools",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "devroot": str(devroot),
            "target": str(target),
        },
        "request": {
            "diff_source": diff_source,
            "commit_range": args.commit_range,
            "cached": args.cached,
            "changed_files": changed_files,
        },
        "diff_raw": diff_text,
        "diff_stats": {
            "length_chars": len(diff_text),
            "line_count": diff_text.count("\n") + 1 if diff_text else 0,
            "threshold": max_diff_chars,
            "threshold_source": threshold_source,
            "is_truncated_for_prompt": len(diff_text) > max_diff_chars if max_diff_chars > 0 else False,
            "truncated_at": max_diff_chars if max_diff_chars > 0 and len(diff_text) > max_diff_chars else None,
        },
    }
    diff_output_path = Path(args.diff_output) if args.diff_output else devroot / "venv" / "tmp" / f"diff-audit-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.json"
    diff_output_path.parent.mkdir(parents=True, exist_ok=True)
    diff_output_path.write_text(json.dumps(diff_audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Diff] 原始 diff 已落盘审计: {diff_output_path} ({len(diff_text)} 字符)")
    sys.stdout.flush()

    # 3. 调用 Agent 生成摘要（agent 插件体系仍从 devroot 加载）
    try:
        summary = generate_summary(devroot, diff_text, commit_message, changed_files, max_diff_chars)
    except Exception as e:
        print(f"[error] 生成失败: {e}", file=sys.stderr)
        return 1

    # 4. 落盘
    output_dir = Path(args.output_dir) if args.output_dir else devroot / "venv" / "tmp"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"ai-summary-{ts}.json"

    payload = {
        "version": "1.0.0",
        "commit_message": commit_message,
        "commit_range": args.commit_range,
        "changed_files": changed_files,
        "changed_files_count": len(changed_files),
        "ai_summary": summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. 输出
    total_elapsed = time.time() - total_start
    print(f"\n{'='*50}")
    print("AI 语义摘要")
    print(f"{'='*50}")
    print(summary)
    print(f"{'='*50}")
    print(f"[Output] 已落盘: {output_path}")
    print(f"[{datetime.now().isoformat()}] [Progress] ========== AI Summary 全流程完成，总耗时 {total_elapsed:.2f}s ==========")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
