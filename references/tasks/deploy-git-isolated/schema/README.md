---
title: schema 目录索引
description: deploy-git-isolated schema 子目录分类导航。按格式与职责分层，避免长期堆根。
date: 2026-06-20
meta: {}
---

# schema 目录说明

本目录存放 **Plugin Result Schema** 统一契约的全部真源与实现。
按**格式 + 职责**分层，禁止长期堆在一级根下。


## 子目录导航

| 子目录 | 用途 | 典型文件 |
|--------|------|---------|
| `json/` | JSON Schema 机器真源（draft-07），供验证器/IDE/生成器消费 | `plugin-result-schema.json` |
| `docs/` | 人类可读规范文档（Markdown），含字段说明、示例、升级指南 | `plugin-result-schema.md` |
| `py/` | Python 代码实现（Pydantic / Dataclass 降级），与 JSON Schema 共享同一契约 | `models.py` |


## 文件清单

| 文件 | 路径 | 说明 |
|------|------|------|
| JSON Schema 真源 | `json/plugin-result-schema.json` | 机器验证、IDE 提示、文档生成 |
| Lint 规则全局清单 | `json/lint-rules-manifest.json` | 全部 lint/验证规则清单，供 audit 巡检对照 |
| Lint 规则清单说明 | `docs/lint-rules-manifest.md` | 清单结构、规则 ID 命名约定、联动义务 |
| 规范文档 | `docs/plugin-result-schema.md` | 人类阅读、开发参考 |
| Commit Message 格式模板 | `docs/commit-message-format.md` | Issue 评论中 commit 记录的标准格式（元数据 + 上下文摘要） |
| 安全审计规范 | `docs/security-audit-spec.md` | 部署前敏感内容巡检流程、检测规则、严重等级定义 |
| Pydantic Model | `py/models.py` | 备选强类型实现（默认 Dict，可选 Pydantic） |
| 安全审计 Schema | `json/security-audit-schema.json` | 审计报告数据结构契约（AuditReport / PhaseResult / Finding） |


## 新增 schema 规则

1. **先判断格式**：JSON Schema → 放 `json/`；Markdown → 放 `docs/`；代码实现 → 放 `<lang>/`
2. **登记 README**：新增文件后在本页导航表中追加条目
3. **联动 ENTRY.json**：`references/runtime/verified-task-index.json` 或本 task 的 `ENTRY.json` 需同步更新路径


## 上级导航

- [父目录 ../README.md](../README.md)
- [TASK-TOOLS-INDEX.md](../TASK-TOOLS-INDEX.md)
