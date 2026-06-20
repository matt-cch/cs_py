#!/usr/bin/env python3
"""
archive_project.py — 项目归档主 CLI
标签：py-tools

职责：分步执行项目归档（扫描 → 压缩 → 验证），支持 cs_py / venv 两组，
      支持 zip / 7z / auto 三种输出格式。

用法：
    python archive_project.py --group cs_py --stage all --format 7z
    python archive_project.py --group venv --stage scan,compress --format auto
    python archive_project.py --group cs_py venv --stage all --force
"""
import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 优先走 py_lib 入口
_scripts_dir = Path(__file__).parent.parent.resolve()
_plugins_dir = _scripts_dir / "py-plugins"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
if str(_plugins_dir) not in sys.path:
    sys.path.insert(0, str(_plugins_dir))

from archive_config import get_group_config, find_7z_exe, update_zip_extension
from archive_scanner import scan_group
from archive_compressor import compress_group


STAGES = ["scan", "compress", "verify"]


def stage_scan(group_name: str, devroot: Path) -> dict:
    """执行扫描阶段"""
    print(f"\n{'='*50}")
    print(f"Stage: scan | Group: {group_name}")
    print(f"{'='*50}")
    cfg = get_group_config(group_name, devroot)
    result = scan_group(cfg)
    return cfg, result


def stage_compress(group_name: str, cfg: dict, seven_zip: Path, fmt: str, force: bool) -> dict:
    """执行压缩阶段"""
    print(f"\n{'='*50}")
    print(f"Stage: compress | Group: {group_name} | Format: {fmt}")
    print(f"{'='*50}")

    # auto 模式下，根据已验证结论默认选 7z（7z 体积更小、速度更快）
    if fmt == "auto":
        fmt = "7z"
        print(f"[auto] 已验证 7z 更优，自动选择 7z")

    cfg = update_zip_extension(cfg, fmt)
    result = compress_group(cfg, seven_zip, fmt=fmt, force=force)
    return result


def stage_verify(group_name: str, cfg: dict, scan_result: dict, compress_result: dict) -> bool:
    """执行验证阶段：比对压缩包内文件数与扫描结果"""
    print(f"\n{'='*50}")
    print(f"Stage: verify | Group: {group_name}")
    print(f"{'='*50}")

    zip_path = compress_result["zip"]
    if not zip_path.exists():
        print(f"[verify] FAIL: 压缩包不存在: {zip_path}")
        return False

    # 用 7z l 列出压缩包内容
    import subprocess
    seven_zip = find_7z_exe(cfg["src"].parents[1] if group_name == "cs_py" else cfg["src"].parent)
    # 重新定位 devroot
    devroot = cfg["src"] if group_name == "cs_py" else cfg["src"].parent
    seven_zip = find_7z_exe(devroot)

    proc = subprocess.run(
        [str(seven_zip), "l", str(zip_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # 解析 7z l 输出中的文件数
    # 典型输出尾行: "2026-06-18 ... 122318751 11472425 7143 files"
    # 或: "  7164 files, 610 folders"
    import re
    archived_files = 0
    for line in proc.stdout.splitlines():
        # 匹配 "数字 files" 或 "数字 files," 模式
        m = re.search(r"(\d+)\s+files", line)
        if m:
            archived_files = int(m.group(1))

    expected_files = scan_result["file_count"]
    print(f"[verify] 扫描文件数: {expected_files}")
    print(f"[verify] 压缩包文件数: {archived_files}")

    if archived_files == expected_files:
        print(f"[verify] PASS: 文件数匹配")
        return True
    else:
        print(f"[verify] FAIL: 文件数不匹配 (差异: {archived_files - expected_files})")
        return False


def run_group(group_name: str, devroot: Path, stages: list, fmt: str, force: bool) -> dict:
    """执行单个分组的完整流程"""
    total_start = time.time()
    seven_zip = find_7z_exe(devroot)

    cfg = None
    scan_result = None
    compress_result = None
    verify_pass = None

    if "scan" in stages:
        cfg, scan_result = stage_scan(group_name, devroot)

    if "compress" in stages and cfg:
        compress_result = stage_compress(group_name, cfg, seven_zip, fmt, force)

    if "verify" in stages and cfg and scan_result and compress_result:
        verify_pass = stage_verify(group_name, cfg, scan_result, compress_result)

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
    parser = argparse.ArgumentParser(description="项目归档主 CLI")
    parser.add_argument("--group", nargs="+", required=True, choices=["cs_py", "venv"], help="归档分组")
    parser.add_argument("--stage", default="all", help="执行阶段：scan,compress,verify，逗号分隔或 all")
    parser.add_argument("--format", default="auto", choices=["zip", "7z", "auto"], help="输出格式")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在的输出文件")
    parser.add_argument("--devroot", default=None, help="devroot 路径（默认自动探测）")
    args = parser.parse_args()

    stages = [s.strip() for s in args.stage.split(",")]
    if stages == ["all"]:
        stages = STAGES

    for s in stages:
        if s not in STAGES:
            print(f"[ERROR] 未知阶段: {s}", file=sys.stderr)
            sys.exit(1)

    # 获取 devroot
    if args.devroot:
        devroot = Path(args.devroot).resolve()
    else:
        from detect_devroot import get_devroot
        devroot = get_devroot()

    print(f"[archive_project] devroot: {devroot}")
    print(f"[archive_project] groups: {args.group}")
    print(f"[archive_project] stages: {stages}")
    print(f"[archive_project] format: {args.format}")
    print(f"[archive_project] force: {args.force}")

    all_ok = True
    for group_name in args.group:
        result = run_group(group_name, devroot, stages, args.format, args.force)
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
