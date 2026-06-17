---
title: deploy-git-isolated — GOAL.md
description: 本任务的完整目标-方案-执行-验收-闭环链条（Goal → Solution → SOP → Apply → Review → Ralph Loop）。
date: 2026-06-17
---

# deploy-git-isolated — GOAL.md

> **本文件职责**：定义本任务的「为什么做」「怎么做」「做到什么程度」「做完怎么确认」「出了问题怎么回滚/改进」的完整闭环。是 Agent 与人类对齐意图的第一入口，也是跨 session 接续时的最高优先级读取文件。
>
> **读取顺序建议**：
> 1. 首次接触本 task → 先读 `README.md`（快速决策）→ 再读 `GOAL.md`（理解完整链条）
> 2. 跨 session 接续 → 先读 `GOAL.md`（确认目标与当前状态）→ 再读 `DESIGN.md`（深入决策细节）
> 3. 执行具体步骤 → 读 `scripts/SOP-CHEATSHEET.md`（复制命令）

---

## 1. GOAL — 目标

### 1.1 核心目标

在 devroot 内部署**完全隔离**的 Git CLI（MinGit），使版本控制操作：
- **不触碰**系统全局 Git 配置（`C:\Users\<user>\.gitconfig`）
- **不泄漏**凭据到 Windows 凭据管理器
- **不依赖**系统 PATH 中的 `git.exe`
- **可复现**：新机器解压项目后即可获得一致的 Git 环境与身份配置
- **支持 CI/CD**：提供自动化脚本可调用的一致 Git 环境与身份切换能力，支撑持续集成/持续部署流水线

### 1.2 成功标准（Definition of Done）

| # | 标准 | 验证方式 |
|---|------|---------|
| 1 | `venv/git/cmd/git.exe` 可执行 | `git-isolated.ps1 --version` 返回 MinGit 版本号 |
| 2 | 全局配置写入隔离目录 | `git-isolated.ps1 config --global --list --show-origin` 指向 `venv/data-git/.gitconfig` |
| 3 | 系统 `.gitconfig` 不被读取 | 删除/重命名系统配置后，隔离 Git 仍能正常工作 |
| 4 | Push 前安全检查通过 | `github-safety-check.ps1` 确认 `.env`、密钥等被 `.gitignore` 屏蔽 |
| 5 | GitHub 连接成功 | Step 7 push 成功，GitHub 仓库可见提交 |
| 6 | 多身份可切换 | 同一机器上不同项目可使用不同 `user.name` / `user.email` |
| 7 | CI/CD 脚本可调用 | 自动化脚本可通过 `git-isolated.ps1` 或 `env:GIT_CONFIG_GLOBAL` 方式执行 Git 操作 |
| 8 | 无头环境可用 | 无 GUI/无交互终端中，Git 操作不弹窗、不阻塞（凭据来自 `.env` 或 `store` 文件） |

### 1.3 约束条件

- **不修改系统 PATH**：隔离 Git 不混入系统环境，避免副作用
- **不安装 GCM**：凭据仅内存缓存，不持久化到系统
- **MinGit 优先**：不选 PortableGit（无冗余 GUI/Bash），与现有 zip 分发工具链风格一致
- **全路径调用**：所有脚本显式指定 `${devroot}\venv\git\cmd\git.exe`

---

## 2. SOLUTION — 方案

### 2.1 高层架构

