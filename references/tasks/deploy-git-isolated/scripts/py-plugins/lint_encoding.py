#!/usr/bin/env python3
"""
插件：文件编码/BOM/行尾符/UTF-8完整性检测器（v1.2.0）
标签：lint, encoding
依赖：core

职责：递归扫描指定目录下的文本文件，检测：
  - UTF-8 BOM 头（前3字节 EF BB BF）
  - 双 BOM（前6字节中出现两次 EF BB BF）
  - CRLF（0D 0A）与 LF（0A）行尾符数量
  - UTF-8 完整性（截断/损坏的多字节序列，所有文本文件适用）

按文件类型区分期望编码（来自 AGENTS.md）：
  - .ps1 含中文 → 期望 UTF-8 with BOM（仅检测双 BOM）
  - .py / .js / .ts / .json / .md / .yml / .yaml / .toml / .sh → 期望 UTF-8 no BOM
  - .bat / .cmd → 期望 GBK（ANSI），不强制检测

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["lint", "encoding"])
    result = registry.lint_encoding.validate(dir_path="/path/to/check")

用法（CLI 直接执行）：
    python lint_encoding.py --dir "/path/to/check"
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

__plugin_registry__ = None

# AGENTS.md 定义的编码要求
NO_BOM_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".md", ".json", ".jsonc",
    ".yml", ".yaml", ".toml", ".sh",
    ".jsonl",
}

BOM_EXPECTED_EXTENSIONS = {".ps1"}

SKIP_EXTENSIONS = {".bat", ".cmd", ".exe", ".dll", ".zip", ".png", ".jpg", ".gif", ".ico"}


def _check_encoding(filepath: Path) -> dict:
    """
    检测单个文件的编码特征。
    返回：{"has_bom": bool, "has_double_bom": bool, "crlf": int, "lf": int, "violations": [str], "fixable": bool}
    """
    ext = filepath.suffix.lower()

    # 跳过二进制文件
    if ext in SKIP_EXTENSIONS:
        return {"has_bom": False, "has_double_bom": False, "crlf": 0, "lf": 0, "violations": [], "fixable": False}

    try:
        raw = filepath.read_bytes()
    except Exception as e:
        return {"has_bom": False, "has_double_bom": False, "crlf": 0, "lf": 0, "violations": [f"读取失败: {e}"], "fixable": False}

    if not raw:
        return {"has_bom": False, "has_double_bom": False, "crlf": 0, "lf": 0, "violations": [], "fixable": False}

    # BOM 检测
    has_bom = len(raw) >= 3 and raw[:3] == b"\xef\xbb\xbf"
    has_double_bom = has_bom and len(raw) >= 6 and raw[3:6] == b"\xef\xbb\xbf"

    # 行尾符统计
    crlf = raw.count(b"\r\n")
    # 纯 LF 数量 = 总 \n 数 - CRLF 中的 \n 数
    total_lf = raw.count(b"\n")
    lf = total_lf - crlf

    violations = []
    fixable = False

    # 双 BOM：任何文件都不允许
    if has_double_bom:
        violations.append("双 BOM 检测（前6字节出现两次 EF BB BF）")
        fixable = True

    # 按扩展名判断 BOM 期望
    if ext in NO_BOM_EXTENSIONS and has_bom:
        violations.append(f"{ext} 文件不应包含 UTF-8 BOM（AGENTS.md 规定）")
        fixable = True

    # CRLF 检测：除 .ps1/.bat/.cmd 外，所有文本文件强制 LF
    # .ps1 保持系统默认（Windows 原生生态），.bat/.cmd 为 GBK 批处理文件
    CRLF_EXEMPT_EXTENSIONS = {".ps1", ".bat", ".cmd"}
    if ext not in CRLF_EXEMPT_EXTENSIONS and crlf > 0:
        violations.append(f"{ext} 文件必须使用 LF 换行符，检测到 {crlf} 处 CRLF")
        fixable = True

    # UTF-8 完整性检测（所有文本文件适用）
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        msg = str(e)
        if "unexpected end of data" in msg:
            violations.append(f"UTF-8 序列截断（文件末尾不完整多字节序列）: {msg}")
        elif "invalid start byte" in msg or "invalid continuation byte" in msg:
            violations.append(f"UTF-8 编码损坏（中间存在非法字节）: {msg}")
        else:
            violations.append(f"UTF-8 编码异常: {msg}")
        # 不可自动修复，不修改 fixable

    return {
        "has_bom": has_bom,
        "has_double_bom": has_double_bom,
        "crlf": crlf,
        "lf": lf,
        "violations": violations,
        "fixable": fixable
    }


def _fix_file(filepath: Path) -> dict:
    """
    修复单个文件的编码问题。
    返回：{"fixed": bool, "actions": [str], "error": str or None}
    """
    ext = filepath.suffix.lower()
    raw = filepath.read_bytes()
    if not raw:
        return {"fixed": False, "actions": [], "error": None}

    has_bom = len(raw) >= 3 and raw[:3] == b"\xef\xbb\xbf"
    crlf_count = raw.count(b"\r\n")

    if not has_bom and crlf_count == 0:
        return {"fixed": False, "actions": [], "error": None}

    try:
        # 解码（去除 BOM 后）
        if has_bom:
            content = raw[3:].decode("utf-8", errors="replace")
        else:
            content = raw.decode("utf-8", errors="replace")

        actions = []

        # CRLF → LF
        if crlf_count > 0:
            content = content.replace("\r\n", "\n")
            actions.append(f"CRLF→LF({crlf_count})")

        # 重新编码
        encoded = content.encode("utf-8")

        # .ps1 含中文 → 加回单 BOM
        if ext in BOM_EXPECTED_EXTENSIONS:
            try:
                content.encode("ascii")
                final = encoded  # 纯 ASCII，无 BOM
            except UnicodeEncodeError:
                final = b"\xef\xbb\xbf" + encoded
                if has_bom:
                    actions.append("双BOM→单BOM")
                else:
                    actions.append("加BOM")
        else:
            # 非 .ps1 去除 BOM
            final = encoded
            if has_bom:
                actions.append("去BOM")

        filepath.write_bytes(final)

        # 回读验证
        verify = filepath.read_bytes()
        verify_crlf = verify.count(b"\r\n")
        verify_double = len(verify) >= 6 and verify[:3] == b"\xef\xbb\xbf" and verify[3:6] == b"\xef\xbb\xbf"

        if verify_crlf > 0 or verify_double:
            return {"fixed": False, "actions": actions, "error": f"验证失败: CRLF={verify_crlf}, DBL_BOM={verify_double}"}

        return {"fixed": True, "actions": actions, "error": None}

    except Exception as e:
        return {"fixed": False, "actions": [], "error": f"{type(e).__name__}: {e}"}


def validate_file(filepath: str, fix: bool = False) -> dict:
    """
    检测单个文件的编码/BOM/行尾符问题。

    参数:
        filepath: 文件路径
        fix: 是否自动修复（默认 False）

    返回:
        {
            "files_scanned": 1,
            "violations_found": int,
            "files_with_violations": int,
            "files_fixed": int,
            "violations": [
                {"file": str, "line": None, "context": str}
            ],
            "fixed_files": [
                {"file": str, "actions": [str]}
            ]
        }
    """
    fp = Path(filepath)
    result = _check_encoding(fp)
    violations = []
    files_with_violations = 0
    fixed_files = []
    files_fixed = 0

    if result["violations"]:
        files_with_violations = 1
        for v in result["violations"]:
            violations.append({
                "file": str(fp),
                "line": None,
                "context": v
            })

        if fix and result["fixable"]:
            fix_result = _fix_file(fp)
            if fix_result["fixed"]:
                files_fixed = 1
                fixed_files.append({
                    "file": str(fp),
                    "actions": fix_result["actions"]
                })

    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "lint_encoding",
        "files_scanned": 1,
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {
            "files_fixed": files_fixed,
            "fixed_files": fixed_files,
            "check_details": {
                "has_bom": result["has_bom"],
                "has_double_bom": result["has_double_bom"],
                "crlf_count": result["crlf"],
                "lf_count": result["lf"],
                "utf8_valid": not any("UTF-8" in v and "截断" in v or "损坏" in v or "异常" in v for v in result["violations"]),
            },
        },
    }


def validate(dir_path: str = None, fix: bool = False) -> dict:
    """
    扫描指定目录下的文本文件，检测编码/BOM/行尾符问题。

    参数:
        dir_path: 要扫描的目录路径。如未传入，尝试从 __plugin_registry__ 获取 devroot。
        fix: 是否自动修复发现的问题（默认 False，只检测不修改）

    返回:
        {
            "files_scanned": int,
            "violations_found": int,
            "files_with_violations": int,
            "files_fixed": int,
            "violations": [
                {"file": str, "line": None, "context": str}
            ],
            "fixed_files": [
                {"file": str, "actions": [str]}
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

    # 扫描常见文本文件（排除二进制和已知大目录）
    text_exts = NO_BOM_EXTENSIONS | BOM_EXPECTED_EXTENSIONS | {".txt", ".ini", ".cfg", ".log"}
    all_files = []
    for ext in text_exts:
        all_files.extend(target_dir.rglob(f"*{ext}"))

    violations = []
    files_with_violations = 0
    fixed_files = []
    files_fixed = 0

    for tf in all_files:
        # 跳过 venv/ 等隔离目录
        parts = tf.relative_to(target_dir).parts
        if any(p in ("venv", "node_modules", ".git", "__pycache__") for p in parts):
            continue

        result = _check_encoding(tf)
        rel_path = str(tf.relative_to(target_dir))

        if result["violations"]:
            files_with_violations += 1
            for v in result["violations"]:
                violations.append({
                    "file": rel_path,
                    "line": None,
                    "context": v
                })

            if fix and result["fixable"]:
                fix_result = _fix_file(tf)
                if fix_result["fixed"]:
                    files_fixed += 1
                    fixed_files.append({
                        "file": rel_path,
                        "actions": fix_result["actions"]
                    })

    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "lint_encoding",
        "files_scanned": len(all_files),
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {
            "files_fixed": files_fixed,
            "fixed_files": fixed_files,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="文件编码/BOM/行尾符检测器")
    parser.add_argument("--dir", required=True, help="要扫描的目录路径")
    parser.add_argument("--fix", action="store_true", help="自动修复发现的问题（去BOM/CRLF→LF）")
    args = parser.parse_args()

    result = validate(dir_path=args.dir, fix=args.fix)
    print(f"扫描文件: {result['files_scanned']} 个")
    print(f"违规文件: {result['files_with_violations']} 个")
    print(f"违规项: {result['violations_found']} 处")

    if args.fix:
        files_fixed = result.get("metadata", {}).get("files_fixed", 0)
        print(f"已修复文件: {files_fixed} 个")
        fixed_files = result.get("metadata", {}).get("fixed_files", [])
        if fixed_files:
            print("\n【修复详情】")
            for f in fixed_files:
                print(f"  {f['file']} — {' | '.join(f['actions'])}")

    remaining = result["violations_found"]
    if result.get("metadata", {}).get("files_fixed", 0):
        # fix 后重新统计剩余违规
        result2 = validate(dir_path=args.dir, fix=False)
        remaining = result2["violations_found"]
        if remaining > 0:
            print(f"\n修复后仍剩余违规: {remaining} 处")

    if remaining > 0:
        print("\n【违规详情】")
        for v in result["violations"]:
            print(f"  {v['file']} — {v['context']}")
        sys.exit(1)
    else:
        print("\n所有文件编码/行尾符合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
