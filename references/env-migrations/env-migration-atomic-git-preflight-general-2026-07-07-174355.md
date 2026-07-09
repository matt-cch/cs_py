---
title: 多 polyrepo 通用 Git Preflight 工具建设
description: 新增 atomic-git-preflight-general.py，解决工具链锚定 Path.cwd() 与操作目标显式分离的多仓库验证问题。
date: 2026-07-07
meta:
  version: "1.0.0"
---

# env-migration-atomic-git-preflight-general-2026-07-07-174355

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 多 polyrepo 通用 Git Preflight 工具（`atomic-git-preflight-general.py`）建设与验证 |
| **日期** | 2026-07-07 |
| **文件名时间戳** | `2026-07-07-174355` |
| **触发原因** | 在 jywl-lab 切换场景中发现 `atomic-git-preflight` 的 `--devroot` 语义将工具链配置与操作目标混为一谈，无法在 polyrepo 下正常工作 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/`（新增 1 个 Workflow 脚本） |
| **风险等级** | 低（新增独立工具，不影响既有脚本） |


## 一、文本文件变更清单

### 1. 新建 `atomic-git-preflight-general.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-preflight-general.py` |
| **变更类型** | 新建 |
| **新增内容** | 通用 Git Preflight 验证原子工具，支持 `--target` 显式指定操作仓库，`--security` / `--security-level` 控制扫描粒度 |
| **作用** | 工具链锚定 `Path.cwd()`，操作目标通过 `--target` 显式指定，解决多 polyrepo 场景下既有 `atomic-git-preflight` 语义冲突 |
| **验证方式** | 在 cs_py devroot 下执行 `--target jywl-lab`，确认输出身份/分支/remote 正确，安全扫描可按级别开关 |
| **迁移方式** | 直接复制文件到目标环境即可，无需额外配置 |

**核心设计差异**（与既有 `atomic-git-preflight.py` 对比）：

| 维度 | 既有 `atomic-git-preflight` | 新增 `atomic-git-preflight-general` |
|------|---------------------------|----------------------------------|
| `--devroot` 语义 | 同时承载工具链配置 + 操作目标 | 工具链锚定 `Path.cwd()`，操作目标用 `--target` |
| `.env` 读取 | `devroot/.env` | `Path.cwd()/.env`（工具链配置） |
| git 检测目标 | `devroot/.git` | `--target/.git` |
| 适用场景 | 单仓库（devroot 自身） | 多 polyrepo（devroot + 任意独立仓库） |
| 安全扫描 | 固定开启 | `--security-level off/minimal/basic/full` 四级控制 |


## 二、非文本操作

本次 session 无文件系统/缓存迁移操作，仅新增脚本文件。


## 三、验证清单

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | 默认模式（无安全扫描） | `python atomic-git-preflight-general.py --target "<devroot>\apps\repos\jywl-team\jywl-lab"` | 输出 Git 环境信息，无 Security Scan 段落 |
| 2 | 快捷开启基本扫描 | `--target jywl-lab --security` | 输出环境 + Security Scan (level: basic) |
| 3 | 最小扫描级别 | `--target jywl-lab --security-level minimal` | 仅显示 tracked 文件数 + violations |
| 4 | 完整扫描级别 | `--target jywl-lab --security-level full` | 显示全部检测项 + violations |
| 5 | 显式关闭 | `--target jywl-lab --security-level off` | 与默认模式等效，无扫描 |
| 6 | lint 验证 | `run-lint.py --files atomic-git-preflight-general.py` | 通过，0 违规 |


## 四、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建文件 | `Remove-Item "references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-preflight-general.py"` |
| 恢复既有工具 | 继续使用 `atomic-git-preflight.py`（单仓库场景仍有效） |


## 五、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-07-174355 |
| **更新人** | Human + Agent Session |
| **变更触发** | jywl-lab polyrepo 切换时发现既有 preflight 语义不匹配 |
| **下次修订条件** | 新增更多 security-level 级别，或 `--target` 支持相对路径 |
| **跨环境迁移参考** | 直接复制 `atomic-git-preflight-general.py` + 按验证清单逐条执行 |


*文档生成时间：2026-07-07-174355*
