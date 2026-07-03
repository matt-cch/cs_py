#!/usr/bin/env python3
r"""
Plugin: runtime_naming
标签：runtime, naming, core
职责：运行时工具下载产物的命名唯一真源。
      所有 ZIP/解压目录的命名规则集中在此处，下游脚本消费，不各自拼接。

用法（通过 py_lib 统一入口加载）：
    from py_lib import load_plugins
    registry = load_plugins(devroot=..., tags=["naming"])
    paths = registry.runtime_naming.get_download_paths(
        download_dir="D:\\download",
        tool_name="git",
        target_version="2.55.0.windows.2",
        asset_name=upstream_result.get("asset_name", ""),
        url_template=tool.get("download_url_template", ""),
        package_type="zip"
    )
    # paths["asset_path"]    → D:\download\MinGit-2.55.0.2-64-bit.zip
    # paths["extract_dir_path"] → D:\download\git-2.55.0.windows.2-extracted
"""
import os


def get_asset_name(tool_name: str, target_version: str,
                   asset_name: str = "", url_template: str = "",
                   package_type: str = "zip") -> str:
    """
    唯一真源：产物文件名生成（支持任意扩展名）。
    优先级：上游实测 asset_name > url_template 推导 > package_type 默认。
    """
    if asset_name:              # P0: 上游实测返回（含原始扩展名）
        return asset_name

    if url_template:            # P1: 从模板推导（保留模板中的扩展名）
        name_template = url_template.split("/")[-1]
        if "{version}" in name_template:
            return name_template.replace("{version}", target_version)
        # 模板不含 {version}，直接返回模板文件名
        return name_template or f"{tool_name}-{target_version}"

    # P2 Fallback: 根据 package_type 推断扩展名
    ext_map = {
        "zip": ".zip",
        "exe": ".exe",
        "msi": ".msi",
        "python_wheel": ".whl",
        "tar": ".tar.gz",
    }
    ext = ext_map.get(package_type, f".{package_type}" if package_type else ".zip")
    return f"{tool_name}-{target_version}{ext}"


def get_extract_dir(tool_name: str, target_version: str) -> str:
    """唯一真源：解压/部署目录名生成。"""
    return f"{tool_name}-{target_version}-extracted"


def get_download_paths(download_dir: str, tool_name: str, target_version: str,
                       asset_name: str = "", url_template: str = "",
                       package_type: str = "zip") -> dict:
    """唯一真源：完整路径生成。"""
    asset = get_asset_name(tool_name, target_version, asset_name, url_template, package_type)
    extract = get_extract_dir(tool_name, target_version)
    return {
        "asset_name": asset,
        "asset_path": os.path.join(download_dir, asset),
        "extract_dir_name": extract,
        "extract_dir_path": os.path.join(download_dir, extract),
    }
