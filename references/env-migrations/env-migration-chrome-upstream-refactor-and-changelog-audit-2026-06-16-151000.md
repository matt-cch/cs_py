---
title: Chromium 上游查询逻辑重构 + Changelog 规则修正 + Audit 自检机制建立
description: 本次 session 三大主线：1）Chromium 上游查询从 Snapshot 构建号体系切换到 Chrome for Testing 语义化版本，修复版本比较与下载链路；2）Changelog 记录规则从追加模式修正为时间线独立文件；3）建立 Audit 自检机制防止版本检测遗漏。
date: 2026-06-16
---

# Chromium 上游查询逻辑重构 + Changelog 规则修正 + Audit 自检机制建立

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Chromium 上游查询逻辑重构 + Changelog 规则修正 + Audit 自检机制建立 |
| **日期** | 2026-06-16 |
| **文件名时间戳** | `2026-06-16-151000` |
| **触发原因** | 1. 运行时检测显示"本地 Chromium 高于上游"异常，根因是 Snapshot 与 Chrome for Testing 版本体系错位；2. 用户对追加模式的质疑，确认规则应为时间线独立文件；3. Agent 在版本检测报告中遗漏 `llama_cpp_python`，要求建立 Audit 自检机制 |
| **影响范围** | `references/runtime/` 下 4 个脚本/模块、2 个索引/配置、2 个新增脚本；`references/changelog/` 下 3 个文档；`references/runtime/verify-runtime-audit-checklist.md`；`references/README.md` |
| **风险等级** | 中（替换了核心查询入口，但已验证通过） |


## 一、文本文件变更清单

### 主线 A：Chromium 上游查询逻辑重构

#### A1. 修改 `references/runtime/upstream-queries.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/upstream-queries.ps1` |
| **变更类型** | 修改（重写 Chromium 查询逻辑） |
| **变更前** | 查询 `chromium-browser-snapshots/Win_x64/`，返回 Snapshot 构建号（如 `r1627931`） |
| **变更后** | 查询 `chrome-for-testing/?max-keys=2000`，返回语义化版本（如 `151.0.7893.0`）；npmmirror 主 + Google 官方 `last-known-good-versions` fallback |
| **核心排序** | 按语义化版本 `(major*1e9 + minor*1e6 + build*1e3 + patch)` 降序 |
| **作用** | 修复 Snapshot 构建号与 Chrome for Testing 语义化版本不互通导致的版本比较错误 |
| **验证方式** | 执行 `download-runtime-tool.ps1 -ToolName chromium`，确认返回 `151.0.7893.0` 且无需更新 |
| **迁移方式** | 直接覆盖 |

#### A2. 修改 `references/runtime/runtime_modules/upstream_checker.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/upstream_checker.py` |
| **变更类型** | 修改（重写 `_query_chromium` 方法） |
| **变更前** | 使用 Snapshot 构建号缓存机制，需下载 330MB ZIP 验证新构建号 |
| **变更后** | 与 PowerShell 一致的双源查询（npmmirror 目录列表 + Google 官方 API），零下载解析 JSON |
| **作用** | 移除过时的 Snapshot 查询，统一为 Chrome for Testing 语义化版本 |
| **验证方式** | 执行 `verify-runtime.py`，确认 chromium upstream 查询通过 |
| **迁移方式** | 直接覆盖 |

#### A3. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改（更新 chromium 节点） |
| **新增字段** | `download_url_template`: `https://registry.npmmirror.com/-/binary/chrome-for-testing/{version}/win64/chrome-win64.zip` |
| **修正字段** | `verification_command` 路径从 `chrome-win` 改为 `chrome-win64` |
| **作用** | 索引与新的 Chrome for Testing 下载链路对齐 |
| **验证方式** | 执行 `verify-runtime.ps1`，确认索引与实测一致 |
| **迁移方式** | 脚本自动更新 |

#### A4. 修改 `references/runtime/runtime_config/chromium_build_map.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/chromium_build_map.json` |
| **变更类型** | 修改（更新缓存） |
| **变更后** | `last_known_build`: `1646714`，`last_known_version`: `151.0.7893.0` |
| **作用** | 保留历史映射，供参考 |
| **迁移方式** | 直接覆盖 |

#### A5. 新建 `references/runtime/chrome-version-check.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/chrome-version-check.py` |
| **变更类型** | 新建 |
| **作用** | 独立双源 Chrome 版本检测脚本（Python），输出 `channels` / `latest_overall` / `latest_by_series` / `downloads` |
| **验证方式** | 执行该脚本，确认输出 JSON 包含 `channels` 和 `latest_overall` |
| **迁移方式** | 直接复制文件 |

