---
title: py-tools atomic 脚本正式化迁移与 JSON 配置编辑工具建设
description: 将 venv/tmp/ 下的 4 个临时 atomic 脚本正式迁移到 py-tools/，建立 docstring schema 规范，创建通用 JSON 配置编辑原子工具，完成修订联动闭环。
date: 2026-07-22
meta:
  version: "1.0.0"
  category: env-migration
---

# env-migration-py-tools-atomic-migration-2026-07-22-170521

> **文档性质**：环境级变更记录。聚焦 py-tools 脚本体系从临时到正式的迁移过程，以及 JSON 配置编辑通用能力的建设。
> **受众**：Human + Agent。新环境复现时按「文本文件变更清单」逐条复制即可。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | py-tools atomic 脚本正式化迁移与 JSON 配置编辑工具建设 |
| **日期** | 2026-07-22 |
| **文件名时间戳** | `2026-07-22-170521` |
| **触发原因** | 用户要求将 venv/tmp/ 下临时 atomic 脚本迁移到 py-tools/ 正式目录，建立统一 docstring schema，并解决 edit 改 JSON 高频失败问题 |
| **影响范围** | py-tools/（新增 5 脚本）、schema/docs/（新增规范）、TASK-TOOLS-INDEX.md、EXEC-CHEATSHEET.md、verified-task-index.json、.cursor/rules/（新增 mdc）、.env |
| **风险等级** | 中（触及索引文件修改、.env 回滚、脚本路径变更） |


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/schema/docs/py-script-docstring-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/docs/py-script-docstring-schema.md` |
| **变更类型** | `新建` |
| **作用** | py-tools 下全部 Python 脚本的命名约定、docstring schema、修订联动义务、索引登记层级 |
| **关键内容** | 四级命名模式（atomic-/workflow-/workflow-phase-/helper）、通用 docstring 模板（12 核心字段）、workflow 扩展模板、修订联动三层清单（L1→L3）、索引登记层级图、迁移检查清单 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接复制 |

### 2. 修改 `references/tasks/deploy-git-isolated/schema/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/README.md` |
| **变更类型** | `修改` |
| **新增内容** | 文件清单表格追加 `py-script-docstring-schema.md` 条目 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |

### 3. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-create.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-create.py` |
| **变更类型** | `新建`（由 `venv/tmp/atomic-create-github-repo.py` 迁移） |
| **作用** | 通过 GH CLI 创建 GitHub 远程仓库，自动注入 PAT、脱敏 stdout、生成 manifest |
| **关键设计** | docstring 按 schema 规范补全（意图/依赖/预检/调用参数/关联），路径推导兼容 `py-tools/` 和 `tmp/` 两种位置 |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 4. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-repo-clone.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-repo-clone.py` |
| **变更类型** | `新建`（由 `venv/tmp/atomic-clone-repo.py` 迁移） |
| **作用** | 隔离 git.exe clone + local git config + 验证 remote/branch/status + manifest |
| **关键设计** | 从 `.env` 读取 `GIT_USER_EMAIL`（唯一真源，修正原 `GITHUB_USER_EMAIL` 重复问题） |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 5. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-push-smoke.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-push-smoke.py` |
| **变更类型** | `新建`（由 `venv/tmp/atomic-smoke-push.py` 迁移） |
| **作用** | 构造 PAT 认证 URL + 阻断 GCM 弹窗 + 双路 preflight（staged + 未 push commit）+ manifest |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 6. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-phase-git-local-diff-add-commit.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-phase-git-local-diff-add-commit.py` |
| **变更类型** | `新建` |
| **作用** | 本地 diff → add → commit Phase 脚本，执行后进入「已 commit 未 push」状态，下游接 atomic-git-push-smoke.py |
| **关键设计** | 支持 --dry-run、--files、--allow-empty、自动生成 commit message |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 7. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py` |
| **变更类型** | `新建` |
| **作用** | 通用 JSON 配置结构化编辑原子工具。RFC 6902 JSON Pointer + JSON Patch，替代手敲 `edit` 修改 JSON |
| **关键设计** | 强制 LF（newline="\n"）、UTF-8 无 BOM、--backup 备份、--dry-run 预览、@file 批量传入、merge 深度合并 |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制 |

