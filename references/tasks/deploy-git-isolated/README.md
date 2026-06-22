---
title: deploy-git-isolated — 隔离 Git 部署任务
description: 在 devroot 内部署隔离版 Git CLI，实现配置隔离与多身份管理。Agent 速查入口，场景化决策路径。
date: 2026-06-19
meta: {}
---

# deploy-git-isolated — 隔离 Git 部署任务

> **版本**: v0.5.0 | **状态**: 核心功能 ready，可执行部署与 GitHub 交互  
> **真源索引**: [ENTRY.json](ENTRY.json) | **目标闭环**: [GOAL.md](GOAL.md) | **标准流程**: [SOP.md](SOP.md) | **执行速查**: [scripts/EXEC-CHEATSHEET.md](scripts/EXEC-CHEATSHEET.md) | **工具索引**: [TASK-TOOLS-INDEX.md](TASK-TOOLS-INDEX.md)  
> **设计文档**: [DESIGN.md](DESIGN.md) | **架构说明**: [docs/PLUGIN-ARCHITECTURE.md](docs/PLUGIN-ARCHITECTURE.md) | **规范基线**: [task-canonical-baseline.md](task-canonical-baseline.md)
>
> ⚠️ **Agent 注意**：本 task 有已定义的规范基线 `task-canonical-baseline.md`。如果你在对话中遗忘了本文件的存在，说明上下文已碎片化——请**立即停止推理，重新读取 `task-canonical-baseline.md`**。


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

> 详细参数与前置条件见 [SOP.md](SOP.md) | 命令速查见 [EXEC-CHEATSHEET.md](scripts/EXEC-CHEATSHEET.md)


## 场景 B: 连接新 GitHub 仓库

**已有隔离 Git，要连新的 GitHub 仓库**：

1. 更新 `.env` 中的 `GITHUB_REPO_URL` 和 `GITHUB_PAT`
2. 执行 Step 6（remote）→ Step 7（push）→ Step 8（upstream）

**首次 push 的新仓库（GitHub 上已创建空仓库）**：

直接执行 **场景 A 的完整 Step 1→8**。


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


## 场景 D/E: 日常 Git 操作

```powershell
# 通用包装器，透传所有 git 子命令
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" status
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" log --oneline
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" diff
```


## 文件导航（一句话职责）

