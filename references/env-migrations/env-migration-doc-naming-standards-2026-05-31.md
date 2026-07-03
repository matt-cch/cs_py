---
title: env-migration — 文档命名规范与 env-migration 模板建设
description: 记录本次 session 在 schema/structure/ 下新建 doc-naming-conventions.md 和 env-migration-template.md，以及导航联动的全部变更。
date: 2026-05-31
---

# env-migration-doc-naming-standards-2026-05-31

> **Session 主题**：建立 `env-migration-*` 文档规范、区分其与 `handoff`/`gotcha`/`retrospective` 的边界、提供标准模板，并同步更新相关导航。  
> **适用场景**：将本次规范建设迁移到新开发环境，或后续按此模板新建 env-migration 文档时参照。


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 文档命名规范与 env-migration 模板建设 |
| **日期** | 2026-05-31 |
| **触发原因** | 用户在生成 `session-diff-manifest-2026-05-31.md` 后质疑 `manifest` 命名的规范性，要求区分 env-migration 与 handoff，并沉淀文档命名决策 |
| **影响范围** | `schema/structure/` 新增 3 份规范文档 + `references/` 新建 2 个子目录 + 多处导航联动修正 + 2 份 env-migration 文档位置迁移 |
| **风险等级** | 极低（纯文档与规范，不影响运行时） |


## 一、文本文件变更清单

### 1. 新建 `schema/structure/env-migration-template.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/env-migration-template.md` |
| **变更类型** | 新建 |
| **内容概要** | `env-migration-*` 文档的标准模板，含：元信息、文本文件变更清单、非文本操作（缓存迁移）、环境变量速查、验证清单、边界说明、回滚方案、常见错误排查 |
| **作用** | 以后任何 session 产生环境级变更时，直接复制此模板填空，确保格式统一、信息完整 |
| **迁移方式** | 直接复制到新环境同名路径 |


### 2. 新建 `schema/structure/doc-naming-conventions.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/doc-naming-conventions.md` |
| **变更类型** | 新建 |
| **内容概要** | 项目文档命名规范：9 种文档类型的定义（handoff、env-migration、gotcha、retrospective、system-analysis、guide、setup、session-context、schema）、handoff vs env-migration 区分、gotcha vs retrospective 区分、不推荐做法（manifest/diff/handoff 混用）、命名速查表、外部术语对照、7 步决策流程 |
| **作用** | 消除命名混乱，确保 human/agent 都能一眼识别文档粒度与目的 |
| **迁移方式** | 直接复制到新环境同名路径 |

> **重要**：此文档是对项目既有实践的**归纳与显式化**，而非凭空创造。其中 `gotcha` 类型源自 DESIGN.md 已定义的 `docs/projects/ap-quotation/gotchas/` 目录；`retrospective` 类型源自已有的 `ui-ux-pro-max-install-retrospective.md` 等文件。


### 3. 修改 `schema/structure/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/README.md` |
| **变更类型** | 导航表追加两行 |
| **新增内容** | `doc-naming-conventions.md` 和 `env-migration-template.md` 的索引条目 |
| **迁移方式** | 直接追加即可 |


### 4. 修改 `schema/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/README.md` |
| **变更类型** | `structure/` 分类描述修正 |
| **修改点** | `structure/` 行的说明文字从"目录结构约定、项目骨架模板、路径与命名规范"扩展为"目录结构约定、项目骨架模板、**文档命名规范、env-migration 模板**" |
| **迁移方式** | 直接替换该单元格内容 |


### 5. 重命名 `docs/tooling/opencode/session-diff-manifest-2026-05-31.md`

| 属性 | 值 |
|------|-----|
| **旧路径** | `docs/tooling/opencode/session-diff-manifest-2026-05-31.md` |
| **新路径** | `docs/tooling/opencode/env-migration-opencode-cache-2026-05-31.md` |
| **变更类型** | 重命名（无内容变更） |
| **原因** | 遵循刚建立的命名规范，`manifest` 不用于描述 session 级环境变更 |
| **迁移方式** | 在新环境直接以新名创建，或删除旧文件后重建 |


