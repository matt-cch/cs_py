---
title: Commit Message / Issue Comment 格式模板
description: 定义 deploy-git-isolated 全链条发布时，Issue 评论中 commit 记录的标准格式。融合 06-18 元数据风格与上下文摘要结构，供 workflow 与手工提交统一使用。
date: 2026-06-22
meta:
  version: "1.0.0"
  format_type: "issue-comment-template"
  based_on: "2026-06-18 issue-comment format v2"
---

# Commit Message / Issue Comment 格式模板

> **适用范围**：`deploy-git-isolated` 全链条 workflow（Step 9 Issue Sync）及手工追加评论。
>
> **设计原则**：一条评论 = 一次提交的完整上下文摘要，读者无需跳转到 GitHub 即可理解本次变更的来龙去脉。

***

## 格式总览

```markdown
## 变更记录 — {timestamp}

**Commit**: `{short_hash}`
**Branch**: `{branch}`
**Author**: `{author}`
**Date**: `{iso_datetime}`

### Goal

{一句话概括本次提交的目标}

### Progress

| 状态 | 内容 |
|******|******|
| ✅ Done | {已完成事项} |
| 🚧 In Progress | {进行中事项} |
| ⏸️ Blocked | {阻塞事项及原因} |

### Key Decisions

| # | 决策 | 理由 |
|***|******|******|
| 1 | {决策描述} | {为什么这样选} |

### Next Steps

- [ ] {下一步行动}
- [ ] {再下一步}

### Critical Context

- {任何需要后续 session 接续的关键上下文}
- {踩坑记录、路径变更、版本锁定等}

### Relevant Files

| 文件 | 路径 | 说明 |
|******|******|******|
| {文件名} | `{相对路径}` | {变更内容简述} |

***

> 模板版本: v1.0.0 | 生成工具: {workflow_name}/{version}
```

***

## 字段规范

| 变量 | 类型 | 必填 | 说明 | 示例 |
|******|******|******|******|******|
| `{timestamp}` | string | ✅ | 人类可读时间戳，精确到秒 | `2026-06-22 14:30:00` |
| `{short_hash}` | string | ✅ | Git short hash（7 位） | `a1b2c3d` |
| `{branch}` | string | ✅ | 当前分支名 | `task/deploy-git-isolated` |
| `{author}` | string | ✅ | 提交者身份（来自 `.env` GIT_USER_NAME） | `matt-cch` |
| `{iso_datetime}` | string | ✅ | ISO 8601 格式 UTC 时间 | `2026-06-22T14:30:00Z` |
| `{workflow_name}` | string | ❌ | 生成该评论的 workflow 名称 | `workflow-deploy-full` |
| `{version}` | string | ❌ | workflow 版本号 | `v1.1.2` |

***

## 适用场景

| 场景 | 使用格式 | 说明 |
|******|*********|******|
| **全自动 workflow** | 完整模板 | Step 9 调用时自动生成全部字段 |
| **半自动（Agent 辅助）** | 完整模板 | Agent 读取上下文后填充 Goal/Progress/Key Decisions |
| **手工追加评论** | 精简版（可选） | 仅保留 **Commit / Branch / Date + 一句话说明** |

***

## 历史格式参考

| 版本 | 时间 | 特点 | 状态 |
|******|******|******|******|
| v1 | 2026-06-17 | `## 变更记录 — {timestamp}` + Markdown 表格（Commit/Branch/Message/Date） | ❌ 已废弃 |
| v2 | 2026-06-18 | `## 变更记录 — {timestamp}` + 键值对（**Commit**: `hash`） | ⚠️ 基础元数据 |
| v3 | 2026-06-20 | `commit {hash}: {message} [{branch}]` | ⚠️ 极简单行 |
| **v4 (本模板)** | 2026-06-22 | 基础元数据 + 上下文摘要（Goal/Progress/Key Decisions/Next Steps/Critical Context/Relevant Files） | ✅ 当前标准 |

***

## 与 workflow 的衔接

`workflow-deploy-full.py` Step 9 调用 `step-09-github-sync-issue.py` 时：

1. 默认读取本模板生成完整格式评论
2. 若 `--body` 参数被显式传入，则覆盖模板（供手工场景）
3. 模板中 `{author}` 从 `.env` 的 `GIT_USER_NAME` 读取
4. `{workflow_name}` 和 `{version}` 从 `workflow-deploy-full.py` 的模块级常量注入

***

## 示例

### 示例 1：全自动 workflow 输出

```markdown
## 变更记录 — 2026-06-22 14:30:00

**Commit**: `a1b2c3d`
**Branch**: `task/deploy-git-isolated`
**Author**: `matt-cch`
**Date**: `2026-06-22T14:30:00Z`

### Goal

将运行时版本记录更新流程从 5 个独立 PowerShell 脚本迁移为统一的 Python Workflow。

### Progress

| 状态 | 内容 |
|******|******|
| ✅ Done | 实现 `runtime_version.py` 版本检测插件（5 种模式） |
| ✅ Done | 实现 `update-version.py` Workflow CLI（自动发现→实测→对比→更新） |
| ✅ Done | 更新 `high-frequency-update-version.mdc` 为 Python CLI 优先 |
| ✅ Done | 修订联动 4 个 task 文档 |
| ⏸️ Blocked | 无 |

### Key Decisions

| # | 决策 | 理由 |
|***|******|******|
| 1 | `runtime_version.py` 优先用纯 Python `ctypes` 读取 PE VersionInfo | 避免外部依赖，跨平台一致 |
| 2 | `update-version.py` 通过扫描 `venv/version/*.md` 自动发现工具列表 | 与 `tools_config.json` 解耦，事实来源驱动 |

### Next Steps

- [ ] 将本模板集成到 `step-09-github-sync-issue.py`
- [ ] 在 `workflow-deploy-full.py` 中注入模板变量

### Critical Context

- `_resolve_devroot()` 原实现从 `__file__` 向上探测时曾错误返回空路径，已修复为检查 `(parent / "references" / "tasks").exists()` 特征
- `process_runner.run_simple()` 的 `label` 参数输出到 `sys.stderr`，在 bash 工具中显示为乱码，不影响功能

### Relevant Files

| 文件 | 路径 | 说明 |
|******|******|******|
| runtime_version.py | `scripts/py-plugins/runtime_version.py` | 版本检测插件 |
| update-version.py | `scripts/py-tools/update-version.py` | Workflow CLI |
| high-frequency-update-version.mdc | `.cursor/rules/high-frequency-update-version.mdc` | 高频任务速查 |

***

> 模板版本: v1.0.0 | 生成工具: workflow-deploy-full/v1.1.2
```

***

## 上级导航

- [schema 目录索引](../README.md)
- [TASK-TOOLS-INDEX.md](../../TASK-TOOLS-INDEX.md)
