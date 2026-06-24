---
title: deploy-git-isolated 可用工具速查表
description: 本 task 全部可用工具的索引、职责、路径与边界说明。包含本地专属脚本与外部通用工具的引用链路，防止重复造轮子。
date: 2026-06-20
meta:
  version: 1.2
---

# deploy-git-isolated 可用工具速查表

> **与 EXEC-CHEATSHEET 的区别**：本文件回答「有什么工具、在哪里、什么时候用」；EXEC-CHEATSHEET 回答「命令怎么执行」。二者互补，不重叠。


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
| `fetch_issue.py` | Python CLI：获取 Issue 完整内容（含评论） | 通过 py_lib 调用 github_api 插件查看 Issue | ready |

> **与 github-create-issue.ps1 的区别**：`github-create-issue.ps1` 是 Phase 3 的遗留脚本，功能单一（仅 create）；`github-sync-issue.ps1` 是统一入口，覆盖全部 Issue 生命周期操作，使用插件架构（github-api.ps1），推荐新场景使用。
> **Python 版补充**：`fetch_issue.py` 走 py_lib 插件体系，与 PS 版 `github-sync-issue.ps1 -Mode get-issue/list-comments` 功能互补，输出格式对齐。

### 1.3 安全与检查

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `github-safety-check.ps1` | 综合安全检查（tracked/staged/敏感文件） | push 前必执行 | ready |
| `git-verify-isolation.ps1` | 验证隔离效果（独立使用） | 怀疑 PATH 泄漏时 | ready |

### 1.4 Lint 插件体系

**可用能力**（由 `py_lib` 插件体系动态提供）：

lint 体系覆盖 JSON / PowerShell / Python / Encoding / Markdown / Link 等验证。具体有哪些插件可用、各自的标签与职责，**通过入口 API 动态发现**，禁止在静态文档中硬编码插件清单。

```python
from py_lib import list_plugins
lint_plugins = list_plugins(tags=["lint"])
```

> **铁律**：
> 1. **`run-lint.py` 是 lint 唯一入口**，所有 lint 操作必须通过它。
> 2. 插件清单的真源是 `py-sort-rules.json`，人类速查只说明能力类别。
> 3. workflow 层禁止直接 `import` plugin。

**CLI 入口**（唯一）：

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `run-lint.py` | **Lint 唯一入口**。全量/按 `--profile`/按 `--files` 路由，支持 `--fix` 三阶段闭环、`--audit` 覆盖度审计 | 新建/更新文档后必执行；规则审计时用 `--audit` | ready |

**覆盖度审计**（新增，规则清单对照）：

```powershell
# 对照 lint-rules-manifest.json 检查规则覆盖度
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --audit
```

**规则清单真源**：`schema/json/lint-rules-manifest.json`（所有 lint 规则 ID、插件归属、可修复性、文件类型路由）

**典型工作流（一步闭环）**：
```powershell
# 单文件 lint→amend→lint 闭环（新建/更新文档后）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.md" --fix

# 目录全量 lint→amend→lint 闭环
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --fix

# 仅检测（不修复）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.py"
```

**文件类型 → 触发插件自动路由**：

| 文件 | 语法检测 | 编码检测 | 链接检测 |
|------|---------|---------|---------|
| `.md` / `.mdc` | `md_lint` | `lint_encoding` | `link_checker` |
| `.py` | `lint_python` | `lint_encoding` | — |
| `.json` / `.jsonc` | `lint_json` | `lint_encoding` | — |
| `.ps1` | `lint_ps1` | `lint_encoding` | — |
| `.js` / `.ts` / 等 | — | `lint_encoding` | — |

**可修复 vs 仅检测**：见 `scripts/EXEC-CHEATSHEET.md` Stage S6 表格。

> 依赖：`py_lib.py`（v1.2.0） + `py-sort-rules.json`（v1.1.0）拓扑排序加载。
> 版本管理 API：`from py_lib import __version__`（py_lib 自身版本）、`get_rules_version()`（py-sort-rules 版本）、`registry.rules_version`（运行时规则版本）。
> 插件通过 `__plugin_registry__` 访问 devroot。

### 1.3 版本记录更新

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `update-version.py` | **Workflow：版本记录更新**。自动发现 venv/version/ 下工具 → 调用 runtime_version 插件实测本地版本 → 对比记录版本 → 更新 .md（frontmatter date + version 表格）+ 追加 `*-history.md` | 记一版 version / 更新 venv/version | ready |

