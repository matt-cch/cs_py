---
title: deploy-git-isolated — 执行速查表
description: Agent 执行参考与用户终端速查，涵盖命令、配置、参数等所有可执行/可操作内容，不限定于命令行格式。
date: 2026-07-23
meta:
  version: 1.1
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
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --auto

# 完整部署（指定 commit message）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx"

# 仅执行单步（如仅 push，调试用）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --step 7 --message "feat: xxx"

# 指定 Issue 编号（Step 9 同步用）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx" --issue 1
```

**终端:**
```powershell
# 全自动发布
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --auto

# 完整部署
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx"
```

> 前置：`.env` 中已配置 `GIT_USER_NAME`、`GIT_USER_EMAIL`、`GITHUB_REPO_URL`、`GITHUB_PAT`


## Stage S5.4: Polyrepo 部署（Python Workflow）

编排 Step 0a→0b→0c→4→4.5→5→6→7→8→9→10，支持单仓库与 polyrepo 两种场景。

**Agent:**
```powershell
# 单仓库完整部署（target 与 devroot 相同，仍须显式传入）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}"

# Polyrepo 完整部署（target 指向另一仓库）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}\apps\repos\jywl-team\jywl-lab"

# 指定 commit message
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}" --message "feat: xxx"

# 仅执行 preflight + manifest 审计（Step 0）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}" --step 0

# 仅执行 add + staged 扫描 + commit（Step 4→5）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}" --step 4
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}" --message "feat: xxx"
```

> 前置：`.env` 中已配置 `GIT_USER_NAME`、`GIT_USER_EMAIL`、`GITHUB_REPO_URL`、`GITHUB_PAT`
> **铁律**：`--target` 强制必填，不可省略。`--devroot` 仅用于验证与 CWD 一致。


## Stage S5.4.1: Polyrepo 初始化（Create + Clone + Smoke Push）

用于从 0 到 1 新建 polyrepo 仓库并完成本地→remote 联动验证。

**Agent:**
```powershell
# Step 1: 创建 GitHub 远程仓库
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-create.py" `
    --devroot "${devroot}" `
    --owner "matt-cch" `
    --repo-name "jywl-settlement" `
    --public `
    --add-readme `
    --description "三方物流企业结算模块" `
    --output "${devroot}\venv\tmp\polyrepo-init-step1-create.json"

# Step 2: Clone 到本地并配置 git identity
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-repo-clone.py" `
    --devroot "${devroot}" `
    --repo-url "https://github.com/matt-cch/jywl-settlement" `
    --target-dir "${devroot}\apps\repos\matt-cch\jywl-settlement" `
    --output "${devroot}\venv\tmp\polyrepo-init-step2-clone.json"

# Step 3: 本地 diff → add → commit（workflow phase）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-phase-git-local-diff-add-commit.py" `
    --devroot "${devroot}" `
    --target "${devroot}\apps\repos\matt-cch\jywl-settlement" `
    --files ".emptydir GOAL.md" `
    --message "init: add .emptydir and GOAL.md" `
    --output "${devroot}\venv\tmp\polyrepo-init-step3-commit.json"

# Step 4: Smoke push（无弹窗安全 push）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-push-smoke.py" `
    --devroot "${devroot}" `
    --target "${devroot}\apps\repos\matt-cch\jywl-settlement" `
    --remote "origin" `
    --branch "main" `
    --output "${devroot}\venv\tmp\polyrepo-init-step4-push.json"
```

**终端:**
```powershell
# 创建远程仓库
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-create.py" --devroot "${devroot}" --owner "matt-cch" --repo-name "jywl-settlement" --public --add-readme --output "${devroot}\venv\tmp\polyrepo-init-step1-create.json"

# Clone 到本地
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-repo-clone.py" --devroot "${devroot}" --repo-url "https://github.com/matt-cch/jywl-settlement" --target-dir "${devroot}\apps\repos\matt-cch\jywl-settlement" --output "${devroot}\venv\tmp\polyrepo-init-step2-clone.json"

