#!/usr/bin/env python3
"""
插件：JavaScript/TypeScript 语法与风格验证器（v1.0.0）
标签：lint, js
依赖：core

职责：调用 ESLint CLI 对 .js/.ts/.jsx/.tsx 文件做语法与风格检测。
支持 --fix 自动修复。

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["lint", "js"])
    result = registry.lint_js.validate(dir_path="/path/to/check")

用法（CLI 直接执行）：
    python lint_js.py --dir "/path/to/check" --fix
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None

# ESLint 扫描的扩展名
JS_EXTENSIONS = {".js", ".ts", ".jsx", ".tsx"}


def _resolve_devroot() -> Path:
    """推断 devroot"""
    if __plugin_registry__:
        devroot = getattr(__plugin_registry__, "devroot", None)
        if devroot:
            return Path(devroot)
    current = Path(__file__).resolve()
    for _ in range(6):
        if current.parent == current:
            break
        current = current.parent
    if (current / "venv").exists():
        return current
    raise RuntimeError("无法自动推断 devroot")


def _get_eslint_cmd(devroot: Path) -> list[str]:
    """构造 ESLint CLI 调用命令列表"""
    eslint_cmd = devroot / "venv" / "eslint" / "node_modules" / ".bin" / "eslint.cmd"
    if not eslint_cmd.exists():
        eslint_cmd = devroot / "venv" / "eslint" / "node_modules" / ".bin" / "eslint"
    config_path = devroot / "venv" / "eslint" / "eslint.config.mjs"
    cmd = [str(eslint_cmd)]
    if config_path.exists():
        cmd.extend(["--config", str(config_path)])
    cmd.extend(["--format", "json"])
    return cmd


def _parse_eslint_output(raw_json: str, target_dir: Path = None) -> tuple:
    """
    解析 ESLint JSON 输出。
    返回 (violations_list, files_with_violations)
    """
    try:
        results = json.loads(raw_json)
    except json.JSONDecodeError:
        return [], 0

    violations = []
    files_with_violations = 0

    for file_result in results:
        file_path = file_result.get("filePath", "")
        messages = file_result.get("messages", [])
        error_count = file_result.get("errorCount", 0)
        warning_count = file_result.get("warningCount", 0)

        if error_count > 0 or warning_count > 0:
            files_with_violations += 1

        for msg in messages:
            line = msg.get("line")
            severity = "error" if msg.get("severity") == 2 else "warn"
            context = f"{msg.get('ruleId', 'unknown')}: {msg.get('message', '')}"
            fixable = msg.get("fix") is not None

            rel_path = file_path
            if target_dir and Path(file_path).is_absolute():
                try:
                    rel_path = str(Path(file_path).relative_to(target_dir))
                except ValueError:
                    rel_path = file_path

            violations.append({
                "file": rel_path,
                "line": line,
                "context": context,
                "severity": severity,
                "fixable": fixable,
            })

    return violations, files_with_violations


def validate_file(filepath: str, fix: bool = False) -> dict:
    """
    检测单个 .js/.ts/.jsx/.tsx 文件。
    返回 plugin-result-schema.json 格式。
    """
    fp = Path(filepath)
    devroot = _resolve_devroot()
    cmd = _get_eslint_cmd(devroot) + [str(fp)]
    if fix:
        cmd.append("--fix")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "schema_version": "1.0.0",
            "plugin": "lint_js",
            "files_scanned": 1,
            "files_with_violations": 1,
            "violations_found": 1,
            "violations": [{"file": str(fp), "line": None, "context": "ESLint 执行超时", "severity": "error", "fixable": False}],
            "metadata": {},
        }
    except Exception as e:
        return {
            "success": False,
            "schema_version": "1.0.0",
            "plugin": "lint_js",
            "files_scanned": 1,
            "files_with_violations": 1,
            "violations_found": 1,
            "violations": [{"file": str(fp), "line": None, "context": f"ESLint 执行异常: {e}", "severity": "error", "fixable": False}],
            "metadata": {},
        }

    violations, files_with_violations = _parse_eslint_output(result.stdout)

    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "lint_js",
        "files_scanned": 1,
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {
            "eslint_exit_code": result.returncode,
        },
    }


def validate(dir_path: str = None, fix: bool = False) -> dict:
    """
    扫描指定目录下的 .js/.ts/.jsx/.tsx 文件。
    返回 plugin-result-schema.json 格式。
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

    devroot = _resolve_devroot()
    cmd = _get_eslint_cmd(devroot) + [str(target_dir)]
    if fix:
        cmd.append("--fix")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "schema_version": "1.0.0",
            "plugin": "lint_js",
            "files_scanned": 0,
            "files_with_violations": 0,
            "violations_found": 1,
            "violations": [{"file": str(target_dir), "line": None, "context": "ESLint 目录扫描超时", "severity": "error", "fixable": False}],
            "metadata": {},
        }
    except Exception as e:
        return {
            "success": False,
            "schema_version": "1.0.0",
            "plugin": "lint_js",
            "files_scanned": 0,
            "files_with_violations": 0,
            "violations_found": 1,
            "violations": [{"file": str(target_dir), "line": None, "context": f"ESLint 执行异常: {e}", "severity": "error", "fixable": False}],
            "metadata": {},
        }

    violations, files_with_violations = _parse_eslint_output(result.stdout, target_dir)

    try:
        files_scanned = len(json.loads(result.stdout))
    except Exception:
        files_scanned = 0

    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "lint_js",
        "files_scanned": files_scanned,
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {
            "eslint_exit_code": result.returncode,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="JavaScript/TypeScript 语法与风格验证器")
    parser.add_argument("--dir", required=True, help="要扫描的目录路径")
    parser.add_argument("--fix", action="store_true", help="自动修复发现的问题")
    args = parser.parse_args()

    result = validate(dir_path=args.dir, fix=args.fix)
    print(f"扫描文件: {result['files_scanned']} 个")
    print(f"违规文件: {result['files_with_violations']} 个")
    print(f"违规项: {result['violations_found']} 处")

    if result["violations"]:
        print("\n【违规详情】")
        for v in result["violations"]:
            line_info = f":{v['line']}" if v.get("line") else ""
            print(f"  {v['file']}{line_info} — {v['context']}")
        sys.exit(1)
    else:
        print("\n所有 JS/TS 文件合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
