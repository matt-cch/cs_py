#!/usr/bin/env python3
"""
插件：归档配置（Archive Config）
标签：archive, core

职责：定义归档分组的配置常量、7z 工具路径解析、输出目录。

用法：
    from archive_config import get_group_config, find_7z_exe
    cfg = get_group_config("cs_py", devroot=Path("D:/pjt/cursor/cs_py"))
    print(cfg["zip"])  # 输出 zip 绝对路径
"""
import json
import os
from pathlib import Path

# 默认 7z 路径（fallback）
_DEFAULT_7Z_PATH = Path(r"D:\download\7-Zip\7z.exe")

# verified-runtime-index.json 路径模板
_RUNTIME_INDEX_TEMPLATE = Path(r"${devroot}") / "references" / "runtime" / "verified-runtime-index.json"

# 归档分组定义
# 注意：cwd 是 7z 压缩时的工作目录，必须与 listfile 中的路径基准一致
GROUPS_SPEC = {
    "cs_py": {
        "arcname": "cs_py",
        "whitelist": [],
        "blacklist": ["venv/", "cs_py/*.zip", "cs_py/*.7z"],
        # cwd 为 devroot.parent，因为 listfile 中的路径是 "cs_py\\..."
        "cwd_parent_level": 1,
        "zip_name": "cs_py",
    },
    "venv": {
        "arcname": "venv",
        "whitelist": [".opencode", "data-opencode", "version"],
        # 精确排除运行时锁定文件（来自 exclude-venv.txt 真源）
        "blacklist": [
            "venv/data-opencode/opencode/log/*",
            "venv/data-opencode/opencode/opencode.db",
            "venv/data-opencode/opencode/opencode.db-shm",
            "venv/data-opencode/opencode/opencode.db-wal",
        ],
        "cwd_parent_level": 0,
        "zip_name": "venv",
    },
}


def _find_toolchainroot(devroot: Path) -> Path:
    """从 verified-runtime-index.json 读取 toolchainroot 路径"""
    index_path = devroot / "references" / "runtime" / "verified-runtime-index.json"
    if index_path.exists():
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            roots = data.get("roots", {})
            tc = roots.get("toolchainroot", {})
            path = tc.get("path", "")
            if path:
                return Path(path)
        except (json.JSONDecodeError, KeyError, OSError):
            pass
    # fallback：从环境变量或默认
    env_tc = os.environ.get("TOOLCHAINROOT", "")
    if env_tc:
        return Path(env_tc)
    return Path(r"D:\download")


def find_7z_exe(devroot = None) -> Path:
    r"""
    查找 7z 可执行文件路径。

    优先级：
    1. 环境变量 SEVEN_ZIP
    2. verified-runtime-index.json -> toolchainroot/7-Zip/7z.exe
    3. 默认 D:\download\7-Zip\7z.exe

    参数:
        devroot: devroot 路径，用于读取 verified-runtime-index.json

    返回:
        Path: 7z.exe 绝对路径

    异常:
        FileNotFoundError: 找不到 7z.exe
    """
    # 1. 环境变量
    env_7z = os.environ.get("SEVEN_ZIP", "")
    if env_7z:
        p = Path(env_7z)
        if p.exists():
            return p.resolve()

    # 2. 从 toolchainroot 推导
    if devroot:
        tcroot = _find_toolchainroot(Path(devroot))
        candidate = tcroot / "7-Zip" / "7z.exe"
        if candidate.exists():
            return candidate.resolve()

    # 3. 默认 fallback
    if _DEFAULT_7Z_PATH.exists():
        return _DEFAULT_7Z_PATH.resolve()

    raise FileNotFoundError(
        f"找不到 7z.exe。"
        f"已尝试: 环境变量 SEVEN_ZIP={env_7z}, "
        f"toolchainroot/7-Zip/7z.exe, "
        f"默认路径 {_DEFAULT_7Z_PATH}"
    )


def get_output_dir(devroot: Path, group_name: str) -> Path:
    """
    获取归档中间产物输出目录。

    路径: devroot/venv/tmp/archive-<group>/
    """
    out = devroot / "venv" / "tmp" / f"archive-{group_name}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def get_group_config(group_name: str, devroot) -> dict:
    """
    获取指定分组的完整配置（含解析后的路径）。

    参数:
        group_name: "cs_py" 或 "venv"
        devroot: devroot 路径（str 或 Path）

    返回:
        dict: 包含 src, arcname, whitelist, blacklist, cwd, zip, listfile, csv, out_dir
    """
    devroot = Path(devroot).resolve()
    if group_name not in GROUPS_SPEC:
        raise ValueError(f"未知分组: {group_name}。可用: {list(GROUPS_SPEC.keys())}")

    spec = GROUPS_SPEC[group_name]

    # 源目录
    if group_name == "cs_py":
        src = devroot
    else:
        src = devroot / "venv"

    # CWD（7z 压缩工作目录）
    parent_level = spec.get("cwd_parent_level", 0)
    cwd = devroot
    for _ in range(parent_level):
        cwd = cwd.parent

    # 输出目录
    out_dir = get_output_dir(devroot, group_name)

    # 输出文件路径
    zip_name = spec["zip_name"]
    zip_path = devroot / f"{zip_name}.zip"  # 默认后缀，可被覆盖
    listfile = out_dir / f"listfile-{group_name}.txt"
    csv_path = out_dir / f"gt-{group_name}.csv"

    return {
        "name": group_name,
        "src": src.resolve(),
        "arcname": spec["arcname"],
        "whitelist": spec.get("whitelist", []),
        "blacklist": spec.get("blacklist", []),
        "cwd": cwd.resolve(),
        "zip": zip_path,
        "listfile": listfile,
        "csv": csv_path,
        "out_dir": out_dir,
    }


def update_zip_extension(cfg: dict, fmt: str) -> dict:
    """
    根据格式更新 zip 文件后缀。

    参数:
        cfg: get_group_config 返回的配置字典
        fmt: "zip" 或 "7z"

    返回:
        更新后的配置字典（zip 路径已变更）
    """
    cfg = dict(cfg)  # 浅拷贝
    name = cfg["name"]
    if fmt == "7z":
        cfg["zip"] = cfg["zip"].with_suffix(".7z")
    else:
        cfg["zip"] = cfg["zip"].with_suffix(".zip")
    return cfg


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    # 自检
    devroot = Path(r"D:\pjt\cursor\cs_py")
    print(f"7z 路径: {find_7z_exe(devroot)}")
    for name in ["cs_py", "venv"]:
        cfg = get_group_config(name, devroot)
        print(f"\n[{name}] 配置:")
        for k, v in cfg.items():
            print(f"  {k}: {v}")
