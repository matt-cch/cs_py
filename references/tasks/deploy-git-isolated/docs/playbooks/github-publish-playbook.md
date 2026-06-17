---
title: GitHub 发布操作手册 — deploy-git-isolated task 发布实录
description: 记录将 deploy-git-isolated task 发布到 GitHub 仓库的完整过程，包括三篇文章的原理启发、实施步骤、形成的脚本与踩坑记录。
date: 2026-06-17
---

# GitHub 发布操作手册 — deploy-git-isolated task 发布实录

> **适用范围**：`references/tasks/deploy-git-isolated/` 目录的 GitHub 发布操作。  
> **阅读对象**：需要理解本次发布设计思路、复现操作步骤、或维护相关脚本的 Agent / Human。  
> **关联文档**：DESIGN.md（设计决策）、ENTRY.json（机器真源）、task-canonical-baseline.md（规范基线）

---

## 一、设计灵感来源 — 三篇文章的原理启发

本次发布不是简单的 "git add + push"，而是借鉴了三篇技术文章的核心设计哲学，将 Git 从"版本工具"提升为"工作流基础设施"。

### 1.1 GBrain — Markdown + Git 作为人类与 AI 共享的真值源

| 文章 | 《爆火 14k 星！GBrain 彻底解决 AI Agent 失忆痛点》 |
|------|-----------------------------------------------------|
| **核心命题** | 用 Markdown + Git 作为人类与 AI 共享的真值源，解决 Agent "失忆"问题 |
| **本 task 的借鉴** | `deploy-git-isolated/` 目录内全部是 Markdown + JSON 配置，天然适合作为"真值源"。发布到 GitHub 后，设计决策（DESIGN.md）、操作规范（SOP-CHEATSHEET.md）、踩坑记录（gotchas/）全部以文件形式存在，人类可读、Agent 可解析、Git 可回溯。 |
| **落地体现** | 目录结构即知识图谱：README.md 是入口，ENTRY.json 是真源索引，scripts/ 是技能工作流，changelog/ 是时间线。 |

### 1.2 goal / Autoloop — Git 分支作为 Agent 的工作记忆

| 文章 | 《GitHub 的 Autoloop：Agent 工作流的 Git 分支持久化模式》 |
|------|-----------------------------------------------------------|
| **核心命题** | 用 Git 分支和 PR 作为 Agent 的"工作记忆"，解决跨会话状态持久化 |
| **本 task 的借鉴** | 不直接在 `main`/`master` 上工作，而是创建 **长期运行分支** `task/deploy-git-isolated`，每次执行追加 commits。分支即工作记忆，PR 是人工介入点，Issue 是结构化进度日志。 |
| **落地体现** | `git checkout -b task/deploy-git-isolated` → 开发 → commit → PR → merge。分支命名即任务标识，永不与其他任务分支冲突。 |

### 1.3 Tolaria — 文件优先、版本优先、离线优先

| 文章 | 《Tolaria：面向AI时代的跨平台Markdown知识库管理工具》 |
|------|-------------------------------------------------------|
| **核心命题** | 文件优先（原生 Markdown）、版本优先（原生 Git）、离线优先 |
| **本 task 的借鉴** | `.gitignore` 采用**白名单模式**——默认排除所有根级目录，只放行目标路径。这确保 push 的内容严格可控，不会误带 venv/、debug/、out/ 等隔离产物。同时支持渐进式放开：未来想 push 其他目录时，只需修改 `.gitignore` 追加放行规则。 |
| **落地体现** | ```gitignore
/*/
!/references/
/references/*
!/references/tasks/
/references/tasks/*
!/references/tasks/deploy-git-isolated/
``` |

---

## 二、实施过程 — 完整时间线

### Phase 0: 前置分析（用户对话触发）

| 时间 | 事件 |
|------|------|
| 2026-06-17 | 用户提出：将 `references/tasks/deploy-git-isolated/` 发布到 GitHub `matt-cch/cs_py` 仓库，其他目录保持不 push。借鉴三篇文章原理，用 Git 管理版本、用 Issues 记录变更历史。 |
| | Agent 读取 `deploy-git-isolated/` 目录，分析自包含性，确认无运行时外部依赖（脚本引用 `schema/tool/` 等外部工具均为开发时 lint/验证工具，不影响目录完整性）。 |

### Phase 1: 环境准备

