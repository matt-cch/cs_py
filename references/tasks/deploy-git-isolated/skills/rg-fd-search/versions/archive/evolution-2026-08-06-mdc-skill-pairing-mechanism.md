---
title: 建立 mdc-skill 配套关联机制——规则层与执行层配对铁律
description: 为 rg-fd-search skill 新增配套关联机制章节，强制要求 mdc 与 skill 双向显式声明，自检清单增加 skill 加载检查项，建立"规则触发 → skill 加载"的不可绕过闭环
date: 2026-08-06
type: evolution
scope: add
category: behavior
target_section: "## 配套 skill 关联机制（新增章节）"
meta:
  version: "1.1.0"
fingerprint:
  content_sha256: "evolution-mdc-skill-pairing-mechanism-20260806"
  semantic_key: "rg-fd-search-mdc-skill-pairing"
---

# 建立 mdc-skill 配套关联机制——规则层与执行层配对铁律

## 背景

2026-08-06 实战 session 中，用户要求"查看 gh 工作进度"。Agent 的 mdc（`rg-fd-search-priority.mdc`，alwaysApply: true）已自动触发，Agent 也按规则使用 `rg/fd` 执行了搜索并输出结果。

但 Agent 声称"没有任何 skill 命中"，完全没有调用 `skill` 工具加载 `rg-fd-search`，导致 SKILL.md 中的 SED 加载机制、标准调用模板、组合示例、Self-Evolution 复盘等能力全部丢失。

核心缺陷：规则层（mdc）与执行层（skill）之间**没有不可绕过的关联机制**，Agent 读 mdc 时不知道有配套 skill，搜索行为与 skill 定义一致但完全错过了 skill 上下文。

## 变更内容

### 1. 新增 SKILL.md 章节"配套 skill 关联机制"

在 SKILL.md 中新增独立章节，定义以下铁律：

#### 铁律 1：mdc 必须显式声明配套 skill

任何 alwaysApply 的 mdc 如果存在配套 skill，必须在以下位置同时声明：

- **frontmatter**：
  ```yaml
  meta:
    paired_skill: "skill-name"
    paired_skill_path: "references/tasks/.../skills/skill-name/SKILL.md"
  ```

- **正文顶部**：
  > **配套 Skill（必须加载）**：本 mdc 有强配套 skill **`<skill-name>`**。Agent 在执行本 mdc 规定的任务前，**必须先通过 `skill` 工具加载 name=`<skill-name>`**。

#### 铁律 2：skill 必须声明配套 mdc

skill 的 SKILL.md 必须在以下位置声明配套 mdc：

- **正文顶部**：
  > **配套规则**：`.cursor/rules/<mdc-name>.mdc`（alwaysApply，自动生效）。
  > **铁律**：mdc 规则与 skill 执行手册必须同时生效。禁止只遵守 mdc 而遗漏 skill 加载。

#### 铁律 3：自检清单必须包含"配套 skill 加载"检查项

mdc 的自检清单（如【rg/fd 搜索优先级审计】）必须追加：

```
- 配套 skill <skill-name> 是否已加载？      是/否 → 若否，立即停止当前路径，先加载 skill
```

Agent 工具调用审计（`high-frequency-tool-shell-audit.mdc`）必须追加：

```
- 当前 mdc 是否有配套 skill？              是/否 → <skill-name>
- 配套 skill 是否已加载？                  是/否
```

#### 铁律 4：高频任务速查表必须登记 skill

`high-frequency-task-index.mdc` 和 `high-frequency-task-show-trigger.mdc` 必须包含本 skill 条目，确保新 session 首次交互时用户和 Agent 都能看到。

条目格式：

```
| # | **rg/fd 搜索** | 搜索、查找、列出文件... | `搜一下 <关键词>` | `rg-fd-search-priority.mdc` + `rg-fd-search` skill |
```

#### 铁律 5：EXEC-CHEATSHEET 命令示例前必须增加 skill 加载提示

所有涉及本 skill 的命令示例前，必须增加不可跳过的前置步骤声明：

> **前置步骤（不可跳过）**：执行前，**必须先加载配套 skill**：`skill` 工具 → name=`<skill-name>`。

### 2. 定义"规则层-执行层配对断裂"诊断模式

当 Agent 在搜索场景中出现以下症状时，即判定为"配对断裂"：

| 症状 | 判定标准 |
|------|---------|
| mdc 已触发但 skill 未加载 | Agent 输出了 mdc 自检清单，但清单中没有"配套 skill 加载"项，或该项为"否" |
| Agent 声称"没有 skill 命中" | 实际上配套 skill 存在于磁盘，但 Agent 因系统提示列表不完整而未发现 |
| 搜索行为与 skill 定义一致 | Agent 使用了 rg/fd，符合 skill 定义，但没加载 skill 获取模板和上下文 |
| 输出结果缺少 SED 能力 | 报告没有使用 skill 中的标准模板、没有执行 Self-Evolution 复盘 |

### 3. 定义 skill 发现机制（不依赖系统提示列表）

Agent 不得仅依赖系统提示的 `<available_skills>` 列表判断 skill 是否存在。正确做法：

```powershell
# 扫描磁盘上的所有 skill 目录
& "${devroot}\venv\fd\fd.exe" -g "SKILL.md" "${devroot}" | Sort-Object

# 或查询 verified-task-index.json
& "${devroot}\venv\ripgrep\rg.exe" -n '"type":\s*"skill"' "${devroot}\references\runtime\verified-task-index.json"
```

### 4. 定义修正触发条件

当用户或 Agent 发现以下任一情况时，触发本次 evolution 的修正流程：

1. 搜索任务执行后，Agent 未输出"配套 skill 已加载"确认
2. 用户追问"为什么没有加载 skill"
3. 系统提示的 skill 列表与磁盘实际不一致

## 影响范围

- SKILL.md 新增"## 配套 skill 关联机制"章节
- 所有配套 mdc（`rg-fd-search-priority.mdc`）同步更新 frontmatter + 正文 + 自检清单
- `high-frequency-task-index.mdc` 总览表新增 rg-fd-search 条目
- `high-frequency-task-show-trigger.mdc` 速查卡新增 rg-fd-search 条目
- `scripts/EXEC-CHEATSHEET.md` rg/fd 节前增加 skill 加载提示
- `verified-trigger-index.json` 中 rg-fd-search 冲突域的 resolution_notes 同步更新

## 与现有规则的衔接

- 新增机制中涉及 bash 调用时，仍需遵守 `high-frequency-shell-guard-content.mdc`
- 新增文件写入后，需遵守 `strictly-forbid-manual-lint-bypass.mdc`，走 `run-lint.py --fix`
- 新增 skill 条目登记需遵守 `tool-registration-revision-linkage.mdc`

## 验收标准

下次搜索类任务执行时，Agent 必须输出：
1. mdc 自检清单（含"配套 skill 加载"检查项）
2. skill 加载确认（"已加载 rg-fd-search skill"）
3. 搜索执行（使用 rg/fd，遵循 P0-P3）
4. 执行后 Self-Evolution 复盘（新认知检测 → 入库判断）

若任一环节缺失，即视为配对断裂，需立即修正。
