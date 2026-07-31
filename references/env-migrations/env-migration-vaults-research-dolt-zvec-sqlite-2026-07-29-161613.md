---
title: vaults 知识库补充：Dolt/zvec/SQLite 调研与组合对比
description: 在本 session 中，基于对 Dolt 2.0、Alibaba zvec、SQLite+FTS5+sqlite-vec 三种技术方案的调研，在 vault-demo 下新增了 Dolt 用法指南和三方案对比分析报告。
date: 2026-07-29
meta: {}
---

# env-migration：vaults 知识库补充调研

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | vault-demo 知识库补充：Dolt / zvec / SQLite 调研对比 |
| **日期** | 2026-07-29 |
| **文件名时间戳** | 2026-07-29-161613 |
| **触发原因** | 用户询问 Dolt 与 zvec、SQLite+sqlite-vec 在 repo 管理场景下的差异，驱动深入调研 |
| **影响范围** | `vaults/vault-demo/wiki/` 下的知识资产（learnings + researches），不涉及代码/配置/工具链变更 |
| **风险等级** | 极低（纯知识沉淀，不影响任何可执行环境） |

## 文本文件变更清单

### 1. 新建 `wiki/learnings/dolt-version-controlled-sql-database-guide.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/learnings/dolt-version-controlled-sql-database-guide.md` |
| **变更类型** | 新建 |
| **内容** | Dolt 2.0 综合指南，含安装方式（Win/Linux/macOS/Docker/源码）、依赖冲突注意事项、CLI/SQL 双模式用法、Prolly Tree 原理、本地版本管理价值分析 |
| **数据来源** | GitHub Release 页面 + 剪藏文章 + 官方文档交叉验证 |
| **验证方式** | `run-lint.py` 检测通过 |

### 2. 新建 `wiki/researches/data-versioning-search-tools-comparison.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/researches/data-versioning-search-tools-comparison.md` |
| **变更类型** | 新建 |
| **内容** | Dolt / zvec / SQLite+FTS5+sqlite-vec 三方案的系统比较，含架构对比、5 维度能力对比矩阵、场景匹配矩阵、各方案短板与风险、选型建议 |
| **验证方式** | `run-lint.py` 检测通过 |

### 3. 修改导航表（两处）

| 文件 | 变更 |
|------|------|
| `vaults/vault-demo/wiki/learnings/README.md` | 新增文件导航表，登记 Dolt 指南条目 |
| `vaults/vault-demo/wiki/researches/README.md` | 新增文件导航表，登记三方案对比条目 |

## 关键结论

> 三方案不是竞争关系，而是解决不同维度的问题：
>
> - **Dolt** — 数据版本管理（分支/合并/审计/时间旅行），搜索是结构性短板
> - **zvec** — 一站式嵌入式搜索引擎（FTS + 向量 + 混合搜索），适合知识库/Agent 记忆
> - **SQLite + FTS5 + sqlite-vec** — SQLite 生态内扩展搜索，灵活性最高但需手动组装

## 验证

- 新文件 lint 已通过
- 导航表已更新

## 回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 删除新文件 | `Remove-Item vaults/vault-demo/wiki/learnings/dolt-version-controlled-sql-database-guide.md, vaults/vault-demo/wiki/researches/data-versioning-search-tools-comparison.md` |
| 恢复导航表 | 从 `learnings/README.md` 和 `researches/README.md` 删除对应导航行 |

## 文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-29-161613 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户调研 Dolt/zvec/SQLite 技术对比 |
| **下次修订条件** | 有新的对比维度补充，或某方案发版重大更新 |

*文档生成时间：2026-07-29*
