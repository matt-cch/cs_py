#!/usr/bin/env python3
"""
workflow-lint-amend-lint.py — lint→amend→lint 巡检工作流（v2.0.0）
标签：py-tools

职责：通过 py_lib 统一入口加载 lint_encoding 插件，完成"检测→修复→验证"闭环。
      本文件是 workflow 编排层，不直接触碰任何 plugin，只与 py_lib 交互。

层级关系：
    workflow-lint-amend-lint.py → py_lib.load_plugins(tags=["lint", "encoding"])
        → py_lib 拓扑排序加载 → lint_encoding plugin

设计原则：
  - 不直接 import 任何 plugin（禁止越级）
  - 所有能力通过 py_lib registry 获取
  - workflow 只负责步骤编排和报告输出

用法：
    python workflow-lint-amend-lint.py --devroot "D:/pjt/cursor/cs_py" [--dir "sub/path"]
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 定位 py_lib
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def step_header(step_id: str, title: str):
    print(f"\n{'=' * 50}")
    print(f"[Step {step_id}] {title}")
    print(f"{'=' * 50}")


def main():
    parser = argparse.ArgumentParser(
        description="lint→amend→lint 巡检工作流（通过 py_lib 统一入口）"
    )
    parser.add_argument("--devroot", required=True, help="Devroot 路径")
    parser.add_argument(
        "--dir", default=None,
        help="要巡检的子目录（相对 devroot，默认 devroot 本身）"
    )
    args = parser.parse_args()

    devroot = Path(args.devroot).resolve()
    if not devroot.exists():
        print(f"错误: devroot 不存在 {devroot}", file=sys.stderr)
        sys.exit(1)

    target_dir = devroot
    if args.dir:
        target_dir = devroot / args.dir

    print(f"[workflow] devroot: {devroot}")
    print(f"[workflow] 目标目录: {target_dir}")
    print(f"[workflow] 通过 py_lib 加载 lint_encoding 插件 ...")

    # ========== 通过 py_lib 统一入口加载能力 ==========
    registry = load_plugins(devroot=str(devroot), tags=["lint", "encoding"])
    lint_encoding = registry.lint_encoding

    print(f"[workflow] py_lib 已加载插件: {registry.list_loaded()}")
    print(f"[workflow] 开始 lint→amend→lint 巡检 ...")

    # ========== Step 1: 首次检测 ==========
    step_header("1", "首次 lint 检测（lint_encoding.validate）")
    result1 = lint_encoding.validate(dir_path=str(target_dir))
    print(f"  扫描文件: {result1['files_scanned']} 个")
    print(f"  违规文件: {result1['files_with_violations']} 个")
    print(f"  违规项:   {result1['violations_found']} 处")

    if result1["violations"]:
        print("\n  【违规详情】")
        for v in result1["violations"]:
            print(f"    ❌ {v['file']} — {v['context']}")

    if result1["violations_found"] == 0:
        step_header("Done", "巡检结论")
        print("  ✅ 首次检测即通过，无需修复")
        sys.exit(0)

    # ========== Step 2: 修复 ==========
    step_header("2", "执行 amend（lint_encoding.validate fix=True）")
    result_fix = lint_encoding.validate(dir_path=str(target_dir), fix=True)
    print(f"  尝试修复: {result_fix['files_with_violations']} 个文件")
    print(f"  实际修复: {result_fix['files_fixed']} 个文件")

    if result_fix.get("fixed_files"):
        print("\n  【修复详情】")
        for f in result_fix["fixed_files"]:
            print(f"    ✅ {f['file']} — {' | '.join(f['actions'])}")

    # ========== Step 3: 重新验证 ==========
    step_header("3", "重新 lint 验证（lint_encoding.validate）")
    result2 = lint_encoding.validate(dir_path=str(target_dir))
    print(f"  扫描文件: {result2['files_scanned']} 个")
    print(f"  违规文件: {result2['files_with_violations']} 个")
    print(f"  违规项:   {result2['violations_found']} 处")

    if result2["violations"]:
        print("\n  【剩余违规】")
        for v in result2["violations"]:
            print(f"    ❌ {v['file']} — {v['context']}")

    # ========== Step 4: 汇总报告 ==========
    step_header("Done", "巡检结论")
    before = result1["violations_found"]
    after = result2["violations_found"]
    fixed = result_fix["files_fixed"]

    print(f"  首次违规: {before} 处")
    print(f"  修复文件: {fixed} 个")
    print(f"  剩余违规: {after} 处")

    if after == 0:
        print(f"\n  ✅ lint→amend→lint 闭环完成，全部通过")
        sys.exit(0)
    else:
        print(f"\n  ❌ 修复后仍有 {after} 处违规，需人工介入")
        sys.exit(1)


if __name__ == "__main__":
    main()
