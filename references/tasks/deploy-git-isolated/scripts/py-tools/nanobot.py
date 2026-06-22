#!/usr/bin/env python3
"""
nanobot.py — 极简 Agent CLI 入口
标签：py-tools

职责：提供命令行接口调用 Agent 核心能力，用于 workflow 集成和手动测试。

用法：
    # 单次调用（默认，不启用工具）
    python nanobot.py "总结这段 git diff" --system "你是代码审查员" --temperature 0.3

    # ReAct 模式（启用工具）
    python nanobot.py "读取 /tmp/test.txt 并总结" --tools --max-turns 10

    # 通过 py_lib 加载（workflow 集成推荐）
    from py_lib import load_plugins
    registry = load_plugins(devroot="...", tags=["agent"])
    answer = registry.agent_core.run(prompt="...", system="...")

环境：
    依赖 .env 中的 MOONSHOT_API_KEY / MOONSHOT_BASE_URL 或 CORECODER_API_KEY。
    配置读取逻辑在 llm_client.get_config() 中统一管理。
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 确保 scripts/ 和 py-plugins/ 在 path 中
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_PY_PLUGINS_DIR = _SCRIPTS_DIR / "py-plugins"
if str(_PY_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PY_PLUGINS_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="nanobot — 极简 Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python nanobot.py "用中文总结这段 diff" --system "代码审查员"
  python nanobot.py "查看当前目录" --tools
  echo "你好" | python nanobot.py --stdin
        """.strip(),
    )
    parser.add_argument("prompt", nargs="?", help="用户提示词（或 --stdin 从管道读取）")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取 prompt")
    parser.add_argument("--system", default="你是一个 helpful assistant", help="system prompt")
    parser.add_argument("--model", default=None, help="模型 ID（默认从 .env 读取）")
    parser.add_argument("--temperature", type=float, default=0.7, help="采样温度")
    parser.add_argument("--max-tokens", type=int, default=None, help="最大生成 token 数")
    parser.add_argument("--tools", action="store_true", help="启用工具调用（ReAct 模式）")
    parser.add_argument("--max-turns", type=int, default=10, help="最大 ReAct 轮次")
    parser.add_argument("--devroot", default=None, help="开发根目录（自动探测）")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出调试信息")

    args = parser.parse_args()

    # 读取 prompt
    if args.stdin:
        prompt = sys.stdin.read().strip()
    else:
        prompt = args.prompt or ""

    if not prompt:
        print("[error] 请提供 prompt 参数或使用 --stdin", file=sys.stderr)
        return 1

    # 加载 agent 插件
    try:
        from py_lib import load_plugins
        registry = load_plugins(devroot=args.devroot, tags=["agent"])
        agent_core = registry.agent_core
    except Exception as e:
        # py_lib 加载失败时，尝试直接 import（降级）
        if args.verbose:
            print(f"[warn] py_lib 加载失败: {e}，尝试直接 import", file=sys.stderr)
        try:
            import agent_core
            agent_core = agent_core.AgentCore()
        except Exception as e2:
            print(f"[error] Agent 加载失败: {e2}", file=sys.stderr)
            return 1

    if args.verbose:
        print(f"[nanobot] model={args.model or 'default'} temperature={args.temperature} tools={args.tools}")

    # 执行
    try:
        answer = agent_core.run(
            prompt=prompt,
            system=args.system,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            enable_tools=args.tools,
            max_turns=args.max_turns,
        )
        print(answer)
        return 0
    except Exception as e:
        print(f"[error] Agent 执行失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
