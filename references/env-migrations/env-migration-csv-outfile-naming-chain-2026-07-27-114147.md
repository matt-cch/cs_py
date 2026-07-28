---
title: CSV 列转换工具 outfile 命名约定闭环建设
description: 补齐 atomic-csv-column-transform.py 的 outfile 构造约定，建立「配置真源 → 调用者读取 → 显式构造入参」的完整链条，同步更新 schema、docstring、EXEC-CHEATSHEET 与业务配置实例。
date: 2026-07-27
meta:
  version: 1.0
---

# env-migration-csv-outfile-naming-chain-2026-07-27-114147

> **Session 主题**：补齐 `atomic-csv-column-transform.py` 的 `--outfile` 命名约定与调用链条，解决「脚本不自动推断 outfile，调用者必须按配置构造」的语义缺失。
> **触发原因**：用户执行脚本时发现 outfile 未按约定自动生成，指出调用者必须先读同目录配置、再按规则构造入参，整个链条必须在文档中闭环。
> **风险等级**：低（文档与 schema 补全，不修改业务逻辑）


## 一、文本文件变更清单

### 1. 修改 `schema/json/csv-transform-config-schema.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/json/csv-transform-config-schema.json` |
| **变更类型** | `追加` |
| **新增内容** | `outfile_naming` 字段：rule、pattern、replacement、example |
| **作用** | 配置真源：定义 outfile 命名规则，供调用者（Agent/脚本）读取后构造入参 |
| **验证方式** | `run-lint.py --files csv-transform-config-schema.json` → lint_json + lint_encoding 通过 |
| **迁移方式** | 直接复制覆盖 |

### 2. 修改 `scripts/py-tools/atomic-csv-column-transform.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-csv-column-transform.py` |
| **变更类型** | `修改 docstring` |
| **新增内容** | 【调用者义务（--outfile 构造约定）】章节，4 步链条 |
| **作用** | 脚本 docstring 明确声明：本脚本不负责自动推断 outfile，命名规则由配置真源驱动，调用者必须显式构造后传入 |
| **验证方式** | `run-lint.py --files atomic-csv-column-transform.py` → lint_python + lint_encoding 通过 |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `新增章节 + 修改参数语义表` |
| **新增内容** | S5.6 新增「调用链条（调用者义务）」小节；`--outfile` 行追加命名约定说明 |
| **作用** | 命令速查真源：让调用者一眼看到必须先读配置、再构造 outfile 的完整流程 |
| **验证方式** | `run-lint.py --files EXEC-CHEATSHEET.md --fix` → md_lint + link_checker + lint_encoding 通过 |
| **迁移方式** | 直接覆盖 |

### 4. 修改业务配置实例 `D:\demo\csv-transform-feiliks-invoice.json`

| 属性 | 值 |
|------|-----|
| **路径** | `D:\demo\csv-transform-feiliks-invoice.json`（与源 CSV 同目录） |
| **变更类型** | `追加` |
| **新增内容** | `outfile_naming` 字段，含 rule 与 example |
| **作用** | 业务配置实例与 schema 保持一致，调用者（Agent）在同目录读取此配置后按规则构造 outfile |
| **验证方式** | 手动确认 JSON 语法正确 |
| **迁移方式** | 业务目录下的配置，随业务数据迁移 |


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等非文本操作。


## 三、调用链条（核心设计决策）

```
1. 定位源 CSV 所在目录
      ↓
2. 检查该目录下是否存在 csv-transform-<场景>.json 配置
      ↓
3. 若存在 → 读取其中 "outfile_naming" 规则 → 按 rule + example 构造 outfile
   若不存在 → 调用者自行决定 outfile（建议与源文件同目录）
      ↓
4. 将构造好的 outfile 绝对路径显式传入 --outfile → 执行脚本
```

**铁律**：`atomic-csv-column-transform.py` 本身不负责自动推断 outfile，命名规则由**配置真源**驱动，调用者必须先读配置、再构造入参。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.json`（csv-transform-config-schema.json） | `run-lint.py` lint_json + lint_encoding | JSON 语法、编码/BOM/换行 | ✅ 通过 |
| `.py`（atomic-csv-column-transform.py） | `run-lint.py` lint_python + lint_encoding | Python 语法、编码/BOM/换行 | ✅ 通过 |
| `.md`（EXEC-CHEATSHEET.md） | `run-lint.py` md_lint + link_checker + lint_encoding | frontmatter、链接、编码 | ✅ 通过 |


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 schema 包含 outfile_naming | 读取 `schema/json/csv-transform-config-schema.json` | 存在 `outfile_naming` 字段 |
| 2 | 确认 docstring 有调用者义务 | 读取 `atomic-csv-column-transform.py` 前 30 行 | 存在【调用者义务】章节 |
| 3 | 确认 EXEC-CHEATSHEET 有链条说明 | 搜索 S5.6「调用链条」 | 存在 4 步流程图 |
| 4 | 端到端执行 | 按调用链条构造 outfile 后执行脚本 | exit 0，outfile 命名符合约定 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 schema | 从 git 恢复 `csv-transform-config-schema.json` |
| 恢复 docstring | 从 git 恢复 `atomic-csv-column-transform.py` |
| 恢复 EXEC-CHEATSHEET | 从 git 恢复 `EXEC-CHEATSHEET.md` |
| 恢复业务配置 | 手动删除 `D:\demo\csv-transform-feiliks-invoice.json` 中的 `outfile_naming` 字段 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-27-114147 |
| **更新人** | Human + Agent Session |
| **变更触发** | atomic-csv-column-transform.py outfile 命名约定缺失，调用链条未闭环 |
| **下次修订条件** | 新增 transform 类型 / 修改 outfile 命名规则 / 发现新调用者义务 |
| **跨环境迁移参考** | 复制 schema + docstring + EXEC-CHEATSHEET 变更；业务配置实例随数据目录迁移 |
