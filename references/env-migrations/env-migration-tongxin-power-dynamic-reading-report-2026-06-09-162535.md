---
title: env-migration — tongxin-power 动态读数报表与模块化脚本建设
description: 记录本次 session 在 debug/tongxin-power/ 目录下的全部建设成果：报表 v1→v6 演进、脚本模块化拆分（≤200行/模块）、渐进式读数逻辑、实测与标注差异检测、项目文档体系（DESIGN/CHANGELOG/README）及 samples/ 副本建设。
date: 2026-06-09
---

# env-migration-tongxin-power-dynamic-reading-report-2026-06-09-162535

> **Session 主题**: tongxin-power 用电数据表动态读数报表生成与脚本模块化重构  
> **日期**: 2026-06-09  
> **文件名时间戳**: `2026-06-09-162535`  
> **触发原因**: 用户需要基于同芯聚联园区用电数据表生成汇总报表，支持渐进式读数（部分子表更新、部分未更新），并要求脚本可维护（每模块≤200行）  
> **影响范围**: `debug/tongxin-power/` 全部内容（脚本、报告、样例、文档）  
> **风险等级**: 低（新增目录与文件，不影响既有工具链）


## 一、文本文件变更清单

### 1. 新建 `debug/tongxin-power/DESIGN.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/tongxin-power/DESIGN.md` |
| **变更类型** | 新建 |
| **作用** | 项目级设计基准文档：结构分析、跨表验证、Schema设计、报表输出完整设计思想 |
| **关键章节** | §10.4 时间维度动态扩展（起止期自动检测设计）、验证结论 |
| **迁移方式** | 直接复制，无需调整 |

### 2. 新建 `debug/tongxin-power/CHANGELOG.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/tongxin-power/CHANGELOG.md` |
| **变更类型** | 新建 |
| **作用** | 报表输出变更日志：v1→v6 的每一次结构变动、Bug修复、设计决策 rationale |
| **关键记录** | v4 源文件污染修复、v5 面积去重 Bug、v6 动态扩展验证、实测与标注差异检测 |
| **迁移方式** | 直接复制，无需调整 |

### 3. 修订 `debug/tongxin-power/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/tongxin-power/README.md` |
| **变更类型** | 修订（大幅扩展） |
| **新增内容** | 根级文档说明、scripts/reports/samples 详细导航、报表结构 v6、渐进式读数特性、已知局限与风险 |
| **迁移方式** | 直接覆盖 |

### 4. 新建 `debug/tongxin-power/scripts/v6/` 目录（7 个模块）

> **设计决策**：单文件 542 行拆分为 7 个模块，每模块 ≤200 行，职责单一。

| 文件 | 行数 | 职责 | 输入 | 输出 |
|------|------|------|------|------|
| `config.py` | 16 | 路径常量、子表映射、仓库顺序 | — | POWER_PATH, AREA_PATH, OUTPUT_DIR, SHEET_MAP |
| `date_scanner.py` | 48 | 扫描子表日期列、解析日期标签、确定全局起止期 | xlsx 各子表 | 起期标签, 止期标签 |
| `area_loader.py` | 82 | 加载面积表、解析维度(库区/楼层/子区)、推断子表名 | 面积明细表 | area_map, infer_subtable |
| `record_builder.py` | ~95 | 构建 location 映射、读取汇总表2、关联起止期读数、fallback 修正 | 汇总表2 + 子表 | records 列表 |
| `aggregator.py` | 27 | parent 分组、仓库分组、排序键 | records | parent_groups, warehouse_groups |
| `excel_writer.py` | ~135 | 样式定义、3 个 Sheet 写入（明细/parent汇总/仓库汇总） | records + groups | xlsx 文件 |
| `main.py` | 56 | 主入口，协调各模块流程 | — | 调用链 + 落盘 |

**关键设计**：
- `record_builder.py` 增加 **fallback 机制**：parent 归类与 location 实际位置不一致时，按 location 修正，并在报表中亮黄底+红字标注，备注完整差异信息
- `excel_writer.py` 定义 `FALLBACK_FILL`（亮黄底）+ `FALLBACK_FONT`（红字加粗）

### 5. 新建 `debug/tongxin-power/samples/` 目录（源数据副本 + 样例）

