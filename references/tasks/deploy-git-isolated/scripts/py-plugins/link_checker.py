#!/usr/bin/env python3
"""
插件：Markdown 内部相对链接验证器（v1.2.0）
标签：md, validation
依赖：core, constants

职责：扫描指定目录下的所有 .md 文件，提取内部相对链接，验证目标文件是否存在；
      同时检测 frontmatter 边界污染（正文中的 --- 水平分隔线）。

用法（通过 py_lib 加载）：
    registry = load_plugins(devroot="D:/pjt/cursor/cs_py", tags=["md", "validation"])
    result = registry.link_checker.validate(
        task_dir="D:/pjt/cursor/cs_py/references/tasks/deploy-git-isolated"
    )
    # result = {"checked": 15, "broken": 0, "issues": [], "format_violations": []}

用法（直接调用）：
    from link_checker import validate
    result = validate(task_dir="...")
"""
import re
import sys
from pathlib import Path

# 可选：通过 __plugin_registry__ 访问 devroot（由 py_lib 注入）
__plugin_registry__ = None


def _extract_md_links(content: str):
    """提取 Markdown 相对链接 [text](path)"""
    links = []
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        text, url = match.groups()
        links.append((text, url))
    return links


def _is_relative_link(url: str) -> bool:
    """判断是否为需要验证的相对链接"""
    if not url:
        return False
    if url.startswith('http://') or url.startswith('https://'):
        return False
    if url.startswith('#'):
        return False
    if url.startswith('mailto:'):
        return False
    return True


def _check_frontmatter_dashes(content: str, file_name: str = "") -> list:
    """
    检测 frontmatter 边界污染：除文件开头的 YAML frontmatter 定界符外，
    正文中不允许出现独立的 --- 行。

    返回违规列表，每项包含 line_no 和 context。
    """
    violations = []
    lines = content.splitlines()
    dash_count = 0

    for idx, line in enumerate(lines, start=1):
        if line.strip() == "---":
            dash_count += 1
            if dash_count > 2:
                # 第 3 个及以后的 --- 都是违规
                context = line.strip()
                violations.append({
                    "line": idx,
                    "context": context,
                    "rule": "正文中禁止使用 --- 水平分隔线（与 YAML frontmatter 定界符冲突）"
                })
    return violations


def _resolve_link(source_file: Path, url: str, task_dir: Path) -> Path:
    """将相对链接解析为绝对路径"""
    url = url.split('#')[0]
    if not url:
        return None
    if url.startswith('/'):
        return task_dir / url.lstrip('/')
    else:
        return source_file.parent / url


def validate(task_dir: str = None, devroot: str = None) -> dict:
    """
    验证指定目录下所有 Markdown 文件的内部相对链接

    参数:
        task_dir: 要验证的 task 目录路径。如未传入，尝试从 __plugin_registry__ 获取 devroot 并拼接。
        devroot: 开发根路径（可选，优先于 registry 中的 devroot）

    返回:
        {
            "checked": int,              # 检查链接总数
            "broken": int,               # 断裂链接数
            "issues": [                  # 断裂链接详情
                {
                    "source": str,     # 源文件相对路径
                    "link_text": str,  # 链接文本
                    "url": str,        # 原始 URL
                    "resolved": str    # 解析后的目标路径
                }
            ],
            "format_violations": [       # Markdown 格式违规（新增）
                {
                    "source": str,     # 源文件相对路径
                    "line": int,       # 行号
                    "context": str,    # 违规内容
                    "rule": str        # 违规规则说明
                }
            ]
        }
    """
    # 优先使用注入的 registry 的 devroot
    _devroot = devroot
    if not _devroot and __plugin_registry__:
        _devroot = __plugin_registry__.devroot

    # 确定 task_dir
    if not task_dir:
        if _devroot:
            task_dir = Path(_devroot) / "references" / "tasks" / "deploy-git-isolated"
        else:
            raise ValueError(
                "task_dir 未传入，且无法从 devroot 推导。"
                "请传入 task_dir 或确保 py_lib 加载时设置了 devroot。"
            )

    task_path = Path(task_dir)
    if not task_path.exists():
        raise ValueError(f"task_dir 不存在: {task_dir}")

    issues = []
    format_violations = []
    checked = 0

    md_files = list(task_path.rglob("*.md"))

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        rel_source = md_file.relative_to(task_path)

        # 1. 检测 frontmatter 边界污染（--- 在正文中出现）
        dash_violations = _check_frontmatter_dashes(content, file_name=str(rel_source))
        for v in dash_violations:
            format_violations.append({
                "source": str(rel_source),
                "line": v["line"],
                "context": v["context"],
                "rule": v["rule"]
            })

        # 2. 验证内部相对链接
        links = _extract_md_links(content)

        for text, url in links:
            if not _is_relative_link(url):
                continue

            checked += 1
            target = _resolve_link(md_file, url, task_path)
            if target is None:
                continue

            # 处理 .md 链接指向目录的情况
            if target.suffix == '' and not target.exists():
                readme_candidate = target / "README.md"
                if readme_candidate.exists():
                    target = readme_candidate

            if not target.exists():
                rel_target = target.relative_to(task_path) if task_path in target.parents else str(target)
                issues.append({
                    "source": str(rel_source),
                    "link_text": text,
                    "url": url,
                    "resolved": str(rel_target)
                })

    return {
        "checked": checked,
        "broken": len(issues),
        "issues": issues,
        "format_violations": format_violations
    }


def main():
    """命令行入口（用于独立测试）"""
    import argparse
    parser = argparse.ArgumentParser(description="验证 Markdown 内部相对链接")
    parser.add_argument("--task-dir", help="要验证的 task 目录路径")
    parser.add_argument("--devroot", help="开发根路径（用于推导 task-dir）")
    args = parser.parse_args()

    result = validate(task_dir=args.task_dir, devroot=args.devroot)

    md_files = list(Path(args.task_dir or '.').rglob('*.md'))
    print(f"扫描文件: {len(md_files)} 个")
    print(f"检查链接: {result['checked']} 个")
    print(f"断裂链接: {result['broken']} 个")
    print(f"格式违规: {len(result.get('format_violations', []))} 处")

    has_error = False

    if result.get("format_violations"):
        print("\n【Markdown 格式违规】")
        for v in result["format_violations"]:
            print(f"  {v['source']}:{v['line']} — {v['rule']}")
        has_error = True

    if result["issues"]:
        print("\n【断裂链接详情】")
        for issue in result["issues"]:
            print(f"  {issue['source']}")
            print(f"     链接文本: {issue['link_text']}")
            print(f"     URL: {issue['url']}")
            print(f"     解析路径: {issue['resolved']}")
        has_error = True

    if has_error:
        sys.exit(1)
    else:
        print("\n所有验证通过（链接 + 格式）")
        sys.exit(0)


if __name__ == "__main__":
    main()
