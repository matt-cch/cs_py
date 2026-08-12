---
title: Session-Tracer Plugin 开发与 Subagent 验证失败实录
description: 编写 OpenCode tool 型 plugin `session-tracer.ts`，尝试通过 subagent 验证其可用性，实测 subagent 无法等价 /new 热加载 plugin。同时讨论 runtime session messages 记录的长期数据模型。
date: 2026-08-10
meta:
  version: 1.0.0
  tags: [opencode, plugin, tool, session-tracer, subagent, env-migration]
---

# env-migration-session-tracer-plugin-and-subagent-validation-2026-08-10-141741

> **Session 主题**：Session-Tracer Plugin 开发、Subagent 验证失败、Runtime Session Messages 记录需求讨论
> **日期**：2026-08-10（文件名时间戳：2026-08-10-141741）
> **触发原因**：用户要求执行真源检测 → 查看 opencode plugin 记录 → 将认知落盘 vault → 提出开发新 tool 型 plugin → 讨论 session trace 记录需求 → subagent 验证
> **影响范围**：`venv/.opencode/plugin/`、`venv/tmp/`、`references/env-migrations/`、`vaults/vault-demo/wiki/learnings/`
> **风险等级**：低（plugin 源码仅落盘，未生效；无文件系统副作用）


## 一、文本文件变更清单

### 1. 新建 `venv/.opencode/plugin/session-tracer.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/session-tracer.ts` |
| **变更类型** | `新建` |
| **作用** | 注册自定义 tool `session_tracer`，用于记录 session trace event（含 sessionID、timestamp、directory、worktree、event_type、payload、notes 等） |
| **SDK 版本** | 基于 `@opencode-ai/plugin` 1.18.15（`dist/tool.d.ts` + `dist/index.d.ts` 真源） |
| **工具定义** | `tool({ description, args: { event_type, payload?, notes? }, execute })` |
| **执行逻辑** | 从 `context` 提取 `sessionID`, `messageID`, `agent`, `directory`, `worktree`，组合用户参数，追加到 `venv/tmp/session-trace.jsonl` |
| **返回值** | `{ title, output, metadata: { trace_file, event_type, timestamp } }` |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过（BOM=no, CRLF=0, LF=87） |
| **当前状态** | ⚠️ **尚未生效**。plugin 在 session 启动时扫描加载，当前 session 无法热重载。 |
| **迁移方式** | 直接复制 `session-tracer.ts` 到新环境 `venv/.opencode/plugin/`，重启 session |

### 2. 新建 `vaults/vault-demo/wiki/learnings/opencode-plugin-agent-cognition-2026-08-10-134831.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/learnings/opencode-plugin-agent-cognition-2026-08-10-134831.md` |
| **变更类型** | `新建` |
| **作用** | Agent 多轮 Session 建设实录：从 md-format-guard 实验到 bash-timeout-guard 投产、SDK 升级、严重踩坑与纠偏 |
| **内容要点** | 触发原因（3 个 session 的 Human 真实意图）、建设时间线（Phase 1→2→3）、核心研究（源码级 Hook 契约）、关键结论、关键操作、产物清单、严重踩坑（3 个反面教材）、技术机制详解、当前 Plugin 行为与局限、跨环境迁移参考 |
| **验证方式** | `run-lint.py` 通过（frontmatter、编码、换行符、正文 `---` 污染均合规） |
| **迁移方式** | 直接复制文件，路径中的 `vault-demo` 按实际 vaultroot 调整 |

### 3. 修改 `vaults/vault-demo/wiki/learnings/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/learnings/README.md` |
| **变更类型** | `修改`（导航表追加一行） |
| **新增内容** | 追加 `opencode-plugin-agent-cognition-2026-08-10-134831.md` 条目 |
| **作用** | 目录导航联动 |


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。唯一涉及的目录创建是 `venv/tmp/`（由 `session-tracer.ts` 的 `ensureTraceFile` 逻辑在首次执行时自动创建），但当前 plugin 尚未加载，因此该目录尚未实际创建。


## 三、Session 踩坑与纠偏记录

### 3.1 Subagent 无法等价 `/new` —— Plugin Tool 热加载假设失败

**现象**：用户提出"delegate subagent 的测试模式似乎可以等价 `/new` 的效果"，Agent 启动 subagent（`task` tool，`subagent_type=general`）执行验证任务。Subagent 报告其可用工具列表仅包含 8 个内置工具（`bash`, `edit`, `glob`, `grep`, `read`, `skill`, `webfetch`, `write`），`session_tracer` 不在其中。

**根因**：
1. `task` tool 启动的 subagent **不重新扫描** `plugin/` 目录。
2. Subagent 要么复用了 parent session 的初始化工具列表（parent session 初始化时 `session-tracer.ts` 尚未存在），要么自身就是受限上下文。
3. 这与 Skill 的行为一致：当前 session 的 tool 列表只在初始化时确定，不热重载。

