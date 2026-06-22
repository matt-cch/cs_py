#!/usr/bin/env python3
"""
插件：Provider 配置真源（Provider Config）
标签：core, llm
依赖：无（纯配置读取，不依赖其它插件）

职责：从 OpenCode config.json 读取 provider 配置，作为项目所有 LLM 调用的统一配置真源。
      同时支持 .env 和环境变量覆盖，形成三层回退：
      环境变量 > .env > OpenCode config.json > 硬编码默认值

用法：
    from provider_config import get_provider

    cfg = get_provider()
    print(cfg["api_key"], cfg["base_url"], cfg["model"], cfg["temperature"])
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# 插件注册表注入点（由 py_lib 在加载时注入）
__plugin_registry__ = None


def _resolve_devroot() -> Optional[Path]:
    """从 registry 或环境变量获取 devroot"""
    if __plugin_registry__ is not None and hasattr(__plugin_registry__, "devroot"):
        return Path(__plugin_registry__.devroot)
    devroot_env = os.environ.get("DEVROOT", "")
    if devroot_env:
        return Path(devroot_env)
    return None


def _read_env_file(env_path: Path) -> Dict[str, str]:
    """简单 .env 解析"""
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


def _read_opencode_config(devroot: Path) -> Optional[Dict[str, Any]]:
    """
    读取 OpenCode config.json。

    返回:
        解析后的 dict，若文件不存在或解析失败返回 None
    """
    config_path = devroot / "venv" / ".opencode" / "config.json"
    if not config_path.exists():
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _resolve_api_key(raw_key: str, base_dir: Path) -> str:
    """
    解析 apiKey 字段，支持 {file:./xxx} 引用格式。

    参数:
        raw_key: config.json 中的 apiKey 值，如 "{file:./moonshot-key.txt}" 或纯字符串
        base_dir: config.json 所在目录，用于解析相对路径
    """
    if raw_key.startswith("{file:") and raw_key.endswith("}"):
        file_path = raw_key[6:-1]  # 提取 ./moonshot-key.txt
        # 去掉开头的 ./ 或 ../
        file_path = file_path.lstrip("./")
        key_file = base_dir / file_path
        if key_file.exists():
            return key_file.read_text(encoding="utf-8").strip()
        return ""
    return raw_key


def _parse_model_string(model_str: str) -> tuple[str, str]:
    """
    解析 OpenCode 的 model 字段格式 "provider/model_id"。

    返回:
        (provider_name, model_id)
    """
    if "/" in model_str:
        parts = model_str.split("/", 1)
        return parts[0], parts[1]
    return "", model_str


def _get_env_provider(devroot: Path, env_file: Optional[str]) -> Dict[str, Any]:
    """从环境变量 + .env 文件读取 provider 配置（env 分支）"""
    env_path = Path(env_file) if env_file else devroot / ".env"
    env_config = _read_env_file(env_path)

    # 环境变量最高优先级
    api_key = (
        os.environ.get("MOONSHOT_API_KEY", "")
        or os.environ.get("CORECODER_API_KEY", "")
        or os.environ.get("OPENAI_API_KEY", "")
    )
    base_url = (
        os.environ.get("MOONSHOT_BASE_URL", "")
        or os.environ.get("CORECODER_BASE_URL", "")
    )
    model = os.environ.get("CORECODER_MODEL", "")

    # .env 回退
    if not api_key:
        api_key = (
            env_config.get("MOONSHOT_API_KEY", "")
            or env_config.get("CORECODER_API_KEY", "")
            or env_config.get("OPENAI_API_KEY", "")
        )
    if not base_url:
        base_url = (
            env_config.get("MOONSHOT_BASE_URL", "")
            or env_config.get("CORECODER_BASE_URL", "")
        )
    if not model:
        model = env_config.get("CORECODER_MODEL", "")

    return {
        "provider": "moonshot",
        "model": model or "kimi-k2.6",
        "api_key": api_key,
        "base_url": (base_url or "https://api.moonshot.cn/v1").rstrip("/"),
        "temperature": None,
        "max_tokens": None,
        "thinking": None,
        "context_limit": 0,
        "output_limit": 0,
    }


def _get_opencode_provider(devroot: Path) -> Dict[str, Any]:
    """从 OpenCode config.json 读取 provider 配置（config.json 分支）"""
    opencode_cfg = _read_opencode_config(devroot)
    if not opencode_cfg:
        return {}

    model_str = opencode_cfg.get("model", "")
    provider_name, model_id = _parse_model_string(model_str)

    providers = opencode_cfg.get("provider", {})
    provider_cfg = providers.get(provider_name, {})

    # baseURL / apiKey
    provider_opts = provider_cfg.get("options", {})
    base_url = provider_opts.get("baseURL", "")
    raw_key = provider_opts.get("apiKey", "")
    api_key = ""
    if raw_key:
        config_dir = devroot / "venv" / ".opencode"
        api_key = _resolve_api_key(raw_key, config_dir)

    # 模型级配置
    models = provider_cfg.get("models", {})
    model_cfg = models.get(model_id, {})
    model_opts = model_cfg.get("options", {})
    temperature = model_opts.get("temperature")
    thinking = model_opts.get("thinking")
    max_tokens = model_opts.get("max_tokens")

    limits = model_cfg.get("limit", {})
    context_limit = limits.get("context", 0)
    output_limit = limits.get("output", 0)

    return {
        "provider": provider_name or "moonshot",
        "model": model_id or "kimi-k2.6",
        "api_key": api_key,
        "base_url": (base_url or "https://api.moonshot.cn/v1").rstrip("/"),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "thinking": thinking,
        "context_limit": context_limit,
        "output_limit": output_limit,
    }


def get_provider(
    env_file: Optional[str] = None,
    devroot: Optional[Path] = None,
    source: str = "auto",
) -> Dict[str, Any]:
    """
    获取统一 provider 配置。

    参数:
        env_file: 指定 .env 文件路径（默认 devroot/.env）
        devroot: 开发根目录
        source: 配置来源策略
            - "auto": 先尝试 env 分支（环境变量 + .env），若 api_key 为空则回退到 config.json 分支
            - "env": 强制使用 env 分支（环境变量 + .env），不读 config.json
            - "config_json": 强制使用 config.json 分支，不读 .env
            - "merge": env 分支覆盖 config.json 分支的凭证字段，但保留 config.json 的模型参数

    返回:
        {
            "provider": str,       # 如 "moonshot"
            "model": str,          # 如 "kimi-k2.6"
            "api_key": str,
            "base_url": str,
            "temperature": float | None,
            "max_tokens": int | None,
            "thinking": dict | None,
            "context_limit": int,
            "output_limit": int,
        }
    """
    if devroot is None:
        devroot = _resolve_devroot() or Path.cwd()
    devroot = Path(devroot)

    # ---------- config.json 分支 ----------
    oc_cfg = _get_opencode_provider(devroot)

    # ---------- env 分支 ----------
    env_cfg = _get_env_provider(devroot, env_file)

    if source == "config_json":
        return oc_cfg or env_cfg  # config.json 不存在时回退 env

    if source == "env":
        return env_cfg

    if source == "merge":
        # env 覆盖凭证，config.json 提供模型参数
        merged = dict(oc_cfg)
        if env_cfg.get("api_key"):
            merged["api_key"] = env_cfg["api_key"]
        if env_cfg.get("base_url"):
            merged["base_url"] = env_cfg["base_url"]
        if env_cfg.get("model") and env_cfg["model"] != "kimi-k2.6":
            merged["model"] = env_cfg["model"]
        return merged

    # source == "auto": 先 env，env 无 key 则回退 config.json
    if env_cfg.get("api_key"):
        return env_cfg
    return oc_cfg or env_cfg
