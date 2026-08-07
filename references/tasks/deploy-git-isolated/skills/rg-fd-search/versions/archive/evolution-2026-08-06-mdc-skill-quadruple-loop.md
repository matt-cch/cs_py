---
title: mdc-skill 配套关联机制再升级——四层闭环 + 生效 mdc 列表 + 审计全覆盖
description: 基于 subagent 实战验证，将配套关联机制从三层闭环升级为四层闭环。新增铁律 9（生效 mdc 列表自检）、铁律 10（read 纳入审计范围）、铁律 11（每次 tool 调用独立审计）。验证结果：subagent 能正确识别 rg-fd-search-priority.mdc 已触发，能正确定位到 rg-fd-search/SKILL.md 并读取，能按 skill 规范使用 rg/fd 执行搜索。
date: 2026-08-06
type: evolution
scope: append
category: rule
target_section: "## 配套 skill 关联机制（新增章节）"
fingerprint:
  content_sha256: "evolution-mdc-skill-quadruple-loop-20260806"
  semantic_key: "rg-fd-search-mdc-skill-quadruple-loop"
meta: {}
---

# mdc-skill 配套关联机制再升级——四层闭环 + 生效 mdc 列表 + 审计全覆盖

## 背景

evolution v1.3.0 建立了三层闭环（mdc 声明 + skill 声明 + 全局审计卡点），并通过 subagent 实战验证。

验证任务："搜索一下 deploy-git-isolated 的 gotchas 目录下，有哪些关于 mdc-skill 配对的踩坑记录。"

验证结果：
- ✅ 三层闭环生效：mdc 触发识别 → 配套 skill 检查 → fallback 读取 SKILL.md → 按规范执行 rg/fd
- ✅ 生效 mdc 列表项有效：subagent 识别到 rg-fd-search-priority.mdc、tool-shell-audit.mdc、shell-guard-content.mdc 三个 alwaysApply mdc
- ✅ skill fallback 正确定位：subagent 读取了 `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md`
- ✅ rg/fd 真实调用：执行了 `fd -e md` 和 `rg -n -i -C 3` 两个命令
- ⚠️ 审计覆盖不完整：step 2（read SKILL.md fallback）、step 4-7 的 tool 调用前未输出 tool-audit 审计块

本次 evolution 基于验证结果，将机制升级为四层闭环，并修复审计覆盖漏洞。

## 变更内容

### 铁律 1-8 保持有效（evolution v1.2.0 + v1.3.0）

- 铁律 1-5：双向显式声明 + 自检清单 + 高频任务速查表 + EXEC-CHEATSHEET 前置提示
- 铁律 6：全局审计卡点（tool-audit.mdc）
- 铁律 7："是"时必须展示操作对象
- 铁律 8：skill 加载失败时必须 fallback 到磁盘 read

### 新增铁律 9：生效 mdc 列表必须显式列出

在 tool-audit.mdc 自检清单中，必须追加：

```
- 当前已触发的生效 mdc 有哪些？              <列出本次 session 中已识别到的 alwaysApply mdc>
```

目的：防止 Agent 只扫描自己所在的 mdc（如 tool-audit），而遗漏其他 alwaysApply mdc（如 rg-fd-search-priority）。

验证结果：subagent 在验证任务中成功列出：
```
rg-fd-search-priority.mdc（alwaysApply=true，搜索场景命中）
high-frequency-tool-shell-audit.mdc（alwaysApply=true，任何 tool 调用前）
high-frequency-shell-guard-content.mdc（涉及 bash 时隐性命中）
```

### 新增铁律 10：read 纳入审计范围

tool-audit.mdc 的适用范围从 `bash`/`write`/`edit` 扩展到 `read`：

```
| 工具 | 触发条件 |
|------|---------|
| `bash` | 任何 Shell 命令执行 |
| `write` | 新建任何文件 |
| `edit` | 对已有文件进行结构性/流程性变更 |
| `read` | 读取任何文件（尤其是 skill/SKILL.md、env-migration 等上下文文件） |
```

原因：subagent 验证中，step 2（read SKILL.md）和 step 5（read 4 个文件）前均没有输出审计块，因为 read 不在当前审计范围内。

### 新增铁律 11：每次 tool 调用必须独立审计

禁止以"这是上一步的延续"为由跳过审计。

具体规则：
- fallback read 不是 skill 加载的子步骤，是独立的 read tool 调用
- rg/fd 搜索优先级审计不能替代 tool-audit 审计
- 即使前一步已输出审计块，下一步 tool 调用前必须重新输出

subagent 验证中的反例：
```
step 1: skill → 有 tool-audit 审计块 ✅
step 2: read SKILL.md → 无 tool-audit 审计块 ❌（Agent 认为是 step 1 的延续）
step 3: bash fd → 有 rg/fd 审计块 ✅（但这是 SKILL.md 的审计，不是 tool-audit）
step 4: bash rg → 无审计块 ❌
```

## 影响范围

- `high-frequency-tool-shell-audit.mdc`：追加生效 mdc 列表项 + read 纳入审计范围 + 每次 tool 调用独立审计铁律
- `rg-fd-search-priority.mdc`：同步更新配套 skill 关联声明
- SED 增量：gotcha（fallback read 遗漏审计块）、evolution（本文件）、learning（生效 mdc 列表模式）

## 验证结果

| 验证项 | 结果 | 证据 |
|--------|------|------|
| 生效 mdc 列表项 | ✅ 通过 | subagent 列出 3 个 alwaysApply mdc |
| skill 正确定位 | ✅ 通过 | fallback_target: `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md` |
| rg/fd 真实调用 | ✅ 通过 | `fd -e md` + `rg -n -i -C 3` 命令原文 |
| 审计全覆盖 | ⚠️ 部分通过 | step 1 和 step 3 有审计块，step 2/4/5/6/7 遗漏 |

## 与现有规则的衔接

- evolution v1.2.0 和 v1.3.0 的铁律 1-8 继续有效
- 本 evolution 是追加，不是替换
- 铁律 10 涉及 read 工具，需与 `rg-fd-search-priority.mdc` 的适用范围对齐

## 验收标准

下次搜索类任务执行时，Agent 必须输出：
1. tool-audit 审计块（含生效 mdc 列表 + 配套 skill 检查）
2. skill 加载确认 或 fallback 到磁盘 read 的确认
3. **每次** tool 调用（skill/read/bash/write）前均输出审计块
4. 搜索执行（使用 rg/fd，遵循 P0-P3）

若 step 2（read SKILL.md）前缺少审计块，视为铁律 11 违规。