| 文件 | 职责 | 何时读 |
|------|------|--------|
| `README.md` | **本文件**：Agent 快速决策、场景路径、状态总览 | **每次进入本 task 先读** |
| `GOAL.md` | **目标闭环**：Goal → Solution → SOP → Apply → Review → Ralph Loop 完整链条 | 首次接触 / 跨 session 接续时 |
| `ENTRY.json` | 机器真源：脚本清单、版本历史、场景映射 | Agent 工具调用前读取 |
| `TASK-TOOLS-INDEX.md` | **工具速查表**：本 task 全部可用工具索引（本地+外部引用+边界矩阵） | 想知道「有什么工具、该调哪个、边界在哪」时 |
| `SOP.md` | **标准流程**：Step 节点契约、验收条件、回滚路径 | 需要理解「流程是什么、怎么验收」时 |
| `scripts/EXEC-CHEATSHEET.md` | **执行速查**：命令、配置、参数 | 需要具体命令复制粘贴时 |
| `DESIGN.md` | 设计文档：决策记录、踩坑 | 需要理解设计背景时 |
| `task-canonical-baseline.md` | **规范基线**：本 task 的认知契约、命名约定、修订联动规则 | 需要理解「文件该怎么组织、怎么命名、怎么联动」时 |
| `docs/PLUGIN-ARCHITECTURE.md` | 插件架构说明：为什么三层、怎么扩展 | 新增插件或维护架构时 |
| `docs/patterns/profile-filter-pattern.md` | **设计模式**：Profile 筛选（稳定框架+黑白名单+依赖补齐） | 需要复用插件筛选机制时 |
| `docs/patterns/manifest-plugin-pattern.md` | **设计模式**：Manifest + Plugins 扩展（机器真源+人类速查+可插拔代码） | 需要复用工具索引体系时 |
| `docs/harness/delivery-checklist.md` | **交付流程**：最小范围测试 → Lint → 验证 → 归档 | 交付前自检 |
| `docs/playbooks/github-publish-playbook.md` | **发布手册**：task 发布到 GitHub 的完整实录 | 需要复现 GitHub 发布流程时 |
| `scripts/github-lib.ps1` | 共享库入口：拓扑排序加载所有插件 | 被 step 脚本点源导入 |
| `scripts/lib-sort-rules.json` | 插件排序真源：依赖图定义 | 新增/修改插件时 |
| `scripts/lib-plugins/*.ps1` | 共享函数插件：编码/常量/配置/检查 | 被 github-lib.ps1 自动加载 |
| `scripts/ps-steps/github-step-0N-*.ps1` | Step 脚本：部署流程的 8 个步骤 | 按场景执行 |
| `scripts/ps-tools/github-safety-check.ps1` | 安全检查：push 前必执行 | push 前 |
| `scripts/ps-tools/github-sync-issue.ps1` | **Issue 同步入口**：create / update / comment / list-comments / get-issue | commit 后同步变更历史 |
| `scripts/ps-tools/github-sync-issue-config.json` | Issue 同步配置真源：模板、labels、endpoint 映射 | 调整 Issue 格式时 |
| `scripts/lib-plugins/github-api.ps1` | 插件：GitHub REST API 封装（UTF-8 encoding） | 被 sync-issue / 其他脚本点源加载 |
| `scripts/ps-tools/git-isolated.ps1` | 通用包装器：日常 git 子命令 | 日常操作 |
| `scripts/py-tools/run-lint.py` | **Workflow：全量 lint**。通过 py_lib 聚合全部 lint 插件 | 脚本交付前必执行 |
| `scripts/py-tools/workflow-lint-amend-lint.py` | **Workflow：编码修复闭环**。通过 py_lib 调用 lint_encoding | 编码问题发现后修复 |
| `scripts/py-tools/update-version.py` | **Workflow：版本记录更新**。自动发现 → 实测 → 对比 → 更新 .md + history | 记一版 version |
| `scripts/py-tools/archive_project.py` | **Workflow：项目归档**。scan → compress → verify 三阶段闭环 | 项目归档（cs_py / venv） |
| `scripts/py-tools/archive_cs_py.py` | 快捷入口：归档 cs_py 分组 | 调用 archive_project.py --group cs_py |
| `scripts/py-tools/archive_venv.py` | 快捷入口：归档 venv 分组 | 调用 archive_project.py --group venv |
| `scripts/py_lib.py` | **统一入口**。所有 workflow 必须通过它获取插件能力 | 禁止越级直接 import plugin |
| `scripts/py-plugins/lint_json.py` | **底座：JSON 语法验证** | 被 py_lib 加载，不直接调用 |
| `scripts/py-plugins/lint_ps1.py` | **底座：PowerShell 语法验证** | 被 py_lib 加载，不直接调用 |
| `scripts/py-plugins/lint_python.py` | **底座：Python 语法验证** | 被 py_lib 加载，不直接调用 |
| `scripts/py-plugins/lint_encoding.py` | **底座：编码/BOM/行尾符检测+修复** | 被 py_lib 加载，不直接调用 |
| `scripts/py-plugins/archive_config.py` | **底座：归档配置**。分组定义、7z 路径、输出目录 | 被 py_lib 加载，不直接调用 |
| `scripts/py-plugins/archive_scanner.py` | **底座：归档扫描**。磁盘扫描、黑白名单、空目录占位 | 被 py_lib 加载，不直接调用 |
| `scripts/py-plugins/archive_compressor.py` | **底座：归档压缩**。7z 压缩、心跳进度、统计解析 | 被 py_lib 加载，不直接调用 |


## Python 插件体系架构（三层 + 配置契约）

