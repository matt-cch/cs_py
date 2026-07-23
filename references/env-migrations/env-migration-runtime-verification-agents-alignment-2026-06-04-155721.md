---
title: 真源检测 + AGENTS.md 与 PROJECT-STRUCTURE 对齐 + 新增 schema
description: >
  执行运行时真源检测，同步更新 verified-runtime-index.json；
  修订 AGENTS.md（权威性边界、真源引用优先级、PS 调用规范）；
  修订 PROJECT-STRUCTURE.md（免责声明、目录对齐、消除过期路径误导）；
  新增 3 个 schema 填补 references/runtime 产物规范缺口。
date: 2026-06-04
---

# env-migration-runtime-verification-agents-alignment-2026-06-04-155721

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 真源检测 + AGENTS.md 与 PROJECT-STRUCTURE 对齐 + 新增 schema |
| **日期** | 2026-06-04 |
| **文件名时间戳** | `2026-06-04-155721` |
| **触发原因** | ① 用户要求执行真源检测；② 发现 AGENTS.md 中自造规则循环论证问题；③ 发现 PROJECT-STRUCTURE.md 过期误导（backend/frontend 已废弃仍展示） |
| **影响范围** | `venv/.opencode/AGENTS.md`、`.cursor/rules/PROJECT-STRUCTURE.md`、`references/runtime/verified-runtime-index.json`、新增 3 个 `schema/structure/*.md` |
| **风险等级** | 低（纯文档与索引更新，无业务代码变更） |


## 一、文本文件变更清单

### 1. 修改 `venv/.opencode/AGENTS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | 追加 + 修改 |
| **新增内容** | ① 开篇「AGENTS.md 的角色与权威性边界」章节；② 「真源引用优先级（硬性规则）」章节（P0/P1/P2 三层 + 三条可执行规则）；③ 与 `PROJECT-STRUCTURE.md` 衔接说明 |
| **修改内容** | ① 「根目录与文件系统」：`PROJECT-STRUCTURE.md` 描述从"实时"改为"概览"；② 「Bash 工具调用子进程时的中文 stdout 编码问题」中 PowerShell 调用方式：删除 `chcp 65001; & "..."`，改为显式 `powershell.exe -File "..."` |
| **作用** | 防止 Agent 自行造法、明确真源引用层级、统一 PS 调用规范 |
| **验证方式** | 通读 `AGENTS.md` 第 1-110 行，确认新增章节存在且无语法错误 |
| **迁移方式** | 直接覆盖目标环境同名文件（注意：此文件为项目级硬性约束，需人工 review） |


### 2. 修改 `.cursor/rules/PROJECT-STRUCTURE.md`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/PROJECT-STRUCTURE.md` |
| **变更类型** | 重写（frontmatter + 免责声明 + 目录树 + 子目录详解） |
| **主要变更** | ① frontmatter：`title` 从"实时目录结构"改为"目录结构概览"，`description` 添加"不承载具体版本号或路径真源"；② 新增顶部免责声明，明确真源出处为 `references/runtime/`；③ 一级目录概览：删除 `backend/` `frontend/`，新增 `.agents/` `apps/` `references/` `schema/`；④ 子目录详解：新增 `apps/` `references/` `schema/` 详解，删除 `backend/` `frontend/` 详解；⑤ `docs/` 目录树补全 `projects/` `research/`；⑥ `toolchainroot` 目录树精简为 `chrome-win/` `slides/`；⑦ 根目录映射表列标题从"实时绝对路径"改为"绝对路径示例" |
| **作用** | 消除过期路径误导（backend/frontend 已废弃），对齐实际目录结构，明确与 `verified-runtime-index.json` 的职责边界 |
| **验证方式** | ① 检查目录树中无 `backend/` `frontend/`；② 检查 `apps/` `references/` `schema/` 存在；③ 检查顶部有免责声明 |
| **迁移方式** | 直接覆盖 |


### 3. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改（版本同步 + 时间戳更新） |
| **修改内容** | ① `toolchain.node.version`：`v26.1.0` → `v26.3.0`；② `toolchain.node.verified_at` 更新；③ `toolchain.node.upstream_sources.aliyun_nodejs_release.latest_checked` 更新；④ `toolchain.npm.version`：`11.13.0` → `11.16.0`；⑤ `toolchain.npm.verified_at` 更新；⑥ `meta.last_updated` 更新为 `2026-06-04T12:06:08` |
| **作用** | 使索引中的 node/npm 版本与本地实测结果一致 |
| **验证方式** | 执行 `verify-runtime.ps1`，确认 node.version 和 npm.version 报告"版本一致" |
| **迁移方式** | 根据 `verify-runtime-report-*.json` 中的 `changed` 项，逐条同步到索引 |


