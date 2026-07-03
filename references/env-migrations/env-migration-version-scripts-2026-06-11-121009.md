---
title: env-migration 版本获取脚本体系与编码修复
description: 新建 5 个版本获取脚本，更新高频任务 mdc 引用，修复 verify-runtime.ps1 UTF-8 编码问题。
date: 2026-06-11
---

# env-migration-版本获取脚本体系-2026-06-11-121009

## 元信息

| 字段 | 填写 |
|------|------|
| **Session 主题** | 版本获取脚本体系建立与编码修复 |
| **日期** | 2026-06-11 |
| **文件名时间戳** | `2026-06-11-121009` |
| **触发原因** | 用户要求创建可复用的版本获取脚本，替代每次现写命令 |
| **影响范围** | schema/tool/ 新增脚本、高频任务 mdc 更新、verify-runtime.ps1 编码修复 |
| **风险等级** | 低（纯工具链变更） |


## 一、文本文件变更清单

### 1. 新建 `schema/tool/get-python-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-python-version.ps1` |
| **变更类型** | 新建 |
| **内容** | 通过 `python.exe --version` 获取 Python 版本，输出 JSON |
| **验证方式** | `powershell.exe -File get-python-version.ps1` |

### 2. 新建 `schema/tool/get-node-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-node-version.ps1` |
| **变更类型** | 新建 |
| **内容** | 通过 `node.exe --version` 获取 Node.js 版本，输出 JSON |
| **验证方式** | `powershell.exe -File get-node-version.ps1` |

### 3. 新建 `schema/tool/get-opencode-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-opencode-version.ps1` |
| **变更类型** | 新建 |
| **内容** | 通过 `opencode.exe --version` 获取 OpenCode 版本，输出 JSON |
| **验证方式** | `powershell.exe -File get-opencode-version.ps1` |

### 4. 新建 `schema/tool/get-cursor-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-cursor-version.ps1` |
| **变更类型** | 新建 |
| **内容** | 三级降级获取 Cursor 版本：cursor.cmd → package.json → PE VersionInfo |
| **验证方式** | `powershell.exe -File get-cursor-version.ps1` |

### 5. 新建 `schema/tool/get-chromium-version.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-chromium-version.ps1` |
| **变更类型** | 新建 |
| **内容** | 通过 PE VersionInfo 获取 Chrome/Chromium 版本（纯 GUI 工具） |
| **验证方式** | `powershell.exe -File get-chromium-version.ps1` |

### 6. 新建 `venv/version/chromium.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/chromium.md` |
| **变更类型** | 新建 |
| **内容** | Chromium 当前版本记录（150.0.7834.0） |

### 7. 新建 `venv/version/chromium-history.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/chromium-history.md` |
| **变更类型** | 新建 |
| **内容** | Chromium 版本变更历史 |

### 8. 修改 `.cursor/rules/high-frequency-update-version.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-update-version.mdc` |
| **变更类型** | 修改 |
| **变更内容** | 实测命令表格改为调用 `.ps1` 脚本，新增 Chromium 行 |
| **插入位置** | 1.2 文件定位表格 |

### 9. 修改 `.cursor/rules/high-frequency-task-index.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-task-index.mdc` |
| **变更类型** | 修改 |
| **变更内容** | Agent 执行路径改为执行脚本，覆盖工具新增 Chromium |
| **插入位置** | 2. 更新版本记录 Agent 执行路径 |

### 10. 修改 `references/runtime/verify-runtime.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime.ps1` |
| **变更类型** | 修改 |
| **变更内容** | 第 332 行添加 `-Encoding UTF8` 参数 |
| **作用** | 修复 PowerShell 5.1 读取 UTF-8 JSON 时的编码问题 |


## 二、非文本操作

本次 session 无文件复制、缓存迁移等非文本操作。


## 三、环境变量速查

无环境变量变更。


## 四、验证清单

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | Python 版本脚本 | `powershell.exe -File "D:\pjt\cursor\cs_py\schema\tool\get-python-version.ps1"` | JSON 输出 version=3.13.13 |
| 2 | Node.js 版本脚本 | `powershell.exe -File "D:\pjt\cursor\cs_py\schema\tool\get-node-version.ps1"` | JSON 输出 version=v26.3.0 |
| 3 | OpenCode 版本脚本 | `powershell.exe -File "D:\pjt\cursor\cs_py\schema\tool\get-opencode-version.ps1"` | JSON 输出 version=1.17.0 |
| 4 | Cursor 版本脚本 | `powershell.exe -File "D:\pjt\cursor\cs_py\schema\tool\get-cursor-version.ps1"` | JSON 输出 version=3.7.27 |
| 5 | Chromium 版本脚本 | `powershell.exe -File "D:\pjt\cursor\cs_py\schema\tool\get-chromium-version.ps1"` | JSON 输出 version=150.0.7834.0 |
| 6 | verify-runtime.ps1 | `powershell.exe -ExecutionPolicy Bypass -File "D:\pjt\cursor\cs_py\references\runtime\verify-runtime.ps1"` | 无 JSON 解析错误 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除版本获取脚本 | `Remove-Item "D:\pjt\cursor\cs_py\schema\tool\get-*-version.ps1"` |
| 删除 Chromium 版本记录 | `Remove-Item "D:\pjt\cursor\cs_py\venv\version\chromium*.md"` |
| 恢复 mdc 文件 | 从 git 恢复 `.cursor/rules/high-frequency-*.mdc` |
| 恢复 verify-runtime.ps1 | 从 git 恢复 `references/runtime/verify-runtime.ps1` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-11-121009 |
| **更新人** | Agent Session |
| **变更触发** | 用户要求创建可复用的版本获取脚本 |
| **下次修订条件** | 新增版本获取脚本或修改检测方法时 |
| **跨环境迁移参考** | 复制本文件 + 按验证清单逐条执行 |


*文档生成时间：2026-06-11*
