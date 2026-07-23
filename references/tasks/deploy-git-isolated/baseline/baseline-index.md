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
| [baseline-structure.md](baseline-structure.md) | 目录结构与文件位置约定（2.x + 6.x）+ Polyrepo 嵌套仓库的 Git 配置分层（2.3） | 新建/移动文件时 |
| [baseline-formats.md](baseline-formats.md) | 文件格式规范（3.x）+ 编码与换行符跨平台一致性（3.7） | 新建/修改文档时 |
| [baseline-operations.md](baseline-operations.md) | 修订联动、执行路径、版本演进与归档（4.x + 5.x + 7.x） | 执行变更、发布版本时 |
| [baseline-plugin-architecture.md](baseline-plugin-architecture.md) | 插件化架构、三层模型、命名规范、越级禁止（8.1-8.5 + 8.8 plugin） | 开发/修改 plugin 或 workflow 时 |
| [baseline-workflow-deploy.md](baseline-workflow-deploy.md) | JS 工具链、全链条部署、Git 空目录保留、三侧冲突仲裁、Pipeline Phase 产物统筹（8.6-8.9 workflow/JS） | 开发 workflow、跨侧工具选型时 |
| [baseline-audit-truth.md](baseline-audit-truth.md) | Trigger 治理、外部工具引用、独立审计、决策真源集中化（8.2 + 8.9-8.10） | 设计审计机制、提取真源模块时 |


## 顶层原则速查（一句话铁律）

| # | 原则 | 出处 |
|---|------|------|
| 1 | 禁止现写命令行，优先复用现成工具 | [baseline-principles.md](baseline-principles.md) 0.1-0.2 |
| 2 | Long-Content 分步落盘，禁止 `python -c` / `powershell -Command` | [baseline-principles.md](baseline-principles.md) 0.3 |
| 3 | Workflow 自闭环执行，Agent 只构造入参、不干预步骤 | [baseline-principles.md](baseline-principles.md) 0.6 |
| 4 | 显式优于隐含，一切上下文必须显式设定、显式验证 | [baseline-principles.md](baseline-principles.md) 0.7 |
| 5 | 隔离 Git 优先，所有 Git 操作默认使用隔离配置 | [baseline-principles.md](baseline-principles.md) 0.7.2 |
| 6 | 命令行纯粹原则：只含解释器+脚本+入参，不塞逻辑 | [baseline-principles.md](baseline-principles.md) 0.7.3 |
| 7 | `--devroot` / `--target` 强制必填，不传示警退出 | [baseline-principles.md](baseline-principles.md) 0.7.3 |
| 8 | 仓库性质分级：Team repo 写操作默认禁止，必须用户亲口确认 | [baseline-principles.md](baseline-principles.md) 0.8 |
| 9 | 未验证脚本绝对禁止用 team repo 测试，调试只限 personal repo | [baseline-principles.md](baseline-principles.md) 0.8.3 |
| 10 | 写操作前必须显式声明内容与影响，用户未肯定回复禁止执行 | [baseline-principles.md](baseline-principles.md) 0.8.2 |
| 11 | 插件注册双向铁律：磁盘 `.py` ↔ `py-sort-rules.json` 一一对应 | [baseline-plugin-architecture.md](baseline-plugin-architecture.md) 8.4.7a |
| 12 | 禁止越级调用：Workflow 必须通过 `py_lib.load_plugins()` 获取能力 | [baseline-plugin-architecture.md](baseline-plugin-architecture.md) 8.4.5 |
| 13 | 审计者不能审计自己，自检≠独立审计 | [baseline-audit-truth.md](baseline-audit-truth.md) 8.9 |
| 14 | 决策真源集中化：下游只消费、不判断 | [baseline-audit-truth.md](baseline-audit-truth.md) 8.10 |
| 15 | Pipeline phase 产物由上级通过 `--output` 显式指定，禁止内部封闭生成 | [baseline-workflow-deploy.md](baseline-workflow-deploy.md) 8.9 |
| 16 | devroot = 可用公共资源根，target = 操作对象；CWD 锚定保障公共资源可用性，target 显性隔离保障 polyrepo 互不污染 | [baseline-principles.md](baseline-principles.md) 0.7.3 |
| 17 | git-security.json = Repo 身份卡；repo_url 基准 vs 实测对碰；default_branch 消除 master/main 硬编码 | [baseline-workflow-deploy.md](baseline-workflow-deploy.md) 8.7.6 |


## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.4.0 | 2026-07-23 | baseline-workflow-deploy.md §8.7.6.2 改为「基准 vs 实测对碰模型」；新增 §8.7.6.6「default_branch 与分支保护策略」；代码层面完成 polyrepo_context.py / atomic-deploy-preflight.py / workflow-git-deploy-full-poly.py / gh-* 脚本的 default_branch 动态读取改造；顶层原则速查追加第 17 条 |
| v2.3.0 | 2026-07-23 | baseline-structure.md §2.3 扩展为完整 Polyrepo Git 配置四件套（`.git/`、`.gitignore`、`.gitattributes`、`git-security.json`），新增「Repo 身份卡」设计意图；baseline-workflow-deploy.md §8.7.6.2 更新 `repo_url` 解析优先级（`git-security.json` 升至第 2 优先级）；明确 `.env` 不再承载 `repo_url` 的 anti-pattern |
| v2.2.0 | 2026-07-23 | baseline-principles.md 0.7.3 新增「语义清晰化：公共资源 vs 操作对象」及「CWD 锚定的实质」；baseline-workflow-deploy.md 新增 §8.7.6「Polyrepo 部署架构设计共识」；顶层原则速查追加第 16 条 |
| v2.1.0 | 2026-07-23 | baseline-workflow-deploy.md 新增 §8.9「Pipeline Phase 产物统筹与 `--output` 统一参数规范」；顶层原则速查追加第 15 条 |
| v2.0.0 | 2026-07-03 | 从 monolithic `task-canonical-baseline.md`（1600+ 行）拆分为 8 个专题 baseline 文件 + 本导航索引 |
| v1.9 | 2026-07-03 | 原文件最后版本，含 8.4.7a/8.9/8.10 新增 |
| v1.8 | 2026-07-03 | 原文件版本，含 8.4.7a/8.9 新增 |
| v1.7 | 2026-06-25 | 原文件版本，含 8.7.5 Git 空目录保留 |
| v1.6 | 2026-06-24 | 原文件版本，含 8.6/8.7/8.8 |
| v1.0 | 2026-06-16 | 骨架创建 |