### 8. 新建 `.cursor/rules/high-frequency-json-edit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-json-edit.mdc` |
| **变更类型** | `新建` |
| **作用** | 高频任务 mdc：任何 JSON 文件新建/编辑/更新时触发即改道，强制使用 atomic-config-edit-json.py |
| **关键内容** | 触发词（显式+隐性）、标准三步流程、分流判断、禁止行为清单、踩坑速查、修订联动义务 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接复制 |

### 9. 修改 `.cursor/rules/high-frequency-task-index.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-task-index.mdc` |
| **变更类型** | `修改` |
| **新增内容** | 总览表追加 #8「JSON 配置原子编辑」条目 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |

### 10. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `修改` |
| **新增内容** | 1.9 部署编排 Workflow 表格追加 atomic-gh-repo-create、atomic-git-repo-clone、atomic-git-push-smoke、workflow-phase-git-local-diff-add-commit、atomic-config-edit-json 五个条目 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |

### 11. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `修改` |
| **新增内容** | ① Stage S5.4.1：polyrepo 初始化四步速查（create → clone → diff-add-commit → push-smoke）；② Stage S5.4.2：JSON 配置原子编辑标准三步流程 + 踩坑速查表 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |

### 12. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `修改` |
| **新增内容** | `available_scripts_and_tools` 追加 5 个条目（atomic-gh-repo-create、atomic-git-repo-clone、atomic-git-push-smoke、workflow-phase-git-local-diff-add-commit、atomic-config-edit-json），`meta.last_updated` 更新为 2026-07-22T17:00:00 |
| **修改方式** | 使用 `atomic-config-edit-json.py --batch @venv/tmp/patch.json --backup` 结构化编辑，非手敲 edit |
| **验证方式** | `run-lint.py lint_json + lint_encoding` 通过 |
| **迁移方式** | 直接复制（或在新环境用 atomic-config-edit-json.py 重新执行 batch） |

### 13. 修改 `.env`

| 属性 | 值 |
|------|-----|
| **路径** | `.env` |
| **变更类型** | `修改`（回滚） |
| **变更内容** | 删除新增的 `GITHUB_USER_EMAIL`，保持 `GIT_USER_EMAIL` 为唯一真源；消费端（atomic-git-repo-clone.py）改为读取 `GIT_USER_EMAIL` |
| **验证方式** | `atomic-git-repo-clone.py` 能正确读取 git email |
| **迁移方式** | 直接编辑 |

### 14. 修改 `atomic-config-edit-json.py`（RFC 6902 语法明确性加固 v1.0.1）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py` |
| **变更类型** | `修改` |
| **变更内容** | ① 方案 A：`_parse_pointer()` 错误提示增加反模式说明（不支持 JSON Path `$.foo` 或 jq `.foo.bar`）；② 方案 B：`--path` 更名为 `--json-pointer`，保留 `--path` 作为兼容别名（`dest="path"` 保证代码零侵入）；③ 版本号 v1.0.0 → v1.0.1；④ 所有 docstring 示例同步更新为 `--json-pointer` |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过；`--json-pointer` 与 `--path` 均能被正确解析 |
| **迁移方式** | 直接复制 |

### 15. 修改 `high-frequency-json-edit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-json-edit.mdc` |
| **变更类型** | `修改` |
| **变更内容** | ① 分流判断表：`--path` → `--json-pointer`；② 单条示例：`--path` → `--json-pointer`；③ 方案 C：踩坑速查追加「路径传了 `$.foo` 或 `.foo.bar`」反模式 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |

### 16. 修改 `EXEC-CHEATSHEET.md` Stage S5.4.2

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `修改` |
| **变更内容** | ① 铁律：`--path` → `--json-pointer`；② 单条示例 + dry-run 示例：`--path` → `--json-pointer`；③ 踩坑速查追加 JSON Path / jq 风格反模式 |
| **验证方式** | `run-lint.py lint-md` 通过 |
| **迁移方式** | 直接编辑 |