> **核心认知**：本架构是**三层主体 + 配置契约**。Config（*.json）不是独立"层"，而是 Entry 和 Plugins 的输入契约。
> - **Workflow** 编排步骤，检查配置有效性，按速查表设计入参，调用 Entry
> - **Entry** 读取 py-sort-rules.json（插件注册表），拓扑排序加载 Plugins
> - **Plugins** 消费业务 Config（如 archive-groups.json）执行能力
> - **Config 来源**：开发时静态编写 / 异步事件登记（新增 plugin）/ Workflow 前置检查

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 3: Workflow（py-tools/ + EXEC-CHEATSHEET）            │
│  run-lint.py                 → 全量 lint 聚合               │
│  workflow-lint-amend-lint.py → 编码修复闭环                 │
│  archive_project.py          → scan → compress → verify     │
│  EXEC-CHEATSHEET.md          → 命令速查真源               │
│  （编排：检查配置 → 设计入参 → 调用 Entry；禁止 import plugin）│
└──────────────────────────────────────────────────────────────┘
                    ↓ 调用 py_lib.load_plugins(profile=...)
┌──────────────────────────────────────────────────────────────┐
│  Layer 2: 统一入口（scripts/py_lib.py）                      │
│  读取 py-sort-rules.json → 拓扑排序 → 依赖补齐 → 注入 registry│
│  （所有调用的唯一网关；禁止被绕过）                          │
└──────────────────────────────────────────────────────────────┘
                    ↓ 动态加载 + 传递 Config
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: 底座插件（py-plugins/）                            │
│  lint_json.py · lint_ps1.py · lint_python.py · lint_encoding │
│  md_lint.py · link_checker · browser_session · github_api    │
│  archive_config · archive_scanner · archive_compressor       │
│  （单一职责，暴露标准化接口；消费 archive-groups.json 等）   │
└──────────────────────────────────────────────────────────────┘

     ╔══════════════════════════════════════════════════════════╗
     ║  Config 契约（*.json）— Entry 与 Plugins 的输入           ║
     ║  py-sort-rules.json  → 插件注册、依赖图、profile         ║
     ║  archive-groups.json → 分组策略、黑白名单                ║
     ║  task-config.json    → 任务参数、路径、场景映射          ║
     ║  （配置与代码分离；开发编写 / 异步登记 / WF 检查）        ║
     ╚══════════════════════════════════════════════════════════╝
```

> **铁律**：Layer 3 Workflow 禁止直接 `import` Layer 1 Plugin。必须通过 `py_lib.load_plugins()` 获取 registry，再访问插件能力。


## 当前状态

| 组件 | 状态 | 说明 |
|------|------|------|
| MinGit 2.54.0 部署 | ✅ | `venv/git/cmd/git.exe` 可用 |
| 隔离配置 `venv/data-git/` | ✅ | `.gitconfig` 已写入 |
| Step 脚本 1-8 | ✅ | 全部 ready，可执行完整 GitHub 初始化流程 |
| 安全检查脚本 | ✅ | `github-safety-check.ps1` 可用 |
| 通用包装器 | ✅ | `git-isolated.ps1` 可用 |
| 插件架构 | ✅ | 拓扑排序自动加载，6 个插件就绪 |
| **Lint 插件体系** | ✅ | 四层架构：workflow → py_lib → config → plugins，禁止越级 |
| **Archive 插件体系** | ✅ | archive_project.py 已迁入四层模型（原直接 import 已纠正） |
| `verified-runtime-index.json` | ✅ | Git 工具链已登记 |
| 标准流程 | ✅ | SOP.md v1.0（Step 契约 + Ralph Loop） |
| 执行速查 | ✅ | EXEC-CHEATSHEET.md v1.0（命令+配置+参数） |
| 工具索引 | ✅ | TASK-TOOLS-INDEX.md v1.0（本地+外部引用+边界） |
| Issue 同步体系 | ✅ | github-sync-issue.ps1 + github-api.ps1 + config.json |
| **版本记录更新** | ✅ | update-version.py（自动发现 → 实测 → 更新 .md + history） |
| **Profile 筛选机制** | ✅ | github-lib.ps1 支持 Profile/Include/Exclude 三层筛选，依赖自动补齐，向后兼容 |


*任务版本: v0.7.0*  
*演进历史: 见 ENTRY.json `meta.version_history`*
