---
title: 隔离 Git 部署 — 设计文档
description: 记录隔离 Git 部署的设计决策、标准操作流程、踩坑与验证结论。
date: 2026-06-16
meta: {}
---

# 隔离 Git 部署 — 设计文档

## 1. 背景

项目采用**多端多根**架构，开发环境需与系统全局完全切割。Git 作为版本控制工具，虽不像 Python/Node 那样有运行时版本锁问题，但在以下场景下隔离部署具有明确价值：

- **配置强隔离**：不同项目/身份需要独立的 `user.name` / `user.email`，不与系统 `C:\Users\<user>\.gitconfig` 冲突。
- **可复现环境**：Git 版本与配置纳入项目资产，新机器可一键复现。
- **SSH 密钥隔离**：公司项目与个人项目使用不同密钥时，可在项目级 `.ssh/` 中独立管理。

## 2. 设计决策

### 2.1 隔离机制：全路径调用 + HOME 重定向

**问题**：如何让隔离 Git 不读取系统全局配置？

**方案**：
- 调用时显式指定隔离 Git 的绝对路径：`${devroot}\venv\git\cmd\git.exe`
- 调用前重定向 `HOME` 环境变量到 `${devroot}\venv\data-git`
- Git 读取配置优先级：`--local` > `--global`（受 `HOME` 影响）> 系统级

**效果**：
- `--global` 配置写入 `venv/data-git/.gitconfig`
- `.ssh/` 读取 `venv/data-git/.ssh/`
- 凭据缓存（若使用 `cache` helper）落在 `venv/data-git/`
- 系统 `C:\Users\<user>\.gitconfig` 不被触及

### 2.2 不修改 PATH

**问题**：是否需要像 opencode/node 那样在 `settings.json` 的 `env.PATH` 中追加 `venv/git/cmd`？

**方案**：**不追加**。

**理由**：
- opencode 必须靠 `PATH` 拦截，因为 Cursor 扩展硬编码了裸命令 `opencode.exe --port ...`。
- Git 的调用完全由用户/脚本控制，不存在外部硬编码调用路径。全路径调用更纯粹、无副作用。
- VS Code 终端内裸 `git` 仍命中系统版，这是**预期行为**——只有明确调用隔离版时才使用隔离配置。

### 2.3 发行版选择：MinGit

**问题**：选择 PortableGit 还是 MinGit？

**方案**：**MinGit**。

**理由**：
- MinGit 是 Git for Windows 的精简版（~40MB），包含完整 `git.exe` + `git-cmd.exe` + 核心工具链，无冗余 GUI/Bash。
- 本项目不需要交互式 Bash shell，只需要 Git CLI 功能。
- 与现有工具链（Python embed、Node.js zip 分发）风格一致：zip 解压即用。

### 2.4 凭据管理：禁用 GCM，使用内存缓存

**问题**：Git for Windows 默认集成 Git Credential Manager (GCM)，可能写入 Windows 凭据管理器，破坏隔离。

**方案**：初始 `.gitconfig` 中显式设置：

```ini
[credential]
    helper = cache
```

**效果**：
- HTTPS 凭据仅缓存在内存中（15 分钟默认），不持久化到系统。
- 如需长期缓存，后续可改为 `store`（明文写入 `venv/data-git/.git-credentials`），仍在隔离范围内。

### 2.5 多身份切换策略

| 层级 | 配置位置 | 切换方式 | 适用场景 |
|------|---------|---------|---------|
| 项目默认 | `venv/data-git/.gitconfig` | `git.exe config --global ...` | 项目内大多数仓库共享的身份 |
| 仓库覆盖 | `<repo>/.git/config` | `git.exe config --local ...` | 特定仓库（如个人开源子项目） |
| 临时指定 | 脚本内 `env:GIT_CONFIG_GLOBAL` | 调用前设置环境变量 | CI/自动化脚本 |

## 3. 目标目录结构

```
venv/
├── git/                      # MinGit 解压目录
│   └── cmd/
│       └── git.exe           # 唯一入口
└── data-git/                 # 隔离 HOME
    ├── .gitconfig            # 隔离全局配置
    └── .ssh/                 # 可选：隔离 SSH 密钥
```

## 4. 标准操作流程（SOP）

### 4.1 完整部署流程（一键）

```powershell
# 待 Step 脚本填充后更新
# python run-entry.py --config task-config.json --stage all
```

### 4.2 分步执行

#### Step 0: 预检
检测 `venv/git/` 与 `venv/data-git/` 是否已有残留，确认网络可用。

#### Step 1: 下载与解压
从 GitHub Release（经代理加速）下载 `MinGit-2.54.0-64-bit.zip`，解压到 `venv/git/`。

#### Step 2: 初始化配置
创建 `venv/data-git/`，写入初始 `.gitconfig`（含 `user.name`、`user.email`、`credential.helper = cache`）。

#### Step 3: 验证隔离
```powershell
$env:HOME = "D:\pjt\cursor\cs_py\venv\data-git"
& "D:\pjt\cursor\cs_py\venv\git\cmd\git.exe" --version
& "D:\pjt\cursor\cs_py\venv\git\cmd\git.exe" config --global --list --show-origin
```
确认输出路径指向 `venv/data-git/.gitconfig`。

