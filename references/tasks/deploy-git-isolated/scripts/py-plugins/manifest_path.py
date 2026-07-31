#!/usr/bin/env python3
r"""
插件：产物落盘路径唯一真源（Manifest Path Resolver）
标签：core, utility
依赖：无（纯计算，零外部依赖）

原始意图
  将「产物文件默认写到哪」这一分散在 baseline 文本中的规则，下沉为
  可被所有脚本统一调用的代码真源。避免每个脚本各自推算路径导致
  不一致（如 workflow-download-article-to-vault.py 曾用 target_dir.parents[2]
  错误指向 vault 目录，或误将 manifest 写到 D:\pjt\cursor\cs_py\vaults\vault-demo\venv\tmp）。

设计目标
  1. 唯一真源：所有脚本/插件对「默认落盘位置」的判断必须收敛到本插件
  2. 环境变量优先：尊重系统 TMP/TEMP 约定，由外部 .code-workspace /
     terminal.env 统一控制，脚本不硬编码路径
  3. 确定性 fallback：当 TMP/TEMP 未配置时，回退到 devroot/venv/tmp/，
     保持 baseline 产物隔离原则（venv/ 已 gitignore，避免污染仓库）
  4. 零副作用：纯计算函数，不创建目录、不写文件，由调用方决定是否 mkdir

作用
  提供两层 API：
    - get_manifest_dir(devroot) -> Path：获取产物应写入的目录
    - build_manifest_path(devroot, tool_name, suffix, ext) -> Path：组装完整文件路径
  文件名格式遵循 baseline 约定：{tool-name}-{suffix}-{timestamp}.{ext}

遵循基准来源
  - baseline-plugin-architecture.md §8.4.8「产出文件默认落盘到 venv/tmp/」
  - baseline-workflow-deploy.md §8.9.2/§8.9.4「--output 回退路径规范」
  以上 baseline 条文已在 2026-07-30 同步更新为「TMP/TEMP 优先，
  未配置时 fallback 到 devroot/venv/tmp/」。

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["utility"])
    manifest_path = registry.manifest_path

    # 获取目录
    dir_path = manifest_path.get_manifest_dir(devroot)

    # 组装完整路径
    full_path = manifest_path.build_manifest_path(
        devroot,
        tool_name="workflow-download-article",
        suffix="manifest",
        ext="json"
    )
    # -> D:\pjt\cursor\cs_py\venv\tmp\workflow-download-article-manifest-20260730-100239.json

用法（CLI 直接执行）：
    python manifest_path.py --devroot "D:\pjt\cursor\cs_py"
    # 输出当前 devroot 的 manifest 目录路径
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def get_manifest_dir(devroot: Path) -> Path:
    r"""
    获取产物落盘目录。

    优先级：
      1. 系统环境变量 TMP / TEMP（外部 terminal.env 统一控制）
      2. Fallback: devroot / "venv" / "tmp"

    参数:
        devroot: devroot 路径对象

    返回:
        Path 对象（目录尚未创建，调用方需自行 mkdir）

    注意：
        本函数为纯计算，零副作用。不读取磁盘、不创建目录、不写文件。
    """
    tmp_env = os.environ.get("TMP") or os.environ.get("TEMP")
    if tmp_env:
        return Path(tmp_env)
    return devroot / "venv" / "tmp"


def build_manifest_path(
    devroot: Path,
    tool_name: str,
    suffix: str = "manifest",
    ext: str = "json",
) -> Path:
    r"""
    组装完整产物文件路径。

    文件名格式: {tool-name}-{suffix}-{timestamp}.{ext}
    示例: workflow-download-article-manifest-20260730-100239.json

    参数:
        devroot: devroot 路径对象
        tool_name: 工具名（用于文件名前缀，不含 .py 扩展名）
        suffix: 文件名中间段（默认: manifest）
        ext: 扩展名（默认: json）

    返回:
        Path 对象（文件尚未创建，调用方需自行 write_text）

    注意：
        本函数为纯计算，零副作用。不创建目录、不写文件。
    """
    manifest_dir = get_manifest_dir(devroot)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"{tool_name}-{suffix}-{ts}.{ext}"
    return manifest_dir / filename


def _resolve_devroot(devroot: str | None) -> Path:
    """解析 devroot 路径（默认从脚本位置向上推导 4 层）。"""
    if devroot:
        return Path(devroot).resolve()
    script_dir = Path(__file__).resolve().parent
    return script_dir.parents[3]


def main():
    parser = argparse.ArgumentParser(
        description="产物落盘路径唯一真源（Manifest Path Resolver）"
    )
    parser.add_argument(
        "--devroot",
        default=None,
        help="devroot 路径（默认自动探测）",
    )
    parser.add_argument(
        "--tool-name",
        default=None,
        help="工具名（用于文件名，如 workflow-download-article）",
    )
    parser.add_argument(
        "--suffix",
        default="manifest",
        help="文件名中间段（默认: manifest）",
    )
    parser.add_argument(
        "--ext",
        default="json",
        help="扩展名（默认: json）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出（供脚本解析）",
    )
    args = parser.parse_args()

    devroot = _resolve_devroot(args.devroot)

    if args.tool_name:
        manifest_path = build_manifest_path(
            devroot,
            tool_name=args.tool_name,
            suffix=args.suffix,
            ext=args.ext,
        )
        if args.json:
            import json
            print(
                json.dumps(
                    {
                        "dir": str(manifest_path.parent),
                        "path": str(manifest_path),
                        "filename": manifest_path.name,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(str(manifest_path))
    else:
        manifest_dir = get_manifest_dir(devroot)
        if args.json:
            import json
            print(json.dumps({"dir": str(manifest_dir)}, ensure_ascii=False))
        else:
            print(str(manifest_dir))


if __name__ == "__main__":
    main()
