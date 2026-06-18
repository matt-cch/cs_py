---
title: deploy-git-isolated — 执行速查表
description: Agent 执行参考与用户终端速查，涵盖命令、配置、参数等所有可执行/可操作内容，不限定于命令行格式。
date: 2026-06-18
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


## Stage S6: Issue 同步

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
