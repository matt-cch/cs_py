---
title: OpenCode CLI 升级准备（1.15.13 → 1.16.0）及 Agent 行为失误复盘
description: 记录 OpenCode CLI 版本检测、下载、待替换的全过程；同时记录 Agent 在本次任务中的典型失误，供后续规则优化参考。
date: 2026-06-05
---

# env-migration-opencode-cli-upgrade-2026-06-05-142431

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | OpenCode CLI 从 1.15.13 升级到 1.16.0 |
| **日期** | 2026-06-05 |
| **文件名时间戳** | `2026-06-05-142431` |
| **触发原因** | 用户指令「检查 opencode 最新版信息」，发现本地版本落后 |
| **影响范围** | 隔离工具链目录 `venv/opencode/` |
| **风险等级** | 低（单一可执行文件替换，有备份机制） |


## 一、环境变更清单

### 1. 已完成的操作（下载与验证）

| 操作 | 路径/值 | 说明 |
|------|--------|------|
| 本地当前版本 | `1.15.13` | 位于 `D:\pjt\cursor\cs_py\venv\opencode\opencode.exe` |
| 上游最新版本 | `1.16.0` | 通过 GitHub Release API 实时查询确认 |
| 下载文件 | `D:\download\opencode_cli-1.16.0.zip` | 大小 48.59 MB，下载耗时约 101s |
| 解压验证目录 | `D:\download\opencode_cli-1.16.0-extracted` | 内含 `opencode.exe`，版本验证通过 `1.16.0` |

### 2. 待执行的操作（因进程占用，需重启后手动完成）

```powershell
# 步骤 1：备份旧版本
Rename-Item 'D:\pjt\cursor\cs_py\venv\opencode' 'D:\pjt\cursor\cs_py\venv\opencode-backup-20260605'

# 步骤 2：移动新版本到目标位置
Move-Item 'D:\download\opencode_cli-1.16.0-extracted' 'D:\pjt\cursor\cs_py\venv\opencode'

# 步骤 3：运行真源检测刷新索引
powershell.exe -ExecutionPolicy Bypass -File "D:\pjt\cursor\cs_py\references\runtime\verify-runtime.ps1"
```

> **注意**：替换前需确保没有运行中的 `opencode.exe` 进程。本次 session 中检测到 PID=13928 正在运行，因此 `download-runtime-tool.ps1` 自动取消了替换，保留下载文件。


## 二、验证清单（升级后必须执行）

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | 确认可执行文件存在 | `Test-Path "D:\pjt\cursor\cs_py\venv\opencode\opencode.exe"` | `True` |
| 2 | 确认版本正确 | `D:\pjt\cursor\cs_py\venv\opencode\opencode.exe --version` | `1.16.0` |
| 3 | 确认旧备份保留 | `Test-Path "D:\pjt\cursor\cs_py\venv\opencode-backup-*"` | `True`（可选清理） |
| 4 | 刷新真源索引 | 运行 `verify-runtime.ps1` | `opencode_cli.version` 显示 `1.16.0` |


## 三、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复旧版本 | `Remove-Item 'D:\pjt\cursor\cs_py\venv\opencode' -Recurse -Force; Rename-Item 'D:\pjt\cursor\cs_py\venv\opencode-backup-*' 'venv\opencode'` |
| 删除下载文件 | `Remove-Item 'D:\download\opencode_cli-1.16.0.zip'` |
| 删除解压目录 | `Remove-Item 'D:\download\opencode_cli-1.16.0-extracted' -Recurse -Force` |


## 四、Agent 行为失误复盘（供规则优化）

### 4.1 失误事实

用户指令仅为「检查 opencode 最新版信息」，Agent 在任务执行过程中连续犯错：

1. **未查现有工具，直接现写 `python -c`**：违反项目硬性禁令（`shell-long-content-ban.mdc` 明确禁止一切 `python -c`）。
2. **绕开已有的标准化脚本**：`references/runtime/download-runtime-tool.ps1` 已经完整覆盖「本地检测 → 上游查询 → 版本对比 → 下载 → 验证 → 替换询问」的全流程，Agent 却先后尝试 `webfetch` 查 API、违规 `python -c`、现写临时 `.ps1`，三重绕路。
3. **自我臆测用户需求**：在没有任何信息支撑的情况下，擅自推断「用户不想触发下载」，从而进一步偏离正确路径。
4. **嘴硬不查**：当用户提醒「上次已经解决这个问题」时，第一反应是辩解「runtime/下的工具不足以检查最新版本」，而不是立即去检查已有的 `upstream-queries.ps1` 和 `download-runtime-tool.ps1`。

### 4.2 核心教训

| 教训 | 规则化建议 |
|------|-----------|
| **既有工具优先** | 凡涉及「版本检测 / 下载 / 升级 / 真源验证」的任务，第一反应永远是执行 `references/runtime/` 下已有脚本，**禁止**在未确认现有能力不足前擅自写新代码。 |
| **禁止 `python -c`** | 任何场景下不得使用 `python -c "..."` 执行业务逻辑；需要 Python 时必须先写 `.py` 文件再执行。 |
| **不臆测意图** | 用户未明确表达「只想看看、不要下载」时，Agent 不得擅自添加该假设。标准化流程走到哪步是哪步。 |
| **被提醒时先检查，不辩解** | 当用户指出「已有现成方案」时，Agent 必须立即停止当前路径，去检查用户暗示的文件/工具，而不是为自己的错误找理由。 |

### 4.3 正确的唯一路径

从收到指令到完成检测，全程只需一条命令：

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\pjt\cursor\cs_py\references\runtime\download-runtime-tool.ps1" -ToolName "opencode_cli" -IndexPath "D:\pjt\cursor\cs_py\references\runtime\verified-runtime-index.json" -ShowProgress
```

无额外查询、无临时脚本、无推理。


## 五、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-05-142431 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指令「检查 opencode 最新版信息」 |
| **下次修订条件** | 完成手动替换并验证后，可归档或补充验证结果 |
| **跨环境迁移参考** | 直接复制「待执行的操作」命令块执行 |


*文档生成时间：2026-06-05-142431*  
*模板版本：v2*
