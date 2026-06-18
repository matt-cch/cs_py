---
title: Profile 筛选模式 — 稳定执行框架 + 配置元数据黑白名单
description: 从 github-lib 插件架构演进中沉淀的设计模式：通过 Profile/Include/Exclude 三层筛选 + 依赖自动补齐，解决"全量加载冗余插件"问题。date: 2026-06-17
---

# Profile 筛选模式

> **来源**：deploy-git-isolated task 的 github-lib.ps1 插件架构演进。
> **问题**：插件目录膨胀后，入口脚本对所有调用者一视同仁加载全部插件，造成冗余导入。
> **解法**：Profile / Include / Exclude 三层筛选 + 依赖自动补齐。


## 1. 问题场景

| 调用者 | 实际需求 | 旧行为（全量加载） | 浪费 |
|--------|---------|-------------------|------|
| `github-step-01-init.ps1` | core/constants/encoding/env-config/git-checks | 加载全部 6 个 | 多加载 github-api |
| `github-sync-issue.ps1` | 需要全部 6 个（含 github-api） | 加载全部 6 个 | 无浪费，但不可控 |
| 未来新增脚本 | 仅需 core/constants | 加载全部 6 个 | 浪费 4 个 |

**核心矛盾**：入口脚本是稳定框架（不应频繁修改），但不同调用者的需求差异越来越大。

## 2. 设计原则

| 原则 | 说明 |
|------|------|
| **框架不动** | 入口脚本（github-lib.ps1）的排序/加载逻辑永不动，只通过 JSON 配置驱动 |
| **配置真源** | 筛选规则集中在 `lib-sort-rules.json`，不散落在各调用脚本中 |
| **显式依赖** | 插件间的 depends 必须在 JSON 中明文声明，禁止隐式依赖 |
| **自动补齐** | 筛选后的插件列表若缺少依赖，算法自动递归拉入，不依赖人工维护完整闭合集 |
| **向后兼容** | 无参数时等价于 `_default`（加载全部），旧脚本零改动 |

## 3. 三层筛选优先级

```
命令行 -Include/-Exclude  →  最高优先级，显式覆盖一切
        ↓
-Profile "xxx"              →  中优先级，从 JSON profiles 节读取
        ↓
_default / 无参数           →  向后兼容，加载全部
```

## 4. 语义铁律

| include | exclude | 结果 |
|---------|---------|------|
| `[]` | `[]` | **all**（向后兼容） |
| `["a","b"]` | `[]` | 只加载 a,b **+ 自动补齐它们的依赖** |
| `[]` | `["c"]` | all **except** c |
| `["a","b"]` | `["b"]` | 只加载 a（b 被显式排除，即使它在 include 里） |

## 5. 依赖自动补齐（核心机制）

```
Profile "deploy" 包含 env-config
    env-config depends on constants
        constants 不在 deploy 的 include 中
        → 自动递归拉入 constants
```

## 6. 生效验证日志（必须输出）

```
[github-lib] Profile: issue-sync
[github-lib] 全图插件: 6 个
[github-lib] 筛选后加载顺序:
  1. constants (constants.ps1)
  2. core (core.ps1)
  3. encoding (encoding.ps1)
  4. env-config (env-config.ps1) [auto-dep]
  5. git-checks (git-checks.ps1)
  6. github-api (github-api.ps1)
[github-lib] 实际加载: 6 个（过滤前 6 个）
```

## 7. 复用条件

本模式适用于以下场景：
- 插件/模块目录持续膨胀
- 不同入口脚本对插件的需求差异明显
- 需要保持入口脚本稳定，通过配置驱动行为变化
- 插件间存在显式依赖关系

## 8. 关联文件

- 实现：`scripts/github-lib.ps1`
- 配置真源：`scripts/lib-sort-rules.json`
- 架构文档：`docs/PLUGIN-ARCHITECTURE.md`


*模式版本: v1.0*  
*沉淀时间: 2026-06-17*  
*验证状态: 已通过 issue-sync/deploy/_default/exclude-override 四场景验证*
