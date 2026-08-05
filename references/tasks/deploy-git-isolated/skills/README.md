---
title: deploy-git-isolated/skills — Skill 目录索引
description: deploy-git-isolated 任务下的 Skill 规范文件存放地。每个 skill 一个子目录，含 SKILL.md + 可选 README.md。
date: 2026-08-05
meta:
  version: 1.0.0
---

# skills/

本目录存放 deploy-git-isolated 任务的 **Skill 规范文件**。每个 skill 独占一个子目录，子目录名即 skill 名。

## 子目录 / 文件导航

| 目录 | 用途 | 触发词 |
|------|------|--------|
| [docstring-quality-harness/](docstring-quality-harness/) | 通过委派 subagent 检验工具 docstring 自说明质量 | docstring 质量、检验注释 |
| [rg-fd-search/](rg-fd-search/) | 通用搜索能力封装（rg + fd），强制搜索优先次序 | 搜索、查找、列出文件、grep、glob |
| [tool-discovery/](tool-discovery/) | 工具发现与用法查询（deploy-git-isolated 内部） | 找工具、查用法、怎么调用 |

## Skill 命名规范

- 子目录名：kebab-case（如 `rg-fd-search`）
- 主文件：`SKILL.md`（必须）
- 自说明：`README.md`（可选，推荐）

## 上级导航

- [deploy-git-isolated 根](../README.md)
- [ENTRY.json](../ENTRY.json) — task 机器可读真源
