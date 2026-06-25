---
title: deploy-git-isolated — 执行速查表
description: Agent 执行参考与用户终端速查，涵盖命令、配置、参数等所有可执行/可操作内容，不限定于命令行格式。
date: 2026-06-19
meta: {}
---

# deploy-git-isolated — 执行速查表（EXEC-CHEATSHEET）

> **本文件职责**：提供**可执行内容的速查**——命令、配置、参数、调用方式。Agent/用户/终端共享同一真源。
>
> **与 SOP.md 的区别**：SOP.md 回答「流程是什么、每一步怎么验收」；本文件回答「命令怎么执行、参数怎么填」。二者互补，不重叠。


## 目录约定

| 变量 | 实际路径 |
|------|---------|
| `${devroot}` | `D:\pjt\cursor\cs_py` |
| 隔离 Git 入口 | `${devroot}\venv\git\cmd\git.exe` |
| 隔离配置目录 | `${devroot}\venv\data-git` |
| 脚本目录 | `${devroot}\references\tasks\deploy-git-isolated\scripts` |


## Stage S1: 初始化（Step 1-3）

### Step 1: git init + 身份配置

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-01-init.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-01-init.ps1
```

> 前置：`.env` 中已配置 `GIT_USER_NAME` 和 `GIT_USER_EMAIL`


### Step 2: 生成安全 .gitignore

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-02-gitignore.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-02-gitignore.ps1
```


### Step 3: 生成 README.md

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-03-readme.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-03-readme.ps1
```


## Stage S2: 提交（Step 4-5）

### Step 4: 安全 add

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-04-stage.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-04-stage.ps1
```


### Step 5: git commit

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-05-commit.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-05-commit.ps1
```

> 可选参数：`-Message "自定义提交信息"`


## Stage S3: 连接（Step 6-8）

### Step 6: 添加 remote

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-06-remote.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-06-remote.ps1
```

> 前置：`.env` 中已配置 `GITHUB_REPO_URL`


### Step 7: git push（使用 PAT）

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-07-push.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-07-push.ps1
```

> 前置：`.env` 中已配置 `GITHUB_PAT`


### Step 8: 设置 upstream

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-08-upstream.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-08-upstream.ps1
```


## Stage S4: 安全检查（强制）

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\github-safety-check.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-tools\github-safety-check.ps1
```

> 输出：已跟踪文件 / staged 文件 / 未跟踪文件 / 敏感文件屏蔽验证


## Stage S5: 日常操作（通用包装器）

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\git-isolated.ps1" status
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\git-isolated.ps1" log --oneline
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\git-isolated.ps1" diff
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-tools\git-isolated.ps1 status
```


## Stage S5.3: 全链条部署（Python Workflow）

编排 Step 4-9（add → commit → remote → push → upstream → issue sync），
可一步到位完成完整流水线，支持 `--step` 单步执行。

**Agent:**
```powershell
# 全自动发布（从 staged 文件自动生成 commit message，推荐日常用）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --auto

# 完整部署（指定 commit message）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --message "feat: xxx"

# 仅执行单步（如仅 push，调试用）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --step 7 --message "feat: xxx"

# 指定 Issue 编号（Step 9 同步用）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --message "feat: xxx" --issue 1
```

**终端:**
```powershell
# 全自动发布
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --auto

# 完整部署
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --message "feat: xxx"
```

> 前置：`.env` 中已配置 `GIT_USER_NAME`、`GIT_USER_EMAIL`、`GITHUB_REPO_URL`、`GITHUB_PAT`


## Stage S5.5: 版本记录更新

### 全量自动检测与更新

