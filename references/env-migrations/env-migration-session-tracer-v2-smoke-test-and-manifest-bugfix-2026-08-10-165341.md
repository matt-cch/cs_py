---
title: session-tracer v2.0.0 Smoke Test 与 Manifest 落盘时序 Bug 修复
description: 重启后验证 session-tracer.ts ToolManifest 双轨输出能力，发现 finalizeManifest 后未再次落盘导致磁盘 manifest 状态为 running，已修复，待 /new 重启后最终回归验证
date: 2026-08-10
meta:
  version: 1.0.0
  tags: [opencode, plugin, session-tracer, schema, smoke-test, env-migration]
---

# env-migration-session-tracer-v2-smoke-test-and-manifest-bugfix-2026-08-10-165341

> **Session 主题**：session-tracer v2.0.0 Smoke Test 与 Manifest 落盘时序 Bug 修复
> **日期**：2026-08-10（文件名时间戳：2026-08-10-165341）
> **触发原因**：接续 env-migration-opencode-plugin-tool-schema-architecture-2026-08-10-162736 中的「重启验证清单」，在当前 session 中执行 smoke test
> **影响范围**：`venv/.opencode/plugin/session-tracer.ts`（1 处修复）
> **风险等级**：低（plugin 源码已修正，但当前 session 未重载，修复尚未生效）


## 一、文本文件变更清单

### 1. 修改 `venv/.opencode/plugin/session-tracer.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/session-tracer.ts` |
| **变更类型** | 修改（追加 6 行） |
| **新增内容** | 在 `finalizeManifest()` 之后追加第二次 `writeManifestFile()`，确保磁盘 manifest 文件包含 `completed` 状态与最终时间戳 |
| **作用** | 修正「manifest 落盘时序 bug」：finalize 后未再次写盘，导致磁盘文件中 step 4 (`write_manifest`) 和 `overall_status` 始终为 `running` |
| **验证方式** | 已修改磁盘源码，但 OpenCode 无热重载，当前 session 内存中仍为旧版本；待 `/new` 重启后验证 |
| **迁移方式** | 文件可直接复制，无路径依赖 |


## 二、非文本操作

| 操作类型 | 路径 | 说明 |
|---------|------|------|
| manifest 生成（测试产物） | `venv/tmp/session-tracer-manifest-msg_feadae02f001wOqsJSJBTAA5Wi.json` | Smoke test 第 1 次调用产物（含 bug：step 4 为 running） |
| manifest 生成（测试产物） | `venv/tmp/session-tracer-manifest-msg_feadcb697001DFIOhRf9GYuFyG.json` | Regression test 第 2 次调用产物（含 bug：step 4 为 running） |
| JSONL 追加 | `venv/tmp/session-trace.jsonl` | 2 条新 TraceEvent 追加（含 `_schema_version: 2.0.0`） |
| 临时测试脚本 | `venv/tmp/test-manifest-audit.ts` | 独立 Node.js 脚本，验证 `generateAuditSummary()` 输出正确性（已清理） |


## 三、Session 踩坑与纠偏记录

### 3.1 Manifest 落盘时序 Bug

**现象**：
- Smoke test 后读取 manifest 文件，发现 step 3 (`write_manifest`) 的 `status` 为 `running`，`overall_status` 也为 `running`。
- 预期：两者均应为 `completed`。

**根因**：
- `session-tracer.ts` 中 `writeManifestFile()` 在 `completeStep()` 之前调用，写入磁盘时 step 3 尚未完成。
- `finalizeManifest()` 将内存中 `overall_status` 更新为 `completed`，但**未再次调用 `writeManifestFile()`**，导致磁盘状态与内存状态脱节。

**修复**：
- 在 `finalizeManifest()` 之后追加：

```typescript
// 修正：finalize 后再次落盘，确保磁盘文件包含 completed 状态与最终时间戳
try {
  writeManifestFile(manifest, messageID)
} catch (e) {
  console.error(`[session-tracer] Final manifest write failed: ${(e as Error).message}`)
}
```

### 3.2 OpenCode Plugin 无热重载

