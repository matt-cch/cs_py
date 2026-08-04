---
title: env-migration 与 handoff 分类边界 mdc 新建
description: 新建 env-migration-handoff-classification.mdc 规则文件，明确分类边界与完整记录义务，并同步更新两个高频任务 mdc 的引用
date: 2026-08-04
meta:
  version: 1.0.0
---

# env-migration-handoff-classification-mdc-2026-08-04-120622

> **Session 阶段性记录说明**：本 env-migration 为单次 session 内的**阶段性记录**，接续上一份 `env-migration-vaultroot-default-remove-2026-08-04-113406.md`。记录范围为：上一份 env-migration 落盘之后，session 继续产生的非 handoffs 变更。

## 元信息

| 字段 | 值 |
|------|---------|
| **Session 主题** | 新建 env-migration-handoff 分类边界规则 + 完整记录义务固化 |
| **日期** | 2026-08-04 |
| **文件名时间戳** | `2026-08-04-120622` |
| **触发原因** | 用户要求新建 mdc 明确 env-migration 与 handoff 分类边界；随后纠偏要求补充"完整记录义务" |
| **影响范围** | `.cursor/rules/` 下 1 个新建 mdc + 2 个既有 mdc 修改 |
| **风险等级** | 低 |


## 一、文本文件变更清单

### 1. 新建 `.cursor/rules/env-migration-handoff-classification.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/env-migration-handoff-classification.mdc` |
| **变更类型** | `新建` |
| **内容摘要** | 明确 env-migration 与 handoff 的分类边界，含速查表、判别逻辑、触发条件索引 |
| **核心规则** | handoff = `apps/` 或 `docs/projects/<project>/` 下的项目交付；其余全部 = env-migration |
| **lint 验证** | `run-lint.py` — 通过 |

### 2. 修改 `.cursor/rules/high-frequency-env-migration.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-env-migration.mdc` |
| **变更类型** | `修改` |
| **修改内容** | 顶部追加引用说明：`> **分类边界**：本文档只定义"怎么记 env-migration"。变更该记 env-migration 还是 handoff，见 .cursor/rules/env-migration-handoff-classification.mdc。` |
| **lint 验证** | `run-lint.py` — 通过 |

### 3. 修改 `.cursor/rules/high-frequency-project-handoff.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-project-handoff.mdc` |
| **变更类型** | `修改` |
| **修改内容** | 顶部追加引用说明：`> **分类边界**：本文档只定义"怎么记 handoff"。变更该记 env-migration 还是 handoff，见 .cursor/rules/env-migration-handoff-classification.mdc。` |
| **lint 验证** | `run-lint.py` — 通过 |


## 二、非文本操作

本次阶段**不涉及**文件系统变更、缓存迁移、目录创建或环境变量修改。


## 三、Session 踩坑与纠偏记录（本阶段）

| # | 失误 | 根因 | 用户纠偏 |
|---|------|------|---------|
| 1 | 新建的 mdc 未包含"完整记录义务" | 只写了分类边界速查表，遗漏了用户刚刚强调的核心约束 | "你补充进这个 mdc" → 用户进一步澄清是"不要遗漏的注意义务" |

### 纠偏后补充的内容

在 `env-migration-handoff-classification.mdc` 中新增"完整记录义务（硬性）"章节，明确：
- 时间线覆盖（禁止只记最后一步）
- 非文本操作逐条登记
- 踩坑与纠偏如实记录
- 产物路径全部列出
- 禁止为套用模板裁剪事实

违规后果标注为**文档交付事故**。


## 四、环境变量速查

无新增或修改的环境变量。


## 五、落盘验证

| 文件 | 验证工具 | 结果 |
|------|---------|------|
| `env-migration-handoff-classification.mdc` | `run-lint.py` | ✅ 通过 |
| `high-frequency-env-migration.mdc` | `run-lint.py` | ✅ 通过 |
| `high-frequency-project-handoff.mdc` | `run-lint.py` | ✅ 通过 |


## 六、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认新建 mdc 存在 | `Test-Path .cursor/rules/env-migration-handoff-classification.mdc` | `True` |
| 2 | 确认分类边界引用已追加 | `grep "env-migration-handoff-classification.mdc" .cursor/rules/high-frequency-env-migration.mdc` | 有匹配 |
| 3 | 确认 handoff mdc 也已追加引用 | `grep "env-migration-handoff-classification.mdc" .cursor/rules/high-frequency-project-handoff.mdc` | 有匹配 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-04-120622 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求新建分类边界 mdc → 纠偏补充完整记录义务 |
| **下次修订条件** | 当分类边界需要扩展（如新增例外场景），或完整记录义务需要补充新约束时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
| **与上一份 env-migration 的关系** | 接续 `env-migration-vaultroot-default-remove-2026-08-04-113406.md`，同属单次 session 的阶段性记录 |


*文档生成时间：2026-08-04*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
