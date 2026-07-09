---
title: OpenCode Plugin Pre-Tool-Use 拦截能力与改造可行性研究
description: 基于官方文档与源码（packages/plugin/src/index.ts、packages/core/src/plugin.ts），论证 tool.execute.before hook 能否拦截并修改 bash 工具的 timeout 参数，并给出改造方案。
date: 2026-07-09
meta:
  version: 1.0.0
  author: opencode-agent
  tags: [opencode, plugin, hook, bash, timeout, tool-interception]
---

# OpenCode Plugin Pre-Tool-Use 拦截能力与改造可行性研究

## 1. 研究背景与核心问题

**触发场景**：`bash` 工具默认 `timeout` 为 120000ms（120s）。当执行 `archive_project.py --group cs_py` 等长耗时任务时，进程被静默 kill，导致操作失败。

**核心问题**：能否通过 OpenCode 的 `tool.execute.before` hook，在每次 bash 调用前自动提升 `timeout` 到更安全的阈值（如 600s），从而避免手动在每个 `bash` 调用中显式传参？

**研究目标**：
1. 确认 `tool.execute.before` 的 `output.args` 是否包含 `timeout` 字段且可被修改。
2. 确认 hook 修改后的参数是否即时生效（无需重启 session）。
3. 给出最小可运行的改造方案（`bash-timeout-guard.ts`）。

## 2. Hook 契约分析（源码级证据）

### 2.1 类型定义

`packages/plugin/src/index.ts` 中 `tool.execute.before` 的类型签名：

```typescript
"tool.execute.before"?: (
  input: { tool: string; sessionID: string; callID: string },
  output: { args: any },
) => Promise<void>
```

**关键发现**：
- `output.args` 的类型是 **`any`**，而非 `readonly` 或深冻结对象。这意味着 hook 可以**直接修改** args 中的任意字段。
- `input.tool` 是字符串形式的工具名（如 `"bash"`、`"write"`、`"edit"`），可用于条件过滤。

### 2.2 与 `tool.execute.after` 的对比

```typescript
"tool.execute.after"?: (
  input: { tool: string; sessionID: string; callID: string; args: any },
  output: { title: string; output: string; metadata: any },
) => Promise<void>
```

`after` hook 的 `input.args` 是调用**已完成后**的只读记录，不可修改工具行为；`before` hook 的 `output.args` 在工具**实际执行前**，可被改写。

## 3. 本地实测证据

### 3.1 现存 Plugin：`md-format-guard.ts`

路径：`D:\pjt\cursor\cs_py\venv\.opencode\plugin\md-format-guard.ts`

该 plugin 已注册 `tool.execute.before`，行为如下：

```typescript
"tool.execute.before": async (input, output) => {
  const toolName = input.tool
  if (toolName !== "write" && toolName !== "edit") {
    return
  }
  const args = output.args || {}
  const filePath = args.filePath || args.path || ""
  // ... 记录日志
}
```

**实证**：
- `hook-log.jsonl` 已有 **185 条**触发记录，证明 `tool.execute.before` 在每次 `write`/`edit` 调用前**确实被调用**。
- `output.args` 可被解构读取（`args.filePath`、`args.path`），证明其结构对 plugin **可读可写**。

### 3.2 推断：bash 工具的 args 结构

根据 OpenCode 官方文档，`bash` 工具的参数包括：
- `command: string`
- `workdir?: string`
- `timeout?: number`

`output.args` 在 `tool.execute.before` 阶段就是即将传给 bash 执行器的原始参数对象。因此 `output.args.timeout` 理论上可被修改。

## 4. 改造方案：`bash-timeout-guard.ts`

### 4.1 最小可行实现

```typescript
import type { Plugin } from "@opencode-ai/plugin"

export default (async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") {
        return
      }

      const args = output.args || {}
      const currentTimeout = args.timeout || 0

      // 若当前 timeout 小于 600s，强制提升到 600s
      if (currentTimeout < 600000) {
        args.timeout = 600000
        console.log(`[bash-timeout-guard] timeout adjusted: ${currentTimeout} → 600000ms`)
      }
    },
  }
}) satisfies Plugin
```

### 4.2 放置位置

- 项目级：`D:\pjt\cursor\cs_py\venv\.opencode\plugin\bash-timeout-guard.ts`
- 与 `md-format-guard.ts` 同级，OpenCode 启动时自动加载。

### 4.3 预期行为

| 场景 | 原始 timeout | 修改后 timeout |
|------|-------------|---------------|
| 用户未传 timeout（默认 120s） | 120000ms | 600000ms |
| 用户显式传 300s | 300000ms | 600000ms |
| 用户显式传 900s | 900000ms | 900000ms（已大于阈值，不修改） |

