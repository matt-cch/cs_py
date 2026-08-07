---
title: 树状文档与磁盘实际之间存在结构性认知 Gap
description: 进度查询类搜索任务中，Agent 常将树状文档的静态声明误认为实时真源。通过 2026-08-06 实战 session 发现文档层+日志层+磁盘层的双源交叉验证模式可系统性修正该认知偏差
date: 2026-08-06
type: learning
category: insight
confidence: high
evidence_count: 1
meta:
  version: "1.1.0"
fingerprint:
  content_sha256: "learning-tree-docs-vs-disk-reality-gap-20260806"
  semantic_key: "rg-fd-search-docs-reality-gap"
---

# 树状文档与磁盘实际之间存在结构性认知 Gap

## 现象

当用户问"某任务/某场景的工作进度到哪里了"时，Agent 的本能反应是搜索 README.md、TASK-TOOLS-INDEX.md、ENTRY.json 等树状文档，读取其中的"状态"字段（如 ready / pending），然后直接报告给用户。

但树状文档中的状态是**静态声明**，不是**实时真源**。它存在以下系统性偏差：

1. **滞后性**：文档更新频率远低于代码变更频率。一个脚本昨天已新建，但文档可能今天才更新，甚至永远没更新。
2. **遗漏性**：env-migration 中声称新建了 5 个文件，实际磁盘只有 3 个。文档不会自动告诉你"少了 2 个"。
3. **掩盖性**：文档说"全部 ready"，但 missing 的文件恰恰是工作进度的关键缺口。

## 根因

Agent 把"文档怎么说"当成了"事实是什么"。这是**以文档为真源**的认知误区。正确的认知是：

> **文档是真源的声明，不是真源本身。磁盘上的实际存在性才是真源。**

## 修复模式

对于"进度/状态查询"类搜索任务，必须执行**双源交叉验证**：

```
源 A（文档层）：README / TASK-TOOLS-INDEX / ENTRY.json / SOP / GOAL
源 B（日志层）：env-migration / handoff（时间线脉络）
源 C（磁盘层）：Test-Path / fd / rg（实际存在性验证）

→ 交叉对比，发现矛盾（文档说有但磁盘没有、日志说待办但文档说 ready）
→ 矛盾本身就是进度的一部分（缺口 = 下一步工作）
→ 输出方向建议
```

## 实战案例

2026-08-06 "gh 场景工作进度"搜索：

- **源 A（文档）**：TASK-TOOLS-INDEX.md 说 atomic-gh-pr-merge.py ready，env-migration 说新建了 5 个脚本
- **源 B（日志）**：8月3日 env-migration 记录了 atomic-git-sync-main.py 和 workflow-git-pr-poly.py 的设计文档
- **源 C（磁盘）**：Test-Path 验证发现这 2 个文件 MISSING
- **洞察**：这不是"疏忽"，而是搜索任务应该自然发现的结论——"文档声称有但实际缺失 = 工作进度存在缺口"
- **方向建议**：补齐 MISSING 文件 或 确认是否需要删除文档中的声明

## 适用边界

- **适用**："进度查询"、"状态检查"、"工作到哪里了"、"完成了吗"
- **不适用**：纯文件查找（"列出所有 .py"）、纯内容搜索（"搜一下某关键词"）——这些场景不需要磁盘验证层

## 关联 gotcha

- `gotchas/tree-docs-stale-vs-disk-missing.md`（如已存在）
