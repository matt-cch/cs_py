---
title: 跨规则层联动——当单向声明无法闭环时，用全局审计卡点兜底
description: 提炼从"mdc-skill 双向声明"到"三层闭环"演进中的可复用认知模式。核心洞察：任何两个层级的配套关系，如果其中一个层级对 Agent 不可见，必须在第三个独立层级设置不可绕过的检查点。
date: 2026-08-06
type: learning
category: pattern
confidence: high
evidence_count: 2
fingerprint:
  content_sha256: "learning-cross-rule-layer-audit-pattern-20260806"
  semantic_key: "cross-rule-layer-audit-pattern"
meta: {}
---

# 跨规则层联动——当单向声明无法闭环时，用全局审计卡点兜底

## 核心洞察

任何两个层级的配套关系（如 mdc ↔ skill），如果其中一个层级的信息对 Agent 不可见（如 skill 不在 available_skills 列表中），仅靠双向声明无法形成闭环。

**必须在第三个独立层级（也是 Agent 可见的层级）设置不可绕过的检查点。**

## 模式定义

```
层级 A（可见）          层级 B（不可见）
    ↓                        ↓
  mdc（alwaysApply）      skill（不在 available_skills）
    ↓                        ↓
 声明"我有配套 skill B"   声明"我有配套 mdc A"
    ↘                      ↙
      单向声明 → 只能生效一半
```

**解决方案**：引入层级 C（全局审计，alwaysApply），对层级 A 的声明进行强制验证：

```
层级 C（全局审计，alwaysApply）
    ↓
【审计清单】
- 层级 A 是否有配套层级 B？    是/否 → 若是：<B 的名称>
- 层级 B 是否已加载/已获取？    是/否 → 若是：确认路径；若否：停止并 fallback
```

## 适用场景

| 场景 | 层级 A | 层级 B | 层级 C（全局审计） |
|------|--------|--------|-------------------|
| rg-fd-search | mdc（rg-fd-search-priority） | skill（rg-fd-search） | tool-shell-audit.mdc |
| 工具登记 | 脚本新增/更新 | 索引登记（ENTRY.json / verified-task-index） | tool-registration-revision-linkage.mdc |
| 文档写入 | write/edit 操作 | lint 验证 | strictly-forbid-manual-lint-bypass.mdc |

## 关键条件

层级 C 要成为有效卡点，必须满足：
1. **独立性**：不是层级 A 或 B 的子集，不依赖 A/B 的加载状态
2. **不可绕过性**：alwaysApply 或每次操作前强制触发
3. **可验证性**：审计输出中的"是"必须附带具体操作对象，不能只是"是"

## 反模式

1. **只在不可见层级改声明**：改 SKILL.md 但 skill 没被加载 = 无效
2. **只在可见层级加自检**：mdc 的自检 Agent 可能跳过
3. **以为"双向"就等于"闭环"**：缺少第三层验证，闭环是幻觉
4. **"是"时不写操作对象**：无法验证是否真执行了

## 与单向声明不足的关联

本模式是对 gotcha `gotcha-2026-08-06-unilateral-declaration-insufficient.md` 的系统性解答：
- gotcha 指出"改 SKILL.md 没用"
- 本模式给出通用解法："用第三个可见层级做全局审计"

## 证据

- evidence #1：rg-fd-search mdc-skill 配对断裂（2026-08-06），最终通过 tool-audit.mdc 全局审计修复
- evidence #2：同一 session 中 Agent 两次踩同一坑（先声称 skill 不存在，后 fallback 到 glob/grep），证明没有全局卡点时双向声明不足

## 复用建议

未来遇到"A 已加载但 B 未加载"的问题时：
1. 不要只改 B 的声明
2. 不要只在 A 的自检中加检查项
3. **找一个 already-alwaysApply 的 C，在 C 中追加不可绕过的检查**
