---
title: 编码样板补齐与 mdc→ps1 联动链路建立
description: 完成 schema/tool/ 下全部 .ps1 编码切换/恢复样板覆盖，在 4 个 .mdc 中建立对验证脚本的显式引用链路。
date: 2026-06-10
---

# env-migration-encoding-boilerplate-and-mdc-linkage-2026-06-10-234043

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 编码样板补齐与 mdc→ps1 联动链路建立 |
| **日期** | 2026-06-10 |
| **文件名时间戳** | `2026-06-10-234043` |
| **触发原因** | list-tools.ps1 执行时中文乱码，检查发现 3 个 .ps1 脚本缺少编码切换样板；继续审查发现已创建的 schema/tool/ 脚本未在 .mdc 规则中被引用 |
| **影响范围** | `schema/tool/*.ps1`、`.cursor/rules/high-frequency-shell-guard-content.mdc`、`strictly-forbid-command-str-content.mdc`、`high-frequency-task-index.mdc`、`high-frequency-tool-shell-audit.mdc` |
| **风险等级** | 低（纯工具链脚本与规则文档变更） |


## 一、文本文件变更清单

### 1. 修改 `schema/tool/check-file-encoding.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/check-file-encoding.ps1` |
| **变更类型** | 修改 |
| **新增内容** | 在 `param` 后插入编码样板（`originalConsoleEncoding` + `Register-EngineEvent` + `try/finally Restore-Encoding`）；主逻辑从裸语句改为 `try { ... } finally { Restore-Encoding }` |
| **作用** | 确保执行时终端编码切为 UTF-8，退出时恢复原编码，避免 bash 捕获乱码 |
| **验证方式** | 执行 `powershell -File check-file-encoding.ps1 -Path <anyfile>`，中文输出正常 |
| **迁移方式** | 直接覆盖 |

### 2. 修改 `schema/tool/lint-ps1.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/lint-ps1.ps1` |
| **变更类型** | 修改 |
| **新增内容** | 同上编码样板 + `try/finally Restore-Encoding` |
| **作用** | 同上 |
| **验证方式** | 执行 `powershell -File lint-ps1.ps1 -Path <some.ps1>`，语法错误信息中文正常输出 |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `schema/tool/list-tools.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/list-tools.ps1` |
| **变更类型** | 修改 |
| **新增内容** | 同上编码样板 + `try/finally`；原 `exit 1` 散落逻辑改为统一 `try { ... } finally` |
| **作用** | 同上 |
| **验证方式** | 执行 `powershell -File list-tools.ps1 -IndexPath ...verified-task-index.json`，中文标题正常输出 |
| **迁移方式** | 直接覆盖 |

### 4~7. 修改 4 个 `.mdc` 规则文件

| 文件 | 路径 | 变更内容 |
|------|------|---------|
| high-frequency-shell-guard-content.mdc | `.cursor/rules/high-frequency-shell-guard-content.mdc` | 「写个 .ps1」行追加编码/语法验证步骤；新增验证工具备注块引用 `check-file-encoding.ps1` + `lint-ps1.ps1` |
| strictly-forbid-command-str-content.mdc | `.cursor/rules/strictly-forbid-command-str-content.mdc` | 事后验收表新增「写入 .ps1 文件编码与语法是否合规」行 |
| high-frequency-task-index.mdc | `.cursor/rules/high-frequency-task-index.mdc` | 顶部追加 `list-tools.ps1` 速查说明；第 6 节执行路径加入验证步骤 |
| high-frequency-tool-shell-audit.mdc | `.cursor/rules/high-frequency-tool-shell-audit.mdc` | 第 4 节追加 `list-tools.ps1` 和 `search-hidden-dir.ps1` 速查说明 |


## 二、非文本操作

无。


## 三、环境变量速查

无变更。


## 四、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 list-tools.ps1 中文输出正常 | `powershell -ExecutionPolicy Bypass -File schema/tool/list-tools.ps1 -IndexPath references/runtime/verified-task-index.json` | 中文标题"可用工具/脚本清单"正常显示，无乱码 |
| 2 | 确认 check-file-encoding.ps1 语法正确 | `powershell -File schema/tool/lint-ps1.ps1 -Path schema/tool/check-file-encoding.ps1` | exit 0 |
| 3 | 确认 lint-ps1.ps1 语法正确 | `powershell -File schema/tool/lint-ps1.ps1 -Path schema/tool/lint-ps1.ps1` | exit 0 |
| 4 | 确认 4 个 .mdc 文件无 CRLF 污染 | CRLF=0 检查 | 全部 CRLF=0 LF>0 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 3 个 .ps1 的旧版本 | 从 git 或备份中 checkout 原文件覆盖 |
| 恢复 4 个 .mdc 的旧版本 | 从 git 或备份中 checkout 原文件覆盖 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-10-234043 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户审查发现脚本编码样板缺失和 mdc→ps1 引用断联 |
| **下次修订条件** | 新增 schema/tool/ 脚本时须同步更新相关 .mdc 引用 |
