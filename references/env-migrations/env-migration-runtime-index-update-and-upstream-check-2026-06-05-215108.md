---
title: 真源索引更新与上游工具链检测下载
description: 本次 session 执行真源检测并同步更新 verified-runtime-index.json，检测 Node.js / Chromium 上游最新版本并下载到临时目录，同时修正 Cursor 安装路径真源。
date: 2026-06-05
---

# env-migration-runtime-index-update-and-upstream-check-2026-06-05-215108

## 元信息

| 字段 | 值 |
|------|------|
| **Session 主题** | 真源索引更新 + Node.js / Chromium 上游版本检测与下载 + Cursor 路径修正 |
| **日期** | 2026-06-05 |
| **文件名时间戳** | `2026-06-05-215108` |
| **触发原因** | 1) 真源检测发现 `verified-runtime-index.json` 与磁盘状态不一致；2) 用户要求检测并下载 node / chromium 最新版本；3) 发现 Cursor 安装在 `D:\Program Files\cursor\` 而非索引中的 `C:\Program Files\cursor\` |
| **影响范围** | `references/runtime/verified-runtime-index.json`、下载临时目录 `D:\download\` |
| **风险等级** | 低（仅索引更新和临时下载，未执行实际替换） |


## 一、文本文件变更清单

### 1. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改` |
| **作用** | 同步真源检测结果，修正过时/错误的路径和版本信息 |
| **验证方式** | 运行 `verify-runtime.ps1`，对比输出与索引字段是否一致 |
| **迁移方式** | 直接覆盖（git 已追踪） |

**具体字段变更**：

| 字段路径 | 旧值 | 新值 | 说明 |
|----------|------|------|------|
| `meta.last_updated` | `2026-06-05T21:25:47` | `2026-06-05T21:50:34` | 刷新检测时间 |
| `roots.vaultroot.verified_at` | `2026-05-30T10:45:18` | `2026-06-05T21:50:34` | 重新检测，目录仍不存在 |
| `toolchain.node.version` | `v26.2.0` | `v26.3.0` | 磁盘实际版本 |
| `toolchain.npm.version` | `11.13.0` | `11.16.0` | 磁盘实际版本 |
| `toolchain.cursor.executable` | `null` | `D:\Program Files\cursor\Cursor.exe` | 修正为 D 盘实际路径 |
| `toolchain.cursor.cmd_wrapper` | `null` | `D:\Program Files\cursor\resources\app\bin\cursor.cmd` | 同步修正 |
| `toolchain.cursor.version` | `null` | `3.6.21` | 实测版本 |
| `toolchain.cursor.package_json` | `C:\Program Files\cursor\resources\app\package.json` | `D:\Program Files\cursor\resources\app\package.json` | 同步修正 |
| `toolchain.cursor.candidate[d_system_install]` | 新增 | `path=D:\Program Files\cursor\`, `status=verified_hit` | 新增候选路径 |
| `toolchain.chromium.version` | `144.0.7507.0` | `150.0.7834.0` | 磁盘实际版本 |
| `toolchain.chromium.verified_at` | `2026-06-03T11:54:17` | `2026-06-05T21:50:34` | 刷新 |
| `github_connectivity.api_direct.api_search.latency_ms` | `878` | `812` | 最新实测 |
| `github_connectivity.api_direct.api_issues.latency_ms` | `899` | `856` | 最新实测 |
| `github_connectivity.web_direct.web_search_issues` | `HTTP=200 LATENCY=1406ms` | `HTTP=TIMEOUT/ERR LATENCY=15015ms` | 本次检测超时 |
| `github_connectivity.web_direct.web_issues_list` | `HTTP=200 LATENCY=1122ms` | `HTTP=TIMEOUT/ERR LATENCY=15024ms` | 本次检测超时 |


## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 下载（保留） | 阿里云 nodejs-release | `D:\download\node-v26.3.0-extracted` | Node.js v26.3.0 win-x64，已验证版本 |
| 下载（保留） | 淘宝 npmmirror | `D:\download\chromium-r1627931-extracted` | Chromium r1627931 (150.0.7834.0)，已验证版本 |

> **注意**：本次 session **未执行替换**。两个工具的本地安装路径保持不变：
> - Node.js 仍位于 `D:\pjt\cursor\cs_py\venv\node\` (v26.2.0)
> - Chromium 仍位于 `D:\download\chrome-win\` (144.0.7507.0)


## 三、环境变量速查

本次 session 未修改 `.vscode/settings.json` 或环境变量配置。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认索引已同步 | `powershell -ExecutionPolicy Bypass -File "references/runtime/verify-runtime.ps1"` | 通过/变更/失败项与索引一致 |
| 2 | 确认 node 版本 | `D:\pjt\cursor\cs_py\venv\node\node.exe -e "console.log(process.version)"` | 输出 `v26.3.0`（若已替换）或 `v26.2.0`（若未替换） |
| 3 | 确认 chromium 版本 | `(Get-ItemProperty 'D:\download\chrome-win\chrome.exe').VersionInfo.ProductVersion` | 输出 `150.0.7834.0`（若已替换）或 `144.0.7507.0`（若未替换） |
| 4 | 确认 cursor 路径 | `Test-Path -LiteralPath 'D:\Program Files\cursor\Cursor.exe'` | `True` |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复索引 | `git checkout references/runtime/verified-runtime-index.json` |
| 删除临时下载 | `Remove-Item -Recurse -Force "D:\download\node-v26.3.0-extracted"`；`Remove-Item -Recurse -Force "D:\download\chromium-r1627931-extracted"` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-05-215108 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指令「实测真源一下」「检测和下载 node, chrome 最新版本」 |
| **下次修订条件** | 执行 Node.js / Chromium 实际替换后，需再次运行真源检测并更新索引 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-05*
