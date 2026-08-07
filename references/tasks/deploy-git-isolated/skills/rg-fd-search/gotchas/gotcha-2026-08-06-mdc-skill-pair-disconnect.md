---
title: mdc 已加载但配套 skill 被遗忘——规则层与执行层配对断裂
description: 搜索场景下 rg-fd-search-priority.mdc（alwaysApply）已自动触发，Agent 也按规则使用了 rg/fd 执行搜索，但完全没意识到应加载配套 skill rg-fd-search，导致 SKILL.md 中的 SED 加载机制、标准调用模板、Self-Evolution 复盘等能力全部丢失
date: 2026-08-06
type: gotcha
meta:
  version: "1.1.0"
fingerprint:
  content_sha256: "gotcha-mdc-skill-pair-disconnect-20260806"
  semantic_key: "mdc-skill-pairing-disconnect"
---

# mdc 已加载但配套 skill 被遗忘——规则层与执行层配对断裂

## 现象

用户问"查看 gh 工作进度"，Agent 的搜索行为如下：

1. **mdc 已触发**：`.cursor/rules/rg-fd-search-priority.mdc`（alwaysApply: true）自动生效，Agent 输出了【rg/fd 搜索优先级审计】
2. **搜索已执行**：Agent 使用 `rg.exe` 和 `fd.exe` 搜索了项目内与 `gh` 相关的文件
3. **skill 被遗忘**：Agent 声称"没有任何 skill 命中"，完全没有调用 `skill` 工具加载 `rg-fd-search`
4. **能力丢失**：SED 加载机制（scripts/ evolutions/ learnings/ gotchas/）、标准调用模板、组合示例、Self-Evolution 复盘自检块全部未加载

用户追问后，Agent 才扫描磁盘发现 `references/tasks/deploy-git-isolated/skills/rg-fd-search/` 确实存在。

## 根因分析

### 根因 1：系统提示的 skill 列表不完整

Agent 默认只扫描系统提示中 `<available_skills>` 列表显示的 skill。该列表只包含 `.agents/skills/` 和 `.opencode/skills/` 下的 skill，**不包含** `references/tasks/deploy-git-isolated/skills/` 下的 skill。

因此 Agent 在判断"是否有 skill 命中"时，根本看不到 `rg-fd-search`。

### 根因 2：mdc 中无配套 skill 显式声明

`rg-fd-search-priority.mdc` 原始版本中：
- 没有 `paired_skill` frontmatter
- 正文中没有"配套 skill 为 rg-fd-search"的声明
- 自检清单中没有"是否已加载配套 skill"的检查项

Agent 读 mdc 时，只知道"要用 rg/fd"，但不知道"还要加载 rg-fd-search skill"。

### 根因 3：Agent 的认知盲区——"我在按规则执行 = 已正确执行"

Agent 的错误推理链：

```
用户问搜索类问题 → mdc 触发 → 我用 rg/fd 搜了 → 输出结果了 → 任务完成
                      ↑
                      └── 缺失环节：skill 加载检查
```

Agent 把"遵守了 mdc 的 rg/fd 规则"误等同于"完整执行了搜索任务"，忽略了 skill 提供的执行手册、模板、复盘机制等关键上下文。

### 根因 4：项目级速查表/索引未登记 rg-fd-search

`high-frequency-task-index.mdc` 和 `high-frequency-task-show-trigger.mdc` 原始版本中均没有 rg-fd-search 条目。Agent 在"高频任务速查"环节无法发现该 skill。

## 修复方式

### 修复 1：mdc 显式声明配套 skill

在 `rg-fd-search-priority.mdc` 中：

1. frontmatter 增加：
   ```yaml
   meta:
     paired_skill: "rg-fd-search"
     paired_skill_path: "references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md"
   ```

2. 正文顶部增加强制声明：
   > **配套 Skill（必须加载）**：本 mdc 有强配套 skill **rg-fd-search**。Agent 在执行任何搜索任务前，**必须先通过 `skill` 工具加载 name=`rg-fd-search`**。

### 修复 2：mdc 自检清单增加"配套 skill 加载"检查项

在【rg/fd 搜索优先级审计】自检清单中追加：

```
- 配套 skill rg-fd-search 是否已加载？    是/否 → 未加载则立即停止，先加载 skill
```

### 修复 3：高频任务速查表/速查卡登记 rg-fd-search

- `high-frequency-task-index.mdc` 总览表新增 #9 rg/fd 搜索
- `high-frequency-task-show-trigger.mdc` 速查卡新增 rg/fd 搜索条目

### 修复 4：EXEC-CHEATSHEET 命令示例前增加 skill 加载提示

在 `scripts/EXEC-CHEATSHEET.md` rg/fd 搜索节前增加：

> **前置步骤（不可跳过）**：执行搜索前，**必须先加载配套 skill**：`skill` 工具 → name=`rg-fd-search`

## 反模式

1. **只扫描系统提示的 skill 列表**：系统提示的 `<available_skills>` 不包含 task 本地 skill，必须主动扫描磁盘 `*/skills/` 目录
2. **mdc 不声明配套 skill**：Agent 无法建立"规则层 ↔ 执行层"的关联
3. **自检清单遗漏 skill 加载项**：即使有声明，没有清单检查 = 仍可能遗漏
4. **Agent 声称"没有 skill 命中"**：实际上 skill 存在且应该命中，但 Agent 没发现

## 验证方式

搜索类任务执行前，Agent 必须自检：

```
【Skill 加载审计】
- 当前任务是否涉及搜索/查找/文件列表？     是/否
- mdc rg-fd-search-priority 是否已触发？     是/否
- 配套 skill rg-fd-search 是否已加载？       是/否 → 若否，立即加载
- 加载后是否获取了标准调用模板？             是/否
- 加载后是否获取了 SED 加载机制？             是/否
```

## 关联规则

- `.cursor/rules/rg-fd-search-priority.mdc` — 搜索优先级规则层
- `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md` — 搜索执行 skill 层
- `.cursor/rules/high-frequency-tool-shell-audit.mdc` — tool 调用前审计

## 来源

2026-08-06 用户要求"查看 gh 工作进度"时触发。Agent 使用 rg/fd 执行搜索但遗漏 skill 加载，被用户追问后才纠正。
