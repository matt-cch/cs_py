---
title: 触发条件索引治理体系建设 — env-migration
description: 建立全项目触发条件统一索引，定义 governance_rules 关联性治理规则，并在 SKILL.md / mdc / AGENTS.md 中植入索引引用说明。
date: 2026-06-10
---

# `env-migration-trigger-index-governance-2026-06-10-155422.md`

> **Session 主题**：触发条件索引治理体系建设（新增 governance_rules schema、索引 governance 字段、来源文件引用说明、AGENTS.md 治理规则章节）
> **触发原因**：用户明确要求触发条件的新增、修改、使用都必须参考规则文件，关联性必须有所描述和记载
> **影响范围**：`schema/structure/`、`references/runtime/`、`.agents/skills/`、`.cursor/rules/`、`venv/.opencode/AGENTS.md`
> **风险等级**：低（纯文档/规则变更，不涉及业务代码或环境配置）


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 触发条件索引治理体系建设 |
| **日期** | 2026-06-10 |
| **文件名时间戳** | `2026-06-10-155422` |
| **触发原因** | 用户明确要求触发条件的新增/修改/使用必须参考规则文件，关联性必须被描述和记载 |
| **影响范围** | schema/structure/、references/runtime/、.agents/skills/、.cursor/rules/、venv/.opencode/AGENTS.md |
| **风险等级** | 低 |


## 一、文本文件变更清单

### 1. 新建 `schema/structure/trigger-index-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/trigger-index-schema.md` |
| **变更类型** | `新建` |
| **内容摘要** | `verified-trigger-index.json` 的 schema 定义，含：meta、naming_convention、trigger_sources、conflict_domains、triggers、conflict_resolution_rules、audit_framework、**governance_rules（第 8 节）**、修订联动义务、迁移指南 |
| **作用** | 定义触发条件索引的数据结构和治理规则，是框架层规范 |
| **验证方式** | `read` 确认文件存在，检查 frontmatter 和章节结构完整 |
| **迁移方式** | 可直接复制 |

### 2. 新建 `references/runtime/verified-trigger-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-trigger-index.json` |
| **变更类型** | `新建` |
| **内容摘要** | 全项目触发条件真源索引，含 20 个 trigger_sources、10 个 conflict_domains、35 个 triggers（含全局唯一 ID）、6 条 conflict_resolution_rules、audit_framework、**meta.governance** |
| **作用** | 全项目触发条件的唯一真源，供 Agent 判断触发时读取 |
| **验证方式** | `read` 确认 JSON 结构完整，检查 `meta.governance` 存在 |
| **迁移方式** | 可直接复制 |

### 3. 修改 `schema/structure/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/README.md` |
| **变更类型** | `追加` |
| **新增内容** | 导航表中追加 `trigger-index-schema.md` 条目 |
| **插入位置** | 导航表末尾，在 `schema-index-schema.md` 之后 |
| **作用** | 目录自说明与新增文件保持联动 |
| **验证方式** | `read` 确认导航表包含新条目 |
| **迁移方式** | 仅需追加一行 |

### 4. 修改 `references/runtime/verified-schema-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-schema-index.json` |
| **变更类型** | `追加` |
| **新增内容** | `schema_files` 中追加 `trigger-index-schema.md` 条目；`last_updated` 更新为 `2026-06-10T16:00:00` |
| **作用** | schema 索引中登记新 schema 文件 |
| **验证方式** | `read` 确认条目存在且 `path_exists: true` |
| **迁移方式** | 仅需追加一个 JSON 对象 |

### 5. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `追加` |
| **新增内容** | `available_scripts_and_tools` 中追加 `trigger-index` helper 条目 |
| **作用** | 任务索引中登记触发条件索引 helper |
| **验证方式** | `read` 确认条目存在 |
| **迁移方式** | 仅需追加一个 JSON 对象 |

### 6. 修改 `.agents/skills/github-proxy-connectivity-test/SKILL.md`

| 属性 | 值 |
|------|-----|
| **路径** | `.agents/skills/github-proxy-connectivity-test/SKILL.md` |
| **变更类型** | `追加` |
| **新增内容** | 在「触发事项」章节开头追加索引引用说明（固定格式） |
| **作用** | 声明本文件触发条件受 `verified-trigger-index.json` 统一管理 |
| **验证方式** | `read` 确认引用说明存在 |
| **迁移方式** | 仅需追加一段引用说明 |

### 7. 修改 `.cursor/rules/high-frequency-shell-guard-content.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-shell-guard-content.mdc` |
| **变更类型** | `追加` |
| **新增内容** | 在「1. 触发词约定」章节开头追加索引引用说明 |
| **作用** | 同上 |
| **验证方式** | `read` 确认引用说明存在 |
| **迁移方式** | 仅需追加一段引用说明 |

