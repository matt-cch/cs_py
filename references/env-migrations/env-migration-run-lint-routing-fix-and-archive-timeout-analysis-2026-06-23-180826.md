---
title: run-lint.py 路由修复 + 归档超时根因分析 + Agent 目录阅读模式文档
description: run-lint.py .md 文件路由漏调 lint_encoding 修复、docs/ CRLF 批量修复、archive 工作流超时根因定位、新增 Agent 目录阅读次序研究文档
date: 2026-06-23
meta: {}
---

# env-migration: run-lint 路由修复与归档超时根因分析

> **Session 主题**: run-lint.py 路由修复（.md 文件漏调 lint_encoding）+ docs/ CRLF 批量修复 + archive 并行压缩超时根因分析 + 新增 Agent 目录阅读模式研究文档
> **日期**: 2026-06-23
> **文件名时间戳**: `2026-06-23-180826`
> **触发原因**: 用户质疑 Agent 为何对 .md 文件只跑 md_lint 不跑 lint_encoding，暴露路由表设计缺陷；后续 archive 全量并行执行超时，暴露 7z 更新模式陷阱
> **影响范围**: `run-lint.py`（路由逻辑）、`high-frequency-verify-runtime.mdc`（文档）、`docs/`（换行符）、`references/env-migrations/README.md`（导航）
> **风险等级**: 低（修复缺陷 + 文档沉淀）


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | 修改 |
| **问题描述** | `.md` / `.mdc` 文件在 `EXT_TO_PLUGIN` 中优先映射到 `md_lint`，导致 `lint_encoding` 永远走不到 |
| **修复内容** | 路由逻辑从 `if/elif` 一对一映射改为 `set` 收集一对多映射：`.md` / `.mdc` 同时命中 `md_lint` + `lint_encoding` |
| **插入位置** | `run_files_via_py_lib()` 函数，文件路由分组逻辑（第 120-132 行） |
| **作用** | 单条 `run-lint.py --files x.md` 命令即可同时检查 frontmatter + 编码/换行符 |
| **验证方式** | `run-lint.py --files agent-directory-reading-pattern.md` → 同时输出 `md_lint` 和 `lint_encoding` 两个插件的执行结果 |
| **迁移方式** | 直接覆盖 |

### 2. 修改 `.cursor/rules/high-frequency-verify-runtime.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-verify-runtime.mdc` |
| **变更类型** | 修改 |
| **修改内容** | 自动路由扩展名映射表中 `.md` 行从 `md_lint` 改为 `md_lint + lint_encoding` |
| **作用** | 文档与代码实现对齐 |
| **迁移方式** | 直接覆盖 |

### 3. 批量修复 `references/tasks/deploy-git-isolated/docs/` 下全部 `.md` 文件换行符

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/**/*.md`（16 个文件） |
| **变更类型** | 修改（CRLF → LF） |
| **问题描述** | 历史遗留：全部 13 个 `.md` 文件（含根级 + 子目录）使用 CRLF 换行符，违反 `markdown-docs-format.mdc` |
| **修复方式** | `lint_encoding.py --dir docs/ --fix` 一键修复 |
| **作用** | 全部 `.md` 文件换行符合规（CRLF=0, LF>0） |
| **验证方式** | `lint_encoding.py --dir docs/` → 违规文件 0 个 |
| **迁移方式** | 无需手动操作，工具已修复 |

### 4. 新增 `references/tasks/deploy-git-isolated/docs/research/agent-directory-reading-pattern.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/research/agent-directory-reading-pattern.md` |
| **变更类型** | 新增 |
| **内容** | Agent 被指向陌生目录时的五层自然阅读次序（目录扫描 → 入口文档 → 机器真源 → 父目录追溯 → 按需深入） |
| **作用** | 认知模式文档，供后续 Agent 参考 |
| **验证方式** | `run-lint.py --files` 通过 md_lint + lint_encoding 双重检查 |
| **迁移方式** | 直接复制 |

### 5. 修改 `references/tasks/deploy-git-isolated/docs/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/README.md` |
| **变更类型** | 修改 |
| **修改内容** | 导航表中追加 `agent-directory-reading-pattern.md` 条目，版本升至 v1.2 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作（踩坑记录）

### archive_project.py 并行压缩超时根因

| 操作类型 | 说明 |
|---------|------|
| **现象** | `archive_project.py --group cs_py venv` 中 cs_py 组压缩耗时 400+ 秒，用户中断 |
| **根因** | 7z 的**更新模式**：当输出文件 `cs_py.7z` 已存在时，`7z.exe a` 会尝试更新已有归档（读取旧归档 + 合并新文件），而非重建。cs_py 组 40,938 文件 / 514MB，更新模式极慢 |
| **对比验证** | 单独执行 `archive_cs_py.py`（输出文件不存在）→ 耗时 79s；单独执行 `archive_venv.py` → 耗时 71s |
| **结论** | **禁止**在已有 `.7z` 文件存在时执行 archive；如必须重新归档，应先删除旧文件或加 `--force` 参数 |


## 三、环境变量速查

无新增环境变量。


## 四、落盘验证

```powershell
# Markdown 文件编码检查
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "D:\pjt\cursor\cs_py" --files "D:\pjt\cursor\cs_py\references\env-migrations\env-migration-run-lint-routing-fix-and-archive-timeout-analysis-2026-06-23-180826.md"

# run-lint.py 自身语法检查
& "D:\pjt\cursor\cs_py\venv\py\python.exe" -m py_compile "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py"
```


## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | run-lint.py .md 双重检查 | `run-lint.py --files x.md` | 同时输出 `md_lint` + `lint_encoding` |
| 2 | docs/ 换行符合规 | `lint_encoding.py --dir docs/` | 违规文件 0 个 |
| 3 | archive 单组执行 | `archive_cs_py.py` / `archive_venv.py` | 各 80s 左右完成 |
| 4 | archive 全量先删旧包 | 先 `Remove-Item cs_py.7z venv.7z` 再 `archive_project.py` | 避免更新模式陷阱 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 run-lint.py 旧路由 | `git checkout -- scripts/py-tools/run-lint.py` |
| 恢复 mdc 文档 | `git checkout -- .cursor/rules/high-frequency-verify-runtime.mdc` |
| 恢复 docs/ 换行符 | 不可回滚（CRLF→LF 是单向修复，不影响内容） |
| 删除新文档 | `Remove-Item docs/research/agent-directory-reading-pattern.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-23-180826 |
| **更新人** | Agent Session |
| **变更触发** | 用户质疑 lint 路由不完整 + archive 超时 |
| **下次修订条件** | run-lint.py 新增更多文件类型的多重插件映射时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-23*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