**现象**：修复磁盘源码后，在当前 session 中再次调用 `session_tracer`，manifest 文件仍显示 `running`。

**根因**：OpenCode 长连接 session 仅在初始化时加载 plugin 源码，后续磁盘变更不会被当前 session 识别。

**根因出处**：`AGENTS.md` 第 3 节「OpenCode 日志与 CLI 命令的信息源区分」：
> 当前 session 的 skill 列表只在初始化时扫描一次，安装新 skill 后不会自动刷新。CLI 命令能看到新 skill，不代表当前长连接 session 能调用它。

Plugin 行为与此一致。

**结论**：磁盘文件已修复，但验证必须等待**发送 `/new` 重启 session**后重新加载 plugin。

### 3.3 `generateAuditSummary` 独立验证

**现象**：manifest 落盘 bug 导致无法通过 plugin 验证 `generateAuditSummary`，需寻找替代验证路径。

**修复**：编写独立 TypeScript 脚本 `venv/tmp/test-manifest-audit.ts`，使用 `npx tsx` 直接运行，绕过 plugin 生命周期，直接调用 `tool-manifest.ts` 的工厂函数和 `generateAuditSummary`。

**验证结果**：
```
=== Tool Manifest: test-tool@1.0.0 ===
Status: completed
Steps: 3 total
  ✅ [0] prepare: 准备环境 (0ms)
  ✅ [1] execute: 执行核心逻辑 (0ms)
      📎 log_file: D:\test\log.txt
  ✅ [2] cleanup: 清理临时文件 (0ms)

Artifacts: 1 total
```

`generateAuditSummary` 逻辑正确，无需修改。


## 四、环境变量速查

本次 session 未新增或修改 `.vscode/settings.json` 中的环境变量注入项。


## 五、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py` | frontmatter、编码、正文 `---` 污染 | BOM=no, CRLF=0, LF>0, frontmatter 合规 |
| `.ts`（session-tracer.ts 修改） | `run-lint.py --profile lint-encoding` | 编码/BOM/换行符 | UTF-8, LF |

全部文件已通过 `run-lint.py --fix` 验证。


## 六、验证清单（重启后必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 发送 `/new` 重启 session | 用户发送 `/new` | OpenCode 重新加载 plugin |
| 2 | 调用 `session_tracer` | 调用 tool `session_tracer` | 响应含 `✅ Recorded ... (4 steps, manifest saved)` |
| 3 | 读取最新 manifest 文件 | `Get-ChildItem venv/tmp/session-tracer-manifest-*.json \| Sort-Object LastWriteTime -Descending \| Select-Object -First 1` | 文件存在，大小 > 2000 bytes |
| 4 | 检查 step 4 状态 | 读取 manifest JSON 的 `steps[3].status` | 必须为 `"completed"` |
| 5 | 检查 overall_status | 读取 manifest JSON 的 `overall_status` | 必须为 `"completed"` |
| 6 | 检查 ended_at | 读取 manifest JSON 的 `ended_at` | 存在且为 ISO 8601 时间戳 |
| 7 | 检查 duration_ms | 读取 manifest JSON 的 `duration_ms` | 存在且 > 0 |
| 8 | 运行 `generateAuditSummary` | 可选：编写独立脚本调用 | 输出含 `Status: completed` 与完整步骤列表 |


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 session-tracer.ts | 从 git history 恢复 `venv/.opencode/plugin/session-tracer.ts` 到修改前版本 |
| 删除测试产物 | `Remove-Item "venv/tmp/session-tracer-manifest-*.json"`（不影响功能） |
| 删除 JSONL 追加行 | 手动编辑 `venv/tmp/session-trace.jsonl` 删除最后 2 行（可选） |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-10-165341 |
| **更新人** | Human + Agent Session |
| **变更触发** | session-tracer v2.0.0 重启验证清单执行 |
| **下次修订条件** | `/new` 重启后最终回归验证完成、tool-verify-demo.ts 开发 |
| **跨环境迁移参考** | 直接复制修改后的 `session-tracer.ts` + 按「验证清单」逐条执行 |


*文档生成时间：2026-08-10*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
