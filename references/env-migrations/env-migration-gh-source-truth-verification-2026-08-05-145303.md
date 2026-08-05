---
title: env-migration — GitHub 真源检测体系开发与修订联动
description: 本次 session 完成 source_truth.py L1-L5 真源推理链、atomic-gh-repo-verify.py 原子 CLI、2 个新 mdc 规则、全量修订联动登记。
date: 2026-08-05
meta: {}
---

# env-migration — GitHub 真源检测体系开发与修订联动

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | GitHub 真源检测体系（L1-L5 推理链）开发与工具登记修订联动规范 |
| **日期** | 2026-08-05 |
| **文件名时间戳** | `2026-08-05-145303` |
| **触发原因** | 修正 gh_preflight 真源认知误区，建立从 git-security.json 到 GitHub PR 状态的完整真源推理链 |
| **影响范围** | deploy-git-isolated task 脚本体系、.cursor/rules mdc 规则、全项目工具索引 |
| **风险等级** | 低（新增工具与规则，不破坏现有流程） |

## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/source_truth.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/source_truth.py` |
| **变更类型** | 新建 |
| **作用** | L1-L5 Git/GitHub 真源推理链核心插件。L1 intent-config（git-security.json）→ L2 local-git（.git/config + HEAD SHA）→ L3 worktree（分支/跟踪/上游一致性）→ L4 remote-HEAD（commit SHA 是否在远程）→ L5 PR-status（当前分支关联的 PR 状态） |
| **关键设计** | L5 查 `--state all` 而非 `--state open`；遍历全部 PR 找 `headRefOid == local_head_sha` 匹配；无匹配时按 `OPEN > MERGED > CLOSED` 优先级取最新；PR 不存在/head_mismatch 只记录为 INFO/WARNING，不阻断 `ok`；唯一阻断条件：L4 commit SHA 不在远程 |
| **验证方式** | jywl-settlement feat/demo 实执行验证通过 |

### 2. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-verify.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-verify.py` |
| **变更类型** | 新建 |
| **作用** | 标准 atomic CLI 入口。调用 source_truth 插件执行 L1-L5 推理链，输出 JSON manifest 供下游 PR 创建/合并复用 |
| **调用契约** | `--devroot` + `--target` 必填；`--output`/`--dry-run`/`--show-progress` 标准可选 |
| **下游消费** | atomic-gh-pr-create.py、atomic-gh-pr-merge.py（尚未集成，见「未改造事项」） |

### 3. 修改 `git-security.json`（cs_py 根 + jywl-settlement feat-demo）

| 属性 | 值 |
|------|-----|
| **路径** | `git-security.json`（两处） |
| **变更类型** | 修改 |
| **新增内容** | `owner_repo` 字段（如 `"matt-cch/jywl-settlement"`） |
| **作用** | 为 L1 intent-config 层提供 owner/repo 真源，替代从 remote URL 反向推断 |

### 4. 新建 `.cursor/rules/tool-registration-revision-linkage.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/tool-registration-revision-linkage.mdc` |
| **变更类型** | 新建 |
| **作用** | 规范新增/更新工具的登记修订联动义务。定义「登记四件套」（ENTRY.json / TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md / verified-task-index.json）+ 父级 README 导航联动 |
| **底座层例外** | py-plugins/ 插件不单独在四件套中登记，由父级 README 自说明承担 |

### 5. 新建 `.cursor/rules/strictly-forbid-manual-lint-bypass.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/strictly-forbid-manual-lint-bypass.mdc` |
| **变更类型** | 新建 |
| **作用** | 严禁手工绕过 lint 修复。lint 报错后唯一允许 `run-lint.py --fix`；禁止 `edit`/`replaceAll`/`bash` 手工 patch；Markdown 正文严禁 `---` 分隔符（根因：Agent 读文档时会把正文 `---` 误判为 YAML frontmatter 结束定界符） |
| **来源** | Agent 多次违规（正文用 `---`、lint 报错后用 `edit replaceAll` 修），用户明确要求固化禁令 |

### 6. 修订联动登记（四件套）

