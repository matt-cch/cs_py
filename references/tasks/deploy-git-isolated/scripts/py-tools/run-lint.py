#!/usr/bin/env python3
"""
run-lint.py — 统一 lint CLI 入口（v1.3.0）
标签：py-tools

职责：通过 py_lib 加载 lint 插件，聚合执行全量/指定类型/指定文件的 lint 检查。
支持 --fix 三阶段闭环（detect → amend → re-verify）。
支持 --audit 交叉校验：对照 lint-rules-manifest.json 做覆盖度检查。

用法（目录扫描模式）：
    python run-lint.py --devroot "D:/pjt/cursor/cs_py"
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --profile lint-json
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --tags lint,encoding

用法（单文件列表模式）：
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --files a.py b.ps1 c.md
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --files "refs/tasks/x/script.py"

用法（三阶段闭环）：
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --files a.md b.py --fix
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --profile lint --fix

用法（覆盖度审计）：
    python run-lint.py --devroot "D:/pjt/cursor/cs_py" --audit
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

# 文件扩展名 -> 插件名 路由表（支持一个扩展名对应多个插件）
EXT_TO_PLUGIN = {
    ".py": ["lint_python"],
    ".ps1": ["lint_ps1"],
    ".json": ["lint_json"],
    ".jsonc": ["lint_json"],
    ".md": ["md_lint", "link_checker"],
    ".mdc": ["md_lint", "link_checker"],
}

# 默认走编码检测的其他文本扩展名
FIX_CAPABLE_PLUGINS = {"lint_encoding", "md_lint"}

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


def run_via_py_lib(devroot: str, profile: str = "lint", tags: list = None, fix: bool = False):
    """
    通过 py_lib 入口执行目录扫描 lint。
    fix=True 时执行 detect→amend→re-verify 三阶段闭环。
    """
    if tags:
        registry = load_plugins(devroot=devroot, tags=tags)
    else:
        registry = load_plugins(devroot=devroot, profile=profile)

    def _run_plugins(phase_label: str, run_fix: bool = False):
        """执行一轮插件 validate 检测（run_fix 时对可修复插件传 fix=True）"""
        phase_results = []
        phase_has_error = False

        for name in registry.list_loaded():
            plugin = getattr(registry, name)
            if not hasattr(plugin, "validate"):
                continue

            print(f"\n{'-' * 40}")
            print(f"[{phase_label}] 插件: {name}")
            print(f"{'-' * 40}")

            try:
                kwargs = {"dir_path": devroot}
                if run_fix and name in FIX_CAPABLE_PLUGINS:
                    kwargs["fix"] = True
                result = plugin.validate(**kwargs)
                phase_results.append({"name": name, "result": result})

                v_found = result.get("violations_found", 0)
                print(f"  违规项: {v_found} 处")

                if result.get("violations"):
                    phase_has_error = True
                    for v in result["violations"]:
                        _print_violation(v)
                else:
                    print(f"    ✅ 通过")

            except Exception as e:
                phase_has_error = True
                print(f"    ❌ 执行异常: {e}")
                phase_results.append({"name": name, "error": str(e)})

        return phase_results, phase_has_error

    # Phase 1: 首次检测
    print(f"\n{'=' * 50}")
    print("[Phase 1] 首次 lint 检测")
    print(f"{'=' * 50}")
    results, has_error = _run_plugins("Phase 1")

    # Phase 2: 修复（仅 fix=True 且 Phase 1 有违规时执行）
    fixed_any = False
    if fix and has_error:
        print(f"\n{'=' * 50}")
        print("[Phase 2] 执行修复（lint_encoding + md_lint）")
        print(f"{'=' * 50}")
        fix_results, _ = _run_plugins("Phase 2", run_fix=True)
        # 汇总修复结果
        total_fixed = 0
        for r in fix_results:
            if "result" in r:
                total_fixed += r["result"].get("metadata", {}).get("files_fixed", 0)
        print(f"\n  ✅ 修复完成，共修复 {total_fixed} 个文件")
        fixed_any = total_fixed > 0

        # Phase 3: 重新验证
        print(f"\n{'=' * 50}")
        print("[Phase 3] 重新 lint 验证")
        print(f"{'=' * 50}")
        results, has_error = _run_plugins("Phase 3")

    return results, has_error, fixed_any


def _run_file_plugins(registry, plugin_files: dict, phase_label: str, fix: bool = False):
    """执行一轮插件 validate_file 检测（run_files_via_py_lib 内复用）"""
    results = []
    has_error = False

    for plugin_name, file_list in plugin_files.items():
        if plugin_name not in registry.list_loaded():
            continue
        plugin = getattr(registry, plugin_name)
        if not hasattr(plugin, "validate_file"):
            continue

        for fpath in file_list:
            try:
                kwargs = {}
                if fix and plugin_name in FIX_CAPABLE_PLUGINS:
                    kwargs["fix"] = True
                result = plugin.validate_file(fpath, **kwargs)
                results.append({"name": plugin_name, "file": fpath, "result": result})

                v_found = result.get("violations_found", 0)
                if result.get("violations"):
                    has_error = True

            except Exception as e:
                print(f"  ⚠ [{phase_label}] {fpath} — {e}")

    return results, has_error


def run_files_via_py_lib(devroot: str, files: list, fix: bool = False):
    """
    通过 py_lib 入口执行单文件列表 lint。
    按扩展名路由到对应插件的 validate_file() 方法。
    fix=True 时执行 detect→amend→re-verify 三阶段闭环。
    """
    registry = load_plugins(devroot=devroot, tags=["lint", "md", "validation"])

    # 按插件名分组文件
    plugin_files: dict = {}
    skipped = []

    for fpath in files:
        fp = Path(fpath)
        ext = fp.suffix.lower()
        matched_plugins = set()

        if ext in EXT_TO_PLUGIN:
            for plugin_name in EXT_TO_PLUGIN[ext]:
                matched_plugins.add(plugin_name)
        if ext in EXT_TO_PLUGIN or ext in ENCODING_EXTENSIONS:
            matched_plugins.add("lint_encoding")

        if not matched_plugins:
            skipped.append(fpath)
            continue
        for plugin_name in matched_plugins:
            plugin_files.setdefault(plugin_name, []).append(fpath)

    # Phase 1: 首次检测
    print(f"\n{'=' * 50}")
    print("[Phase 1] 首次 lint 检测")
    print(f"{'=' * 50}")
    results, has_error = _run_file_plugins(registry, plugin_files, "Phase 1")

    # 输出 Phase 1 明细
    for r in results:
        if "result" in r:
            v_found = r["result"].get("violations_found", 0)
            fpath = r["file"]
            if r["result"].get("violations"):
                print(f"  ❌ {fpath} — {v_found} 处违规")
                for v in r["result"]["violations"]:
                    _print_violation(v)
            else:
                print(f"  ✅ {fpath}")

    # Phase 2: 修复
    fixed_any = False
    if fix and has_error:
        print(f"\n{'=' * 50}")
        print("[Phase 2] 执行修复（lint_encoding + md_lint）")
        print(f"{'=' * 50}")
        fix_results, _ = _run_file_plugins(registry, plugin_files, "Phase 2", fix=True)
        total_fixed = 0
        for r in fix_results:
            if "result" in r:
                total_fixed += r["result"].get("metadata", {}).get("files_fixed", 0)
        print(f"\n  ✅ 修复完成，共修复 {total_fixed} 个文件")
        fixed_any = total_fixed > 0

        # Phase 3: 重新验证
        print(f"\n{'=' * 50}")
        print("[Phase 3] 重新 lint 验证")
        print(f"{'=' * 50}")
        results, has_error = _run_file_plugins(registry, plugin_files, "Phase 3")

        # 输出 Phase 3 明细
        for r in results:
            if "result" in r:
                v_found = r["result"].get("violations_found", 0)
                fpath = r["file"]
                if r["result"].get("violations"):
                    print(f"  ❌ {fpath} — {v_found} 处违规")
                    for v in r["result"]["violations"]:
                        _print_violation(v)
                else:
                    print(f"  ✅ {fpath}")

    if skipped:
        print(f"\n[WARN] 跳过未识别的文件类型 ({len(skipped)} 个):")
        for s in skipped:
            print(f"  - {s}")

    return results, has_error, fixed_any


def _print_summary(results: list, label: str = "汇总报告"):
    """打印 lint 汇总"""
    print(f"\n{'=' * 50}")
    print(f"[run-lint] {label}")
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
    return total_violations


def run_audit(devroot: str):
    """
    对照 lint-rules-manifest.json 做覆盖度审计。
    1. 读取 manifest，校验 JSON 结构
    2. 加载全部 lint 插件
    3. 对比：manifest 条目 vs 实际加载，报告空白/遗漏
    """
    manifest_path = _SCRIPTS_DIR / ".." / "schema" / "json" / "lint-rules-manifest.json"
    manifest_path = manifest_path.resolve()

    if not manifest_path.exists():
        print(f"❌ manifest 文件不存在: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    import json
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_ver = manifest.get("meta", {}).get("version", "unknown")
    manifest_plugins = {p["name"]: p for p in manifest.get("plugins", [])}
    total_manifest_rules = sum(len(p.get("rules", [])) for p in manifest_plugins.values())

    print(f"\n{'=' * 50}")
    print(f"[run-lint --audit] 覆盖度审计")
    print(f"{'=' * 50}")
    print(f"  manifest 版本: {manifest_ver}")
    print(f"  manifest 文件: {manifest_path}")
    print(f"  manifest 登记插件: {len(manifest_plugins)} 个")
    print(f"  manifest 登记规则: {total_manifest_rules} 条")
    print()

    # 加载全部 lint 插件
    registry = load_plugins(devroot=devroot, tags=["lint", "md", "validation", "encoding"])
    actual_names = set(registry.list_loaded())
    manifest_names = set(manifest_plugins.keys())

    # 对比
    missing_from_actual = manifest_names - actual_names
    missing_from_manifest = actual_names - manifest_names

    if missing_from_actual:
        print(f"  ⚠  manifest 有但实际未加载的插件 ({len(missing_from_actual)} 个):")
        for name in sorted(missing_from_actual):
            mp = manifest_plugins[name]
            print(f"    - {name} (v{mp.get('version', '?')}) — {mp.get('description', '')}")

    if missing_from_manifest:
        print(f"  ⚠  实际有但 manifest 未登记的插件 ({len(missing_from_manifest)} 个):")
        for name in sorted(missing_from_manifest):
            print(f"    - {name}")

    if not missing_from_actual and not missing_from_manifest:
        print(f"  ✅ 插件覆盖度: 100%（{len(manifest_plugins)}/全匹配）")

    # 规则覆盖度
    print(f"\n  --- 各插件规则明细 ---")
    actual_rules = 0
    for name in sorted(manifest_plugins.keys()):
        if name not in actual_names:
            continue
        mp = manifest_plugins[name]
        rules = mp.get("rules", [])
        fixable_count = sum(1 for r in rules if r.get("fixable"))
        actual_rules += len(rules)
        print(f"    {name} (v{mp.get('version', '?')}): {len(rules)} 条规则（可修复 {fixable_count} 条）")

    print(f"\n  实际可验证规则: {actual_rules} 条")
    print()

    # 路由覆盖度
    routing = manifest.get("routing", {})
    ext_map = routing.get("ext_to_plugin", {})
    print(f"  --- 文件类型路由覆盖 ---")
    for ext, plugins in sorted(ext_map.items()):
        loaded = [p for p in plugins if p in actual_names]
        missing = [p for p in plugins if p not in actual_names]
        if missing:
            print(f"    ⚠  {ext} → {', '.join(plugins)}（缺失: {', '.join(missing)}）")
        else:
            print(f"    ✅ {ext} → {', '.join(plugins)}")

    print(f"\n  {'=' * 50}")
    print(f"  结论: ✅ 审计完成")
    print(f"  {'=' * 50}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="统一 lint CLI 入口（支持 --fix 三阶段闭环 / --audit 覆盖度审计）")
    parser.add_argument("--devroot", required=True, help="Devroot 路径")
    parser.add_argument("--profile", default="lint", help="lint profile 名（默认: lint）")
    parser.add_argument("--tags", default=None, help="逗号分隔的标签列表（与 profile 互斥）")
    parser.add_argument(
        "--files",
        nargs="*",
        help="指定一个或多个文件路径进行 lint（混合类型自动路由）"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="启用 lint→amend→lint 三阶段闭环（检测→修复→重新验证）"
    )
    parser.add_argument(
        "--audit", action="store_true",
        help="覆盖度审计模式：对照 lint-rules-manifest.json 检查规则覆盖度"
    )
    args = parser.parse_args()

    if not HAS_PY_LIB:
        print("错误: py_lib 不可用，无法执行 lint", file=sys.stderr)
        sys.exit(1)

    if args.audit:
        run_audit(devroot=args.devroot)

    print(f"[run-lint] devroot: {args.devroot}")
    if args.fix:
        print(f"[run-lint] 模式: 三阶段闭环（lint→amend→lint）")

    if args.files:
        print(f"[run-lint] 模式: 单文件列表 ({len(args.files)} 个文件)")
        results, has_error, fixed_any = run_files_via_py_lib(
            devroot=args.devroot, files=args.files, fix=args.fix
        )
        remaining = _print_summary(results)
        if has_error:
            print(f"\n  结论: ❌ 存在 {remaining} 处违规")
            sys.exit(1)
        else:
            if args.fix and fixed_any:
                print(f"\n  结论: ✅ lint→amend→lint 闭环完成，全部通过")
            else:
                print(f"\n  结论: ✅ 全部通过")
            sys.exit(0)
    else:
        tags = None
        if args.tags:
            tags = [t.strip() for t in args.tags.split(",")]

        print(f"[run-lint] profile: {args.profile if not tags else 'N/A (tags mode)'}")
        if tags:
            print(f"[run-lint] tags: {tags}")

        results, has_error, fixed_any = run_via_py_lib(
            devroot=args.devroot, profile=args.profile, tags=tags, fix=args.fix
        )
        remaining = _print_summary(results)
        if has_error:
            print(f"\n  结论: ❌ 存在 {remaining} 处违规")
            sys.exit(1)
        else:
            if args.fix and fixed_any:
                print(f"\n  结论: ✅ lint→amend→lint 闭环完成，全部通过")
            else:
                print(f"\n  结论: ✅ 全部通过")
            sys.exit(0)


if __name__ == "__main__":
    main()
