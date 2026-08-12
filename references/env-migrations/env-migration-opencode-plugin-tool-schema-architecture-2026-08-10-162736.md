---
title: OpenCode Plugin Tool Schema 分层架构建设
description: 以 session-tracer.ts 为引子，建设自定义 tool 的五层 schema 架构（ToolResult / ToolManifest / TraceEvent / TraceIndex / VersionControl），配套目录结构与命名规范，改造 session-tracer.ts 作为 smoke test，产出架构设计文档落盘 vault
date: 2026-08-10
meta:
  version: 1.0.0
  tags: [opencode, plugin, schema, architecture, tool-manifest, env-migration]
---

# env-migration-opencode-plugin-tool-schema-architecture-2026-08-10-162736

> **Session 主题**：OpenCode Plugin Tool Schema 分层架构建设
> **日期**：2026-08-10（文件名时间戳：2026-08-10-162736）
> **触发原因**：session-tracer.ts 验证过程中发现返回值缺乏受控结构化、执行过程黑盒、扩展性不足，遂引出完整 schema 分层设计
> **影响范围**：`venv/.opencode/plugin/` 下全部 tool 型插件及未来新建插件
> **风险等级**：低（plugin 源码仅落盘，未生效；无文件系统副作用）


## 一、文本文件变更清单

### 1. 新建 `venv/.opencode/plugin/tool-schemas/tool-result.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-schemas/tool-result.ts` |
| **变更类型** | 新建 |
| **内容** | ToolResult<T> 泛化壳（success/error/data/meta/summary 五段式）+ 工厂函数 buildResult/ok/err + 错误码枚举 ErrorCode |
| **作用** | 所有自定义 tool 的返回值统一结构，下游可解析、可嵌入 todo pipeline |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过 |

### 2. 新建 `venv/.opencode/plugin/tool-schemas/tool-manifest.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-schemas/tool-manifest.ts` |
| **变更类型** | 新建 |
| **内容** | ToolManifest 执行轨迹 schema（steps + artifacts + audit）+ 生命周期函数 + 序列化/查询工具 |
| **作用** | 记录 tool 执行过程的完整时间线与产物清单，供 audit/追溯/数据库导入 |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过 |

### 3. 新建 `venv/.opencode/plugin/tool-schemas/trace-event.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-schemas/trace-event.ts` |
| **变更类型** | 新建 |
| **内容** | TraceEvent Registry 模式 + 预置 10+ event_type 校验器 |
| **作用** | 业务数据模型，支持通过 registerPayloadValidator 扩展新事件类型 |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过 |

### 4. 新建 `venv/.opencode/plugin/tool-schemas/trace-index.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-schemas/trace-index.ts` |
| **变更类型** | 新建 |
| **内容** | TraceDocument 统一格式 + TraceStoreAdapter 接口 |
| **作用** | JSONL 到数据库的衔接层，支持 FTS/BM25/Vector 索引 |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过 |

### 5. 新建 `venv/.opencode/plugin/tool-schemas/version-control.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-schemas/version-control.ts` |
| **变更类型** | 新建 |
| **内容** | TraceRecordVersion + TraceBranch + TraceCommit + diff 工具 |
| **作用** | 记录级版本链，类似 Git 的本地版本管理（延伸层，实验性） |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过 |

### 6. 改造 `venv/.opencode/plugin/session-tracer.ts`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/session-tracer.ts` |
| **变更类型** | 修改 |
| **变更内容** | 引入 ToolManifest 双轨输出：5 步骤执行轨迹 + ToolResult 同步返回 + manifest 异步落盘 |
| **作用** | 作为 smoke test，验证 schema 分层架构的完整链路 |
| **验证方式** | `run-lint.py --profile lint-encoding` 通过 |

### 7. 新建 `venv/.opencode/plugin/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/README.md` |
| **变更类型** | 新建 |
| **内容** | 命名规则、文件/子目录导航表、加载机制说明 |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |

### 8. 新建 `venv/.opencode/plugin/tool-schemas/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-schemas/README.md` |
| **变更类型** | 新建 |
| **内容** | 5 层 schema 索引与使用方式 |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |

