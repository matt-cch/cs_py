---
title: mdc-skill 配套关联机制升级——从双向声明到三层闭环
description: 基于 gotcha "单向声明不足"的实战教训，将配套关联机制从"mdc↔skill 双向显式声明"升级为"mdc 声明 + skill 声明 + 全局审计卡点"三层不可绕过闭环。同步修订自检清单"是"时必须展示操作对象的规范。
date: 2026-08-06
type: evolution
scope: append
category: rule
target_section: "## 配套 skill 关联机制（新增章节）"
fingerprint:
  content_sha256: "evolution-mdc-skill-triple-loop-20260806"
  semantic_key: "rg-fd-search-mdc-skill-triple-loop"
meta: {}
---

# mdc-skill 配套关联机制升级——从双向声明到三层闭环

## 背景

evolution v1.2.0 建立了 mdc-skill 双向显式声明机制（铁律 1-5），但在实战中暴露致命缺陷：

- mdc 是 alwaysApply，自动加载 → mdc 中的声明对 Agent 可见
- skill 不在系统提示 `<available_skills>` 列表中 → Agent 不会加载 skill → skill 中的声明对 Agent 不可见
- 结果：双向声明实际只有单向生效

用户明确指出："改 SKILL.md 有鬼用啊，都没有触发"

本次 evolution 将机制从"双向声明"升级为"三层闭环"，增加跨规则层全局审计卡点，确保无论 skill 是否可被 `skill` 工具加载，Agent 都会被拦截并执行 fallback。

## 变更内容

### 铁律 1-5 保持有效（evolution v1.2.0）

- 铁律 1：mdc 必须显式声明配套 skill（frontmatter + 正文顶部）
- 铁律 2：skill 必须声明配套 mdc
- 铁律 3：mdc 自检清单必须包含"配套 skill 加载"检查项
- 铁律 4：高频任务速查表必须登记 skill
- 铁律 5：EXEC-CHEATSHEET 命令示例前必须增加 skill 加载提示

### 新增铁律 6：全局审计卡点必须兜底

任何存在配套 skill 的 mdc，其配套 skill 的加载状态必须在**另一个 alwaysApply mdc** 中接受审计。

具体实施：

```
high-frequency-tool-shell-audit.mdc（alwaysApply）
    ↓
【Tool 调用规则层审计】
    ...
    - 当前 mdc 是否有配套 skill？    是/否 → 若是：<skill-name>
    - 配套 skill 是否已加载？        是/否 → 若是：确认 skill 路径 <path>；若否：立即停止当前路径，先加载 skill
```

**为什么选 tool-audit.mdc**：
- 它是 alwaysApply，每次调用 bash/write/edit 前强制触发
- 它独立于任何具体业务 mdc，不会被业务逻辑绕过
- 它已经在做"高频任务命中检查"，追加"配套 skill 检查"是职责内扩展

### 新增铁律 7："是"时必须展示操作对象

所有自检清单中"是/否"类检查项，当答案为"是"时，必须明确写出：

| 检查项 | 合格示例 | 不合格示例 |
|--------|---------|-----------|
| 命中高频任务 mdc | `是 → high-frequency-verify-runtime.mdc` | `是` |
| 涉及 Shell 执行 | `是 → 叠加执行 high-frequency-shell-guard-content.mdc 审计` | `是` |
| 有配套 skill | `是 → rg-fd-search` | `是` |
| skill 已加载 | `是 → 确认 skill 路径 references/tasks/.../rg-fd-search/SKILL.md` | `是` |

**目的**：防止 Agent 写"是"但实际未执行，使审计块可被用户验证。

### 新增铁律 8：skill 加载失败时必须 fallback 到磁盘 read

当 `skill` 工具返回"not found"时，Agent 不得放弃，必须执行 fallback：

```powershell
# Step 1: 扫描磁盘确认 skill 存在性
& "${devroot}\venv\fd\fd.exe" -g "SKILL.md" "${devroot}\references\tasks\deploy-git-isolated\skills"

# Step 2: 直接 read SKILL.md 获取上下文
# 路径从 mdc frontmatter 的 paired_skill_path 获取
```

**fallback 优先级**：
1. `skill` 工具加载（标准路径）
2. `read` 工具读取磁盘 SKILL.md（fallback 路径）
3. 放弃获取 skill 上下文（禁止）

## 影响范围

- `high-frequency-tool-shell-audit.mdc`：追加配套 skill 检查项 + 流程图升级
- `rg-fd-search-priority.mdc`：自检清单"是"时必须展示操作对象（已在本 session 修正）
- 所有含"是/否"检查项的 mdc：逐步按铁律 7 规范

## 与现有规则的衔接

- evolution v1.2.0 的铁律 1-5 继续有效，本 evolution 是追加而非替换
- `high-frequency-tool-shell-audit.mdc` 也是 alwaysApply，与 rg-fd-search-priority.mdc 互补
- 新增铁律 8 涉及 bash 调用时，仍需遵守 `high-frequency-shell-guard-content.mdc`

## 验收标准

下次搜索类任务执行时，Agent 必须输出：
1. tool-audit 审计块（含"配套 skill 检查"项，且"是"时展示操作对象）
2. mdc 自检清单（含"配套 skill 加载"项）
3. skill 加载确认 或 fallback 到磁盘 read 的确认
4. 搜索执行（使用 rg/fd，遵循 P0-P3）

若缺少 1 或 3，即视为"单向声明不足"复发，需立即修正。
