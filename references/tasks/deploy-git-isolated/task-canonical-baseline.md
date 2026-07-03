---
title: deploy-git-isolated — Task Canonical Baseline（已迁移）
description: 本文件为兼容性跳转页。原 monolithic baseline 已拆分为 baseline/ 目录下的 9 个专题文件。请访问 baseline-index.md 获取完整导航。
date: 2026-07-03
meta:
  version: "2.0.0"
  source: task-canonical-baseline.md 拆分
---

# deploy-git-isolated — Task Canonical Baseline（已迁移）

> ⚠️ **注意**：原 monolithic `task-canonical-baseline.md`（1600+ 行）已于 2026-07-03 拆分为 `baseline/` 目录下的 9 个专题文件，以便维护和新 Agent 快速定位。

## 新位置

**完整规范基线请访问**：[`baseline/baseline-index.md`](baseline/baseline-index.md)

### 导航速查

| 文件 | 职责 |
|------|------|
| [baseline/baseline-index.md](baseline/baseline-index.md) | 总入口：顶层原则速查 + 8 文件导航表 |
| [baseline/baseline-principles.md](baseline/baseline-principles.md) | Agent 执行哲学与工程化铁律（0.x） |
| [baseline/baseline-semantics.md](baseline/baseline-semantics.md) | Task/Skill/Workflow 语义定义（1.x） |
| [baseline/baseline-structure.md](baseline/baseline-structure.md) | 目录结构与文件位置约定（2.x + 6.x） |
| [baseline/baseline-formats.md](baseline/baseline-formats.md) | 文件格式规范（3.x） |
| [baseline/baseline-operations.md](baseline/baseline-operations.md) | 修订联动、执行路径、版本演进（4.x + 5.x + 7.x） |
| [baseline/baseline-plugin-architecture.md](baseline/baseline-plugin-architecture.md) | 插件化架构与三层模型（8.1-8.5 + 8.8 plugin） |
| [baseline/baseline-workflow-deploy.md](baseline/baseline-workflow-deploy.md) | JS 工具链、全链条部署、三侧冲突仲裁（8.6-8.8 workflow/JS） |
| [baseline/baseline-audit-truth.md](baseline/baseline-audit-truth.md) | 审计机制、真源治理、决策集中化（8.2 + 8.9-8.10） |


## 保留本文件的原因

- 防止已有链接断裂（`ENTRY.json`、`gotchas/`、`env-migrations/` 等可能引用此路径）
- 作为历史兼容性入口，指引人类和 Agent 前往新位置

**请勿在本文件中追加新内容**。所有新增规范请写入 `baseline/` 下的对应专题文件。
