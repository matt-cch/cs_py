---
title: 单向声明不足——改 SKILL.md 无法阻止 mdc→skill 触发断裂
description: 修正进化路径。先前以为在 SKILL.md 增加配套 mdc 声明即可闭环，但实战中用户指出：mdc 已触发而 skill 未加载时，改 SKILL.md 毫无意义，因为 skill 根本不会被读到。真正的兜底必须在另一个 alwaysApply mdc（tool-shell-audit）中增加跨规则层检查。
date: 2026-08-06
type: gotcha
fingerprint:
  content_sha256: "gotcha-unilateral-declaration-insufficient-20260806"
  semantic_key: "mdc-skill-unilateral-declaration-insufficient"
meta: {}
---

# 单向声明不足——改 SKILL.md 无法阻止 mdc→skill 触发断裂

## 现象

前序 session 建立 mdc-skill 配套关联机制后（evolution v1.2.0），在 SKILL.md 中增加了配套 mdc 声明、在 mdc 自检清单中增加了 skill 加载检查项。

但本次 session 中，用户再次要求"查看 gh 工作进度"，Agent 的 mdc 已自动触发，Agent 也使用 rg/fd 执行了搜索。问题在于：
1. Agent 尝试用 `skill` 工具加载 rg-fd-search，但系统提示的 `<available_skills>` 列表不包含它，加载失败
2. Agent fallback 到 glob/grep 原生工具，完全没读 SKILL.md
3. 用户追问后，Agent 才承认：skill 文件存在但不在 available_skills 里
4. 用户进一步指出："改 SKILL.md 有鬼用啊，都没有触发"

## 根因分析

### 根因 1：单向声明本质上是"死后验尸"

mdc 和 SKILL.md 的互相声明，只有在 Agent **同时读取两者**时才有效。但实战中：
- mdc 是 alwaysApply，被系统自动加载
- skill 不在 `<available_skills>` 列表中，Agent 根本不会去读
- 结果：mdc 的声明对 Agent 可见，skill 的声明对 Agent 不可见
- 单向声明变成"只有一半生效"

### 根因 2："skill 加载失败"≠"skill 不存在"

Agent 的错误推理链：
```
skill 工具返回 "not found" → skill 不存在 → 不需要读 SKILL.md
```
实际上：
```
skill 工具返回 "not found" → 系统提示列表不完整 → 必须 fallback 到磁盘 read
```

Agent 把"工具接口找不到"误等同于"资产不存在"，错过了 fallback 路径。

### 根因 3：没有全局审计卡点

即使有 mdc 声明和 skill 声明，如果 Agent 的执行流程中没有**在操作前强制检查**配套 skill 状态，Agent 仍可能跳过。

evolution v1.2.0 只在 mdc 自检清单中加了检查项，但 mdc 的自检是 mdc 自己触发的——如果 Agent 不输出 mdc 自检（或跳过自检直接执行），检查项就失效了。

## 修复方式

### 修复 1：跨规则层全局审计卡点

在另一个 alwaysApply mdc（`high-frequency-tool-shell-audit.mdc`）中追加配套 skill 检查项：

```
- 当前 mdc 是否有配套 skill？    是/否 → 若是：<skill-name>
- 配套 skill 是否已加载？        是/否 → 若是：确认 skill 路径 <path>；若否：立即停止当前路径，先加载 skill
```

这样，**任何** tool 调用（bash/write/edit）前都会触发审计，审计层独立于具体 mdc，形成全局卡点。

### 修复 2："是"时必须展示操作对象

审计清单中所有"是/否"项，当答案为"是"时，必须明确写出具体的名称、路径或执行动作。例如：

- 错误：`是`（敷衍，无法验证）
- 正确：`是 → high-frequency-shell-guard-content.mdc`（可验证）
- 正确：`是 → 叠加执行 high-frequency-shell-guard-content.mdc 审计`（可验证）

### 修复 3：skill 不可用时必须 fallback 到磁盘 read

Agent 加载 skill 失败后，应立即执行：

```powershell
# 扫描磁盘确认 skill 存在性
& "${devroot}\venv\fd\fd.exe" -g "SKILL.md" "${devroot}\references\tasks\deploy-git-isolated\skills"
# 直接 read SKILL.md 获取上下文
```

禁止以"skill 工具找不到"为由放弃获取 skill 上下文。

## 反模式

1. **只在 SKILL.md 改声明**：skill 没被加载时，修改对 Agent 不可见
2. **只在 mdc 自检清单加检查项**：Agent 可能跳过自检直接执行
3. **"是"时不写具体操作对象**：无法验证是否真执行了
4. **skill 加载失败就放弃**：不尝试 fallback 到磁盘 read
5. **以为"双向声明"等于"闭环"**：没有全局审计卡点时，双向声明只是静态文档

## 关联演进

- evolution v1.2.0：`evolution-2026-08-06-mdc-skill-pairing-mechanism.md`（双向显式声明）
- evolution v1.3.0：本 gotcha 触发后，将"跨规则层全局审计"纳入配套关联机制，升级为三层闭环
