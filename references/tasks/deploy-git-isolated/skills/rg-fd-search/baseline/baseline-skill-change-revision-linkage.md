---
title: 审计基准 — Skill 变更与演进修订联动义务清单
description: 定义 skill 发生任何变更（新增/更新/收敛/归档）后，必须执行的修订联动义务。防止导航断裂、脉络丢失、索引失效。
date: 2026-08-07
meta:
  version: "1.0.0"
  tags: [baseline, revision-linkage, skill-change, checklist, navigation]
---

# Skill 变更与演进修订联动义务清单

## 一句话铁律

**任何 skill 变更（新增 evolution/learning/gotcha/baseline、收敛 SKILL.md、版本升级、目录结构变更）交付前，必须完成"五级联动自检"，缺一不可。**

## 五级联动自检清单

### Level 1 — Skill 内部导航（必须）

| # | 联动文件 | 触发条件 | 更新内容 | 本次遗漏示例 |
|---|---------|---------|---------|-------------|
| 1.1 | `SKILL.md` | 任何 evolution 内容需合并回基准 | 按 target_section 合并补丁 | — |
| 1.2 | `README.md` | 目录结构变化（新增/删除子目录） | 导航表追加/删除/修改条目 | ✅ 最初遗漏：evolutions/ 描述未更新"已收敛"状态 |
| 1.3 | `evolutions/README.md` | 新增/收敛/归档 evolution | 演进脉络追加新版本记录 | ✅ **最初遗漏：停在 v1.4.0，未记录 v1.5.x 和 v2.0.0** |
| 1.4 | `baseline/README.md` | 新增/删除 baseline 文件 | 导航表追加/删除条目 | — |
| 1.5 | `versions/manifest.json` | 任何 SED 文件变更或收敛 | 指纹索引、evolution_history、convergence_history | — |

> **核心教训**：`evolutions/README.md` 不是可选装饰文件，而是**演进脉络真源**。Agent 重置后阅读此文件即可了解 skill 完整历史。遗漏更新会导致历史断裂。

### Level 2 — 父级索引（必须检查）

| # | 联动文件 | 触发条件 | 更新内容 |
|---|---------|---------|---------|
| 2.1 | `skills/README.md`（父目录索引） | skill 职责/触发词/名称变更 | 导航表中 skill 描述或触发词更新 |
| 2.2 | `verified-task-index.json`（全局索引） | skill 路径/入口命令/描述变更 | `available_scripts_and_tools` 中对应条目更新 |

> **检查方式**：`rg -n "skill-name" skills/README.md` + `rg -n "skill-name" verified-task-index.json`

### Level 3 — 配套规则层（必须检查）

| # | 联动文件 | 触发条件 | 更新内容 |
|---|---------|---------|---------|
| 3.1 | `.cursor/rules/*.mdc`（配套 mdc） | skill 核心能力/路径/配套关系变更 | mdc frontmatter 的 `paired_skill_path`、正文配套声明 |
| 3.2 | `EXEC-CHEATSHEET.md`（命令速查） | skill 新增标准命令或变更调用方式 | 对应分类节追加/更新命令示例 |
| 3.3 | `high-frequency-task-index.mdc` / `high-frequency-task-show-trigger.mdc` | skill 触发词变更 | 速查表中触发词或描述更新 |

> **核心教训**：skill 与配套 mdc 是**共生关系**。skill 变更后，mdc 中的配套声明、速查表中的描述可能已过时，必须交叉验证。

### Level 4 — 审计轨迹（必须）

| # | 联动文件 | 触发条件 | 更新内容 |
|---|---------|---------|---------|
| 4.1 | `versions/audit-trail.jsonl` | 任何 skill 执行（包括收敛操作本身） | 追加一行结构化审计记录 |
| 4.2 | `versions/metrics.json`（可选，定期） | audit-trail 积累 >= 10 条或收敛时 | 由聚合脚本生成可读指标视图 |

