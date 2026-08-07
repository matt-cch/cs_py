---
title: 审计基准 — 路径引用不硬编码原则
description: 禁止在搜索范围、工具路径、vault 挂载点等场景中硬编码具体路径。必须遵循"探测 → HITL → 动态引用"三层约定。
date: 2026-08-07
meta:
  version: "1.0.0"
  tags: [baseline, no-hardcode, polyrepo, hitl, audit]
---

# 审计基准 — 路径引用不硬编码原则

## 一句话定义

**任何涉及路径引用、范围扩展、目录探测的搜索操作，禁止将路径写死为常量或默认值；必须先探测存在性，不存在时 HITL 询问用户，最终以用户确认或运行时实测的路径为准。**

## 适用场景

| 场景 | 典型反例 | 正确做法 |
|------|---------|---------|
| 搜索范围扩展至 vaults | "vaults/ 肯定在 devroot 下，直接搜" | 先 `Test-Path` 探测，不存在时询问用户 |
| 工具链调用 | "python 肯定在 venv/py/" | 调用前 `sys.executable` 交叉验证 |
| 跨 polyrepo 操作 | "target 肯定在 devroot/apps/" | 通过 `--devroot` 显式传入，禁止假设 CWD |
| 索引文件引用 | "ENTRY.json 肯定在 task 根目录" | 从 `get_devroot()` 动态推导 |

## 三层约定

### Layer 1 — 探测（Probe）

Agent 在引用任何路径前，必须先执行存在性探测：

```powershell
# PowerShell
Test-Path -LiteralPath (Join-Path $devroot "vaults")

# Python
import os
os.path.exists(os.path.join(devroot, "vaults"))
```

### Layer 2 — HITL（Human-in-the-Loop）

探测结果为 **不存在** 时，**必须暂停当前任务**，向用户说明：

```
[HITL] 未在 devroot 下找到 vaults/ 目录。
当前 devroot: D:\pjt\cursor\cs_py
请确认：
1. vault 是否挂载在其他路径？
2. 是否跳过 vaults/ 搜索范围？
```

**禁止行为**：
- ❌ 自行假设 vault 路径（如 `C:\vaults`、`${devroot}\..\vault`）
- ❌ 跳过 vaults/ 搜索而不告知用户
- ❌ 将假设路径静默写入代码或配置

### Layer 3 — 动态引用（Dynamic Resolution）

探测通过或用户确认后，所有路径引用必须通过变量/参数动态解析：

```powershell
# 正确：通过变量引用
$vaultsDir = Join-Path $devroot "vaults"
& "${devroot}\venv\ripgrep\rg.exe" -n "关键词" "$vaultsDir"

# 错误：硬编码绝对路径
& "${devroot}\venv\ripgrep\rg.exe" -n "关键词" "D:\pjt\cursor\cs_py\vaults"
```

## Agent 自检清单（审计基准）

任何涉及路径的 tool 调用前，Agent 必须输出：

```
【路径引用审计】
- 目标路径是否经过存在性探测？            是/否
- 路径是否硬编码为常量？                   是/否
- 若目标不存在，是否已 HITL 询问用户？      是/否
- 路径是否通过变量/参数动态引用？           是/否
- 是否符合多端多根原则（vaultroot 不固定）？ 是/否
结论：合规 / 需改道
```

## 反面教材

| 场景 | 错误做法 | 后果 |
|------|---------|------|
| 搜索 gh 工作进度 | 仅搜索 `references/env-migrations/`，未探测 `devroot/vaults/` | 丢失 vaults/ 下的进度看板、架构设计、踩坑记录 |
| 下载 Chromium | 硬编码下载目录为 `D:\download` 写入脚本 | 在其他终端（Linux/Mac）上失效 |
| 调用 Python | 脚本中写死 `D:\pjt\cursor\cs_py\venv\py\python.exe` | 多端执行时路径错误 |

## 关联演进

| 演进 | 说明 |
|------|------|
| `evolution-2026-08-07-search-scope-extension-to-vaults.md` | 本次不硬编码原则的直接触发源：P0 搜索范围扩展至 vaults/ 时，必须探测而非假设 |

## Human 偏好声明

> **用户明确确认（2026-08-07）**：vaultroot 为多端不固定根目录，devroot/vaults/ 只是当前仓库内的一个 vault 挂载点。Agent 在任何涉及 vaults/ 的操作中，必须先探测存在性，不存在时 HITL 询问，禁止自行假设路径。
