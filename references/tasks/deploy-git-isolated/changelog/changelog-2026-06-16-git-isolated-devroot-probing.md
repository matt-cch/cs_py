---
title: deploy-git-isolated — git-isolated.ps1 devroot 探测逻辑变更
description: git-isolated.ps1 从硬编码 devroot 路径改为从脚本位置向上回溯探测，同时暴露跨环境迁移的已知缺陷。
date: 2026-06-16
---

# deploy-git-isolated — git-isolated.ps1 devroot 探测逻辑变更

## 变更概览

| 属性 | 值 |
|------|-----|
| **变更类型** | Fixed（修复硬编码）+ Known Issue（暴露跨环境缺陷） |
| **影响范围** | `scripts/git-isolated.ps1` |
| **风险等级** | 低（本地已验证通过） |
| **触发原因** | Subagent 验证时发现 `$devroot = 'D:\pjt\cursor\cs_py'` 为硬编码，用户要求修复 |

---

## 变更时间线

### 2026-06-16 — git-isolated.ps1 devroot 从硬编码改为动态探测

| 变更项 | 之前 | 之后 | 触发原因 |
|--------|------|------|---------|
| `scripts/git-isolated.ps1` 中 `$devroot` 赋值 | 硬编码：`$devroot = 'D:\pjt\cursor\cs_py'` | 动态探测：从 `$PSScriptRoot` 出发，逐级向上检查 `venv\git\cmd\git.exe` 是否存在，命中即停 | Subagent 在零上下文验证时指出硬编码问题，用户要求修复 |
| `scripts/git-isolated.ps1` 防死循环条件 | 无（旧代码无循环） | `while` 循环 + `[string]::IsNullOrWhiteSpace($parent)` 边界检查，防止遍历到盘符根后抛异常 | 动态探测引入循环，需防边界条件 |
| 全 task `.ps1` 硬编码路径扫描 | 存在 `git-isolated.ps1` 中的硬编码 | 全 task 范围内 `.ps1` 已无 `D:\pjt\cursor\cs_py` 硬编码残留 | 修复后验证，确保无遗漏 |

---

## 验证结果

| 检查项 | 结果 |
|--------|------|
| `lint-ps1.ps1` 语法检查 | ✅ 通过 |
| `git status` 执行 | ✅ 正常输出 |
| `git log --oneline` 执行 | ✅ 正常输出 |
| `git remote -v` 执行 | ✅ 正常输出 |
| 全 task 硬编码扫描 | ✅ 无残留 |

---

## 已知问题（待优化）

| 问题 | 说明 | 后续方向 |
|------|------|---------|
| 向上回溯探测不够优雅 | 假设 `git-isolated.ps1` 始终在 devroot 的子目录下，若脚本被移到 devroot 外（如全局工具目录）或跨环境目录结构不同，探测失效 | 用户指示下次优化，方向待定（可能引入环境变量 fallback、调用参数、.env 配置等） |

> **用户原话**："这只是一种实现方法，只算跑通了一条路而已，远谈不上优雅巧妙。比如现在本地环境是这种路径，但是你 push github 了，另外一个环境 pull 下来，那个 devroot 不一定是这种路径，你这条路就走不通了。"

---

## 关联文件

| 文件 | 变更状态 |
|------|---------|
| `scripts/git-isolated.ps1` | ✅ 已修改（硬编码 → 动态探测） |
| `changelog/initial.md` | 无变更 |

---

*变更日期: 2026-06-16*  
*记录人: Agent*  
*下次触发条件: 用户指令优化 devroot 探测逻辑时*