| 文件 | 来源 | 说明 |
|------|------|------|
| `2026年5月用电数据表V3(1)-modified.xlsx` | 从原始源文件修改后复制 | 办公楼 0630 列已更新（差值 50~2000 度），供脚本调试使用 |
| `同芯聚联仓库租赁面积明细表.xlsx` | 从原始源文件复制 | 面积数据源副本 |
| `sample-records.csv` / `.json` | 脚本生成 | 5 条明细记录样例 |
| `sample-schema.json` | 脚本生成 | Schema 样例 |
| `sample-report-mini.xlsx` | 脚本生成 | 迷你报表样例（3 Sheet，5 条数据） |

> **重要**：`scripts/v6/config.py` 默认读取 `samples/` 下的副本，避免污染原始数据。

### 6. 新建/更新 `debug/tongxin-power/reports/` 下的报表文件

| 文件 | 说明 |
|------|------|
| `tongxin-summary-report-v6-modular.xlsx` | **最终报表**：3 Sheet + 渐进式读数 + 差异检测标注 |
| `tongxin-detail-records-v2.csv` / `.json` | 明细数据集 v2（182条，含 schema_uid） |
| `tongxin-schema-v1.json` / `.md` | 统一维度 Schema |
| 历史报表 v2~v5-fixed | 保留供追溯 |

### 7. 历史脚本（保留在 `scripts/` 根目录）

`analyze_*.py`, `validate_*.py`, `generate_*.py`（v2~v5）等历史脚本仍保留在 `scripts/` 根目录，未删除。


## 二、非文本操作（文件系统/数据迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 文件复制 | `D:\yidongyunpan\sync\pjt\fld\tongxin\2026年5月用电数据表V3(1).xlsx` | `debug/tongxin-power/samples/2026年5月用电数据表V3(1)-modified.xlsx` | 用电数据源副本 |
| 文件复制 | `D:\yidongyunpan\sync\pjt\fld\tongxin\同芯聚联仓库租赁面积明细表.xlsx` | `debug/tongxin-power/samples/同芯聚联仓库租赁面积明细表.xlsx` | 面积数据源副本 |
| 目录创建 | — | `debug/tongxin-power/scripts/v6/` | 模块化脚本目录 |
| 数据修改 | 办公楼 sheet 0630 列 | 同一副本内 | 随机生成差值 50~2000 度，使电费可计算 |


## 三、环境变量/配置速查

本次 session **不涉及** `.vscode/settings.json` 或其他环境配置的修改。全部变更局限在 `debug/tongxin-power/` 目录内。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 samples 目录齐全 | `Get-ChildItem "debug\tongxin-power\samples"` | 包含 2 个源数据副本 + 4 个样例文件 |
| 2 | 确认 v6 模块可运行 | `python scripts/v6/main.py` | 输出起止期标签、182 条记录统计、报表落盘路径 |
| 3 | 确认 fallback 检测生效 | 检查报表行110（seq=204） | 亮黄底 + 红字，备注"实测与标注差异" |
| 4 | 确认渐进式读数 | 检查办公楼 10 条设备 | 起期=0530，止期=0630，差值>0 |
| 5 | 确认缺数据处理 | 检查 1/2/3 号仓设备 | 止期=0，行置灰，用电量=None |
| 6 | 确认钩稽关系 | Sheet1 行数 = Sheet2 设备总数之和 = Sheet3 设备总数 | 182 = 182 = 182 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增目录 | `Remove-Item -Recurse "debug\tongxin-power"` |
| 恢复原始源文件 | 从 `.bak` 备份替换（如已修改原始文件） |
| 保留历史脚本 | 如需保留根目录历史脚本，仅删除 `v6/` 子目录和文档 |


## 六、跨环境迁移参考

1. **复制 `debug/tongxin-power/` 整个目录**到新环境
2. **确保原始源文件路径正确**，或修改 `scripts/v6/config.py` 中的 `POWER_PATH` / `AREA_PATH`
3. **运行验证清单** #2~#6，全部通过即完成迁移


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-09-162535 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求生成同芯聚联园区用电数据汇总报表，支持渐进式读数，脚本模块化 |
| **下次修订条件** | 新增子表读数列时验证动态列检测；新增库区时验证面积关联 |
| **跨环境迁移参考** | 直接复制 `debug/tongxin-power/` + 按验证清单执行 |


*文档生成时间：2026-06-09*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
