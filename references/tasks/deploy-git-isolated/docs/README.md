---
title: deploy-git-isolated/docs — 文档分类导航
description: 本 task 的文档子分类：patterns（设计模式）、harness（交付流程）、playbooks（操作手册）、research（深度研究）。date: 2026-06-18
---

# deploy-git-isolated/docs — 文档分类导航

> **分类原则**：`docs/` 下不再堆根，按主题落入子分类。


## 子分类

| 目录 | 主题 | 说明 |
|------|------|------|
| `patterns/` | **设计模式** | 从 task 演进中沉淀的可复用工程模式 |
| `harness/` | **交付流程** | 测试验证、质量门禁、交付检查清单 |
| `playbooks/` | **操作手册** | 具体任务的完整操作实录 |
| `research/` | **深度研究** | 架构决策、选型对比、调研验证的记录 |

## 当前文档

| 文档 | 分类 | 职责 |
|------|------|------|
| [PLUGIN-ARCHITECTURE.md](PLUGIN-ARCHITECTURE.md) | 根级 | 插件化点源架构设计说明 |
| [patterns/profile-filter-pattern.md](patterns/profile-filter-pattern.md) | patterns | Profile 筛选模式 |
| [patterns/manifest-plugin-pattern.md](patterns/manifest-plugin-pattern.md) | patterns | Manifest + Plugins 扩展模式 |
| [harness/delivery-checklist.md](harness/delivery-checklist.md) | harness | 四步交付流程检查清单 |
| [playbooks/github-publish-playbook.md](playbooks/github-publish-playbook.md) | playbooks | GitHub 发布操作实录 |
| [research/scripts-directory-taxonomy-research.md](research/scripts-directory-taxonomy-research.md) | research | scripts/ 目录子分类重构深度研究 |
| [research/task-dependency-graph.md](research/task-dependency-graph.md) | research | Task 依赖图与修订联动路径：PS 点源/Python import/文档引用/配置索引的全量依赖关系


*导航版本: v1.0*  
*创建时间: 2026-06-17*
