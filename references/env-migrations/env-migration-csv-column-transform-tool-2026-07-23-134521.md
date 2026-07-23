---
title: CSV 列无损转换原子工具泛化建设
description: 将 feiliks-invoice-csv 的硬编码日期更新工具泛化为配置驱动的通用 CSV 列转换框架，配套 schema、config、文档与修订联动。
date: 2026-07-23
meta:
  version: 1.0
---

# env-migration-csv-column-transform-tool-2026-07-23-134521

> **Session 主题**：将 `debug/feiliks-invoice-csv/tool/csv_update_invoice_date.py` 泛化为通用 CSV 列转换原子工具 `atomic-csv-column-transform.py`，建设配套 JSON Schema、配置实例、文档索引与修订联动。
> **触发原因**：原工具只改 "Invoice date" 一列，硬编码逻辑无法复用到其他场景；需要配置驱动（改 JSON 配置即可适配新场景，py 框架不变）。
> **风险等级**：低（新增工具，不修改既有业务逻辑）


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-csv-column-transform.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-csv-column-transform.py` |
| **变更类型** | `新建` |
| **作用** | 通用 CSV 列无损转换原子工具：读取源 CSV → 按配置规则转换指定列 → 写入新 CSV → 生成 manifest |
| **核心参数** | `--input`（源 CSV 文件/目录）、`--outfile`（业务产物 CSV）、`--output`（审计 manifest JSON）、`--config`（转换规则配置 JSON）、`--dry-run`（预览模式） |
| **关键决策** | `--output` 严格指 audit manifest（保持 baseline §8.9 ontology 一致），业务产物用 `--outfile` |
| **内置 transform 类型** | `today_ymd`、`today_iso`、`fixed`、`regex_replace`、`empty` |
| **验证方式** | `run-lint.py --files atomic-csv-column-transform.py` → lint_python + lint_encoding 通过 |
| **迁移方式** | 可直接复制到目标环境的对应路径；无需额外配置 |

### 2. 新建 `references/tasks/deploy-git-isolated/schema/json/csv-transform-config-schema.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/json/csv-transform-config-schema.json` |
| **变更类型** | `新建` |
| **作用** | atomic-csv-column-transform.py 的配置驱动契约 JSON Schema（draft-07） |
| **验证方式** | `run-lint.py --files csv-transform-config-schema.json` → lint_json + lint_encoding 通过 |
| **迁移方式** | 随 atomic-csv-column-transform.py 一同复制 |

### 3. 修改 `references/tasks/deploy-git-isolated/schema/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/README.md` |
| **变更类型** | `追加条目` |
| **新增内容** | 在 `json/` 文件清单中追加 `csv-transform-config-schema.json` 条目 |
| **作用** | schema 目录导航联动，确保新增 schema 可被 Agent/人类发现 |
| **验证方式** | `run-lint.py --files schema/README.md --fix` → md_lint + link_checker + lint_encoding 通过 |

### 4. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `追加条目` |
| **新增内容** | 在 py-tools 表格中追加 `atomic-csv-column-transform.py` 条目 |
| **作用** | 工具速查索引，供 Agent tool-audit 时查询 |
| **验证方式** | `run-lint.py --files TASK-TOOLS-INDEX.md --fix` → md_lint + link_checker + lint_encoding 通过 |

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `新增章节` |
| **新增内容** | Stage S5.6 "CSV 列转换（配置驱动）"：参数语义表、默认配置示例、自定义配置示例、内置 transform 类型表 |
| **作用** | 命令执行速查，Agent/用户/终端共享同一真源 |
| **验证方式** | `run-lint.py --files EXEC-CHEATSHEET.md --fix` → md_lint + link_checker + lint_encoding 通过 |

### 6. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `追加条目` |
| **新增内容** | `available_scripts_and_tools.atomic-csv-column-transform` 条目 |
| **修改方式** | `atomic-config-edit-json.py --batch @patch.json --backup`（非手敲 edit） |
| **验证方式** | `run-lint.py --files verified-task-index.json` → lint_json + lint_encoding 通过 |


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等非文本操作。


## 三、配置实例（业务配置 JSON）

配置文件与业务源 CSV **同目录**存放，命名规范 `csv-transform-<场景>.json`：

```json
{
  "$schema": "${devroot}/references/tasks/deploy-git-isolated/schema/json/csv-transform-config-schema.json",
  "transforms": {
    "Invoice date": {"type": "today_ymd"}
  }
}
```

> **注意**：`$schema` 使用 `${devroot}` 占位符，跨机器时需替换为实际 devroot 绝对路径。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py`（atomic-csv-column-transform.py） | `run-lint.py` lint_python + lint_encoding | Python 语法、编码/BOM/换行 | ✅ 通过 |
| `.json`（csv-transform-config-schema.json） | `run-lint.py` lint_json + lint_encoding | JSON 语法、编码/BOM/换行 | ✅ 通过 |
| `.md`（TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md / schema/README.md） | `run-lint.py` md_lint + lint_encoding + link_checker | frontmatter、编码、链接 | ✅ 通过 |
| `.json`（verified-task-index.json） | `run-lint.py` lint_json + lint_encoding | JSON 语法、编码 | ✅ 通过 |


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认脚本语法正确 | `run-lint.py --files atomic-csv-column-transform.py` | lint_python + lint_encoding 通过 |
| 2 | 默认配置转换测试 | `atomic-csv-column-transform.py --input <csv> --outfile <out> --output <manifest>` | exit 0，outfile 中 Invoice date 变为今天 YYYYMMDD |
| 3 | 自定义配置转换测试 | 编写含 `today_iso` / `fixed` / `regex_replace` / `empty` 的配置 JSON，传入 `--config` | 对应列按规则转换 |
| 4 | 预览模式测试 | 追加 `--dry-run` | 输出前 3 行对比，不写入任何文件 |
| 5 | 目录扫描模式 | `--input` 指向含多个 CSV 的目录 | 自动选中最新 mtime 的 CSV，stdout 有 `[目录扫描]` 醒目提示 |
| 6 | manifest output 字段 | 读取生成的 manifest JSON | `"output"` 字段值为 manifest 自身绝对路径（非 null） |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建脚本 | `Remove-Item "references/tasks/deploy-git-isolated/scripts/py-tools/atomic-csv-column-transform.py"` |
| 删除 schema | `Remove-Item "references/tasks/deploy-git-isolated/schema/json/csv-transform-config-schema.json"` |
| 恢复文档 | 从 git 恢复 TASK-TOOLS-INDEX.md、EXEC-CHEATSHEET.md、schema/README.md |
| 恢复索引 | 从 `.bak` 恢复 verified-task-index.json，或 atomic-config-edit-json.py remove 对应条目 |


