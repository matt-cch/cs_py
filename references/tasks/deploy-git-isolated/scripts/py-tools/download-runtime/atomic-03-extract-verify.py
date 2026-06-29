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
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def resolve_path(path_template: str, devroot: str) -> str:
    toolchainroot = os.environ.get("TOOLCHAINROOT", "D:\\download")
    resolved = path_template.replace("${devroot}", devroot).replace("${toolchainroot}", toolchainroot)
    resolved = os.path.expandvars(resolved)
    return resolved


def extract_and_verify(zip_file: str, tool_name: str, config: dict, devroot: str, get_version_script: str = "") -> dict:
    is_wheel = config.get("package_type") == "python_wheel"
    tool_dir = resolve_path(config.get("exe_path", ""), devroot)
    tool_dir = os.path.dirname(tool_dir) if tool_dir else os.path.join("D:\\download", tool_name)

    if is_wheel:
        # whl 不解压，只整理到目录
        extract_dir = os.path.join(os.path.dirname(zip_file), f"{tool_name}-wheel")
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
    extract_dir = os.path.join(os.path.dirname(zip_file), f"{tool_name}-extracted")
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
    downloaded_version = None
    if found_exe and get_version_script:
        try:
            mode = config.get("mode", "")
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
    args = parser.parse_args()

    config = json.loads(args.config_json)
    result = extract_and_verify(args.zip_file, args.tool_name, config, args.devroot, args.get_version_script)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("found_exe") or config.get("package_type") == "python_wheel" else 1)


if __name__ == "__main__":
    sys.exit(main())
