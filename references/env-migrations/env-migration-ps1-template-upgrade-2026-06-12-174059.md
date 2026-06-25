---
title: ps1-template.ps1 升级 v1.1.0 + 交付验证函数 + 编码切换分支适配
description: 升级 ps1-template 点源模块（剥离硬编码 UTF-8、新增通用编码函数、Test-ScriptDelivery 交付验证），同步适配 check-file-encoding 的编码切换分支。
date: 2026-06-12
---

# ps1-template.ps1 升级 v1.1.0 + 交付验证函数 + 编码切换分支适配

> **文档性质**：环境迁移指南。记录本次 session 对开发环境产生的变更（脚本模板升级），供新环境复现。  
> **受众**：Human + Agent。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | ps1-template.ps1 升级 v1.1.0 + 交付验证函数 + 编码切换分支适配 |
| **日期** | 2026-06-12（frontmatter） |
| **文件名时间戳** | `2026-06-12-174059` |
| **触发原因** | ps1-template.ps1 点源导入时硬编码 UTF-8 副作用污染调用方；需增加通用编码弹性与交付验证能力 |
| **影响范围** | `schema/tool/ps1-template.ps1`、`schema/tool/check-file-encoding.ps1` |
| **风险等级** | 低（仅模板与辅助脚本升级，不涉及业务代码） |

## 一、文本文件变更清单

### 1. 修改 `schema/tool/ps1-template.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/ps1-template.ps1` |
| **变更类型** | `修改` |
| **作用** | PowerShell 脚本模板与点源模块升级（v1.0.0 → v1.1.0） |
| **关键变更** | 1. 删除全局作用域硬编码 UTF-8 设置（原第 70-71 行），避免点源导入副作用<br>2. 新增 `Switch-ToEncoding` 通用函数，支持任意 `[System.Text.Encoding]`<br>3. `Switch-ToUtf8` 重构为 `Switch-ToEncoding` 的 UTF-8 快捷封装<br>4. `Invoke-WithEncoding` 替代 `Invoke-Utf8Command`，支持任意编码<br>5. 新增 `Test-ScriptDelivery` 交付验证函数（语法 + BOM + 行尾符 + 中文可读性 + 可选 PS 关键字）<br>6. 扩展点源引用注释：新增 $PSScriptRoot 路径拼接说明、跨目录引用场景<br>7. `.NOTES` 更新版本号、日期、点源引用说明 |
| **验证方式** | `powershell.exe -File schema/tool/ps1-template.ps1` 应正常执行并输出 "脚本执行中..." |
| **迁移方式** | 可直接覆盖；点源调用方需确认是否依赖旧 `Invoke-Utf8Command`（已移除） |

> **注意**：`Invoke-Utf8Command` 已被移除，所有引用方需改用 `Invoke-WithEncoding -Encoding ([System.Text.Encoding]::UTF8)`。

### 2. 修改 `schema/tool/check-file-encoding.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/check-file-encoding.ps1` |
| **变更类型** | `修改` |
| **作用** | 适配 ps1-template v1.1.0+，展示编码切换分支的调用范本 |
| **关键变更** | 1. 点源导入路径改为 `$templatePath = Join-Path $PSScriptRoot "ps1-template.ps1"; . $templatePath`（可移植）<br>2. 新增 `-EncodingMode` 参数（`ValidateSet("Utf8", "Gbk")`，默认 `"Utf8"`）<br>3. 新增 `switch` 分支：根据 `$EncodingMode` 选择 `Switch-ToUtf8` 或 `Switch-ToEncoding -Encoding ([System.Text.Encoding]::GetEncoding("GBK"))`<br>4. 注释同步更新：`Invoke-Utf8Command` → `Invoke-WithEncoding`，增加点源导入编码说明 |
| **验证方式** | `powershell.exe -File schema/tool/check-file-encoding.ps1 -Path schema/tool/ps1-template.ps1` 应输出通过结果 |
| **迁移方式** | 可直接覆盖 |

> **注意**：此为编码切换分支的**范本示例**。以后 ps1-template 若增加 `Switch-ToGbk()` 等快捷函数，调用方只需在 `switch` 中追加对应分支即可。

## 二、非文本操作（文件系统/缓存迁移）

本次 session 不涉及文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。

## 三、环境变量速查

无新增环境变量。

## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 ps1-template 可执行 | `powershell.exe -File schema/tool/ps1-template.ps1` | 输出 "脚本执行中... ParamName=" |
| 2 | 确认点源导入无副作用 | `powershell.exe -Command "$t=Join-Path $PWD 'schema\tool\ps1-template.ps1'; . $t; Write-Output ([Console]::OutputEncoding.WebName)"` | 编码未被强制改为 UTF-8（除非当前环境本身就是 UTF-8） |
| 3 | 确认 Test-ScriptDelivery 可用 | `. schema/tool/ps1-template.ps1; Test-ScriptDelivery -Path schema/tool/check-file-encoding.ps1` | 输出 "结果: 全部通过" |
| 4 | 确认 check-file-encoding 通过 | `powershell.exe -File schema/tool/check-file-encoding.ps1 -Path schema/tool/ps1-template.ps1` | BOM=yes, DOUBLE_BOM=no, CRLF=0, LF>0 |
| 5 | 确认 check-file-encoding GBK 分支 | `powershell.exe -File schema/tool/check-file-encoding.ps1 -Path schema/tool/ps1-template.ps1 -EncodingMode Gbk` | 正常执行无报错 |

## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 ps1-template | `git checkout schema/tool/ps1-template.ps1` |
| 恢复 check-file-encoding | `git checkout schema/tool/check-file-encoding.ps1` |

## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-12-174059 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求提升 ps1-template 点源模块的编码弹性与交付验证能力 |
| **下次修订条件** | ps1-template 新增更多编码快捷函数（如 Switch-ToGbk）、Test-ScriptDelivery 扩展新检查项 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |

*文档生成时间：2026-06-12-174059*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