> **与 5 个独立 get-*-version.ps1 的区别**：`update-version.py` 是统一 Workflow 入口，自动发现、自动对比、自动更新文件；`schema/tool/get-*-version.ps1` 是单工具实测脚本（遗留，仍可用作 fallback）。
> **架构**：update-version.py（Workflow）→ py_lib.load_plugins() → runtime_version 插件（detect 接口）→ process_runner（subprocess 封装）。

**CLI 用法**：
```powershell
# 全量自动检测与更新
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}"

# 仅检测指定工具
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}" --tool node

# 仅检测对比，不写入文件（dry-run）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}" --dry-run
```

### 1.4 安全审计（Security Audit）

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `workflow-security-audit.py` | **Workflow：部署前敏感内容巡检**。组装 security_audit 插件的五 Phase 流程（pattern_scan / git_tracking），输出人类可读报告 + JSON 报告 | commit/push 前必执行，确保无 API key / PAT / 私钥泄露 | ready |
| `security_audit.py` | 底层插件：提供 pattern scan、git tracking 验证、报告聚合能力 | 被 workflow 调用，不直接作为 CLI 入口 | ready |

**架构**：
```
workflow-security-audit.py（Workflow）→ py_lib.load_plugins(profile="validation") → security_audit 插件
  Phase 1: pattern_scan → 对 tracked 文件正则扫描敏感模式
  Phase 4: git_tracking → 验证 .env / config.json / key.txt 未被 git 追踪
  Phase 5: summary → 聚合报告，输出 pass / warn / fail
```

**CLI 用法**：
```powershell
# 完整审计（默认 HEAD~10..HEAD）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}"

# 指定 commit 范围
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}" --commit-range "HEAD~5..HEAD"

# 仅执行特定 phase
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}" --phases pattern_scan git_tracking

# 输出 JSON 报告（自动落盘到 venv/tmp/）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}" --output "${devroot}\venv\tmp\audit.json"
```

> **关联规范**：`schema/docs/security-audit-spec.md`（审计流程、敏感模式定义、严重等级）
> **关联 schema**：`schema/json/security-audit-schema.json`（报告数据结构契约）

### 1.5 时间戳生成

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `get-timestamp.py` | Workflow CLI：通过 py_lib 调用 timestamp + time_source 插件，输出格式化时间 | Agent 写入 .md / .json 的 date/frontmatter 字段时获取标准格式 | ready |
| `timestamp.py` | 底层插件：接收 datetime 对象，格式化为多种字符串 | py_lib 插件体系内调用，只做格式化不生产时间 | ready |
| `time_source.py` | 底层插件：**统一时间来源**。默认当前时间，也支持解析外部时间字符串 | 被 timestamp 依赖；也可独立调用解析时间 | ready |

**架构**：
```
time_source.parse_time(source) → (dt_local, dt_utc)
                ↓
timestamp.format_timestamp(dt_local, dt_utc) → {local_short, local_iso, utc_iso, ...}
```

**CLI 用法**：
```powershell
# 默认当前时间
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --format local_iso

# 指定时间来源（ISO 8601 格式）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --source "2026-06-21" --format utc_short
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --source "2026-06-21T14:30:00" --format utc_iso

# 输出全部格式
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --all
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --json
```

**插件用法（通过 py_lib）**：
```python
registry = load_plugins(devroot="...", tags=["utility"])

# 默认当前时间
ts = registry.timestamp.get_now()
print(ts["local_iso"])

# 指定时间来源
dt_local, dt_utc = registry.time_source.parse_time("2026-01-15T09:00:00")
ts = registry.timestamp.format_timestamp(dt_local, dt_utc)
print(ts["local_iso"])   # 2026-01-15T09:00:00
print(ts["utc_iso"])     # 2026-01-15T01:00:00Z
```

**格式键名速查**：
| 键名 | 说明 | 示例 |
|------|------|------|
| `local_short` | 本地日期（短） | `2026-06-21` |
| `local_long` | 本地时间（长，紧凑） | `2026-06-21T143218` |
| `local_iso` | 本地时间（ISO 扩展） | `2026-06-21T14:32:18` |
| `utc_short` | UTC 日期（短） | `2026-06-21` |
| `utc_long` | UTC 时间（长，紧凑） | `2026-06-21T063218Z` |
| `utc_iso` | UTC 时间（ISO 扩展） | `2026-06-21T06:32:18Z` |
| `filename_safe` | 文件名安全格式 | `2026-06-21-143218` |

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
| `github-lib.ps1` | 共享库聚合入口（拓扑排序 + Profile 筛选 + 依赖自动补齐） | 不直接修改，通过 JSON 驱动 |
| `lib-sort-rules.json` | 插件依赖图、加载顺序真源、**Profile 定义** | 追加条目 / 新增 profile |
| `lib-plugins/*.ps1` | 6 个共享函数插件 | 新建 `.ps1` + 登记 JSON + 可选绑定 profile |

