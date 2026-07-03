---
title: deploy-git-isolated 脚本中文乱码修复与 BOM 补齐
description: 修复 deploy-git-isolated 下多个 .ps1 脚本在 Agent bash 调用时中文输出乱码的问题，补齐 github-init-empty-repo.ps1 缺失的 UTF-8 BOM。
date: 2026-06-16
---

# `env-migration-deploy-git-encoding-fix-and-bom-2026-06-16-231008.md`

> **文档性质**：环境迁移记录。聚焦开发环境既有脚本的编码问题修复，非业务功能交付。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | deploy-git-isolated 脚本中文乱码修复 + github-init-empty-repo.ps1 BOM 缺失补齐 |
| **日期** | 2026-06-16 |
| **文件名时间戳** | `2026-06-16-231008` |
| **触发原因** | 用户发现 `github-safety-check.ps1` 执行时报错，且多个脚本在 bash 调用层中文输出乱码 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/` 下 11 个 `.ps1` 文件 |
| **风险等级** | 低（纯编码修复，无逻辑变更） |


## 一、文本文件变更清单

### 1. 修改 `github-safety-check.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-safety-check.ps1` |
| **变更类型** | 修改 |
| **作用** | 修复缺少 UTF-8 BOM 导致的 PowerShell 5.1 解析失败；修复编码切换时机 |

**具体修改**：

- **补 UTF-8 BOM**：原始文件无 BOM，PowerShell 5.1 误判为 ANSI/GBK，中文注释解析失败，`. $libPath` 执行报错。
- **编码切换前移**：在 `. $libPath` 之前加入 `[Console]::OutputEncoding = UTF8` 和 `$OutputEncoding = UTF8`，确保 `github-lib` 插件加载时的 `Write-Host` 中文输出不被 bash 捕获层误解码。


### 2. 修改 `github-init-empty-repo.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-init-empty-repo.ps1` |
| **变更类型** | 修改 |
| **作用** | 补齐缺失的 UTF-8 BOM |

**具体修改**：原始文件无 BOM，但含大量中文内容。补 BOM 后通过 `lint-ps1.ps1` 验证（exit 0）。


### 3. 修改 Step 1-8 脚本（`github-step-01-init.ps1` ~ `github-step-08-upstream.ps1`）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-step-0[1-8]-*.ps1` |
| **变更类型** | 批量修改（共 8 个文件） |
| **作用** | 统一修复编码切换时机 |

**具体修改**：在每个 step 脚本的 `. $libPath` 之前，新增两行原生编码切换：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

**原因**：`github-lib.ps1` 在点源导入时会输出插件加载信息（如 `拓扑排序结果`），这些信息发生在 `Switch-ToUtf8` 之前，导致 bash 捕获层按 GBK 解码出现乱码。提前切换编码后，`github-lib` 加载阶段的中文也能正确输出。

> **重要**：本次修改**不涉及** `github-lib.ps1` 本身，也不修改 `lib-plugins/encoding.ps1` 等共享库。共享库保持不动，仅修改调用者。


## 二、非文本操作

无。本次不涉及文件复制、缓存迁移或目录创建。


## 三、环境变量/配置速查

无需变更 `.vscode/settings.json` 或 `.env`。本次为脚本编码修复，不涉及环境变量。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `check-file-encoding.ps1` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.ps1`（修改后的脚本） | `lint-ps1.ps1` | 语法无错误 | `[OK]` exit 0 |
| `.ps1`（修改后的脚本） | 手动执行 | 中文输出正常、无报错 | 功能正常 |

**执行命令**（使用现成脚本，禁止现写）：

```powershell
# Markdown 编码检查
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" -Path "${devroot}\references\env-migrations\env-migration-deploy-git-encoding-fix-and-bom-2026-06-16-231008.md"

# PS1 语法检查（对修改后的关键脚本抽样验证）
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-safety-check.ps1"
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-init-empty-repo.ps1"

# 功能验证（抽样执行）
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-safety-check.ps1"
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"
```


## 五、验证清单（新环境/复现时）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---|---------|----------|---------|
| 1 | 确认 safety-check 无解析错误 | `lint-ps1.ps1 -Path github-safety-check.ps1` | exit 0 |
| 2 | 确认 safety-check 中文正常 | 直接执行脚本 | `Git 安全检查` 标题中文正常 |
| 3 | 确认 step-01 中文正常 | 直接执行脚本 | `git init + 身份配置` 标题中文正常 |
| 4 | 确认 github-lib 加载中文正常 | 观察插件列表输出 | `拓扑排序结果` `所有插件加载完成` 中文正常 |
| 5 | 确认 init-empty-repo 有 BOM | `ReadAllBytes` 前 3 字节 | `EF BB BF` |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 step 脚本编码切换位置 | 将 `. $libPath` 前的两行 `[Console]::OutputEncoding = UTF8` 删除（注意：删除后 github-lib 加载阶段会恢复乱码，但脚本功能不受影响） |
| 恢复 safety-check BOM | 若需回滚，从 git 历史恢复旧版 |
| 恢复 init-empty-repo BOM | 若需回滚，从 git 历史恢复旧版 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-16-231008 |
| **更新人** | Agent Session |
| **变更触发** | 用户发现 safety-check 报错 + 脚本中文乱码，要求排查修复 |
| **下次修订条件** | 若新增 step 脚本未遵循编码前置规则 |
| **跨环境迁移参考** | 直接复制修改后的 `.ps1` 文件，无需额外环境配置 |


*文档生成时间：2026-06-16-231008*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
