---
title: env-migration — 真源检测触发链路从 AGENTS.md 迁移到 .mdc 规则文件
description: 将高频任务"真源检测"的触发词映射从 AGENTS.md 迁移至 .cursor/rules/*.mdc，验证 .mdc 的 alwaysApply 与 AGENTS.md 的触发等价性。
date: 2026-06-05
---

# `env-migration-verify-runtime-trigger-migration-2026-06-05-094059.md`

> **文档性质**：环境迁移指南。聚焦 AGENTS.md 与 .cursor/rules/*.mdc 的指令架构调整。  
> **受众**：Human + Agent。理解项目级约束（AGENTS.md）与领域级约束（.mdc）的等价性，以及高频任务的最佳落点。


## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 真源检测触发链路从 AGENTS.md 迁移到 .mdc 规则文件 |
| **日期** | 2026-06-05（frontmatter；文件名时间戳见下表） |
| **文件名时间戳** | `2026-06-05-094059`（与磁盘文件名后缀一致） |
| **触发原因** | 验证 .mdc 与 AGENTS.md 的高频任务触发效果是否等价；避免 AGENTS.md 过度膨胀 |
| **影响范围** | AGENTS.md 内容裁减、新增 .mdc 规则文件、config.json 加载链路（无需修改） |
| **风险等级** | 低（仅影响指令组织方式，不涉及业务代码或运行时工具链） |


## 一、文本文件变更清单

### 1. 新建 `.cursor/rules/high-frequency-verify-runtime.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-verify-runtime.mdc` |
| **变更类型** | `新建` |
| **内容来源** | 从 `venv/.opencode/AGENTS.md` 的"高频任务速查"节整段迁移 |
| **作用** | 将"真源检测"任务的触发词映射与执行路径独立为领域级约束文件 |
| **验证方式** | 重启 Agent 后发送触发词（如"跑一遍真源测试"），观察是否直接执行而不重新推理 |
| **迁移方式** | 可直接复制 `.mdc` 内容到新环境同名路径 |

**文件内容要点**：
- `alwaysApply: true`（确保常驻上下文）
- 触发词："检查真源"、"真源检测"、"verify runtime"、"跑一下 verify-runtime"
- 执行脚本：`references/runtime/verify-runtime.ps1`
- 执行后动作：读取报告 → 更新索引 → 汇报 summary


### 2. 修改 `venv/.opencode/AGENTS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | `删除` + `重新编号` |
| **删除内容** | "### 1. 检查真源 / 真源检测 / verify runtime" 整节（含触发词映射表） |
| **调整内容** | 剩余两个高频任务重新编号：env-migration → 1，handoff → 2 |
| **作用** | 避免 AGENTS.md 与 .mdc 重复挂载同一段触发映射；保持 AGENTS.md 聚焦项目级硬性约束 |
| **验证方式** | 重启 Agent 后确认 AGENTS.md 中已无真源检测任务，且 .mdc 中内容完整 |
| **迁移方式** | 新环境只需确保 `.mdc` 文件存在即可，AGENTS.md 的删减是可选清理 |


## 二、非文本操作

本次 session **不涉及**文件复制、缓存迁移、目录创建等非文本操作。


## 三、环境变量速查

无新增或变更的环境变量。`config.json` 的 `instructions` 字段已包含 `.cursor/rules/*.mdc`，无需修改即可自动加载新规则文件：

```json
"instructions": [
  "./AGENTS.md",
  ".cursor/rules/*.md",
  ".cursor/rules/*.mdc"
]
```


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 .mdc 文件存在 | `Test-Path ".cursor/rules/high-frequency-verify-runtime.mdc"` | `True` |
| 2 | 确认 AGENTS.md 已移除重复内容 | 搜索 `AGENTS.md` 中"检查真源"关键词 | 无匹配（或仅保留历史痕迹） |
| 3 | 确认触发机制生效 | 重启 Agent 后发送"跑一遍真源测试" | Agent 直接执行 `verify-runtime.ps1`，不重新推理询问 |
| 4 | 确认 config.json 加载链路 | 检查 `config.json` 的 `instructions` 是否包含 `.cursor/rules/*.mdc` | 包含 |


## 五、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 AGENTS.md 内容 | 将删除的"真源检测"节重新追加到 AGENTS.md "高频任务速查" |
| 删除 .mdc 文件 | `Remove-Item ".cursor/rules/high-frequency-verify-runtime.mdc"` |
| 重新编号 | 若恢复 AGENTS.md 内容，需将剩余任务编号恢复为原顺序 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-05-094059 |
| **更新人** | Human + Agent Session |
| **变更触发** | 验证 .mdc 与 AGENTS.md 触发等价性实验 |
| **下次修订条件** | 若验证失败（.mdc 触发不如 AGENTS.md 灵敏），需回滚并记录原因 |
| **跨环境迁移参考** | 直接复制 `.mdc` 文件 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-05*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
