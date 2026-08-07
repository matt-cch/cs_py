---
title: rg-fd-search mdc-skill 配对机制建立 + 运行时版本更新 + 工具登记修订联动
description: 本次 session 完成运行时版本记录更新（5 工具版本变更），发现并修正 rg-fd-search skill 与配套 mdc 的关联断裂问题，建立 mdc-skill 配套关联铁律（5 条），完成项目级登记强化（6 文件）与 SED 自闭环入库（gotcha/evolution/learning/manifest）。
date: 2026-08-06
meta:
  version: "1.0"
---

# env-migration-rg-fd-search-mdc-skill-pairing-and-version-update-2026-08-06-152330

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | rg-fd-search mdc-skill 配对机制建立 + 运行时版本更新 |
| **日期** | 2026-08-06 |
| **文件名时间戳** | 2026-08-06-152330 |
| **触发原因** | 用户要求"更新运行时版本信息"，随后追问 gh 工作进度，进而暴露 mdc-skill 关联断裂问题 |
| **影响范围** | venv/version/、.cursor/rules/、references/tasks/deploy-git-isolated/skills/rg-fd-search/、references/tasks/deploy-git-isolated/ENTRY.json、references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md、references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md |
| **风险等级** | 低（文档与规则变更，无运行时依赖变更） |

## 一、文本文件变更清单

### 1. 修改 `venv/version/chromium.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/chromium.md` |
| **变更类型** | 修改 |
| **变更内容** | 版本号 153.0.7991.0 → 153.0.7992.0；frontmatter date 刷新 |
| **作用** | 记录 Chromium 实测版本更新 |

### 2. 修改 `venv/version/cursor.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/cursor.md` |
| **变更类型** | 修改 |
| **变更内容** | 版本号 3.14.27 → 3.15.6；frontmatter date 刷新 |
| **作用** | 记录 Cursor 实测版本更新 |

### 3. 修改 `venv/version/node.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/node.md` |
| **变更类型** | 修改 |
| **变更内容** | 版本号 26.6.0 → 26.7.0；frontmatter date 刷新 |
| **作用** | 记录 Node.js 实测版本更新 |

### 4. 修改 `venv/version/opencode.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/opencode.md` |
| **变更类型** | 修改 |
| **变更内容** | 版本号 1.18.13 → 1.18.14；frontmatter date 刷新 |
| **作用** | 记录 OpenCode CLI 实测版本更新 |

### 5. 修改 `venv/version/python.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/python.md` |
| **变更类型** | 修改 |
| **变更内容** | 版本号 3.13.14 → 3.13.15；frontmatter date 刷新 |
| **作用** | 记录 Python 实测版本更新 |

### 6. 追加 5 个 history 文件

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/chromium-history.md`、`venv/version/cursor-history.md`、`venv/version/node-history.md`、`venv/version/opencode-history.md`、`venv/version/python-history.md` |
| **变更类型** | 追加 |
| **作用** | 记录版本变更历史 |

### 7. 修改 `.cursor/rules/rg-fd-search-priority.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/rg-fd-search-priority.mdc` |
| **变更类型** | 修改 |
| **新增内容** | frontmatter 增加 `paired_skill: "rg-fd-search"` 和 `paired_skill_path`；正文顶部增加"配套 Skill（必须加载）"强制声明 |
| **作用** | 消除推断成本，Agent 读到 mdc 即知应加载 rg-fd-search skill |

### 8. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | 修改 |
| **新增内容** | rg/fd 搜索节前增加"前置步骤（不可跳过）：执行搜索前必须先加载配套 skill"提示 |
| **作用** | 速查表复制即用时不再遗漏 skill 加载 |

### 9. 修改 `.cursor/rules/high-frequency-task-index.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-task-index.mdc` |
| **变更类型** | 修改 |
| **新增内容** | 总览表新增 #9 rg/fd 搜索条目，含触发词、标准 prompt、对应 mdc + skill |
| **作用** | 用户按 Ctrl+F 搜"搜索"即可定位 rg-fd-search |

### 10. 修改 `.cursor/rules/high-frequency-task-show-trigger.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-task-show-trigger.mdc` |
| **变更类型** | 修改 |
| **新增内容** | 速查卡新增 #8 rg/fd 搜索（自动触发）条目，含触发词、标准 prompt、skill 加载提示 |
| **作用** | 新 session 首次交互时用户和 Agent 自动看到 rg-fd-search |

### 11. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **新增内容** | rg-fd-search 条目增强：追加"配套 mdc 引用 + 加载方式（skill 工具 → name=rg-fd-search）" |
| **作用** | 提高 TASK-TOOLS-INDEX 中的信息密度和可发现性 |

### 12. 修改 `references/tasks/deploy-git-isolated/ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | 修改 |
| **新增内容** | version_history 追加 v0.25.1；last_updated 刷新为 2026-08-06T15:13:00 |
| **作用** | task 本地真源索引同步 |

### 13. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-mdc-skill-pair-disconnect.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-mdc-skill-pair-disconnect.md` |
| **变更类型** | 新建 |
| **作用** | 记录"mdc 已加载但配套 skill 被遗忘"的陷阱。含四层根因分析（系统提示列表不完整、mdc 无声明、Agent 认知盲区、速查表未登记）+ 四项修复方式 + 反模式清单 |

