---
title: deploy-git-isolated — 语义定义
description: Task、Skill、Workflow 的本质语义与边界区分。回答「什么是 Task」「Task 与 Skill 的区别」「Workflow 与 SKILL.md 的根本差异」。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 语义定义

## 1.1 什么是 Task

Task 是**将一次可复用的工程操作固化为标准化骨架**的单元。特征：

- **有明确生命周期**：预检 → 扫描 → 处理 → 验证 → 比对 → 清理（6 步闭环）。
- **有真源索引**：`ENTRY.json` 是机器唯一入口，人类通过 `README.md`、`SOP.md` 和 `EXEC-CHEATSHEET.md` 进入。
- **有设计文档**：`DESIGN.md` 记录决策、SOP、踩坑，供跨 session 接续。
- **有脚本化调用**：速查表中的每条命令对应磁盘上的独立 `.ps1` / `.py` 文件，禁止现写。


## 1.2 Task 与 Skill 的区别

| 维度 | Task | Skill |
|------|------|-------|
| **定位** | 一次性/周期性工程操作 | 可复用的 Agent 能力扩展 |
| **载体** | `references/tasks/` 目录 | `.agents/skills/` 或 `.opencode/skills/` |
| **入口** | `ENTRY.json` + `run-entry.py` | `SKILL.md` |
| **调用方** | Agent / 人类终端 | 仅 Agent（OpenCode subagent） |
| **生命周期** | 执行完可归档 | 长期驻留 |


## 1.3 Workflow 与 SKILL.md 的本质区别

> **来源**：用户明确确认（2026-06-25）。本节是 [baseline-principles.md](baseline-principles.md) 0.6 节「Workflow 自闭环执行铁律」的语义补充。

### 1.3.1 设计哲学差异

| 维度 | Workflow（Task 形态） | SKILL.md |
|------|----------------------|----------|
| **设计主体** | human + AI **共同设计**，human 审核确认 | AI **单方面实现**，SKILL.md 是交付物 |
| **固化程度** | **步骤已固化**，不可临场变更 | **步骤开放**，AI 每轮可调整 |
| **验证方式** | 上线前共同验证通过，后续按既定步骤执行 | 每次调用都可能引入新判断逻辑 |
| **迭代方式** | 发现问题 → 修 workflow 代码 → 重新验证 | 发现问题 → AI 临场调整 prompt |

### 1.3.2 AI 介入程度差异

| 阶段 | Workflow | SKILL.md |
|------|---------|----------|
| **执行前** | AI 只构造入参，不做任何预检 | AI 判断是否需要检查环境、读取配置 |
| **执行中** | 代码控制全部流程，AI 不介入 | AI 持续在场，根据输出决定下一步 |
| **执行后** | 代码输出报告，AI 可复述但不可替代 | AI 生成总结、建议、后续操作 |
| **失败时** | AI 读取错误 → 修 workflow/入参 → 重试 | AI 临场分析原因、制定新策略 |

### 1.3.3 类比理解

- **Workflow = 航空 checklist**：飞行员（AI）按清单逐项执行，不临场判断「要不要检查油量」，清单已经规定了「起飞前必须检查油量」。如果 checklist 有缺陷，地面工程师（human + AI）修改 checklist，飞行员下次按新版执行。
  - **workflow 内部的 AI 步骤 = checklist 中的「自动气象报告」**：报告本身是机器生成的，但飞行员不负责判断「要不要生成报告」——checklist 已经写明了「第 5 步：获取自动气象报告」。
- **SKILL.md = 飞行手册**：飞行员（AI）遇到异常时查阅手册，根据当前情况判断「应该做什么」。手册提供指导，但不替代判断。

### 1.3.4 对 Agent 的行为要求

| 场景 | Workflow 的正确行为 | SKILL.md 的正确行为 |
|------|-------------------|-------------------|
| 用户说「部署」 | 直接执行 `workflow-deploy-full.py --auto`，不做任何预检 | 加载 SKILL.md，根据上下文判断如何执行 |
| workflow 失败 | 读取错误输出 → 修 workflow 或修入参 → 重试 | 分析失败原因 → 调整策略 → 继续 |
| 用户说「检查一下」 | 检查是 workflow 的步骤之一，代码执行；不是 AI 临场决定 | AI 判断「检查什么、怎么检查」 |
| 需要新增步骤 | 与 human 共同设计 → 修改 workflow 代码 → 验证 → 固化 | AI 在 SKILL.md 指导下临场扩展 |

### 1.3.5 一句话区分

> **Workflow 是「已验证的剧本」，AI 是演员，只负责念台词（构造入参）和谢幕（等待结果）。**  
> **SKILL.md 是「导演笔记」，AI 是导演，负责临场调度。**


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