# 本地 commit
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-phase-git-local-diff-add-commit.py" --devroot "${devroot}" --target "${devroot}\apps\repos\matt-cch\jywl-settlement" --message "init: add .emptydir and GOAL.md" --output "${devroot}\venv\tmp\polyrepo-init-step3-commit.json"

# Smoke push
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-push-smoke.py" --devroot "${devroot}" --target "${devroot}\apps\repos\matt-cch\jywl-settlement" --remote "origin" --branch "main" --output "${devroot}\venv\tmp\polyrepo-init-step4-push.json"
```

> 前置：`.env` 中已配置 `GITHUB_PAT`、`GITHUB_USERNAME`、`GIT_USER_NAME`、`GIT_USER_EMAIL`
> **调用链**：create → clone → diff-add-commit → push-smoke，四步顺序执行，前一步 exit 0 后方可进入下一步


## Stage S5.4.2: JSON 配置原子编辑

> **替代手敲 `edit` 修改 JSON**。用 RFC 6902 JSON Pointer 做结构化编辑，根治缩进微差、逗号遗漏、CRLF 污染、Shell 中文编码损坏等问题。

### 标准三步流程（必须遵守）

**凡涉及 JSON 文件修改，禁止直接用 `edit` 工具，必须按以下三步执行：**

```
Step 1: write 工具写入 patch 内容到 venv/tmp/patch.json（不经 Shell）
Step 2: atomic-config-edit-json.py --batch @venv/tmp/patch.json --backup
Step 3: run-lint.py 验证修改后的 JSON
```

> **铁律**：
> 1. 中文内容 / 复杂对象 / 批量更新 → **必须**先 write 到文件，再用 `@file` 传入，禁止直接塞进 `--batch` 参数。
> 2. 单条短字符串且无中文（如替换时间戳）→ 可直接 `--operation + --json-pointer + --value`。
> 3. 关键索引文件（verified-task-index.json、verified-runtime-index.json 等）→ **必须**加 `--backup`。
> 4. 修改后 **必须**执行 `run-lint.py` 验证 JSON 语法 + 编码。

### 单条简单操作（无中文短 value）

**Agent:**
```powershell
# 替换时间戳（无中文，可直接传参）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
    --file "${devroot}\references\runtime\verified-task-index.json" `
    --operation replace `
    --json-pointer "/meta/last_updated" `
    --value '"2026-07-22T17:00:00"'
```

### 批量操作（含中文 / 复杂对象 / 多条——标准流程）

**Step 1: write 工具写入 patch 文件（不经 Shell）**

```
write → venv/tmp/patch.json
```

内容示例：
```json
[
  {"op": "replace", "path": "/meta/last_updated", "value": "2026-07-22T17:00:00"},
  {"op": "add", "path": "/available_scripts_and_tools/my-tool", "value": {"name": "我的工具", "description": "中文描述"}}
]
```

**Step 2: 执行编辑（带备份）**

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
    --file "${devroot}\references\runtime\verified-task-index.json" `
    --batch "@venv/tmp/patch.json" `
    --backup
```

**Step 3: lint 验证**

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" `
    --devroot "${devroot}" `
    --files "${devroot}\references\runtime\verified-task-index.json"
```

### 仅预览（dry-run）

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-config-edit-json.py" `
    --file "${devroot}\references\runtime\verified-task-index.json" `
    --operation replace `
    --json-pointer "/meta/last_updated" `
    --value '"2026-07-22T17:00:00"' `
    --dry-run
```

### 常见踩坑速查

| 踩坑场景 | 错误做法 | 正确做法 |
|---------|---------|---------|
| 用 `edit` 改 JSON | `edit` 改 oldString，因缩进微差失败 | 用 `atomic-config-edit-json.py` |


## Stage S5.6: CSV 列转换（配置驱动）

> **适用范围**：任何需要 CSV 列内容转换的场景（如 Invoice date 批量更新、状态字段替换、正则清洗等）。
> **核心原则**：配置驱动，改 JSON 配置即可适配新场景，py 框架不变。

### 调用链条（调用者义务）

```
1. 定位源 CSV 所在目录
      ↓