## 七、踩坑记录（本次 session 发现的真实问题）

### 踩坑 1：初始 `--output` 语义与 baseline §8.9 冲突

- **现象**：最初设计 `--output` 指 CSV 产物，用户指出与 framework 的 `--output=manifest` 语义不一致
- **根因**：原 feiliks 工具有两个输出（CSV + manifest），但 baseline 定义 `--output` 为 audit 产物
- **修复**：改为 `--output` = manifest，`--outfile` = 业务产物 CSV，保持 ontology 一致

### 踩坑 2：manifest 文件中 `output` 字段为 `null`

- **现象**：manifest 落盘后 `"output": null`
- **根因**：代码先 `_save_manifest()` 写盘，后 `manifest["output"] = str(manifest_path)` 赋值，导致文件里没有回填
- **修复**：先赋值 `manifest["output"]`，再调用 `_save_manifest()` 写盘

### 踩坑 3：配置 `$schema` 用了绝对路径

- **现象**：`$schema` 写死 `D:/pjt/cursor/cs_py/...`，跨机器失效
- **修复**：改为 `${devroot}/references/...` 占位符

### 踩坑 4：JSON 编辑时违规使用 `edit` 工具

- **现象**：修改 `verified-task-index.json` 时直接用了 `edit`
- **根因**：忘记先过 tool-audit，凭惯性操作
- **修复**：改道 `atomic-config-edit-json.py --batch @patch.json --backup`


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-23-134521 |
| **更新人** | Human + Agent Session |
| **变更触发** | feiliks-invoice-csv 硬编码工具泛化需求 |
| **下次修订条件** | 新增 transform 类型 / 修改参数语义 / 发现新 bug |
| **跨环境迁移参考** | 复制 `atomic-csv-column-transform.py` + `csv-transform-config-schema.json` + 按「验证清单」逐条执行 |
