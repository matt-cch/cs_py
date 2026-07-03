---
title: runtime 下载脚本代理支持 + 智能路由探测 + 脚本精简
description: >
  在 2026-06-03 模块化重构基础上，新增 GitHub Release 代理下载支持、
  下载前智能路由探测、超时参数联动、opencode_cli 实时查询，
  并将主入口脚本从 422 行精简至 246 行。
date: 2026-06-04
---

# env-migration-runtime-download-proxy-routing-2026-06-04-111336

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | runtime 下载脚本代理支持 + 智能路由探测 + 脚本精简 |
| **日期** | 2026-06-04 |
| **文件名时间戳** | `2026-06-04-111336` |
| **触发原因** | ① GitHub 直连不稳定，需代理回退能力；② 脚本超过 400 行，需精简；③ opencode_cli 版本检测需区分 CLI/GUI 策略 |
| **影响范围** | `references/runtime/` 下 4 个脚本 + 1 个配套文档 |
| **风险等级** | 低（纯增强脚本能力，向后兼容） |
| **前置依赖** | [env-migration-runtime-download-modularization-2026-06-03-175439.md](env-migration-runtime-download-modularization-2026-06-03-175439.md) |


## 一、文本文件变更清单

### 1. 重写 `download-runtime-tool.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-runtime-tool.ps1` |
| **变更类型** | 重写（422 行 → 246 行，注释保留，代码正文从 ~320 行 → 184 行） |
| **新增参数** | `-Proxy <string>`：强制指定代理域名（如 `gh-proxy.com`） |
| **Step 3 精简** | 实时查询结果从 5 行详细输出压缩为 1 行（来源 \| 版本 \| 查询时间） |
| **Step 6 增强** | 新增智能路由探测调用（`Test-DownloadRoute`），自动选择直连或代理 |
| **Step 9 精简** | 确认提示从 4 行压缩为单行：`是否执行替换？ [Y] 备份并替换 / [N] 保留检测文件` |
| **Step 11+12 合并** | 验证与清理合并为一个逻辑块，减少重复空行 |
| **关键修复** | `$actualToolDir` 赋值时 `Write-Output` 污染变量的问题改为先输出后赋值 |
| **验证方式** | PSParser Tokenize 语法检查通过；实测 opencode_cli/node 端到端下载流程完整 |
| **迁移方式** | 直接覆盖目标环境同名文件 |

### 2. 重写 `download-utils.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-utils.ps1` |
| **变更类型** | 重写（~125 行 → ~278 行，主要新增智能路由探测逻辑） |
| **新增函数** | `Test-DownloadRoute`：下载前 HEAD 探测直连/代理，自动选择最佳路由 |
| **新增函数** | `_InvokeGitHubApiWithFallback`：GitHub API 直连失败时自动遍历代理重试 |
| **`Write-ResultLine` 增强** | 新增 `-Lines` 数组参数，支持一次性批量输出多行对齐结果 |
| **`Get-LocalToolVersion` 重构** | 分三类检测策略：①原生 CLI（`--version`）②GUI+cmd wrapper（cursor.cmd）③纯 GUI（PE VersionInfo） |
| **超时常量集中定义** | `$ProbeDirectTimeoutSec=5`、`$ProbeProxyTimeoutSec=10`、`$ProbeDirectThresholdMs=3000` |
| **验证方式** | PSParser Tokenize 语法检查通过；实测三类工具版本检测均正确 |
| **迁移方式** | 直接覆盖目标环境同名文件 |

### 3. 修改 `download-core.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-core.ps1` |
| **变更类型** | 修改（~87 行 → ~100 行） |
| **新增参数** | `-Proxy <string>`：代理域名，URL 自动重写为 `https://$proxy/$原始URL` |
| **新增参数** | `-IsProxy`：开关参数，根据路由类型设置匹配的超时 |
| **动态超时** | 直连：连接 30s / 读写 300s；代理：连接 60s / 读写 900s |
| **比例设计** | 探测 timeout × 6 = 下载连接超时（5s×6=30s，10s×6=60s） |
| **验证方式** | PSParser Tokenize 语法检查通过；实测代理下载 48MB 文件成功 |
| **迁移方式** | 直接覆盖目标环境同名文件 |

