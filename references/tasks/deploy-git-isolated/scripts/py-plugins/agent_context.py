#!/usr/bin/env python3
"""
插件：Agent 上下文管理（Agent Context）
标签：agent, core
依赖：无（纯数据结构管理）

职责：管理对话消息历史，提供添加、查询、压缩、清空能力。
      不直接调用 LLM，压缩动作由 agent_core 协调执行。

用法：
    from agent_context import ContextManager

    ctx = ContextManager(max_messages=40)
    ctx.add("system", "你是代码审查员")
    ctx.add("user", "总结这段 diff")
    messages = ctx.get()

    # 上下文压缩（由 agent_core 在超限时调用）
    ctx.compact("[Summary of previous context]", "之前讨论了文件A和B的修改...")
"""
import copy
from typing import Any, Dict, List, Optional


class ContextManager:
    """
    对话上下文管理器。

    与 SubZeroClaw 的 compact_messages() 对齐：
    - 维护消息列表
    - 超限时由外部（agent_core）触发压缩
    - 压缩后保留 system prompt + 摘要 + 最近 N 条原始消息
    """

    def __init__(self, max_messages: int = 40, keep_recent: int = 10):
        """
        参数:
            max_messages: 触发压缩的阈值（默认 40，与 SubZeroClaw 一致）
            keep_recent: 压缩后保留的最近原始消息数（默认 10）
        """
        self._messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
        self.keep_recent = keep_recent

    def add(self, role: str, content: str, **kwargs) -> None:
        """
        添加一条消息。

        参数:
            role: system | user | assistant | tool
            content: 消息正文
            **kwargs: 额外字段（如 tool_calls, tool_call_id）
        """
        msg: Dict[str, Any] = {"role": role, "content": content}
        msg.update(kwargs)
        self._messages.append(msg)

    def get(self) -> List[Dict[str, Any]]:
        """获取当前完整消息列表的深拷贝（防止外部修改）"""
        return copy.deepcopy(self._messages)

    def count(self) -> int:
        """返回当前消息数"""
        return len(self._messages)

    def is_full(self) -> bool:
        """检查是否达到压缩阈值"""
        return self.count() > self.max_messages

    def compact(self, summary_role: str = "assistant", summary_content: str = "") -> None:
        """
        压缩上下文：保留 system prompt，用摘要替换中间历史，保留最近 N 条。

        参数:
            summary_role: 摘要消息的角色（默认 assistant）
            summary_content: 摘要文本
        """
        if not self.is_full():
            return

        # 保留 system prompt（通常在第一条）
        system_msgs = []
        rest = []
        for msg in self._messages:
            if msg.get("role") == "system":
                system_msgs.append(msg)
            else:
                rest.append(msg)

        # 保留最近 keep_recent 条
        keep = rest[-self.keep_recent:] if len(rest) > self.keep_recent else rest

        # 避免在边界处切断 orphaned tool 消息（tool 消息前必须有对应的 assistant tool_calls）
        # 简单策略：如果 keep 的第一条是 tool，则向前扩展直到找到非 tool
        while keep and keep[0].get("role") == "tool":
            # 从 rest 中往前多取一条
            idx = len(rest) - len(keep) - 1
            if idx < 0:
                break
            keep.insert(0, rest[idx])

        # 重建消息列表
        self._messages = system_msgs[:]
        if summary_content:
            self._messages.append({"role": summary_role, "content": summary_content})
        self._messages.extend(keep)

    def replace_last(self, role: str, content: str, **kwargs) -> None:
        """替换最后一条消息（用于 reflection/重试场景）"""
        if self._messages:
            self._messages.pop()
        self.add(role, content, **kwargs)

    def clear(self) -> None:
        """清空所有消息"""
        self._messages.clear()

    def format_for_prompt(self, max_chars: Optional[int] = None) -> str:
        """
        将消息历史格式化为纯文本（用于日志或调试）。

        参数:
            max_chars: 最大字符数，超限则截断
        """
        lines = []
        for msg in self._messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"[{role}] {content}")
        text = "\n".join(lines)
        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + "\n... (truncated)"
        return text
