#!/usr/bin/env python3
r"""
update-version.py — 版本记录更新 CLI（v2.0.0）
标签：py-tools
依赖：py_lib 插件体系（runtime_version / timestamp / detect_devroot）

改进点（相较 v1.0.0）：
1. 走 py_lib.load_plugins() 统一入口，遵守 Layer 3 Workflow 禁止直接 import Layer 1 Plugin 的架构铁律
2. 通过 PluginRegistry 访问底座能力，不越级触碰 py-plugins/
3. 行为与输出与 v1.0.0 完全兼容，CLI 参数不变

职责：
  1. 自动发现 venv/version/ 下需要维护版本记录的工具（扫描 *.md，排除 *-history.md）
  2. 读取各工具的当前版本文件，提取记录的版本号
  3. 调用 runtime_version.detect() 实测本地版本
  4. 对比记录版本 vs 实测版本
  5. 若变化 → 更新当前版本文件（frontmatter date + version 表格），追加 history
  6. 输出摘要

用法：
    python update-version.py --devroot "D:\pjt\vscode\vsc_py"
    python update-version.py --devroot "D:\pjt\vscode\vsc_py" --tool node
    python update-version.py --devroot "D:\pjt\vscode\vsc_py" --dry-run
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 走 py_lib 统一入口（Layer 2）
_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins

# 加载插件（core + utility 覆盖 detect_devroot / runtime_version / timestamp）
registry = load_plugins(tags=["core", "utility"])


# =============================================================================
# Markdown 解析与更新
# =============================================================================

def parse_md_version(md_path: Path) -> tuple:
    """
    解析 .md 文件，提取 frontmatter 和表格中的 version。

    返回: (frontmatter_str, frontmatter_dict, recorded_version, version_line_idx)
        frontmatter_str: 原始 frontmatter 文本（含 ---）
        frontmatter_dict: 解析后的 frontmatter 键值对
        recorded_version: 表格中的 version 值（如 "3.13.13"）
        version_line_idx: version 所在行号（0-based，不含 frontmatter）
    """
    content = md_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 解析 frontmatter
    fm_lines = []
    fm_dict = {}
    in_fm = False
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not in_fm:
                in_fm = True
                fm_lines.append(line)
                continue
            else:
                fm_lines.append(line)
                body_start = i + 1
                break
        if in_fm:
            fm_lines.append(line)
            # 简单 key: value 解析
            m = re.match(r"^([\w-]+):\s*(.+)$", line.strip())
            if m:
                fm_dict[m.group(1)] = m.group(2).strip()

    # 在正文中查找 | **version** | xxx | 表格行
    recorded_version = None
    version_line_idx = -1
    for i in range(body_start, len(lines)):
        line = lines[i]
        m = re.search(r"\|\s*\*\*version\*\*\s*\|\s*([^|]+)\s*\|", line, re.IGNORECASE)
        if m:
            recorded_version = m.group(1).strip()
            version_line_idx = i
            break

    return "\n".join(fm_lines), fm_dict, recorded_version, version_line_idx


def update_md_version(md_path: Path, new_version: str, today: str) -> bool:
    """
    更新 .md 文件：
    1. frontmatter 中的 date → today
    2. 表格中的 version → new_version

    返回是否成功写入。
    """
    content = md_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 更新 frontmatter date
    for i, line in enumerate(lines):
        if re.match(r"^date:\s*", line.strip()):
            lines[i] = f"date: {today}"
            break

    # 更新表格 version
    for i, line in enumerate(lines):
        if re.search(r"\|\s*\*\*version\*\*\s*\|", line, re.IGNORECASE):
            lines[i] = f"| **version** | {new_version} |"
            break

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return True


def append_history(history_path: Path, today: str, old_ver: str, new_ver: str) -> bool:
    """
    在 history 文件末尾追加一行变更记录。
    格式：| 日期 | **旧版 → 新版** |
    """
    if not history_path.exists():
        return False

    content = history_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # 在表格的最后一行后追加（找到最后一个以 | 开头的行）
    last_table_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith("|"):
            last_table_idx = i
            break

    if last_table_idx < 0:
        return False

    new_line = f"| {today} | **{old_ver} → {new_ver}** |"
    lines.insert(last_table_idx + 1, new_line)

    history_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return True


# =============================================================================
# 工具发现与配置映射
# =============================================================================

def discover_tools(devroot: Path) -> list:
    """
    扫描 venv/version/ 目录，发现需要维护版本记录的工具。
    排除 *-history.md 文件。

    返回: [(tool_name, md_path, history_path), ...]
    """
    version_dir = devroot / "venv" / "version"
    if not version_dir.exists():
        return []

    tools = []
    for md_file in sorted(version_dir.glob("*.md")):
        if md_file.name.endswith("-history.md"):
            continue
        if md_file.name.lower() == "readme.md":
            continue
        tool_name = md_file.stem
        history_path = version_dir / f"{tool_name}-history.md"
        tools.append((tool_name, md_file, history_path))

    return tools


def load_tools_config(devroot: Path) -> dict:
    """加载 runtime_config/tools_config.json，返回 name -> config 映射"""
    config_path = devroot / "references" / "runtime" / "runtime_config" / "tools_config.json"
    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    mapping = {}
    for tool in data.get("tools", []):
        mapping[tool["name"]] = tool
    return mapping


def build_detect_kwargs(tool_config: dict, devroot: str) -> dict:
    """从 tools_config 的 local 配置构建 detect() 的 kwargs"""
    local = tool_config.get("local", {})
    kwargs = {}

    mode = local.get("mode", "subprocess-version")
    if mode == "subprocess-version":
        kwargs["version_arg"] = local.get("version_arg", "--version")
    elif mode == "package-import":
        kwargs["interpreter"] = registry.runtime_version.resolve_path(
            local.get("interpreter", "${devroot}\\venv\\py\\python.exe"), devroot
        )
        kwargs["package_name"] = local.get("package_name", "")
    elif mode == "python-self":
        kwargs["interpreter"] = registry.runtime_version.resolve_path(
            local.get("interpreter", "${devroot}\\venv\\py\\python.exe"), devroot
        )
    elif mode == "cursor-special":
        pass
    elif mode == "file-version":
        pass

    # 传入 tools_config 中声明的 fallback_paths，供 detect() 第一层 fallback 使用
    fallback_paths = local.get("fallback_paths", [])
    if fallback_paths:
        kwargs["fallback_paths"] = fallback_paths

    return kwargs


# =============================================================================
# 主流程
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="版本记录更新 CLI")
    parser.add_argument("--devroot", default="", help="devroot 绝对路径（默认自动探测）")
    parser.add_argument("--tool", default="", help="仅更新指定工具（如 node）")
    parser.add_argument("--dry-run", action="store_true", help="仅检测对比，不写入文件")
    parser.add_argument("--refresh-date", action="store_true", help="版本未变时也刷新 frontmatter date")
    args = parser.parse_args()

    # 获取 devroot（优先命令行参数，否则用 registry 内探测值）
    if args.devroot:
        devroot = registry.detect_devroot.validate_devroot(args.devroot)
    else:
        devroot = registry.detect_devroot.get_devroot()
    devroot_str = str(devroot)

    # 获取今天日期
    today = registry.timestamp.get_now()["local_short"]  # YYYY-MM-DD

    # 发现工具
    tools = discover_tools(devroot)
    if args.tool:
        tools = [t for t in tools if t[0] == args.tool]

    if not tools:
        print("[ERROR] 未发现需要更新的版本记录文件")
        sys.exit(1)

    # 加载工具配置
    config_map = load_tools_config(devroot)

    print(f"Update Version — devroot: {devroot_str}")
    print(f"检测日期: {today}")
    print("=" * 60)

    updated = []
    unchanged = []
    errors = []

    # .md 文件名 → tools_config.json 工具名映射
    NAME_MAP = {"opencode": "opencode_cli", "gh": "gh_cli"}

    for tool_name, md_path, history_path in tools:
        print(f"\n[{tool_name}] {md_path.name}")

        # 1. 读取记录的版本
        _, _, recorded_ver, _ = parse_md_version(md_path)
        if not recorded_ver:
            print(f"  [WARN] 未能从 {md_path.name} 解析到版本号，跳过")
            errors.append((tool_name, "未能解析记录版本"))
            continue
        print(f"  记录版本: {recorded_ver}")

        # 2. 获取检测配置
        config_name = NAME_MAP.get(tool_name, tool_name)
        tool_cfg = config_map.get(config_name)
        if not tool_cfg:
            print(f"  [WARN] tools_config.json 中未找到 {config_name} 配置，跳过")
            errors.append((tool_name, "tools_config 中无配置"))
            continue

        local_cfg = tool_cfg.get("local", {})
        mode = local_cfg.get("mode", "subprocess-version")
        exe_path = local_cfg.get("exe_path", "")
        kwargs = build_detect_kwargs(tool_cfg, devroot_str)

        # 3. 实测本地版本（通过 registry 调用底座插件）
        # 传入 index_path 和 tool_name，让 detect() 在路径 miss 时 fallback 扫描索引 candidate_paths
        # manifest 由调用方传入路径，底层负责写出完整探测上下文
        index_path = str(devroot / "references" / "runtime" / "verified-runtime-index.json")
        manifest_file = str(devroot / "venv" / "tmp" / f"update-version-detect-{config_name}.json")
        result = registry.runtime_version.detect(
            exe_path, mode=mode, devroot=devroot_str,
            index_path=index_path, tool_name=config_name,
            manifest_path=manifest_file,
            **kwargs
        )
        actual_ver = result.get("version")
        print(f"  实测版本: {actual_ver} (status: {result['status']}, path: {result['path']})")

        if result["status"] != "OK":
            print(f"  [WARN] 版本检测失败: {result['error']}")
            errors.append((tool_name, f"检测失败: {result['error']}"))
            continue

        # 4. 对比
        if actual_ver == recorded_ver:
            print(f"  [OK] 版本一致，无需更新")
            if args.refresh_date and not args.dry_run:
                update_md_version(md_path, actual_ver, today)
                print(f"  [REFRESH] 已刷新 frontmatter date")
            unchanged.append((tool_name, actual_ver))
            continue

        # 5. 版本变化 → 更新
        print(f"  [CHANGE] {recorded_ver} → {actual_ver}")
        if args.dry_run:
            print(f"  [DRY-RUN] 跳过写入")
            updated.append((tool_name, recorded_ver, actual_ver))
            continue

        # 更新当前版本文件
        update_md_version(md_path, actual_ver, today)
        print(f"  [WRITE] 已更新 {md_path.name}")

        # 追加 history
        if history_path.exists():
            append_history(history_path, today, recorded_ver, actual_ver)
            print(f"  [WRITE] 已追加 {history_path.name}")
        else:
            print(f"  [WARN] history 文件不存在: {history_path}")

        updated.append((tool_name, recorded_ver, actual_ver))

    # =============================================================================
    # 摘要
    # =============================================================================
    print("\n" + "=" * 60)
    print("更新摘要")
    print("=" * 60)
    print(f"总计: {len(tools)} | 已更新: {len(updated)} | 未变化: {len(unchanged)} | 错误: {len(errors)}")

    if updated:
        print("\n[已更新]")
        for name, old, new in updated:
            print(f"  {name:20s} {old:15s} → {new}")

    if unchanged:
        print(f"\n[未变化] ({len(unchanged)} 个)")
        for name, ver in unchanged:
            print(f"  {name:20s} {ver}")

    if errors:
        print(f"\n[错误] ({len(errors)} 个)")
        for name, err in errors:
            print(f"  {name:20s} {err}")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