#### Step 4: 多身份验证
在子仓库中执行 `--local` 配置，验证覆盖生效。

#### Step 5: 清理与回滚
提供一键回滚脚本，删除 `venv/git/` 与 `venv/data-git/`，恢复纯系统 Git 状态。

## 5. 踩坑记录

### 5.1 Agent 遗忘 task-canonical-baseline.md

**现象**：长对话（10+ 轮）后，Agent 遗忘了本 task 已定义的规范基线文件 `task-canonical-baseline.md`，导致对 SOP-CHEATSHEET 与 TASK-TOOLS-INDEX 的语义边界产生混淆，先是承认两者相同，随后自行否定。

**根因**：上下文窗口碎片化 + 缺乏强制自检机制 + 文件未被纳入「每次必查」清单。

**修复**：
1. 生成 `task-canonical-baseline.md` 到 task 根目录
2. `README.md` 顶部增加「Agent 注意：本 task 有已定义的规范基线」提示
3. `README.md` 文件导航表追加 `task-canonical-baseline.md`
4. `ENTRY.json` 登记 `task-canonical-baseline.md` 路径

**详细记录见**：`gotchas/forget-task-canonical-baseline.md`

## 6. Trigger 治理设计意图（元原则）

> **来源**：用户明确确认（2026-06-16）。本节记录 trigger 对照表/索引体系的原始设计意图，作为后续 Agent 重建、审计、扩展时的根本依据，不得擅自修改。

### 6.1 核心意图（一句话）

**Trigger 必须有治理，登记必须有参照，边界必须有比较，冲突必须有协调，过程必须可审计并且有依据，甚至对重建都可能有作用。**

### 6.2 六维意图拆解

| 维度 | 意图说明 | 在本任务中的落地 |
|------|---------|----------------|
| **治理（Governance）** | Trigger 不是随意堆放的字符串列表，而是受 schema 约束、有版本历史、有变更审批规则的结构化资产 | `task-scenario-triggers.json` 受 `task-trigger-index.schema.json` 约束；全局 `verified-trigger-index.json` 有 governance 节 |
| **参照（Reference）** | 新增 trigger 前能查到已有 trigger，避免重复造词、避免同一语义分散在多个 source 中 | `source_prefix_registry` 全局唯一；task 级 triggers 与全局 triggers 通过 `source_prefix` 对齐 |
| **边界（Boundary）** | 不同 skill/mdc/task 的职责边界必须明文定义，防止"看起来都能处理"的灰色地带 | `conflict_domains` 节定义了与 proxy-downloader、download-runtime、project-handoff 的边界 |
| **协调（Coordination）** | 当两个 trigger 同时命中时，有明确的裁决规则，而非 Agent 自行判断 | `conflict_resolution_rules`（CR-001 ~ CR-006）提供上下文/优先级/排他/全执行四种策略 |
| **审计（Auditability）** | 每次触发命中、冲突发生、裁决应用，都必须留下可追溯的记录 | `audit_framework` 节定义 FP/FN/Collision 日志格式、阈值（95%）、review 周期（7天） |
| **重建（Reconstructability）** | 当环境重置、Agent 重启、session 丢失时，能从磁盘上的结构化文件重建完整的 trigger 认知 | `$schema` 自描述 + `meta` 元数据 + `source_file` 指向，使任何 Agent 都能从零读懂整个体系 |

### 6.3 与 config.json $schema 的关联

`config.json` 顶部的 `"$schema": "https://opencode.ai/config.json"` 是本意图的**技术原型**：
- Schema 即契约：读取者无需猜测结构，schema 已经说明了一切
- 自引用即自描述：文件知道自己该被什么规则验证
- 分布式真源：全局索引只存入口，详细映射存在 task 本地，层级清晰

本任务的 trigger 体系完整复制了这一模式：
```
config.json                  →  verified-trigger-index.json（全局入口）
  ↑ $schema                      ↑ 登记 source_prefix、入口 trigger
opencode.ai/config.json      →  task-trigger-index.schema.json（结构契约）
                                 ↑
                            task-scenario-triggers.json（详细映射）
                              ↑ $schema 自引用
```

### 6.4 未来扩展原则

1. **新增 task trigger 时**：先查全局 `source_prefix_registry` 防重名 → 再按 schema 填写 task 本地 → 最后登记全局入口
2. **修改 trigger 词时**：同步更新 task 本地 + 全局入口 + 审计日志（revision_notes）
3. **发现冲突域重叠时**：不是简单改 trigger 词，而是先修订 `conflict_domains` 和 `conflict_resolution_rules`
4. **环境重建时**：读取 `verified-trigger-index.json` 获取全部 source_prefix → 逐个读取各 task 的 `task-scenario-triggers.json` → 重建完整触发图谱


*文档版本: v0.2*  
*创建时间: 2026-06-16*  
*更新: 2026-06-16 — 新增第 6 节 Trigger 治理设计意图*
