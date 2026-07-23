---
title: Pipeline Phase 产物统筹与 `--output` 统一参数规范整改
description: 将 polyrepo pipeline 中 atomic / workflow-phase 脚本的 manifest 产物路径从内部封闭生成改为由上级编排层通过 `--output` 显式指定，统一参数名、变量名与文件名命名规则。
date: 2026-07-23
meta:
  version: "1.0.0"
  category: env-migration
---

# env-migration-pipeline-output-unification-2026-07-23-104308

> **文档性质**：环境级变更记录。聚焦 pipeline 跨 phase 产物统筹机制的规范化整改。
> **受众**：Human + Agent。新环境复现时按「文本文件变更清单」逐条复制即可。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Pipeline Phase 产物统筹与 `--output` 统一参数规范整改 |
| **日期** | 2026-07-23 |
| **文件名时间戳** | `2026-07-23-104308` |
| **触发原因** | 用户指出 workflow-poly 中存在隐性原则：pipeline phase 之间通过 manifest.json 传递上下文，下级 manifest 应由上级调用者指定路径，方便编排层统筹。该原则此前未显性化，且参数名 `--manifest` / `--output` 混用，需要统一整改并写入 baseline。 |
| **影响范围** | baseline/（新增 §8.9）、schema/（docstring 模板更新）、py-tools/（8 个脚本整改）、verified-task-index.json、EXEC-CHEATSHEET.md |
| **风险等级** | 低（仅 CLI 参数名与代码内变量名调整，业务逻辑不变） |


## 一、文本文件变更清单

### 1. 新建/修改 `baseline/baseline-workflow-deploy.md`

| 属性 | 值 |
|------|-----|
| **路径** | `baseline/baseline-workflow-deploy.md` |
| **变更类型** | `修改`（追加 §8.9） |
| **新增内容** | Pipeline Phase 产物统筹与 `--output` 统一参数规范：核心意图、参数铁律、代码内命名规范、文件名命名规则、迁移义务清单、上下游契约示例 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接复制新增章节 |

### 2. 修改 `baseline/baseline-index.md`

| 属性 | 值 |
|------|-----|
| **路径** | `baseline/baseline-index.md` |
| **变更类型** | `修改` |
| **新增内容** | 导航表职责描述更新、顶层原则速查追加第 15 条、版本历史追加 v2.1.0 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |

### 3. 修改 `schema/docs/py-script-docstring-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/docs/py-script-docstring-schema.md` |
| **变更类型** | `修改` |
| **新增内容** | 通用模板【调用参数】追加 `--output` 参数行；字段说明表「审计产物」追加 `--output` 规范引用；迁移检查清单追加 `--output` 合规项 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |

### 4. 修改 `atomic-agent-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-agent-preflight.py` |
| **变更类型** | `修改` |
| **变更内容** | `--manifest` → `--output`（参数名 + parser help + docstring + 代码内变量 `manifest_path` → `output_path`） |
| **联动影响** | `generate-ai-summary.py` 调用处同步改 `--manifest` → `--output` |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 5. 修改 `generate-ai-summary.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py` |
| **变更类型** | `修改` |
| **变更内容** | 调用 atomic-agent-preflight 处 `--manifest` → `--output` |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接编辑 |

### 6. 修改 `atomic-check-chrome-session.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-check-chrome-session.py` |
| **变更类型** | `修改` |
| **变更内容** | 移除 `-o` 短别名，仅保留 `--output` |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接编辑 |

### 7. 修改 `atomic-gh-repo-create.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-create.py` |
| **变更类型** | `修改` |
| **变更内容** | 新增 `--output` CLI 参数；`_save_manifest()` 接收 `output_path` 参数；docstring【调用参数】登记 `--output` |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 8. 修改 `atomic-git-repo-clone.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-repo-clone.py` |
| **变更类型** | `修改` |
| **变更内容** | 同上（新增 `--output` + `_save_manifest()` 改造 + docstring） |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 9. 修改 `atomic-git-push-smoke.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-push-smoke.py` |
| **变更类型** | `修改` |
| **变更内容** | 同上 |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 10. 修改 `workflow-phase-git-local-diff-add-commit.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-phase-git-local-diff-add-commit.py` |
| **变更类型** | `修改` |
| **变更内容** | 同上 |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 11. 修改 `atomic-config-edit-json.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py` |
| **变更类型** | `修改` |
| **变更内容** | 同上 |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 12. 修改 `verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `修改` |
| **变更内容** | `atomic-agent-preflight` 条目的 description 和 entry_command 中 `--manifest` → `--output` |
| **修改方式** | `atomic-config-edit-json.py --batch @patch.json --backup` 结构化编辑 |
| **验证方式** | `run-lint.py lint_json + lint_encoding` 通过 |
| **迁移方式** | 使用 atomic-config-edit-json.py 重新执行 batch |

### 13. 修改 `EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `修改` |
| **变更内容** | S5.4.1 Polyrepo 初始化四步示例全部追加 `--output`（Agent 多行和终端单行两种形态） |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |


