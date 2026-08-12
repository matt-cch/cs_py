---
title: session-tracer event-type 使用场景梳理与 docstring 防呆改造
description: 接续 session-tracer v2.0.0 回归验证，发现 16:53 smoke test 产生的 milestone 事件触发 _parseError（此前 env-migration 遗漏）。梳理全部 event_type 使用场景与 payload 要求，改造 session-tracer.ts docstring 和 payload 校验失败处理逻辑，lint 通过，待 /new 重启验证。
date: 2026-08-10
meta:
  version: 1.0.0
  tags: [opencode, plugin, session-tracer, schema, docstring, env-migration]
---

# env-migration-session-tracer-event-type-docstring-guard-2026-08-10-172609

> **Session 主题**：session-tracer event-type 使用场景梳理与 docstring 防呆改造
> **日期**：2026-08-10（文件名时间戳：2026-08-10-172609）
> **触发原因**：用户要求读取最新 3 个 env-migration 并按进度继续测试 session-tracer
> **影响范围**：`venv/.opencode/plugin/session-tracer.ts`
> **风险等级**：低（plugin 源码已修正，但当前 session 未重载，修复尚未生效）


## 一、文本文件变更清单

### 1. 修改 `venv/.opencode/plugin/session-tracer.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/session-tracer.ts` |
| **变更类型** | 修改 |
| **作用** | ① 重写 `description`，增加 EVENT TYPE USAGE GUIDE；② 重写 `payload` describe，按 event_type 列出必填字段；③ 在 Step 2（build_event）后增加 payload 校验失败当场拦截逻辑 |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过（BOM=no, CRLF=0, LF=288） |
| **当前状态** | 磁盘源码已修改，但 OpenCode 无热重载，当前 session 内存中仍为旧版本 |
| **迁移方式** | 直接复制 `session-tracer.ts` 到新环境 `venv/.opencode/plugin/`，重启 session |

**变更详情**：

#### 改造 1：description 增加 EVENT TYPE USAGE GUIDE

把原来模糊的示例列表改为按使用场景分类的完整指引，包含每种 event_type 的用途和 payload 必填字段。Agent 在 planning 阶段读到 `session_tracer` 的 description 时，就能判断该选哪个 event_type、该传什么 payload。

#### 改造 2：payload describe 增加必填字段清单

按 event_type 逐条列出 payload 的必填字段：
- milestone: {milestone_id: string, description: string}
- todo_start: {todo_id: string, content: string}
- todo_end: {todo_id: string}
- decision: {decision_id: string, rationale: string}
- error: {error_code: string, message: string}
- user_message: {text: string}
- tool_call: {tool_name: string}
- test, think, turn_start, turn_end: flexible

#### 改造 3：payload 校验失败当场拦截

原逻辑：`buildTraceEvent` 返回的 event.payload 若被降级为 `{_raw, _parseError}`，会直接写入 JSONL，调用方事后读文件才发现。

新逻辑：在 `execute` 中 Step 2 之后增加检查——若 `event.payload` 含 `_parseError`，立即：
- `failStep` 标记 step2 失败
- `finalizeManifest` + `writeManifestFile`
- 返回 `Payload Validation Error` ToolResult

效果：Agent 在 tool 返回结果中当场看到错误，可以立即修正，而不是等事后读 JSONL。


## 二、非文本操作

| 操作类型 | 路径 | 说明 |
|---------|------|------|
| JSONL 追加（当前 session） | `venv/tmp/session-trace.jsonl` | 1 条新 TraceEvent（event_type: test，无 parseError） |
| manifest 生成（当前 session） | `venv/tmp/session-tracer-manifest-msg_feae3aab0001fOr1a4qgx1peBr.json` | 回归验证产物，step 4 completed，overall_status completed |


## 三、Session 踩坑与纠偏记录

### 3.1 "历史记录"误称（用户纠偏）

**现象**：读取 JSONL 时发现前两条 event（session `ses_01525edbbffebReBHgduWLSIgT`）含 `_parseError`。我称这是"历史记录"，暗示此前 env-migration 已记录。

**根因**：三份最新 env-migration（16:27、16:43、16:53）均未提及 `_parseError` 或 `milestone.payload` 校验失败。

**纠偏**：用户直接指出"前面几条 env-migration 都没有记录"，我查证后确认事实，承认错误。

### 3.2 milestone event_type 使用场景缺失

**现象**：16:53 smoke test session 调用 `event_type: "milestone"` 时，payload 为 `{"test_phase":"smoke_test","schema_version":"2.0.0"}`，缺少必填字段 `milestone_id` 和 `description`，触发 `_parseError`。