### 4. 重写 `upstream-queries.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/upstream-queries.ps1` |
| **变更类型** | 重写（~162 行 → ~277 行） |
| **新增 case** | `opencode_cli`：实时查询 GitHub Release（`anomalyco/opencode`） |
| **代理回退** | `_InvokeGitHubApiWithFallback`：直连失败时遍历代理列表重试 |
| **指定版本验证** | `opencode_cli` 支持 `-TargetVersion`，验证 tag 是否存在 |
| **超时常量引用** | 探测 timeout 使用 `download-utils.ps1` 中集中定义的变量 |
| **验证方式** | PSParser Tokenize 语法检查通过；实测 v1.15.13 指定版本验证通过 |
| **迁移方式** | 直接覆盖目标环境同名文件 |

### 5. 新建 `download-runtime-tool.usage.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-runtime-tool.usage.md` |
| **变更类型** | 新建 |
| **作用** | 与 `download-runtime-tool.ps1` 配套的命令速查与架构说明文档 |
| **内容** | ①架构总览（树状调用关系）；②标准调用模板；③智能路由探测说明；④交互约定（Review 确认）；⑤文件位置速查 |
| **配套关系** | 文件名与入口脚本同名（`.usage.md` 后缀），文件系统排序相邻，直观体现一一配套 |
| **验证方式** | 文档格式检查：Obsidian frontmatter + 目录导航完整 |
| **迁移方式** | 直接复制到目标环境同目录 |


## 二、非文本操作

本次 session 不涉及文件系统迁移、缓存复制或目录创建。所有变更均为文本文件级别（脚本 + 配套文档）。


## 三、环境变量速查

本次 session **未修改** `.vscode/settings.json` 或任何环境变量注入项。原有变量配置保持有效。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 5 个文件存在 | `Get-ChildItem references/runtime/download-*.ps1, references/runtime/upstream-queries.ps1, references/runtime/download-runtime-tool.usage.md` | 列出 5 个文件 |
| 2 | 语法检查 | `PSParser::Tokenize` 检查 4 个 `.ps1` | 0 个错误 |
| 3 | 智能路由探测（直连） | `"N" \| powershell -File references/runtime/download-runtime-tool.ps1 -ToolName "opencode_cli" -IndexPath "references/runtime/verified-runtime-index.json" -TargetVersion "1.15.13" -ShowProgress -Force` | `Step 6: [INFO] 直连可用，延迟 xxxms`，下载成功 |
| 4 | 强制代理模式 | `"N" \| powershell -File ... -Proxy "gh-proxy.com" -ShowProgress -Force` | `[INFO] 强制使用代理: gh-proxy.com`，下载成功 |
| 5 | opencode_cli 版本检测 | 观察 Step 2 输出 | `[OK] 本地版本: 1.15.13`（使用 `--version` 而非 PE 属性） |
| 6 | `Write-ResultLine` 数组 | 观察 Step 8「检测摘要」输出 | 多行结果对齐输出，无错位 |
| 7 | cursor 版本检测 | `"N" \| powershell -File ... -ToolName "cursor" -ShowProgress` | `[OK] 本地版本: 3.x.x`（使用 cursor.cmd --version） |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复主入口 | 将拆分前的 `download-runtime-tool.ps1`（2026-06-03 版本，379 行）覆盖回 `references/runtime/` |
| 恢复子模块 | 将 2026-06-03 版本的 `download-utils.ps1`、`download-core.ps1`、`upstream-queries.ps1` 覆盖回同目录 |
| 删除配套文档 | `Remove-Item references/runtime/download-runtime-tool.usage.md` |

> **注意**：回滚后 `-Proxy` 参数、智能路由探测、opencode_cli 实时查询、动态超时、三类版本检测策略均不可用，退化为 2026-06-03 版本功能。


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-04-111336 |
| **更新人** | Human + Agent Session |
| **变更触发** | GitHub 直连不稳定；脚本超过 400 行维护困难；opencode_cli 版本检测不准确 |
| **下次修订条件** | ①代理列表需随网络环境更新（高失效性）；②更多工具需支持实时查询；③主入口仍可进一步精简 |
| **跨环境迁移参考** | 直接复制本文档「文本文件变更清单」中的 5 个文件到新环境同目录，执行「验证清单」 |


*文档生成时间：2026-06-04-111336*  
*模板版本：v2*  
*前置 env-migration：[env-migration-runtime-download-modularization-2026-06-03-175439.md](env-migration-runtime-download-modularization-2026-06-03-175439.md)*
