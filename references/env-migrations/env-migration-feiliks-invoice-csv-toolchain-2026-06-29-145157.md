---
title: FEILIKS FAPINV 发票 CSV 工具链建设
description: 补录 feiliks-invoice-csv 工具链的历史建设过程、工具组成、标准调用方式与数据特征，供后续 session 快速复用。
date: 2026-06-29
meta:
  version: 1.0.0
---

# env-migration-feiliks-invoice-csv-toolchain-2026-06-29-145157

| 字段 | 值 |
|------|-----|
| **Session 主题** | FEILIKS FAPINV 发票 CSV 工具链建设补录 |
| **日期** | 2026-06-29 |
| **文件名时间戳** | `2026-06-29-145157` |
| **触发原因** | 发现工具链已成熟使用（12 次运行记录 + playbook），但 references/env-migrations/ 中无任何记录，存在知识断层 |
| **影响范围** | `debug/feiliks-invoice-csv/tool/`、`docs/playbooks/csv-invoice-date-update-playbook.md` |
| **风险等级** | 低（纯文档补录，无环境变更） |


## 一、工具链概览

### 1.1 位置

```
debug/feiliks-invoice-csv/
├── tool/
│   ├── manifest.json                          # 工具索引
│   ├── xlsx_to_csv.py                         # xlsx → csv 转换
│   ├── feiliks_filter_invoice_csv.py          # 白名单过滤 + 全量校验
│   └── csv_update_invoice_date.py             # 仅更新 Invoice date（轻量版）
├── 20260427-113150/                           # 历史运行记录（过滤+校验）
├── 20260601-102041/ ~ 20260601-103924/        # 历史运行记录（日期更新）
├── 20260602-095507/                           # 历史运行记录（日期更新）
├── amount-check-smoke/                        # 金额校验冒烟测试
├── dq-smoke/                                  # 数据质量冒烟测试
├── standalone-verify-1/                       # 独立校验测试
└── verify-test-20260427/                      # 全链路校验测试
```

### 1.2 数据特征（已验证）

| 特征 | 值 |
|------|-----|
| 典型文件名 | `FEILIKS_FAPINV.YYYYMMDD-NNNN.csv` |
| 列数 | **142 列** |
| 行数 | 4,000 ~ 6,000+ |
| 关键列 | `Invoice no`、`Invoice date`、最后一列为累计金额（如 `TOTAL BILL AMOUNT`） |
| 编码 | utf-8 无 BOM，`\r\n` 换行 |
| xlsx 源 | 包含格式化金额、前导零，需按字符串读取 |


## 二、三个工具的职责与调用

### 2.1 xlsx_to_csv.py — xlsx → csv 转换器

**职责**：将 FEILIKS FAPINV 的 xlsx 源文件转换为 csv，同时输出一个 .xlsx 副本文本版本。

**关键行为**：
- 全部单元格按 **字符串** 读取（`dtype=str`），保留前导零和金额格式
- `Invoice date` 列强制设为 **当天 UTC 日期**（`YYYYMMDD` 格式）
- 输出编码：**utf-8（无 BOM）**，行尾符保持与源文件一致（`\r\n`）
- **金额校验**：读取最后一列的累计金额，与源 xlsx 对比，diff ≤ 0.02 且 NaN = 0 才算 PASS

**调用**：
```powershell
${devroot}/venv/py/python.exe ${devroot}/debug/feiliks-invoice-csv/tool/xlsx_to_csv.py <input.xlsx> <output.csv> [output.xlsx]
```

**示例**：
```powershell
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\debug\feiliks-invoice-csv\tool\xlsx_to_csv.py" "D:\demo\FEILIKS_FAPINV.20260629-2606-new.xlsx" "D:\demo\FEILIKS_FAPINV.20260629-2606-new.csv"
```


### 2.2 feiliks_filter_invoice_csv.py — 白名单过滤 + 全量校验

