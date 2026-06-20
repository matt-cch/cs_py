#!/usr/bin/env python3
"""
插件：JSON 语法验证器（v1.0.0）
标签：lint, json
依赖：core

职责：递归扫描指定目录下的所有 .json / .jsonc 文件，使用 json.load 验证语法有效性。

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["lint", "json"])
    result = registry.lint_json.validate(dir_path="/path/to/check")

用法（CLI 直接执行）：
    python lint_json.py --dir "/path/to/check"
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None


def _check_json_file(filepath: Path) -> dict:
    """
    验证单个 JSON 文件语法。
    返回：{"valid": bool, "error": str or None}
    """
    try:
        content = filepath.read_text(encoding="utf-8-sig")
        json.loads(content)
        return {"valid": True, "error": None}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"JSONDecodeError: {e}"}
    except Exception as e:
        return {"valid": False, "error": f"{type(e).__name__}: {e}"}


def validate_file(filepath: str) -> dict:
    """
    验证单个 JSON 文件语法。

    参数:
        filepath: 文件路径

    返回:
        {
            "files_scanned": 1,
            "violations_found": int,
            "files_with_violations": int,
            "violations": [
                {"file": str, "error": str}
            ]
        }
    """
    fp = Path(filepath)
    result = _check_json_file(fp)
    violations = []
    files_with_violations = 0
    if not result["valid"]:
        files_with_violations = 1
        violations.append({
            "file": str(fp),
            "line": None,
            "context": result["error"],
            "severity": "error",
            "fixable": False,
        })
    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "lint_json",
        "files_scanned": 1,
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {},
    }


def validate(dir_path: str = None) -> dict:
    """
    扫描指定目录下的所有 JSON 文件，验证语法。

    参数:
        dir_path: 要扫描的目录路径。如未传入，尝试从 __plugin_registry__ 获取 devroot。

    返回:
        {
            "files_scanned": int,
            "violations_found": int,
            "files_with_violations": int,
            "violations": [
                {"file": str, "error": str}
            ]
        }
    """
    target_dir = None
    if dir_path:
        target_dir = Path(dir_path)
    elif __plugin_registry__:
        devroot = getattr(__plugin_registry__, "devroot", None)
        if devroot:
            target_dir = Path(devroot)

    if not target_dir or not target_dir.exists():
        raise ValueError("dir_path 未传入且无法从 registry 推导，或目标目录不存在。")

    json_files = list(target_dir.rglob("*.json"))
    # 也检查 .jsonc（带注释的 JSON，用 json.loads 宽容解析）
    json_files += list(target_dir.rglob("*.jsonc"))

    violations = []
    files_with_violations = 0

    for jf in json_files:
        result = _check_json_file(jf)
        if not result["valid"]:
            rel_path = jf.relative_to(target_dir)
            files_with_violations += 1
            violations.append({
                "file": str(rel_path),
                "line": None,
                "context": result["error"],
                "severity": "error",
                "fixable": False,
            })

    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "lint_json",
        "files_scanned": len(json_files),
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {},
    }


def main():
    parser = argparse.ArgumentParser(description="JSON 语法验证器")
    parser.add_argument("--dir", required=True, help="要扫描的目录路径")
    args = parser.parse_args()

    result = validate(dir_path=args.dir)
    print(f"扫描文件: {result['files_scanned']} 个")
    print(f"违规文件: {result['files_with_violations']} 个")

    if result["violations"]:
        print("\n【违规详情】")
        for v in result["violations"]:
            print(f"  {v['file']} — {v['context']}")
        sys.exit(1)
    else:
        print("\n所有 JSON 文件语法合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