**Profile 用法速查**：
```powershell
# 默认（向后兼容，加载全部）
. $libPath

# 使用预设 profile（deploy/issue-sync/minimal）
. $libPath -Profile "issue-sync"

# 命令行覆盖（最高优先级）
. $libPath -Profile "issue-sync" -Exclude @("git-checks")
```

> 插件架构详情见：`docs/PLUGIN-ARCHITECTURE.md`
> PS 插件：`github-api.ps1`（GitHub REST API 封装，自动 UTF-8 encoding）
> Python 插件：`github_api.py`（GitHub REST API 封装，urllib 实现，与 PS 版功能对等）

### 1.6 归档 Workflow

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `archive_project.py` | 项目归档主编排：scan → compress → verify 三阶段闭环 | 归档 cs_py / venv 分组 | ready |
| `archive_cs_py.py` | 快捷入口：归档 cs_py 分组 | `python archive_cs_py.py --format 7z` | ready |
| `archive_venv.py` | 快捷入口：归档 venv 分组 | `python archive_venv.py --format 7z` | ready |

> 架构：三层 + 配置契约。Workflow 通过 `py_lib.load_plugins(profile="archive")` 调用 `archive_config` / `archive_scanner` / `archive_compressor` 插件。
> 配置真源：`py-tools/archive-groups.json`（黑白名单、输出格式）

### 1.7 部署编排 Workflow（Python 版）

Python 版部署流水线，与 PS 版 Step 1-8 功能对等。`workflow-deploy-full.py` 编排 Step 4-9（add → commit → remote → push → upstream → issue sync），按序调用 `py-steps/` 下的独立 step 脚本，任何一步失败立即停止。

**底座脚本**（`py-steps/`，被 workflow 按序调用）：

| 脚本 | 职责 | 对应 PS 版 |
|------|------|-----------|
| `step-04-github-deploy-add.py` | 安全 add + 显示 staged | `github-step-04-stage.ps1` |
| `step-04-github-init-only.py` | 仅 init（部分场景） | — |
| `step-05-github-commit.py` | git commit | `github-step-05-commit.ps1` |
| `step-06-github-remote.py` | 添加 remote | `github-step-06-remote.ps1` |
| `step-07-github-push.py` | git push（从 .env 读取 PAT） | `github-step-07-push.ps1` |
| `step-08-github-upstream.py` | 设置 upstream | `github-step-08-upstream.ps1` |
| `step-09-github-sync-issue.py` | Issue 同步 | `github-sync-issue.ps1` |

**编排 Workflow**：

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `workflow-deploy-full.py` | **全链条部署 Workflow**：编排 Step 4-9，调用 py-steps 分步执行。支持 `--step` 单步执行、`--message` 自定义提交信息、`--issue` 指定 Issue 编号。自动生成 AI 语义摘要和 Issue comment meta。 | 执行完整 GitHub 部署流水线 | ready |

**架构**：
```
workflow-deploy-full.py（Workflow 编排）
  ├── [Preflight] agent 插件 + .env 前置验证
  ├── py-steps/step-04-github-deploy-add.py
  ├── generate-ai-summary.py（Step 4→5 之间，使用 --cached）
  ├── py-steps/step-05-github-commit.py
  ├── [更新 meta commit hash]
  ├── py-steps/step-06-github-remote.py
  ├── py-steps/step-07-github-push.py
  ├── py-steps/step-08-github-upstream.py
  └── py-steps/step-09-github-sync-issue.py（接收 --meta）
```

**CLI 用法**：
```powershell
# 全自动发布（从 staged 文件自动生成 commit message）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --auto

# 完整全链条部署（指定 commit message）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --message "feat: xxx"

# 仅执行单步（如仅 push，调试用）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --step 7 --message "feat: xxx"

# 指定 Issue 编号（Step 9 用）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --message "feat: xxx" --issue 1
```

> **与 PS 版的关系**：PS 版（`github-step-0N-*.ps1`）为原始实现，功能完备；Python 版（`py-steps/step-0N-*.py` + `workflow-deploy-full.py` 编排）为同能力重构版，提供更灵活的编排参数和自动化（AI 摘要、动态 meta）。**凡涉及 Step 4-9 的操作，必须使用 Python 版 workflow，禁止手动逐条调用 ps-steps。**


