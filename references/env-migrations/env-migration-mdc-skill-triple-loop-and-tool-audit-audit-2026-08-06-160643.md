---
title: mdc-skill 配套关联机制升级为三层闭环 + tool-audit 全局审计卡点 + SED 入库
description: 本次 session 基于实战暴露的"单向声明不足"问题，将 rg-fd-search 的 mdc-skill 配套关联从双向声明升级为三层闭环（mdc 声明 + skill 声明 + 全局审计卡点）。改造 high-frequency-tool-shell-audit.mdc 追加不可绕过的配套 skill 检查项，规范自检清单"是"时必须展示操作对象。完成 SED 自闭环入库（gotcha/evolution/learning/manifest v1.3.0）。
date: 2026-08-06
meta:
  version: "1.0"
---

# env-migration-mdc-skill-triple-loop-and-tool-audit-audit-2026-08-06-160643

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | mdc-skill 配套关联机制升级为三层闭环 + tool-audit 全局审计卡点 + SED 入库 |
| **日期** | 2026-08-06 |
| **文件名时间戳** | 2026-08-06-160643 |
| **触发原因** | 用户要求"查看 gh 工作进度"，Agent mdc 已触发但 skill 未加载，用户指出"改 SKILL.md 有鬼用"，暴露单向声明不足问题 |
| **影响范围** | `.cursor/rules/high-frequency-tool-shell-audit.mdc`、`references/tasks/deploy-git-isolated/skills/rg-fd-search/`（gotchas/evolutions/learnings/versions/manifest.json） |
| **风险等级** | 低（规则层与文档变更，无运行时依赖变更） |

## 一、文本文件变更清单

### 1. 修改 `.cursor/rules/high-frequency-tool-shell-audit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| **变更类型** | 修改 |
| **新增内容** | 【Tool 调用规则层审计】自检清单追加 2 项："当前 mdc 是否有配套 skill？"、"配套 skill 是否已加载？"；流程图升级，在"命中高频任务 → 加载对应 mdc"后插入"mdc 是否有配套 skill？→ 已加载？"分支；所有"是/否"检查项改为"是"时必须展示操作对象（如 `是 → high-frequency-shell-guard-content.mdc`） |
| **作用** | 建立跨规则层全局审计卡点，任何 tool 调用前强制检查配套 skill 状态，形成不可绕过闭环 |
| **验证方式** | `rg -n "配套 skill" .cursor/rules/high-frequency-tool-shell-audit.mdc` 应显示检查项 |

### 2. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-unilateral-declaration-insufficient.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-unilateral-declaration-insufficient.md` |
| **变更类型** | 新建 |
| **作用** | 记录"单向声明不足"陷阱：mdc 和 SKILL.md 互相声明但 skill 对 Agent 不可见时，双向声明实际只有单向生效 |

### 3. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-triple-loop.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-triple-loop.md` |
| **变更类型** | 新建 |
| **作用** | 将配套关联机制从双向声明升级为三层闭环，定义铁律 6（全局审计卡点）、铁律 7（"是"时必须展示操作对象）、铁律 8（skill 加载失败必须 fallback 到磁盘 read） |

### 4. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-cross-rule-layer-audit-pattern.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-cross-rule-layer-audit-pattern.md` |
| **变更类型** | 新建 |
| **作用** | 提炼"跨规则层联动"可复用认知模式：当 A↔B 双向配套但 B 对 Agent 不可见时，必须在第三个独立且 alwaysApply 的层级 C 设置不可绕过的检查点 |

### 5. 修改 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |
| **变更类型** | 修改 |
| **新增内容** | `current_version`: 1.2.0 → 1.3.0；`fingerprint_index` 追加 3 个新指纹；`evolution_history` 追加 v1.3.0 记录 |
| **作用** | SED 演进真源索引同步 |

## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。所有变更均为文本文件修改或新建。

## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 tool-audit.mdc 已追加配套 skill 检查项 | `rg -n "配套 skill" .cursor/rules/high-frequency-tool-shell-audit.mdc` | 显示检查项及"是"时展示操作对象的规范 |
| 2 | 确认 SED gotcha 已入库 | `Test-Path "references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-unilateral-declaration-insufficient.md"` | True |
| 3 | 确认 SED evolution 已入库 | `Test-Path "references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-triple-loop.md"` | True |
| 4 | 确认 SED learning 已入库 | `Test-Path "references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-cross-rule-layer-audit-pattern.md"` | True |
| 5 | 确认 manifest 已更新 | `rg -n "1.3.0" references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` | 显示 current_version 和 evolution_history 条目 |
| 6 | 确认 lint 通过 | `run-lint.py --files "<上述5个文件路径>"` | ✅ 全部通过 |

## 四、Session 踩坑与纠偏记录

### 踩坑 1：Agent 再次声称"没有任何 skill 命中"

**现象**：用户要求"查看 gh 工作进度"，Agent mdc 已触发，尝试 `skill` 工具加载 rg-fd-search 失败（不在 available_skills 中），fallback 到 glob/grep 原生工具。

**根因**：
1. 系统提示 `<available_skills>` 不包含 task 本地 skill（同 2026-08-06 上午 session）
2. Agent 未读取 env-migration 中已记录的教训，重复踩同一坑
3. evolution v1.2.0 建立的"双向声明"机制实际只有单向生效（mdc 可见，skill 不可见）

**纠偏**：用户直接指出"改 SKILL.md 有鬼用啊，都没有触发"，Agent 纠正方向，在另一个 alwaysApply mdc（tool-audit.mdc）中建立全局审计卡点。

### 踩坑 2：Agent 未读 env-migration 就从头推理

**现象**：用户说"你去看一下 env-migration"，Agent 花了大量时间重新搜索、分析、得出结论，而没有先读取已有的 env-migration 文档获取上下文。

**根因**：Agent 默认行为是"搜索→分析→推理"，而不是"读取已有记录→复用→执行"。

**纠偏**：用户严厉批评"都解决半天了，你还又从头开始"，Agent 随后读取 env-migration 获取上下文。

### 踩坑 3：Agent  edit 前未全文读取目标文件

**现象**：Agent 试图 edit `rg-fd-search-priority.mdc` 的自检清单，但刚改完就发现 mdc 中已有配套 skill 检查项（只是 SKILL.md 中没有）。

**根因**：Agent 未先全文读取文件就假设内容缺失。

**纠偏**：用户指出"全文都没读，原来文本内容里是不是已经有了，你不用先了解的吗？就直接改？"

## 五、未改造/待完善事项

| # | 事项 | 原因 | 建议优先级 |
|---|------|------|-----------|
| 1 | 其他存在"mdc + skill"配对关系的场景尚未同步建立三层闭环 | tool-discovery、docstring-quality-harness 等 skill 也可能存在类似断裂风险 | 低（逐一排查） |
| 2 | `rg-fd-search-priority.mdc` 自检清单"是"时展示操作对象的规范需人工复核 | 本 session 主要改造的是 tool-audit.mdc，mdc 自身的清单是否已对齐铁律 7 需检查 | 中 |

## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 tool-audit.mdc | 从 git 恢复 `.cursor/rules/high-frequency-tool-shell-audit.mdc` 到修改前版本 |
| 删除 SED 新增文件 | `Remove-Item` 删除 3 个 gotcha/evolution/learning 文件 |
| 恢复 manifest.json | 从 git 恢复 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-06-160643 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求查看 gh 工作进度，暴露 mdc-skill 单向声明不足问题 |
| **下次修订条件** | 当其他 skill（tool-discovery 等）建立三层闭环时；当 rg-fd-search-priority.mdc 自检清单对齐铁律 7 时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
