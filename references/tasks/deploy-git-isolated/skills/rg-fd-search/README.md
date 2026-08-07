---
title: rg-fd-search Skill 目录
description: 通用搜索能力封装——rg（内容搜索）+ fd（文件查找），强制搜索优先次序，默认禁止原生 grep/glob。
date: 2026-08-07
meta:
  version: 1.1.0
---

# rg-fd-search/

通用搜索能力封装 Skill。提供 rg（ripgrep）和 fd 的标准调用模板，强制遵循搜索优先次序（P0-P3），避免默认使用原生 grep/glob。

## 子目录 / 文件导航

| 文件/目录 | 用途 |
|-----------|------|
| [SKILL.md](SKILL.md) | Skill 主文档：触发词、工作流、参数速查、组合示例、SED 加载机制 |
| [scripts/](scripts/) | 执行面：skill 专属可执行脚本与辅助模块（不对外登记） |
| [references/](references/) | 引用面：外部资料、本地索引、配置快照 |
| [assets/](assets/) | 资产面：静态资源（截图、数据文件、图表） |
| [templates/](templates/) | 模板面：可复用模板（prompt、报告、配置片段） |
| [examples/](examples/) | 示例面：使用示例、测试用例、典型场景 |
| [versions/](versions/) | 版本面：演进时间线（`manifest.json`）+ 审计轨迹（`audit-trail.jsonl`）+ 聚合视图（`metrics.json`）+ 收敛归档（`archive/`） |
| [gotchas/](gotchas/) | 错误面：踩坑记录（时间线，不可变追加） |
| [evolutions/](evolutions/) | 行为面：规则/参数/流程演进补丁（有序加载，可收敛；当前已收敛至 v2.0.0，活跃补丁待积累） |
| [learnings/](learnings/) | 认知面：洞察、模式、基线、结论、启发式 |
| [baseline/](baseline/) | **审计基准面**：审计约定、Human/Agent 共同理解、工程偏好沉淀 |

## 搜索优先次序

## 搜索优先次序

| 优先级 | 层级 | 示例 |
|--------|------|------|
| P0 | 树状自说明 | README.md、TASK-TOOLS-INDEX.md、EXEC-CHEATSHEET.md、**devroot/vaults/ 下的 progress/conclusions/learnings/gotchas**（若存在）|
| P1 | JSON 真源索引 | ENTRY.json、verified-task-index.json（并列查询） |
| P2 | docstring | Python 模块注释 |
| P3 | 关键词搜索 | rg 全文搜索、fd 文件查找 |

## 上级导航

- [skills 总索引](../README.md)
- [deploy-git-isolated 根](../../README.md)
