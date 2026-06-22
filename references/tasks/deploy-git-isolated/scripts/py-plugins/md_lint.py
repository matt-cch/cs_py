#!/usr/bin/env python3
"""
插件：Markdown 格式 Linter（v1.2.0）
标签：md, validation
依赖：core

职责：扫描 Markdown 文件，检测并修复 frontmatter 合规性问题。
规则唯一真源：.cursor/rules/markdown-docs-format.mdc（以下简称 mdc）

已实现规则（与 mdc 逐条对齐）：
┌────────┬──────────────────────────────────────────────────────────────┬──────────┐
│ mdc 节 │ 规则内容                                                      │ 实现状态 │
├────────┼──────────────────────────────────────────────────────────────┼──────────┤
│ 1.1    │ 文件开头（第 1 行）必须有 YAML frontmatter（--- 定界）         │ ✅       │
│ 1.1    │ frontmatter 必须包含 title / description / date / meta        │ ✅       │
│ 1.1    │ date 格式严格为 YYYY-MM-DD                                    │ ✅       │
│ 1.2    │ 禁止 description 与 date 拼接在同一行                         │ ✅       │
│ 1.2    │ 正文中严禁使用 --- 水平分隔线（代码块内例外，见下方）           │ ✅       │
│ 7      │ SKILL.md / AGENTS.md 等元文档不受 frontmatter 强制约束        │ ✅       │
├────────┼──────────────────────────────────────────────────────────────┼──────────┤
│ 1.2    │ 禁止 frontmatter 结束符后空一行再写 ---                        │ ⚠️ 间接  │
│        │ （通过"超过 2 个 ---"间接覆盖，不精确区分语义）                 │          │
│ 1.2    │ 禁止使用 Obsidian 不兼容的复杂 YAML 类型                       │ ❌ 未实现 │
│        │ （边界模糊，机器检测困难）                                     │          │
└────────┴──────────────────────────────────────────────────────────────┴──────────┘

代码块内 --- 例外处理：
- mdc 1.2 允许代码块内展示 frontmatter 格式示例使用 ---
- 本实现通过 ``` 配对追踪识别代码块边界，块内 --- 不视为污染

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="...", tags=["md", "validation"])
    result = registry.md_lint.scan(dir_path="/path/to/docs")

用法（CLI 直接执行）：
    python md_lint.py --dir "/path/to/docs" --fix
"""
import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 可选：通过 __plugin_registry__ 访问 devroot
__plugin_registry__ = None

# frontmatter date 格式正则
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 例外文件：具有约定俗成自身格式要求的元文档
# 来源：.cursor/rules/markdown-docs-format.mdc 第 7 行
_EXCLUDED_FILENAMES = {
    "SKILL.md",
    "AGENTS.md",
}


def _is_excluded_file(filepath: Path) -> bool:
    """判断文件是否在 frontmatter 强制约束的例外列表中

    豁免范围（来源：.cursor/rules/markdown-docs-format.mdc）：
    - SKILL.md / AGENTS.md 等约定俗成元文档
    - .cursor/rules/*.mdc（Cursor Rules，自有 frontmatter 规范）
    """
    if filepath.name in _EXCLUDED_FILENAMES:
        return True
    if filepath.suffix == ".mdc":
        return True
    return False


def _extract_frontmatter_lines(content: str):
    """
    提取 frontmatter 的边界和内部行。
    返回：(start_line_no, end_line_no, fm_lines) 或 None（无 frontmatter）

    注意：mdc 1.1 要求 frontmatter 位于"文件开头"，即第 1 行必须是 ---。
    本函数只负责提取，"开头"校验由调用方在 _check_frontmatter_fields 中完成。
    """
    lines = content.splitlines()
    start = None
    for idx, line in enumerate(lines, start=1):
        if line.strip() == "---":
            if start is None:
                start = idx
            else:
                # 找到闭合 ---
                fm_lines = lines[start:idx - 1]  # 不含闭合行
                return start, idx, fm_lines
    return None


def _check_frontmatter_fields(content: str) -> list:
    """
    检测 frontmatter 字段完整性。
    返回违规列表，每项包含 line_no（尽可能）和 context。
    """
    violations = []
    extracted = _extract_frontmatter_lines(content)

    if extracted is None:
        violations.append({
            "line": 1,
            "context": "缺少 YAML frontmatter（必须以 --- 开头和结束）"
        })
        return violations

    start_line, end_line, fm_lines = extracted

    # mdc 1.1: frontmatter 必须位于"文件开头"（第 1 行）
    if start_line != 1:
        violations.append({
            "line": start_line,
            "context": f"frontmatter 必须从第 1 行开始（当前在第 {start_line} 行）"
        })

    # 逐行解析键值（简化 YAML，只处理顶层键）
    keys_found = set()
    description_line_no = None
    description_has_date_glued = False

    for rel_idx, line in enumerate(fm_lines, start=1):
        line_no = start_line + rel_idx
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # 检测 description 和 date 拼接
        if stripped.startswith("description:"):
            description_line_no = line_no
            if "date:" in stripped:
                description_has_date_glued = True

        # 顶层键检测（只取冒号前的键名）
        if ":" in stripped:
            key = stripped.split(":", 1)[0].strip()
            keys_found.add(key)

    # 必填字段检查
    required_fields = {
        "title": "缺少必填字段 title",
        "description": "缺少必填字段 description",
        "date": "缺少必填字段 date",
        "meta": "缺少必填字段 meta（无内容时写 meta: {}）",
    }
    for key, msg in required_fields.items():
        if key not in keys_found:
            violations.append({"line": start_line, "context": msg})

    # description 与 date 拼接检查
    if description_has_date_glued:
        violations.append({
            "line": description_line_no or start_line,
            "context": "description 行末尾拼接了 date，必须换行分隔"
        })

    # date 格式检查
    for rel_idx, line in enumerate(fm_lines, start=1):
        stripped = line.strip()
        if stripped.startswith("date:"):
            val = stripped.split(":", 1)[1].strip()
            if not _DATE_RE.match(val):
                violations.append({
                    "line": start_line + rel_idx,
                    "context": f"date 格式错误（期望 YYYY-MM-DD）：{val}"
                })
            break

    return violations