## 二、非文本操作

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 删除临时脚本 | `venv/tmp/atomic-create-github-repo.py` | — | 已迁移到 py-tools/atomic-gh-repo-create.py |
| 删除临时脚本 | `venv/tmp/atomic-clone-repo.py` | — | 已迁移到 py-tools/atomic-git-repo-clone.py |
| 删除临时脚本 | `venv/tmp/atomic-smoke-push.py` | — | 已迁移到 py-tools/atomic-git-push-smoke.py |
| 删除临时脚本 | `venv/tmp/edit-json-workspace.py` | — | 功能已被 atomic-config-edit-json.py 覆盖，不再维护 |


## 三、环境变量速查

本次 session **未新增**环境变量，复用既有配置：

| 变量 | 来源 | 用途 |
|------|------|------|
| `GITHUB_PAT` | `devroot/.env` | GH CLI / git push 认证 |
| `GITHUB_USERNAME` | `devroot/.env` | git config user.name / 认证 URL 构造 |
| `GIT_USER_EMAIL` | `devroot/.env` | git config user.email（唯一真源） |

> **真源修正**：原临时脚本读取 `GITHUB_USER_EMAIL`，本次 session 修正为读取 `GIT_USER_EMAIL`，避免 .env 中同一信息多头维护。


## 四、落盘验证

| 文件 | 验证工具 | 结果 |
|------|---------|------|
| `py-script-docstring-schema.md` | run-lint.py lint-md | ✅ 通过 |
| `atomic-gh-repo-create.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-git-repo-clone.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-git-push-smoke.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `workflow-phase-git-local-diff-add-commit.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `atomic-config-edit-json.py` | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `high-frequency-json-edit.mdc` | run-lint.py lint-md | ✅ 通过 |
| `high-frequency-task-index.mdc` | run-lint.py lint-md | ✅ 通过 |
| `TASK-TOOLS-INDEX.md` | run-lint.py lint-md | ✅ 通过 |
| `EXEC-CHEATSHEET.md` | run-lint.py lint-md | ✅ 通过 |
| `verified-task-index.json` | run-lint.py lint_json + lint_encoding | ✅ 通过 |
| `atomic-config-edit-json.py`（v1.0.1 加固后） | run-lint.py lint_python + lint_encoding | ✅ 通过 |
| `high-frequency-json-edit.mdc`（加固后） | run-lint.py lint-md | ✅ 通过 |
| `EXEC-CHEATSHEET.md`（加固后） | run-lint.py lint-md | ✅ 通过 |


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 5 个脚本存在 | `Test-Path py-tools/atomic-*.py` / `workflow-phase-*.py` | `True` |
| 2 | 确认 docstring schema 存在 | `Test-Path schema/docs/py-script-docstring-schema.md` | `True` |
| 3 | 确认 lint 通过 | `run-lint.py --files <目标文件>` | 全部通过 |
| 4 | 确认索引已登记 | `atomic-config-edit-json.py --dry-run` 读取 verified-task-index.json | 包含 5 个新条目 |
| 5 | 确认 venv/tmp/ 原文件已清理 | `Get-ChildItem venv/tmp/atomic-*.py` | 无输出 |
| 6 | 确认 .env 无重复 | `Select-String GITHUB_USER_EMAIL .env` | 无匹配 |


## 六、踩坑记录（供后续 session 参考）

### 6.1 edit 改 JSON 反复失败

**现象**：用 `edit` 工具修改 `verified-task-index.json` 时，oldString 与磁盘实际缩进不一致，反复失败。

**根因**：`edit` 工具做字符串替换，JSON 缩进/换行/逗号位置微差即导致不匹配。

**修复方式**：创建 `atomic-config-edit-json.py`，用 Python `json` 模块做结构化修改，不走字符串替换。

### 6.2 Shell 传参中文编码损坏

**现象**：将中文 JSON Patch 直接塞进 `--batch` 参数，执行后中文变成乱码。

**根因**：bash 工具捕获子进程 stdout 时固定按 UTF-8 解码，但 Shell 传参层中文编码不匹配。

**修复方式**：中文内容必须先 `write` 到文件（`venv/tmp/patch.json`），再用 `@file` 传入。

### 6.3 .env 真源重复

