---
title: py-tools 原子型与编排型 Workflow 区分模式
description: 记录 py-tools/ Layer 3 内部的两种形态——原子型（可被上层引用）与编排型（完整剧本，不被引用），以及何时配 JSON、何时不配的设计决策。
date: 2026-06-21
meta:
  version: 1.0.0
---

# py-tools 原子型与编排型 Workflow 区分模式

> **来源**：用户与 Agent 在 2026-06-21 对话中共同确认。本节记录 py-tools/ Layer 3 内部的两档形态差异，以及配套 JSON 配置的外化决策逻辑。


## 1. 问题背景

`scripts/py-tools/` 目录下的脚本**全部属于 Layer 3（Workflow 编排层）**，但它们的形态和引用方式截然不同：

- `get-timestamp.py` 是一个**原子工具**，只干一件事（输出格式化时间），但可以被各种上层 workflow 引用
- `workflow-deploy-full.py` 是一个**编排剧本**，串联 6 个步骤，自己就是顶层入口
- `run-lint.py` 介于两者之间，既可直接执行，也可被 CI workflow 引用

如果不对这两种形态做明确区分，会导致：
1. **错误引用**：把编排型 workflow 当积木拼装，造成流程嵌套混乱
2. **过度配置**：给原子型工具配不必要的 JSON，增加维护负担
3. **配置遗漏**：该外化的编排配置硬编码在脚本里，后续调整必须改代码


## 2. 两档形态定义

### 2.1 原子型 Workflow（Atomic Tool）

**定义**：封装单一原子操作，输入明确、输出标准化、无副作用（或副作用可控），可被上层 Workflow 作为子命令调用。

**特征**：
- 职责单一，不干第二件事
- 输出格式稳定（如 JSON、key=value、纯文本），下游可稳定消费
- 不依赖复杂的步骤编排上下文
- 通常不产生不可逆副作用（如不写磁盘、不改状态），或副作用在调用方可控范围内

**本 task 范例**：

| 工具 | 职责 | 被引用场景 |
|------|------|-----------|
| `get-timestamp.py` | 输出格式化时间字符串 | 任何需要写入 `date:` / `verified_at:` 的 workflow |
| `run-lint.py` | 聚合 lint 插件输出结果 | CI 流程中在构建前调用 |
| `fetch_issue.py` | 获取 GitHub Issue 内容 | 报告生成 workflow 中拉取数据 |
| `check-links.py` | 验证 Markdown 内部链接 | 文档发布前检查 |
| `screenshot_verifier.py` | 对 URL 截图 | 前端验证 workflow 中调用 |

**调用方式**：通过 `subprocess.run()` 作为外部命令调用，保持层间隔离：

```python
# 上层 workflow 中调用原子型工具
ts_proc = subprocess.run(
    [python_exe, get_timestamp_py, "--format", "local_iso"],
    capture_output=True, text=True, encoding="utf-8"
)
timestamp = ts_proc.stdout.strip()
```

**JSON 配置需求**：通常 **不配**。原子型工具是参数驱动的（`--format`、`--source` 等），配置项少且变动低频。

### 2.2 编排型 Workflow（Orchestration Script）

**定义**：串联多个步骤的完整流程，面向 Agent 或终端用户的**顶层入口**，自身就是剧本，不往下被其他 Workflow 引用。

**特征**：
- 包含 ≥2 个有依赖关系的步骤
- 有明确的步骤顺序、失败处理、回滚路径
- 面向「完成一个完整目标」而非「提供一个原子能力」
- 通常包含不可逆副作用（如 git push、文件压缩）

**本 task 范例**：

| 工具 | 职责 | 步骤数 |
|------|------|--------|
| `workflow-deploy-full.py` | add → commit → remote → push → upstream → issue sync | 6 |
| `workflow-lint-amend-lint.py` | 检测 → 修复 → 验证闭环 | 3 |
| `archive_project.py` | scan → compress → verify | 3 |

**调用方式**：直接被 Agent / 人类调用，不被其他 Workflow 引用：

```powershell
# Agent 直接调用编排型 workflow
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx"
```

**JSON 配置需求**：当步骤列表/顺序/策略可能变动时，**必须外化**。

| 工具 | 是否已配 JSON | 原因 |
|------|-------------|------|
| `archive_project.py` | ✅ `archive-groups.json` | 分组策略和黑白名单经常调整 |
| `workflow-deploy-full.py` | ❌ 当前硬编码 | 步骤顺序可能调整，建议外化 |
| `workflow-lint-amend-lint.py` | ❌ 不配 | 三步闭环固定，策略选项少（2个） |


## 3. JSON 配置外化决策逻辑

什么场景下编排型 Workflow 需要配 JSON？四个条件，满足任一即配：

### 条件一：数据会变，代码不想变

