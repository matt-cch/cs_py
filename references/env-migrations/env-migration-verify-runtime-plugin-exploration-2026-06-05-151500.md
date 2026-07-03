---
title: env-migration — 真源实测更新 + OpenCode Plugin Hook 机制深度验证与功能探索
description: 记录从 tree-sitter 脉络延续下来的 session：真源实测更新、md-format-guard.ts plugin 验证误判复盘、tool.execute.before 已知 bug 发现、client.session.prompt 注入上下文探索。
date: 2026-06-05
---

# env-migration-verify-runtime-plugin-exploration-2026-06-05-151500.md

> **文档性质**：环境迁移指南。聚焦真源检测更新、OpenCode Plugin 验证机制深度探讨、Hook 能力边界实测。
> **脉络说明**：本次 session 从 env-migration-tree-sitter-article-pipeline-2026-06-04-175042.md 延续而来——在 tree-sitter 知识体系梳理后，需要保持项目工具链真源的实时性，同时探索 OpenCode Plugin 作为自动化检查机制的可行性。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 真源实测更新 + md-format-guard.ts Plugin 验证 + tool.execute.before Hook 能力边界探索 |
| **日期** | 2026-06-05 |
| **文件名时间戳** | 2026-06-05-151500 |
| **触发原因** | 1) 用户要求更新真源实测（OpenCode CLI 升级后）；2) 用户质疑 Agent 在验证 plugin 时轻率下错误结论；3) 探索 plugin 如何让 Agent 自动记得读取 Markdown 格式规则 |
| **影响范围** | references/runtime/、venv/.opencode/plugin/、docs/tooling/opencode/ |
| **风险等级** | 低（文档与插件验证，不涉及业务代码） |
| **前置脉络** | env-migration-tree-sitter-article-pipeline-2026-06-04-175042.md 工具链真源维护意识延续 |


## 一、文本文件变更清单

### 1. 更新 references/runtime/verified-runtime-index.json

| 属性 | 值 |
|------|-----|
| **路径** | references/runtime/verified-runtime-index.json |
| **变更类型** | 修改（真源快照更新） |
| **修改内容** | meta.last_updated 2026-06-05T14:49:20；toolchain.opencode_cli.version 1.16.0；canonical_sources.opencode.verified_version v1.16.0；GitHub 连通性 latency 数据刷新 |
| **作用** | 保持真源索引与最新实测一致，为后续 Agent 引用提供准确路径/版本信息 |
| **验证方式** | 执行 opencode debug info 确认 version 显示 1.16.0 |
| **迁移方式** | 直接运行 references/runtime/verify-runtime.ps1，根据报告自动更新 |

### 2. 新建 docs/tooling/opencode/local-plugin-creation-guide.md

| 属性 | 值 |
|------|-----|
| **路径** | docs/tooling/opencode/local-plugin-creation-guide.md |
| **变更类型** | 新建 |
| **作用** | 本地单文件 Plugin 创建与验证的完整操作手册，涵盖类型定义依据、Hook 签名、生效条件、验证方法 |
| **验证方式** | Test-Path docs/tooling/opencode/local-plugin-creation-guide.md 返回 True |
| **迁移方式** | 直接复制 |

### 3. 新建 docs/tooling/opencode/local-plugin-verification-retrospective.md

| 属性 | 值 |
|------|-----|
| **路径** | docs/tooling/opencode/local-plugin-verification-retrospective.md |
| **变更类型** | 新建 |
| **作用** | 记录 Agent 在验证 plugin 时因忽视真实日志、臆测条件、未检查过滤逻辑而导致的完整误判链 |
| **验证方式** | Test-Path docs/tooling/opencode/local-plugin-verification-retrospective.md 返回 True |
| **迁移方式** | 直接复制 |

### 4. 修改 docs/tooling/opencode/README.md

| 属性 | 值 |
|------|-----|
| **路径** | docs/tooling/opencode/README.md |
| **变更类型** | 修改 |
| **新增内容** | 在导航表中追加 local-plugin-creation-guide.md 和 local-plugin-verification-retrospective.md 两行 |
| **验证方式** | 读取文件确认两行链接存在 |
| **迁移方式** | edit 最小化修改 |

### 5. 修改 venv/.opencode/plugin/md-format-guard.ts

| 属性 | 值 |
|------|-----|
| **路径** | venv/.opencode/plugin/md-format-guard.ts |
| **变更类型** | 修改 |
| **修改内容** | 注释掉两处 console.log（初始化加载日志 + Hook 触发日志），仅保留 hook-log.jsonl 静默记录 |
| **原因** | console.log 输出会回流到 Agent Chat UI，造成干扰；hook-log.jsonl 已足够实证 |
| **验证方式** | 读取文件确认 console.log 已被注释；执行 edit 写入 .md 文件后检查 hook-log.jsonl 是否追加 |
| **迁移方式** | 直接复制文件 + 重启 OpenCode |


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建。唯一操作是 OpenCode CLI 升级（已在 env-migration-opencode-cli-upgrade-2026-06-05-142431.md 中记录）。


