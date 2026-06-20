#!/usr/bin/env python3
"""
插件：Python 脚本语法验证器（v1.0.0）
标签：lint, python
依赖：core

职责：递归扫描指定目录下的所有 .py 文件，使用 py_compile 验证语法有效性。

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["lint", "python"])
    result = registry.lint_python.validate(dir_path="/path/to/check")

用法（CLI 直接执行）：
    python lint_python.py --dir "/path/to/check"
"""
import argparse
import py_compile
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None


def _check_python_file(filepath: Path) -> dict:
    """
    使用 py_compile 验证单个 Python 文件语法。
    返回：{"valid": bool, "error": str or None}
    """
    try:
        # doraise=True 确保异常抛出
        py_compile.compile(str(filepath), doraise=True)
        return {"valid": True, "error": None}
    except py_compile.PyCompileError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": False, "error": f"{type(e).__name__}: {e}"}


def validate_file(filepath: str) -> dict:
    """
    验证单个 Python 文件语法。

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
    result = _check_python_file(fp)
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
        "plugin": "lint_python",
        "files_scanned": 1,
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {},
    }


def validate(dir_path: str = None) -> dict:
    """
    扫描指定目录下的所有 .py 文件，验证语法。

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

    py_files = list(target_dir.rglob("*.py"))
    violations = []
    files_with_violations = 0

    for pf in py_files:
        result = _check_python_file(pf)
        if not result["valid"]:
            rel_path = pf.relative_to(target_dir)
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
        "plugin": "lint_python",
        "files_scanned": len(py_files),
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {},
    }


def main():
    parser = argparse.ArgumentParser(description="Python 脚本语法验证器")
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
        print("\n所有 Python 脚本语法合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
