---
title: deploy-git-isolated — 隔离 Git 部署任务
description: 在 devroot 内部署隔离版 Git CLI，实现配置隔离与多身份管理。Agent 速查入口，场景化决策路径。
date: 2026-06-16
---

# deploy-git-isolated — 隔离 Git 部署任务

> **版本**: v0.5.0 | **状态**: 核心功能 ready，可执行部署与 GitHub 交互  
> **真源索引**: [ENTRY.json](ENTRY.json) | **目标闭环**: [GOAL.md](GOAL.md) | **命令速查**: [scripts/SOP-CHEATSHEET.md](scripts/SOP-CHEATSHEET.md) | **工具索引**: [TASK-TOOLS-INDEX.md](TASK-TOOLS-INDEX.md)  
> **设计文档**: [DESIGN.md](DESIGN.md) | **架构说明**: [docs/PLUGIN-ARCHITECTURE.md](docs/PLUGIN-ARCHITECTURE.md) | **规范基线**: [task-canonical-baseline.md](task-canonical-baseline.md)
>
> ⚠️ **Agent 注意**：本 task 有已定义的规范基线 `task-canonical-baseline.md`。如果你在对话中遗忘了本文件的存在，说明上下文已碎片化——请**立即停止推理，重新读取 `task-canonical-baseline.md`**。

---

## Agent 快速决策（三句话定位）

| 用户意图 | 你的判断 | 立即执行 |
|---------|---------|---------|
| "部署隔离 Git" / "装 git" / "初始化 git" | **场景 A: 首次部署** | 按 Step 1→8 顺序执行 |
| "连 GitHub" / "push 到 github" / "建仓库" | **场景 B: GitHub 连接** | 确认 `.env` 有 PAT → 执行 Step 1→8 |
| "检查哪些文件会传上去" / "安全确认" | **场景 C: 安全检查** | 执行 `github-safety-check.ps1` |
| "git status" / "看看改了什么" / "哪些 staged" | **场景 D: 日常查询** | 执行 `git-isolated.ps1 status` |
| "commit" / "push" / "add" | **场景 E: 日常操作** | 执行 `git-isolated.ps1 <子命令>` |
| "同步 Issue" / "更新 Issue" / "追加评论" | **场景 F: Issue 同步** | 执行 `github-sync-issue.ps1` |

> **铁律**：不确定时先执行 `github-safety-check.ps1`，确认无敏感文件后再 push。

---

## 场景 A: 首次部署隔离 Git（Step 1→8）

**前提条件**：
- `.env` 中已配置 `GIT_USER_NAME`、`GIT_USER_EMAIL`
- `.env` 中已配置 `GITHUB_REPO_URL`（如要连 GitHub）
- `.env` 中已配置 `GITHUB_PAT`（如要 push）

**执行链**（Agent 直接复制执行）：

```powershell
# Step 1: init + 身份
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# Step 2: .gitignore
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-02-gitignore.ps1"

# Step 3: README
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-03-readme.ps1"

# Step 4: add
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-04-stage.ps1"

# Step 5: commit
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-05-commit.ps1"

# Step 6: remote
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-06-remote.ps1"

# Step 7: push（需要 PAT）
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-07-push.ps1"

# Step 8: upstream
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-08-upstream.ps1"
```

**人类终端等价格式**：把 `powershell -ExecutionPolicy Bypass -File` 换成 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\`，路径改用相对路径。

> 详细参数与前置条件见 [SOP-CHEATSHEET.md](scripts/SOP-CHEATSHEET.md)

---

## 场景 B: 连接新 GitHub 仓库

**已有隔离 Git，要连新的 GitHub 仓库**：

1. 更新 `.env` 中的 `GITHUB_REPO_URL` 和 `GITHUB_PAT`
2. 执行 Step 6（remote）→ Step 7（push）→ Step 8（upstream）

**首次 push 的新仓库（GitHub 上已创建空仓库）**：

直接执行 **场景 A 的完整 Step 1→8**。

---

## 场景 C: Push 前安全检查（强制）

```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-safety-check.ps1"
```

**输出示例**：
```
[1] 已跟踪文件（会随 push 上传）：
  - .gitignore
  - README.md
[2] 已 staged 文件（即将 commit）：
  - xxx
