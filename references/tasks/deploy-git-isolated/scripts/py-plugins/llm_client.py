#!/usr/bin/env python3
"""
插件：LLM 客户端（LLM Client）
标签：core, llm
依赖：env_config

职责：封装 OpenAI 兼容格式的 Chat Completions HTTP 调用，提供统一接口供 Agent 模块消费。
      与 schema/json/llm-chat-schema.json 对齐输入输出契约。

用法：
    import sys
    sys.path.insert(0, r"...\\scripts")
    from py_lib import load_plugins
    registry = load_plugins(devroot="D:/pjt/cursor/cs_py", tags=["llm"])

    # 单次调用
    msg, finish_reason = registry.llm_client.chat(
        messages=[
            {"role": "system", "content": "你是代码审查员"},
            {"role": "user", "content": "总结这段 diff"},
        ],
        model="kimi-k2.5",
        temperature=0.3,
    )
    print(msg["content"])

    # 带 tools 的调用
    msg, finish_reason = registry.llm_client.chat(
        messages=[...],
        tools=[{"type": "function", "function": {"name": "shell", ...}}],
    )
"""
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# 插件注册表注入点（由 py_lib 在加载时注入）
__plugin_registry__ = None


# ---------- 默认配置 ----------
DEFAULT_MODEL = "kimi-k2.6"
DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_TIMEOUT = 120.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF = 1.0  # 秒，指数退避基数


def _get_devroot() -> Optional[Path]:
    """从 registry 或环境变量获取 devroot"""
    if __plugin_registry__ is not None and hasattr(__plugin_registry__, "devroot"):
        return Path(__plugin_registry__.devroot)
    devroot_env = os.environ.get("DEVROOT", "")
    if devroot_env:
        return Path(devroot_env)
    return None


def _read_env_file(env_path: Path) -> Dict[str, str]:
    """简单 .env 解析（不依赖 python-dotenv）"""
    config: Dict[str, str] = {}
    if not env_path.exists():
        return config
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def get_config(source: str = "auto") -> Dict[str, Any]:
    """
    读取 LLM 配置。统一由 provider_config 插件提供。

    参数:
        source: 配置来源策略（透传给 provider_config.get_provider）
            - "auto": 先 env 分支，无 key 则回退 config.json
            - "env": 强制 env 分支
            - "config_json": 强制 config.json 分支
            - "merge": env 覆盖凭证 + config.json 提供模型参数

    返回:
        {
            "api_key": str,
            "base_url": str,
            "model": str,
            "timeout": float,
            "temperature": float | None,
            "max_tokens": int | None,
            "thinking": dict | None,
        }
    """
    # 通过 registry 调用 provider_config（py_lib 拓扑排序后已加载）
    provider_cfg: Dict[str, Any] = {}
    if __plugin_registry__ is not None and hasattr(__plugin_registry__, "provider_config"):
        provider_cfg = __plugin_registry__.provider_config.get_provider(source=source)
    else:
        # fallback: 直接 import（支持独立运行）
        try:
            import provider_config
            devroot = _get_devroot()
            provider_cfg = provider_config.get_provider(devroot=devroot, source=source)
        except Exception:
            provider_cfg = {}

    timeout_str = os.environ.get("NANOBOT_TIMEOUT", "")

    return {
        "api_key": provider_cfg.get("api_key", ""),
        "base_url": provider_cfg.get("base_url", DEFAULT_BASE_URL).rstrip("/"),
        "model": provider_cfg.get("model", DEFAULT_MODEL),
        "timeout": float(timeout_str) if timeout_str else DEFAULT_TIMEOUT,
        "temperature": provider_cfg.get("temperature"),
        "max_tokens": provider_cfg.get("max_tokens"),
        "thinking": provider_cfg.get("thinking"),
    }


