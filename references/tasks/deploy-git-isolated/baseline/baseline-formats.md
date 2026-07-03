---
title: deploy-git-isolated — 文件格式规范
description: SOP.md / EXEC-CHEATSHEET.md / TASK-TOOLS-INDEX.md / ENTRY.json / DESIGN.md 的格式模板、强制规则与互斥边界。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 文件格式规范

## 3.1 SOP.md（标准操作流程）

> **核心原则**：每个 Step 定义 **Input → Process → Output → Validation** 四元契约，支持 Ralph Loop 自闭环追踪审计。

### 格式模板

```markdown
### Step N: 步骤名称

| 契约项 | 定义 |
|--------|------|
| **Input** | 预期输入条件（环境变量、前置步骤、文件状态） |
| **Process** | 执行过程描述（调用哪个脚本、关键操作） |
| **Output** | 预期输出（文件、日志、返回值） |
| **Validation** | 验收条件（通过标准、失败标准） |
| **Audit Trail** | 执行记录（状态、日志路径、产物清单） |
| **Rollback** | 回滚路径（失败时如何恢复） |
```

### 强制规则

1. **输入可预期**：不满足 Input 条件不得执行
2. **输出可验证**：必须通过 Validation 后才可进入下一步
3. **过程可追踪**：执行后必须留下 Audit Trail（状态、日志、产物）
4. **失败可回滚**：每个 Step 必须定义 Rollback 路径
5. **禁止混杂命令细节**：SOP 只管「流程是什么、怎么验收」，不管「命令怎么敲」。命令细节见 `EXEC-CHEATSHEET.md`。
6. **禁止混杂工具索引**：SOP 只管「标准流程」，不管「有什么工具、边界在哪」。工具索引见 `TASK-TOOLS-INDEX.md`。


## 3.2 EXEC-CHEATSHEET.md（执行速查表）

> **核心原则**：涵盖命令、配置、参数等所有可执行/可操作内容，不限定于命令行格式。Agent/人类/终端共享同一真源。

### 格式模板

```markdown
## Stage SX: 阶段名称（Step N-M）

### Step N: 步骤名称

**Agent:**
```powershell
& "${devroot}\...\script.ps1" <args>
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\...\script.ps1 <args>
```

> 前置：`.env` 中已配置 `XXX`
```

### 强制规则

1. **真源唯一**：速查表中所有命令指向 `scripts/` 下的同一 `.ps1` 文件，Agent/人类/终端共享。
2. **上下对照**：每个功能区块内先写 Agent 格式，紧接写终端格式，用 `---` 分隔不同功能。
3. **变量约定**：Agent 格式使用 `${devroot}` 等变量；终端格式使用相对路径 `.\references\...`。
4. **执行策略**：Agent 使用 `&` 调用操作符；终端用 `Set-ExecutionPolicy -Scope Process ...;` 前缀。
5. **禁止表格罗列命令**：速查表的主体是**对照代码块**，不是表格。
6. **禁止混杂流程说明**：EXEC-CHEATSHEET 只管「命令怎么执行」，不管「流程是什么、怎么验收」。流程说明见 `SOP.md`。
7. **禁止混杂工具索引**：EXEC-CHEATSHEET 只管「命令怎么执行」，不管「有什么工具、边界在哪」。工具索引见 `TASK-TOOLS-INDEX.md`。


## 3.3 TASK-TOOLS-INDEX.md（工具索引表）

> **核心原则**：回答「这个 task 有什么工具？在哪里？什么时候用？边界是什么？」。
> **与 EXEC-CHEATSHEET 的本质区别**：EXEC-CHEATSHEET 面向「执行者」（知道要做什么，想知道怎么敲命令）；TOOLS-INDEX 面向「规划者」（想知道有哪些能力、该调哪个工具、是否已有现成轮子、能否用外部通用工具替代）。

### 必须包含的章节

1. **本地专属脚本清单**：按职责分类（部署流水线 / 安全检查 / 通用包装器 / 共享库），每项含 `脚本名 | 职责 | 典型场景 | 状态`
2. **外部通用工具引用**：明确列出本 task 可能用到的 `runtime/`、`schema/tool/` 下的通用工具，每项含 `工具名 | 全局路径 | 登记索引 | 本 task 中的用途 | 边界说明`
3. **边界矩阵**：8+ 个典型场景的首选工具、次选/备选、禁止行为
4. **速查命令**：本地脚本 + 外部通用工具的典型调用命令

