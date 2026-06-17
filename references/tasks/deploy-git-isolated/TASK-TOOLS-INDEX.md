---
title: deploy-git-isolated 可用工具速查表
description: 本 task 全部可用工具的索引、职责、路径与边界说明。包含本地专属脚本与外部通用工具的引用链路，防止重复造轮子。
date: 2026-06-16
---

# deploy-git-isolated 可用工具速查表

> **与 SOP-CHEATSHEET 的区别**：本文件回答「有什么工具、在哪里、什么时候用」；SOP-CHEATSHEET 回答「命令怎么执行」。二者互补，不重叠。

---

## 1. 本地专属脚本（scripts/）

本 task 的核心脚本，全部位于 `references/tasks/deploy-git-isolated/scripts/`。

### 1.1 部署流水线（Step 1-8）

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `github-step-01-init.ps1` | git init + 身份配置 | 首次部署隔离 Git | ready |
| `github-step-02-gitignore.ps1` | 生成安全 .gitignore | 初始化仓库防护 | ready |
| `github-step-03-readme.ps1` | 生成 README.md | 初始化仓库文档 | ready |
| `github-step-04-stage.ps1` | 安全 add + 显示 staged | 准备提交 | ready |
| `github-step-05-commit.ps1` | git commit | 提交变更 | ready |
| `github-step-06-remote.ps1` | 添加 remote | 连接 GitHub | ready |
| `github-step-07-push.ps1` | git push（从 .env 读取 PAT） | 推送到远程 | ready |
| `github-step-08-upstream.ps1` | 设置 upstream | 建立分支追踪 | ready |

### 1.2 Issue 同步（新增）

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `github-sync-issue.ps1` | Issue 同步入口：create / update / comment / list-comments / get-issue | commit 后同步变更历史到 Issue | ready |
| `github-sync-issue-config.json` | 配置真源：模板、labels、endpoint 映射 | 调整 Issue 格式时修改此文件，不动脚本 | ready |

> **与 github-create-issue.ps1 的区别**：`github-create-issue.ps1` 是 Phase 3 的遗留脚本，功能单一（仅 create）；`github-sync-issue.ps1` 是统一入口，覆盖全部 Issue 生命周期操作，使用插件架构（github-api.ps1），推荐新场景使用。

### 1.3 安全与检查

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `github-safety-check.ps1` | 综合安全检查（tracked/staged/敏感文件） | push 前必执行 | ready |
| `git-verify-isolation.ps1` | 验证隔离效果（独立使用） | 怀疑 PATH 泄漏时 | ready |

### 1.4 通用包装器

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `git-isolated.ps1` | 隔离 Git 通用包装器（透传 git 子命令） | 日常 git status/log/diff 等 | ready |
| `git-clone-isolated.ps1` | 隔离方式 Clone | 克隆新仓库 | ready |
| `git-config-global.ps1` | 设置隔离全局身份（独立使用） | 仅需改身份时 | ready |
| `git-multi-identity.ps1` | 多身份切换演示 | 教学/验证 | ready |

### 1.5 共享库体系

| 文件 | 职责 | 扩展方式 |
|------|------|---------|
| `github-lib.ps1` | 共享库聚合入口（拓扑排序加载插件） | 不直接修改，通过 JSON 驱动 |
| `lib-sort-rules.json` | 插件依赖图与加载顺序真源 | 追加条目即可 |
| `lib-plugins/*.ps1` | 6 个共享函数插件 | 新建 `.ps1` + 登记 JSON |

> 插件架构详情见：`docs/PLUGIN-ARCHITECTURE.md`
> 新增插件：`github-api.ps1`（GitHub REST API 封装，自动 UTF-8 encoding）

---

## 2. 外部通用工具引用（runtime / schema/tool）

本 task 执行过程中**不应自行实现**以下能力，应直接调用已登记的通用工具。

