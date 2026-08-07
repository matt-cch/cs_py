---
title: 规则层 alwaysApply mdc 与配套 skill 的配对机制——从断裂到闭环的认知模式
description: 基于 2026-08-06 rg-fd-search 配对断裂实例，提炼出"规则层-执行层配对"的可复用认知模式，定义配对建立、配对检测、配对修复的完整方法论
date: 2026-08-06
type: learning
category: pattern
confidence: high
evidence_count: 1
meta:
  version: "1.1.0"
  related_evolution: "evolutions/evolution-2026-08-06-mdc-skill-pairing-mechanism.md"
  related_gotcha: "gotchas/gotcha-2026-08-06-mdc-skill-pair-disconnect.md"
fingerprint:
  content_sha256: "learning-rule-skill-pairing-pattern-20260806"
  semantic_key: "mdc-skill-pairing-pattern"
---

# 规则层 alwaysApply mdc 与配套 skill 的配对机制——从断裂到闭环的认知模式

## 现象

项目中存在一种常见的架构模式：

- **规则层**：`.cursor/rules/*.mdc`（alwaysApply: true），负责定义禁令、审计清单、触发条件
- **执行层**：`*/skills/*/SKILL.md`，负责提供标准调用模板、工作流、参数速查、Self-Evolution 复盘

二者本应是**强配对关系**：mdc 触发 → skill 加载 → 协同执行。但在实战中，这种配对极易断裂。

2026-08-06 的 rg-fd-search 实例是典型断裂案例：
- mdc `rg-fd-search-priority.mdc` 已触发（alwaysApply）
- Agent 按规则用 rg/fd 执行了搜索
- 但配套 skill `rg-fd-search` 完全没有被加载
- 结果：SED 加载机制、标准模板、Self-Evolution 复盘全部丢失

## 根因：三层认知盲区

### 盲区 1：系统提示的 skill 列表 ≠ 磁盘实际 skill

Agent 默认只扫描系统提示中的 `<available_skills>` 列表。该列表通常只包含 `.agents/skills/` 和 `.opencode/skills/` 下的 skill，**不包含** task 本地 skill（如 `references/tasks/deploy-git-isolated/skills/rg-fd-search/`）。

**认知误区**："系统提示没显示这个 skill → 这个 skill 不存在 → 没有 skill 命中"

**正确认知**："系统提示的列表只是子集，磁盘上可能还有更多 skill。搜索任务前应主动扫描 `*/skills/` 目录。"

### 盲区 2：mdc 中无配套 skill 声明 → Agent 无法建立关联

如果 mdc 中没有显式声明"配套 skill 为 X"，Agent 读 mdc 时只知道规则内容，但不知道还有配套 skill 需要加载。

**认知误区**："我在按 mdc 规则执行 = 我已经正确执行了"

**正确认知**："mdc 是规则层，skill 是执行层。规则遵守了 ≠ 执行完整了。执行层可能包含 mdc 没有覆盖的模板、上下文、复盘机制。"

### 盲区 3：自检清单缺少"skill 加载"项 → 无卡点

即使 mdc 中有 skill 声明，如果自检清单中没有"配套 skill 是否已加载"的检查项，Agent 仍可能在无意识中跳过 skill 加载。

**认知误区**："我读了 mdc，我知道有配套 skill，我记住了"

**正确认知**："记住不可靠。只有自检清单中的硬性检查项才是真正的卡点。"

## 可复用模式：规则层-执行层配对闭环

### 模式定义

```
配对建立 → 配对检测 → 配对修复
```

### 步骤 1：配对建立（设计时）

**mdc 侧**：
- frontmatter 增加 `paired_skill` + `paired_skill_path`
- 正文顶部增加"配套 Skill（必须加载）"强制声明
- 自检清单增加"配套 skill 是否已加载"检查项

**skill 侧**：
- 正文顶部增加"配套 mdc"声明
- 明确 skill 与 mdc 的职责边界

**索引侧**：
- `verified-trigger-index.json` 中 mdc 和 skill 登记到同一 `conflict_domain`
- `high-frequency-task-index.mdc` / `high-frequency-task-show-trigger.mdc` 中登记条目

### 步骤 2：配对检测（执行时）

Agent 执行涉及 mdc 的任务时，必须输出以下审计：

```
【规则层-执行层配对审计】
- 当前触发的 mdc：<mdc-name>
- 该 mdc 是否有配套 skill？              是/否 → <skill-name>
- 配套 skill 是否已在系统提示列表中？    是/否
- 若不在列表中 → 是否已扫描磁盘确认？    是/否
- 配套 skill 是否已加载？                是/否
- 加载后是否获取了执行模板？             是/否
- 结论：配对完整 / 配对断裂（需修复）
```

### 步骤 3：配对修复（断裂时）

若审计发现"配对断裂"，立即执行：

1. **停止当前路径**：不继续执行搜索/操作
2. **加载配套 skill**：`skill` 工具 → name=`<skill-name>`
3. **重新执行审计**：确认 skill 已加载且获取了模板
4. **继续原任务**：使用 skill 提供的上下文执行

## 适用边界

- **适用**：所有存在"alwaysApply mdc + 配套 skill"架构的场景
- **不适用**：纯 mdc 无配套 skill、纯 skill 无配套 mdc 的场景
- **典型场景**：rg-fd-search、tool-discovery、docstring-quality-harness 等

## 实战案例

2026-08-06 rg-fd-search 配对断裂：

| 阶段 | 状态 | 问题 |
|------|------|------|
| 配对建立 | ❌ 缺失 | mdc 无 `paired_skill` frontmatter，无配套声明 |
| 配对检测 | ❌ 缺失 | 自检清单无"skill 加载"项，Agent 未主动扫描磁盘 |
| 配对修复 | ❌ 未触发 | Agent 未意识到断裂，直接完成任务 |

修复后：

| 阶段 | 状态 | 措施 |
|------|------|------|
| 配对建立 | ✅ 已补 | mdc 增加 `paired_skill` + 正文声明 + 速查表登记 |
| 配对检测 | ✅ 已补 | 自检清单增加"配套 skill 加载"项 + EXEC-CHEATSHEET 前置提示 |
| 配对修复 | ✅ 已定义 | evolution 中定义了"断裂 → 加载 → 重审"的标准修复路径 |

## 关联文件

- **本次 gotcha**：`gotchas/gotcha-2026-08-06-mdc-skill-pair-disconnect.md`
- **本次 evolution**：`evolutions/evolution-2026-08-06-mdc-skill-pairing-mechanism.md`
- **本 learning**：本文件
