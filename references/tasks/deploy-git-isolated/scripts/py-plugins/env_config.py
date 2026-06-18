#!/usr/bin/env python3
"""
插件：环境配置读取（Env Config）
标签：core

职责：读取 .env 文件，提供类型化的配置访问。

用法：
    from plugins.env_config import read_env
    
    config = read_env()
    user_name = config.get("GIT_USER_NAME")
"""
import os
from pathlib import Path


def read_env(env_file: str = None) -> dict:
    """
    读取 .env 文件，返回键值对字典。
    
    参数:
        env_file: .env 文件路径。如未传入，尝试从环境变量或默认位置查找。
    
    返回:
        dict: 环境变量键值对
    """
    if not env_file:
        # 尝试从环境变量获取
        env_file = os.environ.get("DEPLOY_GIT_ENV_FILE", "")
        if not env_file:
            # 尝试从 devroot 推导
            devroot = os.environ.get("DEVROOT", "")
            if devroot:
                env_file = Path(devroot) / ".env"
            else:
                # 当前目录查找
                env_file = Path(".env")
    
    env_path = Path(env_file)
    if not env_path.exists():
        return {}
    
    config = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip('"').strip("'")
    
    return config


def get_required_env(env_file: str = None, *keys: str) -> dict:
    """
    读取 .env 并检查必填项。
    
    参数:
        env_file: .env 文件路径
        *keys: 必填的环境变量名
    
    返回:
        dict: 环境变量键值对
    
    异常:
        ValueError: 必填项缺失
    """
    config = read_env(env_file)
    missing = [k for k in keys if not config.get(k)]
    if missing:
        raise ValueError(f"缺少必填环境变量: {missing}")
    return config