2. 检查该目录下是否存在 csv-transform-<场景>.json 配置
      ↓
3. 若存在 → 读取其中 "outfile_naming" 规则 → 按 rule + example 构造 outfile 文件名
   若不存在 → 调用者自行决定 outfile（建议与源文件同目录）
      ↓
4. 将构造好的 outfile 绝对路径显式传入 --outfile → 执行本脚本
```

> **铁律**：本脚本不负责自动推断 outfile 名称，命名规则由配置真源驱动，调用者必须显式构造后传入。

### 标准调用（默认配置：Invoice date → today_ymd）

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-csv-column-transform.py" `
    --input "D:\\demo\\FEILIKS_FAPINV.20260722-2607.csv" `
    --outfile "D:\\demo\\FEILIKS_FAPINV.20260723.csv" `
    --output "${devroot}\venv\tmp\polyrepo-wf-step3-transform.json"
```

### 自定义配置（多列转换）

**Step 1: write 工具写入配置 JSON**

```json
{
  "transforms": {
    "Invoice date": {"type": "today_ymd"},
    "Status": {"type": "fixed", "value": "ACTIVE"},
    "Amount": {"type": "regex_replace", "pattern": ",", "replacement": ""}
  }
}
```

**Step 2: 执行转换**

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-csv-column-transform.py" `
    --input "D:\\demo\\data.csv" `
    --outfile "D:\\demo\\data_processed.csv" `
    --config "${devroot}\venv\tmp\transform-config.json" `
    --output "${devroot}\venv\tmp\csv-transform-manifest.json"
```

### 参数语义（严格区分）

| 参数 | 语义 | 必填 | 说明 |
|------|------|------|------|
| `--input` | 源 CSV 路径（或目录） | ✅ | 目录时自动扫描 *.csv 取最新 |
| `--outfile` | 业务产物：转换后的 CSV | ✅ | 只读源文件，写入新文件。命名约定：基于源文件名，将日期段替换为当天 YYYYMMDD，去掉版本后缀（如 `-2607`）。例：`FEILIKS_FAPINV.20260722-2607.csv` → `FEILIKS_FAPINV.20260727.csv` |
| `--output` | 审计产物：manifest JSON | 可选 | workflow 调用时必须显式传入；未传时回退 `venv/tmp/atomic-csv-column-transform-manifest-{ts}.json` |
| `--config` | 转换规则配置 JSON | 可选 | 未传时使用内置默认 |
| `--dry-run` | 预览模式 | 可选 | 输出前 3 行转换对比，不写入任何文件 |

### 内置 transform 类型

| type | 说明 | 额外字段 |
|------|------|---------|
| `today_ymd` | 今天 YYYYMMDD（UTC） | 无 |
| `today_iso` | 今天 ISO 日期 | 无 |
| `fixed` | 固定值 | `value` |
| `regex_replace` | 正则替换 | `pattern`, `replacement` |
| `empty` | 清空列 | 无 |
| 中文直接塞 `--batch` | Shell 编码损坏，中文变乱码 | 先 `write` 到文件，再用 `@file` |
| 修改后忘记验证 | JSON 语法错误未被发现 | 修改后必执行 `run-lint.py` |
| 关键索引无备份 | 改坏后无法回滚 | 加 `--backup`，.bak 文件自动保留 |
| 数组追加用 `--operation add` | 误覆盖已有元素 | 路径用 `/-/`（如 `/trigger_words/-`）表示末尾追加 |
| 只想更新对象部分字段 | `--operation replace` 覆盖整个对象 | 用 `--operation merge` 深度合并 |
| 路径用了 `$.foo` 或 `.foo.bar` | 混淆 JSON Path / jq 风格与 JSON Pointer | 必须用 `/foo/bar` 格式，脚本会拦截并提示 |


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


## Stage S6: Git 前置验证（Preflight）

