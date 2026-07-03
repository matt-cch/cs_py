---
title: 运行时检测/下载全局入口对齐
description: 将全局高频任务 mdc 的执行脚本入口从旧单体脚本对齐到 task 原子脚本体系，旧路径标记 legacy。
date: 2026-07-02
meta:
  version: 1.0.0
---

# env-migration-runtime-verify-download-entry-alignment-2026-07-02-173105

| 字段 | 值 |
|------|-----|
| **Session 主题** | 运行时检测/下载全局入口对齐（mdc → task 原子脚本体系） |
| **日期** | 2026-07-02 |
| **文件名时间戳** | `2026-07-02-173105` |
| **触发原因** | 用户要求「一说到 task/ 下的运行时版本检测和下载，能够马上联系到正确的执行工具、步骤和路径」 |
| **影响范围** | `.cursor/rules/high-frequency-verify-runtime.mdc`、`.cursor/rules/high-frequency-download-runtime.mdc`、`references/runtime/verified-task-index.json`、`references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **风险等级** | 低（仅文档/索引路径变更，无文件系统操作） |


## 一、文本文件变更清单

### 1. 修改 `.cursor/rules/high-frequency-verify-runtime.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-verify-runtime.mdc` |
| **变更类型** | `修改` |
| **新增/修改内容** | 执行脚本从 `references/runtime/verify-runtime.py` 改为 `references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py`；标准命令同步更新；旧 `verify-runtime.py`/`verify-runtime.ps1` 降级为 legacy fallback |
| **作用** | 用户触发「检查真源」时，Agent 第一时间执行 task 原子脚本体系而非旧单体脚本 |
| **验证方式** | 读取 mdc 确认「执行脚本」行指向 `wf-verify-runtime.py` |
| **迁移方式** | 可直接覆盖 |

### 2. 修改 `.cursor/rules/high-frequency-download-runtime.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-download-runtime.mdc` |
| **变更类型** | `修改` |
| **新增/修改内容** | 入口脚本从 `references/runtime/download-runtime-tool.py` 改为 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py`；全部 CLI 示例同步更新（标准命令、工具速查表、指定版本、自动替换）；旧路径降级为 legacy |
| **作用** | 用户触发「下载运行时」时，Agent 第一时间执行 task 原子脚本体系 |
| **验证方式** | 读取 mdc 确认所有命令示例含 `wf-download-runtime.py` 而非 `download-runtime-tool.py` |
| **迁移方式** | 可直接覆盖 |

### 3. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | `verify-runtime` 条目补 `status: "legacy"`，名称改为「真源检测脚本（legacy）」；`download-runtime-tool` 条目补 `status: "legacy"`，名称改为「运行时下载脚本（Python 版，legacy）」 |
| **作用** | 索引层级明确区分新旧两套运行时工具，避免 Agent 误选旧入口 |
| **验证方式** | `grep '"status": "legacy"' verified-task-index.json` 命中 3 处（含原有的 `download-runtime-tool-legacy`） |
| **迁移方式** | 可直接覆盖 |

### 4. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | 第 2 节「外部通用工具引用」中运行时工具指向新路径；第 3 节「边界矩阵」中「真源扫描」「下载 MinGit」指向 `wf-verify-runtime.py` / `wf-download-runtime.py` |
| **作用** | task 内部文档与全局入口保持一致 |
| **验证方式** | 搜索 `wf-verify-runtime` 和 `wf-download-runtime` 命中 |
| **迁移方式** | 可直接覆盖 |


## 二、非文本操作（文件系统/缓存迁移）

无。本次 session 全部为代码/文档修改，无文件复制、缓存迁移或目录创建。


## 三、环境变量速查

无新增环境变量。本次变更不涉及 `.vscode/settings.json` 或终端环境变量修改。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.mdc` | `run-lint.py` (md_lint + lint_encoding) | frontmatter、BOM、CRLF、LF | BOM=no, CRLF=0, LF>0 |
| `.md` | `run-lint.py` (md_lint + lint_encoding) | frontmatter、BOM、CRLF、LF | BOM=no, CRLF=0, LF>0 |
| `.json` | `run-lint.py` (lint_json) | JSON 语法正确性 | `[OK]` 无解析错误 |

**执行结果**：全部通过 ✅


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 mdc 入口已更新 | `grep 'wf-verify-runtime.py' .cursor/rules/high-frequency-verify-runtime.mdc` | 命中标准命令行 |
| 2 | 确认 mdc 下载入口已更新 | `grep 'wf-download-runtime.py' .cursor/rules/high-frequency-download-runtime.mdc` | 命中标准命令行 |
| 3 | 确认索引 legacy 标记 | `grep '"status": "legacy"' references/runtime/verified-task-index.json` | 命中 3 处 |
| 4 | 确认 task 索引对齐 | `grep 'wf-verify-runtime' references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` | 命中边界矩阵 |
| 5 | lint 验证 | `run-lint.py --files <上述4个文件>` | 全部通过 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 mdc | 从 git 历史恢复 `.cursor/rules/high-frequency-verify-runtime.mdc` 和 `high-frequency-download-runtime.mdc` |
| 恢复索引 | 从 git 历史恢复 `references/runtime/verified-task-index.json` |
| 恢复 task 索引 | 从 git 历史恢复 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-02-173105 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求运行时检测/下载入口与 task 原子脚本体系对齐 |
| **下次修订条件** | wf-runtime-full.py 验证通过后提升为推荐入口；新增运行时工具需同步更新 mdc 和索引 |
| **跨环境迁移参考** | 直接覆盖文件 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-02*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
