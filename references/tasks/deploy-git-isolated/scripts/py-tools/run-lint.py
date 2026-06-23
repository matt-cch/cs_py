#!/usr/bin/env python3
"""
run-lint.py — 统一 lint CLI 入口（v1.1.0）
标签：py-tools

职责：通过 py_lib 加载 lint 插件，聚合执行全量/指定类型/指定文件的 lint 检查。

用法（目录扫描模式）：
    python run-lint.py --devroot "D:/pjt/cursor/cs_py"
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --profile lint-json
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --tags lint,encoding

用法（单文件列表模式）：
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --files a.py b.ps1 c.md
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --files "refs/tasks/x/script.py"
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 优先尝试走 py_lib 入口
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

try:
    from py_lib import load_plugins
    HAS_PY_LIB = True
except Exception as e:
    HAS_PY_LIB = False
    print(f"[WARN] py_lib 加载失败: {e}", file=sys.stderr)

# 文件扩展名 -> 插件名 路由表
EXT_TO_PLUGIN = {
    ".py": "lint_python",
    ".ps1": "lint_ps1",
    ".json": "lint_json",
    ".jsonc": "lint_json",
    ".md": "md_lint",
    ".mdc": "md_lint",
}

# 默认走编码检测的其他文本扩展名
ENCODING_EXTENSIONS = {
    ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
    ".yml", ".yaml", ".toml", ".sh", ".txt",
    ".ini", ".cfg", ".log",
}


def _print_violation(v: dict):
    """统一打印单条违规（基于 plugin-result-schema v1.0.0）"""
    file_name = v.get("file", "unknown")
    context = v.get("context", "")
    line = v.get("line")
    severity = v.get("severity", "error")
    if line is not None:
        print(f"    ❌ [{severity}] {file_name}:{line} — {context}")
    else:
        print(f"    ❌ [{severity}] {file_name} — {context}")


def run_via_py_lib(devroot: str, profile: str = "lint", tags: list = None):
    """通过 py_lib 入口执行目录扫描 lint"""
    if tags:
        registry = load_plugins(devroot=devroot, tags=tags)
    else:
        registry = load_plugins(devroot=devroot, profile=profile)

    results = []
    has_error = False

    for name in registry.list_loaded():
        plugin = getattr(registry, name)
        if not hasattr(plugin, "validate"):
            continue

        print(f"\n{'=' * 50}")
        print(f"[lint] 执行插件: {name}")
        print(f"{'=' * 50}")

        try:
            result = plugin.validate(dir_path=devroot)
            results.append({"name": name, "result": result})

            scanned = result.get("files_scanned", 0)
            v_found = result.get("violations_found", 0)
            print(f"  扫描文件: {scanned} 个")
            print(f"  违规项: {v_found} 处")

            if result.get("violations"):
                has_error = True
                for v in result["violations"]:
                    _print_violation(v)
            else:
                print(f"    ✅ 通过")

        except Exception as e:
            has_error = True
            print(f"    ❌ 执行异常: {e}")
            results.append({"name": name, "error": str(e)})

    return results, has_error


def run_files_via_py_lib(devroot: str, files: list):
    """
    通过 py_lib 入口执行单文件列表 lint。
    按扩展名路由到对应插件的 validate_file() 方法。
    """
    # 加载全部 lint + md-validation 插件（覆盖所有可能的文件类型）
    registry = load_plugins(devroot=devroot, tags=["lint", "md", "validation"])

    # 按插件名分组文件
    plugin_files: dict = {}
    skipped = []

    for fpath in files:
        fp = Path(fpath)
        ext = fp.suffix.lower()
        matched_plugins = set()

        if ext in EXT_TO_PLUGIN:
            matched_plugins.add(EXT_TO_PLUGIN[ext])
        if ext in ENCODING_EXTENSIONS or ext in (".md", ".mdc"):
            matched_plugins.add("lint_encoding")

        if not matched_plugins:
            skipped.append(fpath)
            continue

        for plugin_name in matched_plugins:
            plugin_files.setdefault(plugin_name, []).append(fpath)

    results = []
    has_error = False

    for plugin_name, file_list in plugin_files.items():
        if plugin_name not in registry.list_loaded():
            print(f"\n[WARN] 插件 '{plugin_name}' 未加载，跳过 {len(file_list)} 个文件")
            continue

        plugin = getattr(registry, plugin_name)
        if not hasattr(plugin, "validate_file"):
            print(f"\n[WARN] 插件 '{plugin_name}' 不支持单文件验证，跳过")
            continue

        print(f"\n{'=' * 50}")
        print(f"[lint] 执行插件: {plugin_name} ({len(file_list)} 个文件)")
        print(f"{'=' * 50}")

        for fpath in file_list:
            try:
                result = plugin.validate_file(fpath)
                results.append({"name": plugin_name, "file": fpath, "result": result})

                scanned = result.get("files_scanned", 0)
                v_found = result.get("violations_found", 0)

                if result.get("violations"):
                    has_error = True
                    print(f"  ❌ {fpath} — {v_found} 处违规")
                    for v in result["violations"]:
                        _print_violation(v)
                else:
                    print(f"  ✅ {fpath}")

            except Exception as e:
                has_error = True
                print(f"  ❌ {fpath} — 执行异常: {e}")
                results.append({"name": plugin_name, "file": fpath, "error": str(e)})

    if skipped:
        print(f"\n[WARN] 跳过未识别的文件类型 ({len(skipped)} 个):")
        for s in skipped:
            print(f"  - {s}")

    return results, has_error


def main():
    parser = argparse.ArgumentParser(description="统一 lint CLI 入口")
    parser.add_argument("--devroot", required=True, help="Devroot 路径")
    parser.add_argument("--profile", default="lint", help="lint profile 名（默认: lint）")
    parser.add_argument("--tags", default=None, help="逗号分隔的标签列表（与 profile 互斥）")
    parser.add_argument(
        "--files",
        nargs="*",
        help="指定一个或多个文件路径进行 lint（混合类型自动路由）"
    )
    args = parser.parse_args()

    if not HAS_PY_LIB:
        print("错误: py_lib 不可用，无法执行 lint", file=sys.stderr)
        sys.exit(1)

    print(f"[run-lint] devroot: {args.devroot}")

    if args.files:
        # 文件列表模式
        print(f"[run-lint] 模式: 单文件列表 ({len(args.files)} 个文件)")
        results, has_error = run_files_via_py_lib(
            devroot=args.devroot,
            files=args.files
        )

        # 汇总
        print(f"\n{'=' * 50}")
        print("[run-lint] 汇总报告")
        print(f"{'=' * 50}")
        total_scanned = sum(
            r["result"].get("files_scanned", 0)
            for r in results if "result" in r
        )
        total_violations = sum(
            r["result"].get("violations_found", 0)
            for r in results if "result" in r
        )
        print(f"  总扫描文件: {total_scanned} 个")
        print(f"  总违规项: {total_violations} 处")

        if has_error:
            print(f"\n  结论: ❌ 存在违规，请修复后重试")
            sys.exit(1)
        else:
            print(f"\n  结论: ✅ 全部通过")
            sys.exit(0)
    else:
        # 目录扫描模式
        tags = None
        if args.tags:
            tags = [t.strip() for t in args.tags.split(",")]

        print(f"[run-lint] profile: {args.profile if not tags else 'N/A (tags mode)'}")
        if tags:
            print(f"[run-lint] tags: {tags}")

        results, has_error = run_via_py_lib(
            devroot=args.devroot,
            profile=args.profile,
            tags=tags
        )

        # 汇总
        print(f"\n{'=' * 50}")
        print("[run-lint] 汇总报告")
        print(f"{'=' * 50}")
        total_scanned = sum(
            r["result"].get("files_scanned", 0)
            for r in results if "result" in r
        )
        total_violations = sum(
            r["result"].get("violations_found", 0)
            for r in results if "result" in r
        )
        print(f"  总扫描文件: {total_scanned} 个")
        print(f"  总违规项: {total_violations} 处")

        if has_error:
            print(f"\n  结论: ❌ 存在违规，请修复后重试")
            sys.exit(1)
        else:
            print(f"\n  结论: ✅ 全部通过")
            sys.exit(0)


if __name__ == "__main__":
    main()
