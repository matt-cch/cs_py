---
title: deploy-git-isolated/docs — 文档分类导航
description: 本 task 的文档子分类：patterns（设计模式）、harness（交付流程）、playbooks（操作手册）、research（深度研究）。
date: 2026-06-18
meta: {}
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
| [patterns/browser-inject-three-layer-pattern.md](patterns/browser-inject-three-layer-pattern.md) | patterns | 浏览器注入三层架构：JS 资产体系 + Playwright 注入 |
| [harness/delivery-checklist.md](harness/delivery-checklist.md) | harness | 四步交付流程检查清单 |
| [playbooks/github-publish-playbook.md](playbooks/github-publish-playbook.md) | playbooks | GitHub 发布操作实录 |
| [research/scripts-directory-taxonomy-research.md](research/scripts-directory-taxonomy-research.md) | research | scripts/ 目录子分类重构深度研究 |
| [research/task-dependency-graph.md](research/task-dependency-graph.md) | research | Task 依赖图与修订联动路径：PS 点源/Python import/文档引用/配置索引的全量依赖关系 |
| [research/workflow-entry-plugins-architecture-research.md](research/workflow-entry-plugins-architecture-research.md) | research | workflow→entry→plugins 三层架构选型演进与反例分析（lint 体系建设 session 共识沉淀） |
| [research/task-agent-self-explanation-validation.md](research/task-agent-self-explanation-validation.md) | research | Task Agent 自说明能力验证实验 — 从零上下文到自主执行的探索，含知行 gap 分析与改进建议 |
| [research/agent-directory-reading-pattern.md](research/agent-directory-reading-pattern.md) | research | Agent 目录自然阅读次序模式 — 从目录扫描到意图衔接的五层认知模型 |
| [research/runtime-atomic-integration-experience.md](research/runtime-atomic-integration-experience.md) | research | 运行时域原子脚本集成经验 — verify-runtime / download-runtime-tool 重构踩坑、决策与修复路径 |
| [research/git-local-remote-state-timeline-clarification.md](research/git-local-remote-state-timeline-clarification.md) | research | Git 本地/Remote 生效机制时间线 — workflow-deploy 与 workflow-gh 的衔接前提与常见误判 |
| [research/branch-vs-worktree-equivalence-and-differences.md](research/branch-vs-worktree-equivalence-and-differences.md) | research | Branch 与 Worktree 模式在 PR 闭环中的等价性与差异 |
| [research/crlf-lf-line-ending-governance-research-2026-07-08-111237.md](research/crlf-lf-line-ending-governance-research-2026-07-08-111237.md) | research | CRLF/LF 换行符治理深度研究 — 全仓库文本文件强制 LF 的决策路径 |
| [research/scriptc-windows-native-build-investigation-2026-07-29-111400.md](research/scriptc-windows-native-build-investigation-2026-07-29-111400.md) | research | scriptc Windows 原生编译踩坑实录 — 冲动试错 vs 先搜 Issues 的教训 |


*导航版本: v1.7*  
*更新时间: 2026-07-08*