**现象**：atomic-git-repo-clone.py 读取 `GITHUB_USER_EMAIL`，但 .env 中只有 `GIT_USER_EMAIL`。

**根因**：临时脚本自创变量名，与既有真源不一致。

**修复方式**：回滚 .env（删除 `GITHUB_USER_EMAIL`），修改 py 脚本读取 `GIT_USER_EMAIL`。

### 6.4 修订联动遗漏

**现象**：迁移 4 个脚本后忘记更新 `verified-task-index.json` 和 `EXEC-CHEATSHEET.md`，用户追问才补。

**根因**：Agent 执行惯性，写脚本后急于验证，跳过索引登记。

**修复方式**：在 docstring schema 中明确「修订联动义务清单」，新增脚本后强制自检三项联动。

### 6.5 .mdc 文件正文 --- 污染

**现象**：`high-frequency-task-index.mdc` 提交后 lint 报错「正文出现 ---」。

**根因**：.mdc 文件使用 `---` 作为章节分隔线，与 frontmatter 定界符冲突。

**修复方式**：`run-lint.py --fix` 自动删除正文中的 `---`，改用空行或 `##` 分隔。

### 6.6 JSON Pointer 语法歧义风险

**现象**：用户担心 Agent 在使用 `atomic-config-edit-json.py` 时，可能因肌肉记忆传入 JSON Path（`$.meta.last_updated`）或 jq（`.meta.last_updated`）风格路径，而非 RFC 6902 JSON Pointer（`/meta/last_updated`）。

**根因**：`--path` 参数名过于通用，缺乏「pointer」语义暗示；文档未明确列出「不要这样做」的反模式。

**修复方式**：
- **方案 A（运行时）**：`_parse_pointer()` 报错信息增加反模式提示，明确告知「不支持 JSON Path / jq 风格」。
- **方案 B（参数名）**：`--path` 更名为 `--json-pointer`，保留 `--path` 作为兼容别名（`dest="path"` 零代码侵入）。
- **方案 C（文档）**：`high-frequency-json-edit.mdc` 和 `EXEC-CHEATSHEET.md` 踩坑速查追加反模式条目，所有示例统一使用 `--json-pointer`。


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 5 个新脚本 | `Remove-Item py-tools/atomic-gh-repo-create.py` 等 |
| 删除 docstring schema | `Remove-Item schema/docs/py-script-docstring-schema.md` |
| 删除 JSON edit mdc | `Remove-Item .cursor/rules/high-frequency-json-edit.mdc` |
| 恢复索引 | 从 `verified-task-index.json.bak` 恢复（atomic-config-edit-json 自动备份） |
| 恢复 EXEC-CHEATSHEET | git checkout 或手动删除新增 Stage |
| 恢复 TASK-TOOLS-INDEX | git checkout 或手动删除新增行 |
| 恢复 .env | 重新添加 `GITHUB_USER_EMAIL`（如需要） |
| 恢复临时脚本 | 从 git history 恢复 `venv/tmp/atomic-*.py` |


## 八、关联文档

| 文档 | 说明 |
|------|------|
| `references/tasks/deploy-git-isolated/schema/docs/py-script-docstring-schema.md` | 本 session 新建的 docstring 与命名规范 |
| `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py` | 本 session 新建的 JSON 编辑工具 |
| `references/env-migrations/env-migration-jywl-settlement-polyrepo-init-2026-07-21-173210.md` | 上游触发源：jywl-settlement polyrepo 初始化时产生的临时脚本 |


## 九、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-22-170521（v1.0.1 加固补丁：2026-07-22-171200） |
| **更新人** | OpenCode Agent Session |
| **变更触发** | 用户要求将临时 atomic 脚本正式化迁移，建立 docstring schema，解决 edit JSON 踩坑；后续用户要求对 JSON Pointer 语法明确性做 A/B/C 三层加固 |
| **下次修订条件** | 新增第 6 种脚本类型；atomic-config-edit-json.py 扩展新操作类型（如 move/copy）；或 JSON Pointer 语法再次引发歧义 |
| **跨环境迁移参考** | 直接复制本文档「文本文件变更清单」中的全部文件到新环境对应路径 |


*文档生成时间：2026-07-22*  
*模板版本：v2*
