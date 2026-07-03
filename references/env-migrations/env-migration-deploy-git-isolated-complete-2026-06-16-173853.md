---
title: deploy-git-isolated 隔离 Git 部署任务建设与文档体系完善
description: 从零部署隔离 Git CLI（MinGit 2.54.0），建立完整的文档体系（规范基线、工具索引、命令速查、触发真源），并通过 Subagent 零上下文验证其自包含性。
date: 2026-06-16
---

# deploy-git-isolated 隔离 Git 部署任务建设与文档体系完善

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | deploy-git-isolated 隔离 Git 部署任务完整建设与文档体系完善 |
| **日期** | 2026-06-16 |
| **文件名时间戳** | 2026-06-16-173853 |
| **触发原因** | 用户要求建立隔离 Git CLI 部署能力，实现配置隔离、GitHub 推送、文档自包含 |
| **影响范围** | `references/tasks/deploy-git-isolated/` 目录全部文件、`schema/tool/lint-json.py`、全局 `verified-trigger-index.json`、`verified-task-index.json` |
| **风险等级** | 中（涉及 GitHub PAT 和 .env 配置，但已隔离处理） |


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/` 目录及核心文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `README.md` | 新建 | Agent/人类场景化决策入口（5 场景速查） |
| `DESIGN.md` | 新建 | 设计文档：隔离机制、SOP、Trigger 治理六维意图 |
| `ENTRY.json` | 新建 | 机器真源索引：脚本清单、版本历史（v0.5.0）、场景映射 |
| `task-config.json` | 新建 | 配置真源：路径、下载源、Git 配置项 |
| `task-canonical-baseline.md` | 新建 | **规范基线**：认知契约、SOP vs TOOLS-INDEX 语义区分、changelog 记录规范 |
| `TASK-TOOLS-INDEX.md` | 新建 | **工具索引**：本地脚本 + 外部通用工具引用 + 边界矩阵 |
| `task-scenario-triggers.json` | 新建 | **触发真源**：5 场景 trigger 映射，带 `$schema` 自描述 |

### 2. 新建/修改 `scripts/` 目录

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `github-lib.ps1` | 新建 | 共享库聚合入口：拓扑排序加载插件 |
| `lib-sort-rules.json` | 新建 | 插件排序真源（依赖图定义） |
| `lib-plugins/core.ps1` | 新建 | 插件：Test-IsolatedGit / Write-StepHeader |
| `lib-plugins/encoding.ps1` | 新建 | 插件：Switch-ToUtf8 / Restore-Encoding |
| `lib-plugins/constants.ps1` | 新建 | 插件：$devroot / $gitExe / $gitHome / $envFile |
| `lib-plugins/env-config.ps1` | 新建 | 插件：Read-EnvConfig |
| `lib-plugins/git-checks.ps1` | 新建 | 插件：tracked / staged / status / safety-check |
| `github-step-01-init.ps1` ~ `github-step-08-upstream.ps1` | 新建 | Step 1-8：完整部署流水线 |
| `github-safety-check.ps1` | 新建 | 综合安全检查（push 前必执行） |
| `git-isolated.ps1` | 新建/修改 | 通用包装器（硬编码 → 动态 devroot 探测） |
| `git-config-global.ps1` | 新建 | 设置隔离全局身份 |
| `git-clone-isolated.ps1` | 新建 | 隔离方式 Clone |
| `git-multi-identity.ps1` | 新建 | 多身份切换演示 |
| `git-verify-isolation.ps1` | 新建 | 验证隔离效果 |
| `SOP-CHEATSHEET.md` | 新建/修改 | 命令速查表（v1.2，精简为纯命令，移除工具索引内容） |

### 3. 新建/修改 `docs/` 目录

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `PLUGIN-ARCHITECTURE.md` | 新建 | 插件化点源架构设计文档（Kahn 拓扑排序、零重命名插入） |

### 4. 新建 `changelog/` 记录

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `changelog/initial.md` | 新建 | v0.1 骨架创建记录 |
| `changelog/changelog-2026-06-16-git-isolated-devroot-probing.md` | 新建 | git-isolated.ps1 硬编码修复 + 已知跨环境缺陷 |

### 5. 新建 `gotchas/` 记录

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `gotchas/forget-task-canonical-baseline.md` | 新建 | Agent 在长对话中遗忘规范基线文件的踩坑记录 |

### 6. 修改全局索引/工具

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `schema/tool/lint-json.py` | 新建 | JSON 语法验证工具（替代 `python -c json.load`） |
| `references/runtime/verified-task-index.json` | 修改 | 登记 `lint-json` 工具 + `.json` lint 规则升级 |
| `references/runtime/verified-trigger-index.json` | 修改 | 登记 `task-deploy-git` source-prefix + 入口 trigger + 冲突域 |
| `references/runtime/verified-runtime-index.json` | 修改 | 登记 Git 工具链 |


## 二、非文本操作

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| MinGit 下载解压 | GitHub Release (ghproxy) | `venv/git/` | MinGit 2.54.0 解压到隔离目录 |
| 隔离配置初始化 | — | `venv/data-git/.gitconfig` | git init + user.name/user.email + credential.helper=cache |
| GitHub 仓库初始化 | — | `https://github.com/matt-cch/cs_py` | 空仓库 push（仅 .gitignore + README.md） |
| `.env` 更新 | — | `D:\pjt\cursor\cs_py\.env` | 追加 GITHUB_REPO_URL / GITHUB_USERNAME / GITHUB_PAT 等配置 |


## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | MinGit 部署验证 | `git-isolated.ps1 --version` | 输出 `git version 2.54.0.windows.1` |
| 2 | 隔离配置验证 | `git-isolated.ps1 config --global --list --show-origin` | 路径指向 `venv/data-git/.gitconfig` |
| 3 | GitHub 推送验证 | `git-isolated.ps1 log --oneline` | 显示 `0996977 init: empty scaffold...` |
| 4 | Subagent 自包含验证 | 零上下文 subagent 读取 task 文档并执行 `git status/log/remote` | 成功执行并判定「足够自包含」 |
| 5 | lint-json.py 验证 | 对 `verified-trigger-index.json`、`ENTRY.json` 执行 lint | `[OK]` 全部通过 |
| 6 | lint-ps1.ps1 验证 | 对所有 `.ps1` 执行语法检查 | 无错误 |


## 四、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除隔离 Git | `Remove-Item -Recurse "venv/git"`、`Remove-Item -Recurse "venv/data-git"` |
| 恢复系统 Git | 删除环境变量 HOME 重定向，裸 `git` 调用恢复系统行为 |
| 删除 task 目录 | `Remove-Item -Recurse "references/tasks/deploy-git-isolated"` |
| 清理 .env | 删除 `.env` 中 GITHUB_PAT 等敏感配置 |


## 五、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-16-173853 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求建立隔离 Git CLI 部署能力 |
| **下次修订条件** | 用户指令优化 devroot 探测逻辑、新增 Step 脚本、目录结构变更 |
| **跨环境迁移参考** | 直接复制 `references/tasks/deploy-git-isolated/` 目录 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-16-173853*  
*模板来源：schema/structure/env-migration-template.md*
