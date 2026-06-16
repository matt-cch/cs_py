---
title: 插件化点源架构 — 设计决策与操作规范
description: 记录 github-lib.ps1 + lib-sort-rules.json + lib-plugins/ 三层架构的设计理由、实现逻辑与扩展操作要求。
date: 2026-06-16
---

# 插件化点源架构 — 设计决策与操作规范

> **适用范围**：`references/tasks/deploy-git-isolated/scripts/` 下的共享库体系。  
> **阅读对象**：未来需要新增插件、修改加载顺序或维护本架构的 Agent / Human。  
> **版本**：v1.0（与 task-canonical-baseline.md 对齐）

---

## 1. 背景与问题

### 1.1 原始方案及其缺陷

早期 `github-lib.ps1` 是**单体脚本**（~250 行），把所有共享函数塞进一个文件：

- **编码函数**（Switch-ToUtf8 / Restore-Encoding）
- **项目常量**（$devroot / $gitExe）
- **配置读取**（Read-EnvConfig）
- **Git 检查**（Get-GitTrackedFiles / Invoke-GitSafetyCheck）

**问题**：
- 文件过大，维护困难
- 新增功能时改大文件，风险集中
- 无加载顺序控制，依赖关系隐式埋藏在代码顺序中

### 1.2 第一次迭代：数字前缀排序

拆分为子模块，用文件名数字前缀控制加载顺序（`00-core.ps1`、`01-encoding.ps1`...）。

**问题**：
- 文件名承担排序职责，语义被污染
- 中间插入新模块时必须重命名后续所有文件
- 违反「文件名一旦确定，永不再改」的硬性原则

---

## 2. 设计决策

### 2.1 核心原则

| 原则 | 说明 |
|------|------|
| **文件名冻结** | 插件文件一旦命名，永不再改 |
| **配置与代码分离** | 排序规则用独立 JSON 文件承载，不混在代码目录 |
| **显式依赖** | 依赖关系必须在 JSON 中明文声明，禁止隐式依赖 |
| **自动加载** | 新增插件只需「放文件 + 写 JSON」，不改入口代码 |

### 2.2 三层架构

```
scripts/
├── github-lib.ps1          # 聚合入口（只读 JSON → 排序 → 循环导入）
├── lib-sort-rules.json     # 排序真源（依赖图定义）
└── lib-plugins/            # 纯代码目录（只放 .ps1）
    ├── core.ps1
    ├── encoding.ps1
    ├── constants.ps1
    ├── env-config.ps1
    └── git-checks.ps1
```

| 层级 | 职责 | 修改频率 |
|------|------|---------|
| **入口** `github-lib.ps1` | 读取 JSON → 拓扑排序 → 校验后缀 → 点源导入 | **极低**（架构稳定后不动） |
| **真源** `lib-sort-rules.json` | 定义插件列表、依赖关系、文件映射 | **渐进式**（新增插件时追加） |
| **插件** `lib-plugins/*.ps1` | 实现具体共享函数 | **按需新增** |

---

## 3. 实现逻辑

### 3.1 加载流程

```
github-lib.ps1
    ↓
读取 lib-sort-rules.json（ConvertFrom-Json）
    ↓
Invoke-TopologicalSort（Kahn 算法）
    ↓
按排序结果遍历插件
    ├── 校验：后缀必须是 .ps1
    ├── 校验：文件必须存在于 lib-plugins/
    └── 点源导入：. $filePath
    ↓
输出加载完成日志
```

### 3.2 拓扑排序（Kahn 算法）

输入：`plugins[]`（含 name / file / depends[]）

步骤：
1. 构建 `name → plugin` 哈希映射
2. 校验：所有 `depends` 必须存在于映射中（缺失则报错）
3. 构建邻接表 + 入度表
4. 队列初始化：入度为 0 的插件先入队
5. 循环出队 → 减邻接入度 → 入度为 0 则入队
6. 环检测：输出数量 ≠ 输入数量则存在环，报错

**输出**：按依赖关系排好序的插件对象数组。

### 3.3 校验层

