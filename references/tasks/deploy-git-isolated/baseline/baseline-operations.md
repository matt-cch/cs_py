---
title: deploy-git-isolated — 修订联动、执行路径与版本演进
description: 修订联动规则、Agent vs Human 执行路径对照、版本语义与归档机制、Changelog 记录规范。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 修订联动、执行路径与版本演进

## 4. 修订联动规则

当 task 目录发生以下变更时，必须同步更新关联文件：

| 触发条件 | 必须联动 | 更新内容 |
|---------|---------|---------|
| 新增/修改骨架脚本（`skeleton/*.py`） | `scripts/*.ps1` | 新增或更新对应调用脚本 |
| 新增/修改任何脚本 | `SOP.md` | 新增/修改 Step 契约（Input/Output/Validation） |
| 新增/修改任何脚本 | `EXEC-CHEATSHEET.md` | 新增/修改对照命令块 |
| 新增/重命名脚本 | `TASK-TOOLS-INDEX.md` | 更新本地脚本清单 |
| 发现外部通用工具可替代本 task 功能 | `TASK-TOOLS-INDEX.md` | 在外部引用节追加，更新边界矩阵 |
| 变更 `active_scripts[].status` | `ENTRY.json` | 同步状态字段 |
| 新增踩坑 | `gotchas/*.md` + `DESIGN.md` 第 7 章 | 记录现象/根因/修复 |
| 里程碑完成 | `changelog/` | 追加条目 |
| 新增/修改 trigger | `task-scenario-triggers.json` + 全局 `verified-trigger-index.json` | 同步登记 |


## 5. Agent vs Human 执行路径

### 5.1 Agent 调用

```
1. 读取 ENTRY.json 确认当前入口、脚本状态、Step Manifest
2. 读取 TASK-TOOLS-INDEX.md 判断「该用哪个工具、有没有现成轮子」
3. 读取 SOP.md 确认当前 Step 的 Input/Output/Validation 契约
4. 读取 EXEC-CHEATSHEET.md 获取具体命令格式
5. 通过 bash 调用：& "<abs-path>" <args>
6. 执行后按 SOP.md Validation 规则验收，更新 ENTRY.json step_manifests 状态
```

### 5.2 Human 调用

```
1. 查看 README.md 了解任务总览
2. 查看 GOAL.md 理解 Stage 路线图与成功标准
3. 查看 TASK-TOOLS-INDEX.md 了解本 task 有哪些工具、边界在哪
4. 查看 SOP.md 确认流程与验收条件
5. 查看 EXEC-CHEATSHEET.md 复制具体命令
6. 在 VS Code/Cursor 终端内粘贴执行（相对路径格式）
7. 如需了解设计决策，阅读 DESIGN.md
```

### 5.3 核心差异

| 维度 | Agent | Human |
|------|-------|-------|
| 路径风格 | 绝对路径 `${devroot}\...` | 相对路径 `.\references\...` |
| 执行前缀 | `powershell -ExecutionPolicy Bypass -File` | `Set-ExecutionPolicy -Scope Process ...;` |
| 信息来源 | ENTRY.json（机器） | README.md + GOAL.md + SOP.md + EXEC-CHEATSHEET.md + TASK-TOOLS-INDEX.md（人类） |
| 状态追踪 | 自动更新 ENTRY.json | 手动阅读 README.md 待办 |


## 7. 版本演进与归档机制

### 7.1 版本语义

Task 采用 **SemVer-like** 三段式版本号：`MAJOR.MINOR.PATCH`

| 段位 | 递增条件 | 示例 |
|------|---------|------|
| **MAJOR** | 架构级重构、目录结构重排、职责边界变更 | `v1.x → v2.0` |
| **MINOR** | 新增功能/脚本、新增 Step、扩展配置、新增工具索引 | `v1.0 → v1.1` |
| **PATCH** | 修复、文档更新、状态变更（ready/pending）、真源刷新 | `v1.0.0 → v1.0.1` |

