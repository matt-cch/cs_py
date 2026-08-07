---
title: mdc-skill 强关联从"无效双向声明"到"有效四层闭环"的演进
description: 记录本次 session 的核心成果：改造前 mdc 与 skill 的配套关系形同虚设（Agent 声称"没有任何 skill 命中"）；改造后通过 tool-audit.mdc 全局审计卡点，Agent 能正确定位到指定 skill 并 fallback 读取 SKILL.md。验证证据来自 subagent 实战测试。
date: 2026-08-06
type: gotcha
fingerprint:
  content_sha256: "gotcha-mdc-skill-strong-association-evolution-20260806"
  semantic_key: "mdc-skill-strong-association-evolution"
meta: {}
---

# mdc-skill 强关联从"无效双向声明"到"有效四层闭环"的演进

## 现象（改造前）

用户要求"查看 gh 工具链开发工作进度"，Agent 的 mdc（`rg-fd-search-priority.mdc`，alwaysApply: true）已自动触发，Agent 也使用 rg/fd 执行了搜索。

但 Agent 声称：
> "没有任何 skill 命中"

实际上 `rg-fd-search` skill 完全命中（触发词：搜索、查找、进度查询），且 skill 文件存在于磁盘：`references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md`。

**核心问题**：mdc 和 skill 之间没有不可绕过的关联机制。Agent 读 mdc 时不知道有配套 skill，搜索行为与 skill 定义一致但完全错过了 skill 上下文。

## 第一次尝试（双向声明）

在 mdc 和 SKILL.md 中互相声明配套关系：
- mdc frontmatter 增加 `paired_skill: "rg-fd-search"`
- mdc 正文顶部增加"配套 Skill（必须加载）"声明
- SKILL.md 增加配套 mdc 声明

**结果**：仍然无效。用户直接指出：
> "改 SKILL.md 有鬼用啊，都没有触发"

**根因**：双向声明本质上是"死后验尸"——只有 Agent **同时读取两者**时才有效。但 skill 不在 `<available_skills>` 列表中，Agent 根本不会去读。单向声明变成"只有一半生效"（mdc 可见，skill 不可见）。

## 第二次尝试（三层闭环）

引入第三个独立层级（全局审计卡点）：
- 在 `high-frequency-tool-shell-audit.mdc`（alwaysApply）中追加配套 skill 检查项
- 每次 tool 调用前强制检查：当前 mdc 是否有配套 skill？配套 skill 是否已加载？

**结果**：审计卡点生效了，但存在两个漏洞：
1. Agent 的审计输出中"是"时没有展示具体操作对象（不可验证）
2. Agent 只检查了自己所在的 mdc，没检查其他 alwaysApply mdc

## 第三次尝试（四层闭环）

在三层闭环基础上追加：
- **铁律 7**："是"时必须展示操作对象（如 `是 → rg-fd-search`）
- **铁律 9**：生效 mdc 列表必须显式列出（防止只检查 tool-audit 自己）
- **铁律 10**：read 纳入审计范围
- **铁律 11**：每次 tool 调用必须独立审计

## 验证结果（改造后）

subagent 执行搜索任务时的实际轨迹：

```
step 1: 【Tool 调用规则层审计】
        - 当前已触发的生效 mdc 有哪些？
          → rg-fd-search-priority.mdc（alwaysApply=true）
          → high-frequency-tool-shell-audit.mdc（alwaysApply=true）
        - 当前 mdc 是否有配套 skill？
          → 是 → rg-fd-search
        - 配套 skill 是否已加载？
          → 否 → 立即加载

step 2: skill 工具加载失败 → fallback 到磁盘 read
        read: references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md

step 3: 【rg/fd 搜索优先级审计】（SKILL.md 定义的模板）
        - P0 树状自说明是否命中？ 否
        - P1 JSON 索引是否命中？   否
        - P2 docstring 是否命中？  否
        - P3 关键词搜索是否必要？  是
        - 配套 skill rg-fd-search 是否已加载？ 是（已通过磁盘 read 加载）

step 4: bash(fd) → 列出文件
        bash(rg) → 搜索内容
```

**关键验证点**：
| 检查项 | 改造前 | 改造后 |
|--------|--------|--------|
| 识别到 rg-fd-search-priority.mdc 已触发 | ❌ 无 | ✅ 列出生效 mdc |
| 检测到配套 skill rg-fd-search | ❌ 声称"无 skill 命中" | ✅ 明确写出 skill 名称 |
| fallback 到正确 SKILL.md | ❌ 未发生 | ✅ `skills/rg-fd-search/SKILL.md` |
| 按 skill 规范执行 rg/fd | ❌ 用 glob/grep | ✅ `fd -e md` + `rg -n -i -C 3` |

## 核心洞察

**mdc-skill 强关联的关键不是"互相声明"，而是"不可绕过的检查点"。**

- 双向声明：静态文档，Agent 可能看不到其中一方
- 三层闭环：增加了全局审计，但 Agent 可能只审计自己所在的 mdc
- 四层闭环：强制列出所有生效 mdc + 对每个 mdc 检查配套 skill + "是"时展示操作对象 + fallback 到磁盘 read

只有当 Agent **无法在不检查的情况下继续执行**时，配套关联才真正生效。

## 反模式

1. **以为双向声明就等于闭环**：没有全局审计卡点时，双向声明只是静态文档
2. **只在 SKILL.md 改声明**：skill 没被加载时，修改对 Agent 不可见
3. **只在 mdc 自检清单加检查项**：Agent 可能跳过自检直接执行
4. **"是"时不写具体操作对象**：无法验证是否真执行了
5. **skill 加载失败就放弃**：不尝试 fallback 到磁盘 read

## 关联演进

- evolution v1.2.0：建立双向显式声明（铁律 1-5）
- evolution v1.3.0：升级为三层闭环（铁律 6-8）
- evolution v1.4.0：升级为四层闭环（铁律 9-11），验证通过