#### A6. 新建 `references/runtime/chrome-version-check.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/chrome-version-check.ps1` |
| **变更类型** | 新建 |
| **作用** | 同上，PowerShell 实现版本 |
| **验证方式** | 执行该脚本，确认输出 JSON 包含 `channels` 和 `latest_overall` |
| **迁移方式** | 直接复制文件 |

#### A7. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 修改（追加条目） |
| **新增内容** | 登记 `chrome-version-check-py` 和 `chrome-version-check-ps1` 两个脚本条目 |
| **作用** | 确保后续 Agent 可通过索引复用这两个脚本 |
| **验证方式** | 读取 `verified-task-index.json`，确认两个条目存在且 `path_exists` 为 `true` |
| **迁移方式** | 直接覆盖 |


### 主线 B：Changelog 记录规则修正

#### B1. 修改 `references/changelog/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/README.md` |
| **变更类型** | 修改（追加规则章节 + 重排文件导航表） |
| **新增内容** | 新增「记录规则（硬性）」章节，含：记录单位、命名格式、时间线标识、slug、排序规则、禁止行为、命名示例 |
| **插入位置** | 在「与项目级 changelog 的区分」之前插入新章节 |
| **作用** | 明确 changelog 记录规则，确保后续 Agent/Human 不再误用追加模式 |
| **验证方式** | 打开文件，确认存在「记录规则（硬性）」章节，且文件导航表按日期倒序排列 |
| **迁移方式** | 可直接覆盖 |

#### B2. 修改 `references/changelog/monorepo-env-changelog.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/monorepo-env-changelog.md` |
| **变更类型** | 修改（顶部追加归档说明，标题标注历史归档） |
| **新增内容** | 顶部添加 `⚠️ 归档说明` blockquote，声明自 2026-06-16 起不再追加；title 和 description 同步标注「历史归档」 |
| **插入位置** | 文件开头 frontmatter 之后、一级标题之前 |
| **作用** | 防止后续 session 误将新变更追加到此文件 |
| **验证方式** | 打开文件，确认顶部存在归档说明，且 title 含「历史归档」字样 |
| **迁移方式** | 可直接覆盖 |

#### B3. 新建 `references/changelog/changelog-2026-06-16-chrome-for-testing-upstream-fix.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/changelog-2026-06-16-chrome-for-testing-upstream-fix.md` |
| **变更类型** | 新建 |
| **作用** | 首个按新规则创建的独立 changelog 文件，记录 Chromium 上游查询逻辑重构 |
| **验证方式** | 文件存在，且 `README.md` 导航表中已登记 |
| **迁移方式** | 直接复制文件 |


### 主线 C：Audit 自检机制建立

#### C1. 新建 `references/runtime/verify-runtime-audit-checklist.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime-audit-checklist.md` |
| **变更类型** | 新建 |
| **新增内容** | 运行时版本检测 Audit 自检清单，含：必须检测的 7 项 toolchain 清单、自检流程（Step 1~3）、Audit 输出格式、修订联动义务 |
| **作用** | 防止 Agent 在执行版本检测后遗漏任何 toolchain 项（如本次遗漏 `llama_cpp_python` 的问题） |
| **验证方式** | 文件存在，且内容包含 7 项 toolchain 清单 |
| **迁移方式** | 直接复制文件 |

#### C2. 修改 `references/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/README.md` |
| **变更类型** | 修改（更新子目录导航描述） |
| **变更内容** | `runtime/` 行增加对 `verify-runtime-audit-checklist.md` 的引用 |
| **作用** | 使 Audit 清单可从 references 首页导航发现 |
| **验证方式** | 打开文件，确认 runtime/ 行包含 audit checklist 引用 |
| **迁移方式** | 可直接覆盖 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 不涉及文件复制、缓存迁移、目录创建等非文本操作。


## 三、环境变量速查

本次 session 不涉及环境变量变更。


## 四、运行时检测执行记录（本次 session 实测）

### 4.1 真源检测执行

| 属性 | 值 |
|------|-----|
| **执行命令** | `powershell.exe -ExecutionPolicy Bypass -File "${devroot}\references\runtime\verify-runtime.ps1"` |
| **报告文件** | `verify-runtime-report-20260616T111818.json` |
| **总计** | 25 |
| **通过** | 25 |
| **失败** | 0 |
| **未变更** | 20 |
| **已变更** | 5 |

**唯一变更项**：`chromium.version`: `150.0.7834.0` → `151.0.7893.0`（本地版本已更新）

**全部 toolchain 状态**：

