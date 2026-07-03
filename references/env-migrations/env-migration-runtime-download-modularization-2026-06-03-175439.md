---
title: runtime 下载脚本模块化重构 + Python 指定版本支持
description: 将 download-runtime-tool.ps1 从单文件拆分为 4 个模块，新增 Python 实时版本查询与 -TargetVersion 参数，修复进度条与子目录识别逻辑。
date: 2026-06-03
---

# env-migration-runtime-download-modularization-2026-06-03-175439

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | runtime 下载脚本模块化重构 + Python 指定版本下载支持 |
| **日期** | 2026-06-03 |
| **文件名时间戳** | `2026-06-03-175439` |
| **触发原因** | 单文件 696 行难以维护；Python 高版本（3.14/3.15）出现，需支持指定版本下载而非仅自动最新版 |
| **影响范围** | `references/runtime/` 下 4 个脚本文件 + `verified-runtime-index.json` |
| **风险等级** | 低（纯新增/重构脚本，不影响运行中工具） |


## 一、文本文件变更清单

### 1. 新建 `download-utils.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-utils.ps1` |
| **变更类型** | 新建 |
| **作用** | 通用工具函数：Write-Section、Write-ResultLine、Get-LocalToolVersion、Get-ToolConfigFromIndex、Normalize-Version、Resolve-DownloadUrl、Get-RunningProcessInfo |
| **行数** | ~63 行 |
| **验证方式** | PSParser Tokenize 语法检查通过 |
| **迁移方式** | 直接复制到目标环境同目录 |

### 2. 新建 `download-core.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-core.ps1` |
| **变更类型** | 新建 |
| **作用** | 下载核心：Download-FileWithProgress（同步分块下载 + `#` 进度条 / 异步 WebClient） |
| **关键修复** | 使用 `[Console]::WriteLine()` 替代 `Write-Output`，避免 PowerShell 变量捕获吞掉进度输出 |
| **行数** | ~88 行 |
| **验证方式** | PSParser Tokenize 语法检查通过；实测 node/chromium/python 下载进度正常显示 |
| **迁移方式** | 直接复制到目标环境同目录 |

### 3. 新建 `upstream-queries.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/upstream-queries.ps1` |
| **变更类型** | 新建 |
| **作用** | 上游实时版本查询：node（阿里云 index.json）、chromium（npmmirror 构建号）、python（阿里云目录列表解析 + 预发布版本排序） |
| **关键新增** | Python 实时查询支持 `-TargetVersion` 指定版本验证；`_ConvertToSortableVersion` 辅助函数正确处理 `a/b/rc` 预发布标记 |
| **行数** | ~163 行 |
| **验证方式** | PSParser Tokenize 语法检查通过；实测 node 自动查询、python 指定版本验证均正常 |
| **迁移方式** | 直接复制到目标环境同目录 |

### 4. 重写 `download-runtime-tool.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-runtime-tool.ps1` |
| **变更类型** | 重写（由单文件 696 行 → 379 行主入口） |
| **作用** | 主入口：参数定义、编码处理、子模块加载（点源引用 `. $scriptDir\*.ps1`）、Step 1-12 主逻辑 |
| **新增参数** | `-TargetVersion <string>`（仅 python 支持指定版本） |
| **关键变更** | 通过 `$MyInvocation.MyCommand.Path` 自动定位同目录子模块，无需硬编码绝对路径 |
| **行数** | ~379 行 |
| **验证方式** | PSParser Tokenize 语法检查通过；实测 node/python 端到端下载流程完整 |
| **迁移方式** | 直接覆盖目标环境同名文件 |

### 5. 修改 `verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改（python 配置项） |
| **修改内容** | `python.download_url_template` 从 `https://www.python.org/ftp/python/{version}/...` 改为 `https://mirrors.aliyun.com/python-release/windows/python-{version}-embed-amd64.zip`；upstream_sources 同步更新为阿里云镜像 |
| **作用** | 与实时查询来源一致，优先走国内镜像 |
| **验证方式** | 脚本读取索引后正确生成下载链接 |
| **迁移方式** | 直接覆盖或手动修改 python 配置项 |


## 二、非文本操作

本次 session 不涉及文件系统迁移、缓存复制或目录创建。所有变更均为文本文件级别（脚本 + JSON 配置）。


## 三、环境变量速查

本次 session **未修改** `.vscode/settings.json` 或任何环境变量注入项。原有变量配置保持有效。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---|---------|----------|---------|
| 1 | 确认 4 个文件存在 | `Get-ChildItem references/runtime/download-*.ps1, references/runtime/upstream-queries.ps1` | 列出 4 个文件 |
| 2 | 语法检查 | `PSParser::Tokenize` 检查 4 个 `.ps1` | 0 个错误 |
| 3 | 子模块加载测试 | `echo "N" | powershell -File references/runtime/download-runtime-tool.ps1 -ToolName "node" -IndexPath "references/runtime/verified-runtime-index.json" -ShowProgress` | 正常输出版本对比、下载进度（取消替换即可） |
| 4 | Python 指定版本测试 | `echo "N" | powershell -File references/runtime/download-runtime-tool.ps1 -ToolName "python" -IndexPath "references/runtime/verified-runtime-index.json" -TargetVersion "3.13.13" -ShowProgress` | 显示"本地版本与上游一致，无需更新"（或下载后版本验证通过） |
| 5 | 索引 JSON 格式 | `Get-Content references/runtime/verified-runtime-index.json | ConvertFrom-Json` | 无解析错误 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复旧脚本 | 将拆分前的 `download-runtime-tool.ps1` 备份（如有）覆盖回 `references/runtime/` |
| 删除子模块 | `Remove-Item references/runtime/download-utils.ps1, references/runtime/download-core.ps1, references/runtime/upstream-queries.ps1` |
| 恢复索引 | 将 `verified-runtime-index.json` 中 python 的 `download_url_template` 改回 `https://www.python.org/ftp/python/...` |

> **注意**：回滚后 `-TargetVersion` 参数和 Python 实时查询功能将不可用，退化为仅索引快照 + 固定模板。


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-03-175439 |
| **更新人** | Human + Agent Session |
| **变更触发** | 单文件过大（696 行）维护困难；Python 3.14/3.15 上线需指定版本下载能力 |
| **下次修订条件** | 新增 opencode_cli 实时查询；新增更多工具的实时上游查询；主入口仍需进一步拆分（当前 379 行） |
| **跨环境迁移参考** | 直接复制本文档「文本文件变更清单」中的 5 个文件到新环境同目录，执行「验证清单」 |


*文档生成时间：2026-06-03-175439*  
*模板版本：v2*
