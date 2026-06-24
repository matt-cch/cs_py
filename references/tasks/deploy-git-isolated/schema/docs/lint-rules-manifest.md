---
title: Lint Rules Manifest 说明
description: lint-rules-manifest.json 的结构说明、规则 ID 命名约定、联动义务
date: 2026-06-24
meta: {}
---

# Lint Rules Manifest 说明

**文件**：`schema/json/lint-rules-manifest.json`
**版本**：1.0.0
**用途**：deploy-git-isolated task 全部 lint/验证规则的全局清单，供 audit 巡检时对照核查。

## 结构

| 顶层字段 | 说明 |
|---------|------|
| `meta` | 清单自身元信息（版本、更新时间、来源文件） |
| `profiles` | py-sort-rules.json 中所有 profile 定义 |
| `plugins` | 按插件归类：每个插件的所有规则 |
| `routing` | 文件扩展名 → 插件路由表 |
| `fix_capabilities` | 可自动修复的操作清单 |
| `cross_references` | 上下游文档引用 |
| `summary` | 总数统计 |

## 规则 ID 命名约定

| 前缀 | 插件 | 示例 |
|------|------|------|
| `LINT-ENC-` | lint_encoding | LINT-ENC-005 |
| `MD-LINT-` | md_lint | MD-LINT-003 |
| `LINK-CHK-` | link_checker | LINK-CHK-001 |
| `LINT-JSON-` | lint_json | LINT-JSON-001 |
| `LINT-PY-` | lint_python | LINT-PY-001 |
| `LINT-PS1-` | lint_ps1 | LINT-PS1-001 |
| `SEC-AUDIT-` | security_audit | SEC-AUDIT-001 |

## 联动义务

- 新增 lint 规则时：**必须**同步更新 `lint-rules-manifest.json`，新增对应 `rules[]` 条目。
- 修改已有规则（严重等级、可修复性等）：同步更新对应字段。
- 删除规则：从 manifest 中移除对应条目。
- 变更后执行：`run-lint.py --files <manifest路径>` 验证 JSON 语法。