### 4. 新建 `schema/structure/runtime-index-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/runtime-index-schema.md` |
| **变更类型** | 新建 |
| **内容** | 定义 `verified-runtime-index.json` 的顶层 7 个字段（meta/roots/toolchain/project_layout/opencode/canonical_sources/github_connectivity），每个字段的类型、必填项、示例，以及一致性规则（时间戳格式、路径格式、版本号格式、current/legacy 区分） |
| **作用** | 填补 references/runtime 核心产物无 schema 可循的缺口，确保 Agent 读写索引时格式一致 |
| **验证方式** | 检查文件存在且包含所有顶层字段定义 |
| **迁移方式** | 直接复制到新环境 `schema/structure/` |


### 5. 新建 `schema/structure/runtime-report-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/runtime-report-schema.md` |
| **变更类型** | 新建 |
| **内容** | 定义 `verify-runtime-report-*.json` 的标准结构（summary/meta/results），summary 数学约束，`status` 语义（PASS/FAIL/SKIP），`name` 命名规范，以及与 `verified-runtime-index.json` 的更新关系图 |
| **作用** | 规范检测报告格式，确保下游消费（AGENTS.md 引用、diff 展示）一致 |
| **验证方式** | 检查文件存在且包含 summary 约束公式 |
| **迁移方式** | 直接复制 |


### 6. 新建 `schema/structure/playbook-template.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/playbook-template.md` |
| **变更类型** | 新建 |
| **内容** | 定义 playbook 文档的标准 8 章节（适用场景、前置依赖、快速命令、详细步骤、踩坑记录、验证清单、回滚方案、元信息），与 env-migration/changelog/usage 的边界区分 |
| **作用** | 填补 `references/runtime/chromium-win-recovery-playbook.md` 无模板可循的缺口 |
| **验证方式** | 检查文件存在且包含 8 个标准章节 |
| **迁移方式** | 直接复制 |


### 7. 修改 `schema/structure/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/README.md` |
| **变更类型** | 追加 |
| **新增内容** | 导航表中新增 3 行：`runtime-index-schema.md`、`runtime-report-schema.md`、`playbook-template.md` |
| **作用** | 保持 schema 导航与新增文件同步 |
| **验证方式** | 检查导航表中包含新增的 3 个 schema |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作

本次 session 涉及一次真源检测执行：

| 操作类型 | 命令/路径 | 说明 |
|---------|----------|------|
| 执行检测 | `references/runtime/verify-runtime.ps1` | 执行后自动生成 `verify-runtime-report-20260604T120614.json` |
| 检测结论 | 总计 26 项，通过 24 项，失败 2 项（cursor candidate_paths 预期内 missing），变更 6 项（node/npm 版本升级 + GitHub 连通性延迟波动） |

> **注意**：检测报告为运行时生成物，无需手动迁移。新环境解压后重新执行 `verify-runtime.ps1` 即可生成新报告。


## 三、环境变量速查

本次 session **未变更** `.vscode/settings.json` 中的环境变量注入项。


## 四、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 AGENTS.md 新增章节存在 | `read venv/.opencode/AGENTS.md` 前 110 行 | 包含「AGENTS.md 的角色与权威性边界」和「真源引用优先级」 |
| 2 | 确认 PROJECT-STRUCTURE.md 无 backend/frontend | `read .cursor/rules/PROJECT-STRUCTURE.md` | 目录树中无 `backend/` `frontend/`，有 `apps/` |
| 3 | 确认 schema 已新增 | `glob schema/structure/*.md` | 包含 `runtime-index-schema.md`、`runtime-report-schema.md`、`playbook-template.md` |
| 4 | 确认索引版本已同步 | `read references/runtime/verified-runtime-index.json` | `toolchain.node.version` = `v26.3.0`，`toolchain.npm.version` = `11.16.0` |
| 5 | 确认 verify-runtime 可正常执行 | `powershell.exe -File "references/runtime/verify-runtime.ps1"` | 无语法错误，exit 0 |


## 五、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 AGENTS.md | 从 git 历史恢复 `venv/.opencode/AGENTS.md` 到修改前版本 |
| 恢复 PROJECT-STRUCTURE.md | 从 git 历史恢复 `.cursor/rules/PROJECT-STRUCTURE.md` |
| 恢复 verified-runtime-index.json | 从 `verified-runtime-index.history.json` 或 git 历史恢复旧版本 |
| 删除新增 schema | `Remove-Item "schema/structure/runtime-index-schema.md"`、`runtime-report-schema.md`、`playbook-template.md` |
| 恢复 schema/README.md | 从 git 历史恢复 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-04-155721 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求执行真源检测 → 发现 AGENTS.md 自造规则问题 → 对齐 PROJECT-STRUCTURE.md → 补充缺失 schema |
| **下次修订条件** | ① 有新的 monorepo 级环境变更；② `verified-runtime-index.json` 中的 `verified_at` 超过 7 天需重新检测 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 + 重新执行 `verify-runtime.ps1` 生成新报告 |


*文档生成时间：2026-06-04*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
