---
title: 运行时工具链检测与下载（opencode / node / chromium）
description: 执行真源检测发现 opencode_cli 可更新、node 和 chromium 缺失，使用 download-runtime-tool.py 完成三工具下载与验证。
date: 2026-06-26
meta:
  version: 1.0.0
---

# 运行时工具链检测与下载

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 运行时工具链检测与下载（opencode / node / chromium） |
| **日期** | 2026-06-26 |
| **文件名时间戳** | `2026-06-26-173243` |
| **触发原因** | 用户要求检测 opencode、chrome、node.js 版本并下载最新版 |
| **影响范围** | `D:\download\` 下载缓存、`verified-runtime-index.json` 真源索引更新 |
| **风险等级** | 低（仅下载到缓存目录，未执行替换） |


## 一、文本文件变更清单

### 1. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | 更新 `last_updated`、`toolchain` 下各工具的 `verified_at`、`version`、`status`、`upstream_version`、`local_error` 等字段 |
| **作用** | 同步真源检测实测结果到索引，供下游脚本和 Agent 引用 |
| **验证方式** | `run-lint.py --profile lint-json` 验证通过 |
| **迁移方式** | 已由真源检测脚本自动更新，新环境直接复用即可 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 涉及以下工具下载，全部保留在 `D:\download\` 缓存目录，未替换到 `venv/` 或 `toolchainroot/`：

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 下载 | GitHub Release (via gh-proxy.com) | `D:\download\opencode_cli-1.17.11.zip` | opencode_cli 1.17.11 |
| 解压 | — | `D:\download\opencode_cli-1.17.11-extracted\` | 可执行文件验证通过 |
| 下载 | 阿里云 nodejs-release | `D:\download\node-v26.4.0.zip` | Node.js v26.4.0 |
| 解压 | — | `D:\download\node-v26.4.0-extracted\` | 可执行文件验证通过 |
| 下载 | npmmirror Chrome for Testing | `D:\download\chromium-151.0.7914.0.zip` | Chromium 151.0.7914.0 |
| 解压 | — | `D:\download\chromium-151.0.7914.0-extracted\` | 可执行文件验证通过 |

### 版本对比汇总

| 工具 | 本地版本 | 上游最新版 | 状态 |
|------|---------|-----------|------|
| opencode_cli | 1.17.7 | 1.17.11 | 可更新 |
| node | 缺失 | v26.4.0 | 需下载 |
| chromium | 缺失 | 151.0.7914.0 | 需下载 |

### 下载命令复现

```powershell
# opencode_cli（需代理，GitHub Release 直连不稳定）
"N" | & "${devroot}\venv\py\python.exe" "${devroot}\references\runtime\download-runtime-tool.py" `
    --tool-name "opencode_cli" `
    --index-path "${devroot}\references\runtime\verified-runtime-index.json" `
    --show-progress --proxy "gh-proxy.com"

# node（阿里云直链）
"N" | & "${devroot}\venv\py\python.exe" "${devroot}\references\runtime\download-runtime-tool.py" `
    --tool-name "node" `
    --index-path "${devroot}\references\runtime\verified-runtime-index.json" `
    --show-progress

# chromium（npmmirror 直链）
"N" | & "${devroot}\venv\py\python.exe" "${devroot}\references\runtime\download-runtime-tool.py" `
    --tool-name "chromium" `
    --index-path "${devroot}\references\runtime\verified-runtime-index.json" `
    --show-progress
```

> **注意**：`${devroot}` 需替换为实际路径。`"N" |` 表示只下载+解压验证，不替换旧版本。如需替换，改为 `"Y" |` 或在提示时手动输入 `Y`。


## 三、环境变量速查

无新增环境变量。本次操作为纯工具链下载，不涉及 `.vscode/settings.json` 或终端环境变量变更。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文件） | `check-file-encoding.ps1` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 opencode 下载文件存在 | `Test-Path "D:\download\opencode_cli-1.17.11-extracted\opencode.exe"` | `True` |
| 2 | 确认 node 下载文件存在 | `Test-Path "D:\download\node-v26.4.0-extracted\node-v26.4.0-win-x64\node.exe"` | `True` |
| 3 | 确认 chromium 下载文件存在 | `Test-Path "D:\download\chromium-151.0.7914.0-extracted\chrome-win64\chrome.exe"` | `True` |
| 4 | 确认 ZIP 文件完整性 | `Test-Path "D:\download\opencode_cli-1.17.11.zip"` 等 | `True` |
| 5 | 真源检测验证 | 执行 `verify-runtime.py` | opencode 显示 outdated，node/chromium 显示 missing |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除下载文件 | `Remove-Item -Recurse "D:\download\opencode_cli-1.17.11*"`、`Remove-Item -Recurse "D:\download\node-v26.4.0*"`、`Remove-Item -Recurse "D:\download\chromium-151.0.7914.0*"` |
| 恢复旧版 opencode | 若已替换，从 `venv\opencode-backup` 恢复 |
| 恢复旧版 node | 若已替换，从 `venv\node-backup` 恢复 |
| 恢复旧版 chromium | 若已替换，从 `toolchainroot\chrome-win64-backup` 恢复 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-26-173243 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求检测并下载 opencode、chrome、node.js 最新版 |
| **下次修订条件** | 执行替换安装后更新替换路径与验证步骤 |
| **跨环境迁移参考** | 直接复现「下载命令复现」节中的命令，替换 `${devroot}` 为实际路径 |


*文档生成时间：2026-06-26*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