| 工具名 | 全局路径 | 登记索引 | 本 task 中的用途 | 边界说明 |
|--------|---------|---------|----------------|---------|
| **lint-json.py** | `schema/tool/lint-json.py` | `verified-task-index.json` → `lint-json` | 验证 `.json` 文件语法（如 `task-scenario-triggers.json`、`ENTRY.json` 修改后） | JSON lint 是通用能力，不在 task 本地实现 |
| **lint-ps1.ps1** | `schema/tool/lint-ps1.ps1` | `verified-task-index.json` → `lint-ps1` | 验证本 task 下所有 `.ps1` 脚本语法 | PS 语法检查是通用能力 |
| **check-file-encoding.ps1** | `schema/tool/check-file-encoding.ps1` | `verified-task-index.json` → `check-file-encoding` | 检查所有落盘文件的 BOM/CRLF/LF | 编码检查统一走此工具 |
| **file-write-helper.py** | `schema/tool/file-write-helper.py` | `verified-task-index.json` → `file-write-helper` | 写入含中文的 `.ps1` 时处理 UTF-8 BOM | 文件写入 helper 是通用能力 |
| **get-timestamp.ps1** | `schema/tool/get-timestamp.ps1` | `verified-task-index.json` → `get-timestamp` | 生成带时间戳的文件名或记录操作时间 | 时间戳生成是通用能力 |
| **verify-runtime.ps1** | `references/runtime/verify-runtime.ps1` | `verified-task-index.json` → `verify-runtime` | 真源检测时扫描 `venv/git/` 是否存在 | 运行时真源检测是全局能力 |
| **download-runtime-tool.ps1** | `references/runtime/download-runtime-tool.ps1` | `verified-task-index.json` → `download-runtime-tool` | 如需升级 MinGit 版本时使用 | 运行时下载是全局能力，本 task 只消费 |
| **trigger-index** | `references/runtime/verified-trigger-index.json` | `verified-task-index.json` → `trigger-index` | 查询 trigger 归属、注册新 trigger | trigger 治理是全局能力 |

> **铁律**：以上工具已存在且已登记，本 task 禁止自行实现同类功能。新增需求时先查 `verified-task-index.json` → `available_scripts_and_tools`。

---

## 3. 边界矩阵（什么时候用什么）

| 需求 | 首选工具 | 次选/备选 | 禁止行为 |
|------|---------|----------|---------|
| 验证 JSON 语法 | `lint-json.py`（通用） | — | 禁止用 `python -c` 内嵌验证 |
| 验证 PS 语法 | `lint-ps1.ps1`（通用） | — | 禁止不验证直接交付 `.ps1` |
| 检查文件编码 | `check-file-encoding.ps1`（通用） | — | 禁止现写编码检查命令 |
| 写入含中文 `.ps1` | `file-write-helper.py`（通用） | — | 禁止 Shell 重定向写 `.ps1` |
| 生成时间戳文件名 | `get-timestamp.ps1`（通用） | — | 禁止内嵌 `Get-Date` 拼文件名 |
| git init / push | `github-step-01/07.ps1`（本地） | — | 禁止裸命令操作 Git |
| push 前安全检查 | `github-safety-check.ps1`（本地） | — | 禁止跳过安全检查直接 push |
| 日常 git 操作 | `git-isolated.ps1`（本地） | — | 禁止裸 `git` 调用（可能命中系统版） |
| 真源扫描 | `verify-runtime.ps1`（通用） | — | 禁止自行实现文件存在性扫描 |
| 下载 MinGit | `download-runtime-tool.ps1`（通用） | — | 禁止自行写 `curl`/`Invoke-WebRequest` 下载 |
| Issue 同步（create/update/comment） | `github-sync-issue.ps1`（本地） | — | 禁止裸 API 调用，禁止重复造轮子 |

---

## 4. 速查命令

### 4.1 本地脚本调用（Agent 格式）

```powershell
# Step 1-8
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# 安全检查
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-safety-check.ps1"

# 通用包装器（示例：git status）
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" status

# Issue 同步（示例：追加评论记录 commit）
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-sync-issue.ps1" -Mode comment -IssueNumber 1 -Body "commit abc123: 新增 GOAL.md"
```

> 完整命令见：`scripts/SOP-CHEATSHEET.md`

### 4.2 外部通用工具调用

```powershell
# JSON lint（修改 task-scenario-triggers.json / ENTRY.json 后必执行）
"${devroot}\venv\py\python.exe" "${devroot}\schema\tool\lint-json.py" -v "${devroot}\references\tasks\deploy-git-isolated\task-scenario-triggers.json"

# PS lint（修改 .ps1 后必执行）
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# 编码检查（落盘后必执行）
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# 文件写入 helper（含中文 .ps1）
"${devroot}\venv\py\python.exe" "${devroot}\schema\tool\file-write-helper.py" --config "${devroot}\venv\tmp\job.ini"
```

---

## 5. 关联文件导航

| 文件 | 用途 |
|------|------|
| `README.md` | 场景化决策入口（5 个场景速查） |
| `ENTRY.json` | 机器真源（脚本清单、状态、版本历史） |
| `task-scenario-triggers.json` | 触发条件真源（5 场景 trigger 映射） |
| `scripts/SOP-CHEATSHEET.md` | 命令速查（Agent/终端双格式） |
| `docs/PLUGIN-ARCHITECTURE.md` | 插件化架构设计文档 |
| `DESIGN.md` | 设计决策与踩坑记录 |

---

*速查表版本: v1.0*  
*创建时间: 2026-06-16*  
*关联全局索引: `references/runtime/verified-task-index.json`*