### 6. 修改 `docs/tooling/opencode/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/README.md` |
| **变更类型** | 导航表追加一行，后修正移除 |
| **新增内容** | 先追加 `env-migration-opencode-cache-2026-05-31.md` 索引，后因文件迁走而移除 |
| **迁移方式** | 直接追加即可 |

### 7. 新建 `schema/structure/changelog-template.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/changelog-template.md` |
| **变更类型** | 新建 |
| **内容概要** | Monorepo 环境变更记录模板：意图与现象、diff 前后对照、落地步骤、踩坑与验证、文档元信息 |
| **作用** | 统一 `references/changelog/` 下新增记录的格式，确保 human/agent 都能完整复现环境变更 |
| **迁移方式** | 直接复制到新环境同名路径 |

### 8. 新建 `references/changelog/` 目录及文件

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/README.md` |
| **变更类型** | 新建 |
| **内容概要** | changelog 目录索引 + 与项目级 changelog 的区分说明 |

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/monorepo-env-changelog.md` |
| **变更类型** | 新建 |
| **内容概要** | 本次缓存隔离修正的 monorepo 级变更时间线（按模板格式） |

### 9. 新建 `references/env-migrations/` 目录并迁移文件

| 属性 | 值 |
|------|-----|
| **来源** | `docs/tooling/opencode/env-migration-opencode-cache-2026-05-31.md` |
| **目标** | `references/env-migrations/env-migration-opencode-cache-2026-05-31.md` |
| **变更类型** | 迁移（目录新建 + 文件移动） |
| **原因** | env-migration 是一次性交接单，不应与长期规范混放在 schema/ 或 docs/tooling/ 下 |

| 属性 | 值 |
|------|-----|
| **来源** | `schema/structure/env-migration-doc-naming-standards-2026-05-31.md` |
| **目标** | `references/env-migrations/env-migration-doc-naming-standards-2026-05-31.md` |
| **变更类型** | 迁移（文件移动） |
| **原因** | 同上 |

### 10. 修改 `references/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/README.md` |
| **变更类型** | 导航表追加两行 |
| **新增内容** | `env-migrations/` 和 `changelog/` 子目录登记 |
| **迁移方式** | 直接追加即可 |

### 11. 修正 `schema/structure/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/README.md` |
| **变更类型** | 导航表移除一行 + 追加一行 |
| **修改点** | ① 移除已迁走的 `env-migration-doc-naming-standards-2026-05-31.md` 索引  <br>② 追加 `changelog-template.md` 索引 |
| **迁移方式** | 手动编辑 |

### 12. 修正 `schema/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/README.md` |
| **变更类型** | 回退 earlier 修改 |
| **修改点** | `structure/` 描述从"目录结构约定、项目骨架模板、文档命名规范、env-migration 模板"回退为"目录结构约定、项目骨架模板、文档命名规范" |
| **原因** | env-migration 模板迁走后，schema/ 不再存放一次性文档 |


## 二、非文本操作

本次 session 涉及一次文件系统迁移操作（env-migration 文档从 schema/ 和 docs/tooling/ 迁到 references/env-migrations/），**不涉及 git 追踪的文件**。


## 三、验证清单（新环境必须执行）

