---
title: tool-discovery Skill 新建 — 解决 Agent 工具查询凭文件名推断的结构性缺陷
description: 本次 session 用户纠正 Agent 不查索引、仅凭文件名 glob/grep 推断工具列表的认知缺陷，新建 tool-discovery skill，建立先查 verified-task-index.json 真源索引 → 再查 README 自说明 → 再查脚本 docstring → 再查 skill 文档的检索规范。触发词已登记到 verified-trigger-index.json。
date: 2026-08-03
meta:
  version: "1.0.0"
---

# env-migration-tool-discovery-skill-creation-2026-08-03-110725

> **文档性质**：环境级变更记录。聚焦 tool-discovery skill 从设计到登记到验证的完整建设过程。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | tool-discovery Skill 新建与触发条件索引登记 |
| **日期** | 2026-08-03 |
| **文件名时间戳** | `2026-08-03-110725` |
| **触发原因** | 用户要求查看 jywl-settlement 进度，Agent 仅通过 glob `**/atomic-*git*.py` 推断工具列表，被用户指出"完全没有去看自说明或 index.json，认知不全面" |
| **影响范围** | `references/tasks/deploy-git-isolated/skills/tool-discovery/`、`references/runtime/verified-trigger-index.json` |
| **风险等级** | 低（新增 skill 和索引条目，不修改既有逻辑） |

## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/skills/tool-discovery/SKILL.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/tool-discovery/SKILL.md` |
| **变更类型** | `新建` |
| **作用** | 核心规范：定义 tool-discovery skill 的触发词、工作流、rg 检索策略、禁止行为 |
| **关键设计** | 检索优先级：① `verified-task-index.json`（真源索引）→ ② `README.md`（自说明导航）→ ③ Python docstring（脚本注释）→ ④ `skills/` 文档 |
| **验证方式** | `run-lint.py` lint-md 通过 |
| **迁移方式** | 无需迁移，skill 随 devroot 同步 |

### 2. 新建 `references/tasks/deploy-git-isolated/skills/tool-discovery/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/tool-discovery/README.md` |
| **变更类型** | `新建` |
| **作用** | 目录自说明导航：含使用示例、文件导航、上级链接 |
| **验证方式** | `run-lint.py` lint-md + link_checker 通过 |

### 3. 修改 `references/runtime/verified-trigger-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-trigger-index.json` |
| **变更类型** | `修改` |
| **新增内容** | ① `trigger_sources.skill-tool-discovery`（source_file 指向 SKILL.md）；② `triggers` 下 5 个触发条目（T001-T003 + E001-E002）；③ `conflict_domains.tool-discovery`；④ `conflict_resolution_rules.CR-007` |
| **作用** | 将 tool-discovery skill 纳入全项目触发条件统一索引，确保 Agent 能按规则触发 |
| **验证方式** | `run-lint.py` lint-json 通过 |
| **备份文件** | `venv/tmp/atomic-config-edit-json-verified-trigger-index-20260803-025112.bak` |

## 二、认知纠正记录（用户纠正项）

### 纠正 1：不查索引，仅凭文件名推断

**Agent 错误**：用户问"你会使用哪些 git/gh 工具"时，Agent 用 `glob **/atomic-*git*.py` 扫磁盘，凭文件名推断工具列表。

**用户纠正**：文件名不能反映真实职责，必须先看 `verified-task-index.json`（真源索引）和 `README.md`（自说明），再看 docstring。

**结果**：触发本次 skill 建设。

### 纠正 2：搜索范围遗漏 skills/

**Agent 错误**：最初设计的搜索范围只提到 scripts/py-tools/ 和 py-plugins/，遗漏了 skills/ 目录。

**用户纠正**：skills/ 下的 SKILL.md 和 README.md 也是工具发现的重要来源。

**结果**：skill 工作流 Step 5 增补 skills/ 检索。

### 纠正 3：术语抽象，不接地气

**Agent 错误**：最初使用"三层真源"等术语，用户反馈"陌生环境根本不知在说什么"。

**用户纠正**：改为大白话：先查索引 → 再查自说明 → 再查 docstring → 再查 skill。

**结果**：SKILL.md 中全部使用口语化表述。

## 三、触发词设计（你我约定）

| 场景 | 触发词 | 说明 |
|------|--------|------|
| **T001 — 场景工具查询** | "用什么工具做"、"这个该用什么脚本"、"查一下 deploy-git-isolated 的工具"、"py-tools 里有什么"、"找一下工具" | 用户想找一个功能对应的工具 |
| **T002 — 单工具用法查询** | "`atomic-git-push-smoke` 怎么调用"、"`workflow-deploy-full` 的用法是什么"、"`gh-pr-create` 的参数"、"这个脚本的入口命令" | 用户知道工具名，想知道怎么用 |
| **T003 — 工具列表查询** | "列出 deploy-git-isolated 的脚本"、"有哪些 atomic 脚本"、"workflow 脚本清单"、"task/下有什么工具"、"deploy-git-isolated 下有哪些工具"、"这个 task 里有什么工具" | 用户想获取某个类别的工具列表 |
| **E001 — 排他：直接执行** | "执行真源检测"、"记一版 version"、"下载 opencode" | 直接命中对应 mdc/skill |
| **E002 — 排他：高频任务** | "有什么高频任务"、"能做什么"、"帮助" | 命中 mdc-task-show |

## 四、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 skill 文件存在 | `Test-Path skills/tool-discovery/SKILL.md` | `True` |
| 2 | 确认 README 存在 | `Test-Path skills/tool-discovery/README.md` | `True` |
| 3 | 确认 lint 通过 | `run-lint.py --files SKILL.md README.md` | ✅ 全部通过 |
| 4 | 确认索引已登记 | `rg skill-tool-discovery verified-trigger-index.json` | 命中 T001-T003、E001-E002 |
| 5 | 确认 skill 可触发 | 用户 prompt "atomic-git-push-smoke 怎么调用" | Agent 加载 tool-discovery skill |

## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 skill 目录 | `Remove-Item -Recurse references/tasks/deploy-git-isolated/skills/tool-discovery` |
| 恢复 trigger-index | `Copy-Item venv/tmp/atomic-config-edit-json-verified-trigger-index-20260803-025112.bak references/runtime/verified-trigger-index.json` |
| 更新 README 导航 | 从 `references/env-migrations/README.md` 导航表中移除对应行 |

## 六、关联文档

| 文档 | 说明 |
|------|------|
| `references/tasks/deploy-git-isolated/skills/tool-discovery/SKILL.md` | skill 核心规范 |
| `references/tasks/deploy-git-isolated/skills/tool-discovery/README.md` | skill 自说明导航 |
| `references/runtime/verified-trigger-index.json` | 触发条件索引（已登记） |
| `schema/structure/trigger-index-schema.md` | 触发索引 schema 定义 |
| `schema/structure/env-migration-template.md` | env-migration 模板 |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-03-110725 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户纠正 Agent 工具查询认知缺陷，要求建立 skill 固化检索规范 |
| **下次修订条件** | ① trigger_words 增补/调整；② 检索范围扩展；③ rg 参数策略优化 |
| **跨环境迁移参考** | 复制 `skills/tool-discovery/` 目录 + 在目标环境 `verified-trigger-index.json` 中登记 trigger |

*文档生成时间：2026-08-03*  
*模板版本：v2*
