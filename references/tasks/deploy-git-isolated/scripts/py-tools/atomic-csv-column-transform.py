#!/usr/bin/env python3
r"""
py-tools/atomic-csv-column-transform.py — CSV 列无损转换原子工具（v1.1.0）
标签：py-tools
版本：v1.1.0
日期：2026-07-23

【意图】
通用 CSV 列内容转换框架：读取源 CSV，按配置规则对指定列进行无损转换，
写入新 CSV（绝不触碰源文件），生成 manifest 供审计追踪。
源于 env-migration 中 feiliks-invoice-csv 工具的泛化需求：原工具只改
"Invoice date" 一列，本框架通过配置驱动支持任意列、任意转换规则，
 py 执行框架不变，改配置即可适配新场景。

【职责】
  1. 读取源 CSV（支持文件或目录扫描自动选取）
  2. 按 --config JSON 定义的规则对指定列执行转换
  3. 写入 outfile（编码/换行符/BOM 与源文件保持一致）
  4. 生成 manifest 落盘到 --output 指定路径（默认 venv/tmp/）

【依赖】
底层能力（py-plugins/）：无（纯 Python 标准库）
外部工具：无
环境变量：无

【预检】
  - 文件存在性: --input 指向的文件或目录存在
  - 配置合法性: --config JSON 存在且符合 transforms schema
  - 列存在性: 源 CSV header 包含配置中声明的全部列名

【调用参数】
  --input       <str, 必填>                源 CSV 文件路径或目录（目录时扫描 *.csv 取最新）
  --outfile     <str, 必填>                业务产物：转换后的 CSV 输出路径
  --output      <str, 可选>                审计产物：manifest JSON 路径（workflow 调用时必须显式传入；
                                           未传时回退到 devroot/venv/tmp/atomic-csv-column-transform-manifest-{timestamp}.json）
  --config      <str, 可选>                转换规则配置 JSON 文件路径（未传时使用内置默认：Invoice date → today_ymd）
  --dry-run     <flag, 可选>               预览模式：输出前 3 行转换前后对比，不写入任何文件

【用法示例】
    # 默认配置（Invoice date → 今天 YYYYMMDD）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-csv-column-transform.py" `
        --input "D:\demo\FEILIKS_FAPINV.20260722-2607.csv" `
        --outfile "D:\demo\FEILIKS_FAPINV.20260723.csv" `
        --output "${devroot}\venv\tmp\polyrepo-wf-step3-transform.json"

    # 自定义配置（多列转换）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-csv-column-transform.py" `
        --input "D:\demo\data.csv" `
        --outfile "D:\demo\data_processed.csv" `
        --config "${devroot}\venv\tmp\transform-config.json"

    # 预览模式（不写入文件，仅看效果）
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-csv-column-transform.py" `
        --input "D:\demo\20260702tecsv" `
        --outfile "D:\demo\20260702tecsv\FEILIKS_FAPINV.20260723.csv" `
        --config "D:\demo\20260702tecsv\csv-transform-feiliks-invoice.json" `
        --dry-run

【返回】
    exit 0 = 转换成功
    exit 1 = 失败（文件不存在、配置非法、列缺失、IO 错误等）

【审计产物】
    ${devroot}/venv/tmp/atomic-csv-column-transform-manifest-{timestamp}.json:
      {
        "atomic_tool": "atomic-csv-column-transform",
        "version": "1.1.0",
        "source_csv": "...",
        "outfile": "...",
        "output": "...",
        "transforms_applied": {...},
        "read_encoding": "utf-8|utf-8-sig",
        "write_encoding": "utf-8|utf-8-sig",
        "utf8_bom_at_source_start": true|false,
        "output_newline": "\\r\\n|\\n",
        "csv_data_rows_total": N,
        "rows_written": N,
        "columns": M,
        "exit_code": 0,
        "exit_at": "..."
      }

【关联】
    - workflow: 被任何需要 CSV 列转换的 workflow phase 调用
    - 上游触发: debug/feiliks-invoice-csv/tool/csv_update_invoice_date.py 的泛化
    - 配置 schema: 见 docstring 中「配置驱动 schema」章节
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# =============================================================================
# 内置默认配置（兼容原 feiliks-invoice-csv 行为）
# =============================================================================
_DEFAULT_CONFIG = {
    "transforms": {
        "Invoice date": {"type": "today_ymd"}
    }
}

# =============================================================================
# 编码感知（复用原脚本逻辑）
# =============================================================================
def _detect_utf8_bom(path: Path) -> bool:
    with path.open("rb") as f:
        return f.read(3) == b"\xef\xbb\xbf"


def _sniff_newline(path: Path, sample: int = 65536) -> str:
    with path.open("rb") as f:
        chunk = f.read(sample)
    crlf = chunk.count(b"\r\n")
    lf = chunk.count(b"\n") - crlf
    return "\r\n" if crlf >= lf else "\n"


def _encoding_for_read(path: Path) -> str:
    if _detect_utf8_bom(path):
        return "utf-8-sig"
    return "utf-8"


def _encoding_for_write(read_encoding: str) -> str:
    if read_encoding == "utf-8-sig":
        return "utf-8-sig"
    return "utf-8"


# =============================================================================
# Transform 引擎
# =============================================================================
def _today_ymd() -> str:
    d = datetime.now(timezone.utc).date()
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


_TRANSFORM_REGISTRY = {
    "today_ymd": lambda cell, cfg: _today_ymd(),
    "today_iso": lambda cell, cfg: _today_iso(),
    "fixed": lambda cell, cfg: cfg.get("value", ""),
    "regex_replace": lambda cell, cfg: re.sub(cfg["pattern"], cfg["replacement"], str(cell)),
    "empty": lambda cell, cfg: "",
}


def _apply_transform(cell: str, cfg: dict) -> str:
    ttype = cfg.get("type")
    if ttype not in _TRANSFORM_REGISTRY:
        raise ValueError(f"未知 transform 类型: {ttype!r}")
    return _TRANSFORM_REGISTRY[ttype](cell, cfg)


def _load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return _DEFAULT_CONFIG
    text = config_path.read_text(encoding="utf-8")
    cfg = json.loads(text)
    if "transforms" not in cfg:
        raise ValueError("配置 JSON 必须包含顶层 'transforms' 字段")
    return cfg


# =============================================================================
# 源文件解析（文件或目录）
# =============================================================================
def _resolve_source(input_path: Path) -> tuple[Path, dict]:
    if input_path.is_file():
        return input_path, {
            "mode": "explicit_file",
            "input_path": str(input_path),
            "selected": str(input_path),
            "selection_reason": "User provided a file path directly.",
        }

    if not input_path.is_dir():
        raise SystemExit(f"Input path does not exist or is not a file/directory: {input_path}")

    all_csv = list(input_path.glob("*.csv"))
    if not all_csv:
        raise SystemExit(f"No CSV files found in: {input_path}")

    selected = max(all_csv, key=lambda p: p.stat().st_mtime)
    return selected, {
        "mode": "scan_directory",
        "input_path": str(input_path),
        "scanned_total": len(all_csv),
        "selected": str(selected),
        "selected_mtime": datetime.fromtimestamp(selected.stat().st_mtime, tz=timezone.utc).isoformat(),
        "selection_reason": "Newest modification time among CSV files.",
    }


# =============================================================================
# Manifest
# =============================================================================
def _save_manifest(devroot: Path, data: dict, output_path: str | None) -> Path:
    manifest_dir = devroot / "venv" / "tmp"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    if output_path:
        manifest_path = Path(output_path)
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        manifest_path = manifest_dir / f"atomic-csv-column-transform-manifest-{ts}.json"
    manifest_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


# =============================================================================
# 主逻辑
# =============================================================================
def main() -> int:
    parser = argparse.ArgumentParser(description="CSV 列无损转换原子工具")
    parser.add_argument("--input", required=True, help="源 CSV 文件路径或目录")
    parser.add_argument("--outfile", required=True, help="业务产物：转换后的 CSV 输出路径")
    parser.add_argument(
        "--output",
        default=None,
        help="审计产物：manifest JSON 路径（workflow 调用时必须显式传入；未传时回退到 devroot/venv/tmp/atomic-csv-column-transform-manifest-{timestamp}.json）",
    )
    parser.add_argument("--config", default=None, help="转换规则配置 JSON 文件路径（未传时使用内置默认）")
    parser.add_argument("--dry-run", action="store_true", help="预览模式：输出前 3 行转换前后对比，不写入任何文件")
    args = parser.parse_args()

    devroot = Path.cwd()
    input_path = Path(args.input).expanduser().resolve()
    outfile = Path(args.outfile).expanduser().resolve()

    # 解析源文件
    src_csv, source_discovery = _resolve_source(input_path)

    # 目录扫描时输出醒目提示
    if source_discovery["mode"] == "scan_directory":
        scanned = source_discovery["scanned_total"]
        selected_name = Path(source_discovery["selected"]).name
        print(f"[目录扫描] 发现 {scanned} 个 CSV，选中: {selected_name} (最新修改时间)")

    # 加载配置
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    cfg = _load_config(config_path)
    transforms = cfg["transforms"]

    # 编码感知
    read_enc = _encoding_for_read(src_csv)
    write_enc = _encoding_for_write(read_enc)
    has_bom = _detect_utf8_bom(src_csv)
    newline = _sniff_newline(src_csv)

    # 执行转换
    header: list[str] | None = None
    rows_total = 0
    rows_written = 0
    preview_rows: list[tuple[list[str], list[str]]] = []  # (原始行, 转换后行)

    # 列名 → 索引映射
    col_index: dict[str, int] = {}

    with src_csv.open("r", encoding=read_enc, newline="") as fin:
        reader = csv.reader(fin)
        try:
            header = next(reader)
        except StopIteration:
            raise SystemExit("Source CSV is empty.")

        # 校验所有目标列存在
        missing = [c for c in transforms if c not in header]
        if missing:
            raise SystemExit(f"CSV header 缺少配置中声明的列: {missing!r}")

        for c in transforms:
            col_index[c] = header.index(c)

        # dry-run：只读，不写文件
        if args.dry_run:
            for row in reader:
                rows_total += 1
                original = row.copy()
                for col_name, t_cfg in transforms.items():
                    idx = col_index[col_name]
                    cell = row[idx] if idx < len(row) else ""
                    new_val = _apply_transform(cell, t_cfg)
                    if idx >= len(row):
                        row.extend([""] * (idx + 1 - len(row)))
                    row[idx] = new_val
                rows_written += 1
                if len(preview_rows) < 3:
                    preview_rows.append((original, row))
                if rows_total >= 3:
                    break

            print(f"\n[Dry-Run 预览] 前 {len(preview_rows)} 行转换对比：")
            for i, (orig, conv) in enumerate(preview_rows, 1):
                print(f"  行 {i}:")
                for col_name in transforms:
                    idx = col_index[col_name]
                    o = orig[idx] if idx < len(orig) else ""
                    c = conv[idx] if idx < len(conv) else ""
                    print(f"    {col_name}: '{o}' → '{c}'")
            print(f"\n[Dry-Run] 共扫描 {rows_total} 行，未写入任何文件。")
            return 0

        # 正常模式：写入 outfile
        outfile.parent.mkdir(parents=True, exist_ok=True)
        with outfile.open("w", encoding=write_enc, newline="") as fout:
            writer = csv.writer(fout, lineterminator=newline)
            writer.writerow(header)

            for row in reader:
                rows_total += 1
                for col_name, t_cfg in transforms.items():
                    idx = col_index[col_name]
                    if idx < len(row):
                        cell = row[idx]
                    else:
                        cell = ""
                    new_val = _apply_transform(cell, t_cfg)
                    # 确保行长度足够
                    if idx >= len(row):
                        row.extend([""] * (idx + 1 - len(row)))
                    row[idx] = new_val
                writer.writerow(row)
                rows_written += 1

    # 构建 manifest
    manifest = {
        "atomic_tool": "atomic-csv-column-transform",
        "version": "1.1.0",
        "source_csv": str(src_csv),
        "outfile": str(outfile),
        "output": None,
        "source_discovery": source_discovery,
        "transforms_applied": transforms,
        "read_encoding": read_enc,
        "write_encoding": write_enc,
        "utf8_bom_at_source_start": has_bom,
        "output_newline": "\\r\\n" if newline == "\r\n" else "\\n",
        "csv_data_rows_total": rows_total,
        "rows_written": rows_written,
        "columns": len(header),
        "exit_code": 0,
        "exit_at": datetime.now(timezone.utc).isoformat(),
    }

    # 先回填 output 路径，再落盘 manifest
    manifest_path = _save_manifest(devroot, manifest, args.output)
    manifest["output"] = str(manifest_path)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Source: {src_csv}")
    print(f"Outfile: {outfile}")
    print(f"Manifest: {manifest_path}")
    print(f"Rows written: {rows_written}")
    print(f"Transforms: {list(transforms.keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