def _check_frontmatter_dashes(content: str) -> list:
    """
    检测 frontmatter 边界污染（正文中的 --- 水平分隔线）。
    返回违规列表，每项包含 line_no 和 original_line。

    mdc 1.2 例外：代码块内（``` 包裹）的 --- 不视为污染。
    本实现通过追踪 ``` 配对来识别代码块边界。
    """
    violations = []
    lines = content.splitlines()
    dash_count = 0
    inside_code_block = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # 追踪代码块边界（``` 开头，支持可选语言标识）
        if stripped.startswith("```"):
            inside_code_block = not inside_code_block
            continue

        if stripped == "---":
            dash_count += 1
            if dash_count > 2:
                # 第三个及以后的 --- 属于正文
                # 代码块内例外（mdc 1.2 唯一例外）
                if not inside_code_block:
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


def _fix_frontmatter_fields(content: str) -> str:
    """
    自动修复 frontmatter 字段问题（目前只修复 description/date 拼接）。
    """
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        # 检测 description 行把 date 吸到同一行的情况
        if line.strip().startswith("description:") and "date:" in line.strip():
            parts = line.strip().split("date:", 1)
            desc_part = parts[0].rstrip()
            date_part = "date:" + parts[1].lstrip()
            # 保留原缩进
            indent = line[:len(line) - len(line.lstrip())]
            new_lines.append(indent + desc_part)
            new_lines.append(indent + date_part)
        else:
            new_lines.append(line)
    result = "\n".join(new_lines)
    if content.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def validate_file(filepath: str, fix: bool = False, strategy="delete") -> dict:
    """
    验证单个 Markdown 文件的 frontmatter 完整性和正文 --- 污染。

    返回 Plugin Result Schema v1.0.0 格式 dict。
    """
    fp = Path(filepath)
    content = fp.read_text(encoding="utf-8")

    violations = []
    files_with_violations = 0
    files_fixed = 0
    fixed_content = content

    # 1. frontmatter 字段校验（例外文件跳过，来源：markdown-docs-format.mdc）
    if not _is_excluded_file(fp):
        field_v = _check_frontmatter_fields(content)
        if field_v:
            files_with_violations = 1
            for v in field_v:
                violations.append({
                    "file": str(fp),
                    "line": v["line"],
                    "context": v["context"],
                })
            if fix:
                fixed_content = _fix_frontmatter_fields(fixed_content)
                files_fixed = 1

    # 2. --- 污染校验（所有文件都检查）
    dash_v = _check_frontmatter_dashes(fixed_content)
    if dash_v:
        if not files_with_violations:
            files_with_violations = 1
        for v in dash_v:
            violations.append({
                "file": str(fp),
                "line": v["line"],
                "context": "正文出现 ---（frontmatter 边界污染）",
            })
        if fix:
            fixed_content = _fix_content(fixed_content, strategy=strategy)
            files_fixed = 1

    if fix and files_fixed:
        fp.write_text(fixed_content, encoding="utf-8")

    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "md_lint",
        "files_scanned": 1,
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {
            "files_fixed": files_fixed,
        },
    }


def scan(dir_path: str = None, fix: bool = False, strategy="delete") -> dict:
    """
    扫描指定目录下的所有 .md 文件，检测 frontmatter 完整性和正文 --- 污染。

    返回 Plugin Result Schema v1.0.0 格式 dict。
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

        rel_path = str(md_file.relative_to(target_dir))
        file_has_v = False
        fixed_content = content

        # 1. frontmatter 字段校验（例外文件跳过）
        if not _is_excluded_file(md_file):
            field_v = _check_frontmatter_fields(content)
            if field_v:
                file_has_v = True
                for v in field_v:
                    violations.append({
                        "file": rel_path,
                        "line": v["line"],
                        "context": v["context"],
                    })
                if fix:
                    fixed_content = _fix_frontmatter_fields(fixed_content)

        # 2. --- 污染校验（所有文件都检查）
        dash_v = _check_frontmatter_dashes(fixed_content)
        if dash_v:
            file_has_v = True
            for v in dash_v:
                violations.append({
                    "file": rel_path,
                    "line": v["line"],
                    "context": "正文出现 ---（frontmatter 边界污染）",
                })
            if fix:
                fixed_content = _fix_content(fixed_content, strategy=strategy)

        if file_has_v:
            files_with_violations += 1
            if fix:
                md_file.write_text(fixed_content, encoding="utf-8")
                files_fixed += 1

    return {
        "success": True,
        "schema_version": "1.0.0",
        "plugin": "md_lint",
        "files_scanned": len(md_files),
        "files_with_violations": files_with_violations,
        "violations_found": len(violations),
        "violations": violations,
        "metadata": {
            "files_fixed": files_fixed,
        },
    }


# 别名：validate = scan，兼容 run-lint 插件接口
validate = scan


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
    print(f"违规项: {result['violations_found']} 处")

    if args.fix:
        files_fixed = result.get("metadata", {}).get("files_fixed", 0)
        print(f"已修复文件: {files_fixed} 个")

    if result["violations"]:
        print("\n【违规详情】")
        for v in result["violations"]:
            print(f"  {v['file']}:{v['line']} — {v['context']}")
        sys.exit(1)
    else:
        print("\n所有 Markdown 格式合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
