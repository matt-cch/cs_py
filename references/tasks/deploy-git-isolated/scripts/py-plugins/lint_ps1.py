#!/usr/bin/env python3
"""
插件：PowerShell 脚本语法验证器（v1.0.0）
标签：lint, ps1
依赖：core

职责：递归扫描指定目录下的所有 .ps1 文件，使用 PowerShell PSParser::Tokenize 验证语法。

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["lint", "ps1"])
    result = registry.lint_ps1.validate(dir_path="/path/to/check")

用法（CLI 直接执行）：
    python lint_ps1.py --dir "/path/to/check"
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None


def _check_ps1_file(filepath: Path) -> dict:
    """
    使用 PowerShell PSParser::Tokenize 验证 .ps1 语法。
    返回：{"valid": bool, "error": str or None}
    """
    ps_cmd = (
        "$errors = @(); "
        f"$content = Get-Content -LiteralPath '{filepath}' -Raw; "
        "$null = [System.Management.Automation.PSParser]::Tokenize($content, [ref]$errors); "
        "if ($errors.Count -gt 0) { "
        "    Write-Output ('ERROR_COUNT=' + $errors.Count); "
        "    foreach ($e in $errors) { Write-Output ($e.Message) } "
        "} else { Write-Output 'OK' }"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=False,
            timeout=30,
        )
        # PowerShell 输出编码可能是 GBK(ANSI) 或 UTF-8，用 replace 策略安全解码
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        stderr_text = result.stderr.decode("utf-8", errors="replace").strip() if result.stderr else ""
        if stdout == "OK" and not stderr_text:
            return {"valid": True, "error": None}
        else:
            # 截断错误信息，避免过长
            lines = stdout.splitlines()
            summary = lines[0] if lines else "未知错误"
            detail = " | ".join(lines[1:4]) if len(lines) > 1 else ""
            err_msg = f"{summary}; {detail}"
            if stderr_text:
                err_msg += f" | stderr: {stderr_text[:200]}"
            return {"valid": False, "error": err_msg}
    except subprocess.TimeoutExpired:
        return {"valid": False, "error": "PowerShell 执行超时"}
    except Exception as e:
        return {"valid": False, "error": f"{type(e).__name__}: {e}"}


def validate_file(filepath: str) -> dict:
    """
    验证单个 PowerShell 文件语法。

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
    result = _check_ps1_file(fp)
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
        "plugin": "lint_ps1",
        "files_scanned": 1,
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {},
    }


def validate(dir_path: str = None) -> dict:
    """
    扫描指定目录下的所有 .ps1 文件，验证语法。

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

    ps1_files = list(target_dir.rglob("*.ps1"))
    violations = []
    files_with_violations = 0

    for pf in ps1_files:
        result = _check_ps1_file(pf)
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
        "plugin": "lint_ps1",
        "files_scanned": len(ps1_files),
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {},
    }


def main():
    parser = argparse.ArgumentParser(description="PowerShell 脚本语法验证器")
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
        print("\n所有 PowerShell 脚本语法合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