### 9. 新建 `venv/.opencode/plugin/tool-types/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-types/README.md` |
| **变更类型** | 新建 |
| **内容** | 纯类型定义目录说明（当前预留） |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |

### 10. 新建 `venv/.opencode/plugin/tool-shared/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/tool-shared/README.md` |
| **变更类型** | 新建 |
| **内容** | 共享工具函数目录说明（当前预留） |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |

### 11. 新建 `venv/.opencode/plugin/shared/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/plugin/shared/README.md` |
| **变更类型** | 新建 |
| **内容** | 全局共享目录说明（跨 hook/tool/tui） |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |

### 12. 新建 `vaults/vault-demo/wiki/designs/opencode-plugin-tool-schema-architecture-2026-08-10-162321.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/designs/opencode-plugin-tool-schema-architecture-2026-08-10-162321.md` |
| **变更类型** | 新建 |
| **内容** | 完整架构设计文档（背景、五层 schema、规范、目录结构、实现、验证计划、待办） |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |

### 13. 修改 `vaults/vault-demo/wiki/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/README.md` |
| **变更类型** | 修改（导航表追加 designs/ 条目） |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |


## 二、非文本操作

| 操作类型 | 路径 | 说明 |
|---------|------|------|
| 目录创建 | `venv/.opencode/plugin/tool-schemas/` | tool 型插件 schema 定义目录 |
| 目录创建 | `venv/.opencode/plugin/tool-types/` | tool 型插件纯类型定义目录（预留） |
| 目录创建 | `venv/.opencode/plugin/tool-shared/` | tool 型插件共享工具函数目录（预留） |
| 目录创建 | `venv/.opencode/plugin/shared/` | 全局共享目录（跨 hook/tool/tui） |
| 目录创建 | `vaults/vault-demo/wiki/designs/` | 架构设计文档分类目录（新增） |


## 三、Session 踩坑与纠偏记录

### 3.1 `glob` 按名称排序不可靠

**现象**：Agent 用 `glob "references/env-migrations/env-migration-*.md"` 查找最新文件，按名称排序返回的是字母顺序而非时间顺序，导致读取的不是最新文件。

**根因**：`glob` 默认按文件名排序，env-migration 文件名虽含时间戳，但按名称排序在跨月份或格式不一致时会失效。

**修复**：改用 `Get-ChildItem | Sort-Object LastWriteTime -Descending` 按实际修改时间排序。

**改进**：Agent 在查找最新文件时，必须优先使用 `LastWriteTime` 而非文件名排序。

### 3.2 `plugin/` 目录与 npm 包子路径概念混淆

**现象**：Agent 建议 `plugin/tool/` 子目录，用户质疑是否与 `@opencode-ai/plugin/tui`、`@opencode-ai/plugin/zod` 等官方子路径冲突。

**根因**：Agent 混淆了 A 级（官方 npm 包内部导出路径）与 B 级（本地自定义 plugin 目录）两个完全不同的层级。

**澄清**：
- A 级：`node_modules/@opencode-ai/plugin/` 下的 `tui/`、`zod/`、`v2/` 等，由 npm 包提供
- B 级：`venv/.opencode/plugin/` 下的 `tool-schemas/`、`tool-types/`、`tool-shared/`、`shared/`，由项目自定义

**结论**：两者物理隔离，无冲突。B 级目录命名采用 `tool-schemas/`（带连字符）以区分官方子路径。

### 3.3 目录导航越级链接

**现象**：`plugin/README.md` 中写了指向项目根目录的链接，用户指出不应越级链接。

**根因**：Agent 未严格遵守「只维护直接父子目录导航」的原则。

**修复**：删除越级链接，仅保留直接父目录说明。


## 四、验证清单

### 4.1 编码验证

