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
import subprocess
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


def resolve_repo_url(toolchain_root: Path, target: Path = None, git_exe: Path = None) -> str:
    """
    解析目标仓库的 remote URL。

    优先级：
        1. git -C target remote get-url origin
        2. toolchain_root/.env 中的 GITHUB_REPO_URL
        3. 空字符串

    参数:
        toolchain_root: 工具链根目录绝对路径
        target: 操作目标仓库绝对路径。省略时默认等于 toolchain_root
        git_exe: git 可执行文件路径。省略时从 toolchain_root 推导

    返回:
        str: repo_url
    """
    if target is None:
        target = toolchain_root
    if git_exe is None:
        git_exe = toolchain_root / "venv" / "git" / "cmd" / "git.exe"

    # 1. 优先从 target 的 git remote 读取
    if git_exe.exists():
        r = subprocess.run(
            [str(git_exe), "-C", str(target), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()

    # 2. fallback 到 .env
    env = read_env(str(toolchain_root / ".env"))
    repo_url = env.get("GITHUB_REPO_URL", "").strip()
    if repo_url:
        return repo_url

    return ""
