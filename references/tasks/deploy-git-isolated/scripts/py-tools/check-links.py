#!/usr/bin/env python3
"""
check-links.py — Markdown 内部链接验证工具
标签：py-tools
职责：扫描任务目录下的所有 .md 文件，验证内部相对链接有效性。

用法（通过 py_lib 入口加载）：
    import sys
    sys.path.insert(0, r"...\\scripts")
    from py_lib import load_plugins
    registry = load_plugins(devroot="D:/pjt/cursor/cs_py", profile="md-validation")
    result = registry.link_checker.validate(task_dir="...")

用法（直接作为 CLI 工具执行）：
    python check-links.py --devroot "D:/pjt/cursor/cs_py"

设计原则：
- 走 py_lib 正规入口，演示插件体系的实际用法
- 支持 CLI 参数，可直接作为独立工具运行
- 输出 UTF-8，适配 Agent bash 捕获层
"""
import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 优先尝试走 py_lib 入口（正规用法）
try:
    # 假设本文件在 scripts/py-tools/ 下，py_lib.py 在 scripts/ 根下
    from pathlib import Path
    _scripts_dir = Path(__file__).parent.parent.resolve()
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from py_lib import load_plugins
    HAS_PY_LIB = True
except Exception:
    HAS_PY_LIB = False


def run_via_py_lib(devroot: str, task_dir: str = None):
    """通过 py_lib 入口执行验证（正规用法示范）"""
    registry = load_plugins(devroot=devroot, profile="md-validation")
    if task_dir is None:
        task_dir = registry.resolve_path("${devroot}\\references\\tasks\\deploy-git-isolated")
    result = registry.link_checker.validate(task_dir=str(task_dir))
    return result


def run_standalone(task_dir: str):
    """独立执行（不依赖 py_lib，直接 import 插件）"""
    _scripts_dir = Path(__file__).parent.parent.resolve()
    _plugins_dir = _scripts_dir / "py-plugins"
    if str(_plugins_dir) not in sys.path:
        sys.path.insert(0, str(_plugins_dir))
    from link_checker import validate
    return validate(task_dir=task_dir)


def main():
    parser = argparse.ArgumentParser(description="Markdown 内部链接验证工具")
    parser.add_argument("--devroot", default=None, help="Devroot 路径（默认自动探测）")
    parser.add_argument("--task-dir", default=None, help="任务目录路径（默认推断）")
    args = parser.parse_args()

    if HAS_PY_LIB and args.devroot:
        print("[模式] 通过 py_lib 入口加载（正规用法）")
        result = run_via_py_lib(devroot=args.devroot, task_dir=args.task_dir)
    else:
        print("[模式] 独立执行（fallback）")
        if args.task_dir:
            result = run_standalone(task_dir=args.task_dir)
        else:
            print("错误: 独立模式需要 --task-dir 参数")
            sys.exit(1)

    print(f"\n结果: checked={result['checked']}, broken={result['broken']}")

    has_error = False

    if result.get("format_violations"):
        print(f"\n格式违规: {len(result['format_violations'])} 处")
        for v in result["format_violations"]:
            print(f"  {v['source']}:{v['line']} — {v['rule']}")
        has_error = True

    if result.get("issues"):
        print("\n断裂链接:")
        for issue in result["issues"]:
            print(f"  {issue}")
        has_error = True

    if has_error:
        sys.exit(1)
    else:
        print("所有验证通过（链接 + 格式）")
        sys.exit(0)


if __name__ == "__main__":
    main()