### 14. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-pairing-mechanism.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-pairing-mechanism.md` |
| **变更类型** | 新建 |
| **作用** | 建立 mdc-skill 配套关联机制，定义 5 条铁律：mdc 显式声明配套 skill、skill 声明配套 mdc、自检清单增加 skill 加载检查项、高频任务速查表登记、EXEC-CHEATSHEET 前置提示 |

### 15. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-rule-skill-pairing-pattern.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-rule-skill-pairing-pattern.md` |
| **变更类型** | 新建 |
| **作用** | 提炼"规则层 alwaysApply mdc 与配套 skill 的配对闭环"可复用认知模式，定义配对建立→检测→修复三步方法论 |

### 16. 修改 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |
| **变更类型** | 修改 |
| **新增内容** | 版本号 1.1.0 → 1.2.0；fingerprint_index 追加 3 个新指纹；evolution_history 追加 v1.2.0 记录 |
| **作用** | SED 演进真源索引同步 |

## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。所有变更均为文本文件修改或新建。

## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认版本记录已更新 | `rg -n "记录版本" venv/version/*.md` | 5 个文件显示最新版本号 |
| 2 | 确认 mdc 已声明配套 skill | `rg -n "rg-fd-search" .cursor/rules/rg-fd-search-priority.mdc` | 显示 `paired_skill` 和配套声明 |
| 3 | 确认速查卡已登记 | `rg -n "rg/fd 搜索" .cursor/rules/high-frequency-task-show-trigger.mdc` | 显示条目 |
| 4 | 确认 SED 文件已入库 | `fd -e md "2026-08-06" references/tasks/deploy-git-isolated/skills/rg-fd-search/` | 显示 3 个新文件 |
| 5 | 确认 manifest 已更新 | `rg -n "1.2.0" references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` | 显示 current_version |

## 四、Session 踩坑与纠偏记录

### 踩坑 1：Agent 声称"没有任何 skill 命中"

**现象**：用户要求"查看 gh 工作进度"，Agent 使用 rg/fd 执行搜索后声称"没有任何 skill 命中"。实际上 `rg-fd-search` skill 完全命中（触发词：搜索、查找、进度查询）。

**根因**：
1. 系统提示的 `<available_skills>` 列表不包含 task 本地 skill（`references/tasks/deploy-git-isolated/skills/rg-fd-search/`）
2. Agent 仅扫描系统提示列表，未主动扫描磁盘
3. mdc 中无配套 skill 显式声明，Agent 无法建立"规则层→执行层"关联

**纠偏**：用户追问后，Agent 扫描磁盘发现 skill 存在，承认错误，并立即建立配套关联机制。

**沉淀**：
- gotcha：`gotchas/gotcha-2026-08-06-mdc-skill-pair-disconnect.md`
- evolution：`evolutions/evolution-2026-08-06-mdc-skill-pairing-mechanism.md`
- learning：`learnings/learning-2026-08-06-rule-skill-pairing-pattern.md`

### 踩坑 2：Agent 最初误解"gh 工作进度"为 GitHub CLI 官方版本

**现象**：用户说"查看一下最新的 gh 工作进度"，Agent 误解为查询 GitHub CLI 官方最新版本，执行了 `gh --version` + `webfetch`。

**纠偏**：用户纠正"我是说，我们近期对 gh 工具链的开发进度情况"，Agent 改为搜索项目内部与 gh 相关的文件和脚本。

**教训**：遇到歧义触发词时，应先确认用户意图再执行，避免"默认执行最常用语义"。

## 五、未改造/待完善事项

| # | 事项 | 原因 | 建议优先级 |
|---|------|------|-----------|
| 1 | `rg-fd-search-priority.mdc` 自检清单尚未追加"配套 skill 加载"检查项 | evolution 已定义铁律 3，但 mdc 正文中的【rg/fd 搜索优先级审计】清单尚未实际追加该行 | 高（下次触及 mdc 时立即补） |
| 2 | `SKILL.md` 尚未新增"配套 skill 关联机制"独立章节 | evolution 已落盘，但尚未收敛回 SKILL.md 基准文件 | 中（evolution 积累到收敛阈值后合并） |
| 3 | `high-frequency-tool-shell-audit.mdc` 尚未追加"配套 skill/mdc 关联扫描"通用项 | evolution 铁律 3 建议扩展 tool-audit，但尚未实施 | 中 |
| 4 | 其他存在"mdc + skill"配对关系的场景尚未同步建立关联机制 | 如 `tool-discovery`、`docstring-quality-harness` 等 skill 也可能存在类似断裂风险 | 低（逐一排查） |

## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 mdc | 从 git 恢复 `.cursor/rules/rg-fd-search-priority.mdc` 到修改前版本 |
| 恢复速查表 | 从 git 恢复 `.cursor/rules/high-frequency-task-index.mdc` 和 `high-frequency-task-show-trigger.mdc` |
| 恢复 EXEC-CHEATSHEET | 从 git 恢复 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| 恢复 TASK-TOOLS-INDEX | 从 git 恢复 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| 恢复 ENTRY.json | 从 git 恢复 `references/tasks/deploy-git-isolated/ENTRY.json` |
| 删除 SED 新增文件 | `Remove-Item` 删除 3 个 gotcha/evolution/learning 文件 |
| 恢复 manifest.json | 从 git 恢复 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-06-152330 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求更新运行时版本 + 查看 gh 工作进度 |
| **下次修订条件** | 当 rg-fd-search-priority.mdc 自检清单实际追加 skill 加载项时；当 SKILL.md 收敛 evolution 时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