**职责**：最复杂的工具，做三件事：
1. **白名单过滤**：从 xlsx 读取 `Invoice no` 列作为白名单，过滤 CSV 只保留白名单中的行
2. **日期替换**：将保留行的 `Invoice date` 改为指定 YYYYMMDD
3. **校验闭环**：
   - 字段级校验：逐行逐列对比源 CSV 和过滤后 CSV，除 `Invoice date` 外所有字段必须一致
   - 金额累计校验：过滤后 CSV 的最后一列 vs xlsx 同列，diff ≤ 0.02 通过
   - 数据质量报告：检测重复 Invoice no、行数不匹配等

**输出产物**：
```
out/reports/feiliks-invoice-csv/<run_id>/filtered.csv
debug/feiliks-invoice-csv/<run_id>/manifest.json
debug/feiliks-invoice-csv/<run_id>/verify_report.json
debug/feiliks-invoice-csv/<run_id>/verify_mismatches.csv
debug/feiliks-invoice-csv/<run_id>/skipped_not_in_whitelist.csv
debug/feiliks-invoice-csv/<run_id>/encoding-source.txt
```

**调用**：
```powershell
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\debug\feiliks-invoice-csv\tool\feiliks_filter_invoice_csv.py" --csv "D:\demo\source.csv" --xlsx "D:\demo\whitelist.xlsx"
```


### 2.3 csv_update_invoice_date.py — 仅更新日期（轻量版）

**职责**：从复杂逻辑中拆出来的单一职责脚本，只做一件事：
- 读取 CSV → 把 `Invoice date` 列全部改为今天日期 → 写新 CSV

**特点**：
- 支持**目录扫描**：如果传入目录而非文件，自动扫描 `*.YYYYMMDD-NNNN.csv` 模式，选修改时间最新的
- 支持**文件名自动推导**：`FEILIKS_FAPINV.20260527-2605.csv` → `FEILIKS_FAPINV.20260601.csv`
- 输出 manifest 和 encoding 记录到 `debug/feiliks-invoice-csv/<run_id>/`

**调用**：
```powershell
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\debug\feiliks-invoice-csv\tool\csv_update_invoice_date.py" "D:\demo\FEILIKS_FAPINV.20260527-2605.csv"
```


## 三、标准流水线

FEILIKS FAPINV 的完整处理流水线：

```
Step 1: xlsx 源文件 → xlsx_to_csv.py → csv（日期已更新，金额已校验）
Step 2: csv + xlsx 白名单 → feiliks_filter_invoice_csv.py → 过滤后 csv（含字段级校验）
Step 3: 仅需改日期 → csv_update_invoice_date.py → 新 csv
```

> 实际使用中，Step 1 和 Step 2 经常合并：用户拿到新的 xlsx 源文件，先转 csv，再用白名单过滤。


## 四、历史运行记录

| 日期 | 子目录 | 工具 | 源文件 | 行数 |
|------|--------|------|--------|------|
| 2026-04-27 | 20260427-113150 | filter | FEILIKS_FAPINV.20260423-2604.csv | — |
| 2026-06-01 | 20260601-102041 ~ 103924 | update_date | FEILIKS_FAPINV.20260527-2605.csv | 5,719 |
| 2026-06-02 | 20260602-095507 | update_date | FEILIKS_FAPINV.20260527-2605.csv | 5,719 |
| 2026-06-29 | （本次） | xlsx_to_csv | FEILIKS_FAPINV.20260629-2606-new.xlsx | 4,373 |


## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认工具存在 | `Test-Path "debug/feiliks-invoice-csv/tool/xlsx_to_csv.py"` | `True` |
| 2 | 确认 xlsx 可转 csv | 执行 `xlsx_to_csv.py` | `Verify: PASS` |
| 3 | 确认 csv 可过滤 | 执行 `feiliks_filter_invoice_csv.py` | `verify_ok: True` |
| 4 | 确认日期可更新 | 执行 `csv_update_invoice_date.py` | 输出新 csv + manifest |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-29-145157 |
| **更新人** | Human + Agent Session |
| **变更触发** | 发现 env-migrations 中缺少 feiliks-invoice-csv 工具链记录，补录 |
| **下次修订条件** | 新增工具脚本、数据特征变更、发现新踩坑点 |
| **跨环境迁移参考** | 直接复制 `debug/feiliks-invoice-csv/tool/` 目录 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-29*
*模板版本：v2*
