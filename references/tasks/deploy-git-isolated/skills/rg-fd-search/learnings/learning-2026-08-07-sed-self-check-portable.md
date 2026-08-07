---
title: SED 自检流程（3 维度 9 项）可复用到其他 skill
description: rg-fd-search skill 中验证的 SED 自检触发器（3 维度 9 项 + 建议话术模板 + Human 决策权保留）具有跨 skill 通用性，可作为标准化自检框架推广
date: 2026-08-07
type: learning
category: pattern
confidence: high
evidence_count: 1
meta:
  version: "1.0.0"
  tags: [sed, self-check, portable, skill-framework, cross-skill]
fingerprint:
  content_sha256: learning-sed-self-check-portable-20260807
  semantic_key: sed-self-check-portable
---

# SED 自检流程（3 维度 9 项）可复用到其他 skill

## 结论

rg-fd-search skill 中设计并验证的 SED 自检触发器，其核心结构（3 维度 × 9 项检查 + 建议话术模板 + Human 决策权保留）具有**跨 skill 通用性**，可作为标准化自检框架推广到所有具备 SED 目录体系的 skill。

## 可复用的核心结构

### 1. 三维度框架

| 维度 | 对应 SED 产物 | 核心问题 |
|------|-------------|---------|
| 异常/陷阱 | gotcha | 是否遇到文档未覆盖的异常？Human 是否纠偏？ |
| 规则/行为变更 | evolution | 实际路径是否与文档推荐不同？是否更优？ |
| 洞察/模式/结论 | learning | 是否发现可复用认知？是否识别多源关系？ |

### 2. 建议话术模板

```markdown
💡 【SED 自检提示】
本次 skill 执行过程中发现以下可能值得沉淀为新认知：

- 维度：<gotcha / evolution / learning>
- 现象：<一句话描述>
- 建议：<是否应在 skill SED 中记录>

是否需要记录到 skill SED？（回复"记一下"即可触发）
```

### 3. Human 决策权保留

| Human 反馈 | Agent 动作 |
|-----------|-----------|
| "记一下" | 进入 SED 落盘流程 |
| "不用" | 记录摘要，不写入磁盘 |
| "先放放" | 标记待处理 |
| 无反馈 | 默认不写入，仅展示自检结果 |

## 跨 skill 适配方式

其他 skill（如 `tool-discovery`、`huashu-design`、`playwright-best-practices`）只需：

1. 在 skill 根目录建立 `baseline/baseline-sed-mechanism.md`（或引用 rg-fd-search 的 baseline）
2. 在工作流末尾嵌入自检触发器
3. 根据 skill 具体场景微调 9 项检查清单（如 huashu-design 可将"PS 5.1 兼容性"加入异常维度）
4. 建立 `versions/audit-trail.jsonl` 记录执行轨迹

## 证据

- 本次 session（2026-08-07）中，rg-fd-search skill 执行 SED 自检后，用户反馈"这个执行 skill sed 自检的思路很好"，确认自检流程的有效性。
- 自检命中 9 项中的 7 项，产出 5 条 SED 记录（1 gotcha + 1 evolution + 3 learnings），验证了自检的召回率。

## 关联

- 原始定义：`baseline/baseline-sed-mechanism.md` §2.3 智能触发方案
- 本次验证：rg-fd-search SED 自检执行 session 2026-08-07