| 目标文件 | 登记内容 |
|---------|---------|
| `ENTRY.json` | version_history 追加 `0.24.0`；active_scripts 追加 `source_truth.py` + `atomic-gh-repo-verify.py`；last_updated 刷新 |
| `TASK-TOOLS-INDEX.md` | 1.10 GitHub CLI 节追加 2 行（atomic-gh-repo-verify.py、source_truth.py）；新增 L1-L5 推理链说明段落 |
| `EXEC-CHEATSHEET.md` | 追加 atomic-gh-repo-verify.py 标准命令示例 |
| `verified-task-index.json` | available_scripts_and_tools 追加 `atomic-gh-repo-verify` + `source-truth`；meta.last_updated 刷新 |
| `verified-trigger-index.json` | 追加 `mdc-tool-registration` + `mdc-lint-bypass` 两个 source_prefix 及触发条件；meta.last_updated 刷新 |

### 7. 知识沉淀文档

| 路径 | 说明 |
|------|------|
| `vaults/vault-demo/wiki/conclusions/git-gh-source-truth-verification-design.md` | L1-L5 真源推理链设计文档，含 gh_preflight 认知误区修正说明 |

## 二、未改造事项（待后续 session）

以下工具/流程与 atomic-gh-repo-verify.py 直接相关，但**本次 session 未触及改造**：

| # | 工具/流程 | 当前状态 | 建议改造方向 |
|---|----------|---------|------------|
| 1 | `atomic-gh-pr-create.py` | 直接调用 `gh_preflight.verify()`，未调用 source_truth | PR 创建前应先执行 `atomic-gh-repo-verify.py` 或内嵌 source_truth L1-L4 验证，确保本地 commit 已在远程 |
| 2 | `atomic-gh-pr-merge.py` | 同上 | PR 合并前应验证 PR 状态与本地 HEAD 一致性 |
| 3 | `workflow-gh-pr.py` | 编排 create → merge → pull，未嵌入 repo verify | 在 Step 0 或 Step 1 嵌入 `atomic-gh-repo-verify.py` 调用，阻断不一致场景 |
| 4 | `gh-pr-create.py`（legacy） | 未集成 | legacy 脚本保持现状，但建议在 EXEC-CHEATSHEET 中标注「推荐改用 atomic-gh-repo-verify.py + atomic-gh-pr-create.py 组合」 |
| 5 | `gh-pr-merge.py`（legacy） | 未集成 | 同上 |

## 三、Session 踩坑与纠偏记录

| # | 违规场景 | 根因 | 纠偏措施 |
|---|---------|------|---------|
| 1 | Markdown 正文使用 `---` 做分隔符 | 未理解 `---` 与 YAML frontmatter 定界符冲突 | 已新建 `strictly-forbid-manual-lint-bypass.mdc` 明文禁令 |
| 2 | lint 报错后用 `edit replaceAll` 全局替换 `---` | 试图绕过 `run-lint.py --fix` | 已明文禁止，强制走标准三阶段闭环 |
| 3 | 生成 env-migration 时遗漏 gh 工具开发核心内容 | 要点梳理不完整 | 用户 review 后补充完整 |

## 四、验证清单

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | source_truth 插件语法 | `run-lint.py --profile lint-python` | ✅ 通过 |
| 2 | atomic-gh-repo-verify CLI 语法 | `run-lint.py --profile lint-python` | ✅ 通过 |
| 3 | jywl-settlement feat/demo 实执行 | `atomic-gh-repo-verify.py --devroot ... --target ...` | manifest 输出完整，L1-L5 全部通过 |
| 4 | 修订联动文件 lint | `run-lint.py --files ENTRY.json TASK-TOOLS-INDEX.md EXEC-CHEATSHEET.md verified-task-index.json` | ✅ 全部通过 |
| 5 | 新 mdc lint | `run-lint.py --files tool-registration-revision-linkage.mdc strictly-forbid-manual-lint-bypass.mdc` | ✅ 全部通过 |

## 五、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 删除新增文件 | `source_truth.py`、`atomic-gh-repo-verify.py`、2 个 mdc 文件、知识沉淀文档 |
| 恢复修订联动 | 从 ENTRY.json / TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md / verified-task-index.json / verified-trigger-index.json 中移除本次追加条目 |
| 恢复 git-security.json | 移除 `owner_repo` 字段 |

## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-05-145303 |
| **更新人** | Human + Agent Session |
| **变更触发** | GitHub 真源检测体系开发 + 工具登记规范建设 |
| **下次修订条件** | atomic-gh-pr-create/merge 集成 source_truth 验证后更新「未改造事项」 |
