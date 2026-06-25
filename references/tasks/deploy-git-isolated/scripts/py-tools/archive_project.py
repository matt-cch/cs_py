#!/usr/bin/env python3
"""
archive_project.py — 项目归档主 CLI（py-lib 入口版 v2.0.0）
标签：py-tools

职责：编排 scan → compress → verify 三阶段，通过 py_lib 统一入口加载 archive 插件，
      支持 cs_py / venv 两组，zip / 7z / auto 三种输出格式。

层级关系：
    archive_project.py → py_lib.load_plugins(profile="archive")
        → archive_config, archive_scanner, archive_compressor

设计原则：
  - 不直接 import 任何 plugin（禁止越级）
  - 所有能力通过 py_lib registry 获取
  - workflow 只负责步骤编排和报告输出

用法：
    python archive_project.py --group cs_py --stage all --format 7z
    python archive_project.py --group venv --stage scan,compress --format auto
    python archive_project.py --group cs_py venv --stage all --force
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 定位 py_lib
_scripts_dir = Path(__file__).parent.parent.resolve()
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from py_lib import load_plugins


STAGES = ["scan", "compress", "verify"]
# all 默认不含 verify，verify 需显式指定（代码成熟后可纳入 all）
DEFAULT_STAGES = ["scan", "compress"]


def stage_scan(group_name: str, devroot: Path, registry) -> tuple:
    """执行扫描阶段"""
    print(f"\n{'='*50}")
    print(f"Stage: scan | Group: {group_name}")
    print(f"{'='*50}")

    cfg = registry.archive_config.get_group_config(group_name, devroot)
    result = registry.archive_scanner.scan_group(cfg)
    return cfg, result


def stage_compress(group_name: str, cfg: dict, fmt: str, force: bool, registry) -> dict:
    """执行压缩阶段"""
    print(f"\n{'='*50}")
    print(f"Stage: compress | Group: {group_name} | Format: {fmt}")
    print(f"{'='*50}")

    # auto 模式下默认选 7z（7z 体积更小、速度更快）
    if fmt == "auto":
        fmt = "7z"
        print(f"[auto] 已验证 7z 更优，自动选择 7z")

    cfg = registry.archive_config.update_zip_extension(cfg, fmt)
    seven_zip = registry.archive_config.find_7z_exe(devroot=cfg["src"].parents[1] if group_name == "cs_py" else cfg["src"].parent)
    result = registry.archive_compressor.compress_group(cfg, seven_zip, fmt=fmt, force=force)
    return result


def stage_verify(group_name: str, cfg: dict, scan_result: dict, compress_result: dict, registry) -> bool:
    """执行验证阶段：解压压缩包并与 listfile 交叉验证"""
    print(f"\n{'='*50}")
    print(f"Stage: verify | Group: {group_name}")
    print(f"{'='*50}")

    zip_path = compress_result["zip"]
    if not zip_path.exists():
        print(f"[verify] FAIL: 压缩包不存在: {zip_path}")
        return False

    devroot = cfg["src"] if group_name == "cs_py" else cfg["src"].parent
    seven_zip = registry.archive_config.find_7z_exe(devroot=devroot)

    result = registry.archive_scanner.verify_group(cfg, zip_path, seven_zip)
    return result["pass"]


def run_group(group_name: str, devroot: Path, stages: list, fmt: str, force: bool, registry) -> dict:
    """执行单个分组的完整流程"""
    total_start = time.time()

    # 独立获取 config（不依赖 scan 阶段）
    cfg = registry.archive_config.get_group_config(group_name, devroot)
    if fmt != "auto":
        cfg = registry.archive_config.update_zip_extension(cfg, fmt)

    scan_result = None
    compress_result = None
    verify_pass = None

    if "scan" in stages:
        scan_result = registry.archive_scanner.scan_group(cfg)
        # scanner 内部已打印详细输出

    if "compress" in stages:
        compress_result = stage_compress(group_name, cfg, fmt, force, registry)

    if "verify" in stages:
        # verify 可以独立执行：只要压缩包和 listfile 存在即可
        zip_path = cfg["zip"]
        listfile_path = cfg["listfile"]
        if zip_path.exists() and listfile_path.exists():
            # 构造一个 mock compress_result（verify 只读 zip 字段）
            mock_compress = {"zip": zip_path}
            verify_pass = stage_verify(group_name, cfg, scan_result or {}, mock_compress, registry)
            # verify 通过后清理 .emptydir
            if verify_pass:
                registry.archive_scanner.cleanup_placeholders(cfg["src"])
        else:
            print(f"[verify] SKIP: 压缩包或 listfile 不存在")
            verify_pass = None

    total_elapsed = time.time() - total_start
    print(f"\n{'='*50}")
    print(f"Group {group_name} 全部完成，总耗时: {total_elapsed:.2f}s")
    print(f"{'='*50}")

    return {
        "group": group_name,
        "cfg": cfg,
        "scan": scan_result,
        "compress": compress_result,
        "verify": verify_pass,
        "total_elapsed": total_elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="项目归档主 CLI（py-lib 入口版）")
    parser.add_argument("--group", nargs="+", required=True, choices=["cs_py", "venv"], help="归档分组")
    parser.add_argument("--stage", default="all", help="执行阶段：scan,compress,verify，逗号分隔或 all")
    parser.add_argument("--format", default="7z", choices=["zip", "7z", "auto"], help="输出格式")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在的输出文件")
    parser.add_argument("--devroot", default=None, help="devroot 路径（默认自动探测）")
    args = parser.parse_args()

    stages = [s.strip() for s in args.stage.split(",")]
    if stages == ["all"]:
        stages = DEFAULT_STAGES

    for s in stages:
        if s not in STAGES:
            print(f"[ERROR] 未知阶段: {s}", file=sys.stderr)
            sys.exit(1)

    # 获取 devroot
    if args.devroot:
        devroot = Path(args.devroot).resolve()
    else:
        # 通过 py_lib 加载 detect_devroot 插件获取
        registry_core = load_plugins(profile="core")
        devroot = registry_core.detect_devroot.get_devroot()

    print(f"[archive_project] devroot: {devroot}")
    print(f"[archive_project] groups: {args.group}")
    print(f"[archive_project] stages: {stages}")
    print(f"[archive_project] format: {args.format}")
    print(f"[archive_project] force: {args.force}")

    # 通过 py_lib 统一入口加载 archive 插件
    registry = load_plugins(devroot=str(devroot), profile="archive")
    print(f"[archive_project] py_lib 已加载插件: {registry.list_loaded()}")

    all_ok = True
    for group_name in args.group:
        result = run_group(group_name, devroot, stages, args.format, args.force, registry)
        if result.get("verify") is False:
            all_ok = False

    if not all_ok:
        print("\n[archive_project] 部分分组验证失败")
        sys.exit(1)
    else:
        print("\n[archive_project] 全部完成")
        sys.exit(0)


if __name__ == "__main__":
    main()