### 执行 Git Preflight 验证

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-preflight.py"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-preflight.py"
```

> 前置：`.env` 中已配置 `GIT_USER_NAME` 和 `GIT_USER_EMAIL`
> 职责：验证 git.exe 可用性、身份配置、当前分支、working tree 状态、.gitignore 安全屏蔽


### 执行部署特有 Preflight 验证

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-deploy-preflight.py"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-deploy-preflight.py"
```

> 前置：`.env` 中已配置 `GITHUB_REPO_URL` 和 `GITHUB_PAT`
> 职责：验证 .env 部署配置、分支保护（禁止 master 直接 push）、agent 插件加载、git 空目录保留


### 执行 Staged 内容安全扫描（必须在 git add 后）

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-staged-after-add.py"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-staged-after-add.py"
```

> 前置：已执行 `git add`
> 职责：强制扫描 staged 文件内容中的敏感模式（API key、PAT、私钥等）。无 staged 文件时报错。


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


## Stage S6.5: Chrome / 浏览器 Session 检测

### 检测 Chrome Session 登录态（头条系）

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py"
```

> 职责：读取 Chrome Cookies DB，检测登录态标志（sessionid / passport_auth_status 等）、新鲜度（10 分钟窗口）、TTL 有效期。
> 输出：stdout 格式化报告 + `--output` 结构化 JSON manifest（供 pipeline 复用）。
> **结论分级**：A. 有效 / B. 残留 / C. 残缺 / D. 失效（明确无歧义）。

**指定 manifest 输出路径（pipeline 复用）:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py" --output "${devroot}\venv\tmp\pipeline-manifest.json"
```

**指定 Chrome Profile 路径:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py" --user-data-dir "D:\custom\chrome-profile"
```

**检测其他域名（如 GitHub）:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py" --domain-patterns "%github%" --key-cookies "session_id,auth_token"
```


## Stage S6.5.5: Chrome 交互式登录 / 续期

> **设计意图**：提供标准化交互式登录 CLI，让用户在持久化 Chrome Profile 中手动完成登录或续期操作。与 `run.py` 等临时脚本不同，本 CLI 是 pipeline 的一环，通过 `--output` 显式指定 manifest 路径供下游复用。
> **禁止行为**：禁止自行写 Playwright 登录脚本；所有登录/续期操作必须通过本入口复用已有 browser_session 插件和持久化 Profile。

### 基本用法（交互式窗口）

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-chrome-login-interactive.py" --output "${devroot}\venv\tmp\login-manifest.json"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-chrome-login-interactive.py" --output "${devroot}\venv\tmp\login-manifest.json"
```

> 执行后自动弹出 Chrome 窗口，在目标网站完成登录/续期后关闭窗口即可。
> `--output` 为**必填**参数，指定 manifest 落盘路径，供 pipeline 连贯复用。

### 指定 Chrome Profile 路径

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-chrome-login-interactive.py" --output "${devroot}\venv\tmp\login-manifest.json" --user-data-dir "D:\custom\chrome-profile"
```

### 指定初始导航 URL

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-chrome-login-interactive.py" --output "${devroot}\venv\tmp\login-manifest.json" --start-url "https://www.toutiao.com"
```

### 参数语义

| 参数 | 语义 | 必填 | 说明 |
|------|------|------|------|
| `--output` | manifest 输出路径 | ✅ | JSON 文件路径，记录登录后 Cookies 摘要和元数据 |
| `--user-data-dir` | Chrome Profile 路径 | 可选 | 默认 `devroot/venv/data-chrome` |
| `--start-url` | 初始导航 URL | 可选 | 窗口打开后首先访问的页面，默认不导航 |
| `--devroot` | devroot 路径 | 可选 | 默认自动探测；polyrepo 场景下显式传入 |


## Stage S6.6: 文章下载（头条 / 通用 URL）

> **设计意图**：将「从 URL 提取文章正文」封装为标准化 CLI 工具。对头条域名额外执行 Session 登录态检测门禁，未登录则拒绝执行，防止在登录墙前做无效提取。
> **禁止行为**：禁止自行写 Playwright 脚本下载文章；所有文章提取必须通过本入口复用已有 Chrome Session 和 JS 注入链路。