**Agent:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}"
```

### 仅检测指定工具

```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}" --tool node
```

### 仅检测对比，不写入文件（dry-run）

```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}" --dry-run
```

> **覆盖工具**：自动扫描 `venv/version/*.md` 发现，当前为 python / node / opencode / cursor / chromium
> **历史记录**：变更自动追加到对应 `*-history.md`


## Stage S5.7: 时间戳生成（禁止现写）

> **铁律**：`.md` / `.json` 文件中的 `date` 字段和文件名时间戳，**必须使用**本工具生成，禁止在 Agent 回复中现写时间字符串。

### CLI 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--format <键名>` | 输出指定格式（默认 `local_iso`） | `--format filename_safe` |
| `--source <时间>` | 指定时间来源（默认当前时间） | `--source "2026-06-21"` `--source "2026-06-21T14:30:00"` |
| `--all` | 输出全部格式键值对 | — |
| `--json` | 以 JSON 输出全部格式 | — |

### 格式键名与输出示例

| 键名 | 说明 | 典型用途 | 示例输出 |
|------|------|---------|---------|
| `local_short` | 本地日期 | `.md` frontmatter `date` | `2026-06-25` |
| `local_long` | 本地时间紧凑 | 文件名（无冒号） | `2026-06-25T162111` |
| `local_iso` | 本地时间 ISO | `.md` 内联时间戳 | `2026-06-25T16:21:11` |
| `utc_short` | UTC 日期 | 跨时区日期标记 | `2026-06-25` |
| `utc_long` | UTC 时间紧凑 | GitHub Release 文件名 | `2026-06-25T082111Z` |
| `utc_iso` | UTC 时间 ISO | API 时间戳、日志 | `2026-06-25T08:21:11Z` |
| `filename_safe` | 文件名安全 | env-migration 文件名后缀 | `2026-06-25-162111` |

### 常用命令

**默认当前时间（local_iso）：**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --format local_iso
# → 2026-06-25T16:21:11
```

**文件名安全格式（env-migration 命名）：**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --format filename_safe
# → 2026-06-25-162111
```

**UTC ISO（GitHub / API 用）：**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --format utc_iso
# → 2026-06-25T08:21:11Z
```

**指定时间来源：**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --source "2026-06-21" --format utc_short
# → 2026-06-21

"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --source "2026-06-21T14:30:00" --format utc_iso
# → 2026-06-21T06:30:00Z
```

**全部格式（查看可用键名）：**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --all
# → local_short=2026-06-25
# → local_long=2026-06-25T162111
# → local_iso=2026-06-25T16:21:11
# → utc_short=2026-06-25
# → utc_long=2026-06-25T082111Z
# → utc_iso=2026-06-25T08:21:11Z
# → filename_safe=2026-06-25-162111
```

**JSON 输出（脚本消费）：**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --json
```

> **与 `schema/tool/get-timestamp.ps1` 的区别**：PS1 版为 legacy fallback；Python 版是当前推荐，支持更多格式、JSON 输出、指定时间来源。


## Stage S6: Lint 检查（脚本交付前必执行）

### 架构层级（禁止越级）

```
run-lint.py          → 唯一入口（编排层），支持 --fix 三阶段闭环
  ↓ 通过 py_lib 统一入口
py_lib.load_plugins  → 聚合层（拓扑排序、依赖补齐、registry 注入）
  ↓ 加载
py-plugins/*         → 底座层（具体检测/修复能力）
```

> **铁律**：
> 1. **所有 lint 操作必须通过 `run-lint.py` 唯一入口**，禁止绕行其他工具。
> 2. workflow 禁止直接 `import` plugin。所有能力必须通过 `py_lib.load_plugins()` 获取。
> 3. 修复能力由各插件内部 `fix=True` 参数提供，`run-lint.py` 编排三阶段闭环。


### run-lint.py — 唯一 lint 入口

通过 py_lib 加载全部 lint 插件，统一执行、统一报告。
支持 `--fix` 三阶段闭环：detect → amend → re-verify。

#### Phase 1: 检测

**单文件列表（新建/更新文档后必执行）：**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.md" "path/to/file.py"
```

**目录全量扫描：**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}"
```

#### Phase 1-3: 检测→修复→验证闭环（推荐）

```powershell
# 单文件三阶段闭环
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.md" --fix

# 目录全量三阶段闭环
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --fix
```

**输出示例：**
```
[Phase 1] 首次 lint 检测
  ❌ docs/README.md — 1 处违规 (CRLF)
  ❌ docs/README.md — 1 处违规 (缺少 meta)

[Phase 2] 执行修复（lint_encoding + md_lint）
  ✅ 修复完成，共修复 1 个文件

[Phase 3] 重新 lint 验证
  ✅ docs/README.md (CRLF 已修复)
  ❌ docs/README.md — 缺少必填字段 meta（不可自动修复）
```

**注意**：可自动修复的违规类型见下方「可修复 vs 仅检测」表。不可修复项需人工介入。

#### 覆盖度审计（对照 manifest 检查规则完整性）

```powershell
# audit 模式：读取 schema/json/lint-rules-manifest.json → 加载插件 → 交叉校验覆盖度
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --audit
```

**输出示例**：
```
[run-lint --audit] 覆盖度审计
  manifest 版本: 1.0.0
  manifest 登记插件: 7 个
  manifest 登记规则: 27 条
  ✅ 插件覆盖度: 100%（7/全匹配）
  各插件规则明细:
    link_checker (v1.3.0): 3 条（可修复 0 条）
    lint_encoding (v1.0.0): 9 条（可修复 3 条）
    ...
  结论: ✅ 审计完成
```

#### 按需单类型（通过 profile 筛选）

```powershell
# 仅 JSON
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-json

# 仅 PowerShell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-ps1

# 仅 Python
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-python

# 仅编码/BOM/CRLF
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-encoding
```


### 可修复 vs 仅检测

| 插件 | 可自动修复 | 修复内容 | 仅检测 |
|------|-----------|---------|-------|
| `lint_encoding` | ✅ | 双 BOM、去/加 BOM、CRLF→LF | — |
| `md_lint` | ✅ | description/date 拼接、正文 `---` 污染 | 缺失 frontmatter、缺失必填字段 |
| `lint_json` | ❌ | — | JSON 语法 |
| `lint_python` | ❌ | — | Python 语法 |
| `lint_ps1` | ❌ | — | PowerShell 语法 |
| `link_checker` | ❌ | — | MD 内部链接断裂 |


### 文件类型 → 触发插件速查

| 文件类型 | 语法检测 | 编码检测 | 链接检测 |
|---------|---------|---------|---------|
| `.md` / `.mdc` | `md_lint` | `lint_encoding` | `link_checker` |
| `.py` | `lint_python` | `lint_encoding` | — |
| `.json` / `.jsonc` | `lint_json` | `lint_encoding` | — |
| `.ps1` | `lint_ps1` | `lint_encoding` | — |
| `.js` / `.ts` / `.html` / 等 | — | `lint_encoding` | — |


## Stage S7: Issue 同步

### 追加评论（记录 commit）

**Agent:**
```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\github-sync-issue.ps1" -Mode comment -IssueNumber 1 -Body "commit abc123: 新增功能"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\ps-tools\github-sync-issue.ps1 -Mode comment -IssueNumber 1 -Body "commit abc123: 新增功能"
```

### 获取 Issue 详情

```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\github-sync-issue.ps1" -Mode get-issue -IssueNumber 1
```

### 列出评论

```powershell
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\github-sync-issue.ps1" -Mode list-comments -IssueNumber 1
```


## 高级：插件 Profile 筛选

**直接点源 github-lib 时指定 Profile：**

```powershell
# 使用预设 profile（deploy/issue-sync/minimal）
. "${devroot}\references\tasks\deploy-git-isolated\scripts\github-lib.ps1" -Profile "issue-sync"

# 命令行覆盖：排除特定插件
. "${devroot}\references\tasks\deploy-git-isolated\scripts\github-lib.ps1" -Profile "issue-sync" -Exclude @("git-checks")

# 仅加载指定插件（自动补齐依赖）
. "${devroot}\references\tasks\deploy-git-isolated\scripts\github-lib.ps1" -Include @("constants", "github-api")
```

> 优先级：`-Include/-Exclude` > `-Profile` > `_default`（向后兼容，加载全部）


## CI/CD 自动化调用

```powershell
# 方式 A：通过 git-isolated.ps1 包装器（推荐）
& "${devroot}\references\tasks\deploy-git-isolated\scripts\ps-tools\git-isolated.ps1" push

# 方式 B：直接调用 + HOME 重定向（脚本内使用）
$env:HOME = "${devroot}\venv\data-git"
& "${devroot}\venv\git\cmd\git.exe" push origin main

# 方式 C：临时身份覆盖（多仓库 CI）
$env:GIT_CONFIG_GLOBAL = "${devroot}\venv\data-git\.gitconfig-special"
& "${devroot}\venv\git\cmd\git.exe" push origin main
```


## 关联文档

| 文件 | 用途 |
|------|------|
| `../SOP.md` | 标准操作流程（Step 契约、验收条件、回滚路径） |
| `../TASK-TOOLS-INDEX.md` | 本 task 全部可用工具索引（本地 + 外部引用） |
| `../docs/PLUGIN-ARCHITECTURE.md` | 插件化点源架构设计文档 |
| `../README.md` | 场景化决策入口 |


*速查表版本: v1.0*  
*创建时间: 2026-06-18*  
*修订: 从 SOP-CHEATSHEET.md 更名，明确 EXEC（Execution）语义，不限定于 CMD*