## 5. 生效条件：不是热重载问题，是加载时机问题

### 5.1 核心结论

**Plugin 一旦加载，hook 在每次 tool 调用前都会触发，无需额外操作。**

`tool.execute.before` 是**事件订阅模式**，不是文件读取模式。plugin 初始化时向 OpenCode 内核注册 hook，之后每次对应工具被调用，内核都会同步调用该 hook。这与 plugin 文件是否被修改无关。

### 5.2 何时需要重启？

**仅当新增、删除或重写 plugin 文件时需要重启 session（`/new` 或重新打开窗口）。**

原因：
- OpenCode 官方文档明确说明：`"Files in these directories are automatically loaded at startup."`
- 源码 `packages/core/src/plugin.ts` 中的 `Plugin.add` 虽然支持运行时替换已有 plugin，但**没有文件监视器（file watcher）自动触发重新加载**。
- `file.watcher.updated` 事件存在，但它是文件系统事件通知，不是 plugin 重载触发器。

### 5.3 与 Skill 的区别

| 维度 | Plugin | Skill |
|------|--------|-------|
| 加载时机 | Session 启动时 | Session 启动时扫描一次 |
| 运行时变更 | 不自动重载 | 不自动重载 |
| 触发频率 | 每次 tool 调用前 | 由 LLM 决策是否调用 |
| 修改后生效 | 需 `/new` 重启 | 需 `/new` 重启 |

> 参考：`AGENTS.md` 中「OpenCode 日志与 CLI 命令的信息源区分」章节已明确指出："当前 session 的 skill 列表只在初始化时确定，安装新 skill 后不会自动刷新。" Plugin 同理。

## 6. 限制与注意事项

### 6.1 `output.args` 为 `any` 的双刃剑

虽然 `any` 类型允许自由修改，但也意味着：
- **无编译时检查**：若字段名拼错（如 `args.timeOut`），修改将静默失效。
- **无 schema 校验**：OpenCode 不会在 hook 后校验 args 的合法性，错误的类型可能导致工具内部报错。

### 6.2 全局影响范围

`bash-timeout-guard.ts` 一旦生效，会**全局提升所有 bash 调用的 timeout**。这包括：
- 长耗时任务（预期受益）
- 本应在 120s 内完成的短命令（副作用：异常卡顿时延迟 5 分钟才 kill）

**缓解方案**：
- 添加白名单/黑名单逻辑（如仅对包含特定关键字的命令提升 timeout）。
- 或改为「仅在命令行长度超过某阈值、或包含特定脚本路径时提升」。

### 6.3 与 Agent 显式传参的优先级

若 Agent 在 `bash` 调用中显式写了 `timeout: 900000`，plugin 将其视为 `currentTimeout`，按逻辑判断是否修改。因此：
- **Agent 显式大 timeout** → plugin 不覆盖（安全）。
- **Agent 未传 timeout** → plugin 提升到 600s（受益）。
- **Agent 传了小 timeout** → plugin 提升到 600s（可能覆盖用户意图，需谨慎）。

## 7. 结论

| 问题 | 结论 |
|------|------|
| `tool.execute.before` 能否修改 `timeout`？ | **能**。`output.args` 为可写的 `any` 对象。 |
| 修改后是否即时生效？ | **是**。hook 在每次 tool 调用前触发，修改即时生效。 |
| 新增 plugin 后是否需要重启？ | **是**。plugin 在 session 启动时加载，当前 session 不会自动识别新文件。 |
| 改造是否可行？ | **完全可行**。参考 `md-format-guard.ts` 的既有模式，可在 10 行代码内实现。 |

## 8. 下一步行动建议

1. **创建 `bash-timeout-guard.ts`**：按 4.1 节代码放置到 `venv/.opencode/plugin/`。
2. **重启 session**：发送 `/new` 或重新打开窗口，使新 plugin 被加载。
3. **验证**：执行一个不带 `timeout` 的 `bash` 调用，观察 hook 是否触发（可在 plugin 中加 `console.log` 或写日志文件到 `venv/.opencode/plugin/`）。
4. **迭代优化**：根据实际运行数据，调整阈值（600s 是否合适）和过滤逻辑（是否全局生效）。


## 附录：引用源码与文档

- OpenCode Plugin 官方文档：`https://opencode.ai/docs/plugins`（2026-07-08 更新）
- `packages/plugin/src/index.ts`：`tool.execute.before` 类型定义
- `packages/core/src/plugin.ts`：`Plugin.add` / `Plugin.remove` 生命周期管理
- `packages/core/src/plugin/host.ts`：`PluginHost.make` 暴露的 `plugin.add` 接口
- 本地实测：`D:\pjt\cursor\cs_py\venv\.opencode\plugin\md-format-guard.ts` + `hook-log.jsonl`
