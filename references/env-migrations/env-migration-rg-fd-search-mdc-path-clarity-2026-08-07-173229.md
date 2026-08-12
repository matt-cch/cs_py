---
title: env-migration — rg-fd-search-priority.mdc 强化 skill 绝对路径提示
description: 本次 session 因 Agent 臆想 system prompt 默认 skill 路径（.agents/skills/）而找错文件，暴露 mdc 路径提示不够清晰的问题。通过 3 处改造将 skill 绝对路径明确为 ${devroot}/references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md，消除歧义。
date: 2026-08-07
meta:
  version: "1.0.0"
  tags: [rg-fd-search, mdc, skill-path, anti-hallucination, path-clarity]
---

# env-migration — rg-fd-search-priority.mdc 强化 skill 绝对路径提示

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | rg-fd-search-priority.mdc 路径提示改造：消除 skill 位置歧义 |
| **日期** | 2026-08-07 |
| **文件名时间戳** | `2026-08-07-173229` |
| **触发原因** | 用户要求查看今天工作进度，Agent 执行 rg-fd-search 任务时凭记忆臆想 skill 默认路径 `.agents/skills/`，实际在 `references/tasks/deploy-git-isolated/skills/`，导致找错文件。用户指出 mdc 明示力度不足，要求改造。 |
| **影响范围** | `.cursor/rules/rg-fd-search-priority.mdc` |
| **风险等级** | 低（纯文档提示强化，无代码逻辑变更） |

## 一、文本文件变更清单

### 1. 修改 `.cursor/rules/rg-fd-search-priority.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/rg-fd-search-priority.mdc` |
| **变更类型** | 修改 |
| **作用** | 消除 skill 路径歧义，防止 Agent 凭 system prompt 默认路径臆想 |

#### 改造点 1：frontmatter `paired_skill_path`

| 项 | 改造前 | 改造后 |
|----|--------|--------|
| `paired_skill_path` | `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md` | **`${devroot}/references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md`** |

**原因**：去掉占位符歧义，直接给出可拼接的绝对路径模板。

#### 改造点 2：顶部配套 skill 说明块

| 项 | 改造前 | 改造后 |
|----|--------|--------|
| 说明方式 | 一句话带过 "skill 文件位于..." | **新增醒目块**：<br>`skill 磁盘绝对路径（唯一真源）`<br>`禁止凭记忆臆想默认路径`<br>`skill 工具加载失败时必须直接 read 上述绝对路径` |

**新增内容原文**：

```markdown
> **skill 磁盘绝对路径（唯一真源）**：`${devroot}/references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md`
> - **禁止凭记忆臆想默认路径**：system prompt 中可能存在 `.agents/skills/` 等默认路径提示，但本 mdc 配套的 skill **不在默认位置**。
> - **skill 工具加载失败时**：禁止假设 skill 在 `.agents/skills/` 或 `.opencode/skills/` 下，必须直接 `read` 上述绝对路径。
```

#### 改造点 3：第5节强制自检清单

| 项 | 改造前 | 改造后 |
|----|--------|--------|
| skill 加载检查项 | `若否，立即 read SKILL.md（skill 工具不可用时直接 read 磁盘文件）` | **`若是：确认 skill 路径 ${devroot}/references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md；若否：立即停止当前路径，先加载 skill，加载失败则直接 read 上述绝对路径`** |

## 二、非文本操作

| 操作类型 | 说明 |
|---------|------|
| 无 | 本次 session 仅涉及 `.mdc` 文本修改，无文件系统/缓存/目录操作 |

## 三、Session 踩坑与纠偏记录

| # | 踩坑 | 现象 | 纠偏 |
|---|------|------|------|
| 1 | **Agent 臆想 skill 默认路径** | 用户要求查看工作进度，Agent 需要加载 rg-fd-search skill，但凭 system prompt 中的默认路径提示 `.agents/skills/`，去读取一个不存在的文件 `D:\pjt\cursor\cs_py\.agents\skills\rg-fd-search\SKILL.md`，报错 "File not found" | 用户指出错误后，Agent 用 fd 搜索实际路径，发现 skill 在 `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md` |
| 2 | **mdc 路径提示不够强** | mdc 虽在正文写了 "skill 文件位于 `${devroot}/references/tasks/.../SKILL.md"，但 Agent 被 system prompt 的 `.agents/skills/` 默认路径覆盖，未遵守 mdc 明示 | 用户要求 mdc 必须 unmistakable，用醒目块 + 绝对路径 + 禁止臆想警告，三重锚定 |
| 3 | **未优先执行 tool-audit** | 最初执行时未输出【Tool 调用规则层审计】，直接上 bash + glob | 用户批评后，Agent 补做审计，改道 rg-fd-search skill |

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.mdc` | `run-lint.py --profile lint-md` | frontmatter、正文 --- 污染、编码、换行符 | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, 正文无 --- |

**执行结果**：

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\.cursor\rules\rg-fd-search-priority.mdc" --fix
```

**结论**：✅ 全部通过（总违规项 0 处）。

## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 mdc 中 skill 路径明确 | `rg "references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md" "${devroot}\.cursor\rules\rg-fd-search-priority.mdc"` | 命中 ≥ 3 处 |
| 2 | 确认含 "禁止凭记忆臆想" 警告 | `rg "禁止凭记忆臆想" "${devroot}\.cursor\rules\rg-fd-search-priority.mdc"` | 命中 1 处 |
| 3 | 确认 lint 通过 | `run-lint.py --files rg-fd-search-priority.mdc` | 全部通过 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 mdc | `git checkout .cursor/rules/rg-fd-search-priority.mdc`（恢复改造前版本） |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-07-173229 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求查看工作进度，Agent 找错 skill 路径，暴露 mdc 提示歧义 |
| **下次修订条件** | 当 rg-fd-search skill 迁移目录，或新增配套 skill 需统一路径格式时 |
| **跨环境迁移参考** | 直接复制 mdc 改造点；其他 mdc 若配套 skill 不在默认路径，可复用本模式 |

*文档生成时间：2026-08-07*
*模板版本：env-migration-template.md v2*
