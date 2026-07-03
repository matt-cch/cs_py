---
title: deploy-git-isolated — Baseline 导航索引
description: 规范基线总入口，提供全部 baseline 文件的导航与顶层原则速查。取代原 monolithic task-canonical-baseline.md。
date: 2026-07-03
meta:
  version: "2.0.0"
  source: task-canonical-baseline.md 拆分
---

# deploy-git-isolated — Baseline 导航索引

> **核心意图**：本文档是 **Agent 与人类在渐进式交互中共同确认的事实标准**的入口。  
> 它确保双方对以下问题有**归一化的理解**：
> - 什么是 Task（与 Skill 的边界在哪）
> - 真源（Single Source of Truth）存放在哪里
> - 命名约定（Naming Convention）如何消除歧义
> - Agent 执行路径与人类查阅路径如何对照
> - 如何渐进式确认、认可、固化事实
>
> **适用范围**：`references/tasks/deploy-git-isolated/` 目录下的全部文件与操作。  
> **约束性质**：框架层规范，极低变动频率；触及修改时按修订联动规则执行。  
> **模板来源**：`schema/task-template/task-canonical-baseline.md`


## 文件导航

| 文件 | 职责 | 阅读时机 |
|------|------|---------|
| [baseline-principles.md](baseline-principles.md) | Agent 执行哲学与工程化铁律（0.x） | 任何 Agent 执行操作前 |
| [baseline-semantics.md](baseline-semantics.md) | Task/Skill/Workflow 语义定义（1.x） | 不确定 Task 与 Skill 边界时 |
| [baseline-structure.md](baseline-structure.md) | 目录结构与文件位置约定（2.x + 6.x） | 新建/移动文件时 |
| [baseline-formats.md](baseline-formats.md) | 文件格式规范（SOP/CHEATSHEET/TOOLS-INDEX/ENTRY/DESIGN）（3.x） | 新建/修改文档时 |
| [baseline-operations.md](baseline-operations.md) | 修订联动、执行路径、版本演进与归档（4.x + 5.x + 7.x） | 执行变更、发布版本时 |
| [baseline-plugin-architecture.md](baseline-plugin-architecture.md) | 插件化架构、三层模型、命名规范、越级禁止（8.1-8.5 + 8.8 plugin） | 开发/修改 plugin 或 workflow 时 |
| [baseline-workflow-deploy.md](baseline-workflow-deploy.md) | JS 工具链、全链条部署、Git 空目录保留、三侧冲突仲裁（8.6-8.8 workflow/JS） | 开发 workflow、跨侧工具选型时 |
| [baseline-audit-truth.md](baseline-audit-truth.md) | Trigger 治理、外部工具引用、独立审计、决策真源集中化（8.2 + 8.9-8.10） | 设计审计机制、提取真源模块时 |


## 顶层原则速查（一句话铁律）

| # | 原则 | 出处 |
|---|------|------|
| 1 | 禁止现写命令行，优先复用现成工具 | [baseline-principles.md](baseline-principles.md) 0.1-0.2 |
| 2 | Long-Content 分步落盘，禁止 `python -c` / `powershell -Command` | [baseline-principles.md](baseline-principles.md) 0.3 |
| 3 | Workflow 自闭环执行，Agent 只构造入参、不干预步骤 | [baseline-principles.md](baseline-principles.md) 0.6 |
| 4 | 显式优于隐含，一切上下文必须显式设定、显式验证 | [baseline-principles.md](baseline-principles.md) 0.7 |
| 5 | 插件注册双向铁律：磁盘 `.py` ↔ `py-sort-rules.json` 一一对应 | [baseline-plugin-architecture.md](baseline-plugin-architecture.md) 8.4.7a |
| 6 | 禁止越级调用：Workflow 必须通过 `py_lib.load_plugins()` 获取能力 | [baseline-plugin-architecture.md](baseline-plugin-architecture.md) 8.4.5 |
| 7 | 审计者不能审计自己，自检≠独立审计 | [baseline-audit-truth.md](baseline-audit-truth.md) 8.9 |
| 8 | 决策真源集中化：下游只消费、不判断 | [baseline-audit-truth.md](baseline-audit-truth.md) 8.10 |


## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.0.0 | 2026-07-03 | 从 monolithic `task-canonical-baseline.md`（1600+ 行）拆分为 8 个专题 baseline 文件 + 本导航索引 |
| v1.9 | 2026-07-03 | 原文件最后版本，含 8.4.7a/8.9/8.10 新增 |
| v1.8 | 2026-07-03 | 原文件版本，含 8.4.7a/8.9 新增 |
| v1.7 | 2026-06-25 | 原文件版本，含 8.7.5 Git 空目录保留 |
| v1.6 | 2026-06-24 | 原文件版本，含 8.6/8.7/8.8 |
| v1.0 | 2026-06-16 | 骨架创建 |