| 校验项 | 时机 | 失败行为 |
|--------|------|---------|
| JSON 文件存在性 | 加载前 | `Write-Error` + `exit 1` |
| 依赖存在性 | 拓扑排序时 | `throw` 缺失依赖名 |
| 环检测 | 拓扑排序后 | `throw` 涉及插件名 |
| 后缀 `.ps1` | 点源导入前 | `Write-Error` + `exit 1` |
| 文件存在性 | 点源导入前 | `Write-Error` + `exit 1` |

---

## 4. 操作要求

### 4.1 新增插件（标准流程）

**Step 1**：在 `lib-plugins/` 下新建 `.ps1` 文件
- 文件名任意，**不得与已有文件同名**
- 文件内按 ps1-template 格式编写（含帮助注释、编码处理）
- **禁止**在文件名中加数字前缀排序

**Step 2**：在 `lib-sort-rules.json` 的 `plugins` 数组中追加条目

```json
{
  "name": "middleware",
  "file": "middleware.ps1",
  "depends": ["constants"],
  "description": "可选描述"
}
```

**Step 3**：如有必要，修改下游插件的 `depends` 数组

**Step 4**：执行 `github-lib.ps1` 自检，确认排序输出符合预期

> **禁止**：新建 `.ps1` 后忘记在 JSON 中登记 → 会导致插件不被加载

### 4.2 修改依赖关系

- **只允许修改 `lib-sort-rules.json`**
- **禁止重命名 `lib-plugins/` 下的任何文件**
- 修改后必须执行入口脚本验证无环

### 4.3 删除插件

- 从 `lib-sort-rules.json` 中移除对应条目
- 可选：删除 `lib-plugins/` 下的 `.ps1` 文件（或保留作为历史痕迹）
- **禁止**：只删文件不删 JSON 条目 → 会导致 `文件不存在` 报错

### 4.4 禁止行为清单

| # | 禁止行为 | 后果 |
|---|---------|------|
| 1 | 用文件名数字前缀控制排序 | 语义污染、插入困难 |
| 2 | 把 `lib-sort-rules.json` 放回 `lib-plugins/` 内 | 代码目录被非代码文件污染 |
| 3 | 在 `lib-plugins/` 下放非 `.ps1` 文件 | 后缀校验失败，加载中断 |
| 4 | 插件隐式依赖（JSON 不声明，代码里直接用） | 加载顺序不确定，运行时失败 |
| 5 | 修改 `github-lib.ps1` 的排序/加载逻辑 | 破坏架构稳定性，除非架构升级 |

---

## 5. 示例：在 env-config 和 git-checks 之间插入新插件

**场景**：新增 `middleware.ps1`，需在 `env-config` 之后、`git-checks` 之前加载。

### 操作前状态

```json
// lib-sort-rules.json（节选）
[
  { "name": "env-config", "file": "env-config.ps1", "depends": ["constants"] },
  { "name": "git-checks", "file": "git-checks.ps1", "depends": ["core", "constants"] }
]
```

### 操作步骤

1. 新建 `lib-plugins/middleware.ps1`
2. 修改 JSON：

```json
[
  { "name": "env-config", "file": "env-config.ps1", "depends": ["constants"] },
  { "name": "middleware", "file": "middleware.ps1", "depends": ["constants"] },
  { "name": "git-checks", "file": "git-checks.ps1", "depends": ["core", "middleware"] }
]
```

3. 执行入口脚本，验证输出：

```
[github-lib] 拓扑排序结果（加载顺序）：
  1. constants (constants.ps1)
  2. core (core.ps1)
  3. encoding (encoding.ps1)
  4. env-config (env-config.ps1)
  5. middleware (middleware.ps1)      ← 插入成功
  6. git-checks (git-checks.ps1)
```

**注意**：零文件重命名，`env-config.ps1` 和 `git-checks.ps1` 完全不动。

---

## 6. 与 Canonical Baseline 的关系

本架构是 `task-canonical-baseline.md` 中「脚本化 > 现写」原则的具体落地：

- **真源唯一**：`lib-sort-rules.json` 是加载顺序的唯一真源
- **渐进式确认**：新增插件后通过入口脚本日志验证排序结果
- **修订联动**：新增/修改插件时必须同步更新 JSON，并在 `changelog/` 记录

---

*文档版本: v1.0*  
*创建时间: 2026-06-16*  
*对应架构: github-lib.ps1 v1.0 + lib-sort-rules.json v1.0*