| 时间 | 事件 |
|------|------|
| 2026-06-17 | **修改 `.gitignore`**：从"黑名单排除敏感文件"改为"白名单只放行目标目录"。策略：`/*/` 排除所有根级子目录，然后逐层 `!/references/` → `!/references/tasks/` → `!/references/tasks/deploy-git-isolated/`。 |
| | **追加 `skills-lock.json` 排除**：防止运行时生成的技能锁定文件被误带。 |
| | **创建 `.gitattributes`**：在 `deploy-git-isolated/` 目录内强制 LF 换行符（`* text eol=lf`），确保 Windows / Linux / GitHub 三者一致。 |
| | **修改 `constants.ps1`**：将硬编码 `$devroot = 'D:\pjt\cursor\cs_py'` 改为动态探测（从 `$PSScriptRoot` 向上遍历找 `venv\git\cmd\git.exe`），实现跨机器可复用。 |

### Phase 2: Git 操作

| 时间 | 事件 |
|------|------|
| 2026-06-17 | `git checkout -b task/deploy-git-isolated` — 从 `master` 创建长期运行分支。 |
| | `git add references/tasks/deploy-git-isolated/` — 精确添加目标目录（43 个文件）。 |
| | `git commit -m "feat: deploy-git-isolated v0.5.0"` — 初始提交。 |
| | `git push -u origin task/deploy-git-isolated` — 首次推送。 |

### Phase 3: 自动化 Issue 创建

| 时间 | 事件 |
|------|------|
| 2026-06-17 | **编写 `github-create-issue.ps1`**：调用 GitHub REST API (`POST /repos/{owner}/{repo}/issues`)，自动从 `.env` 读取 PAT，提取当前分支 commit 信息生成 Issue body，创建带 `task-active` label 的追踪 Issue。 |
| | **踩坑**：PowerShell 5.1 `Invoke-RestMethod` 发送 JSON body 默认使用系统 GBK 编码，导致 GitHub 收到中文乱码。修复：显式 `[System.Text.Encoding]::UTF8.GetBytes($bodyJson)` + `ContentType 'application/json; charset=utf-8'`。 |
| | **Issue #1 创建成功**：`[Task Tracking] deploy-git-isolated 变更历史`，包含 commit hash、分支名、变更摘要、后续追踪指引。 |

### Phase 4: 修复与追加提交

| 时间 | 事件 |
|------|------|
| 2026-06-17 | `github-create-issue.ps1` 追加到目录，commit 并 push。 |
| | 修复 Issue #1 乱码内容（通过 Python 脚本 PATCH API，将 body 更新为正确 UTF-8）。 |
| | 最终 commit：`c913cc4 fix: github-create-issue.ps1 UTF-8 encoding for API body`。 |

---

## 三、形成的脚本与文件

### 3.1 新增/修改的文件清单

| 文件 | 路径 | 作用 | 变更类型 |
|------|------|------|---------|
| `.gitignore` | `D:\pjt\cursor\cs_py\.gitignore` | 白名单模式：默认排除所有根级目录，只放行目标路径 | 重写 |
| `.gitattributes` | `references/tasks/deploy-git-isolated/.gitattributes` | 强制 LF 换行符，确保跨平台一致 | 新增 |
| `constants.ps1` | `references/tasks/deploy-git-isolated/scripts/lib-plugins/constants.ps1` | 动态探测 devroot（从脚本位置向上遍历） | 修改 |
| `github-create-issue.ps1` | `references/tasks/deploy-git-isolated/scripts/github-create-issue.ps1` | 自动化创建 GitHub Issue 脚本 | 新增 |

### 3.2 github-create-issue.ps1 核心能力

```powershell
# 用法
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-create-issue.ps1"

# 自动完成：
# 1. 从 .env 读取 GITHUB_PAT / GITHUB_USERNAME / GITHUB_REPO_URL
# 2. 提取当前分支最新 commit 信息（hash / message / date）
# 3. 生成结构化 Markdown Issue body
# 4. 调用 GitHub API 创建带 task-active label 的 Issue
# 5. 输出生成的 Issue URL 供下游消费
```

**关键编码修复**（PowerShell 5.1 踩坑点）：
```powershell
# 错误做法（导致中文乱码）：
# Invoke-RestMethod ... -Body $body -ContentType 'application/json'

# 正确做法：
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyJson)
Invoke-RestMethod ... -Body $bodyBytes -ContentType 'application/json; charset=utf-8'
```

---

## 四、最终结果

### 4.1 GitHub 仓库状态

| 属性 | 值 |
|------|-----|
| **仓库** | https://github.com/matt-cch/cs_py |
| **分支** | `task/deploy-git-isolated` |
| **Commits** | 3 个 |
| **Files** | 44 个（`references/tasks/deploy-git-isolated/` 完整目录） |

### 4.2 Commit 历史

```
c913cc4 fix: github-create-issue.ps1 UTF-8 encoding for API body
352f8bd feat: add github-create-issue.ps1 for automated Issue creation
e94e8e5 feat: deploy-git-isolated v0.5.0
```

### 4.3 Issue #1