```
┌─────────────────────────────────────────────────────────────┐
│  调用层（scripts/*.ps1）                                      │
│  ├── github-step-01-init.ps1        # 初始化仓库 + 身份       │
│  ├── github-step-02-gitignore.ps1   # 生成安全 .gitignore     │
│  ├── github-step-03-readme.ps1      # 生成 README            │
│  ├── github-step-04-stage.ps1       # 安全 add               │
│  ├── github-step-05-commit.ps1      # commit                │
│  ├── github-step-06-remote.ps1      # 添加 remote           │
│  ├── github-step-07-push.ps1        # push（PAT 认证）       │
│  ├── github-step-08-upstream.ps1    # 设置 upstream         │
│  ├── github-safety-check.ps1        # Push 前安全检查        │
│  └── git-isolated.ps1               # 通用包装器            │
├─────────────────────────────────────────────────────────────┤
│  共享层（github-lib.ps1 + lib-plugins/）                      │
│  ├── lib-constants.ps1              # 常量定义              │
│  ├── lib-encoding.ps1               # 编码处理（BOM/UTF-8）  │
│  ├── lib-config.ps1                 # .env / .gitconfig 读写 │
│  ├── lib-check.ps1                  # 前置检查              │
│  └── lib-git-helpers.ps1            # Git 操作封装          │
├─────────────────────────────────────────────────────────────┤
│  运行时（venv/）                                              │
│  ├── venv/git/                      # MinGit 解压目录       │
│  │   └── cmd/git.exe                # 唯一入口              │
│  └── venv/data-git/                 # 隔离 HOME             │
│      ├── .gitconfig                 # 隔离全局配置          │
│      └── .ssh/                      # 可选：隔离 SSH 密钥   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 关键设计决策

| 决策点 | 选型 | 理由 |
|--------|------|------|
| 隔离机制 | HOME 重定向 + 全路径调用 | 零系统入侵，配置完全收束到项目内 |
| 发行版 | MinGit 2.54.0 | 精简、zip 解压即用、无 GUI 冗余 |
| 凭据管理 | `credential.helper = cache` | 内存缓存，不写入系统凭据管理器 |
| 插件加载 | 拓扑排序（Kahn 算法） | 零文件重名即可插入新插件，依赖自动解析 |
| 身份分层 | global → local → env 覆盖 | 项目默认 + 仓库覆盖 + 临时指定，三层灵活切换 |

### 2.3 边界定义

- **本 task 不做**：Git 服务器搭建、复杂分支策略、完整的 CI/CD 平台（如 Jenkins/GitHub Actions 本身）
- **本 task 做**：MinGit 部署、隔离配置初始化、GitHub 连接、安全检查、日常操作包装、**CI/CD 可调用接口**（提供脚本化 Git 操作能力与身份切换机制）

---

## 3. SOP — 标准操作流程

### 3.1 完整部署流程（首次执行）

```
Step 0: 预检        → 检测残留、确认网络、读取 .env
Step 1: 初始化      → git init + user.name/user.email（来自 .env）
Step 2: .gitignore  → 生成白名单模式 .gitignore（屏蔽 .env / venv / 敏感文件）
Step 3: README      → 生成项目 README（若不存在）
Step 4: 暂存        → git add（仅已跟踪文件 + 新文件安全确认）
Step 5: 提交        → git commit（规范化消息模板）
Step 6: Remote      → git remote add origin（来自 .env GITHUB_REPO_URL）
Step 7: Push        → git push（PAT 认证，HTTPS）
Step 8: Upstream    → git branch --set-upstream-to=origin/main
```

### 3.2 安全检查（Push 前强制）

```
github-safety-check.ps1
├── [1] 已跟踪文件清单
├── [2] 已 staged 文件清单
├── [3] 未跟踪文件清单
└── [4] 敏感文件屏蔽验证（.env / *.pem / venv/ 等必须被 .gitignore 屏蔽）
```

> **铁律**：任何 push 操作前必须先执行安全检查，确认无敏感文件泄露。

### 3.3 日常操作

```
git-isolated.ps1 <子命令>
├── status / log / diff        # 状态查询
├── add / commit / push        # 写入操作
├── clone                      # 隔离方式克隆
└── config --global ...        # 修改隔离全局配置
```

### 3.4 CI/CD 自动化操作

```
# 场景：自动化脚本/CI 流水线中调用隔离 Git
# 方式 A：通过 git-isolated.ps1 包装器（推荐）
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" push

# 方式 B：直接调用 + HOME 重定向（脚本内使用）
$env:HOME = "${devroot}\venv\data-git"
& "${devroot}\venv\git\cmd\git.exe" push origin main

