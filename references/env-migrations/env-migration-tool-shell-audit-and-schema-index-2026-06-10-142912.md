---
title: Tool/Shell 调用规则层审计 + 渐进式真源索引体系建设
description: 新增 high-frequency-tool-shell-audit.mdc 机制；新增 verified-task-index.json 和 verified-schema-index.json 两个渐进式真源索引；rules/ mdc 与索引系统建立关联。
date: 2026-06-10
---

# env-migration-tool-shell-audit-and-schema-index-2026-06-10-142912

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Tool/Shell 调用规则层审计机制建设 + 渐进式真源索引体系（task-index + schema-index） |
| **日期** | 2026-06-10（frontmatter；文件名时间戳 `2026-06-10-142912`） |
| **触发原因** | 用户指出 env-migration 未命中高频任务 mdc 而是临时发挥；要求建立 tool 调用前审计机制；要求建立渐进式索引供快速检索引用 |
| **影响范围** | `.cursor/rules/`、 `references/runtime/`、 `schema/structure/` |
| **风险等级** | 低（纯规则与索引建设，不涉及业务代码或运行时配置） |


## 一、文本文件变更清单

### 1. 新建 `.cursor/rules/high-frequency-tool-shell-audit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| **变更类型** | 新建 |
| **作用** | 任何 tool（bash/write/edit）调用前强制自检：是否命中高频任务？是否有现成脚本？是否重复造轮子？ |
| **关键内容** | `alwaysApply: true`；强制自检清单模板（含 schema 可用性检查）；高频任务速查表（7 项）；现成脚本速查表（13 项）；与 Shell 审计的衔接流程；违规后果 |
| **验证方式** | 下次涉及 tool 调用时，检查是否自动输出【Tool 调用规则层审计】自检块 |
| **迁移方式** | 直接复制 |

### 2. 新建 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 新建 |
| **作用** | 高频任务 mdc 与现成脚本/工具的真源索引，供 Agent 快速查询 |
| **关键内容** | `meta`（含 `last_updated`、`source_directory_mdc` 等）；`high_frequency_tasks`（8 项，覆盖全部 high-frequency-*.mdc）；`available_scripts_and_tools`（15 项，覆盖现成脚本与 skills） |
| **验证方式** | `Test-Path` 确认文件存在；抽查 `path_exists` 字段与磁盘实际一致 |
| **迁移方式** | 直接复制 |

### 3. 新建 `schema/structure/task-index-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/task-index-schema.md` |
| **变更类型** | 新建 |
| **作用** | `verified-task-index.json` 的 schema 定义，确保 Agent 读写格式一致 |
| **关键内容** | `meta` 结构；`high_frequency_tasks` 任务定义对象（含 `mdc_file`、`trigger_words`、`standard_prompt` 等）；`available_scripts_and_tools` 工具定义对象（含 `type` 枚举：`script`/`skill`/`helper`/`skill_python`）；修订联动义务 |
| **验证方式** | 对照 JSON 实际结构，确认 schema 定义无遗漏 |
| **迁移方式** | 直接复制 |

### 4. 新建 `references/runtime/verified-schema-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-schema-index.json` |
| **变更类型** | 新建 |
| **作用** | `schema/` 目录下全部规范文件的渐进式真源索引 |
| **关键内容** | `meta`；`schema_categories`（4 个分类：structure/encoding/design/tool，共 19 个文件条目）；每个条目含 `path_exists`、`target_data_files`（若适用）、`verified_at` |
| **验证方式** | `Test-Path` 确认文件存在；抽查分类目录下文件数量与索引一致 |
| **迁移方式** | 直接复制 |

### 5. 新建 `schema/structure/schema-index-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/schema-index-schema.md` |
| **变更类型** | 新建 |
| **作用** | `verified-schema-index.json` 的 schema 定义 |
| **关键内容** | `meta` 结构；`schema_categories` 分类定义对象（含 `files` 子对象）；文件定义对象结构（含 `target_data_files`）；修订联动义务 |
| **验证方式** | 对照 JSON 实际结构确认 |
| **迁移方式** | 直接复制 |

### 6. 修改 `.cursor/rules/high-frequency-task-index.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-task-index.mdc` |
| **变更类型** | 修改 |
| **新增/修改内容** | 顶部「使用方法」段落追加："**机器可读真源**：Agent 执行层应以 `references/runtime/verified-task-index.json` 为真源速查..."；总览表追加第 7 项 "Tool/Shell 调用规则层审计"；新增 "## 7. Tool/Shell 调用规则层审计" 详细说明；快速决策表追加对应行 |
| **作用** | 将高频任务索引与 `verified-task-index.json` 关联，确保 Agent 执行层以 JSON 为真源 |
| **验证方式** | `read` 确认新增段落和条目存在 |
| **迁移方式** | 直接覆盖 |

### 7. 修改 `.cursor/rules/high-frequency-tool-shell-audit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| **变更类型** | 修改 |
| **新增/修改内容** | 第 4 节「常见现成脚本/工具速查」重构为两层：4.1 权威索引（指向 `verified-task-index.json`）+ 4.2 速查摘要；自检义务更新为「先扫上表，再核对 `verified-task-index.json`」 |
| **作用** | 明确 JSON 索引为真源，内嵌表格仅作人类速查参考 |
| **验证方式** | `read` 确认 4.1/4.2 层级存在 |
| **迁移方式** | 直接覆盖 |

### 8. 修改 `schema/structure/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/README.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 文件导航表追加 `task-index-schema.md` 和 `schema-index-schema.md` 两条 |
| **作用** | schema 目录自说明与新增文件保持联动 |
| **验证方式** | `read` 确认导航表含新条目 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。


## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 tool-audit mdc 存在 | `Test-Path ".cursor/rules/high-frequency-tool-shell-audit.mdc"` | `True` |
| 2 | 确认 task-index JSON 存在 | `Test-Path "references/runtime/verified-task-index.json"` | `True` |
| 3 | 确认 schema-index JSON 存在 | `Test-Path "references/runtime/verified-schema-index.json"` | `True` |
| 4 | 确认 task-index schema 存在 | `Test-Path "schema/structure/task-index-schema.md"` | `True` |
| 5 | 确认 schema-index schema 存在 | `Test-Path "schema/structure/schema-index-schema.md"` | `True` |
| 6 | 确认 mdc 关联链接 | `read ".cursor/rules/high-frequency-task-index.mdc"` | 含 "机器可读真源" 段落 |
| 7 | 确认 schema 导航联动 | `read "schema/structure/README.md"` | 导航表含两个新 schema 条目 |
| 8 | 确认 tool 调用触发审计 | 发送任意涉及 tool 的 prompt | 自动输出【Tool 调用规则层审计】 |


## 四、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增 mdc | `Remove-Item ".cursor/rules/high-frequency-tool-shell-audit.mdc"` |
| 删除新增 JSON | `Remove-Item "references/runtime/verified-task-index.json"`、`Remove-Item "references/runtime/verified-schema-index.json"` |
| 删除新增 schema | `Remove-Item "schema/structure/task-index-schema.md"`、`Remove-Item "schema/structure/schema-index-schema.md"` |
| 恢复 mdc 修改 | 从 git history 恢复 `.cursor/rules/high-frequency-task-index.mdc`、`.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| 恢复 schema README | 从 git history 恢复 `schema/structure/README.md` |


## 五、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-10-142912 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求：① env-migration 必须命中高频任务、杜绝现写；② 建立 tool 调用前审计机制；③ 建立渐进式真源索引体系 |
| **下次修订条件** | 新增高频任务 mdc、新增 skill/脚本、schema 结构扩展 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