### 强制规则

1. **禁止重复造轮子**：外部已存在且已登记的工具（如 `lint-json.py`、`lint-ps1.ps1`、`check-file-encoding.ps1`），必须在「外部通用工具引用」中列出，并在「边界矩阵」中规定「禁止自行实现同类功能」。
2. **铁律声明**：外部工具引用节必须包含一句铁律——「以上工具已存在且已登记，本 task 禁止自行实现同类功能。新增需求时先查 `verified-task-index.json` → `available_scripts_and_tools`。」
3. **关联文件导航**：底部必须列出与本 task 相关的全部文档的「文件 | 用途」对照表。


## 3.4 SOP vs EXEC-CHEATSHEET vs TASK-TOOLS-INDEX 对比总结

| 对比维度 | SOP.md | EXEC-CHEATSHEET.md | TASK-TOOLS-INDEX.md |
|---------|--------|-------------------|---------------------|
| **核心问题** | 「流程是什么、怎么验收？」 | 「命令怎么执行、参数怎么填？」 | 「有什么工具、边界在哪？」 |
| **内容形式** | Step 契约表格（Input/Process/Output/Validation） | Agent/终端双格式代码块 | 表格清单 + 边界矩阵 + 引用链路 |
| **是否含外部工具** | ❌ 否 | ❌ 否（只含本 task 脚本调用） | ✅ **是**（必须引用 runtime/ 和 schema/tool/ 通用工具） |
| **读者角色** | 流程设计者（确认边界与验收） | 执行者（复制粘贴命令） | 规划者（选择工具、判断边界） |
| **更新时机** | 新增/修改 Step、变更验收条件时 | 新增/修改脚本命令时 | 新增/删除工具、发现外部通用工具可替代时 |
| **典型错误** | 把命令细节塞进来 | 把流程说明塞进来 | 把命令执行细节塞进来 |

> **一句话区分**：SOP 是「流程契约」，EXEC-CHEATSHEET 是「执行手册」，TOOLS-INDEX 是「能力地图」。


## 3.5 ENTRY.json

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `meta.description` | string | task 一句话描述 |
| `meta.last_updated` | string | 最后更新日期 `YYYY-MM-DD` |
| `meta.source_of_truth` | string | 人类权威文档路径（通常是 `DESIGN.md`） |
| `meta.trigger_index` | string | 触发条件真源路径（`task-scenario-triggers.json`） |
| `meta.tools_index` | string | 工具索引路径（`TASK-TOOLS-INDEX.md`） |
| `current_workflow.entry_script` | string | 统一入口脚本名 |
| `current_workflow.usage` | string | 典型调用示例 |
| `active_scripts` | array | 活跃脚本清单，每项含 `name`、`role`、`path`、`status` |
| `active_scripts[].status` | string | `pending` / `ready` / `deprecated` |
| `design_doc` | string | DESIGN.md 路径 |
| `sop` | string | **SOP.md 路径**（标准流程） |
| `cheatsheet` | string | **EXEC-CHEATSHEET.md 路径**（执行速查） |
| `changelog_dir` | string | changelog 目录路径 |
| `gotchas_dir` | string | gotchas 目录路径 |

### `sop`、`cheatsheet` 与 `tools_index` 字段语义

- `sop`：指向**标准操作流程**（SOP.md），回答「流程是什么、怎么验收」。
- `cheatsheet`：指向**执行速查表**（EXEC-CHEATSHEET.md），回答「命令怎么执行」。
- `tools_index`：指向**工具索引表**（TASK-TOOLS-INDEX.md），回答「有什么工具、边界在哪」。
- 三者互补，不可互相替代。`ENTRY.json` 必须同时登记三者。


## 3.6 DESIGN.md

- 必须包含「背景」「设计决策」「目标目录结构」「SOP」「踩坑记录」章节。
- 设计决策必须记录「问题 → 方案 → 效果」三步。
- SOP 章节必须与 `SOP.md` 内容一致，但可更详细（含解释性文字）。
- **新增**：Trigger 治理设计意图（第 6 节），记录 trigger 体系的六维元原则（治理、参照、边界、协调、审计、重建）。


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