## 2. 外部通用工具引用（runtime / schema/tool）

本 task 执行过程中**不应自行实现**以下能力，应直接调用已登记的通用工具。

| 工具名 | 全局路径 | 登记索引 | 本 task 中的用途 | 边界说明 |
|--------|---------|---------|----------------|---------|
| **lint-json.py** | `schema/tool/lint-json.py` | `verified-task-index.json` → `lint-json` | 验证 `.json` 文件语法（如 `task-scenario-triggers.json`、`ENTRY.json` 修改后） | JSON lint 是通用能力，不在 task 本地实现 |
| **lint-ps1.ps1** | `schema/tool/lint-ps1.ps1` | `verified-task-index.json` → `lint-ps1` | 验证本 task 下所有 `.ps1` 脚本语法 | PS 语法检查是通用能力 |
| **check-file-encoding.ps1** | `schema/tool/check-file-encoding.ps1` | `verified-task-index.json` → `check-file-encoding` | 检查所有落盘文件的 BOM/CRLF/LF | 编码检查统一走此工具 |
| **file-write-helper.py** | `schema/tool/file-write-helper.py` | `verified-task-index.json` → `file-write-helper` | 写入含中文的 `.ps1` 时处理 UTF-8 BOM | 文件写入 helper 是通用能力 |
| **verify-runtime.ps1** | `references/runtime/verify-runtime.ps1` | `verified-task-index.json` → `verify-runtime` | 真源检测时扫描 `venv/git/` 是否存在 | 运行时真源检测是全局能力 |
| **download-runtime-tool.py** | `references/runtime/download-runtime-tool.py` | `verified-task-index.json` → `download-runtime-tool` | 如需升级 MinGit 版本时使用 | 运行时下载是全局能力，本 task 只消费 |
| **trigger-index** | `references/runtime/verified-trigger-index.json` | `verified-task-index.json` → `trigger-index` | 查询 trigger 归属、注册新 trigger | trigger 治理是全局能力 |

> **铁律**：以上工具已存在且已登记，本 task 禁止自行实现同类功能。新增需求时先查 `verified-task-index.json` → `available_scripts_and_tools`。


## 3. 边界矩阵（什么时候用什么）

| 需求 | 首选工具 | 次选/备选 | 禁止行为 |
|------|---------|----------|---------|
| 验证 JSON 语法 | `lint_json.py`（本地，py_lib 插件） | `schema/tool/lint-json.py`（通用） | 禁止用 `python -c` 内嵌验证 |
| 验证 PS 语法 | `lint_ps1.py`（本地，py_lib 插件） | `schema/tool/lint-ps1.ps1`（通用） | 禁止不验证直接交付 `.ps1` |
| 验证 Python 语法 | `lint_python.py`（本地，py_lib 插件） | — | 禁止不验证直接交付 `.py` |
| 检查文件编码 | `lint_encoding.py`（本地，py_lib 插件） | `schema/tool/check-file-encoding.ps1`（通用） | 禁止现写编码检查命令 |
| 写入含中文 `.ps1` | `file-write-helper.py`（通用） | — | 禁止 Shell 重定向写 `.ps1` |
| 生成时间戳文件名 | `get-timestamp.py`（本地 workflow） | — | 禁止内嵌 `Get-Date` 拼文件名 |
| git init / push | `github-step-01/07.ps1`（本地） | — | 禁止裸命令操作 Git |
| push 前安全检查 | `github-safety-check.ps1`（本地） | — | 禁止跳过安全检查直接 push |
| 日常 git 操作 | `git-isolated.ps1`（本地） | — | 禁止裸 `git` 调用（可能命中系统版） |
| 真源扫描 | `verify-runtime.ps1`（通用） | — | 禁止自行实现文件存在性扫描 |
| 下载 MinGit | `download-runtime-tool.py`（通用） | — | 禁止自行写 `curl`/`Invoke-WebRequest` 下载 |
| Issue 同步（create/update/comment） | `github-sync-issue.ps1`（本地） | — | 禁止裸 API 调用，禁止重复造轮子 |
| Issue 内容查看（body + 评论） | `fetch_issue.py`（本地，py_lib 插件） | `github-sync-issue.ps1 -Mode get-issue/list-comments` | 禁止裸 API 调用 |
| 插件筛选加载 | `github-lib.ps1` -Profile（本地） | — | 禁止全量加载冗余插件 |
| 项目归档（cs_py） | `archive_cs_py.py`（本地 workflow） | `archive_project.py --group cs_py` | 禁止裸 `7z`/`zip` 命令归档 |
| 项目归档（venv） | `archive_venv.py`（本地 workflow） | `archive_project.py --group venv` | 禁止裸 `7z`/`zip` 命令归档 |
| 版本记录更新 | `update-version.py`（本地 workflow） | — | 禁止自行写 `python -c` 测版本 |
| 获取时间戳 | `get-timestamp.py`（本地 workflow） | — | 禁止内嵌 `Get-Date` 拼文件名 |
| 全链条部署（Step 4-9） | `workflow-deploy-full.py`（本地 workflow） | PS 版 Step 1-8 | 禁止手动逐条调用 ps-steps |


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

