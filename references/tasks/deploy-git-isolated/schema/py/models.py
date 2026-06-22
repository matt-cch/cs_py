#!/usr/bin/env python3
"""
schema/models.py — Plugin Result Schema 的 Pydantic Model 备选实现

职责：为需要强类型检查的场景提供 Pydantic BaseModel 封装。
      与 plugin-result-schema.json 共享同一契约，二者必须同步更新。

用法：
    from schema.models import PluginResult, Violation

    result = PluginResult(
        plugin="lint_python",
        files_scanned=1,
        files_with_violations=0,
        violations_found=0,
        violations=[]
    )
    dict_result = result.model_dump()  # 转为 dict 供上层消费

注意：本文件为可选依赖。未安装 pydantic 时，插件仍可直接返回 dict。
"""
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object  # type: ignore


if HAS_PYDANTIC:

    class Violation(BaseModel):
        """单条违规记录"""
        file: str = Field(description="违规文件路径")
        line: Optional[int] = Field(default=None, description="违规所在行号")
        context: str = Field(description="违规描述文本（替代旧 error 字段）")
        severity: str = Field(default="error", description="error | warning | info")
        fixable: bool = Field(default=False, description="是否可自动修复")


    class PluginResult(BaseModel):
        """插件统一返回格式（与 plugin-result-schema.json 对齐）"""
        success: bool = Field(
            default=True,
            description="执行是否成功（有 violations 不影响，只有异常时才 false）"
        )
        schema_version: str = Field(
            default="1.0.0",
            const=True,
            description="格式版本号"
        )
        plugin: str = Field(description="插件标识名")
        files_scanned: int = Field(ge=0, description="扫描文件总数")
        files_with_violations: int = Field(ge=0, description="含违规文件数")
        violations_found: int = Field(ge=0, description="违规总项数")
        violations: List[Violation] = Field(default_factory=list)
        metadata: Dict[str, Any] = Field(
            default_factory=dict,
            description="插件自定义扩展字段"
        )

else:
    # 降级：无 pydantic 时提供兼容的纯 dataclass 实现
    from dataclasses import dataclass, field

    @dataclass
    class Violation:
        file: str
        context: str
        line: Optional[int] = None
        severity: str = "error"
        fixable: bool = False

    @dataclass
    class PluginResult:
        plugin: str
        files_scanned: int = 0
        files_with_violations: int = 0
        violations_found: int = 0
        success: bool = True
        schema_version: str = "1.0.0"
        violations: List[Violation] = field(default_factory=list)
        metadata: Dict[str, Any] = field(default_factory=dict)

        def model_dump(self) -> dict:
            """兼容 Pydantic 的 model_dump 接口"""
            return {
                "success": self.success,
                "schema_version": self.schema_version,
                "plugin": self.plugin,
                "files_scanned": self.files_scanned,
                "files_with_violations": self.files_with_violations,
                "violations_found": self.violations_found,
                "violations": [
                    {
                        "file": v.file,
                        "line": v.line,
                        "context": v.context,
                        "severity": v.severity,
                        "fixable": v.fixable,
                    }
                    for v in self.violations
                ],
                "metadata": self.metadata,
            }


# =============================================================================
# LLM Chat Schema Models（与 llm-chat-schema.json 对齐）
# =============================================================================

if HAS_PYDANTIC:

    class ToolCall(BaseModel):
        """工具调用请求（assistant 消息中）"""
        id: str = Field(description="工具调用唯一标识")
        type: str = Field(default="function", const=True)
        function: Dict[str, str] = Field(description="{name, arguments}")

    class Message(BaseModel):
        """OpenAI 兼容消息格式"""
        role: str = Field(description="system | user | assistant | tool")
        content: Optional[str] = Field(default=None, description="消息正文")
        tool_calls: Optional[List[ToolCall]] = Field(default=None, description="工具调用列表")
        tool_call_id: Optional[str] = Field(default=None, description="tool 角色时对应的 tool_call id")

    class LLMChatRequest(BaseModel):
        """LLM Chat Completions 请求体"""
        model: str = Field(description="模型 ID，如 kimi-k2.5")
        messages: List[Message] = Field(description="对话消息列表")
        temperature: float = Field(default=0.7, ge=0.0, le=2.0)
        max_tokens: Optional[int] = Field(default=None, ge=1)
        tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="工具定义列表")

    class LLMChatResponse(BaseModel):
        """LLM Chat Completions 响应体（简化，只取 choices[0]）"""
        choices: List[Dict[str, Any]] = Field(description="choices 数组")
        usage: Optional[Dict[str, int]] = Field(default=None, description="token 用量")

else:
    # 降级：无 pydantic 时提供兼容的纯 dataclass 实现

    @dataclass
    class ToolCall:
        id: str
        type: str = "function"
        function: Dict[str, str] = field(default_factory=dict)

    @dataclass
    class Message:
        role: str
        content: Optional[str] = None
        tool_calls: Optional[List[ToolCall]] = None
        tool_call_id: Optional[str] = None

    @dataclass
    class LLMChatRequest:
        model: str
        messages: List[Message]
        temperature: float = 0.7
        max_tokens: Optional[int] = None
        tools: Optional[List[Dict[str, Any]]] = None

    @dataclass
    class LLMChatResponse:
        choices: List[Dict[str, Any]] = field(default_factory=list)
        usage: Optional[Dict[str, int]] = None