| 文件/目录 | 验证工具 | 结果 |
|-----------|---------|------|
| `tool-schemas/*.ts` (5 个) | `run-lint.py --profile lint-encoding` | 全部通过 |
| `session-tracer.ts` | `run-lint.py --profile lint-encoding` | 通过 |
| `plugin/README.md` | `run-lint.py --profile lint-md` | 通过 |
| `tool-schemas/README.md` | `run-lint.py --profile lint-md` | 通过 |
| `tool-types/README.md` | `run-lint.py --profile lint-md` | 通过 |
| `tool-shared/README.md` | `run-lint.py --profile lint-md` | 通过 |
| `shared/README.md` | `run-lint.py --profile lint-md` | 通过 |
| `vaults/.../designs/*.md` | `run-lint.py --profile lint-md` | 通过 |
| `vaults/.../wiki/README.md` | `run-lint.py --profile lint-md` | 通过 |

### 4.2 重启后验证清单（待执行）

```
1. 发送 /new 重启 session
2. 调用 session_tracer 记录测试事件
3. 检查 JSONL 文件是否追加新行
4. 检查 venv/tmp/ 下是否生成 session-tracer-manifest-*.json
5. 读取 manifest 文件，确认 steps 字段完整（5 个步骤）
6. 验证 ToolResult 返回结构（含 success/data/meta/summary）
7. 运行 generateAuditSummary 生成人类可读摘要
```


## 五、待办事项与下一步行动

### 5.1 当前 session 已完成

- [x] tool-schemas/tool-result.ts
- [x] tool-schemas/tool-manifest.ts
- [x] tool-schemas/trace-event.ts
- [x] tool-schemas/trace-index.ts
- [x] tool-schemas/version-control.ts
- [x] session-tracer.ts 改造（引入 ToolManifest）
- [x] plugin/ 及子目录 README.md（5 个）
- [x] vaults/.../designs/ 架构设计文档
- [x] wiki/README.md 导航更新

### 5.2 下一步行动（供重启后接续）

| # | 任务 | 优先级 | 说明 |
|---|------|--------|------|
| 1 | **重启验证 session-tracer.ts** | 高 | 发送 `/new`，调用 `session_tracer`，检查 ToolResult + ToolManifest 双轨输出 |
| 2 | **tool-verify-demo.ts 开发** | 高 | 设计多步骤 tool（如 Playwright 验证），完整展示 ToolManifest 的 audit 价值 |
| 3 | **填充 tool-types/** | 中 | 从 tool-schemas/ 抽取纯类型定义 |
| 4 | **填充 tool-shared/** | 中 | 抽取共用工具函数 |
| 5 | **TraceStoreAdapter 实现** | 低 | SQLite/PostgreSQL 适配器 |

### 5.3 tool-verify-demo.ts 预设计

**目标**：验证 ToolManifest 在多步骤、多产物场景下的完整能力。

**模拟场景**：前端页面可用性验证（简化版 Playwright）

```
Phase 1: 环境准备
  Step 1.1: check_node_env
  Step 1.2: create_temp_dir

Phase 2: 测试执行
  Step 2.1: write_test_script
  Step 2.2: run_test
  Step 2.3: capture_screenshot

Phase 3: 清理与报告
  Step 3.1: analyze_results
  Step 3.2: cleanup
  Step 3.3: generate_report

产物清单：
  - screenshot: venv/tmp/tool-verify-demo-<timestamp>.png
  - manifest: venv/tmp/tool-verify-demo-manifest-<callID>.json
  - log: venv/tmp/tool-verify-demo-<timestamp>.log
```


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 schema 文件 | `Remove-Item "venv/.opencode/plugin/tool-schemas/*.ts"` |
| 恢复 session-tracer.ts | 从 git history 恢复旧版本 |
| 删除 README.md 文件 | `Remove-Item "venv/.opencode/plugin/README.md"` 及子目录 README |
| 删除 designs/ 文档 | `Remove-Item "vaults/vault-demo/wiki/designs/opencode-plugin-tool-schema-architecture-*.md"` |
| 恢复 wiki/README.md | 从 git history 恢复 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-10-162736 |
| **更新人** | OpenCode Agent Session |
| **变更触发** | session-tracer.ts 验证缺陷 → Tool Schema 分层架构设计 |
| **下次修订条件** | 重启验证结果、tool-verify-demo.ts 开发、schema 版本升级 |
| **跨环境迁移参考** | 复制 `tool-schemas/*.ts` + `session-tracer.ts` + 按「验证清单」逐条执行 |


*文档生成时间：2026-08-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
