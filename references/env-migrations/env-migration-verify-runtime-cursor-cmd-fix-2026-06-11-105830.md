---
title: verify-runtime.ps1 cursor.cmd 联动检测修复
description: 修复真源检测脚本中 candidate 命中后未联动检测 cursor.cmd 版本的 bug，补全头部注释
date: 2026-06-11
---

# env-migration-verify-runtime-cursor-cmd-fix-2026-06-11-105830

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | verify-runtime.ps1 cursor 版本检测修复 + 头部注释规范化 |
| **日期** | 2026-06-11（frontmatter；文件名时间戳见上表） |
| **文件名时间戳** | `2026-06-11-105830`（与磁盘文件名后缀一致） |
| **触发原因** | 真源检测发现 Cursor 从 D 盘迁移至 C 盘后，candidate[default_system_install] 命中但 cursor.version 返回 null |
| **影响范围** | `references/runtime/verify-runtime.ps1`（脚本逻辑修复）、`references/runtime/verified-runtime-index.json`（索引同步更新） |
| **风险等级** | 低（仅影响检测脚本，不涉及业务代码） |


## 一、文本文件变更清单

### 1. 修改 `references/runtime/verify-runtime.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime.ps1` |
| **变更类型** | `修改` |
| **新增/修改内容** | ① 添加标准头部注释（`<# .SYNOPSIS ... #>` 格式）；② 修复 cursor 版本检测逻辑：candidate 命中后自动沿候选路径拼接 `cursor.cmd` 检测版本 |
| **插入位置** | 文件头部（注释）、第 287-339 行（cursor case） |
| **作用** | 当 cursor 主路径失效、candidate 命中时，自动沿候选路径检测版本，不再返回 null |
| **验证方式** | 重新执行 `verify-runtime.ps1`，cursor.version 不再出现在变更/失败项中 |
| **迁移方式** | 直接覆盖 |

### 2. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | 同步真源检测结果：cursor.executable 迁移至 C 盘、candidate 状态更新、chromium 版本更新、github_connectivity latency 更新 |
| **插入位置** | cursor 节、chromium 节、github_connectivity 节 |
| **作用** | 保持索引与磁盘实测一致 |
| **验证方式** | 读取 JSON 确认 cursor.executable 指向 C 盘路径 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 是否涉及文件复制、缓存迁移、目录创建等**无法被 git 追踪**的操作？

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| （无） | — | — | 本次仅修改脚本和索引文件，无文件系统操作 |


## 三、环境变量速查

本次变更不涉及环境变量修改。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认脚本语法正确 | `powershell.exe -ExecutionPolicy Bypass -File "schema\tool\lint-ps1.ps1" -Path "references\runtime\verify-runtime.ps1"` | exit 0，无输出 |
| 2 | 确认文件编码正确 | `powershell.exe -ExecutionPolicy Bypass -File "schema\tool\check-file-encoding.ps1" -Path "references\runtime\verify-runtime.ps1"` | BOM=yes, DOUBLE_BOM=no |
| 3 | 确认真源检测通过 | `powershell.exe -ExecutionPolicy Bypass -File "references\runtime\verify-runtime.ps1"` | cursor.version 不出现在变更/失败项中 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 verify-runtime.ps1 | 从 git 恢复上一版本：`git checkout HEAD~1 -- references/runtime/verify-runtime.ps1` |
| 恢复 verified-runtime-index.json | 从 git 恢复上一版本：`git checkout HEAD~1 -- references/runtime/verified-runtime-index.json` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-11-105830 |
| **更新人** | Agent (OpenCode) |
| **变更触发** | 真源检测实测发现 cursor.version 返回 null |
| **下次修订条件** | verify-runtime.ps1 新增其他工具的 candidate 联动检测逻辑时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-11*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