## 三、环境变量速查

无新增或变更的环境变量。

Plugin 采用 auto-discovery 模式，venv/.opencode/plugin/*.ts 在 OpenCode 启动时自动扫描加载，不需要在 config.json 的 plugin 数组中显式注册。


## 四、关键发现与技术讨论（供下次 session 接续）

### 4.1 真源实测结果

| 指标 | 数值 |
|------|------|
| 总计 | 26 |
| 通过 | 24 |
| 失败 | 2（Cursor 候选路径不存在，属已知非关键项） |
| 已变更 | 5（opencode_cli.version 1.15.13 1.16.0；GitHub API latency 刷新） |

### 4.2 Plugin 验证中的关键教训

1. **日志是最高优先级证据**。启动日志中 service=plugin path=... loading plugin 明确加载时，不得以任何臆测推翻。
2. **没记录不等于没加载**。必须先看源码过滤条件（md-format-guard.ts 第 36行），再下结论。
3. **验证顺序强制 checklist**（5步）：检查过滤条件 确认 plugin 被加载 确认初始化执行 确认 Hook 触发 确认非目标文件不触发。

### 4.3 tool.execute.before 的已知限制（GitHub Issue #26910）

| 限制 | 说明 |
|------|------|
| output.args 修改有 bug | 官方 issue 确认：修改 output.args 后，工具实际执行时不采纳修改后的值 |
| throw new Error() 可靠 | 抛错可以阻断工具执行，这是当前唯一可靠的拦截方式 |
| 无法反向驱动 Agent | Hook 不能发起新的工具调用，不能让 Agent 暂停当前操作去 read 规则 |

### 4.4 client.session.prompt({ noReply: true }) 的发现

SDK 文档确认 client.session.prompt({ path: { id }, body: { noReply: true, parts: [...] } }) 可向 session 注入上下文消息，不触发 AI 响应。

**但未解决的核心问题**：tool.execute.before 触发时 LLM 已生成 edit 调用，注入消息只能在下一次推理时被看到，无法中断当前操作。

### 4.5 三个可行解法（待下次 session 决策）

| 解法 | 机制 | 靠谱度 |
|------|------|--------|
| **Plugin 自己读规则自己检查** | 在 Hook 中读取 markdown-docs-format.mdc，对 output.args.content 执行格式检查，违规则 throw | 最靠谱 |
| **阻断 + 注入提示** | throw 阻断当前 edit，同时注入规则提醒到 session | 体验不流畅 |
| **System Prompt 全局注入** | 在 AGENTS.md / .mdc 中写死铁律 | 容易遗忘 |

**下次 session 的待办**：决策采用哪个解法，并将检查逻辑写进 md-format-guard.ts。


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认真源索引已更新 | Get-Content references/runtime/verified-runtime-index.json 搜索 1.16.0 | 命中 opencode_cli.version 行 |
| 2 | 确认 plugin 创建指南存在 | Test-Path docs/tooling/opencode/local-plugin-creation-guide.md | True |
| 3 | 确认验证复盘存在 | Test-Path docs/tooling/opencode/local-plugin-verification-retrospective.md | True |
| 4 | 确认 plugin 源码中 console.log 已注释 | Select-String -Path venv/.opencode/plugin/md-format-guard.ts -Pattern console.log | 无命中 |
| 5 | 确认 plugin 仍正常加载 | opencode debug info | plugins 列表中出现 md-format-guard.ts |
| 6 | 确认 Hook 仍静默记录 | 执行一次 edit 写入 .md 文件，检查 hook-log.jsonl | 末尾出现新 JSON 行 |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 console.log | 取消 md-format-guard.ts 中两处注释 |
| 删除新文档 | Remove-Item docs/tooling/opencode/local-plugin-creation-guide.md、local-plugin-verification-retrospective.md |
| 恢复 README 导航 | 从 git 历史恢复 docs/tooling/opencode/README.md |
| 真源索引回滚 | 从 git 历史恢复 references/runtime/verified-runtime-index.json |
| 重启 OpenCode | 必须重启以应用 plugin 变更 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-05-151500 |
| **更新人** | Agent Session |
| **变更触发** | 用户要求更新真源实测 + 用户严厉批评验证不严谨 + 联网搜索 OpenCode Plugin 机制 |
| **下次修订条件** | 1) 决策 md-format-guard.ts 检查逻辑实现方案后更新；2) tool.execute.before bug 修复后更新限制说明 |
| **跨环境迁移参考** | 直接复制相关文件 + 按验证清单逐条执行 |
| **前置脉络** | env-migration-tree-sitter-article-pipeline-2026-06-04-175042.md |


*文档生成时间：2026-06-05*  
*模板版本：env-migration-template v2*