[3] 未跟踪文件：...
[4] 敏感文件屏蔽验证：
  [OK] .env -> 被 .gitignore 屏蔽
```

> **任何 push 操作前必须先执行本脚本**，确认 `.env`、密钥等被屏蔽。

---

## 场景 D/E: 日常 Git 操作

```powershell
# 通用包装器，透传所有 git 子命令
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" status
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" log --oneline
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" diff
```

---

## 文件导航（一句话职责）

| 文件 | 职责 | 何时读 |
|------|------|--------|
| `README.md` | **本文件**：Agent 快速决策、场景路径、状态总览 | **每次进入本 task 先读** |
| `GOAL.md` | **目标闭环**：Goal → Solution → SOP → Apply → Review → Ralph Loop 完整链条 | 首次接触 / 跨 session 接续时 |
| `ENTRY.json` | 机器真源：脚本清单、版本历史、场景映射 | Agent 工具调用前读取 |
| `TASK-TOOLS-INDEX.md` | **工具速查表**：本 task 全部可用工具索引（本地+外部引用+边界矩阵） | 想知道「有什么工具、该调哪个、边界在哪」时 |
| `scripts/SOP-CHEATSHEET.md` | **命令速查**：Agent/终端双格式执行命令 | 需要具体命令复制粘贴时 |
| `DESIGN.md` | 设计文档：决策记录、SOP、踩坑 | 需要理解设计背景时 |
| `task-canonical-baseline.md` | **规范基线**：本 task 的认知契约、命名约定、修订联动规则 | 需要理解「文件该怎么组织、怎么命名、怎么联动」时 |
| `docs/PLUGIN-ARCHITECTURE.md` | 插件架构说明：为什么三层、怎么扩展 | 新增插件或维护架构时 |
| `docs/github-publish-playbook.md` | **发布手册**：task 发布到 GitHub 的完整实录（三篇文章原理、实施步骤、踩坑） | 需要复现 GitHub 发布流程或理解设计思路时 |
| `scripts/github-lib.ps1` | 共享库入口：拓扑排序加载所有插件 | 被 step 脚本点源导入 |
| `scripts/lib-sort-rules.json` | 插件排序真源：依赖图定义 | 新增/修改插件时 |
| `scripts/lib-plugins/*.ps1` | 共享函数插件：编码/常量/配置/检查 | 被 github-lib.ps1 自动加载 |
| `scripts/github-step-0N-*.ps1` | Step 脚本：部署流程的 8 个步骤 | 按场景执行 |
| `scripts/github-safety-check.ps1` | 安全检查：push 前必执行 | push 前 |
| `scripts/github-sync-issue.ps1` | **Issue 同步入口**：create / update / comment / list-comments / get-issue | commit 后同步变更历史 |
| `scripts/github-sync-issue-config.json` | Issue 同步配置真源：模板、labels、endpoint 映射 | 调整 Issue 格式时 |
| `scripts/lib-plugins/github-api.ps1` | 插件：GitHub REST API 封装（UTF-8 encoding） | 被 sync-issue / 其他脚本点源加载 |
| `scripts/git-isolated.ps1` | 通用包装器：日常 git 子命令 | 日常操作 |

---

## 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| MinGit 2.54.0 部署 | ✅ | `venv/git/cmd/git.exe` 可用 |
| 隔离配置 `venv/data-git/` | ✅ | `.gitconfig` 已写入 |
| Step 脚本 1-8 | ✅ | 全部 ready，可执行完整 GitHub 初始化流程 |
| 安全检查脚本 | ✅ | `github-safety-check.ps1` 可用 |
| 通用包装器 | ✅ | `git-isolated.ps1` 可用 |
| 插件架构 | ✅ | 拓扑排序自动加载，5 个插件就绪 |
| `verified-runtime-index.json` | ✅ | Git 工具链已登记 |
| 命令速查 | ✅ | SOP-CHEATSHEET.md v1.2（纯命令） |
| 工具索引 | ✅ | TASK-TOOLS-INDEX.md v1.0（本地+外部引用+边界） |
| Issue 同步体系 | ✅ | github-sync-issue.ps1 + github-api.ps1 + config.json |

---

*任务版本: v0.6.0*  
*演进历史: 见 ENTRY.json `meta.version_history`*
