---
title: 版本获取脚本体系建立与编码修复
description: 记录一次 session 产生的环境级变更（配置、环境变量、缓存迁移等），供 human/agent 在新开发环境复现。
date: 2026-06-11
---

# `env-migration-version-scripts-and-encoding-2026-06-11-173900.md`

> **文档性质**：环境迁移指南。与 `project-handoff-*` 不同，env-migration 聚焦**单次 session 对开发环境本身**的修改（配置、环境变量、缓存位置、工具链参数等），而非业务功能交付。  
> **受众**：Human + Agent。在新环境解压项目后，Agent 可直接阅读此文档并执行复现步骤。


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 版本获取脚本体系建立与编码修复 |
| **日期** | 2026-06-11 |
| **文件名时间戳** | `2026-06-11-173900` |
| **触发原因** | 用户要求创建可复用的版本检测脚本，解决 PowerShell UTF-8 编码问题 |
| **影响范围** | schema/tool/ 目录新增脚本、check-file-encoding.ps1 改造、编码处理逻辑修复 |
| **风险等级** | 低（仅影响开发环境工具链，不涉及业务代码） |


## 一、文本文件变更清单

### 1. 新建 `schema/tool/get-python-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-python-version.ps1` |
| **变更类型** | 新建 |
| **作用** | 获取 Python 版本号 |
| **验证方式** | `powershell.exe -File schema/tool/get-python-version.ps1` |
| **迁移方式** | 直接复制 |

### 2. 新建 `schema/tool/get-node-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-node-version.ps1` |
| **变更类型** | 新建 |
| **作用** | 获取 Node.js 版本号 |
| **验证方式** | `powershell.exe -File schema/tool/get-node-version.ps1` |
| **迁移方式** | 直接复制 |

### 3. 新建 `schema/tool/get-opencode-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-opencode-version.ps1` |
| **变更类型** | 新建 |
| **作用** | 获取 OpenCode CLI 版本号 |
| **验证方式** | `powershell.exe -File schema/tool/get-opencode-version.ps1` |
| **迁移方式** | 直接复制 |

### 4. 新建 `schema/tool/get-cursor-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-cursor-version.ps1` |
| **变更类型** | 新建 |
| **作用** | 获取 Cursor 版本号（3级回退：cursor.cmd → package.json → PE VersionInfo） |
| **验证方式** | `powershell.exe -File schema/tool/get-cursor-version.ps1` |
| **迁移方式** | 直接复制 |

### 5. 新建 `schema/tool/get-chromium-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-chromium-version.ps1` |
| **变更类型** | 新建 |
| **作用** | 获取 Chromium 版本号（PE VersionInfo） |
| **验证方式** | `powershell.exe -File schema/tool/get-chromium-version.ps1` |
| **迁移方式** | 直接复制 |

### 6. 新建 `schema/tool/validate-file.py`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/validate-file.py` |
| **变更类型** | 新建 |
| **作用** | 通用文件校验工具（BOM、行尾符、中文、PS关键字） |
| **验证方式** | `python.exe schema/tool/validate-file.py <文件路径>` |
| **迁移方式** | 直接复制 |

### 7. 新建 `schema/tool/ps1-template.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/ps1-template.ps1` |
| **变更类型** | 新建 |
| **作用** | PS1 模板文件，示范规范格式，可被导入复用编码处理函数 |
| **验证方式** | 直接执行：`powershell.exe -File schema/tool/ps1-template.ps1`；点源导入：`. .\schema\tool\ps1-template.ps1` |
| **迁移方式** | 直接复制 |

### 8. 修改 `schema/tool/check-file-encoding.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/check-file-encoding.ps1` |
| **变更类型** | 修改 |
| **新增内容** | 点源导入 `ps1-template.ps1`，使用 Switch-ToUtf8/Restore-Encoding 函数 |
| **插入位置** | param() 块之后，主逻辑之前 |
| **作用** | 简化编码处理代码，从 18 行减少到 1 行导入 |
| **验证方式** | `powershell.exe -File schema/tool/check-file-encoding.ps1 -Path <文件>` |
| **迁移方式** | 直接复制 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 不涉及文件复制、缓存迁移、目录创建等操作。


## 三、编码处理逻辑变更

### 关键修复

1. **`Restore-Encoding` 函数**：恢复到保存的原始值，而非强制统一
   - Console: GB2312 (CodePage: 936)
   - Output: US-ASCII (CodePage: 20127)
   - 这是 PowerShell 5.1 的默认行为，两者不一致是正常的

2. **`validate-file.py`**：开头保存原始编码并切换到 UTF-8，退出时恢复
   - 使用 `sys.stdout.reconfigure(encoding='utf-8')`
   - 退出时通过 `restore_encoding()` 恢复


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 验证版本脚本 | `powershell.exe -File schema/tool/get-python-version.ps1` | 输出 JSON 格式版本信息 |
| 2 | 验证校验工具 | `python.exe schema/tool/validate-file.py schema/tool/ps1-template.ps1 --require-bom --expect-ps-keywords` | 全部通过 |
| 3 | 验证模板直接执行 | `powershell.exe -File schema/tool/ps1-template.ps1 -ParamName "test"` | 输出"脚本执行中... ParamName=test" |
| 4 | 验证模板点源导入 | `. .\schema\tool\ps1-template.ps1; Switch-ToUtf8; Write-Output "OK"; Restore-Encoding` | 输出"OK" |
| 5 | 验证 check-file-encoding | `powershell.exe -File schema/tool/check-file-encoding.ps1 -Path schema/tool/ps1-template.ps1` | 输出 BOM=yes, CRLF=0, LF=xx |
| 6 | 验证编码恢复 | 执行 check-file-encoding 后检查 `$OutputEncoding` | 恢复到 US-ASCII (CodePage: 20127) |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增脚本 | `Remove-Item schema/tool/get-*-version.ps1` |
| 删除校验工具 | `Remove-Item schema/tool/validate-file.py` |
| 删除模板 | `Remove-Item schema/tool/ps1-template.ps1` |
| 恢复 check-file-encoding | 从 git 恢复原版本 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-11-173900 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求创建可复用的版本检测脚本 |
| **下次修订条件** | 新增版本检测工具或修改编码处理逻辑时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-11*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
