---
title: deploy-git-isolated — 隔离 Git 部署任务
description: 在 devroot 内部署隔离版 Git CLI，实现配置隔离与多身份管理。Agent 速查入口，场景化决策路径。
date: 2026-06-19
meta: {}
---

# deploy-git-isolated — 隔离 Git 部署任务

> **版本**: v0.5.0 | **状态**: 核心功能 ready，可执行部署与 GitHub 交互  
> **真源索引**: [ENTRY.json](ENTRY.json) | **目标闭环**: [GOAL.md](GOAL.md) | **标准流程**: [SOP.md](SOP.md) | **执行速查**: [scripts/EXEC-CHEATSHEET.md](scripts/EXEC-CHEATSHEET.md) | **工具索引**: [TASK-TOOLS-INDEX.md](TASK-TOOLS-INDEX.md)  
> **设计文档**: [DESIGN.md](DESIGN.md) | **架构说明**: [docs/PLUGIN-ARCHITECTURE.md](docs/PLUGIN-ARCHITECTURE.md) | **规范基线**: [baseline/baseline-index.md](baseline/baseline-index.md)
>
> ⚠️ **Agent 注意**：本 task 有已定义的规范基线 `baseline/baseline-index.md`。如果你在对话中遗忘了本文件的存在，说明上下文已碎片化——请**立即停止推理，重新读取 `baseline/baseline-index.md`**。


## 版本记录

| 版本 | 日期 | slug | 关键变更 |
|------|------|------|---------|
| **v0.22.0** | 2026-07-10 | `git-reset-guard-poly-step45` | 新增 git_reset 插件 + atomic-git-reset-staged 原子 CLI；poly.py Step 4.5 消除越级调用；baseline 新增裸 git reset 禁令 |
| v0.21.1 | 2026-07-10 | `poly-except-bugfix` | 修复 workflow-git-deploy-full-poly.py 重复 except 块 |
| v0.21.0 | 2026-07-07 | `preflight-atomic` | Preflight 抽离为 atomic 脚本；新增 Step 4.5 staged 扫描 |
| v0.20.0 | 2026-06-26 | `runtime-atomic` | 运行时域集成：verify-runtime + download-runtime 拆分为 task 原子脚本体系 |
| v0.19.0 | 2026-06-26 | `update-version-v2` | update-version.py 架构归一化，走 py_lib 插件体系 |
| v0.18.0 | 2026-06-24 | `lint-upgrade` | lint 体系全面升级：link_checker、py_lib v1.2.0、run-lint v1.3.0 |
| v0.17.0 | 2026-06-24 | `workflow-deploy` | 新增 workflow-deploy-full.py 全链条部署 Workflow |

> 完整历史见 [ENTRY.json](ENTRY.json) `meta.version_history`


## Task 结构概览

> **免责声明**：本目录树仅作"分类示意"，不保证各子目录当前是否仍然存在或已迁移。凡涉及具体路径、版本号的引用，**禁止**以本文档作为唯一依据，优先查 [ENTRY.json](ENTRY.json) 机器真源。

