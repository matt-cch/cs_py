---
title: Workflow 自闭环执行铁律固化与部署脚本文档增强
description: 在 task-canonical-baseline.md 中新增 0.6 节「Workflow 自闭环执行铁律」与 1.3 节「Workflow 与 SKILL.md 的本质区别」；重写 workflow-deploy-full.py docstring，明确 preflight 内置、参数表格、调用示例与回滚说明。
date: 2026-06-25
meta: {}
---

# `env-migration-workflow-self-contained-execution-2026-06-25-142208.md`

> **文档性质**：环境迁移指南。聚焦开发环境工具链与规范的变更，非业务功能交付。  
> **受众**：Human + Agent。在新环境可直接阅读本文档并执行复现步骤。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Workflow 自闭环执行铁律固化与部署脚本文档增强 |
| **日期** | 2026-06-25 |
| **文件名时间戳** | `2026-06-25-142208` |
| **触发原因** | 执行 deploy-git-isolated 自动部署时，Agent 先现写 bash 预检再执行 workflow，违背「workflow 步骤已固化、Agent 不应干预」的原则 |
| **影响范围** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md`、`scripts/py-tools/workflow-deploy-full.py` |
| **风险等级** | 低（规范补充与文档改进，不影响现有工具链运行） |

## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | 追加 |
| **新增内容** | 0.6 节「Workflow 自闭环执行铁律（No Ad-hoc Intervention）」+ 1.3 节「Workflow 与 SKILL.md 的本质区别」 |
| **作用** | 明确 workflow 与 SKILL.md 的边界：workflow 步骤已固化，Agent 执行时不得预检、干预、替代总结或绕过；SKILL.md 则允许 AI 持续在场判断 |
| **验证方式** | 检索文档中是否包含「0.6 Workflow 自闭环执行铁律」标题 |
| **迁移方式** | 直接覆盖（追加章节，不破坏既有内容） |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | 修改（docstring 重写） |
| **新增/修改内容** | 重写顶部 docstring：明确「先执行内置 preflight，再编排 Step 4-9」；新增参数表格（--devroot / --message / --auto / --step / --issue）；新增 4 个 Agent 调用示例（绝对路径）；新增回滚说明 |
| **作用** | 消除 Agent 对「是否需要预检」的歧义，直接构造入参执行即可 |
| **验证方式** | `python -m py_compile workflow-deploy-full.py` 通过；执行 `--auto` 模式成功部署 |
| **迁移方式** | 直接覆盖 |

## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。

## 三、环境变量速查

无新增环境变量。

## 四、落盘验证

| 文件类型 | 验证工具 | 结果 |
|---------|---------|------|
| `.md`（baseline） | run-lint.py（md_lint + lint_encoding） | ✅ 通过 |
| `.py`（workflow） | run-lint.py（lint_python + lint_encoding） | ✅ 通过 |

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 baseline 已更新 | `Select-String -Path "task-canonical-baseline.md" -Pattern "0.6 Workflow 自闭环执行铁律"` | 命中 |
| 2 | 确认 workflow docstring 已更新 | `Select-String -Path "workflow-deploy-full.py" -Pattern "先执行内置 preflight"` | 命中 |
| 3 | 确认 workflow 可直接执行 | `python workflow-deploy-full.py --auto` | `[SUCCESS] 部署完成` |
| 4 | 确认部署未触发预检 | 观察执行日志 | 无 Agent 现写 bash 预检命令 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 baseline | `git checkout references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| 恢复 workflow docstring | `git checkout references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-25-142208 |
| **更新人** | Human + Agent Session |
| **变更触发** | workflow 执行过程中 Agent 误用预检命令，需固化为规范 |
| **下次修订条件** | workflow 新增参数或执行模式变更时同步更新 docstring |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-25*  
*模板版本：v2*