**结论**：**验证自定义 tool plugin 的唯一可靠路径仍是 `/new` 重启 session 或新开窗口。** Subagent 不能作为 plugin 加载的测试替身。

### 3.2 Hook-Log 数据分析发现

在 session 早期，Agent 读取了 `venv/.opencode/plugin/hook-log.jsonl` 的前 100 行（共 1809 行）。关键发现：
- 时间跨度：2026-06-05 至 2026-08-10（约 66 天）
- 记录维度：仅包含 `event`, `tool`, `sessionID`, `callID`, `filePath`, `argsKeys`, `_loggedAt`
- **缺失维度**：`args` 的值（仅记录键名）、用户消息内容、LLM 回复内容、待办状态、推理过程

这些缺失维度正是用户提出的"session trace 长远需求"的核心。


## 四、Runtime Session Messages 记录需求讨论（决策上下文）

### 4.1 用户原始诉求

用户提出长远需求：记录 runtime session 时间线，实现可追踪、可审计、可巡检、可搜索定位、可 BI 展示。关键信息项包括：
- `sessionID`：会话唯一标识
- `callID`：单次 tool 调用标识
- `timestamp`：时间戳
- `traceID`：跨 session 的追踪标识（如一次复杂任务涉及多次 `/new`）
- `turnID`：对话轮次标识
- `think`：Agent 推理过程
- `todos`：待办状态快照
- 其他：用户原始输入、LLM 回复、tool 执行结果等

### 4.2 当前已有数据 vs 理想数据模型

| 维度 | 当前 hook-log.jsonl（tool.execute.before） | 理想 session-trace.jsonl |
|------|------------------------------------------|-------------------------|
| sessionID | ✅ 有 | ✅ 有 |
| callID | ✅ 有 | ✅ 有 |
| timestamp | ✅ 有 | ✅ 有 |
| tool 名称 | ✅ 有 | ✅ 有 |
| filePath | ✅ 有 | ✅ 有 |
| argsKeys | ✅ 有（仅键名） | ❌ 应包含完整 args 值 |
| traceID | ❌ 无 | ✅ 需新增 |
| turnID | ❌ 无 | ✅ 需新增 |
| user_message | ❌ 无 | ✅ 需通过 chat.message hook 捕获 |
| llm_response | ❌ 无 | ✅ 需通过 tool.execute.after 或 chat 相关 hook 捕获 |
| think | ❌ 无 | ✅ 需推断或 LLM 输出标记 |
| todos | ❌ 无 | ✅ 需 Agent 主动调用 session_tracer 记录 |

### 4.3 三层数据采集架构（讨论结论）

```
┌─────────────────────────────────────────────────────────┐
│  层级 1：OpenCode Plugin Hooks（已落地）                 │
│  - tool.execute.before / after → 工具调用审计            │
│  - chat.message → 用户消息捕获（experimental，待验证）   │
│  - chat.params → LLM 参数快照                            │
│  - event → 全局事件监听（experimental）                  │
├─────────────────────────────────────────────────────────┤
│  层级 2：自定义 tool（session_tracer，待 /new 验证）       │
│  - Agent 主动调用 session_tracer(event_type, payload)    │
│  - 用于记录"里程碑事件"（决策点、待办变更、错误恢复等）   │
├─────────────────────────────────────────────────────────┤
│  层级 3：后处理与聚合（未来）                             │
│  - 按 sessionID 聚合为 Session Manifest                  │
│  - 按 traceID 跨 session 关联为 Trace Graph              │
│  - 导入 Graph DB 或 Vector DB 支持 RAG 查询              │
└─────────────────────────────────────────────────────────┘
```

### 4.4 下一步选项（用户未做最终决策，需重启后继续）

| 选项 | 内容 | 状态 |
|------|------|------|
| A | 手动 `/new` 验证 `session_tracer` tool 可用性 | ⏳ 待执行 |
| B | 扩展 hook 型 plugin 采集能力（完整 args、chat.message） | ⏳ 待讨论 |
| C | 先讨论数据模型设计，出 `session-trace-schema.md` | ⏳ 待讨论 |


## 五、验证清单（重启后必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 plugin 文件存在 | `Test-Path "venv/.opencode/plugin/session-tracer.ts"` | `True` |
| 2 | 重启 OpenCode session | `/new` 或重新打开窗口 | — |
| 3 | 检查新 session 是否加载了 session_tracer | 查看 Agent 可用工具列表中是否包含 `session_tracer` | 包含 |
| 4 | 调用 session_tracer tool | 发送 prompt："调用 session_tracer 记录一个测试事件" | Tool 被调用，返回成功 |
| 5 | 检查 trace 文件 | `Test-Path "venv/tmp/session-trace.jsonl"` | `True` |
| 6 | 验证 trace 内容 | 读取 `venv/tmp/session-trace.jsonl` 末尾 | 包含 `event_type: "test_subagent_invocation"` 或用户指定的测试事件 |