def chat(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    timeout: Optional[float] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    provider_cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    调用 LLM Chat Completions API（OpenAI 兼容格式）。

    参数:
        messages: 消息列表，每项为 {"role": "...", "content": "..."} 格式
        model: 模型 ID，None 时取配置默认值
        temperature: 采样温度，None 时不传（让 API 用默认值）。
                     注意：Moonshot kimi-k2.6 thinking 开启时只允许 temperature=1
        max_tokens: 最大生成 token 数
        tools: 可选的工具定义列表（OpenAI function calling 格式）
        timeout: 单次请求超时秒数
        max_retries: 最大重试次数

    返回:
        (message_dict, finish_reason)
        message_dict: {"role": "assistant", "content": "...", "tool_calls": [...]}
        finish_reason: "stop" | "length" | "tool_calls" | None

    异常:
        RuntimeError: 配置缺失或 API 调用最终失败
        httpx.HTTPStatusError: HTTP 非 2xx 且重试耗尽
    """
    cfg = provider_cfg if provider_cfg is not None else get_config()
    api_key = cfg.get("api_key", "")
    if not api_key:
        raise RuntimeError("LLM API key 未配置。请在 .env 中设置 MOONSHOT_API_KEY / CORECODER_API_KEY，或通过环境变量传入。")

    effective_model = model or cfg.get("model", DEFAULT_MODEL)
    effective_timeout = timeout or cfg.get("timeout", DEFAULT_TIMEOUT)

    # temperature 优先级：显式参数 > provider_cfg > None（不传）
    effective_temperature = temperature
    if effective_temperature is None and provider_cfg is not None:
        effective_temperature = provider_cfg.get("temperature")

    payload: Dict[str, Any] = {
        "model": effective_model,
        "messages": messages,
    }
    if effective_temperature is not None:
        payload["temperature"] = effective_temperature
    # max_tokens 优先级：显式参数 > provider_cfg.context_limit > None（不传）
    effective_max_tokens = max_tokens
    if effective_max_tokens is None and provider_cfg is not None:
        effective_max_tokens = provider_cfg.get("context_limit")
    if effective_max_tokens is not None:
        payload["max_tokens"] = effective_max_tokens
    if tools is not None:
        payload["tools"] = tools
    # 传递 thinking 参数（如 provider_cfg 中有）
    thinking = cfg.get("thinking") if provider_cfg is not None else None
    if thinking is not None:
        payload["thinking"] = thinking

    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=effective_timeout,
            )
            response.raise_for_status()
            data = response.json()

            # 解析 OpenAI 兼容响应格式
            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError(f"LLM 响应不含 choices: {json.dumps(data, ensure_ascii=False)[:500]}")

            choice = choices[0]
            message = choice.get("message", {})
            finish_reason = choice.get("finish_reason")

            return message, finish_reason

        except httpx.HTTPStatusError as e:
            last_err = e
            # 4xx 客户端错误不重试（除 429 rate limit）
            if e.response.status_code < 500 and e.response.status_code != 429:
                raise
            if attempt < max_retries:
                wait = DEFAULT_BACKOFF * (2 ** (attempt - 1))
                print(f"[LLM Client] HTTP {e.response.status_code}，第 {attempt} 次重试，等待 {wait:.1f}s...")
                time.sleep(wait)
            continue

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_err = e
            if attempt < max_retries:
                wait = DEFAULT_BACKOFF * (2 ** (attempt - 1))
                print(f"[LLM Client] 网络异常，第 {attempt} 次重试，等待 {wait:.1f}s...")
                time.sleep(wait)
            continue

    raise RuntimeError(f"LLM 调用在 {max_retries} 次重试后仍失败: {last_err}")


def chat_simple(
    prompt: str,
    system: str = "你是一个 helpful assistant",
    **kwargs,
) -> str:
    """
    极简单次调用：传入 prompt，返回 assistant content 字符串。

    参数:
        prompt: 用户输入
        system: system prompt
        **kwargs: 透传给 chat() 的额外参数（model, temperature, max_tokens 等）

    返回:
        assistant 的 content 字符串
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    message, _ = chat(messages, **kwargs)
    return message.get("content", "")
