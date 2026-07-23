#!/usr/bin/env python3
r"""
py-tools/atomic-config-edit-json.py — JSON 配置原子编辑工具（v1.0.1）
标签：py-tools
版本：v1.0.1
日期：2026-07-22

【意图】
Agent 用 `edit` 工具修改 JSON 文件时高频失败：缩进微差导致 oldString 不匹配、
数组追加遗漏逗号、嵌套路径深导致字符串拼接出错、json.dump 默认产生 CRLF。
本工具通过 Python json 模块做结构化修改（不走字符串替换），根治以上问题。
支持 RFC 6902 JSON Pointer 定位 + JSON Patch 批量操作，是全部 JSON 配置/索引
文件修订的唯一推荐入口。

【职责】
  1. 读取 JSON 文件，按 JSON Pointer（RFC 6902）定位字段
  2. 支持单条操作（--operation + --json-pointer + --value）或批量操作（--batch）
  3. 支持 add / replace / remove（标准 RFC 6902）+ merge（对象深度合并，扩展）
  4. 安全写回：强制 LF（newline="\n"）+ UTF-8 无 BOM + 可选备份
  5. 生成 manifest 供审计追踪

【依赖】
底层能力（py-plugins/）：
  无（纯 Python 标准库，零外部依赖）
外部工具：
  无
环境变量：
  无

【预检】
执行本脚本前必须满足的前置条件：
  - 文件存在性: --file 指向的 JSON 文件存在且语法合法
  - 路径合法性: --json-pointer 为合法 JSON Pointer（以 / 开头）
  - 操作合法性: --operation 为 add/replace/remove/merge 之一

【调用参数】
  --file          <str, 必填>                目标 JSON 文件路径
  --operation     <str, 可选>                单条操作类型: add | replace | remove | merge
  --json-pointer  <str, 可选>                JSON Pointer 路径（RFC 6902，如 /a/b/0）
  --value         <str, 可选>                JSON 值（JSON 字符串，如 '{"x":1}' 或 '"hello"'）
  --batch         <str, 可选>                JSON Patch 批量操作（RFC 6902 数组格式）
  --indent        <int, 可选, 默认=4>         JSON 输出缩进空格数
  --backup        <flag, 可选>               修改前备份原文件为 .json.bak
  --dry-run       <flag, 可选>               仅预览修改结果，不写入磁盘
  --output        <str, 可选>                产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-config-edit-json-manifest-{timestamp}.json）

【JSON Pointer 速查】
  /foo/bar      → 根对象下的 foo 字段下的 bar 字段
  /foo/0        → 根对象下 foo 数组的第 0 个元素
  /foo~0bar     → 键名为 "foo~bar"（~ 转义为 ~0）
  /foo~1bar     → 键名为 "foo/bar"（/ 转义为 ~1）

【用法示例】
    # 标准三步流程（中文内容 / 批量更新 / 任何复杂 value）：
    #   Step 1: write 工具写入 patch 内容到 venv/tmp/patch.json（不经 Shell）
    #   Step 2: atomic-config-edit-json.py --batch @venv/tmp/patch.json --backup
    #   Step 3: run-lint.py 验证修改后的 JSON
    #
    # 单条简单操作（value 为短字符串且无中文时可用）：
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
        --file "${devroot}\references\runtime\verified-task-index.json" `
        --operation replace `
        --json-pointer "/meta/last_updated" `
        --value '"2026-07-22T14:00:00"'

    # 批量操作（推荐，中文内容必须走此流程）
    # Step 1: write 工具写入 patch 文件
    # Step 2:
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
        --file "${devroot}\references\runtime\verified-task-index.json" `
        --batch "@venv/tmp/patch.json" `
        --backup

    # batch 文件示例（venv/tmp/patch.json）：
    # [
    #   {"op": "replace", "path": "/meta/last_updated", "value": "2026-07-22T14:00:00"},
    #   {"op": "add", "path": "/available_scripts_and_tools/my-tool", "value": {"name": "..."}}
    # ]

    # 数组追加：向 trigger_words 追加一个词
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
        --file "${devroot}\references\runtime\verified-task-index.json" `
        --operation add `
        --json-pointer "/high_frequency_tasks/verify_runtime/trigger_words/-" `
        --value '"真源检测"'

    # 对象深度合并（merge）：只更新部分字段，不覆盖整个对象
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
        --file "${devroot}\references\runtime\verified-task-index.json" `
        --operation merge `
        --json-pointer "/available_scripts_and_tools/run-lint" `
        --value '{"verified_at": "2026-07-22T14:00:00"}'

    # 仅预览（dry-run）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
        --file "${devroot}\references\runtime\verified-task-index.json" `
        --operation replace `
        --json-pointer "/meta/last_updated" `
        --value '"2026-07-22T14:00:00"' `
        --dry-run

【返回】
    exit 0 = 修改成功（或 --dry-run 预览成功）
    exit 1 = 失败（文件不存在、JSON 语法错误、路径不存在、操作非法等）

【审计产物】
    ${devroot}/venv/tmp/config-edit-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-config-edit-json",
        "version": "1.0.1",
        "file": "...",
        "operations": [...],
        "dry_run": false,
        "backup_path": "...",
        "exit_code": 0,
        "exit_at": "...",
        "errors": []
      }

【关联】
    - workflow: 被任何需要修改 JSON 索引/配置的脚本或 workflow 调用
    - 上游消费: 人类终端、Agent tool、其他 atomic 脚本
    - 下游替代: 逐步替代手敲 `edit` 修改 JSON 的所有场景
"""
import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


