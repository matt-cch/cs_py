---
title: fallback read 前遗漏审计块——三级 tool 调用中 audit 输出不完整
description: 验证测试中发现：step 1（skill 加载）有审计块，step 2（fallback read SKILL.md）和 step 4（rg 搜索）没有审计块。根因：Agent 将 fallback read 视为 skill 加载的延续步骤，而非独立的 tool 调用，因此未按 tool-audit.mdc 要求输出审计块。
date: 2026-08-06
type: gotcha
fingerprint:
  content_sha256: "gotcha-fallback-read-missing-audit-block-20260806"
  semantic_key: "fallback-read-missing-audit-block"
meta: {}
---

# fallback read 前遗漏审计块——三级 tool 调用中 audit 输出不完整

## 现象

subagent 执行 rg-fd-search 任务时，tool 调用序列如下：

```
step 1: skill（加载 rg-fd-search）→ 有审计块 ✅
step 2: read（fallback 读取 SKILL.md）→ 无审计块 ❌
step 3: bash（fd 列出文件）→ 有审计块 ✅（但这是 rg/fd 搜索优先级审计，不是 tool-audit）
step 4: bash（rg 搜索内容）→ 无审计块 ❌
step 5: read（读取 4 个文件确认）→ 无审计块 ❌
step 6: bash（Test-Path）→ 无审计块 ❌
step 7: write（落盘 manifest）→ 无审计块 ❌
```

只有 step 1 和 step 3 有审计块，其余 5 次 tool 调用均未输出 tool-audit 审计块。

## 根因分析

### 根因 1：Agent 将 fallback 视为"同一动作的延续"

step 1 的审计块中写了：
```
配套 skill 是否已加载？  待确认 → 立即加载
结论：命中 rg-fd-search 场景，必须先加载配套 skill
```

Agent 认为 step 2（read SKILL.md）是 step 1（加载 skill）的延续，不是独立的 tool 调用，因此不再输出审计块。

### 根因 2：rg/fd 搜索优先级审计 ≠ Tool 调用规则层审计

step 3 有审计块，但那是 SKILL.md 定义的【rg/fd 搜索优先级审计】，不是 tool-audit.mdc 定义的【Tool 调用规则层审计】。

Agent 在 step 3 输出了 rg/fd 审计，但 step 4-7 的 bash/read/write 调用前没有输出 tool-audit 审计。

### 根因 3：tool-audit.mdc 的适用范围遗漏了 read

tool-audit.mdc 当前只要求 `bash`/`write`/`edit` 前审计。`read` 不在列表中，因此 step 2 和 step 5 的 read 调用前没有审计义务。

## 修复方式

### 修复 1：tool-audit.mdc 适用范围扩展

将 `read` 纳入必须审计的 tool 类型：

```
| 工具 | 触发条件 |
|------|---------|
| `bash` | 任何 Shell 命令执行 |
| `write` | 新建任何文件 |
| `edit` | 对已有文件进行结构性/流程性变更 |
| `read` | 读取任何文件（尤其是 skill/SKILL.md 等上下文文件） |
```

### 修复 2：fallback 动作视为独立 tool 调用

在审计块中明确声明：
```
- 配套 skill 是否已加载？  否 → fallback 到磁盘 read，本次 read 视为独立 tool 调用，需叠加审计
```

### 修复 3：二级/三级 tool 调用必须重复审计

任何一次 tool 调用（即使与前一次有因果关系）都必须独立输出审计块。禁止以"这是上一步的延续"为由跳过审计。

## 反模式

1. **将 fallback read 视为 skill 加载的子步骤**：read 是独立 tool，必须独立审计
2. **用 rg/fd 审计替代 tool-audit**：两者是不同层级的审计，不可互相替代
3. **以为"输出过一次审计块就覆盖全程"**：每次 tool 调用前都必须重新审计

## 关联演进

- evolution v1.3.0：建立了三层闭环（mdc 声明 + skill 声明 + 全局审计卡点）
- evolution v1.4.0：应基于本 gotcha，将审计覆盖范围从 bash/write/edit 扩展到 read，并强化"每次 tool 调用独立审计"的铁律