| # | 工具 | 本地版本 | 状态 |
|---|------|---------|------|
| 1 | python | 3.13.14 | ✅ |
| 2 | node | 26.3.0 | ✅ |
| 3 | npm | 11.16.0 | ✅ |
| 4 | opencode_cli | 1.17.7 | ✅ |
| 5 | cursor | 3.7.36 | ✅ |
| 6 | **llama_cpp_python** | **0.3.29** | **✅** |
| 7 | chromium | 151.0.7893.0 | ✅ |

### 4.2 Chromium 下载检测执行

| 属性 | 值 |
|------|-----|
| **执行命令** | `"N" | powershell.exe -ExecutionPolicy Bypass -File "${devroot}\references\runtime\download-runtime-tool.ps1" -ToolName "chromium" -IndexPath "..." -ShowProgress` |
| **本地版本** | 151.0.7893.0 |
| **上游版本** | 151.0.7893.0（npmmirror Chrome for Testing） |
| **结论** | 版本一致，无需更新 |


## 五、验证清单（新环境必须执行）

### 主线 A 验证

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| A1 | 确认 upstream-queries.ps1 已更新 | `read references/runtime/upstream-queries.ps1` 搜索 `chrome-for-testing` | 存在 Chrome for Testing 查询逻辑 |
| A2 | 确认 upstream_checker.py 已更新 | `read references/runtime/runtime_modules/upstream_checker.py` 搜索 `_query_chromium` | 方法内使用语义化版本查询 |
| A3 | 确认索引已更新 | `read references/runtime/verified-runtime-index.json` 搜索 `download_url_template` | chromium 节点存在该字段 |
| A4 | 确认 build_map 已更新 | `read references/runtime/runtime_config/chromium_build_map.json` | `last_known_version` 为 `151.0.7893.0` |
| A5 | 确认 py 检测脚本存在 | `Test-Path references/runtime/chrome-version-check.py` | `True` |
| A6 | 确认 ps1 检测脚本存在 | `Test-Path references/runtime/chrome-version-check.ps1` | `True` |
| A7 | 确认 task-index 已登记 | `read references/runtime/verified-task-index.json` 搜索 `chrome-version-check` | 存在两个条目 |

### 主线 B 验证

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| B1 | 确认 README 规则章节存在 | `read references/changelog/README.md` | 存在「记录规则（硬性）」章节 |
| B2 | 确认归档说明已添加 | `read references/changelog/monorepo-env-changelog.md` | 顶部存在 `⚠️ 归档说明` |
| B3 | 确认独立 changelog 文件存在 | `Test-Path references/changelog/changelog-2026-06-16-chrome-for-testing-upstream-fix.md` | `True` |
| B4 | 确认导航表已更新 | `read references/changelog/README.md` 查看文件导航 | 包含该文件条目，且按日期倒序排列 |

### 主线 C 验证

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| C1 | 确认 Audit 自检清单存在 | `Test-Path references/runtime/verify-runtime-audit-checklist.md` | `True` |
| C2 | 确认 references/README 导航已更新 | `read references/README.md` | runtime/ 行包含 audit checklist 引用 |
| C3 | 确认 Audit 清单含 7 项 | `read references/runtime/verify-runtime-audit-checklist.md` | 表格列出 7 项 toolchain |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 upstream-queries.ps1 | 从 git 回滚 `references/runtime/upstream-queries.ps1` |
| 恢复 upstream_checker.py | 从 git 回滚 `references/runtime/runtime_modules/upstream_checker.py` |
| 恢复 verified-runtime-index.json | 从 git 回滚（或从 `verified-runtime-index.history.json` 恢复） |
| 恢复 chromium_build_map.json | 从 git 回滚 |
| 删除新增 py 脚本 | `Remove-Item references/runtime/chrome-version-check.py` |
| 删除新增 ps1 脚本 | `Remove-Item references/runtime/chrome-version-check.ps1` |
| 恢复 changelog README | 从 git 回滚 `references/changelog/README.md` |
| 恢复 monorepo-env-changelog.md | 从 git 回滚 `references/changelog/monorepo-env-changelog.md` |
| 删除独立 changelog 文件 | `Remove-Item references/changelog/changelog-2026-06-16-chrome-for-testing-upstream-fix.md` |
| 删除 Audit 清单 | `Remove-Item references/runtime/verify-runtime-audit-checklist.md` |
| 恢复 references/README.md | 从 git 回滚 `references/README.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-16-151000 |
| **更新人** | Human + Agent Session |
| **变更触发** | 1. 运行时检测显示"本地 Chromium 高于上游"异常；2. 用户对追加模式的质疑；3. Agent 遗漏 `llama_cpp_python` |
| **下次修订条件** | `verified-runtime-index.json` toolchain 节点增删工具项时同步更新 Audit 对照表；changelog 规则需要再次调整时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