# =============================================================================
# JSON Pointer 解析（RFC 6902）
# =============================================================================
def _unescape_token(token: str) -> str:
    """将 JSON Pointer 的转义还原：~1 → /, ~0 → ~"""
    return token.replace("~1", "/").replace("~0", "~")


def _parse_pointer(pointer: str) -> list:
    """解析 JSON Pointer 为路径段列表。"""
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ValueError(
            f"JSON Pointer 必须以 / 开头（如 /meta/last_updated）。"
            f"不支持 JSON Path（$.foo）或 jq（.foo.bar）风格: {pointer}"
        )
    tokens = pointer[1:].split("/")
    return [_unescape_token(t) for t in tokens]


def _get_value(data, tokens: list):
    """按 tokens 路径获取值，返回 (parent, key, value) 或 None。"""
    current = data
    for i, token in enumerate(tokens[:-1]):
        if isinstance(current, dict):
            if token not in current:
                return None
            current = current[token]
        elif isinstance(current, list):
            try:
                idx = int(token)
                current = current[idx]
            except (ValueError, IndexError):
                return None
        else:
            return None

    last = tokens[-1] if tokens else None
    if last is None:
        return (None, None, current)

    if isinstance(current, dict):
        if last in current:
            return (current, last, current[last])
        return (current, last, None)
    elif isinstance(current, list):
        if last == "-":
            return (current, "-", None)
        try:
            idx = int(last)
            if 0 <= idx < len(current):
                return (current, idx, current[idx])
            if idx == len(current):
                return (current, idx, None)
            return None
        except ValueError:
            return None
    return None


# =============================================================================
# 操作实现
# =============================================================================
def _op_add(data, tokens: list, value):
    """add / replace 的统一实现。"""
    if not tokens:
        return value

    current = data
    for token in tokens[:-1]:
        if isinstance(current, dict):
            if token not in current:
                current[token] = {}
            current = current[token]
        elif isinstance(current, list):
            idx = int(token)
            current = current[idx]
        else:
            raise ValueError(f"无法在非容器类型上导航: {type(current)}")

    last = tokens[-1]
    if isinstance(current, dict):
        current[last] = value
    elif isinstance(current, list):
        if last == "-":
            current.append(value)
        else:
            idx = int(last)
            if idx == len(current):
                current.append(value)
            else:
                current[idx] = value
    else:
        raise ValueError(f"add 目标不是容器: {type(current)}")
    return data


