---
title: session-tracer.ts SDK 契约适配修复
description: 重启后验证 session-tracer plugin 时发现 SDK ToolResult 类型不匹配，修复三处返回值以适配 OpenCode SDK 契约（output 字段必填），并通过 lint 验证。
date: 2026-08-10
meta:
  version: 1.0.0
  tags: [opencode, plugin, session-tracer, sdk-compatibility, env-migration]
---

# env-migration-session-tracer-sdk-compatibility-fix-2026-08-10-164345

> **Session 主题**：session-tracer.ts SDK 契约适配修复
> **日期**：2026-08-10（文件名时间戳：2026-08-10-164345）
> **触发原因**：用户要求查看最新 env-migration 并测试 session_tracer tool
> **影响范围**：`venv/.opencode/plugin/session-tracer.ts`
> **风险等级**：低（plugin 源码修复，无运行时副作用；修复后须 `/new` 重新加载生效）


## 一、文本文件变更清单

### 1. 修改 `venv/.opencode/plugin/session-tracer.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/session-tracer.ts` |
| **变更类型** | `修改` |
| **作用** | 修复 ToolResult 返回值与 OpenCode SDK 契约不匹配的问题 |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过（BOM=no, CRLF=0, LF=230） |
| **当前状态** | ⚠️ **尚未生效**。plugin 在 session 启动时扫描加载，当前 session 无法热重载。 |
| **迁移方式** | 直接复制 `session-tracer.ts` 到新环境 `venv/.opencode/plugin/`，重启 session |

**变更详情**：

SDK 真源 `tool.d.ts` 定义 `ToolResult` 为：

```typescript
string | {
    title?: string;
    output: string;      // ← 必填字段
    metadata?: { [key: string]: any; };
    attachments?: ToolAttachment[];
}
```

原 `session-tracer.ts` 三处 `return` 均直接返回自定义 `ToolResult<T>` 结构（`{ success, data, meta, summary }`），**缺少 `output` 字段**，导致 SDK 内部处理返回值时访问 `result.output.split(...)` 得到 `undefined`，抛出 `undefined is not an object (evaluating 'c.split')`。

修复方式：在三处 `return` 外层包裹 **SDK 兼容壳**，将自定义结构完整内嵌到 `metadata.tool_result` 中：

| 返回路径 | 修改前 | 修改后 |
|---------|--------|--------|
| `parse_input` 失败 | `return err(...)` | `const parseErr = err(...); return { title: "Payload Parse Error", output: parseErr.summary, metadata: { tool_result: parseErr } }` |
| `write_jsonl` 失败 | `return err(...)` | `const ioErr = err(...); return { title: "Trace Write Error", output: ioErr.summary, metadata: { tool_result: ioErr } }` |
| 成功路径 | `return ok(...)` | `const result = ok(...); return { title: "Recorded ...", output: result.summary, metadata: { tool_result: result } }` |

**设计意图**：外层遵守 SDK 契约（`output` 供 OpenCode 渲染），内层保留完整分层 schema（`metadata.tool_result` 供下游代码解析）。


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。


## 三、Session 踩坑与纠偏记录

### 3.1 glob 按名称排序踩坑（第二次重复）

**现象**：用户要求"查看最新的 env-migration"，Agent 使用 `glob "references/env-migrations/env-migration-*.md"` 查找，按文件名排序返回字母顺序结果，误读了 14:17 的旧文件，忽略了 16:27 的最新文件。

**根因**：`glob` 默认按文件名排序，env-migration 文件名虽含时间戳，但按名称排序在跨时段或格式不一致时会失效。此坑已在 `env-migration-opencode-plugin-tool-schema-architecture-2026-08-10-162736.md` 的 3.1 节记录并纠正。

**修复**：改用 `Get-ChildItem | Sort-Object LastWriteTime -Descending` 按实际修改时间排序。

**纠偏**：用户直接指出"你就不想想我现在已经是重启后的状态"，打断 Agent 的惯性假设（旧 session 未加载 plugin）。Agent 随后意识到当前 session 确实是重启后的新 session，`session_tracer` 已在工具列表中，可以直接调用测试。

### 3.2 SDK ToolResult 契约不匹配

**现象**：调用 `session_tracer` 后报错 `undefined is not an object (evaluating 'c.split')`。Agent 最初怀疑 `payload` 类型不匹配或 `import.meta.dirname` 为 `undefined`。

**根因**：OpenCode SDK 要求 tool 返回值必须含 `output: string` 字段。我们的 `ok()` / `err()` 工厂函数返回的是自定义 `{ success, data, meta, summary }` 结构，SDK 内部处理时访问 `result.output` 得到 `undefined`。

**修复**：读取 SDK 真源 `venv/.opencode/node_modules/@opencode-ai/plugin/dist/tool.d.ts`，确认 `ToolResult` 类型定义，然后在 `session-tracer.ts` 三处 `return` 加兼容壳。

**验证**：最小化测试（不传 payload）与完整测试（传 payload）均复现同一错误，排除参数类型问题，锁定根因。


## 四、落盘验证

| 文件/目录 | 验证工具 | 结果 |
|-----------|---------|------|
| `session-tracer.ts` | `run-lint.py --profile lint-encoding` | ✅ 通过（BOM=no, CRLF=0, LF=230） |


## 五、验证清单（重启后必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 发送 `/new` 重启 session | `/new` 或重新打开窗口 | — |
| 2 | 调用 session_tracer 记录测试事件 | 发送 prompt："调用 session_tracer 记录一个测试事件" | Tool 被调用，返回成功，不再报 `undefined is not an object` |
| 3 | 检查 JSONL 文件 | `Test-Path "venv/tmp/session-trace.jsonl"` | `True` |
| 4 | 检查 manifest 文件 | `Test-Path "venv/tmp/session-tracer-manifest-*.json"` | `True` |
| 5 | 验证 ToolResult 返回结构 | 查看返回结果 | 含 `title`、`output`、`metadata.tool_result` |
| 6 | 验证 metadata.tool_result 完整性 | 读取返回的 `metadata.tool_result` | 含 `success`、`data`、`meta`、`summary` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复旧版本 | 从 git history 恢复 `session-tracer.ts` 的旧版本（未加 SDK 兼容壳前） |
| 重启 session | `/new` 或重新打开窗口 |


## 七、关联文档

| 文档 | 说明 |
|------|------|
| `references/env-migrations/env-migration-session-tracer-plugin-and-subagent-validation-2026-08-10-141741.md` | session-tracer 初始开发与 subagent 验证失败 |
| `references/env-migrations/env-migration-opencode-plugin-tool-schema-architecture-2026-08-10-162736.md` | 五层 schema 架构建设（含 glob 排序踩坑记录） |
| `venv/.opencode/node_modules/@opencode-ai/plugin/dist/tool.d.ts` | SDK ToolResult 类型真源 |
| `venv/.opencode/plugin/tool-schemas/tool-result.ts` | 自定义 ToolResult<T> 分层 schema |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-10-164345 |
| **更新人** | OpenCode Agent Session |
| **变更触发** | 用户要求查看最新 env-migration + 测试 session_tracer + 修复 SDK 契约不匹配 |
| **下次修订条件** | `/new` 验证 session_tracer 可用性后，补充实测结果 |
| **跨环境迁移参考** | 复制 `session-tracer.ts` + 按「验证清单」逐条执行 |


*文档生成时间：2026-08-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
