---
title: "scriptc Windows 原生编译踩坑实录：冲动试错 vs 先搜 Issues"
description: "记录一次典型的 Agent 冲动试错行为——在编译失败时反复安装依赖、调整参数，而非先查上游已知问题，最终发现 scriptc 官方已明确 Windows 原生编译不支持。"
date: 2026-07-29
meta:
  tags: [agent-failure, impulse-trial, scriptc, windows, posix, clang]
---

## 事件背景

用户要求用 `scriptc` 将 TypeScript 编译为 Windows 原生可执行文件（`.exe`），观测产物大小和运行效果。此前，`atomic-npm-isolated-install.py` 已完成改造，`scriptc@0.0.17` 也已通过 Local 模式隔离安装成功，`scriptc --version` 验证通过。

## 我的错误行为

### 第一阶段：冲动试错循环

面对 `scriptc build fib.ts` 失败，我的第一反应不是**搜索上游已知问题**，而是立即进入本地试错循环：

1. **反复执行 `scriptc build` / `scriptc run`** —— 期望某次会突然成功
2. **试图安装 clang** —— 假设失败原因是"缺少编译器"，开始查找 Windows 下 clang 的安装方式
3. **调整参数、重试** —— 在没有任何信息支撑的情况下，凭直觉换命令、换路径

整个过程持续了多轮交互，消耗大量 token 和时间，产出为零。

### 第二阶段：信息搜集严重滞后

直到用户明确批评：

> "先搜信息再行动，不要冲动试错。"

我才去搜索 scriptc 的 GitHub Issues，发现：

- **Issue #25**: "Could not run on windows" —— 用户已报告 Windows 编译失败
- **Issue #27**: "runtime: add MSVC POSIX shims for Windows native builds" —— **仍在开发中**（Open 状态）

这些信息**一开始就存在**，我却把它们放在了试错十几轮之后。

## 根因分析

### 不是缺 clang

我最初的假设是"Windows 没有 clang，所以编译失败"。这个假设是**错误的**。

Issue #25 中，用户明确安装了 **VS2022 + clang 19.1.5**，`scriptc run fib.ts` **仍然失败**。这说明编译器不是瓶颈。

### 真正的瓶颈：POSIX-only API

scriptc 的 C runtime 使用了大量 **POSIX-only** 的头文件和类型，Windows（包括 MSVC 和 clang-cl）根本不提供：

| 缺失项 | 来源 | Windows 替代方案 |
|--------|------|-----------------|
| `ssize_t` | POSIX 类型 | `SSIZE_T` (Windows SDK) |
| `clock_gettime` / `CLOCK_MONOTONIC` | POSIX 定时器 | `QueryPerformanceCounter` |
| `nanosleep` | POSIX 睡眠 | `Sleep` / `NtDelayExecution` |
| `dirent.h` | POSIX 目录操作 | `FindFirstFile` API |
| `unistd.h` | POSIX 系统调用 | Windows 无对等头文件 |

官方需要通过 **Issue #27** 添加 "MSVC POSIX shims"（兼容层）才能解决。这不是本地配置问题，是**上游代码层面未完成适配**。

### 当前 Windows 可用能力

| 命令 | 状态 | 说明 |
|------|------|------|
| `scriptc coverage` | ✅ 可用 | 前端静态分析/类型检查（本机已验证 100% static） |
| `scriptc build` | ❌ 不可用 | C runtime 编译失败 |
| `scriptc run` | ❌ 不可用 | 内部仍需编译，同样失败 |

## 正确做法应该是什么

### Step 1：工具安装成功后，立即验证核心能力

`scriptc --version` 通过 ≠ `scriptc build` 可用。安装后应**第一时间**用最小 demo 测试目标功能（`build` / `run`），若失败立即进入 Step 2，而不是反复重试同一命令。

### Step 2：失败一次后，立即搜索上游 Issues

技术工具首次在陌生平台失败时，**最短的排查路径是 GitHub Issues**，不是本地环境：

```
https://github.com/vercel-labs/scriptc/issues?q=windows
```

 Issue #25 和 #27 的标题已经说明了一切。

### Step 3：区分"配置问题"和"上游缺失"

| 特征 | 配置问题 | 上游缺失 |
|------|---------|---------|
| 错误类型 | 路径找不到、权限不足、版本不匹配 | 编译错误（缺失头文件/类型/函数） |
| Issue 中是否有同类报告 | 通常没有 | 通常已有 |
| 本地能否解决 | 调整环境即可 | 必须等上游更新 |

本次错误（`ssize_t` 未定义、`unistd.h` 找不到）是典型的**上游缺失**信号。

## 教训与铁律

### 铁律 1：陌生工具 + 陌生平台 → 先搜 Issues，再动手

在任何技术工具首次部署到新平台时，**先执行一次 GitHub Issues 搜索**（关键词：平台名 + 错误关键词），确认是否有已知兼容性问题。这个过程不超过 2 分钟，可能节省数十分钟的无效试错。

### 铁律 2：同一命令失败 2 次 → 停止重试，切换排查路径

如果同一命令在相同环境下连续失败 2 次，继续第 3 次、第 4 次重试是**纯赌博行为**。必须立即切换策略：读日志 → 搜 Issues → 读源码，三者选其一。

### 铁律 3：编译错误优先怀疑代码兼容性，而非环境缺失

当编译错误涉及"头文件找不到"、"类型未定义"、"函数未声明"时，**优先怀疑项目本身的平台兼容性**，而不是"我少装了某个依赖"。特别是在 Windows 上遇到 POSIX 头文件（`unistd.h`、`dirent.h`、`sys/*.h`）缺失时，几乎可以确定是上游未适配。

### 铁律 4：用户的"先搜信息"指令是止损信号

当用户明确说"先搜集信息"、"不要冲动试错"时，这是**立即终止当前试错路径**的指令。此时应：

1. 停止所有本地命令执行
2. 转向搜索引擎 / Issues / 文档
3. 将搜索结果汇报给用户，确认方向后再行动

## 相关文件与链接

- `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-npm-isolated-install.py` — 隔离安装 scriptc 的工具
- `venv/tmp/fib.ts` — 测试用 TypeScript demo
- `venv/tmp/.scriptc/fib.ll` — scriptc 生成的 LLVM IR 中间产物（前端成功，后端中断）
- https://github.com/vercel-labs/scriptc/issues/25 — "Could not run on windows"
- https://github.com/vercel-labs/scriptc/issues/27 — "runtime: add MSVC POSIX shims for Windows native builds"

## 记录者

Agent (OpenCode / kimi-k2.6)
记录时间：2026-07-29