| 属性 | 值 |
|------|-----|
| **Number** | #1 |
| **Title** | `[Task Tracking] deploy-git-isolated 变更历史` |
| **State** | `open` |
| **Labels** | `task-active` |
| **URL** | https://github.com/matt-cch/cs_py/issues/1 |
| **Body** | 包含 commit hash、分支名、变更摘要、后续追踪指引 |

### 4.4 目录结构在 remote 上的效果

```
cs_py/                           ← 仓库根（其他路径未跟踪）
├── .gitignore                   ← 白名单策略基线
├── README.md                    ← 仓库基线
└── references/
    └── tasks/
        └── deploy-git-isolated/ ← 唯一被跟踪的子目录
            ├── .gitattributes   ← LF 强制
            ├── DESIGN.md
            ├── ENTRY.json
            ├── README.md
            ├── ...
            └── scripts/
                └── github-create-issue.ps1
```

---

## 五、踩坑记录

### 5.1 PowerShell 5.1 Invoke-RestMethod 默认编码陷阱

| 维度 | 详情 |
|------|------|
| **现象** | `github-create-issue.ps1` 首次执行后，GitHub Issue 标题和正文中文全部显示为 `????` |
| **根因** | PowerShell 5.1 `Invoke-RestMethod` 的 `-Body` 参数在传入字符串时，默认使用系统 ANSI 编码（Windows 上为 GBK）发送 HTTP body。GitHub API 收到 GBK 编码的中文后无法解析，显示为问号。 |
| **修复** | 显式将 JSON 字符串转为 UTF-8 bytes：`[System.Text.Encoding]::UTF8.GetBytes($bodyJson)`，并设置 `ContentType: 'application/json; charset=utf-8'`。 |
| **教训** | PowerShell 5.1 的 HTTP 客户端层默认编码与脚本文件编码（UTF-8 BOM）不一致，发送中文时必须手动干预编码层。 |

### 5.2 .gitignore 白名单模式的渐进式放开

| 维度 | 详情 |
|------|------|
| **现象** | 用户要求"只 push 目标目录，其他保持为空"，同时要求"未来可渐进式放开其他目录"。 |
| **方案** | 采用 `/*/` 排除所有根级子目录，然后逐层 `!` 放行。新增目录时只需在 `.gitignore` 中追加对应的 `!` 规则，无需重写整个文件。 |
| **验证** | `git check-ignore -v <路径>` 可验证任意路径的 ignore 状态。 |

### 5.3 constants.ps1 硬编码路径的跨机器问题

| 维度 | 详情 |
|------|------|
| **现象** | `constants.ps1` 中硬编码 `$devroot = 'D:\pjt\cursor\cs_py'`，clone 到其他机器后路径失效。 |
| **修复** | 改为从 `$PSScriptRoot` 向上遍历，动态探测包含 `venv\git\cmd\git.exe` 的目录作为 devroot。 |
| **局限** | 当前探测逻辑假设脚本始终在 devroot 的子目录下。若目录结构大幅变更（如 devroot 与 venv/ 分离），探测会失效。后续优化方向：引入环境变量 fallback 或 `.env` 配置项。 |

### 5.4 .ps1 文件 UTF-8 BOM 双保险

| 维度 | 详情 |
|------|------|
| **现象** | 编写 `github-create-issue.ps1` 时，初次落盘未加 BOM，PowerShell 5.1 解析中文注释时语法错误。 |
| **修复** | 通过 `[System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding $true))` 重写文件，确保 BOM 存在。 |
| **教训** | 含中文的 `.ps1` 必须 UTF-8 with BOM，这是项目硬性规则，不可省略。 |

---

## 六、后续操作指引

### 6.1 创建 Pull Request（手动）

1. 访问 https://github.com/matt-cch/cs_py/pull/new/task/deploy-git-isolated
2. base: `master` ← compare: `task/deploy-git-isolated`
3. PR 标题：`[Task] deploy-git-isolated v0.5.0`
4. PR 描述中填写：`Relates to #1`

### 6.2 未来复用 github-create-issue.ps1

```powershell
# 为其他 task 创建追踪 Issue 时：
# 1. 复制脚本到对应 task 的 scripts/ 目录
# 2. 修改脚本中的 $issueTitle 和 Issue body 模板
# 3. 执行：
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\references\tasks\<task-name>\scripts\github-create-issue.ps1"
```

### 6.3 渐进式放开其他目录

在 `.gitignore` 中追加：
```gitignore
# 示例：放开 apps/api-demo/
!/apps/
/apps/*
!/apps/api-demo/
```

---

*文档生成时间: 2026-06-17*  
*记录人: Agent Session*  
*下次触发条件: 新增 task 需要 GitHub 发布、或优化 devroot 探测逻辑时*
