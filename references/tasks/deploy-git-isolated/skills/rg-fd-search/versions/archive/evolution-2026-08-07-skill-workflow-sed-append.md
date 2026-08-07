---
title: SKILL.md 工作流扩展 — 追加 baseline 创建和 audit-trail 追加流程
description: 将 SED 自检触发器和 SEAS 审计记录追加流程纳入 SKILL.md 标准工作流，使 Agent 每次执行 skill 后自动完成自检和审计落盘
date: 2026-08-07
type: evolution
scope: add
category: workflow
target_section: "## 工作流"
meta:
  version: "1.0.0"
  tags: [workflow, sed, seas, skill]
fingerprint:
  content_sha256: evolution-skill-workflow-sed-append-20260807
  semantic_key: skill-workflow-sed-append
---

# SKILL.md 工作流扩展 — 追加 baseline 创建和 audit-trail 追加流程

## 背景

当前 SKILL.md 的"## 工作流"节定义了 P0-P3 搜索流程，但未包含以下两个关键步骤：

1. **SED 自检触发器**：skill 执行完毕后是否执行了新认知检测？
2. **SEAS 审计记录**：是否将本次执行的结构化审计数据追加到 `audit-trail.jsonl`？

这两个步骤在本次 session（2026-08-07）中被实际执行，但 SKILL.md 未声明，导致后续 Agent 重置后可能遗漏。

## 变更内容

### 1. 工作流末尾追加 Step 7：SED 自检触发器

在现有工作流（P0-P3 搜索 → 输出解析 → 磁盘验证 → 上下文补查 → 洞察建议）之后，追加：

```
Step 7: SED 自检触发器（强制）
  执行【新认知检测】3 维度 9 项自检清单
    ↓
  若命中 ≥ 1 项：
    - 在"下一步建议"末尾追加 SED 建议话术
    - 等待 Human 决策："记一下" / "不用" / "先放放"
  若未命中：
    - 正常结束，不追加 SED 建议
```

### 2. 工作流末尾追加 Step 8：SEAS 审计记录

在 Step 7 之后、"下一步建议"输出之前，追加：

```
Step 8: SEAS 审计记录（强制）
  在内存中构造符合 SEAS schema 的 JSON 对象
    ↓
  追加到 versions/audit-trail.jsonl（只增不改）
    ↓
  输出审计确认块：
    【Skill 执行审计记录】
    - 记录时间: <timestamp>
    - 审计轨迹: versions/audit-trail.jsonl（已追加）
    - 本次执行: P0命中=是/否, P1命中=是/否, ...
    - 合规状态: audit_block=✓/✗, skill_loaded=✓/✗, native_fallback=✓/✗
    - SED 事件: self_check=✓/✗, suggested=✓/✗, human_decision=<decision>
    - 异常: <count> 个
```

### 3. 工作流图示更新

原工作流：
```
Step 1-6: P0-P3 搜索 → 验证 → 补查 → 洞察建议
    ↓
输出"下一步建议"
```

新工作流：
```
Step 1-6: P0-P3 搜索 → 验证 → 补查 → 洞察建议
    ↓
Step 7: SED 自检触发器（强制）
    ↓
Step 8: SEAS 审计记录（强制）
    ↓
输出"下一步建议"（含 SED 建议，若自检命中）
```

## 影响范围

- SKILL.md "## 工作流"节末尾追加 Step 7/8
- 不影响现有 P0-P6 搜索逻辑，保持向后兼容
- 新增步骤为强制审计层，不可跳过

## 验收标准

下次 rg-fd-search skill 执行时：
1. 必须输出 SED 自检结果
2. 必须输出 SEAS 审计确认块
3. `audit-trail.jsonl` 必须新增一行记录

## 关联

- 依据 baseline：`baseline/baseline-sed-mechanism.md` §2.3 智能触发方案
- 依据 baseline：`baseline/baseline-skill-audit-schema.md` §4 记录时机与操作方式