**根因**：
1. `session-tracer.ts` 的 `description` 和 `payload` describe 只给了一个扁平示例列表，没有区分"自由类型"和"结构类型"
2. Agent 看到 `milestone` 和 `test` 并列示例，误以为两者 payload 一样自由
3. `trace-event.ts` 的校验器正确工作，但错误处理是"悄悄降级"而非"当场报错"

**修复**：
1. 在 docstring 中按使用场景分类，明确每种 event_type 的 payload 要求
2. 把"悄悄降级"改为"当场返回错误"，让 Agent 在调用阶段就能发现

### 3.3 改造方案未被用户认可前的推理偏差

**现象**：最初提出改造方案时，用户说"你建议的 1，2 方案我都没法评估，因为我不知道不确定你做这些意图是什么"。

**根因**：我只说"改 description""改 payload describe"，但没有先梳理清楚：现有 event_type 有哪些、各自用在什么场景、当前设计哪里让调用方困惑。

**纠偏**：用户要求"先梳理到底这个 event-type 的通常使用场景需要哪些类型"，我重新按实际代码和调用经验整理了完整表格，再谈改造意图和效果，才获得认可。


## 四、现有 event_type 全梳理（改造前状态）

| 分类 | event_type | 使用场景 | payload 要求 |
|------|-----------|---------|-------------|
| 通常场景 | tool_call | Agent 调用某个 tool 时记录 | {tool_name: string} |
| | user_message | 记录用户发送的原始 prompt | {text: string} |
| | think | 记录 Agent 的思考/推理过程 | string 或 object |
| | turn_start / turn_end | 标记交互轮次开始/结束 | 无严格要求 |
| 待办场景 | todo_start | 标记待办任务开始 | {todo_id, content} |
| | todo_end | 标记待办任务完成 | {todo_id} |
| 决策场景 | decision | 记录关键架构/方案决策 | {decision_id, rationale} |
| 里程碑场景 | milestone | 标记阶段性成果/版本发布 | {milestone_id, description} |
| 错误场景 | error | 记录异常/报错/失败 | {error_code, message} |
| 测试场景 | test / test_subagent_invocation | 回归测试/功能验证 | 无严格要求 |


## 五、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 结果 |
|---------|---------|---------|------|
| `.ts`（session-tracer.ts 修改） | `run-lint.py --profile lint-encoding` | 编码/BOM/换行符 | ✅ 通过（BOM=no, CRLF=0, LF=288） |


## 六、验证清单（重启后必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 发送 `/new` 重启 session | 用户发送 `/new` | OpenCode 重新加载 plugin |
| 2 | 不合规 payload 当场拦截 | 调用 `session_tracer`，`event_type: "milestone"`，`payload: {"test":"fail"}` | 返回 `Payload Validation Error`，JSONL 不追加 |
| 3 | 合规调用仍然正常 | 调用 `session_tracer`，`event_type: "test"`，`payload: {"phase":"regression"}` | 返回 `✅ Recorded test`，JSONL 追加，manifest completed |
| 4 | 检查 manifest step 2 状态 | 读取 manifest JSON 的 `steps[1].status` | 若为验证 2，应为 `failed`；若为验证 3，应为 `completed` |


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 session-tracer.ts | 从 git history 恢复 `venv/.opencode/plugin/session-tracer.ts` 到修改前版本 |
| 重启 session | `/new` 或重新打开窗口 |


## 八、关联文档

| 文档 | 说明 |
|------|------|
| `references/env-migrations/env-migration-opencode-plugin-tool-schema-architecture-2026-08-10-162736.md` | 五层 schema 架构建设 |
| `references/env-migrations/env-migration-session-tracer-sdk-compatibility-fix-2026-08-10-164345.md` | SDK 契约适配修复 |
| `references/env-migrations/env-migration-session-tracer-v2-smoke-test-and-manifest-bugfix-2026-08-10-165341.md` | Smoke test + manifest 落盘 bug 修复（遗漏了 milestone parseError） |
| `venv/.opencode/plugin/tool-schemas/trace-event.ts` | payload 校验器真源 |


## 九、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-10-172609 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求读取最新 env-migration + 继续测试 session-tracer + 纠偏 parseError 遗漏 + 改造 docstring |
| **下次修订条件** | `/new` 重启后验证清单完成 |
| **跨环境迁移参考** | 复制修改后的 `session-tracer.ts` + 按「验证清单」逐条执行 |


*文档生成时间：2026-08-10*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
