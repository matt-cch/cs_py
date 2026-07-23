---
title: Shell 禁令规则体系重构 + 高频任务 .mdc 拆分 + gotcha 基础设施
description: 新建 strictly-forbid-command-str-content.mdc（禁令真源）与 high-frequency-shell-guard-content.mdc（执法包装器），拆分 AGENTS.md 高频任务到 .cursor/rules/，新建 docs/tooling/gotchas/ 与 gotcha 模板，更新真源检测。
date: 2026-06-06
---

# env-migration-shell-ban-rulesystem-and-gotcha-infra-2026-06-06-084200

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Shell 禁令规则体系重构 + 高频任务 .mdc 拆分 + gotcha 基础设施 |
| **日期** | 2026-06-06 |
| **文件名时间戳** | `2026-06-06-084200` |
| **触发原因** | 真源检测后更新版本记录时发现 Agent 仍违规使用 `python -c`，暴露文本禁令对 LLM 约束力有限，需升级为工程性程序机制 |
| **影响范围** | `.cursor/rules/*.mdc`、AGENTS.md、docs/tooling/gotchas/、schema/structure/、references/runtime/ |
| **风险等级** | 低（纯规则与文档变更，不涉及运行时配置） |


## 一、文本文件变更清单

### 1. 新建 `.cursor/rules/strictly-forbid-command-str-content.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/strictly-forbid-command-str-content.mdc` |
| **变更类型** | 新建 |
| **作用** | **禁令真源**。明确禁止一切 `command + str-content` 形式，取代旧 `shell-long-content-ban.mdc` |
| **核心内容** | 规则意图（消除踩坑 + 可追溯）、一句话铁律、Human-in-the-Loop 例外、禁止清单 4 条、允许行为、程序性约束（事前自检/事后验收/可追溯/可复原）、异常记录与 gotcha 沉淀机制、BOM 附注 |
| **验证方式** | `Test-Path -LiteralPath ".cursor/rules/strictly-forbid-command-str-content.mdc"` 返回 `True` |
| **迁移方式** | 新文件，直接存在 |

> **关联操作**：删除旧文件 `shell-long-content-ban.mdc`（已执行 `Remove-Item`）


### 2. 新建 `.cursor/rules/high-frequency-shell-guard-content.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-shell-guard-content.mdc` |
| **变更类型** | 新建 |
| **作用** | **执法程序包装器**。用户 prompt 命中 Shell/脚本相关触发词时，强制加载 forbid mdc 并自检 |
| **核心内容** | 触发词约定（显式 4 个 + 隐性 5 类场景）、强制加载 → 自检 → 执行路径、审计与验收输出格式、常见任务速查、与 forbid mdc 的职责分工 |
| **验证方式** | `Test-Path -LiteralPath ".cursor/rules/high-frequency-shell-guard-content.mdc"` 返回 `True` |


### 3. 新建 `.cursor/rules/high-frequency-update-version.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-update-version.mdc` |
| **变更类型** | 新建 |
| **作用** | 将 AGENTS.md 中「更新版本记录」条目拆分为独立 .mdc |
| **核心内容** | 触发词、文件定位（实测优先）、更新步骤（通用流程：先实测目录 → 循环各工具 → 无命令则询问）、与真源检测的时间差说明、常见错误 |
| **验证方式** | `Test-Path -LiteralPath ".cursor/rules/high-frequency-update-version.mdc"` 返回 `True` |


### 4. 新建 `.cursor/rules/high-frequency-env-migration.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-env-migration.mdc` |
| **变更类型** | 新建 |
| **作用** | 将 AGENTS.md 中「记录 env-migration」条目拆分为独立 .mdc |
| **验证方式** | `Test-Path -LiteralPath ".cursor/rules/high-frequency-env-migration.mdc"` 返回 `True` |


### 5. 新建 `.cursor/rules/high-frequency-project-handoff.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-project-handoff.mdc` |
| **变更类型** | 新建 |
| **作用** | 将 AGENTS.md 中「记录 project-handoff」条目拆分为独立 .mdc |
| **验证方式** | `Test-Path -LiteralPath ".cursor/rules/high-frequency-project-handoff.mdc"` 返回 `True` |


