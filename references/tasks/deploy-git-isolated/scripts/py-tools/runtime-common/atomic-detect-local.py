#!/usr/bin/env python3
r"""
runtime-common/atomic-detect-local.py — 本地运行时检测原子（v1.0.0）
标签：atomic, runtime
职责：检测单个工具的本地 exe 存在性和实际版本号

用法：
    python atomic-detect-local.py --config-json '{"exe_path":"${devroot}\\venv\\node\\node.exe","mode":"subprocess-version","version_arg":"--version"}' --devroot "D:\\pjt\\vscode\\vsc_py" --tool-name node --index-path ".../verified-runtime-index.json"

输出（stdout JSON）：
    {"exe_exists":true,"resolved_path":"D:\\pjt\\vscode\\vsc_py\\venv\\node\\node.exe","local_version":"26.4.0","error":null}
"""
import argparse
import json
import os
import re
import subprocess
import sys
import atexit
from pathlib import Path

# 编码处理闭环：保存原始编码 → 切换 UTF-8 → 退出时恢复
_original_stdout_encoding = sys.stdout.encoding
_original_stderr_encoding = sys.stderr.encoding

def _restore_encoding():
    try:
        if sys.stdout.encoding != _original_stdout_encoding:
            sys.stdout.reconfigure(encoding=_original_stdout_encoding)
    except Exception:
        pass
    try:
        if sys.stderr.encoding != _original_stderr_encoding:
            sys.stderr.reconfigure(encoding=_original_stderr_encoding)
    except Exception:
        pass

atexit.register(_restore_encoding)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 引入 task 本地 runtime_version 插件（消除对 schema/ 层工具的默认依赖）
# atomic-detect-local.py 在 py-tools/runtime-common/ 下，py-plugins 需上两级到 scripts/
_PLUGIN_DIR = str(Path(__file__).resolve().parents[2] / "py-plugins")
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)


# =============================================================================
# 路径解析
# =============================================================================

def resolve_path(path_template: str, devroot: str) -> str:
    toolchainroot = os.environ.get("TOOLCHAINROOT", "D:\\download")
    resolved = path_template.replace("${devroot}", devroot).replace("${toolchainroot}", toolchainroot)
    resolved = os.path.expandvars(resolved)
    return resolved


# =============================================================================
# 版本检测（复用 get-runtime-version.py）
# =============================================================================

def _get_version_via_script(devroot: str, script_path: str, mode: str, target: str, **kwargs) -> str:
    python_exe = os.path.join(devroot, "venv", "py", "python.exe")
    cmd = [python_exe, script_path, "--mode", mode, "--target", target]
    if mode == "subprocess-version":
        cmd.append(f"--version-arg={kwargs.get('version_arg', '--version')}")
    elif mode in ("package-import", "python-self"):
        interpreter = kwargs.get("interpreter", python_exe)
        cmd.extend(["--interpreter", interpreter])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        data = json.loads(result.stdout.strip())
        return data.get("version") if data.get("success") else None
    except Exception:
        return None


def _fallback_version(exe: str) -> str:
    """兜底：直接 exe --version，正则提取版本号"""
    try:
        result = subprocess.run([exe, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        output = result.stdout.strip() or result.stderr.strip()
        if not output:
            return None
        match = re.search(r"v?(\d+\.\d+\.\d+(?:[-\w.]*))?", output)
        return match.group(1) if match and match.group(1) else None
    except Exception:
        return None


# =============================================================================
# 主逻辑
# =============================================================================

def detect_local(config: dict, devroot: str, tool_name: str, index_path: str = "", get_version_script: str = "") -> dict:
    mode = config.get("mode", "")
    exe_path = resolve_path(config.get("exe_path", ""), devroot)

    result = {
        "exe_exists": False,
        "exe_path": exe_path,
        "resolved_path": exe_path,
        "local_version": None,
        "fallback_version": None,
        "error": None,
        "candidate_hit": None,
    }

    # 1. 检查 exe 存在性（支持 fallback_paths）
    actual_exe = exe_path
    if not os.path.exists(actual_exe):
        for fallback in config.get("fallback_paths", []):
            fb = resolve_path(fallback, devroot)
            if os.path.exists(fb):
                actual_exe = fb
                result["exe_path"] = actual_exe
                result["resolved_path"] = actual_exe
                break

    # 2. 主路径 + fallback 全 miss，扫描 candidate_paths（索引兜底）
    if not os.path.exists(actual_exe) and index_path and tool_name:
        candidates = _load_candidate_paths(index_path, tool_name)
        for candidate in candidates:
            if isinstance(candidate, dict):
                candidate_dir = resolve_path(candidate.get("path", ""), devroot)
                candidate_exe_name = candidate.get("exe_name", "")
                candidate_full = os.path.join(candidate_dir, candidate_exe_name) if candidate_exe_name else candidate_dir
            else:
                candidate_full = resolve_path(candidate, devroot)
            if os.path.exists(candidate_full):
                actual_exe = candidate_full
                result["exe_path"] = actual_exe
                result["resolved_path"] = actual_exe
                result["candidate_hit"] = candidate if isinstance(candidate, dict) else candidate_full
                break

    result["exe_exists"] = os.path.exists(actual_exe)
    if not result["exe_exists"]:
        result["error"] = "可执行文件不存在"
        return result

    # 3. 检测版本
    # 优先级：用户自定义脚本（扩展点）> 本地 runtime_version 插件 > fallback 正则
    version = None
    if get_version_script and mode:
        # 用户显式传入自定义检测脚本（扩展点，保持向后兼容）
        version = _get_version_via_script(devroot, get_version_script, mode, actual_exe,
                                          version_arg=config.get("version_arg", "--version"),
                                          interpreter=resolve_path(config.get("interpreter", ""), devroot) if config.get("interpreter") else "")
    elif mode:
        # 默认走本地 runtime_version 插件，消除对 schema/ 层工具的耦合
        import runtime_version
        rv_result = runtime_version.detect(
            exe_path=actual_exe,
            mode=mode,
            devroot=devroot,
            version_arg=config.get("version_arg", "--version"),
            interpreter=resolve_path(config.get("interpreter", ""), devroot) if config.get("interpreter") else "",
            package_name=config.get("package_name", "")
        )
        version = rv_result.get("version")

    # 4. 兜底
    if not version:
        version = _fallback_version(actual_exe)
        if version:
            result["fallback_version"] = version

    result["local_version"] = version
    if not version:
        result["error"] = "版本检测失败"

    return result


def _load_candidate_paths(index_path: str, tool_name: str) -> list:
    if not os.path.exists(index_path):
        return []
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        return index.get("toolchain", {}).get(tool_name, {}).get("candidate_paths", [])
    except Exception:
        return []


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="本地运行时检测原子")
    parser.add_argument("--config-json", required=True, help="本地配置 JSON 字符串")
    parser.add_argument("--devroot", required=True, help="devroot 绝对路径")
    parser.add_argument("--tool-name", default="", help="工具名（用于 candidate_paths 兜底）")
    parser.add_argument("--index-path", default="", help="verified-runtime-index.json 路径")
    parser.add_argument("--get-version-script", default="", help="get-runtime-version.py 绝对路径")
    args = parser.parse_args()

    config = json.loads(args.config_json)
    result = detect_local(config, args.devroot, args.tool_name, args.index_path, args.get_version_script)

    # 输出 JSON（无额外 stdout 干扰）
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["exe_exists"] else 1)


if __name__ == "__main__":
    sys.exit(main())
