---
title: rg-fd-search Skill — Baseline 层索引
description: 审计基准、Human/Agent 共同理解、工程偏好的沉淀目录。供 Agent 重置后快速对齐行为约束。
date: 2026-08-07
meta:
  version: "1.0.0"
  tags: [baseline, audit, convention, hitl]
---

# baseline/

> **职责**：沉淀本 skill 的审计基准约定、Human/Agent 共同理解、Human 的工程偏好。
> Baseline 文件是行为约束的"最低水位线"，Agent 执行搜索任务前必须通读本节相关条目。

## 子目录 / 文件导航

| 文件 | 类型 | 用途 |
|------|------|------|
| [baseline-no-hardcode-paths.md](baseline-no-hardcode-paths.md) | 审计基准 | 路径引用不硬编码原则：多端多根对齐 + HITL fallback |
| [baseline-sed-mechanism.md](baseline-sed-mechanism.md) | 审计基准 | SED（Self-Evolution Directory）机制运行规范：目标、触发策略、实现路径、有效性检验、智能自检方案 |
| [baseline-skill-audit-schema.md](baseline-skill-audit-schema.md) | 审计基准 | SEAS 落地方案：执行审计 schema、JSON Lines 载体、记录时机、聚合查询方式 |
| [baseline-skill-change-revision-linkage.md](baseline-skill-change-revision-linkage.md) | 审计基准 | Skill 变更与演进修订联动义务清单：五级联动自检（Level 1-5）+ 审计块模板 + 反面教材 |

## 使用方式

1. **Agent 重置后速查**：阅读本目录下的 baseline 文件，快速对齐当前 skill 的行为约束。
2. **任务执行前自检**：涉及路径引用、范围扩展等操作时，对照相应 baseline 逐项确认。
3. **Human 纠偏依据**：当 Agent 行为偏离 Human 偏好时，将纠偏结论沉淀为新的 baseline 文件。

## 上级导航

- [rg-fd-search Skill 根目录](../README.md)
- [skills 总索引](../../README.md)
