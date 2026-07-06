---
title: jywl-lab 外部仓库 clone 与 Workspace 注册
description: 将 jywl-team/jywl-lab 仓库 clone 到 apps/repos/ 下，并注册为 cs-py.code-workspace 的第四个 folder root，完成 polyrepo 工作流落地。
date: 2026-07-06
meta:
  version: 1.0.0
---

# env-migration-polyrepo-jywl-lab-clone-2026-07-06-164910

> **文档性质**：环境迁移指南。聚焦单次 session 对开发环境配置的变更，供新环境复现。  
> **受众**：Human + Agent。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | jywl-lab 外部仓库 clone 与 Workspace 注册 |
| **日期** | 2026-07-06 |
| **文件名时间戳** | `2026-07-06-164910` |
| **触发原因** | 完成 polyrepo 工作流第一步的后续操作，将 jywl-team/jywl-lab 纳入同一 IDE 并行开发 |
| **影响范围** | `apps/repos/` 目录、`cs-py.code-workspace`、开发环境 workspace 结构 |
| **风险等级** | 低（仅涉及外部 repo clone 和 IDE 配置，不涉及 devroot 业务代码） |

## 一、文本文件变更清单

### 1. 新建 `apps/repos/jywl-team/jywl-lab/`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/repos/jywl-team/jywl-lab/` |
| **变更类型** | `新建`（通过 `git clone`） |
| **来源** | `https://github.com/jywl-team/jywl-lab.git` |
| **作用** | 将外部 polyrepo 纳入 devroot 目录树，与 monorepo 子项目并行开发 |
| **验证方式** | `Test-Path apps/repos/jywl-team/jywl-lab/.git` 应为 `True` |
| **迁移方式** | 在新环境执行 `git clone https://github.com/jywl-team/jywl-lab.git apps/repos/jywl-team/jywl-lab` |

### 2. 新建 `apps/repos/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/repos/README.md` |
| **变更类型** | `新建` |
| **作用** | 外部仓库统一入口的目录自说明文档，含设计原则、子目录导航、新增流程 |
| **验证方式** | `Test-Path apps/repos/README.md` 应为 `True` |
| **迁移方式** | 直接复制文件内容 |

### 3. 修改 `cs-py.code-workspace`

| 属性 | 值 |
|------|-----|
| **路径** | `cs-py.code-workspace`（devroot 根目录） |
| **变更类型** | `追加` |
| **新增内容** | 第四个 folder root：`jywl-lab` → `apps/repos/jywl-team/jywl-lab` |
| **插入位置** | `folders` 数组末尾，原 `web-demo` 之后 |
| **作用** | 在 Multi-root Workspace 中注册 jywl-lab，使其在 IDE Explorer 中独立显示 |
| **验证方式** | JSON 解析后 `folders` 长度为 4，且包含 `name="jywl-lab"` |
| **迁移方式** | 在目标环境的 `.code-workspace` 中追加相同结构 |

## 二、非文本操作（文件系统/缓存迁移）

### 1. Git Clone

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| `git clone` | `https://github.com/jywl-team/jywl-lab.git` | `apps/repos/jywl-team/jywl-lab/` | 完整克隆，含 `.git/`、remote、分支 |

### 复现命令

```powershell
# 确认父目录存在
$repoParent = "<devroot>\apps\repos\jywl-team"
if (-not (Test-Path $repoParent)) {
    New-Item -ItemType Directory -Path $repoParent -Force | Out-Null
}

# 执行 clone
git clone https://github.com/jywl-team/jywl-lab.git "$repoParent\jywl-lab"
```

> **注意**：`<devroot>` 替换为实际绝对路径（如 `D:\pjt\cursor\cs_py`）。clone 完成后目标目录拥有独立的 `.git/` 和 remote 配置。

## 三、环境变量速查

本次 session **无环境变量变更**。`apps/repos/` 下的项目共享 devroot 的 `venv/` 隔离工具链，不额外注入变量。

## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文件） | `run-lint.py` | frontmatter + encoding + md_lint | BOM=no, CRLF=0, frontmatter 合规 |

**执行示例**：
```powershell
"<devroot>\venv\py\python.exe" "<devroot>\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "<devroot>" --files "<devroot>\references\env-migrations\env-migration-polyrepo-jywl-lab-clone-2026-07-06-164910.md"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 jywl-lab 目录存在 | `Test-Path apps/repos/jywl-team/jywl-lab` | `True` |
| 2 | 确认 jywl-lab 是独立 git 仓库 | `Test-Path apps/repos/jywl-team/jywl-lab/.git` | `True` |
| 3 | 确认 remote 配置正确 | `git -C apps/repos/jywl-team/jywl-lab remote -v` | 显示 `origin https://github.com/jywl-team/jywl-lab.git` |
| 4 | 确认 .code-workspace 已注册 | 读取 `cs-py.code-workspace` | `folders` 包含 4 个条目，含 `jywl-lab` |
| 5 | 确认 README.md 导航表已登记 | 读取 `apps/repos/README.md` | 导航表含 `jywl-team/jywl-lab` 行 |
| 6 | 确认 devroot git 不追踪 | `git check-ignore -v apps/repos/jywl-team/jywl-lab` | 被 `.gitignore` 排除 |

## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 从 Workspace 中移除 jywl-lab | 从 `cs-py.code-workspace` 的 `folders` 中删除 `jywl-lab` 条目 |
| 删除 clone 的仓库 | `Remove-Item -Recurse -Force apps/repos/jywl-team/jywl-lab` |
| 保留或删除 README.md | 若 `jywl-team/` 下无其他仓库，可一并删除 `README.md`；若有则保留 |

## 七、与前置 env-migration 的关系

| 前置文档 | 关系 | 说明 |
|---------|------|------|
| `env-migration-polyrepo-workspace-setup-2026-07-06-125559.md` | 前置步骤 | 创建了 `.code-workspace` 框架，但当时仅含 3 个 root，明确说"为后续 jywl-lab clone 做准备" |
| `env-migration-polyrepo-workspace-terminal-env-fix-2026-07-06-160818.md` | 同期配置 | 修复 terminal.env 注入时，`.code-workspace` 已包含 4 个 root（含 jywl-lab） |

> **时间线**：`12:55` 创建 Workspace（3 root）→ `14:10` clone jywl-lab → `14:14` 写 README.md → `16:08` 修复 terminal.env（此时已为 4 root）。本文件补录 `14:10` 的 clone 事件。

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-06-164910 |
| **更新人** | Human + Agent Session |
| **变更触发** | polyrepo 工作流落地，将外部仓库 jywl-lab 纳入 Workspace |
| **下次修订条件** | 新增其他外部仓库到 `apps/repos/`、jywl-lab remote 变更 |
| **跨环境迁移参考** | 执行「复现命令」中的 `git clone` + 追加 `.code-workspace` folder root + 更新 `README.md` 导航表 |

*文档生成时间：2026-07-06*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
