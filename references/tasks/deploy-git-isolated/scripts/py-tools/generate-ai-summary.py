#!/usr/bin/env python3
"""
generate-ai-summary.py — AI 语义摘要生成器（示范脚本）
标签：py-tools

职责：读取 git diff，调用自研 Agent 底层能力生成中文语义摘要，并落盘到 venv/tmp/。
      用于验证 nanobot Agent 插件体系在 workflow 场景下的可用性。

用法：
    python generate-ai-summary.py --devroot "D:/pjt/cursor/cs_py"
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

# 确保 scripts/ 在 path 中
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


def get_git_diff(devroot: Path, commit_range: str = "HEAD~1..HEAD", cached: bool = False) -> str:
    """获取 git diff 文本。commit_range 仅当 cached=False 时使用。"""
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    cmd = [str(git_exe), "-C", str(devroot), "diff"]
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
    return result.stdout


def get_changed_files(devroot: Path, commit_range: str = "HEAD~1..HEAD", cached: bool = False) -> list[str]:
    """获取变更文件列表"""
    git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
    cmd = [str(git_exe), "-C", str(devroot), "diff", "--name-only"]
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


def generate_summary(devroot: Path, diff_text: str, commit_message: str, changed_files: list[str]) -> str:
    """
    调用 Agent 底层能力生成中文语义摘要。

    依赖 py_lib 加载 agent 插件体系。
    调试阶段使用 source="config_json" 命中 OpenCode config.json 分支。
    """
    from py_lib import load_plugins
    registry = load_plugins(devroot=str(devroot), profile="agent")

    # 显式从 config.json 读取 provider 配置（调试：确保命中 config.json 分支）
    provider_cfg = registry.provider_config.get_provider(source="config_json")
    print(f"[Provider] 来源: config.json | model: {provider_cfg.get('model')} | base_url: {provider_cfg.get('base_url')}")

    # 构造 prompt
    file_list_text = "\n".join(f"- {f}" for f in changed_files) if changed_files else "（无文件变更）"

    # 截断 diff 防止超出上下文窗口
    diff_truncated = diff_text[:12000] if len(diff_text) > 12000 else diff_text
    if len(diff_text) > 12000:
        diff_truncated += "\n\n... (diff 已截断，原始长度 {len(diff_text)} 字符)"

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

    print("[Agent] 正在生成语义摘要...")
    start = time.time()
    try:
        # 显式构造 AgentCore，传入 config.json 的 provider_cfg
        # 【原则】generate-ai-summary 不创造/修改任何参数，全部从 config.json 照搬
        agent = registry.agent_core.AgentCore(
            enable_tools=False,
            provider_cfg=provider_cfg,
        )
        summary = agent.run(
            prompt=prompt,
            system="你是资深代码审查员，擅长用中文提炼代码变更的业务语义。",
            max_turns=1,
        )
        elapsed = time.time() - start
        print(f"[Agent] 摘要生成完成 (耗时 {elapsed:.2f}s)")
        return summary
    except Exception as e:
        elapsed = time.time() - start
        print(f"[Agent] 摘要生成失败 (耗时 {elapsed:.2f}s): {e}", file=sys.stderr)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="AI 语义摘要生成器（nanobot Agent 示范）")
    parser.add_argument("--devroot", default=r"D:\pjt\cursor\cs_py", help="Devroot 路径")
    parser.add_argument("--commit-range", default="HEAD~1..HEAD", help="Git diff 范围（仅当未传 --cached 时使用）")
    parser.add_argument("--cached", action="store_true", help="使用 staged diff（git diff --cached），替代 --commit-range")
    parser.add_argument("--message", default="", help="Commit message（覆盖自动读取）")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认 devroot/venv/tmp）")
    args = parser.parse_args()

    devroot = Path(args.devroot)
    if not devroot.exists():
        print(f"[error] devroot 不存在: {devroot}", file=sys.stderr)
        return 1

    # 1. 获取 commit message（如未传入，从 git log 读取）
    commit_message = args.message
    if not commit_message:
        git_exe = devroot / "venv" / "git" / "cmd" / "git.exe"
        result = subprocess.run(
            [str(git_exe), "-C", str(devroot), "log", "-1", "--pretty=%s"],
            capture_output=True, text=True, encoding="utf-8"
        )
        commit_message = result.stdout.strip() or "（无 commit message）"

    # 2. 获取 diff 和变更文件
    if args.cached:
        diff_source = "staged (--cached)"
        diff_text = get_git_diff(devroot, cached=True)
        changed_files = get_changed_files(devroot, cached=True)
    else:
        diff_source = args.commit_range
        diff_text = get_git_diff(devroot, args.commit_range)
        changed_files = get_changed_files(devroot, args.commit_range)
    print(f"[Diff] 读取范围: {diff_source}")
    print(f"[Diff] 变更文件: {len(changed_files)} 个")

    if not diff_text.strip():
        print("[warn] diff 为空，可能无变更或范围错误", file=sys.stderr)
        return 0

    # 3. 调用 Agent 生成摘要
    try:
        summary = generate_summary(devroot, diff_text, commit_message, changed_files)
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
    print(f"\n{'='*50}")
    print("AI 语义摘要")
    print(f"{'='*50}")
    print(summary)
    print(f"{'='*50}")
    print(f"[Output] 已落盘: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
