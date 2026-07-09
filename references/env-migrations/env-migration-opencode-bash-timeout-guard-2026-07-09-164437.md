---
title: OpenCode bash-timeout-guard Plugin 新增
description: 新增 OpenCode Plugin，在 bash 工具调用前自动将 timeout 提升至 600s，解决长耗时任务被静默 kill 的问题。
date: 2026-07-09
meta:
  version: 1.0.0
  author: opencode-agent
  tags: [opencode, plugin, bash, timeout]
---

# OpenCode bash-timeout-guard Plugin 新增

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 新增 OpenCode bash-timeout-guard Plugin，自动提升 bash timeout |
| **日期** | 2026-07-09 |
| **文件名时间戳** | `2026-07-09-164437` |
| **触发原因** | `archive_project.py --group cs_py` 执行时被 bash 120s 默认 timeout 静默 kill |
| **影响范围** | OpenCode Plugin 目录（`venv/.opencode/plugin/`） |
| **风险等级** | 低（仅提升 timeout，不修改业务逻辑） |

## 一、文本文件变更清单

### 1. 新建 `venv/.opencode/plugin/bash-timeout-guard.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/bash-timeout-guard.ts` |
| **变更类型** | `新建` |
| **作用** | 注册 `tool.execute.before` hook，拦截所有 `bash` 工具调用，将 `timeout < 600000ms` 的参数强制提升到 `600000ms` |
| **验证方式** | 重启 session 后执行不带 timeout 的 bash 命令，检查同目录 `hook-log.jsonl` 中是否出现 `timeout_adjusted` 记录 |
| **迁移方式** | 直接复制文件到新环境对应路径 |

**文件内容**（可直接复制）：

```typescript
import type { Plugin } from "@opencode-ai/plugin"
import { appendFileSync, existsSync } from "node:fs"
import { resolve } from "node:path"

const LOG_FILE = resolve(import.meta.dirname || ".", "hook-log.jsonl")

function logHook(entry: Record<string, unknown>) {
  const line = JSON.stringify({
    ...entry,
    _loggedAt: new Date().toISOString(),
  }) + "\n"
  appendFileSync(LOG_FILE, line, "utf-8")
}

export default (async () => {
  if (!existsSync(LOG_FILE)) {
    appendFileSync(LOG_FILE, "", "utf-8")
  }

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") {
        return
      }

      const args = output.args || {}
      const currentTimeout = args.timeout || 0

      if (currentTimeout < 600000) {
        args.timeout = 600000
        logHook({
          event: "tool.execute.before",
          tool: input.tool,
          sessionID: input.sessionID,
          callID: input.callID,
          action: "timeout_adjusted",
          oldTimeout: currentTimeout,
          newTimeout: 600000,
        })
      }
    },
  }
}) satisfies Plugin
```

## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移等非文本操作。

## 三、环境变量速查

无需新增或修改环境变量。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.ts` | `run-lint.py --profile lint-encoding` | BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |

**执行记录**：
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\venv\.opencode\plugin\bash-timeout-guard.ts"
# 结论：✅ 全部通过（0 违规）
```

## 五、验证清单（新环境 / 重启后必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 plugin 文件存在 | `Test-Path "venv/.opencode/plugin/bash-timeout-guard.ts"` | `True` |
| 2 | 重启 OpenCode session | `/new` 或重新打开窗口 | — |
| 3 | 执行一次 bash 调用（不带 timeout） | 任意 `bash` 工具调用 | 命令正常执行，不被 120s kill |
| 4 | 检查 hook 日志 | 读取 `venv/.opencode/plugin/hook-log.jsonl` 末尾 | 包含 `action: "timeout_adjusted"` 记录 |

> **注意**：新增 plugin 文件后，**必须重启 session** 才能生效。当前 session 不会自动加载新 plugin。

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 plugin 文件 | `Remove-Item "venv/.opencode/plugin/bash-timeout-guard.ts"` |
| 重启 session | `/new` 或重新打开窗口 |
| 验证恢复 | 执行长耗时 bash 命令，确认 120s 后被 kill（恢复默认行为） |

## 七、关联文档

| 文档 | 说明 |
|------|------|
| `references/tasks/deploy-git-isolated/docs/research/opencode-plugin-pre-tool-use-research-2026-07-09-163543.md` | 本次改造的源码级可行性研究 |
| `venv/.opencode/plugin/md-format-guard.ts` | 既有 plugin 参考实现 |

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-09-164437 |
| **更新人** | OpenCode Agent Session |
| **变更触发** | archive_project.py 被 bash 120s timeout kill |
| **下次修订条件** | 调整 timeout 阈值、增加过滤逻辑、或 plugin 行为异常时 |
| **跨环境迁移参考** | 直接复制 `bash-timeout-guard.ts` 到新环境 `venv/.opencode/plugin/` + 重启 session |
