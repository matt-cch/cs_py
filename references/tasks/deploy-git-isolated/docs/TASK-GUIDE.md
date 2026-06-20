---
title: deploy-git-isolated — Task Canonical Baseline 落地指南
description: 本 task 如何遵循 task-canonical-baseline.md 定义的语义、真源、命名与认知契约。
date: 2026-06-16
meta: {}
---

# deploy-git-isolated — Task Canonical Baseline 落地指南

> **对应基线**：`schema/task-template/task-canonical-baseline.md`  
> **本指南职责**：说明本 task 的目录结构、命名选择、真源位置、Agent/Human 对照路径如何落地基线。


## 1. 语义确认（Intent → Baseline）

### 1.1 本 Task 的意图

| 问题 | 确认答案 |
|------|---------|
| 这是什么？ | 在 devroot 内部署隔离版 Git CLI，实现配置/身份与系统全局切割 |
| 不是 Skill 的理由？ | 这是一次性部署操作，非 Agent 可复用的能力扩展 |
| 预期执行者？ | Agent 执行下载部署，人类 review 验证结果、配置身份 |
| 执行后产物？ | `venv/git/` + `venv/data-git/` + 可复用的隔离调用脚本 |

### 1.2 边界约定

- **不做的事**：不修改系统 PATH、不替换系统 Git、不强制 VS Code 终端注入
- **做的事**：全路径调用 + HOME 重定向，让隔离 Git 自包含运行


## 2. 真源契约（Single Source of Truth）

### 2.1 路径真源

| 语义 | 真源文件 | 字段 |
|------|---------|------|
| 隔离 Git 可执行文件 | `verified-runtime-index.json` | `toolchain.git.executable` |
| 隔离配置目录 | `task-config.json` | `paths.git_data_dir` |
| 下载源与版本 | `task-config.json` | `download.version`, `download.asset_name` |
| 脚本清单与状态 | `ENTRY.json` | `active_scripts` |

### 2.2 命名真源

| 命名项 | 约定值 | 消歧说明 |
|--------|--------|---------|
| 隔离 Git 目录 | `venv/git/` | 与 `venv/py/`、`venv/node/` 对齐，一级子目录 |
| 隔离数据目录 | `venv/data-git/` | 与 `venv/data-chrome/`、`venv/data-opencode/` 对齐 |
| 脚本前缀 | `git-*.ps1` | 明确指向 Git 隔离场景，不与系统 Git 脚本混淆 |
| 标准流程 | `SOP.md` | task 根目录，流程契约与验收条件 |
| 执行速查 | `EXEC-CHEATSHEET.md` | `scripts/` 目录，与脚本强绑定（命令+配置+参数） |


## 3. 认知确认（Agent ↔ Human）

### 3.1 已确认的事实

以下事实经 Agent 执行 + Human review 后共同认可：

1. **MinGit 2.54.0** 已下载并解压到 `venv/git/`，`git.exe` 实测可用
2. **HOME 重定向** 生效，`--global` 配置确实落到 `venv/data-git/.gitconfig`
3. **系统 Git 不受影响**，`git --version` 在系统终端仍返回 `2.45.1.windows.1`
4. **不修改 PATH** 的纯隔离方案可行，与 opencode/node 的 PATH 拦截策略区分

### 3.2 待确认的事实（渐进式）

| # | 待确认项 | 状态 | 下一步 |
|---|---------|------|--------|
| 1 | 默认身份（user.name/email）是否写入 | ⏳ 待 Human 提供 | Human 提供后 Agent 写入 |
| 2 | SSH 密钥是否也需要隔离 | ⏳ 待 Human 决策 | 若需要，扩展 `data-git/.ssh/` |
| 3 | GCM 禁用 vs 使用 `store` helper | ⏳ 待 Human 决策 | 当前默认 `cache`（内存） |


## 4. 执行路径对照（Canonical Execution Paths）

### 4.1 速查表位置

- **标准流程文件**：`SOP.md`（task 根目录）
- **执行速查文件**：`scripts/EXEC-CHEATSHEET.md`
- **ENTRY.json 登记**：`"sop": "references/tasks/deploy-git-isolated/SOP.md"`, `"cheatsheet": "references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md"`
- **选择理由**：SOP 是 task 级流程契约，放根目录；EXEC-CHEATSHEET 与 `scripts/*.ps1` 强绑定，放同目录便于 Human 查命令时顺便看脚本

### 4.2 调用格式对照

详见 `scripts/EXEC-CHEATSHEET.md`，核心约定：

| 执行者 | 格式 | 前缀 |
|--------|------|------|
| Agent | `powershell -ExecutionPolicy Bypass -File "${devroot}\...\script.ps1"` | 绝对路径 + 显式策略 |
| Human | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\...\script.ps1` | 相对路径 + 进程级策略 |


## 5. 修订联动记录

| 变更 | 联动文件 | 状态 |
|------|---------|------|
| 新增 `git-*.ps1` 脚本 | `SOP.md` 新增 Step 契约，`EXEC-CHEATSHEET.md` 新增对照块 | ✅ 已完成 |
| 脚本状态 `ready` | `ENTRY.json` 更新 `status` | ✅ 已完成 |
| 速查表位置例外（放 `scripts/`） | 本指南记录理由 | ✅ 已完成 |
| 登记 Git 工具链 | `verified-runtime-index.json` | ✅ 已完成 |


## 6. 与 Canonical Baseline 的差异说明

| 基线推荐 | 本 task 实际 | 差异理由 |
|---------|-------------|---------|
| `SOP.md` 默认在 task 根目录 | 实际在 task 根目录 | 标准流程是 task 级契约，与 README/ENTRY 同级 |
| `EXEC-CHEATSHEET.md` 默认在 `scripts/` | 实际在 `scripts/` | 执行速查与脚本强绑定，Human 查命令时需同时看脚本源码 |
| `run-entry.py` 统一入口 | 当前未填充 | 本 task 以分步执行为主，一键入口待后续补充 |
| `step-01-scan.py` / `step-04-compare.py` / `step-05-cleanup.py` | 状态 `pending` | 骨架已建，按需填充 |


*指南版本: v1.0*  
*对应基线: task-canonical-baseline.md v1.0*  
*创建时间: 2026-06-16*
