---
title: Agent 遗忘 task-canonical-baseline.md 踩坑记录
description: Agent 在长对话中遗忘了本 task 已定义的规范基线文件，导致重复推理和语义混淆。
date: 2026-06-16
---

# Agent 遗忘 task-canonical-baseline.md 踩坑记录

## 现象

在长对话（10+ 轮交互）中，Agent 与用户共同协商、批准并定义了以下概念实体：

- `task-canonical-baseline.md` — 本 task 的认知基线与真源契约
- `TASK-TOOLS-INDEX.md` — 工具索引（与 SOP-CHEATSHEET 的语义区分）
- Trigger 治理六维意图（治理、参照、边界、协调、审计、重建）

但在后续讨论中，Agent **完全遗忘了这些已定义实体的存在**，表现为：

1. 用户问「sop-cheatsheet 和 task 可用工具速查表是不是同一个东西」时，Agent 先是承认「是」，随后自行否定，暴露出对 `task-canonical-baseline.md` 中已定义语义的无知。
2. 用户提示「D:\pjt\cursor\cs_py\schema\task-template\task-canonical-baseline.md」时，Agent 才「记起来」。
3. 用户明确说「我刚才说了半天，你都想不起来这个文件的意图和作用」，Agent 才意识到需要补救。

## 根因分析

### 1. 上下文窗口碎片化

Agent 的上下文窗口在 10+ 轮交互后，早期定义的概念实体被后续操作细节淹没。`task-canonical-baseline.md` 虽然被定义过，但没有在每次后续操作前被 **显式引用**，导致 Agent 的注意力完全转移到执行层面。

### 2. 缺乏强制自检机制

`task-canonical-baseline.md` 定义了「Agent 执行路径」：
```
1. 读取 ENTRY.json
2. 读取 TASK-TOOLS-INDEX.md
3. 读取 SOP-CHEATSHEET.md
4. 执行命令
```

但在实际对话中，Agent 没有执行这个自检流程，而是直接从记忆中推断，导致记忆偏差。

### 3. 文件未被纳入「每次必查」清单

`task-canonical-baseline.md` 虽然被定义，但没有被写入 `ENTRY.json` 的强制读取清单，也没有在 `README.md` 的文件导航中被赋予最高优先级（直到本次补救才追加）。

## 修复方式

### 立即修复

1. **生成 `task-canonical-baseline.md`**：把协商过的语义定义、命名约定、修订联动规则写入本 task 根目录。
2. **修订联动**：
   - `README.md` 文件导航表追加 `task-canonical-baseline.md` 条目
   - `ENTRY.json` 登记 `task-canonical-baseline.md` 路径

### 机制修复

1. **每次进入 task 时的强制读取清单**：Agent 在操作本 task 前，必须按顺序读取：
   - `README.md`（总览）
   - `task-canonical-baseline.md`（规范基线）
   - `ENTRY.json`（机器真源）
   - 然后才是 `TASK-TOOLS-INDEX.md` / `SOP-CHEATSHEET.md`

2. **在 `task-canonical-baseline.md` 顶部增加自我引用提醒**：
   > **Agent 自检提示**：如果你在对话中遗忘了本文件的存在，说明上下文窗口已碎片化。请立即停止推理，重新读取本文件。

3. **在 `README.md` 顶部增加醒目提示**：
   > **Agent 注意**：本 task 有已定义的规范基线 `task-canonical-baseline.md`，操作前必读。

## 反模式

- ❌ 「我记得之前定义过什么东西」→ 凭记忆推断，不重新读取文件
- ❌ 「用户提示了什么我才想起什么」→ 被动回忆，缺乏主动自检
- ❌ 把 `task-canonical-baseline.md` 当作可选文档 → 它是本 task 的认知契约，不是补充说明

## 关联文件

- `task-canonical-baseline.md` — 被遗忘了的文件本身
- `README.md` — 应在顶部提示本文件存在
- `ENTRY.json` — 应登记本文件路径
- `DESIGN.md` 第 7 章 — 踩坑记录的权威汇总


*记录时间: 2026-06-16*  
*教训等级: 高（导致语义混淆和重复劳动）*  
*避免方式: 每次进入 task 先读 task-canonical-baseline.md*