### 7.2 版本登记位置

| 文件 | 字段 | 说明 |
|------|------|------|
| `README.md` | 文末 `*任务版本: vX.Y.Z*` | 人类速览当前版本 |
| `ENTRY.json` | `meta.version` | 机器读取的真源版本 |
| `ENTRY.json` | `meta.version_history[]` | 演进历史记录 |
| `changelog/*.md` | 文件名含日期/版本 | 详细变更内容 |

### 7.3 演进示例（ENTRY.json）

```json
{
  "meta": {
    "version": "0.4.0",
    "version_history": [
      {"version": "0.1.0", "date": "2026-06-16", "note": "骨架创建，设计冻结"},
      {"version": "0.2.0", "date": "2026-06-16", "note": "Step 1-8 执行通过，插件架构就绪"},
      {"version": "0.3.0", "date": "2026-06-16", "note": "新增 task-scenario-triggers.json 触发真源"},
      {"version": "0.4.0", "date": "2026-06-16", "note": "拆分 TASK-TOOLS-INDEX.md，命令速查精简为纯执行命令"}
    ]
  }
}
```

### 7.4 Changelog 记录规范

> **共识来源**：用户与 Agent 在 2026-06-16 对话中共同确认。禁止自由发挥，必须按本格式记录。

#### 7.4.1 记录时机

- 任何对 task 文件的实质性修改（新增、重构、修复）完成后，必须立即记录 changelog
- 禁止「先改代码，等有空再补 changelog」—— changelog 是修改的**必要组成部分**

#### 7.4.2 文件格式

- **命名**：`changelog-YYYY-MM-DD-<slug>.md`（kebab-case slug，简短可识别）
- **位置**：`references/tasks/<task-name>/changelog/`
- **Frontmatter**：必须含 `title`、`description`、`date`

#### 7.4.3 正文结构（强制）

| 章节 | 是否强制 | 说明 |
|------|---------|------|
| **变更概览** | ✅ | 表格：类型、影响范围、风险等级、触发原因 |
| **变更时间线** | ✅ | 表格：变更项、之前、之后、触发原因 |
| **验证结果** | ✅ | 表格/列表：逐项确认（lint、执行、扫描等） |
| **已知问题** | 有则必填 | 本次变更暴露的待优化项，不可隐瞒 |
| **关联文件** | ✅ | 哪些文件被修改，状态标记 |

#### 7.4.4 禁止行为

- ❌ **禁止自由发挥**：不写「变更概览」直接罗列修改；不写「验证结果」直接声称「已验证」
- ❌ **禁止无时间线**：changelog 文件名和正文中都必须有明确的日期标识
- ❌ **禁止无触发原因**：每个变更项必须说明「为什么改」，不能只写「改了什么」
- ❌ **禁止隐瞒已知问题**：如果用户指出了缺陷或待优化方向，必须在「已知问题」中如实记录

#### 7.4.5 示例

见 `changelog/changelog-2026-06-16-git-isolated-devroot-probing.md`


### 7.5 归档机制

> **自包含原则**：每个 task 的归档历史存放在自身的 `archive/` 子目录下，不集中到 `references/tasks/` 根目录，方便 task 内直接检索。

**触发条件**：
- Task 进入长期冻结（6 个月无活跃变更）
- MAJOR 版本升级（架构重构），旧版本保留历史
- 人类明确指令「归档此 task」

**归档路径**：
```
references/tasks/deploy-git-isolated/archive/deploy-git-isolated-vN/
```

**归档内容**：
- 完整复制 task 根目录所有文件（保留历史真源）
- 归档目录内的 `README.md` 顶部标注 `**已归档**` + 归档日期 + 替代版本路径
- 原 `references/tasks/deploy-git-isolated/` 继续承载当前版本

**归档后当前版本处理**：
- 当前版本的 `README.md` 中增加「历史版本」导航链接
- `ENTRY.json` 的 `meta.archived_versions` 记录归档路径


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