迁移完成后，按此表逐项验证：

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认模板文件存在 | `Test-Path "schema/structure/env-migration-template.md"` | `True` |
| 2 | 确认命名规范文件存在 | `Test-Path "schema/structure/doc-naming-conventions.md"` | `True` |
| 3 | 确认结构目录 README 已更新 | `Select-String "env-migration-template" "schema/structure/README.md"` | 有匹配行 |
| 4 | 确认 schema 根 README 已更新 | `Select-String "env-migration" "schema/README.md"` | 有匹配行 |
| 5 | 确认 env-migration 文档已重命名 | `Test-Path "docs/tooling/opencode/env-migration-opencode-cache-2026-05-31.md"` | `True`；旧名 `session-diff-manifest-...` 不应存在 |
| 6 | 确认 tooling/opencode README 已更新 | `Select-String "env-migration-opencode-cache" "docs/tooling/opencode/README.md"` | 有匹配行 |
| 7 | 确认 gotcha 类型被正确纳入 | `Select-String "gotcha|trap\.md" "schema/structure/doc-naming-conventions.md"` | 有多处匹配 |
| 8 | 确认 handoff 与 env-migration 区分清晰 | `Select-String "handoff.*env-migration|一句话区分" "schema/structure/doc-naming-conventions.md"` | 有匹配行 |
| 9 | 确认 changelog-template 存在 | `Test-Path "schema/structure/changelog-template.md"` | `True` |
| 10 | 确认 references/changelog/ 存在 | `Test-Path "references/changelog/monorepo-env-changelog.md"` | `True` |
| 11 | 确认 env-migrations/ 有文件 | `Get-ChildItem "references/env-migrations"` | 显示 2 个 env-migration 文件 |
| 12 | 确认 tooling/opencode README 已移除旧索引 | `Select-String "env-migration-opencode-cache" "docs/tooling/opencode/README.md"` | **无匹配**（已迁走） |


## 四、与其他 Session 的边界说明

本次 session **不包含**以下变更（这些已在其他文档中记录或属于历史 session）：

| 文件/目录 | 所属文档/Session | 说明 |
|-----------|----------------|------|
| `.vscode/settings.json` 追加 `XDG_CACHE_HOME` | `env-migration-opencode-cache-2026-05-31.md` | OpenCode 缓存隔离修正 |
| `docs/tooling/opencode/data-opencode-directory-intent-and-evolution.md` | 同左 | 缓存隔离决策复盘 |
| `docs/tooling/opencode/cursor-opencode-setup-and-logs.md` | 同左 | 文档修正 |
| `venv/data-opencode/cache/` 目录及缓存迁移 | 同左 | 文件系统操作 |
| `apps/`、`backend/` 全部业务代码 | Handoff V1~V12 | 项目功能交付 |


## 五、回滚方案

若迁移后发现问题，按以下步骤回退：

| 回滚步骤 | 命令 |
|---------|------|
| 删除模板文件 | `Remove-Item "schema/structure/env-migration-template.md"` |
| 删除命名规范文件 | `Remove-Item "schema/structure/doc-naming-conventions.md"` |
| 删除 changelog-template | `Remove-Item "schema/structure/changelog-template.md"` |
| 恢复 schema/structure/README.md | 从版本控制回退或手动移除 changelog-template 导航行 |
| 恢复 schema/README.md | 从版本控制回退或手动恢复 structure/ 描述（去掉 env-migration 模板字样） |
| 恢复 env-migration 旧名（如需） | `Rename-Item "...env-migration-opencode-cache..." "...session-diff-manifest..."` |
| 恢复 tooling/opencode/README.md | 手动移除 env-migration 导航行 |
| 删除 references/changelog/ | `Remove-Item -Recurse "references/changelog"` |
| 删除 references/env-migrations/ | `Remove-Item -Recurse "references/env-migrations"` |
| 恢复 references/README.md | 从版本控制回退 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-05-31 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户质疑 `manifest` 命名规范性，要求建立 env-migration 规范；后续进一步要求建立 changelog 模板和目录 |
| **下次修订条件** | 新增 env-migration 文档时按此模板执行；文档命名规范本身若有新增类型，同步修正 |
| **跨环境迁移参考** | 新环境只需复制 `schema/structure/` 下的 3 份模板/规范 + `references/` 下的 2 个子目录及内容 |


*文档生成时间：2026-05-31*  
*最后更新时间：2026-05-31*  
*对应 Session 主题：文档命名规范、env-migration 模板与 changelog 模板建设*