# 方式 C：临时身份覆盖（多仓库 CI）
$env:GIT_CONFIG_GLOBAL = "${devroot}\venv\data-git\.gitconfig-special"
& "${devroot}\venv\git\cmd\git.exe" push origin main
```

**CI/CD 关键原则**：
- 凭据来自 `.env`（PAT）或 `store` 文件（长期缓存），不弹窗交互
- `HOME` 重定向确保配置隔离，不污染 CI 运行环境的系统配置
- 所有操作可脚本化、可 headless（无 GUI、无阻塞）

### 3.5 分步命令速查

详见 `scripts/SOP-CHEATSHEET.md`（Agent/终端双格式对照）。

---

## 4. APPLY — 应用/执行

### 4.1 场景触发映射

| 用户意图 | 场景 ID | 执行链 |
|---------|---------|--------|
| "部署隔离 Git" / "装 git" / "初始化 git" | deploy-git | Step 1→8 完整执行 |
| "连 GitHub" / "push 到 github" / "建仓库" | github-connect | Step 6→8（已有仓库）或 Step 1→8（新仓库） |
| "检查哪些文件会传上去" / "安全确认" | safety-check | `github-safety-check.ps1` |
| "git status" / "看看改了什么" | daily-git | `git-isolated.ps1 status` |
| "commit" / "push" / "add" | daily-git | `git-isolated.ps1 <子命令>` |

### 4.2 前置条件

| 条件 | 来源 | 验证方式 |
|------|------|---------|
| `GIT_USER_NAME` | `.env` | `lib-config.ps1` 读取 |
| `GIT_USER_EMAIL` | `.env` | `lib-config.ps1` 读取 |
| `GITHUB_REPO_URL` | `.env` | Step 6 使用 |
| `GITHUB_PAT` | `.env` | Step 7 HTTPS 认证使用 |
| MinGit 已部署 | `venv/git/` | `Test-Path venv/git/cmd/git.exe` |

### 4.3 执行入口

- **Agent 格式**：`powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\<script>.ps1"`
- **终端格式**：`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\references\tasks\deploy-git-isolated\scripts\<script>.ps1`

---

## 5. REVIEW — 审查与验收

### 5.1 部署完成验收清单

| # | 验收项 | 命令 | 期望结果 |
|---|--------|------|---------|
| 1 | Git 版本正确 | `git-isolated.ps1 --version` | `git version 2.54.0.windows.1` |
| 2 | 身份已配置 | `git-isolated.ps1 config --global user.name` | 输出 `.env` 中的 `GIT_USER_NAME` |
| 3 | 配置隔离 | `git-isolated.ps1 config --global --list --show-origin` | 路径指向 `venv/data-git/.gitconfig` |
| 4 | .gitignore 生效 | `git-isolated.ps1 check-ignore -v .env` | 输出 `.gitignore:1:.env` 等匹配规则 |
| 5 | 安全检查通过 | `github-safety-check.ps1` | `[OK] .env -> 被 .gitignore 屏蔽` |
| 6 | Push 成功 | `github-step-07-push.ps1` | GitHub 仓库可见提交记录 |
| 7 | CI/CD 脚本可调用 | 写一个 `.ps1` 脚本调用 `git-isolated.ps1 push` | Push 成功，无弹窗、无交互阻塞 |
| 8 | 无头环境可用 | 在无 GUI 的 PowerShell 会话中执行 `git-isolated.ps1 status` | 正常返回状态，不弹凭据窗口 |

### 5.2 持续监控项

| 监控项 | 频率 | 负责人 | 工具 |
|--------|------|--------|------|
| 隔离配置是否被系统配置污染 | 每次执行 git 操作前 | Agent | `git-isolated.ps1` 自动重定向 HOME |
| .gitignore 是否覆盖新增敏感文件 | 新增文件后 | Agent/人类 | `github-safety-check.ps1` |
| MinGit 版本是否过时 | 每季度 | Agent | `verify-runtime.ps1` 扫描 |
| PAT 是否过期 | 每次 push 前 | 人类 | GitHub 返回 401 时更换 |
| CI/CD 脚本凭据是否可用 | 每次自动化执行前 | Agent/CI | `.env` 中 `GITHUB_PAT` 非空且未过期 |
| 隔离 HOME 重定向是否生效 | 每次自动化执行前 | Agent/CI | 检查 `git config --global --show-origin` 指向隔离目录 |

### 5.3 质量门

