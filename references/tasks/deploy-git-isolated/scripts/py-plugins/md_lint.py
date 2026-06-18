#!/usr/bin/env python3
"""
插件：Markdown 格式 Linter（v1.0.0）
标签：md, validation
依赖：core

职责：扫描 Markdown 文件，检测并修复 frontmatter 边界污染（正文中的 --- 水平分隔线）。
      支持 CLI 调用和 py_lib 插件加载。

规则（来自 .cursor/rules/markdown-docs-format.mdc）：
1. YAML frontmatter 的 --- 定界符有且仅有一对，位于文件开头
2. 正文中绝对禁止出现独立的 --- 行
3. 视觉分隔改用空行、## 二级标题或 ***（水平规则备选）

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["md", "validation"])
    result = registry.md_lint.scan(dir_path="/path/to/docs")
    # result = {"files_scanned": 10, "violations": [...], "fixed": 5}

用法（CLI 直接执行）：
    python md_lint.py --dir "/path/to/docs" --fix
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 可选：通过 __plugin_registry__ 访问 devroot
__plugin_registry__ = None


def _check_frontmatter_dashes(content: str) -> list:
    """
    检测 frontmatter 边界污染。
    返回违规列表，每项包含 line_no 和 original_line。
    """
    violations = []
    lines = content.splitlines()
    dash_count = 0

    for idx, line in enumerate(lines, start=1):
        if line.strip() == "---":
            dash_count += 1
            if dash_count > 2:
                violations.append({"line": idx, "original": line})
    return violations


def _fix_content(content: str, strategy="delete") -> str:
    """
    修复正文中的 ---。
    strategy:
        - "delete": 直接删除 --- 行（默认）
        - "replace_stars": 替换为 ***
    """
    lines = content.splitlines()
    dash_count = 0
    new_lines = []

    for line in lines:
        if line.strip() == "---":
            dash_count += 1
            if dash_count <= 2:
                new_lines.append(line)
            else:
                if strategy == "replace_stars":
                    new_lines.append("***")
                # delete: 不添加任何内容
        else:
            new_lines.append(line)

    result = "\n".join(new_lines)
    # 保持原文件末尾换行符风格
    if content.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def scan(dir_path: str = None, fix: bool = False, strategy="delete") -> dict:
    """
    扫描指定目录下的所有 .md 文件，检测 frontmatter 边界污染。

    参数:
        dir_path: 要扫描的目录路径。如未传入，尝试从 __plugin_registry__ 获取 devroot。
        fix: 是否自动修复（默认 False，只检测不修改）
        strategy: 修复策略，"delete" 或 "replace_stars"

    返回:
        {
            "files_scanned": int,
            "violations_found": int,
            "files_with_violations": int,
            "files_fixed": int,
            "violations": [
                {
                    "file": str,
                    "line": int,
                    "context": str
                }
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
        raise ValueError(
            "dir_path 未传入且无法从 registry 推导，"
            "或目标目录不存在。"
        )

    md_files = list(target_dir.rglob("*.md"))
    violations = []
    files_with_violations = 0
    files_fixed = 0

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        file_violations = _check_frontmatter_dashes(content)

        if file_violations:
            rel_path = md_file.relative_to(target_dir)
            files_with_violations += 1
            for v in file_violations:
                violations.append({
                    "file": str(rel_path),
                    "line": v["line"],
                    "context": v["original"]
                })

            if fix:
                fixed_content = _fix_content(content, strategy=strategy)
                md_file.write_text(fixed_content, encoding="utf-8")
                files_fixed += 1

    return {
        "files_scanned": len(md_files),
        "violations_found": len(violations),
        "files_with_violations": files_with_violations,
        "files_fixed": files_fixed,
        "violations": violations
    }


def main():
    parser = argparse.ArgumentParser(description="Markdown 格式 Linter")
    parser.add_argument("--dir", required=True, help="要扫描的目录路径")
    parser.add_argument("--fix", action="store_true", help="自动修复违规")
    parser.add_argument(
        "--strategy", choices=["delete", "replace_stars"], default="delete",
        help="修复策略：delete（删除）或 replace_stars（替换为 ***）"
    )
    args = parser.parse_args()

    result = scan(dir_path=args.dir, fix=args.fix, strategy=args.strategy)

    print(f"扫描文件: {result['files_scanned']} 个")
    print(f"违规文件: {result['files_with_violations']} 个")
    print(f"违规行数: {result['violations_found']} 处")

    if args.fix:
        print(f"已修复文件: {result['files_fixed']} 个")

    if result["violations"]:
        print("\n【违规详情】")
        for v in result["violations"]:
            print(f"  {v['file']}:{v['line']} — 正文出现 ---")
        sys.exit(1)
    else:
        print("\n所有 Markdown 格式合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
