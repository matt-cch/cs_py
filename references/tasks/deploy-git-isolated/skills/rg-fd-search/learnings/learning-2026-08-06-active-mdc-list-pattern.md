---
title: 生效 mdc 列表——解决 alwaysApply mdc 的"不可见性"问题
description: 提炼从 subagent 验证中发现的可复用认知模式。核心洞察：alwaysApply mdc 对 Agent 是"被动生效"的，Agent 需要主动列出当前生效的 mdc 列表，才能发现被遗漏的配套 skill。本模式从 rg-fd-search 验证中提炼，可复用于任何多 mdc 并存场景。
date: 2026-08-06
type: learning
category: pattern
confidence: high
evidence_count: 1
fingerprint:
  content_sha256: "learning-active-mdc-list-pattern-20260806"
  semantic_key: "active-mdc-list-pattern"
meta: {}
---

# 生效 mdc 列表——解决 alwaysApply mdc 的"不可见性"问题

## 核心洞察

alwaysApply mdc（如 rg-fd-search-priority.mdc、tool-shell-audit.mdc）对 Agent 是**被动加载**的——Agent 不需要主动读取，系统会自动注入。但这也导致一个问题：**Agent 不知道自己被哪些 mdc 约束着**。

在 subagent 验证任务中，如果没有"当前已触发的生效 mdc 有哪些"这个检查项，Agent 只输出：
```
当前 mdc 是否有配套 skill？  否
```

因为它只检查了 tool-audit.mdc（自己），没有检查 rg-fd-search-priority.mdc（另一个 alwaysApply mdc）。

加入生效 mdc 列表项后，Agent 输出：
```
当前已触发的生效 mdc 有哪些？
  rg-fd-search-priority.mdc（alwaysApply=true，搜索场景命中）
  high-frequency-tool-shell-audit.mdc（alwaysApply=true）
  high-frequency-shell-guard-content.mdc（涉及 bash 时隐性命中）
```

然后才意识到 rg-fd-search-priority.mdc 有配套 skill。

## 模式定义

```
Agent 收到 prompt
    ↓
【tool-audit】自检
    ↓
旧逻辑（单层自检）：
    - 当前 mdc 是否有配套 skill？ → 只检查 tool-audit 自己 → 可能遗漏

新逻辑（列表自检）：
    - 当前已触发的生效 mdc 有哪些？ → 列出全部 alwaysApply mdc
    - 对每个生效 mdc 检查：是否有配套 skill？
    → 不遗漏
```

## 适用场景

| 场景 | 生效 mdc 数量 | 风险 | 列表自检价值 |
|------|-------------|------|-----------|
| 纯文本问答 | 1（tool-audit） | 低 | 低 |
| 搜索/查找任务 | 2+（tool-audit + rg-fd-search-priority） | 中 | 高 |
| Shell 脚本任务 | 3+（tool-audit + shell-guard + rg-fd-search-priority） | 高 | 高 |
| 文件写入任务 | 2+（tool-audit + shell-guard + markdown-format） | 中 | 高 |

## 关键条件

生效 mdc 列表要成为有效工具，必须满足：
1. **必须显式列出名称**：不能只写"有 3 个 mdc 生效"，必须写出每个 mdc 的具体名称
2. **必须标注 alwaysApply 状态**：让 Agent 意识到这些 mdc 是强制生效的，不是自己可选的
3. **必须逐一检查配套 skill**：列出生效 mdc 后，对每个 mdc 检查是否有配套 skill

## 反模式

1. **只检查"当前 mdc"**：Agent 把"当前 mdc"理解为自己正在输出的这个 audit block 所在的 mdc，遗漏其他 alwaysApply mdc
2. **列出不检查**：列出生效 mdc 列表后，不再检查每个 mdc 的配套 skill
3. **用触发词替代列表**：Agent 凭记忆判断"这个 prompt 像不像搜索"，而不是列出所有生效 mdc 后逐一核对

## 证据

- evidence #1：subagent 验证任务（2026-08-06），加入生效 mdc 列表项后，成功识别 rg-fd-search-priority.mdc 并触发 skill 检查

## 复用建议

未来遇到"Agent 遗漏 alwaysApply mdc"的问题时：
1. 不要在单个 mdc 的自检清单中增加"检查其他 mdc"项
2. **在全局审计 mdc（tool-audit.mdc）中增加"生效 mdc 列表"项**，强制 Agent 在每次 tool 调用前扫描全部 alwaysApply mdc
3. 列表输出后，要求 Agent 对每个生效 mdc 执行配套 skill 检查