> **规则**：`audit-trail.jsonl` 为只增不改文件。即使本次变更是"收敛"而非"搜索"，也必须追加审计记录（intent_category: skill_maintenance）。

### Level 5 — 归档与备份（收敛时强制）

| # | 操作 | 触发条件 | 执行内容 |
|---|------|---------|---------|
| 5.1 | 归档 SKILL.md | 收敛前 | `Copy-Item SKILL.md versions/archive/SKILL-vX.Y.Z-YYYYMMDD-convergence-backup.md` |
| 5.2 | 归档 evolution 文件 | 收敛后 | `Move-Item evolutions/evolution-*.md versions/archive/` |
| 5.3 | 保留空目录标记 | evolutions/ 清空后 | 放置 `.gitkeep` 确保目录不被 git 忽略 |

## 自检执行流程（交付前不可跳过）

```
Step 1: 变更完成后，按 Level 1-5 逐项检查
    ↓
Step 2: 对每一项，自问："本次变更是否影响该文件？"
    ├── 是 → 执行更新
    └── 否 → 在审计块中标注 "N/A"
    ↓
Step 3: 输出【Skill 变更修订联动审计块】
    ↓
Step 4: run-lint.py 验证全部修改后的文件
    ↓
Step 5: 交付
```

## 审计块模板（必须输出）

```
【Skill 变更修订联动审计】
变更类型：<新增 evolution / 收敛 / 目录变更 / 其他>

Level 1 — Skill 内部导航:
- [ ] SKILL.md 已更新（如适用）
- [ ] README.md 导航表已同步
- [ ] evolutions/README.md 演进脉络已追加
- [ ] baseline/README.md 导航表已同步
- [ ] manifest.json 已更新（指纹/历史/收敛记录）

Level 2 — 父级索引:
- [ ] skills/README.md 已检查（N/A / 已更新）
- [ ] verified-task-index.json 已检查（N/A / 已更新）

Level 3 — 配套规则层:
- [ ] 配套 mdc 已检查（N/A / 已更新）
- [ ] EXEC-CHEATSHEET.md 已检查（N/A / 已更新）
- [ ] 高频任务速查表已检查（N/A / 已更新）

Level 4 — 审计轨迹:
- [ ] audit-trail.jsonl 已追加本次执行记录

Level 5 — 归档与备份（收敛时）:
- [ ] SKILL.md 已归档到 versions/archive/
- [ ] 已收敛 evolution 已移入 versions/archive/
- [ ] evolutions/ 已放置 .gitkeep

遗漏项：<如有，列出并说明补救计划>
```

## 反面教材：本次 session 的遗漏

| 遗漏项 | 影响 | 发现方式 | 补救 |
|--------|------|---------|------|
| `evolutions/README.md` 停在 v1.4.0 | 新 Agent 阅读时误认为 skill 未升级 | 用户主动指出 | 追加 v1.5.0~v2.0.0 全部记录 |
| `rg-fd-search/README.md` evolutions/ 描述过时 | 描述暗示"有活跃补丁"，实际已清空 | 用户主动指出 | 更新为"当前已收敛至 v2.0.0，活跃补丁待积累" |

## 与现有规则的衔接

- `.cursor/rules/tool-registration-revision-linkage.mdc`：定义 task 级别工具的登记五件套，skill 变更时同样适用（ENTRY.json / TASK-TOOLS-INDEX.md 等）
- `.cursor/rules/markdown-docs-format.mdc`：所有 README.md 更新须遵循 frontmatter + 导航联动规则
- `baseline/baseline-sed-mechanism.md`：SED 自检触发器执行后，应将"修订联动是否完成"纳入维度 2（规则/行为变更）的检查项

## Human 偏好声明

> **用户明确确认（2026-08-07）**：skill 变更后的修订联动义务必须规范化，避免遗漏。特别是 `evolutions/README.md` 演进脉络和 `README.md` 导航描述，常被 Agent 忽略，必须纳入强制自检清单。

## 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-08-07 | 初始创建：五级联动自检清单（Level 1-5）、审计块模板、反面教材、与现有规则衔接 |