```
references/tasks/deploy-git-isolated/
├── README.md                           # 本文件：场景化决策入口 + 版本记录 + 结构概览
├── GOAL.md                             # 目标闭环：Goal → Solution → SOP → Apply → Review
├── SOP.md                              # 标准流程：Step 契约 + Ralph Loop + 验收条件
├── DESIGN.md                           # 设计文档：决策记录、踩坑、架构演进
├── ENTRY.json                          # 机器真源：脚本清单、版本历史、状态、场景映射
├── TASK-TOOLS-INDEX.md                 # 工具速查表：本地+外部引用+边界矩阵
├── task-config.json                    # 任务配置：路径、工具链、下载源
├── task-scenario-triggers.json         # 触发条件真源：8 场景 trigger 映射
├── task-canonical-baseline.md          # 规范基线导航
├── baseline/                           # 规范基线（9 个专题文件）
│   ├── baseline-index.md               # 基线导航
│   ├── baseline-principles.md          # 顶层原则（含裸 git reset 禁令 §0.8.5）
│   ├── baseline-workflow-deploy.md     # 部署流程契约（Step 4.5 架构约束）
│   └── ...
├── changelog/                          # 变更记录（按日期 slug）
├── gotchas/                            # 踩坑记录
├── docs/                               # 架构文档与设计模式
│   ├── PLUGIN-ARCHITECTURE.md          # 三层架构说明
│   ├── patterns/                       # 设计模式（Profile 筛选、Manifest+Plugin）
│   ├── harness/                        # 交付流程与检查清单
│   └── playbooks/                      # 发布手册
├── schema/                             # 数据契约（JSON Schema + Pydantic Model）
│   ├── json/                           # lint-rules-manifest.json、plugin-result-schema.json
│   └── docs/                           # Schema 人类可读文档
├── scripts/                            # 全部可执行脚本与资产
│   ├── github-lib.ps1                  # PS 共享库入口（拓扑排序 + Profile 筛选）
│   ├── lib-sort-rules.json             # PS 插件依赖图
│   ├── lib-plugins/*.ps1               # PS 共享函数插件
│   ├── ps-steps/                       # PowerShell Step 脚本（Step 1-8）
│   ├── ps-tools/                       # PS 工具脚本（安全检查、Issue 同步、通用包装器）
│   ├── py_lib.py                       # Python 统一入口（v1.2.0）
│   ├── py-sort-rules.json              # Python 插件注册表 + Profile 定义
│   ├── py-plugins/                     # Python 底座插件（Layer 1）
│   │   ├── git_reset.py                # Git Reset 封装（v1.0.0，操作前审计+验证）
│   │   ├── git_staged_scan.py          # Staged 内容扫描
│   │   ├── git_security.py             # Git 安全扫描
│   │   ├── git_preflight.py            # Git Preflight 编排
│   │   ├── lint_*.py                   # Lint 插件（json/ps1/python/encoding/md/link）
│   │   └── ...                         # 其他核心/归档/LLM 插件
│   ├── py-tools/                       # Python Workflow + 原子 CLI（Layer 3）
│   │   ├── workflow-deploy-full.py     # 单仓库全链条部署 Workflow
│   │   ├── workflow-git-deploy-full-poly.py  # Polyrepo 全链条部署 Workflow
│   │   ├── run-lint.py                 # 全量 lint 唯一入口
│   │   ├── atomic-git-preflight.py     # 原子：Git 前置验证
│   │   ├── atomic-deploy-preflight.py  # 原子：部署特有验证
│   │   ├── atomic-check-staged-after-add.py  # 原子：Staged 安全扫描
│   │   ├── atomic-git-reset-staged.py  # 原子：Git Staged 回滚（v1.0.0）
│   │   ├── workflow-gh-pr.py           # GitHub PR 自闭环 Workflow（gh CLI 编排：create→merge→cleanup→pull）
│   │   ├── gh-pr-create.py             # 子脚本：创建 PR（含 AI title 生成）
│   │   ├── gh-pr-merge.py              # 子脚本：合并 PR（squash/merge/rebase + admin 绕过保护）
│   │   ├── gh-branch-protect.py        # 子脚本：分支保护规则管理
│   │   ├── workflow-gh-preflight-demo.py  # gh CLI 前置验证演示（gh.exe + PAT + 认证状态）
│   │   ├── verify-runtime/             # 真源检测 Workflow + 公共原子
│   │   ├── download-runtime/           # 运行时下载 Workflow + 原子步骤
│   │   └── ...                         # 其他 Workflow（归档、版本更新、文章下载）
│   ├── py-steps/                       # Python Step 脚本（被 workflow 调用）
│   ├── py-examples/                    # 用法示例
│   ├── js_lib.js                       # JS 统一入口
│   ├── js-sort-rules.json              # JS 资产注册表
│   ├── js-plugins/                     # JS 可复用模块
│   ├── js-tools/                       # JS 工具脚本（readability、turndown、extract-article）
│   └── EXEC-CHEATSHEET.md              # 执行速查：命令+配置+参数
├── skills/                             # Skill 规范与质量 Harness
│   └── docstring-quality-harness/      # 工具文档自说明质量测试（subagent 探针 + baseline 积累）
│       ├── SKILL.md
│       ├── schema/
│       ├── baseline/
│       └── examples/
└── archive/                            # 旧版归档
```


## Agent 快速决策（三句话定位）