### 6. 修改 `venv/.opencode/AGENTS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | ① 高频任务速查改为索引占位（引用 `.cursor/rules/high-frequency-*.mdc` 系列）；② 长字符串 / Shell 执行边界章节精简，删除重复禁令，引用 forbid mdc 定边界 |
| **插入位置** | `## 高频任务速查` 及 `### 长字符串 / Shell 执行边界` 章节 |
| **作用** | AGENTS.md 聚焦操作细则，禁令真源下沉到 .cursor/rules/*.mdc |
| **迁移方式** | 直接覆盖对应章节 |


### 7. 新建 `docs/tooling/gotchas/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/gotchas/README.md` |
| **变更类型** | 新建 |
| **作用** | 通用工具链踩坑记录目录导航 |
| **验证方式** | `Test-Path -LiteralPath "docs/tooling/gotchas/README.md"` 返回 `True` |


### 8. 新建 `schema/structure/gotcha-template.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/gotcha-template.md` |
| **变更类型** | 新建 |
| **作用** | 踩坑记录标准模板，供所有 gotchas 目录复用 |
| **验证方式** | `Test-Path -LiteralPath "schema/structure/gotcha-template.md"` 返回 `True` |


### 9. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | cursor.version 3.6.31 → 3.7.12；github_connectivity 延迟更新；verified_at / last_updated 更新为 2026-06-06T07:02:57 |
| **作用** | 真源检测后同步变更项 |
| **迁移方式** | 直接修改对应字段 |


### 10. 修改 `venv/version/cursor.md` 与 `cursor-history.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/cursor.md`、`venv/version/cursor-history.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | cursor.md：version 3.6.31 → 3.7.12，date 2026-06-06；cursor-history.md：末尾追加 `2026-06-06 | **3.6.31 → 3.7.12**` |
| **作用** | 版本记录更新 |


## 二、非文本操作（文件系统）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 目录创建 | — | `docs/tooling/gotchas/` | 通用工具链踩坑记录目录 |
| 文件删除 | `.cursor/rules/shell-long-content-ban.mdc` | — | 旧禁令文件，已被 `strictly-forbid-command-str-content.mdc` 取代 |


## 三、环境变量速查

无新增环境变量。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 forbid mdc 存在 | `Test-Path -LiteralPath ".cursor/rules/strictly-forbid-command-str-content.mdc"` | `True` |
| 2 | 确认 guard mdc 存在 | `Test-Path -LiteralPath ".cursor/rules/high-frequency-shell-guard-content.mdc"` | `True` |
| 3 | 确认 update-version mdc 存在 | `Test-Path -LiteralPath ".cursor/rules/high-frequency-update-version.mdc"` | `True` |
| 4 | 确认旧文件已删除 | `Test-Path -LiteralPath ".cursor/rules/shell-long-content-ban.mdc"` | `False` |
| 5 | 确认 gotchas 目录存在 | `Test-Path -LiteralPath "docs/tooling/gotchas/README.md"` | `True` |
| 6 | 确认 gotcha 模板存在 | `Test-Path -LiteralPath "schema/structure/gotcha-template.md"` | `True` |
| 7 | 确认 AGENTS.md 高频任务为索引 | `Select-String -Path "venv/.opencode/AGENTS.md" -Pattern "high-frequency-.*.mdc"` | 命中 4 个或以上 |
| 8 | 确认真源索引 cursor 版本 | `Select-String -Path "references/runtime/verified-runtime-index.json" -Pattern '"version": "3.7.12"'` | 命中 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复旧禁令文件 | 从 git 历史恢复 `shell-long-content-ban.mdc`（若已纳入版本控制） |
| 删除新 .mdc 文件 | `Remove-Item ".cursor/rules/strictly-forbid-command-str-content.mdc"`、`Remove-Item ".cursor/rules/high-frequency-shell-guard-content.mdc"` 等 |
| 恢复 AGENTS.md | 从 git 历史恢复旧版本 |
| 删除 gotchas 目录 | `Remove-Item -Recurse "docs/tooling/gotchas"` |
| 删除 gotcha 模板 | `Remove-Item "schema/structure/gotcha-template.md"` |
| 恢复版本记录 | cursor.md 回退到 3.6.31，删除 history 最新行 |
| 恢复真源索引 | verified-runtime-index.json 回退 cursor.version 到 3.6.31 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-06-084200 |
| **更新人** | Human + Agent Session |
| **变更触发** | 真源检测后更新版本记录时发现 Agent 仍踩 `python -c` 坑，推动禁令从文本描述升级为工程性程序机制 |
| **下次修订条件** | 新增高频任务需拆分、guard-content mdc 触发词需扩展、forbid mdc 程序性约束需迭代 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-06*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