### 8. 修改 `.cursor/rules/high-frequency-tool-shell-audit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| **变更类型** | `追加` |
| **新增内容** | 在文件开头（一句话铁律之前）追加索引引用说明 |
| **作用** | 同上 |
| **验证方式** | `read` 确认引用说明存在 |
| **迁移方式** | 仅需追加一段引用说明 |

### 9. 修改 `venv/.opencode/AGENTS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | `追加` |
| **新增内容** | 文档末尾新增「触发条件索引治理规则」完整章节（含统一索引说明、4 条关联性义务、受约束触发条件清单、违规后果） |
| **作用** | AGENTS.md 作为项目级硬性约束，承载触发条件治理规则 |
| **验证方式** | `read` 确认章节存在且结构完整 |
| **迁移方式** | 仅需追加一个章节 |

### 10. 新建 `references/changelog/changelog-2026-06-10-trigger-index-governance.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/changelog-2026-06-10-trigger-index-governance.md` |
| **变更类型** | `新建` |
| **内容摘要** | 本次变更的 changelog 记录（概览式），含变更记录表、关键决策、文档元信息 |
| **作用** | 按时间线独立记录本次 monorepo 级变更，不修改已有的 `monorepo-env-changelog.md` |
| **验证方式** | `read` 确认文件存在 |
| **迁移方式** | 可直接复制 |

### 11. 修改 `references/changelog/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/README.md` |
| **变更类型** | `追加` |
| **新增内容** | 文件导航表中追加新建的 changelog 文件条目 |
| **作用** | 目录自说明与新增文件保持联动 |
| **验证方式** | `read` 确认导航表包含新条目 |
| **迁移方式** | 仅需追加一行 |


## 二、非文本操作

本次 session **无**文件系统/缓存迁移等非文本操作。所有变更均为文本文件的新建或追加。


## 三、环境变量速查

本次 session **不涉及**环境变量变更。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 trigger-index-schema.md 存在 | `read "${devroot}/schema/structure/trigger-index-schema.md"` | 文件存在，含第 8 节 governance_rules |
| 2 | 确认 verified-trigger-index.json 存在 | `read "${devroot}/references/runtime/verified-trigger-index.json"` | 文件存在，`meta.governance` 对象完整 |
| 3 | 确认 SKILL.md 索引引用 | `read "${devroot}/.agents/skills/github-proxy-connectivity-test/SKILL.md"`，搜索「触发条件索引」 | 引用说明存在于「触发事项」章节开头 |
| 4 | 确认 mdc 索引引用 | `read "${devroot}/.cursor/rules/high-frequency-shell-guard-content.mdc"`，搜索「触发条件索引」 | 引用说明存在于「1. 触发词约定」开头 |
| 5 | 确认 AGENTS.md 治理规则 | `read "${devroot}/venv/.opencode/AGENTS.md"`，搜索「触发条件索引治理规则」 | 章节存在，含 4 条关联性义务 |
| 6 | 确认 schema-index 已登记 | `read "${devroot}/references/runtime/verified-schema-index.json"`，搜索 `trigger-index-schema` | 条目存在，`path_exists: true` |
| 7 | 确认 task-index 已登记 | `read "${devroot}/references/runtime/verified-task-index.json"`，搜索 `trigger-index` | 条目存在 |


## 五、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 删除新建文件 | `Remove-Item "${devroot}/schema/structure/trigger-index-schema.md"`、`Remove-Item "${devroot}/references/runtime/verified-trigger-index.json"`、`Remove-Item "${devroot}/references/changelog/changelog-2026-06-10-trigger-index-governance.md"` |
| 恢复来源文件 | 从 `references/env-migrations/env-migration-trigger-index-governance-2026-06-10-155422.md` 中提取各文件的 `oldString`，用 `edit` 回滚 |
| 恢复索引文件 | 从本 env-migration 中提取 `verified-schema-index.json` 和 `verified-task-index.json` 的旧状态，用 `edit` 回滚 |
| 恢复导航文件 | 从 `references/changelog/README.md` 和 `schema/structure/README.md` 中删除新增条目 |

> **注意**：回滚前务必 `read` 各文件当前状态，确认无后续 session 的变更覆盖。


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-10-155422 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求触发条件的新增/修改/使用必须参考规则文件，关联性必须被描述和记载 |
| **下次修订条件** | 新增/修改触发条件时，同步验证本 env-migration 中的文件清单是否仍有效 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-10-155422*