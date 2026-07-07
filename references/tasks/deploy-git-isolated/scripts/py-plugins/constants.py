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


# ========== 敏感内容扫描唯一真源 ==========
import re

# 敏感内容正则（staged 文件内容扫描）
SENSITIVE_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT"),
    (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "私钥"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}", "API Key"),
]


def _is_placeholder_token(token: str) -> bool:
    """判断 token 是否为占位符形式（如 ghp_xxxxxxxx...、sk-xxxxxxxx...）。"""
    if token.startswith(("ghp_", "sk-")):
        sep = "_" if "_" in token else "-"
        suffix = token.split(sep, 1)[1] if sep in token else token
        return set(suffix) <= {"x", "X", "0"}
    return False


def scan_sensitive_content(content: str, filepath: str = "") -> list:
    """
    扫描文本内容中的敏感模式。

    参数:
        content: 文件内容字符串
        filepath: 文件路径（用于生成 violation 信息）

    返回:
        violations 列表，每项格式："filepath:line_num: 发现 类型 — 行内容"
    """
    violations = []
    for pattern, desc in SENSITIVE_PATTERNS:
        for match in re.finditer(pattern, content):
            token = match.group(0)
            if _is_placeholder_token(token):
                continue
            line_num = content[:match.start()].count("\n") + 1
            lines = content.splitlines()
            line_text = lines[line_num - 1] if line_num <= len(lines) else ""
            line_text = line_text.strip()
            if len(line_text) > 80:
                line_text = line_text[:77] + "..."
            prefix = f"{filepath}:" if filepath else ""
            violations.append(f"{prefix}{line_num}: 发现 {desc} — {line_text}")
    return violations