| 用户意图 | 你的判断 | 立即执行 |
|---------|---------|---------|
| "部署隔离 Git" / "装 git" / "初始化 git" | **场景 A: 首次部署** | Step 1→3 用 PS 脚本 → Step 4→9 **必须**用 workflow |
| "连 GitHub" / "push 到 github" / "建仓库" | **场景 B: GitHub 连接** | 确认 `.env` 有 PAT → 执行 Step 1→8 |
| "检查哪些文件会传上去" / "安全确认" | **场景 C: 安全检查** | 执行 `github-safety-check.ps1` |
| "git status" / "看看改了什么" / "哪些 staged" | **场景 D: 日常查询** | 执行 `git-isolated.ps1 status` |
| "发布github" / "自动部署" / "auto deploy" / "完整流水线" | **场景 G: 全自动发布** | 执行 `workflow-deploy-full.py --auto` |
| "commit并push到github" / "提交并发布" | **场景 E: 提交+发布** | 执行 `workflow-deploy-full.py --message "feat: xxx"` |
| "同步 Issue" / "更新 Issue" / "追加评论" | **场景 F: Issue 同步** | 执行 `github-sync-issue.ps1` |
| "回退 staged" / "取消暂存" / "unstage" / "git reset" | **场景 H: Staged 回滚** | 执行 `atomic-git-reset-staged.py`（**禁止**现写 `git reset` 命令） |
| "部署 polyrepo" / "多仓库发布" / "跨仓库 deploy" | **场景 I: Polyrepo 部署** | 执行 `workflow-git-deploy-full-poly.py`（**--target 强制必填**，即使与 --devroot 相同） |
| "建 PR" / "提 PR" / "合并 PR" / "PR 自闭环" / "gh pr" | **场景 J: GitHub PR 自闭环（gh）** | 已 push feature 分支后执行 `workflow-gh-pr.py --auto --admin` |

> **铁律**：不确定时先执行 `github-safety-check.ps1`，确认无敏感文件后再 push。
> **铁律**：凡涉及 Step 4-9（add→commit→push→issue sync）的操作，**必须**使用 `workflow-deploy-full.py`，禁止手动逐条调用 ps-steps。
> **铁律**：凡涉及 staged 回滚的操作，**必须**使用 `atomic-git-reset-staged.py`，禁止现写 `git reset` 命令（见 `baseline-principles.md` §0.8.5）。


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

# Step 4-9: 全链条部署（add → commit → push → issue sync）
# 【铁律】必须使用 workflow-deploy-full.py，禁止手动逐条调用 ps-steps
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --auto
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


## 场景 I: Polyrepo 部署

**用途**：在 polyrepo（多仓库）场景下执行全链条部署，或明确指定 `--target` 的单仓库部署。

**执行链**：
```powershell
# 单仓库完整部署（target 与 devroot 相同，仍须显式传入）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}"

# Polyrepo 完整部署（target 指向另一个仓库）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}\apps\repos\jywl-team\jywl-lab"

# 指定 commit message
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}" --message "feat: xxx"

# 仅执行 preflight + manifest 审计（Step 0）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "${devroot}" --target "${devroot}" --step 0
```

> **铁律**：`--target` 为强制参数，不可省略。`--devroot` 仅用于验证与 CWD 一致。
> **与 workflow-deploy-full.py 的区别**：`workflow-deploy-full.py` 面向单仓库，无 `--target` 参数；`workflow-git-deploy-full-poly.py` 面向 polyrepo，支持跨仓库部署，--target 强制必填。


## 场景 J: GitHub PR 自闭环（gh CLI）

**前提**：已完成 `workflow-deploy-full.py`（或 poly 版）的 push，当前在 feature 分支且 `origin/<branch>` 已存在。

**执行链**（一键 PR 闭环，全程本机 + headless 认证）：

```powershell
# 全自动（推荐）：AI 生成 title + body → PR create → PR merge（admin 绕过保护）→ 删除分支 → 同步 master
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-pr.py" --auto --admin
```

**认证**：gh CLI 隔离部署于 `venv/gh/bin/gh.exe`，配置隔离于 `venv/data-gh`。自动化无需 `gh auth login`，直接注入：
```powershell
$env:GH_TOKEN = $env:GITHUB_PAT
$env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"
```

**补充说明**：`workflow-deploy-full*.py` 主流程覆盖 `init → commit → push → issue sync`，但**不封装 `repo create`（新建仓库）**。新建 GitHub 仓库本机化可用已部署的 gh CLI 补齐：
```powershell
$env:GH_TOKEN = $env:GITHUB_PAT
$env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"
& "${devroot}\venv\gh\bin\gh.exe" repo create my-new-project --private --source . --push
```

> **认知澄清**：`gh pr merge` 本质是 GitHub REST API 的命令行封装，代码合并发生在**远端服务器**，本地 `master` 需 `pull` 才同步（workflow 默认已做）。PR 自动化属可行性验证阶段，是否纳入主部署流水线取决于用户仓库分支保护策略。


## 文件导航（一句话职责）