> **判断标准**：配置的修改频率高于代码的修改频率。

| 范例 | 分析 |
|------|------|
| `archive-groups.json` ✅ | 归档分组和黑白名单经常调整，但扫描逻辑不需要跟着改 |
| `workflow-deploy-full.py` ⚠️ | 当前硬编码 6 步，如果以后要"跳过 issue sync"或"插入新步骤"，就得改代码 |

### 条件二：多工具共享同一套数据

> **判断标准**：同一配置被 ≥2 个工具消费，且需要保持一致。

| 范例 | 分析 |
|------|------|
| `archive-groups.json` ✅ | `archive_cs_py.py`、`archive_venv.py`、`archive_project.py` 共享同一套分组定义 |
| `py-sort-rules.json` ✅ | 所有通过 `py_lib.load_plugins()` 加载的工具共享插件拓扑 |

### 条件三：机器需要动态消费（Agent/脚本决策）

> **判断标准**：Agent 或其他脚本需要读取配置做"用哪个工具"的决策。

| 范例 | 分析 |
|------|------|
| `py-sort-rules.json` ✅ | `run-lint.py` 按扩展名路由到插件时需要知道 `.mdc` → `md_lint` |
| `archive-groups.json` ✅ | `archive_scanner.py` 需要知道 cs_py 分组排除 `venv/` |

### 条件四：枚举型/映射型数据

> **判断标准**：配置内容是"列表、映射、策略选项"而非"开关、路径、数值"。

| 类型 | 需要 JSON？ | 范例 |
|------|-----------|------|
| 步骤列表/工作流定义 | ✅ | deploy 的 Step 顺序 |
| 插件路由表 | ✅ | `.json` → `lint_json` |
| 白名单/黑名单 | ✅ | archive 黑白名单 |
| 单一路径/数值 | ❌ | `--devroot`、`--issue-number` |
| 策略枚举（仅 2-3 个选项） | ❌ | lint-amend-lint 修复策略只有 delete/replace_stars |


## 4. 层级关系总图

```
┌──────────────────────────────────────────────────────────────────┐
│  Layer 3a: 编排型 Workflow（不被引用，顶层入口）                │
│  ────────────────────────────────────────────────────────────   │
│  workflow-deploy-full.py    → add→commit→push→upstream→issue  │
│  archive_project.py         → scan→compress→verify             │
│  workflow-lint-amend-lint.py → detect→fix→re-verify            │
│  （完整剧本，面向 Agent / 人类；不往下被引用）                  │
└──────────────────────────────────────────────────────────────────┘
                           ↑ 被调用
┌──────────────────────────────────────────────────────────────────┐
│  Layer 3b: 原子型 Workflow（可被上层引用，CLI 积木）            │
│  ────────────────────────────────────────────────────────────   │
│  get-timestamp.py           → 输出时间戳                        │
│  run-lint.py                → 聚合 lint 结果                    │
│  fetch_issue.py             → 获取 Issue 内容                   │
│  check-links.py             → 验证链接                          │
│  screenshot_verifier.py     → URL 截图                          │
│  （单一职责，输出标准化；可被 Layer 3a 或跨 task workflow 引用）│
└──────────────────────────────────────────────────────────────────┘
              ↓ 通过 subprocess.run() / CLI 调用（层间隔离）
┌──────────────────────────────────────────────────────────────────┐
│  Layer 2: 统一入口层（py_lib.py）                               │
│  读取 py-sort-rules.json → 拓扑排序 → 加载 Plugins              │
└──────────────────────────────────────────────────────────────────┘
              ↓ 动态加载
┌──────────────────────────────────────────────────────────────────┐
│  Layer 1: 能力底座层（py-plugins/）                             │
│  timestamp.py · time_source.py · lint_json.py · github_api.py  │
└──────────────────────────────────────────────────────────────────┘
```


## 5. 铁律

1. **编排型 Workflow 禁止被其他 Workflow 引用**。它是完整剧本，引用会导致流程嵌套混乱。
2. **原子型 Workflow 通过 subprocess 调用，禁止 import**。保持层间隔离，输出格式标准化即可。
3. **JSON 配置只给"数据会变、代码不想变"的场景配**。原子型工具通常参数驱动即可，不配 JSON。
4. **步骤列表硬编码是技术债**。编排型 Workflow 的步骤顺序如果可能调整，应外化为 JSON。


## 6. 关联文件

| 文件 | 说明 |
|------|------|
| `task-canonical-baseline.md` 第 8.4 节 | 三层 + 配置契约基础定义 |
| `TASK-TOOLS-INDEX.md` 第 1.3 节 | get-timestamp 用法速查 |
| `py-sort-rules.json` | 插件注册与依赖图真源 |
| `archive-groups.json` | JSON 外化配置范例 |
