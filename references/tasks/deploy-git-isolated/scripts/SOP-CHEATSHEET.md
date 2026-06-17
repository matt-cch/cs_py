---
title: 隔离 Git 部署 — 命令速查表
description: Agent 执行参考与用户终端速查，所有命令指向 scripts/ 下的同一 .ps1 真源。
date: 2026-06-16
---

# 隔离 Git 部署 — 命令速查表

> **真源唯一**：本速查表中所有命令均调用 `references/tasks/deploy-git-isolated/scripts/` 下的 .ps1 脚本，Agent/用户/终端共享同一文件。

## 目录约定

| 变量 | 实际路径 |
|------|---------|
| `${devroot}` | `D:\pjt\cursor\cs_py` |
| 隔离 Git 入口 | `${devroot}\venv\git\cmd\git.exe` |
| 隔离配置目录 | `${devroot}\venv\data-git` |
| 脚本目录 | `${devroot}\references\tasks\deploy-git-isolated\scripts` |

---

## Step 1: git init + 身份配置

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1
```

> 前置：`.env` 中已配置 `GIT_USER_NAME` 和 `GIT_USER_EMAIL`

---

## Step 2: 生成安全 .gitignore

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-02-gitignore.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-02-gitignore.ps1
```

---

## Step 3: 生成 README.md

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-03-readme.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-03-readme.ps1
```

---

## Step 4: 安全 add（仅 .gitignore + README）

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-04-stage.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-04-stage.ps1
```

---

## Step 5: git commit

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-05-commit.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-05-commit.ps1
```

> 可选参数：`-Message "自定义提交信息"`

---

## Step 6: 添加 remote

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-06-remote.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-06-remote.ps1
```

> 前置：`.env` 中已配置 `GITHUB_REPO_URL`

---

## Step 7: git push（使用 PAT）

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-07-push.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-07-push.ps1
```

> 前置：`.env` 中已配置 `GITHUB_PAT`

---

## Step 8: 设置 upstream

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-08-upstream.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-step-08-upstream.ps1
```

---

## 共享库（点源）

各 step 脚本通过点源导入 `github-lib.ps1`，提供编码处理、.env 读取、路径常量等共享能力。

- `github-lib.ps1` — 共享库聚合入口（拓扑排序加载插件）
- 插件架构详情见：`../docs/PLUGIN-ARCHITECTURE.md`
- 工具索引与边界说明见：`../TASK-TOOLS-INDEX.md`

## 9. Issue 同步

### 9.1 追加评论（记录 commit）

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-sync-issue.ps1" -Mode comment -IssueNumber 1 -Body "commit abc123: 新增功能"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-sync-issue.ps1 -Mode comment -IssueNumber 1 -Body "commit abc123: 新增功能"
```

### 9.2 获取 Issue 详情

```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-sync-issue.ps1" -Mode get-issue -IssueNumber 1
```

### 9.3 列出评论

```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-sync-issue.ps1" -Mode list-comments -IssueNumber 1
```

---

## 10. 插件 Profile 筛选（高级）

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

---

## 11. 安全检查（综合）

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-safety-check.ps1"
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\github-safety-check.ps1
```

> 输出：已跟踪文件 / staged 文件 / 未跟踪文件 / 敏感文件屏蔽验证

---

## 关联文档

| 文件 | 用途 |
|------|------|
| `../TASK-TOOLS-INDEX.md` | 本 task 全部可用工具索引（本地 + 外部引用） |
| `../docs/PLUGIN-ARCHITECTURE.md` | 插件化点源架构设计文档 |
| `../README.md` | 场景化决策入口 |

---

*速查表版本: v1.2*  
*创建时间: 2026-06-16*  
*修订: v1.2 — 移除工具索引与插件架构细节，迁移至 TASK-TOOLS-INDEX.md 与 PLUGIN-ARCHITECTURE.md，本文件仅保留命令速查*