def _op_remove(data, tokens: list):
    """remove 实现。"""
    if not tokens:
        raise ValueError("remove 操作不能用于根对象")

    current = data
    for token in tokens[:-1]:
        if isinstance(current, dict):
            current = current[token]
        elif isinstance(current, list):
            current = current[int(token)]
        else:
            raise ValueError(f"无法在非容器类型上导航: {type(current)}")

    last = tokens[-1]
    if isinstance(current, dict):
        if last not in current:
            raise ValueError(f"路径不存在，无法 remove: /{'/'.join(tokens)}")
        del current[last]
    elif isinstance(current, list):
        if last == "-":
            raise ValueError("remove 不支持 '-' 指针")
        idx = int(last)
        if not (0 <= idx < len(current)):
            raise ValueError(f"数组索引越界: {idx}")
        del current[idx]
    else:
        raise ValueError(f"remove 目标不是容器: {type(current)}")
    return data


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典，override 的值优先。"""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _op_merge(data, tokens: list, value):
    """merge 实现：深度合并对象。"""
    if not isinstance(value, dict):
        raise ValueError("merge 操作的 value 必须是 JSON Object")

    result = _get_value(data, tokens)
    if result is None:
        # 路径不存在，直接创建
        return _op_add(data, tokens, value)

    parent, key, existing = result
    if existing is None:
        return _op_add(data, tokens, value)
    if not isinstance(existing, dict):
        raise ValueError(f"merge 目标不是 Object: {type(existing)}")

    merged = _deep_merge(existing, value)
    if parent is None:
        return merged
    if isinstance(parent, dict):
        parent[key] = merged
    elif isinstance(parent, list):
        parent[key] = merged
    return data


def _apply_op(data: dict, op: dict) -> dict:
    """应用单条 JSON Patch 操作。"""
    operation = op.get("op")
    path = op.get("path", "")
    value = op.get("value")
    tokens = _parse_pointer(path)

    if operation == "add":
        return _op_add(copy.deepcopy(data), tokens, value)
    elif operation == "replace":
        return _op_add(copy.deepcopy(data), tokens, value)
    elif operation == "remove":
        return _op_remove(copy.deepcopy(data), tokens)
    elif operation == "merge":
        return _op_merge(copy.deepcopy(data), tokens, value)
    else:
        raise ValueError(f"不支持的操作类型: {operation}")


# =============================================================================
# Manifest
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str = None) -> Path:
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"config-edit-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 主逻辑
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="JSON 配置原子编辑工具（RFC 6902 JSON Pointer + JSON Patch）")
    parser.add_argument("--file", required=True, help="目标 JSON 文件路径")
    parser.add_argument("--operation", choices=["add", "replace", "remove", "merge"], help="单条操作类型")
    parser.add_argument("--json-pointer", "--path", dest="path", default=None, help="JSON Pointer 路径（RFC 6902，如 /a/b/0）。不支持 JSON Path（$.foo）或 jq（.foo.bar）风格")
    parser.add_argument("--value", default=None, help="JSON 值（JSON 字符串）")
    parser.add_argument("--batch", default=None, help='JSON Patch 批量操作。支持两种形式：① JSON 字符串（如 \'[{"op":"add",...}]\'）；② @文件路径（如 @venv/tmp/patch.json，从文件读取）')
    parser.add_argument("--indent", type=int, default=4, help="JSON 输出缩进空格数（默认 4）")
    parser.add_argument("--backup", action="store_true", help="修改前备份原文件为 .json.bak")
    parser.add_argument("--dry-run", action="store_true", help="仅预览修改结果，不写入磁盘")
    parser.add_argument("--output", default=None, help="产物输出路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/config-edit-manifest-{timestamp}.json）")
    args = parser.parse_args()

    file_path = Path(args.file)
    devroot = Path.cwd()

    # 从文件路径推导 devroot（向上查找 venv/ 目录）
    for parent in file_path.parents:
        if (parent / "venv").exists():
            devroot = parent
            break

    # 预检：文件存在
    if not file_path.exists():
        print(f"[ERROR] 文件不存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    # 读取 JSON
    try:
        original_text = file_path.read_text(encoding="utf-8")
        data = json.loads(original_text)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 构建操作列表
    operations = []
    if args.batch:
        batch_raw = args.batch.strip()
        # 支持 @file 语法：从文件读取 batch
        if batch_raw.startswith("@"):
            batch_path = Path(batch_raw[1:])
            if not batch_path.exists():
                print(f"[ERROR] batch 文件不存在: {batch_path}", file=sys.stderr)
                sys.exit(1)
            try:
                batch_raw = batch_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[ERROR] 读取 batch 文件失败: {e}", file=sys.stderr)
                sys.exit(1)
        try:
            batch_ops = json.loads(batch_raw)
            if not isinstance(batch_ops, list):
                raise ValueError("--batch 必须是 JSON 数组")
            operations = batch_ops
        except json.JSONDecodeError as e:
            print(f"[ERROR] --batch JSON 解析失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.operation:
        if not args.path:
            print("[ERROR] 单条操作必须提供 --json-pointer（或兼容别名 --path）", file=sys.stderr)
            sys.exit(1)
        op = {"op": args.operation, "path": args.path}
        if args.operation in ("add", "replace", "merge"):
            if args.value is None:
                print(f"[ERROR] {args.operation} 操作必须提供 --value", file=sys.stderr)
                sys.exit(1)
            try:
                op["value"] = json.loads(args.value)
            except json.JSONDecodeError as e:
                print(f"[ERROR] --value JSON 解析失败: {e}", file=sys.stderr)
                sys.exit(1)
        operations.append(op)
    else:
        print("[ERROR] 必须提供 --operation + --json-pointer（或兼容别名 --path）+ --value 或 --batch", file=sys.stderr)
        sys.exit(1)

    # 执行操作
    modified = copy.deepcopy(data)
    manifest = {
        "atomic_tool": "atomic-config-edit-json",
        "version": "1.0.1",
        "file": str(file_path),
        "operations": operations,
        "dry_run": args.dry_run,
        "backup_path": None,
        "exit_code": None,
        "exit_at": None,
        "errors": [],
    }

    try:
        for op in operations:
            modified = _apply_op(modified, op)
    except ValueError as e:
        print(f"[ERROR] 操作失败: {e}", file=sys.stderr)
        manifest["errors"].append(str(e))
        manifest["exit_code"] = 1
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(1)

    # 序列化（强制 LF + UTF-8 无 BOM）
    output_text = json.dumps(modified, ensure_ascii=False, indent=args.indent)
    if not output_text.endswith("\n"):
        output_text += "\n"

    # --dry-run：预览
    if args.dry_run:
        print("\n" + "=" * 50)
        print("[DRY-RUN] 修改预览")
        print("=" * 50)
        print(output_text)
        manifest["exit_code"] = 0
        manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
        mp = _save_manifest(devroot, manifest, args.output)
        print(f"[Manifest] 已落盘: {mp}")
        sys.exit(0)

    # 备份
    if args.backup:
        bak_path = file_path.with_suffix(file_path.suffix + ".bak")
        bak_path.write_text(original_text, encoding="utf-8", newline="\n")
        manifest["backup_path"] = str(bak_path)
        print(f"[Backup] 已备份: {bak_path}")

    # 写回（强制 LF）
    file_path.write_text(output_text, encoding="utf-8", newline="\n")
    print(f"[OK] 已写回: {file_path}")

    manifest["exit_code"] = 0
    manifest["exit_at"] = datetime.now(timezone.utc).isoformat()
    mp = _save_manifest(devroot, manifest)
    print(f"[Manifest] 已落盘: {mp}")
    sys.exit(0)


if __name__ == "__main__":
    main()