## 二、非文本操作

本次 session **未涉及**文件复制、缓存迁移、目录创建等非文本操作。


## 三、环境变量速查

本次 session **未新增/修改**环境变量。


## 四、落盘验证

| 文件 | 验证工具 | 结果 |
|------|---------|------|
| `baseline-workflow-deploy.md` | run-lint.py lint-md | ✅ 通过 |
| `baseline-index.md` | run-lint.py lint-md | ✅ 通过 |
| `py-script-docstring-schema.md` | run-lint.py lint-md | ✅ 通过 |
| `atomic-agent-preflight.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `generate-ai-summary.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-check-chrome-session.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-gh-repo-create.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-git-repo-clone.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-git-push-smoke.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `workflow-phase-git-local-diff-add-commit.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-config-edit-json.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `verified-task-index.json` | run-lint.py lint_json + lint_encoding | ✅ 通过 |
| `EXEC-CHEATSHEET.md` | run-lint.py lint-md | ✅ 通过 |


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 5 个新脚本含 `--output` | `grep -n "--output" atomic-gh-repo-create.py atomic-git-repo-clone.py atomic-git-push-smoke.py workflow-phase-git-local-diff-add-commit.py atomic-config-edit-json.py` | 每个文件至少命中 2 处（parser.add_argument + docstring） |
| 2 | 确认 atomic-agent-preflight 已改 `--output` | `grep -n "--output" atomic-agent-preflight.py` | 命中；`--manifest` 无命中 |
| 3 | 确认 generate-ai-summary 调用处已改 | `grep -n "--output" generate-ai-summary.py` | 命中 `--output` |
| 4 | 确认 baseline §8.9 存在 | `grep -n "8.9" baseline-workflow-deploy.md` | 命中 |
| 5 | 确认 verified-task-index.json 已更新 | `grep -n "--output" verified-task-index.json` | 命中 `--output`；无 `--manifest` |
| 6 | 确认 EXEC-CHEATSHEET 示例含 `--output` | `grep -n "--output" EXEC-CHEATSHEET.md` | 命中 4 处（四步各一） |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 atomic-agent-preflight 参数名 | `git checkout atomic-agent-preflight.py`（或手动改回 `--manifest`） |
| 恢复 generate-ai-summary 调用 | `git checkout generate-ai-summary.py` |
| 恢复 5 个新脚本的 `--output` | `git checkout atomic-gh-repo-create.py atomic-git-repo-clone.py atomic-git-push-smoke.py workflow-phase-git-local-diff-add-commit.py atomic-config-edit-json.py` |
| 恢复 baseline | `git checkout baseline/baseline-workflow-deploy.md baseline/baseline-index.md` |
| 恢复 schema | `git checkout schema/docs/py-script-docstring-schema.md` |
| 恢复索引 | `cp verified-task-index.json.bak verified-task-index.json` |
| 恢复速查表 | `git checkout scripts/EXEC-CHEATSHEET.md` |


## 七、关联文档

| 文档 | 说明 |
|------|------|
| `baseline/baseline-workflow-deploy.md` §8.9 | 本 session 新增的 Pipeline Phase 产物统筹规范 |
| `schema/docs/py-script-docstring-schema.md` | docstring 模板已更新 `--output` 参数要求 |
| `references/env-migrations/env-migration-py-tools-atomic-migration-2026-07-22-170521.md` | 上游触发源：昨天 py-tools atomic 脚本正式化迁移 |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-23-104308 |
| **更新人** | OpenCode Agent Session |
| **变更触发** | 用户要求将 workflow-poly 中的隐性原则显性化，统一 `--output` 参数名 |
| **下次修订条件** | 新增产生 manifest 的 py-tools 脚本；或 `--output` 规范需要扩展覆盖新产物类型 |
| **跨环境迁移参考** | 直接复制本文档「文本文件变更清单」中的全部文件到新环境对应路径 |


*文档生成时间：2026-07-23*  
*模板版本：v2*
