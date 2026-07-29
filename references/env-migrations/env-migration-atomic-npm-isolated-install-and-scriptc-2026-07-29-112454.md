---
title: "env-migration: atomic-npm-isolated-install 原子 CLI 新增 + 索引修订联动"
description: "记录 atomic-npm-isolated-install.py v1.2.0 新增、scriptc 隔离安装实测、以及三处工具登记索引的修订联动。"
date: 2026-07-29
meta:
  tags: [env-migration, npm, atomic-cli, scriptc, tool-index]
---

# env-migration-atomic-npm-isolated-install-and-scriptc-2026-07-29-112454

> **Session 主题**：新增 `atomic-npm-isolated-install.py` 原子 CLI（v1.2.0），完成 npm 隔离安装标准化；实测安装 `scriptc@0.0.17` 并沉淀 Windows 踩坑经验；执行三处索引修订联动。


## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 新增 atomic-npm-isolated-install 原子 CLI + scriptc 安装实测 + 索引修订联动 |
| **日期** | 2026-07-29 |
| **文件名时间戳** | `2026-07-29-112454` |
| **触发原因** | 用户要求用 scriptc 编译 TS → Windows 原生可执行文件；过程中发现需要标准化 npm 隔离安装工具 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/` 新增原子脚本；`references/runtime/verified-task-index.json` 更新；`venv/scriptc/` 隔离安装 |
| **风险等级** | 低（新增工具，不破坏既有流程） |


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-npm-isolated-install.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-npm-isolated-install.py` |
| **变更类型** | 新建 |
| **新增内容** | v1.2.0 npm 隔离安装原子 CLI。支持 Local（带 package.json）和 Global（单包）双模式。内置重组安全检查、CWD 切换检查、--show-progress 实时 npm 输出、bin 可用性验证（--version/--help）。生成 JSON manifest。 |
| **作用** | 将 npm 包安全安装到隔离目录，避免污染全局 node_modules 或系统 PATH |
| **验证方式** | `run-lint.py --files atomic-npm-isolated-install.py` 通过；实际安装 scriptc@0.0.17 成功并验证 `scriptc --version` |
| **迁移方式** | 直接复制文件到新环境即可 |

### 2. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 追加 |
| **新增内容** | `available_scripts_and_tools.atomic-npm-isolated-install` 条目；`meta.last_updated` 更新为 `2026-07-29T11:19:20` |
| **插入位置** | `available_scripts_and_tools` 对象末尾（在 `download-article` 之前） |
| **作用** | 将新原子脚本登记到全局工具索引，供 Agent tool-audit 时查询 |
| **验证方式** | `run-lint.py --files verified-task-index.json` 通过（JSON 语法 + 编码） |
| **迁移方式** | 通过 `atomic-config-edit-json.py --batch` 执行，已自动备份 `.bak` |

### 3. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 追加 |
| **新增内容** | 编排 Workflow 表格追加 `atomic-npm-isolated-install.py` 一行 |
| **插入位置** | 1.6 归档 Workflow 后的原子工具表格末尾 |
| **作用** | 本 task 人类速查：新增工具的职责、典型场景、状态 |
| **验证方式** | `run-lint.py --files TASK-TOOLS-INDEX.md` 通过 |
| **迁移方式** | 直接追加行 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | 追加 |
| **新增内容** | 新增 **Stage S8.5: npm 隔离安装**，含 Local 模式和 Global 模式的 Agent/终端双形态命令 |
| **插入位置** | Stage S8（运行时域）末尾，CI/CD 之前 |
| **作用** | 可执行速查：提供可直接复制的命令示例 |
| **验证方式** | `run-lint.py --files EXEC-CHEATSHEET.md` 通过 |
| **迁移方式** | 直接追加章节 |

### 5. 新建 `references/tasks/deploy-git-isolated/docs/research/scriptc-windows-native-build-investigation-2026-07-29-111400.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/research/scriptc-windows-native-build-investigation-2026-07-29-111400.md` |
| **变更类型** | 新建 |
| **新增内容** | scriptc Windows 原生编译踩坑实录：冲动试错 vs 先搜 Issues 的教训 |
| **作用** | 沉淀踩坑经验，防止后续 Agent 重蹈覆辙 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 直接复制 |


## 二、非文本操作（文件系统/隔离安装）

本次 session 涉及 npm 隔离安装，产生**无法被 git 追踪**的目录：

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 隔离安装 | npm registry | `venv/scriptc/` | `atomic-npm-isolated-install.py --mode local --target-dir venv/scriptc --packages scriptc@0.0.17` |
| 目录创建 | — | `venv/scriptc/node_modules/` | Local 模式自动生成 |
| 中间产物 | — | `venv/tmp/.scriptc/fib.ll` | scriptc coverage 生成的 LLVM IR |

> **注意**：`venv/scriptc/` 是隔离安装产物，**不应提交到 git**。若在新环境复现，直接重新执行 atomic-npm-isolated-install 即可，无需复制目录。


## 三、环境变量速查

本次 session **未新增**环境变量注入项。npm 隔离安装依赖现有变量：

```json
"terminal.integrated.env.windows": {
    "PATH": "...;${workspaceFolder}\\venv\\node;...",
    "npm_config_cache": "${workspaceFolder}\\venv\\node\\.npm-cache",
    ...
}
```

> 已有的 `npm_config_cache` 确保 npm 缓存收束到项目内，是隔离安装的前提。


## 四、落盘验证（写入后已执行）

| 文件类型 | 验证工具 | 验证内容 | 结果 |
|---------|---------|---------|------|
| `.md` | `run-lint.py` | frontmatter / 编码 / 链接 | ✅ 全部通过 |
| `.json` | `run-lint.py` | JSON 语法 / 编码 | ✅ 全部通过 |
| `.py` | `run-lint.py` | Python 语法 / 编码 | ✅ 全部通过 |


## 五、验证清单（新环境复现步骤）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 atomic-npm-isolated-install 存在 | `Test-Path "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-npm-isolated-install.py"` | `True` |
| 2 | 确认 verified-task-index.json 已登记 | `grep '"atomic-npm-isolated-install"' verified-task-index.json` | 命中 |
| 3 | 验证 Local 模式安装 | 执行 EXEC-CHEATSHEET Stage S8.5 示例 | `node_modules/` 生成、`--version` 验证通过 |
| 4 | 验证索引可读性 | `run-lint.py --files verified-task-index.json` | 通过 |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 删除原子脚本 | `Remove-Item "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-npm-isolated-install.py"` |
| 恢复索引 | 从 `verified-task-index.json.bak` 恢复，或 `atomic-config-edit-json.py --operation remove --json-pointer "/available_scripts_and_tools/atomic-npm-isolated-install"` |
| 删除 TASK-TOOLS-INDEX 行 | `edit` 移除对应表格行 |
| 删除 EXEC-CHEATSHEET 章节 | `edit` 移除 Stage S8.5 |
| 删除隔离安装产物 | `Remove-Item -Recurse "${devroot}\venv\scriptc"` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-29-112454 |
| **更新人** | Agent (OpenCode / kimi-k2.6) |
| **变更触发** | 用户要求用 scriptc 编译 Windows 原生可执行文件；过程中完成 npm 隔离安装工具改造 |
| **下次修订条件** | atomic-npm-isolated-install.py 功能升级（如新增模式、参数变更）；或 scriptc 官方 Issue #27 合并后重新评估 Windows 支持 |
| **跨环境迁移参考** | 直接复制 atomic-npm-isolated-install.py + 执行索引修订联动三步 |


*文档生成时间：2026-07-29*
*模板版本：v2*