# 获取 Issue 完整内容（Python 版，含评论）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\fetch_issue.py" --issue-number 1

# 全链条部署（Python Workflow）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --message "feat: xxx"
```

> 完整命令见：`scripts/EXEC-CHEATSHEET.md`
> 标准流程与验收条件见：`SOP.md`

### 4.2 外部通用工具调用

```powershell
# 全量 lint（交付前必执行，推荐）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}"

# 按需 lint
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-json
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-ps1
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-python
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-encoding

# JSON lint（修改 task-scenario-triggers.json / ENTRY.json 后必执行）
"${devroot}\venv\py\python.exe" "${devroot}\schema\tool\lint-json.py" -v "${devroot}\references\tasks\deploy-git-isolated\task-scenario-triggers.json"

# PS lint（修改 .ps1 后必执行）
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# lint→amend→lint 工作流（workflow → py_lib → lint_encoding）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-lint-amend-lint.py" --devroot "${devroot}" --dir "references\tasks\deploy-git-isolated"

# 编码检查（落盘后必执行）
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# 文件写入 helper（含中文 .ps1）
"${devroot}\venv\py\python.exe" "${devroot}\schema\tool\file-write-helper.py" --config "${devroot}\venv\tmp\job.ini"

# 归档 cs_py（快捷入口）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\archive_cs_py.py" --stage all --format 7z

# 归档 venv（快捷入口）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\archive_venv.py" --stage all --format 7z

# 归档全量（主编排层）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\archive_project.py" --group cs_py venv --stage all --format 7z

# 全链条部署（Python Workflow）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --message "feat: xxx"
```


## 5. 关联文件导航

| 文件 | 用途 |
|------|------|
| `README.md` | 场景化决策入口（5 个场景速查） |
| `ENTRY.json` | 机器真源（脚本清单、状态、版本历史） |
| `task-scenario-triggers.json` | 触发条件真源（5 场景 trigger 映射） |
| `SOP.md` | 标准流程（Step 契约 + Ralph Loop） |
| `scripts/EXEC-CHEATSHEET.md` | 执行速查（命令+配置+参数） |
| `scripts/py-tools/run-lint.py` | 统一 lint CLI 入口（JSON/PS1/Python/Encoding，支持 `--files` 单文件列表） |
| `scripts/py-tools/update-version.py` | 版本记录更新 Workflow（自动发现 → 实测 → 更新 .md + history） |
| `scripts/py-tools/fetch_issue.py` | 获取 GitHub Issue 完整内容（含评论） |
| `scripts/py-tools/workflow-deploy-full.py` | **全链条部署 Workflow**：编排 Step 4-9，支持 --step/--issue 参数 |
| `scripts/py-plugins/lint_*.py` | Lint 插件（json/ps1/python/encoding） |
| `scripts/py-plugins/github_api.py` | GitHub REST API 封装（Python 插件） |
| `schema/json/lint-rules-manifest.json` | Lint 规则全局清单（7 插件、27 规则、5 可修复，审计时对照） |
| `schema/json/plugin-result-schema.json` | 插件返回格式 JSON Schema 真源（v1.0.0） |
| `schema/docs/plugin-result-schema.md` | 插件返回格式规范文档（人类可读） |
| `schema/py/models.py` | Pydantic / Dataclass 备选 Model 实现 |
| `docs/PLUGIN-ARCHITECTURE.md` | 插件化架构设计文档 |
| `DESIGN.md` | 设计决策与踩坑记录 |


*速查表版本: v1.1*  
*创建时间: 2026-06-16*  
*更新时间: 2026-06-24*  
*关联全局索引: `references/runtime/verified-task-index.json`*