### 基本用法（headless，默认输出到 devroot/out/articles/）

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://www.toutiao.com/article/123456/"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://www.toutiao.com/article/123456/"
```

> 前置：Chrome Session 已登录头条（通过 `atomic-chrome-login-interactive.py --output <path>` 交互式登录）
> 输出：`devroot/out/articles/<slug>.md` + `<slug>_files/img-001.jpg`


### 指定标签（写入 Markdown frontmatter）

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --tags "AI,编程"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --tags "AI,编程"
```


### 指定输出目录

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --output-dir "D:/articles"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --output-dir "D:/articles"
```


### 显示浏览器窗口（headed，调试用）

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --headed
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --headed
```


### 显式指定 devroot（polyrepo 场景）

**Agent:**
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --devroot "D:/workspace/other-repo"
```

**终端:**
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/post" --devroot "D:/workspace/other-repo"
```


### 参数语义

| 参数 | 语义 | 必填 | 说明 |
|------|------|------|------|
| `--url` | 文章 URL | ✅ | 支持任意 URL；头条域名（toutiao.com/cn）会额外触发 Session 检测 |
| `--tags` | 标签列表 | 可选 | 逗号分隔，如 `"AI,编程"`，写入输出 Markdown 的 frontmatter |
| `--output-dir` | 输出目录 | 可选 | 默认 `devroot/out/articles/` |
| `--headed` | 显示浏览器窗口 | 可选 | 非 headless 模式，用于调试；与 `--headless` 互斥 |
| `--devroot` | devroot 路径 | 可选 | 默认自动探测；polyrepo 场景下显式传入以定位 Chrome Profile 和输出目录 |
| `--skip-preflight` | 跳过前置检查 | 可选 | ⚠️ **仅本地调试，生产环境禁止** |


### 输出格式

- **Markdown 文件**：`{slug}.md`，含 YAML frontmatter（title / description / date / source / tags）
- **图片目录**：`{slug}_files/`（文章中引用的图片下载到本地，Markdown 改为相对路径）
- **Obsidian 兼容**：frontmatter 和链接格式均兼容 Obsidian 解析


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


## Stage S7.2: GitHub CLI / PR 自闭环（gh）

> 前提：已完成 deploy push，当前在 feature 分支且 `origin/<branch>` 已存在。gh CLI 隔离部署于 `venv/gh/bin/gh.exe`，配置隔离于 `venv/data-gh`。

**Agent：**
```powershell
# 全自动 PR 闭环（推荐）：AI 生成 title+body → create → merge(admin) → 删分支 → 同步 master
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-pr.py" --auto --admin

# 仅创建 PR（不自动 merge，留人工 review）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\gh-pr-create.py" --auto --base master

# 仅合并（PR 已存在）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\gh-pr-merge.py" --strategy rebase --admin

# gh CLI 前置验证演示（gh.exe + PAT + 认证状态）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-preflight-demo.py"
```

**headless 认证（终端/CI，无需 `gh auth login`）：**
```powershell
$env:GH_TOKEN = $env:GITHUB_PAT
$env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"
& "${devroot}\venv\gh\bin\gh.exe" repo create my-new-project --private --source . --push
```

> 认知澄清：`gh pr merge` 是 GitHub REST API 的命令行封装，合并发生在远端服务器，本地 master 需 pull 才同步（workflow 默认已做）。


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


## Stage S8: 运行时域（真源检测与下载）

### 真源检测

```powershell
# 全量检测
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}"

# 单工具检测
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}" --tool node
```

### 运行时下载

```powershell
# 检测+下载一体化（推荐，全程带进度条）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\runtime-common\wf-runtime-full.py" --devroot "${devroot}" --tools node,opencode_cli

# 检测+下载（不替换，默认保留文件）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py" --devroot "${devroot}" --tool-name node

# 强制下载并替换（需确认无运行中进程）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py" --devroot "${devroot}" --tool-name node --force

# 显示下载进度
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py" --devroot "${devroot}" --tool-name node --show-progress
```

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
