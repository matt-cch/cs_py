#!/usr/bin/env python3
"""
插件：Agent 工具注册（Agent Tools）
标签：agent, core
依赖：无（纯框架，不依赖其它插件）

职责：提供工具注册装饰器与执行框架，供 ReAct Agent 循环调用。
      与 OpenAI function calling 格式对齐。

用法：
    from agent_tools import tool, execute_tool, get_tools_spec

    # 注册工具
    @tool("read_file", "读取文件内容", {"path": {"type": "string", "description": "文件路径"}})
    def read_file(path):
        return Path(path).read_text(encoding="utf-8", errors="replace")

    # 生成 tools 定义给 LLM
    tools_json = get_tools_spec()

    # 执行工具调用（LLM 返回的 tool_calls 格式）
    result = execute_tool(tool_call_dict)
"""
import json
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 插件注册表注入点（由 py_lib 在加载时注入）
__plugin_registry__ = None

# 工具注册表: {name: {"fn": Callable, "description": str, "params": dict}}
_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, params: Dict[str, Any]):
    """
    工具装饰器。注册一个可被 LLM 调用的工具函数。

    参数:
        name: 工具全局唯一名称（LLM 通过此名调用）
        description: 工具功能描述（传给 LLM 的 system prompt）
        params: JSON Schema 格式的参数定义，如
            {"path": {"type": "string", "description": "文件路径"}}

    用法:
        @tool("read_file", "读取文件", {"path": {"type": "string"}})
        def read_file(path):
            return Path(path).read_text()
    """
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[name] = {
            "fn": fn,
            "description": description,
            "params": params,
        }
        return fn
    return decorator


def get_tools_spec() -> List[Dict[str, Any]]:
    """
    生成 OpenAI function calling 格式的 tools 定义列表。

    返回:
        [{"type": "function", "function": {"name": ..., "description": ..., "parameters": ...}}, ...]
    """
    tools = []
    for name, meta in _REGISTRY.items():
        properties = {}
        required = []
        for param_name, param_def in meta["params"].items():
            properties[param_name] = param_def
            # 默认所有参数都必填（简化；如需可选参数，params 中可扩展）
            required.append(param_name)

        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": meta["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        })
    return tools


def execute_tool(tool_call: Dict[str, Any]) -> str:
    """
    执行单个 tool_call。

    参数:
        tool_call: LLM 返回的 tool_call 格式，如
            {
                "id": "call_xxx",
                "type": "function",
                "function": {"name": "read_file", "arguments": '{"path": "/tmp/a.txt"}'}
            }

    返回:
        工具执行结果的字符串表示

    异常:
        RuntimeError: 工具未找到或参数解析失败
    """
    fn_info = tool_call.get("function", {})
    name = fn_info.get("name", "")
    args_json = fn_info.get("arguments", "{}")

    if name not in _REGISTRY:
        return f"[error] 未知工具: {name}"

    try:
        args = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError as e:
        return f"[error] 参数 JSON 解析失败: {e}"

    meta = _REGISTRY[name]
    fn = meta["fn"]

    try:
        result = fn(**args)
        return str(result)
    except Exception as e:
        return f"[error] 工具执行异常 ({name}): {e}"


def list_registered_tools() -> List[str]:
    """返回已注册工具名称列表（调试用）"""
    return list(_REGISTRY.keys())


# =============================================================================
# 内置工具（参考 SubZeroClaw：shell 是一切工具的入口）
# =============================================================================

@tool("read_file", "读取本地文件内容", {
    "path": {"type": "string", "description": "要读取的文件绝对路径"}
})
def _read_file(path: str) -> str:
    """读取文件内容"""
    p = Path(path)
    if not p.exists():
        return f"[error] 文件不存在: {path}"
    if not p.is_file():
        return f"[error] 路径不是文件: {path}"
    return p.read_text(encoding="utf-8", errors="replace")


@tool("bash", "执行 shell 命令", {
    "command": {"type": "string", "description": "要执行的 shell 命令字符串"}
})
def _bash(command: str) -> str:
    """执行 shell 命令，返回 stdout + stderr 合并输出"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr
        output += f"\n[exit:{result.returncode}]"
        return output
    except subprocess.TimeoutExpired:
        return "[error] 命令执行超时 (60s)"
    except Exception as e:
        return f"[error] 命令执行异常: {e}"


def _resolve_devroot() -> Path:
    """获取 devroot（优先 registry，其次环境变量）"""
    if __plugin_registry__ is not None and hasattr(__plugin_registry__, "devroot"):
        return Path(__plugin_registry__.devroot)
    devroot_env = os.environ.get("DEVROOT", "")
    if devroot_env:
        return Path(devroot_env)
    return Path.cwd()


def _get_allowed_write_dirs() -> List[Path]:
    """返回允许写入的目录白名单"""
    devroot = _resolve_devroot()
    allowed = [
        devroot / "venv" / "tmp",
    ]
    # 系统临时目录
    for env_name in ("TMP", "TEMP", "TMPDIR"):
        val = os.environ.get(env_name, "")
        if val:
            allowed.append(Path(val))
    return allowed


def _is_path_under_any(target: Path, candidates: List[Path]) -> bool:
    """检查 target 是否位于 candidates 中任一目录下（解析为绝对路径后比较）"""
    try:
        target_abs = target.resolve()
    except (OSError, ValueError):
        return False
    for c in candidates:
        try:
            if str(target_abs).startswith(str(c.resolve())):
                return True
        except (OSError, ValueError):
            continue
    return False


@tool("write_file", "写入文件内容（仅限 tmp 目录）", {
    "path": {"type": "string", "description": "目标文件绝对路径。仅限 devroot/venv/tmp/ 或系统 TMP/TEMP 目录。"},
    "content": {"type": "string", "description": "要写入的内容"},
})
def _write_file(path: str, content: str) -> str:
    """写入文件（覆盖模式）。安全策略：只允许写入 tmp 目录。"""
    p = Path(path)
    allowed_dirs = _get_allowed_write_dirs()

    if not _is_path_under_any(p, allowed_dirs):
        return (
            f"[error] 写入被拒绝：路径不在允许的白名单目录内。\n"
            f"  目标: {path}\n"
            f"  允许: {', '.join(str(d) for d in allowed_dirs)}"
        )

    try:
        # 确保父目录存在
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"[ok] 已写入 {path} ({len(content)} 字节)"
    except Exception as e:
        return f"[error] 写入失败: {e}"
