#!/usr/bin/env python3
"""
插件：项目常量（Constants）
标签：core
依赖：detect_devroot

职责：定义项目级路径常量，从 detect_devroot 模块获取已验证的 devroot 值，
      供其他插件引用。本身不执行探测，只消费 detect_devroot.py 提供的结果。

用法：
    from plugins.constants import DEVROOT, GIT_EXE, GIT_HOME, ENV_FILE
    
    # 或通过 registry 访问
    registry.constants.DEVROOT
"""
from pathlib import Path

# 从 detect_devroot 模块获取已验证的 devroot
# 注意：这里使用延迟加载，避免模块导入时立即探测
try:
    from detect_devroot import get_devroot
    DEVROOT = get_devroot()
except Exception:
    # 如果 devroot 尚未就绪，设为 None，由调用方处理
    DEVROOT = None

# py-plugins/ 目录（自己可控范围）
_PY_PLUGINS_DIR = Path(__file__).parent.resolve()
_SCRIPTS_DIR = _PY_PLUGINS_DIR.parent.resolve()
_TASK_DIR = _SCRIPTS_DIR.parent.resolve()

# 基于 devroot 的常用路径（延迟计算，避免导入时出错）
def _lazy_path(*parts):
    """延迟计算路径，仅在访问时检查 DEVROOT"""
    if DEVROOT is None:
        return None
    return DEVROOT.joinpath(*parts)

# Git 相关路径
GIT_DIR = _lazy_path("venv", "git")
GIT_EXE = _lazy_path("venv", "git", "cmd", "git.exe")
GIT_HOME = _lazy_path("venv", "data-git")

# 配置文件
ENV_FILE = _lazy_path(".env")

# Task 内部路径（不依赖 devroot）
TASK_DIR = _TASK_DIR
SCRIPTS_DIR = _SCRIPTS_DIR
PY_PLUGINS_DIR = _PY_PLUGINS_DIR