- **Lint 通过**：所有 `.ps1` 脚本必须通过 `schema/tool/lint-ps1.ps1`
- **编码合规**：所有 `.ps1` 含中文内容必须为 UTF-8 with BOM
- **文件写入合规**：所有文件写入必须通过 `file-write-helper.py`，禁止 Shell 内嵌字符串写盘

---

## 6. RALPH LOOP — 闭环与迭代

### 6.1 回滚方案（Rollback）

| 回滚场景 | 操作 | 影响 |
|---------|------|------|
| 完全移除隔离 Git | `Remove-Item -Recurse venv/git/`, `Remove-Item -Recurse venv/data-git/` | 项目内 Git 功能失效，需重新部署 |
| 重置隔离配置 | 删除 `venv/data-git/.gitconfig`，重新执行 Step 1 | 身份、凭据清空，重新初始化 |
| 撤销最近一次 commit | `git-isolated.ps1 reset --soft HEAD~1` | 仅影响本地仓库 |
| 从 GitHub 删除仓库 | 在 GitHub Web UI 操作 | 远程历史丢失，本地保留 |

### 6.2 改进循环（Kaizen）

```
执行 → 记录 → 复盘 → 改进 → 再执行
   ↑                              ↓
   └──────────────────────────────┘
```

| 阶段 | 动作 | 产物 |
|------|------|------|
| **执行** | 按 SOP 执行 Step 脚本 | 操作结果（成功/失败） |
| **记录** | 变更记入 `changelog/` | `changelog-YYYY-MM-DD-*.md` |
| **复盘** | 踩坑记入 `gotchas/` | `gotchas/*.md` |
| **改进** | 更新脚本 / SOP / 设计决策 | `scripts/*.ps1`, `DESIGN.md`, `SOP-CHEATSHEET.md` |
| **再执行** | 验证改进效果 | 测试通过即固化 |

### 6.3 版本演进触发条件

| 触发条件 | 版本递增 | 动作 |
|---------|---------|------|
| 修复脚本 bug / 文档更新 | PATCH | 更新 `changelog/`，刷新 `ENTRY.json` 状态 |
| 新增 Step / 新增工具索引 / 扩展配置 | MINOR | 更新 `ENTRY.json` version_history，追加 changelog |
| 架构重构 / 目录结构重排 / 职责边界变更 | MAJOR | 归档旧版本到 `archive/`，当前版本重置 |

### 6.4 跨 Session 接续协议

当 Agent 在新 session 中继续本 task 时：

1. **读取 `GOAL.md`** → 确认目标与成功标准未变
2. **读取 `README.md` 当前状态** → 了解哪些 Step 已完成
3. **读取 `ENTRY.json`** → 确认脚本状态（ready/pending/deprecated）
4. **读取 `changelog/` 最新条目** → 了解上次 session 的变更与遗留问题
5. **执行下一步** → 按 SOP 继续未完成的 Step

> **自检**：如果在对话中遗忘了 `task-canonical-baseline.md` 的存在，说明上下文已碎片化——请**立即停止推理，重新读取 `task-canonical-baseline.md`**。

---

## 7. 文件导航

| 文件 | 在 GOAL 链条中的角色 | 读取时机 |
|------|---------------------|---------|
| `GOAL.md`（本文件） | **总纲**：目标 → 方案 → SOP → 执行 → 验收 → 闭环 | 首次接触 / 跨 session 接续 |
| `README.md` | **速查**：场景决策、当前状态、待办 | 每次进入 task 先读 |
| `DESIGN.md` | **深度**：设计决策、踩坑、Trigger 治理意图 | 需要理解「为什么这样设计」时 |
| `task-canonical-baseline.md` | **规范**：命名约定、文件组织、修订联动规则 | 需要理解「文件该怎么组织」时 |
| `scripts/SOP-CHEATSHEET.md` | **执行**：Agent/终端双格式命令 | 需要复制具体命令时 |
| `TASK-TOOLS-INDEX.md` | **能力地图**：有什么工具、边界在哪 | 规划「该调哪个工具」时 |
| `ENTRY.json` | **机器真源**：脚本清单、版本历史、状态 | Agent 工具调用前读取 |

---

*文档版本: v1.0*  
*创建时间: 2026-06-17*  
*关联: DESIGN.md v0.2, README.md v0.5.0, task-canonical-baseline.md v1.0*
