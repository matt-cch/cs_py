---
title: baseline/ 层不仅限于审计基准，可用于沉淀机制规范
description: 从 rg-fd-search skill 的实践中发现，baseline/ 层可承载 SED 机制运行规范、SEAS 审计 schema 等机制性内容，超出"审计基准"的原始定义
date: 2026-08-07
type: learning
category: insight
confidence: high
evidence_count: 2
meta:
  version: "1.0.0"
  tags: [baseline, skill-architecture, mechanism, sed]
fingerprint:
  content_sha256: learning-baseline-layer-mechanism-scope-20260807
  semantic_key: baseline-layer-mechanism-scope
---

# baseline/ 层不仅限于审计基准，可用于沉淀机制规范

## 现象

rg-fd-search skill 的 `baseline/` 目录最初定位为"审计基准约定、Human/Agent 共同理解、工程偏好"。

但在本次 session（2026-08-07）中，`baseline/` 下实际沉淀了：

| 文件 | 内容性质 | 原始定位是否覆盖 |
|------|---------|----------------|
| `baseline-no-hardcode-paths.md` | 审计基准（路径引用原则） | ✅ 是 |
| `baseline-sed-mechanism.md` | **机制规范**（SED 运行目标、触发策略、实现路径、收敛流程） | ❌ 否 |
| `baseline-skill-audit-schema.md` | **机制规范**（SEAS schema 定义、记录时机、聚合查询） | ❌ 否 |

## 洞察

**baseline/ 层的实际承载能力超出了"审计基准"的字面定义。**

当 skill 的 SED 机制本身需要规范化文档时（如定义 evolutions 如何创建、如何收敛、如何检验有效性），这些文档天然适合放在 `baseline/` 下，因为：

1. **行为约束层级**：它们定义了"skill 自身如何演进"的最低水位线
2. **Agent 重置后速查**：新 Agent 需要快速理解 skill 的演进规则
3. **Human 纠偏依据**：当 Agent 未执行 SED 自检时，Human 可引用 baseline 进行纠偏

## 模式提炼

```
baseline/ 层职责扩展 = 原始审计基准 + 机制运行规范

原始定位：
  - 审计基准约定（如路径不硬编码）
  - Human/Agent 共同理解
  - 工程偏好

扩展后定位：
  + 机制运行规范（如 SED 如何触发、如何收敛）
  + 数据 schema 定义（如 SEAS 审计记录结构）
  + 流程约束（如每次 skill 执行后必须做什么）
```

## 适用边界

- **适用**：skill 的元机制（自身如何运行、如何演进、如何审计）需要文档化时
- **不适用**：具体业务规则的变更（应走 evolution）；具体踩坑记录（应走 gotcha）；具体认知洞察（应走 learning）

## 证据

| 证据 | 来源 |
|------|------|
| baseline-sed-mechanism.md 被创建并验证有效 | 本次 session 2026-08-07 |
| baseline-skill-audit-schema.md 被创建并验证有效 | 本次 session 2026-08-07 |
| Human 主动提出"有必要增加 skill/baseline/" | 用户 feedback 2026-08-07 |

## 关联

- 触发源：`baseline/baseline-sed-mechanism.md` 的创建过程
- 对应的 gotcha：`gotcha-skill-sed-frontmatter-missing.md`
