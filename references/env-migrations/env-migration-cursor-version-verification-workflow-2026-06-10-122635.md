---
title: Cursor 版本检测流程标准化 + 工具版本记录更新
description: cursor.md 版本检测从 package.json 改为 cursor.cmd --version 两步验证；verified-runtime-index.json 延迟数据更新；OpenCode/Cursor 版本记录升级。
date: 2026-06-10
---

# env-migration-cursor-version-verification-workflow-2026-06-10-122635

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Cursor 版本检测流程标准化（真源层级明确化）+ 运行时版本记录更新 |
| **日期** | 2026-06-10（frontmatter；文件名时间戳 `2026-06-10-122635`） |
| **触发原因** | 用户指出 cursor.md 仍使用旧的 package.json 检测方式，未使用已验证的 cursor.cmd --version 办法 |
| **影响范围** | `venv/version/` 下版本记录文件、`references/runtime/verified-runtime-index.json` |
| **风险等级** | 低（纯文档与记录更新，不涉及业务代码或运行时配置） |


## 一、文本文件变更清单

### 1. 修改 `venv/version/cursor.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/cursor.md` |
| **变更类型** | 重写（检测流程重构） |
| **作用** | 将版本检测方式从 `package.json` 读取改为 `cursor.cmd --version` 两步验证，并明确真源层级 |
| **关键变化** | ① 新增「铁律」区块：`verified-runtime-index.json` 是参考而非真源；② Step 1（参考索引）→ Step 2（实测存在性）→ Step 3（执行 --version）的明确顺序；③ 新增分支处理策略（Test-Path False → 必须重新扫描）；④ 新增「当前环境实测记录」区块 |
| **验证方式** | 按文档内 Step 1→2→3 顺序执行，应输出 `3.7.21` |
| **迁移方式** | 无需迁移，纯文档更新 |

### 2. 修改 `venv/version/opencode.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/opencode.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | `version: 1.16.2 → 1.17.0`，`date: 2026-06-08 → 2026-06-10` |
| **作用** | 同步 OpenCode CLI 实测版本 |
| **验证方式** | `& "${devroot}\venv\opencode\opencode.exe" --version` → `1.17.0` |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `venv/version/opencode-history.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/opencode-history.md` |
| **变更类型** | 追加 |
| **新增内容** | `\| 2026-06-10 \| **1.16.2 → 1.17.0** \|` |
| **作用** | 记录 OpenCode 版本升级历史 |
| **迁移方式** | 在末尾追加一行 |

### 4. 修改 `venv/version/cursor.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/cursor.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | `version: 3.7.12 → 3.7.21`，`date: 2026-06-06 → 2026-06-10` |
| **作用** | 同步 Cursor 实测版本 |
| **验证方式** | `& "C:\Program Files\cursor\resources\app\bin\cursor.cmd" --version` → `3.7.21` |
| **迁移方式** | 直接覆盖 |

### 5. 修改 `venv/version/cursor-history.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/cursor-history.md` |
| **变更类型** | 追加 |
| **新增内容** | `\| 2026-06-10 \| **3.7.12 → 3.7.21** \|` |
| **作用** | 记录 Cursor 版本升级历史 |
| **迁移方式** | 在末尾追加一行 |

### 6. 修改 `venv/version/python.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/python.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | `date: 2026-06-05 → 2026-06-10` |
| **作用** | 版本未变（`3.13.13`），仅刷新检测日期 |
| **验证方式** | `& "${devroot}\venv\py\python.exe" --version` → `3.13.13` |
| **迁移方式** | 直接覆盖 |

### 7. 修改 `venv/version/node.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/node.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | `date: 2026-06-05 → 2026-06-10` |
| **作用** | 版本未变（`v26.3.0`），仅刷新检测日期 |
| **验证方式** | `& "${devroot}\venv\node\node.exe" --version` → `v26.3.0` |
| **迁移方式** | 直接覆盖 |

### 8. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | `last_updated: 2026-06-10T11:37:38 → 2026-06-10T12:03:39`；`github_connectivity.api_search.latency_ms: 780 → 823`；`github_connectivity.api_issues.latency_ms: 891 → 935`；`github_connectivity.web_search_issues.latency_ms: 1207 → 1948`；`github_connectivity.web_issues_list.latency_ms: 817 → 1971`；所有 `verified_at` 同步更新 |
| **作用** | 同步真源检测最新延迟数据 |
| **验证方式** | 重新执行 `verify-runtime.ps1`，对比输出与索引一致 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。


## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 cursor.md 流程可读 | `read venv/version/cursor.md` | 包含 Step 1→2→3 及分支处理 |
| 2 | 确认 cursor.cmd 路径存在 | `Test-Path "C:\Program Files\cursor\resources\app\bin\cursor.cmd"` | `True`（以本机实测路径为准） |
| 3 | 确认 cursor 版本 | `& "C:\Program Files\cursor\resources\app\bin\cursor.cmd" --version` | `3.7.21` |
| 4 | 确认 opencode 版本 | `& "${devroot}\venv\opencode\opencode.exe" --version` | `1.17.0` |
| 5 | 确认 python 版本 | `& "${devroot}\venv\py\python.exe" --version` | `3.13.13` |
| 6 | 确认 node 版本 | `& "${devroot}\venv\node\node.exe" --version` | `v26.3.0` |
| 7 | 确认索引时间戳 | `read references/runtime/verified-runtime-index.json` | `last_updated` 为最新检测时间 |


## 四、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| cursor.md | 从 git history 恢复旧版本（`git checkout HEAD~ -- venv/version/cursor.md`） |
| 版本记录文件 | 从 git history 恢复（`git checkout HEAD~ -- venv/version/*.md venv/version/*-history.md`） |
| 真源索引 | 从 git history 恢复（`git checkout HEAD~ -- references/runtime/verified-runtime-index.json`） |


## 五、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-10-122635 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指出 cursor.md 仍使用 package.json 检测，要求改为 cursor.cmd --version；同时更新版本记录 |
| **下次修订条件** | Cursor/OpenCode 再次升级，或真源检测流程需要进一步调整 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
