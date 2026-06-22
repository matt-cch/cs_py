#!/usr/bin/env python3
"""
插件：Agent 核心引擎（Agent Core）
标签：agent
依赖：llm_client, agent_tools, agent_context

职责：实现标准 ReAct 循环（Reasoning + Acting），协调 LLM 调用、工具执行、上下文管理。
      与 OpenCode processGeneration / SubZeroClaw agent_run 对齐。

用法：
    import sys
    sys.path.insert(0, r"...\\scripts")
    from py_lib import load_plugins
    registry = load_plugins(devroot="D:/pjt/cursor/cs_py", tags=["agent"])

    # 单次调用（无需工具）
    answer = registry.agent_core.run(
        prompt="总结这段 diff",
        system="你是代码审查员",
        model="kimi-k2.5",
        temperature=0.3,
    )

    # 完整 ReAct（启用工具）
    answer = registry.agent_core.run(
        prompt="读取 /tmp/test.txt 并告诉我内容",
        enable_tools=True,
        max_turns=10,
    )
"""
import json
from typing import Any, Dict, List, Optional

# 依赖模块通过 py_lib 拓扑排序后已加载到同命名空间
# 但为支持直接 import，使用延迟导入
_llm_client = None
_agent_tools = None
_agent_context = None


def _resolve_deps():
    """延迟解析依赖模块（支持 py_lib 加载和直接 import 两种模式）"""
    global _llm_client, _agent_tools, _agent_context
    if _llm_client is None:
        try:
            import llm_client as _llm_client
        except ImportError:
            _llm_client = None
    if _agent_tools is None:
        try:
            import agent_tools as _agent_tools
        except ImportError:
            _agent_tools = None
    if _agent_context is None:
        try:
            import agent_context as _agent_context
        except ImportError:
            _agent_context = None