| 文件 | 职责 | 何时读 |
|------|------|--------|
| `README.md` | **本文件**：Agent 快速决策、场景路径、状态总览 | **每次进入本 task 先读** |
| `GOAL.md` | **目标闭环**：Goal → Solution → SOP → Apply → Review → Ralph Loop 完整链条 | 首次接触 / 跨 session 接续时 |
| `ENTRY.json` | 机器真源：脚本清单、版本历史、场景映射 | Agent 工具调用前读取 |
| `TASK-TOOLS-INDEX.md` | **工具速查表**：本 task 全部可用工具索引（本地+外部引用+边界矩阵） | 想知道「有什么工具、该调哪个、边界在哪」时 |
| `SOP.md` | **标准流程**：Step 节点契约、验收条件、回滚路径 | 需要理解「流程是什么、怎么验收」时 |
| `scripts/EXEC-CHEATSHEET.md` | **执行速查**：命令、配置、参数 | 需要具体命令复制粘贴时 |
| `scripts/README.md` | **scripts 目录索引**：串接 PS / Python / JS 三层工具链入口 | 需要概览 scripts/ 全部资产时 |
| `scripts/py-tools/README.md` | **py-tools 目录索引**：全部 Python Workflow 脚本与 py-plugins 插件清单 | 需要查看 Python 侧可用工具时 |
| `DESIGN.md` | 设计文档：决策记录、踩坑 | 需要理解设计背景时 |
| `baseline/baseline-index.md` | **规范基线导航**：本 task 的认知契约、命名约定、修订联动规则（已拆分为 9 个专题文件） | 需要理解「文件该怎么组织、怎么命名、怎么联动」时 |
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
| `scripts/py-tools/workflow-deploy-full.py` | **Workflow：全链条部署**。编排 Step 4-9，调用 py-steps 分步执行 | 完整 GitHub 部署流水线 |
| `scripts/py-tools/workflow-gh-pr.py` | **Workflow：GitHub PR 自闭环**。编排 gh-pr-create → gh-pr-merge → 本地同步，基于已 push 的 feature 分支 | PR 自动化闭环（需先 deploy push） |
| `scripts/py-tools/gh-pr-create.py` | **子脚本：创建 PR**。支持 --auto AI 生成 title + --body/--base/--draft | PR 创建（可独立调用） |
| `scripts/py-tools/gh-pr-merge.py` | **子脚本：合并 PR**。squash/merge/rebase + --admin 绕过保护 + --delete-branch | PR 合并（可独立调用） |
| `scripts/py-tools/gh-branch-protect.py` | **子脚本：分支保护**。管理仓库分支保护规则 | 分支保护配置 |
| `scripts/py-tools/workflow-gh-preflight-demo.py` | **演示：gh CLI 前置验证**。验证 gh.exe + PAT + 认证状态 | gh 可用性自检 |
| `scripts/py-plugins/gh_preflight.py` | **插件：gh CLI 前置检测**。验证 gh.exe / PAT / 认证状态，返回 GhContext（含 run_gh 封装） | 被 workflow-gh-pr / gh-pr-* 调用 |
| `scripts/py-steps/step-04-*.py` ~ `step-09-*.py` | Python 版 Step 脚本：add / commit / remote / push / upstream / issue sync | 被 workflow-deploy-full.py 调用 |
| `scripts/py-tools/run-lint.py` | **Workflow：全量 lint**。--fix 三阶段闭环、--audit 覆盖度审计（对照 lint-rules-manifest.json） | 脚本交付前必执行 |
| `scripts/py-tools/workflow-lint-amend-lint.py` | **Workflow：编码修复闭环**。通过 py_lib 调用 lint_encoding | 编码问题发现后修复 |
| `scripts/py-tools/update-version.py` | **Workflow：版本记录更新** v2.0.0。走 py_lib → registry 调用 runtime_version。旧版归档到 `archive/update-version-legacy-*.py` | 记一版 version |
| `scripts/py-tools/verify-runtime/wf-verify-runtime.py` | **Workflow：真源检测**。编排 detect → query → compare → report，替代 runtime/verify-runtime.py | 执行真源检测 |
| `scripts/py-tools/download-runtime/wf-download-runtime.py` | **Workflow：运行时下载**。编排 detect → query → compare → route → download → extract → backup → replace → cleanup，替代 runtime/download-runtime-tool.py | 下载/更新运行时 |
| `scripts/py-tools/runtime-common/atomic-detect-local.py` | **公共原子：本地检测**。exe 存在性 + candidate_paths 兜底 + 版本提取 | 被 wf-verify-runtime / wf-download-runtime 调用 |
| `scripts/py-tools/runtime-common/atomic-query-upstream.py` | **公共原子：上游查询**。python/node/opencode/chromium/llama 上游版本实时查询 | 被 wf-verify-runtime / wf-download-runtime 调用 |
| `scripts/py-tools/runtime-common/atomic-compare-version.py` | **公共原子：版本对比**。up_to_date/outdated/unknown 判定 | 被 wf-verify-runtime / wf-download-runtime 调用 |
| `scripts/py-tools/runtime-common/atomic-generate-report.py` | **公共原子：报告生成**。stdout 表格 + JSON 落盘 | 被 wf-verify-runtime 调用 |
| `scripts/py-tools/download-runtime/atomic-01-route-probe.py` | **原子：路由探测**。HEAD 探测直连+代理，返回最优路由 | 被 wf-download-runtime 调用 |
| `scripts/py-tools/download-runtime/atomic-02-download-file.py` | **原子：文件下载**。流式下载 + 进度条 + 代理支持 | 被 wf-download-runtime 调用 |
| `scripts/py-tools/download-runtime/atomic-03-extract-verify.py` | **原子：解压验证**。ZIP 解压 + 定位 exe + 版本验证 | 被 wf-download-runtime 调用 |
| `scripts/py-tools/download-runtime/atomic-04-backup-replace.py` | **原子：备份替换**。进程检测 + 备份旧版 + 替换新版 | 被 wf-download-runtime 调用 |
| `scripts/py-tools/download-runtime/atomic-05-cleanup-temp.py` | **原子：清理临时**。清理解压目录和 ZIP 文件 | 被 wf-download-runtime 调用 |
| `scripts/py-tools/archive_project.py` | **Workflow：项目归档**。scan → compress → verify 三阶段闭环 | 项目归档（cs_py / venv） |
| `scripts/py-tools/archive_cs_py.py` | 快捷入口：归档 cs_py 分组 | 调用 archive_project.py --group cs_py |
| `scripts/py-tools/archive_venv.py` | 快捷入口：归档 venv 分组 | 调用 archive_project.py --group venv |
| `scripts/py-tools/atomic-git-preflight.py` | **原子：Git 前置验证**。通过 py_lib 加载 git_preflight 插件，执行环境检测 + 安全扫描，返回 GitContext | 任何 git 业务脚本开头的前置验证 |
| `scripts/py-tools/atomic-deploy-preflight.py` | **原子：部署特有前置验证**。验证 .env PAT、分支保护、agent 插件、git 空目录保留 | workflow-deploy-full 部署前验证 |
| `scripts/py-tools/atomic-check-staged-after-add.py` | **原子：Staged 内容安全扫描**。必须在 git add 后执行，强制扫描 staged 文件敏感模式 | add 后 commit 前的安全卡点 |
| `schema/json/lint-rules-manifest.json` | **Lint 规则全局清单**。7 插件 27 条规则，供 audit 巡检对照 | 审计时对照、新增规则后同步更新 |
| `schema/docs/lint-rules-manifest.md` | 清单结构说明、规则 ID 命名约定、联动义务 | 理解 manifest 格式时查阅 |
| `scripts/py_lib.py` | **统一入口**。v1.2.0，新增 __version__ / get_rules_version() / registry.rules_version | 禁止越级直接 import plugin |
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
| **Python 全链条部署** | ✅ | workflow-deploy-full.py 编排 Step 4-9，调用 py-steps 分步执行，支持 --step/--issue 参数 |
| 工具索引 | ✅ | TASK-TOOLS-INDEX.md v1.0（本地+外部引用+边界） |
| Issue 同步体系 | ✅ | github-sync-issue.ps1 + github-api.ps1 + config.json |
| **gh CLI 隔离部署** | ✅ | venv/gh/bin/gh.exe + venv/data-gh（GH_CONFIG_DIR）；headless 认证 GH_TOKEN+GH_CONFIG_DIR，无需 gh auth login |
| **GitHub PR 自闭环** | ✅ | workflow-gh-pr.py（编排 gh-pr-create/merge）+ gh_preflight 插件；研究见 docs/gh-cli-...feasibility-study |
| **版本记录更新** | ✅ | update-version.py（自动发现 → 实测 → 更新 .md + history） |
| **Profile 筛选机制** | ✅ | github-lib.ps1 支持 Profile/Include/Exclude 三层筛选，依赖自动补齐，向后兼容 |


*任务版本: v0.22.0*  
*演进历史: 见 [ENTRY.json](ENTRY.json) `meta.version_history`*
