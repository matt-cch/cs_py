---
title: env-migration — Markdown 格式规则强化 + OpenCode Plugin 实验 + Shell 长内容禁令
description: 新建 shell-long-content-ban.mdc、markdown-docs-format.mdc 补充、新建 md-format-guard.ts plugin、清理正文 --- 分隔线、新建 repo-metadata-practices.md
---

# `env-migration-md-format-plugin-and-shell-ban-2026-06-05-141555.md`

> **文档性质**：环境迁移指南。聚焦 Agent 指令体系（.mdc）、OpenCode Plugin 实验、文档格式铁律修复。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Markdown 格式规则强化 + OpenCode Plugin 实验 + Shell 长内容禁令 |
| **日期** | 2026-06-05 |
| **文件名时间戳** | `2026-06-05-141555` |
| **触发原因** | 1) 验证 `.mdc` 高频任务触发效果时发现 `---` 分隔线违规；2) 探索 OpenCode `tool.execute.before` plugin 机制实现写 .md 前自动检查；3) 总结 `python -c` / Shell 拼接长文本的系统性禁令 |
| **影响范围** | `.cursor/rules/*.mdc`、`venv/.opencode/plugin/`、`docs/architecture/*.md` |
| **风险等级** | 低（指令级调整，不涉及业务代码或运行时工具链） |

## 一、文本文件变更清单

### 1. 新建 `.cursor/rules/shell-long-content-ban.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/shell-long-content-ban.mdc` |
| **变更类型** | `新建` |
| **作用** | 项目级硬性禁令：禁止在 Shell 命令行参数中拼接长字符串、整段脚本正文、JSON/HTML 等多行内容 |
| **内容要点** | 一句话铁律「正文落盘用 write，Shell 只执行短命令」；禁止行为清单（超长命令行参数、`python -c`、Shell 写中间产物）；允许行为（仅短命令）；标准三步流程；附节：`.ps1` 文件 BOM 重复陷阱（已踩坑记录） |
| **验证方式** | `Test-Path -LiteralPath ".cursor/rules/shell-long-content-ban.mdc"` 返回 `True` |
| **迁移方式** | 直接复制文件到新环境同名路径 |

### 2. 修改 `.cursor/rules/markdown-docs-format.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/markdown-docs-format.mdc` |
| **变更类型** | `修改` |
| **新增内容 1** | 1.2 节追加条款：「正文中严禁使用 `---` 水平分隔线」，唯一例外为代码块内的 frontmatter 示例及 `SKILL.md`/`AGENTS.md` 等元文档 |
| **新增内容 2** | 1.4 节「落盘后换行符验证（`.md` / `.mdc` 强制）」：提供 PowerShell 字节流检查命令模板，确认 `CRLF=0` |
| **作用** | 把本次踩坑教训（正文 `---` 导致解析异常、CRLF 污染）固化为可执行规则 |
| **验证方式** | 读取文件确认第 35 行附近有「正文中严禁使用 `---`」；第 45 行附近有换行符验证命令 |
| **迁移方式** | 直接覆盖或 `edit` 最小化修改 |

### 3. 新建 `venv/.opencode/plugin/md-format-guard.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/md-format-guard.ts` |
| **变更类型** | `新建` |
| **作用** | 实验性 OpenCode Plugin，注册 `tool.execute.before` hook，拦截 `write`/`edit` 对 `.md`/`.mdc` 文件的调用并记录日志 |
| **当前功能** | 检测工具名 + 文件扩展名 → 写入 `hook-log.jsonl`（JSON Lines 格式，每行一个触发记录） |
| **待扩展** | 读取 `output.args.content` 检测正文 `---`、CRLF 等格式违规 |
| **生效条件** | **必须重启 OpenCode**（plugin 在启动时扫描加载，运行中 session 不热重载） |
| **验证方式** | 1. 重启 OpenCode；2. 执行一次 `write` 或 `edit` 写入 `.md` 文件；3. 检查同目录 `hook-log.jsonl` 是否出现新行；4. 或查看启动日志是否有 `[md-format-guard] Plugin loaded` |
| **迁移方式** | 直接复制 `md-format-guard.ts` 到新环境 `venv/.opencode/plugin/`，重启 OpenCode |

### 4. 新建 `docs/architecture/repo-metadata-practices.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/architecture/repo-metadata-practices.md` |
| **变更类型** | `新建` |
| **内容来源** | 基于 `engineering-metadata-and-docs-practices.md` 原始内容重写（因原文件被覆盖后格式异常，用户要求新建干净文件） |
| **新增内容** | 2.1 节「已验证实践：高频任务触发映射宜下沉到 `.mdc`」——记录 `verify-runtime` 从 AGENTS.md 迁移到 `.mdc` 的验证结论 |
| **作用** | 长期可复用的经验沉淀文档，非一次性交接单 |
| **验证方式** | `Test-Path` 确认存在；读取确认无正文 `---`、换行符为 LF |
| **迁移方式** | 直接复制 |

### 5. 修改 `docs/architecture/engineering-metadata-and-docs-practices.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/architecture/engineering-metadata-and-docs-practices.md` |
| **变更类型** | `修复` |
| **修复内容 1** | 回滚误加的表格修改（恢复了 `.cursor/rules` 列的原始描述）和 2.1 节（已删除） |
| **修复内容 2** | 清理正文中的所有 `---` 水平分隔线（原 10 处 → 仅保留 frontmatter 的 2 处） |
| **修复内容 3** | 换行符从 CRLF 修复为 LF |
| **作用** | 恢复原文件的干净状态，消除之前误操作引入的格式异常 |
| **验证方式** | `grep "^---$"` 仅命中第 1、5 行；字节流检查 `CRLF=0` |
| **迁移方式** | 若新环境原文件正常，可跳过；若同样被污染，参照 `repo-metadata-practices.md` 重建 |

