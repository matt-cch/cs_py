#!/usr/bin/env python3
r"""
download-runtime/atomic-03-extract-verify.py — 解压与验证原子（v1.0.0）
标签：atomic, runtime
职责：解压 ZIP → 定位可执行文件 → 验证版本

用法：
    python atomic-03-extract-verify.py --zip-file "...\\node.zip" --tool-name node --config-json '{...}' --devroot "..."

输出（stdout JSON）：
    {"extract_dir":"...","found_exe":"...\\node.exe","downloaded_version":"26.4.0","error":null}
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import atexit
import zipfile
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
# atomic-03-extract-verify.py 在 py-tools/download-runtime/ 下，py-plugins 需上两级到 scripts/
_PLUGIN_DIR = str(Path(__file__).resolve().parents[2] / "py-plugins")
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)


def resolve_path(path_template: str, devroot: str) -> str:
    toolchainroot = os.environ.get("TOOLCHAINROOT", "D:\\download")
    resolved = path_template.replace("${devroot}", devroot).replace("${toolchainroot}", toolchainroot)
    resolved = os.path.expandvars(resolved)
    return resolved


def extract_and_verify(zip_file: str, tool_name: str, config: dict, devroot: str,
                       get_version_script: str = "", target_version: str = "",
                       extract_dir: str = "") -> dict:
    is_wheel = config.get("package_type") == "python_wheel"
    tool_dir = resolve_path(config.get("exe_path", ""), devroot)
    tool_dir = os.path.dirname(tool_dir) if tool_dir else os.path.join("D:\\download", tool_name)

    # 版本后缀用于命名（若外部未传入 extract_dir，则自行计算）
    ver_suffix = f"-{target_version}" if target_version else ""

    if is_wheel:
        # whl 不解压，只整理到目录
        extract_dir = extract_dir or os.path.join(os.path.dirname(zip_file), f"{tool_name}{ver_suffix}-wheel")
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir, exist_ok=True)
        dest_whl = os.path.join(extract_dir, os.path.basename(zip_file))
        shutil.move(zip_file, dest_whl)
        return {
            "extract_dir": extract_dir,
            "found_exe": None,
            "downloaded_version": config.get("upstream_version", ""),
            "error": None,
        }

    # ZIP 解压
    extract_dir = extract_dir or os.path.join(os.path.dirname(zip_file), f"{tool_name}{ver_suffix}-extracted")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file, "r") as z:
        z.extractall(extract_dir)

    # 定位可执行文件
    exe_name = Path(resolve_path(config.get("exe_path", ""), devroot)).name
    found_exe = None
    if exe_name:
        for root, dirs, files in os.walk(extract_dir):
            if exe_name in files:
                found_exe = os.path.join(root, exe_name)
                break

    # 验证版本
    # 优先级：本地 runtime_version 插件 > 用户自定义脚本（扩展点）> 上游版本声明
    downloaded_version = None
    if found_exe:
        mode = config.get("mode", "")
        if mode:
            import runtime_version
            rv_result = runtime_version.detect(
                exe_path=found_exe,
                mode=mode,
                devroot=devroot,
                version_arg=config.get("version_arg", "--version")
            )
            downloaded_version = rv_result.get("version")

        # 用户显式传入自定义脚本时作为 fallback 扩展点
        if not downloaded_version and get_version_script:
            try:
                python_exe = os.path.join(devroot, "venv", "py", "python.exe")
                cmd = [python_exe, get_version_script, "--mode", mode, "--target", found_exe]
                if mode == "subprocess-version":
                    cmd.append(f"--version-arg={config.get('version_arg', '--version')}")
                result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
                data = json.loads(result.stdout.strip())
                downloaded_version = data.get("version") if data.get("success") else None
            except Exception:
                pass

    if not downloaded_version:
        downloaded_version = config.get("upstream_version", "")

    return {
        "extract_dir": extract_dir,
        "found_exe": found_exe,
        "downloaded_version": downloaded_version,
        "error": None if found_exe else f"未找到可执行文件: {exe_name}",
    }


def main():
    parser = argparse.ArgumentParser(description="解压与验证原子")
    parser.add_argument("--zip-file", required=True, help="ZIP 文件路径")
    parser.add_argument("--tool-name", required=True, help="工具名")
    parser.add_argument("--config-json", required=True, help="配置 JSON 字符串")
    parser.add_argument("--devroot", required=True, help="devroot 绝对路径")
    parser.add_argument("--get-version-script", default="", help="get-runtime-version.py 路径")
    parser.add_argument("--target-version", default="", help="目标版本号（用于命名解压目录）")
    parser.add_argument("--extract-dir", default="", help="解压目录路径（由调用方统一生成，覆盖内部命名）")
    args = parser.parse_args()

    config = json.loads(args.config_json)
    result = extract_and_verify(
        args.zip_file, args.tool_name, config, args.devroot,
        args.get_version_script, args.target_version, args.extract_dir
    )
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("found_exe") or config.get("package_type") == "python_wheel" else 1)


if __name__ == "__main__":
    sys.exit(main())