## 六、Lint 与语法检测覆盖说明

### 6.1 `run-lint.py` 对 `.ts` / `.js` 的覆盖矩阵

| 检测维度 | `.js` | `.ts` | run-lint 插件 | 能否 `--fix` |
|----------|-------|-------|--------------|-------------|
| 编码/BOM/换行符 | ✅ 覆盖 | ✅ 覆盖 | `lint_encoding` | ✅ |
| 语法解析 | ❌ 未覆盖 | ❌ 未覆盖 | — | — |
| 类型检查 | N/A | ❌ 未覆盖 | — | — |

### 6.2 JS 语法检测：`node --check`

```powershell
& "${devroot}\venv\node\node.exe" --check "path/to/file.js"
```

- 等价于 Python 的 `python -m py_compile file.py`
- 只解析不执行，检测语法错误
- **但对 `.ts` 不适用**——TypeScript 类型注解等语法不是合法 JS

### 6.3 TS 语法检测：`tsc --noEmit`（当前环境未安装）

```powershell
# 需先安装 typescript
& "${devroot}\venv\node\npm.cmd" --prefix "${devroot}\venv\.opencode" install typescript --save-dev
& "${devroot}\venv\node\npx.cmd" --prefix "${devroot}\venv\.opencode" tsc --noEmit --esModuleInterop path/to/file.ts
```

**当前状态**：`venv/.opencode/` 下**没有** `typescript` 包，`tsc` 不可用。

### 6.4 对当前 plugin 文件的实际验证来源

1. **OpenCode 启动时加载**（第一关）：`.ts` 有语法错误则 session 初始化时报错，plugin 不会被加载。
2. **编码层 lint**（第二关）：`run-lint.py` 保证 BOM/换行符合规。
3. **人工 review**（第三关）：代码量小（<100 行），肉眼可读。

### 6.5 结论

> `run-lint.py` 对 `.js`/`.ts` **只覆盖编码层**，**不覆盖语法层**。`.js` 语法可用 `node --check`（类 `py_compile`）；`.ts` 语法需要 `tsc --noEmit`，但当前环境未安装 `typescript`。当前 plugin 规模下，OpenCode 启动时的加载报错是实际语法验证机制。


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 plugin 文件 | `Remove-Item "venv/.opencode/plugin/session-tracer.ts"` |
| 重启 session | `/new` 或重新打开窗口 |
| 删除 trace 文件（如已生成） | `Remove-Item "venv/tmp/session-trace.jsonl"` |
| 删除 vault 认知文档（可选） | `Remove-Item "vaults/vault-demo/wiki/learnings/opencode-plugin-agent-cognition-2026-08-10-134831.md"` |
| 恢复 learnings/README.md | 从 git history 恢复 |


## 八、关联文档

| 文档 | 说明 |
|------|------|
| `vaults/vault-demo/wiki/learnings/opencode-plugin-agent-cognition-2026-08-10-134831.md` | 本次 session 早期生成的 OpenCode Plugin 系统性认知沉淀 |
| `references/tasks/deploy-git-isolated/docs/research/opencode-plugin-pre-tool-use-research-2026-07-09-163543.md` | Hook 型 plugin 的可行性研究 |
| `references/env-migrations/env-migration-opencode-plugin-sdk-upgrade-and-atomic-npm-update-2026-08-10-125601.md` | SDK 升级与 atomic-npm-update 建设 |
| `venv/.opencode/plugin/md-format-guard.ts` | 既有 hook 型 plugin 参考 |
| `venv/.opencode/plugin/bash-timeout-guard.ts` | 既有 hook 型 plugin 参考 |
| `venv/.opencode/node_modules/@opencode-ai/plugin/dist/tool.d.ts` | SDK tool 类型真源 |
| `venv/.opencode/node_modules/@opencode-ai/plugin/dist/index.d.ts` | SDK Plugin/Hooks 类型真源 |


## 九、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-10-142800（补充 Lint 与语法检测覆盖说明） |
| **更新人** | OpenCode Agent Session |
| **变更触发** | 真源检测 → plugin 记录查看 → 认知落盘 vault → tool plugin 开发 → subagent 验证 → session trace 需求讨论 → 补充 lint 语法覆盖说明 |
| **下次修订条件** | `/new` 验证 session_tracer 结果、扩展 hook 采集能力、确定 session trace schema、引入 tsc 语法检测 |
| **跨环境迁移参考** | 复制 `session-tracer.ts` + 按「验证清单」逐条执行；vault 文档可直接复制 |


*文档生成时间：2026-08-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