### 6. 修改 `docs/architecture/agent-execution-isolation.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/architecture/agent-execution-isolation.md` |
| **变更类型** | `修复` |
| **修复内容** | 清理正文中的所有 `---` 水平分隔线（原 10 处 → 仅保留 frontmatter 的 2 处） |
| **作用** | 消除 `---` 导致的 Markdown 解析异常 |
| **验证方式** | `grep "^---$"` 仅命中第 1、6 行 |
| **迁移方式** | 直接覆盖或逐条 edit |

### 7. 修改 `references/env-migrations/env-migration-verify-runtime-trigger-migration-2026-06-05-094059.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/env-migrations/env-migration-verify-runtime-trigger-migration-2026-06-05-094059.md` |
| **变更类型** | `修正` |
| **删除内容** | 第 93-113 行「六、验证结果（已回填）」整节（验证结论不应放在一次性交接单中） |
| **恢复后状态** | 恢复为纯交接文件，验证结论已迁移至 `docs/architecture/repo-metadata-practices.md` 2.1 节 |
| **作用** | 纠正 env-migration 与长期经验沉淀文档的职责边界混淆 |
| **验证方式** | 读取文件确认已无「验证结果」章节 |
| **迁移方式** | 无需迁移，属于对既有文件的修正 |

## 二、非文本操作

本次 session **不涉及**文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。唯一涉及的目录创建是 `venv/.opencode/plugin/`（已随 `md-format-guard.ts` 新建自动生成）。

## 三、环境变量速查

无新增或变更的环境变量。OpenCode 的 `config.json` 的 `instructions` 字段已包含 `.cursor/rules/*.mdc`，无需修改即可自动加载新规则文件：

```json
"instructions": [
  "./AGENTS.md",
  ".cursor/rules/*.md",
  ".cursor/rules/*.mdc"
]
```

Plugin 采用 auto-discovery 模式：
- `venv/.opencode/plugin/*.ts` 或 `*.js` 会在 OpenCode 启动时自动扫描加载
- **不需要**在 `config.json` 的 `plugin` 数组中显式注册
- 修改 plugin 文件后，**必须退出并重启 OpenCode** 才能生效

## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 `shell-long-content-ban.mdc` 存在 | `Test-Path ".cursor/rules/shell-long-content-ban.mdc"` | `True` |
| 2 | 确认 `markdown-docs-format.mdc` 已更新 | 读取文件搜索「正文中严禁使用 `---`」和「落盘后换行符验证」 | 均存在 |
| 3 | 确认 `md-format-guard.ts` 存在 | `Test-Path "venv/.opencode/plugin/md-format-guard.ts"` | `True` |
| 4 | 确认 plugin 被加载 | 重启 OpenCode，查看启动日志或检查 `venv/.opencode/plugin/hook-log.jsonl` 是否被创建 | 日志中出现 `[md-format-guard] Plugin loaded` 或 `hook-log.jsonl` 存在 |
| 5 | 确认 plugin hook 触发 | 重启后执行一次 `write` 写入任意 `.md` 文件，检查 `hook-log.jsonl` | 文件末尾出现新 JSON 行，含 `"tool":"write"`、`"filePath":"..."` |
| 6 | 确认 `repo-metadata-practices.md` 存在 | `Test-Path "docs/architecture/repo-metadata-practices.md"` | `True` |
| 7 | 确认 `engineering-metadata-and-docs-practices.md` 无 `---` 污染 | `powershell: (Get-Content "docs/architecture/engineering-metadata-and-docs-practices.md" | Select-String "^---$").Count` | `2`（仅 frontmatter） |
| 8 | 确认 `agent-execution-isolation.md` 无 `---` 污染 | `powershell: (Get-Content "docs/architecture/agent-execution-isolation.md" | Select-String "^---$").Count` | `2`（仅 frontmatter） |
| 9 | 确认所有 `.md` / `.mdc` 为 LF | 对涉及文件执行字节流检查（见 `markdown-docs-format.mdc` 1.4 节命令） | `CRLF=0` |

## 五、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 移除 `shell-long-content-ban.mdc` | `Remove-Item ".cursor/rules/shell-long-content-ban.mdc"` |
| 恢复 `markdown-docs-format.mdc` | 从 git 历史恢复或手动删除新增的两个条款 |
| 移除 `md-format-guard.ts` | `Remove-Item "venv/.opencode/plugin/md-format-guard.ts"`；同时删除 `hook-log.jsonl` |
| 移除 `repo-metadata-practices.md` | `Remove-Item "docs/architecture/repo-metadata-practices.md"` |
| 恢复 `engineering-metadata-and-docs-practices.md` | 从 git 历史恢复或参照原始内容重建 |
| 重启 OpenCode | 必须重启以卸载已移除的 plugin |

## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-05-141555 |
| **更新人** | Agent Session |
| **变更触发** | `.mdc` 触发验证成功 + `---` 分隔线格式违规踩坑 + OpenCode Plugin hook 机制调研 |
| **下次修订条件** | 1) `md-format-guard.ts` 扩展为实际检查逻辑后更新；2) 新增 `.mdc` 规则文件时同步 |
| **跨环境迁移参考** | 直接复制 `shell-long-content-ban.mdc`、`md-format-guard.ts`、`repo-metadata-practices.md` + 按「验证清单」逐条执行 |
