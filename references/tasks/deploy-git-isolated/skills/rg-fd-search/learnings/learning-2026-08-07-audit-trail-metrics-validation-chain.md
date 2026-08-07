---
title: audit-trail.jsonl → metrics.json → evolution 有效性检验的完整数据链路
description: 从 SEAS 落地实践中提炼的数据链路模式：原始审计轨迹（jsonl）经聚合生成可读指标（json），再支撑 SED 有效性检验标准，形成闭环
date: 2026-08-07
type: learning
category: pattern
confidence: high
evidence_count: 1
meta:
  version: "1.0.0"
  tags: [seas, audit, metrics, data-chain, evolution-validation]
fingerprint:
  content_sha256: learning-audit-trail-metrics-validation-chain-20260807
  semantic_key: audit-trail-metrics-validation-chain
---

# audit-trail.jsonl → metrics.json → evolution 有效性检验的完整数据链路

## 结论

抽象的 evolution 有效性检验标准（"被引用 >= 3 次"、"同一问题是否复现"）可以通过以下数据链路落地：

```
audit-trail.jsonl（原始轨迹，逐行追加）
    ↓ 聚合脚本读取
metrics.json（聚合视图，收敛时生成）
    ↓ 人工/Agent 读取
evolution 有效性检验（标准判定）
    ↓ 反馈
SKILL.md 收敛决策（是否将 evolution 合并回主文档）
```

## 各节点职责

| 节点 | 格式 | 职责 | 更新频率 |
|------|------|------|---------|
| `audit-trail.jsonl` | JSON Lines | 记录每次 skill 执行的完整结构化数据 | 每次 skill 执行后追加 |
| `metrics.json` | JSON | 从 jsonl 聚合出的可读指标（命中率、合规率、异常率等） | 收敛时生成 |
| 有效性检验 | 逻辑判定 | 对比 metrics.json 中的指标与阈值（如 >= 3 次） | 收敛时执行 |

## 数据流转示例

**场景**：验证 `evolution-2026-08-07-search-scope-extension-to-vaults` 是否有效

1. **原始轨迹**：在 `audit-trail.jsonl` 中搜索 `sed.sed_files_created` 包含该 evolution 路径的记录
2. **聚合视图**：`metrics.json` 中 `evolution_effectiveness.search-scope-extension.executions_since_applied = 3`
3. **标准判定**：3 >= 3 → 通过短期检验
4. **决策**：该 evolution 可纳入 SKILL.md 收敛候选

## 查询方式

```powershell
# 查询特定 evolution 被引用次数
& "${devroot}\venv\ripgrep\rg.exe" -c "evolution-2026-08-07-search-scope-extension-to-vaults" "${devroot}\references\tasks\deploy-git-isolated\skills\rg-fd-search\versions\audit-trail.jsonl"

# 查询所有包含异常记录的行
& "${devroot}\venv\ripgrep\rg.exe" -n '"exceptions":\s*\[' "${devroot}\references\tasks\deploy-git-isolated\skills\rg-fd-search\versions\audit-trail.jsonl"
```

## 适用边界

- **适用**：需要量化验证 skill 规则/流程/补丁有效性的场景
- **不适用**：纯定性认知（如设计理念、偏好声明）——这些应走 learning/baseline，无需 metrics 支撑

## 证据

- SEAS baseline 创建过程（2026-08-07）中，通过检查 `versions/` 目录确认此前无任何 audit/metrics 落地，从而触发本数据链路设计。

## 关联

- 依据 baseline：`baseline/baseline-skill-audit-schema.md` §5 聚合查询方式
- 依据 baseline：`baseline/baseline-sed-mechanism.md` §4 有效性检验