class AgentCore:
    """
    ReAct Agent 核心引擎。

    循环逻辑：
        for turn in 1..max_turns:
            1. 检查上下文是否超限 → 触发压缩
            2. 调用 LLM（携带 tools 定义）
            3. 解析响应
               - finish_reason == "tool_calls" → 执行工具 → 结果追加上下文 → continue
               - finish_reason == "stop" / "length" → 返回答案
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_turns: int = 10,
        max_tokens: Optional[int] = None,
        enable_tools: bool = False,
        context_max_messages: int = 40,
        context_keep_recent: int = 10,
        provider_cfg: Optional[Dict[str, Any]] = None,
    ):
        """
        参数:
            model: 模型 ID，None 时取 llm_client 配置默认值
            temperature: 采样温度
            max_turns: 最大 ReAct 轮次
            max_tokens: 单次生成最大 token 数
            enable_tools: 是否启用工具调用（默认 False，仅文本生成）
            context_max_messages: 上下文压缩阈值
            context_keep_recent: 压缩后保留的最近消息数
            provider_cfg: 显式传入的 provider 配置（如 config.json 来源），
                          None 时由 llm_client 自行读取
        """
        _resolve_deps()
        self.model = model
        self.temperature = temperature
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.enable_tools = enable_tools
        self.provider_cfg = provider_cfg
        self.ctx = _agent_context.ContextManager(
            max_messages=context_max_messages,
            keep_recent=context_keep_recent,
        )

    def _maybe_compact(self) -> None:
        """检查并压缩上下文（由 agent_core 协调 LLM 做摘要）"""
        if not self.ctx.is_full():
            return
        if _llm_client is None:
            return  # 无 LLM 客户端，跳过压缩

        # 生成历史摘要
        history_text = self.ctx.format_for_prompt(max_chars=4000)
        summary_prompt = (
            "Summarize this conversation. Keep all facts, file paths, commands, and decisions. "
            "Be concise.\n\n" + history_text
        )
        try:
            summary = _llm_client.chat_simple(
                prompt=summary_prompt,
                system="你是一个对话摘要助手",
                model=self.model,
                temperature=0.3,
                max_tokens=512,
            )
            self.ctx.compact("assistant", summary)
        except Exception as e:
            # 压缩失败不阻塞主流程，仅截断旧消息
            print(f"[AgentCore] 上下文压缩失败: {e}，执行简单截断")
            # 强制截断：保留 system + 最近 keep_recent 条
            msgs = self.ctx.get()
            system_msgs = [m for m in msgs if m.get("role") == "system"]
            rest = [m for m in msgs if m.get("role") != "system"]
            keep = rest[-self.ctx.keep_recent:]
            self.ctx.clear()
            for m in system_msgs:
                self.ctx.add(m["role"], m.get("content", ""), **{k: v for k, v in m.items() if k not in ("role", "content")})
            for m in keep:
                self.ctx.add(m["role"], m.get("content", ""), **{k: v for k, v in m.items() if k not in ("role", "content")})

    def _call_llm(self) -> tuple[Dict[str, Any], Optional[str]]:
        """调用 LLM，返回 (message_dict, finish_reason)"""
        if _llm_client is None:
            raise RuntimeError("llm_client 插件未加载")

        tools_spec = None
        if self.enable_tools and _agent_tools is not None:
            tools_spec = _agent_tools.get_tools_spec()

        return _llm_client.chat(
            messages=self.ctx.get(),
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=tools_spec if tools_spec else None,
            provider_cfg=self.provider_cfg,
        )

    def _process_tool_calls(self, message: Dict[str, Any]) -> None:
        """处理 assistant 消息中的 tool_calls"""
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            return

        # 追加 assistant 的 tool_calls 消息
        self.ctx.add(
            "assistant",
            message.get("content") or "",
            tool_calls=tool_calls,
        )

        # 逐个执行工具并追加结果
        for tc in tool_calls:
            if _agent_tools is None:
                self.ctx.add(
                    "tool",
                    "[error] agent_tools 插件未加载",
                    tool_call_id=tc.get("id", ""),
                )
                continue

            result = _agent_tools.execute_tool(tc)
            self.ctx.add(
                "tool",
                result,
                tool_call_id=tc.get("id", ""),
            )

    def run(
        self,
        prompt: str,
        system: str = "你是一个 helpful assistant",
        **kwargs,
    ) -> str:
        """
        执行 ReAct 循环，返回最终文本答案。

        参数:
            prompt: 用户输入
            system: system prompt
            **kwargs: 可覆盖构造参数（model, temperature, max_turns, enable_tools 等）

        返回:
            assistant 的最终回答文本
        """
        # 允许单次 run 覆盖构造参数
        model = kwargs.get("model", self.model)
        temperature = kwargs.get("temperature", self.temperature)
        max_turns = kwargs.get("max_turns", self.max_turns)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        enable_tools = kwargs.get("enable_tools", self.enable_tools)

        # 重置上下文（每次 run 是独立会话）
        self.ctx.clear()
        self.ctx.add("system", system)
        self.ctx.add("user", prompt)

        for turn in range(1, max_turns + 1):
            # 1. 上下文压缩检查
            self._maybe_compact()

            # 2. 调用 LLM
            try:
                message, finish_reason = self._call_llm()
            except Exception as e:
                return f"[AgentCore] LLM 调用失败 (turn {turn}): {e}"

            # 3. 解析响应
            if finish_reason == "tool_calls":
                self._process_tool_calls(message)
                continue  # 继续下一轮

            # stop / length / None → 返回结果
            return message.get("content", "")

        return "[AgentCore] 达到最大轮次，未收敛"


# =============================================================================
# 便捷函数（无需显式实例化 AgentCore）
# =============================================================================

_default_agent: Optional[AgentCore] = None


def run(
    prompt: str,
    system: str = "你是一个 helpful assistant",
    **kwargs,
) -> str:
    """
    全局便捷入口：使用默认 AgentCore 实例执行单次任务。

    用法:
        from agent_core import run
        answer = run("总结这段 diff", system="你是代码审查员", temperature=0.3)
    """
    global _default_agent
    if _default_agent is None:
        _default_agent = AgentCore()
    return _default_agent.run(prompt, system=system, **kwargs)
