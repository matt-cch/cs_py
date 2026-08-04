---
name: tool-discovery
description: 在 deploy-git-isolated 项目中帮助用户定位工具、查询脚本用法、获取正确的 entry_command。触发词：atomic-xxx 怎么调用、workflow-xxx 的用法、查一下 deploy-git-isolated 的工具、py-tools 里有什么、这个脚本怎么用。
---

# Tool Discovery — 工具发现与用法查询

## 本质

当你不确定 deploy-git-isolated 项目里**有哪些工具可用**，或者知道工具名但**不知道怎么调用**时，本 skill 帮你从项目的真源索引和脚本自说明中定位答案。

## 适用范围

仅适用于 `references/tasks/deploy-git-isolated/` 目录下的脚本资产，包括：
- `scripts/py-tools/` 下的 Workflow 和 Atomic 脚本
- `scripts/py-plugins/` 下的底座插件
- `skills/` 下的 skill 规范文件
- `references/runtime/verified-task-index.json` 中登记的全部 script/skill 类型工具

## 触发词

> **触发条件索引**：本文档中的触发条件受 `verified-trigger-index.json` 统一管理。
> 索引真源：`${devroot}/references/runtime/verified-trigger-index.json`
> 冲突裁决与边界判断以索引中的 `conflict_domains` 和 `conflict_resolution_rules` 为准。

### 正面触发（T）

| 场景 | 触发词 | 说明 |
|------|--------|------|
| **T001 — 场景工具查询** | "用什么工具做"、"这个该用什么脚本"、"查一下 deploy-git-isolated 的工具"、"py-tools 里有什么"、"找一下工具" | 用户想找一个功能对应的工具 |
| **T002 — 单工具用法查询** | "`atomic-git-push-smoke` 怎么调用"、"`workflow-deploy-full` 的用法是什么"、"`gh-pr-create` 的参数"、"这个脚本的入口命令" | 用户知道工具名，想知道怎么用 |
| **T003 — 工具列表查询** | "列出 deploy-git-isolated 的脚本"、"有哪些 atomic 脚本"、"workflow 脚本清单"、"task/下有什么工具"、"deploy-git-isolated 下有哪些工具"、"这个 task 里有什么工具" | 用户想获取某个类别的工具列表 |

### 排他触发（E）

| 场景 | 触发词 | 说明 |
|------|--------|------|
| **E001 — 直接执行具体任务** | "执行真源检测"、"记一版 version"、"下载 opencode" | 用户已明确说出具体任务名，直接命中对应 mdc/skill，不走本 skill |
| **E002 — 高频任务列表** | "有什么高频任务"、"能做什么"、"帮助" | 命中 `mdc-task-show` 领域，展示高频任务速查卡 |

## 工作流

### Step 1: 判断用户意图

- 若用户说了**具体脚本名**（如 `atomic-git-push-smoke.py`）→ 走 **T002 单工具查询**
- 若用户描述了**功能/场景**（如"怎么安全 push"）→ 走 **T001 场景查询**
- 若用户要求**列表**（如"有哪些 workflow 脚本"）→ 走 **T003 列表查询**

### Step 2: 检索真源索引（第一优先）

用 `rg`（ripgrep）在 `verified-task-index.json` 中搜索：

```powershell
& "${devroot}\venv\ripgrep\rg.exe" -i -C 2 "<关键词>" "${devroot}\references\runtime\verified-task-index.json"
```

检索目标：
- `available_scripts_and_tools` 中的 `name`、`description`、`typical_scenarios`
- `entry_command` 字段
- `path_exists` 和 `verified_at` 字段

### Step 3: 检索脚本自说明（第二优先）

用 `rg` 在脚本 README 中搜索：

```powershell
& "${devroot}\venv\ripgrep\rg.exe" -i -C 2 "<关键词>" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\README.md"
& "${devroot}\venv\ripgrep\rg.exe" -i -C 2 "<关键词>" "${devroot}\references\tasks\deploy-git-isolated\scripts\README.md"
```

### Step 4: 检索脚本 docstring（第三优先）

用 `rg` 在 Python 脚本文件中搜索模块注释：

```powershell
& "${devroot}\venv\ripgrep\rg.exe" -i -A 15 "<关键词>" --type py "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\"
& "${devroot}\venv\ripgrep\rg.exe" -i -A 15 "<关键词>" --type py "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\"
```

docstring 检索重点字段：
- 【意图】— 为什么存在这个脚本
- 【职责】— 具体做什么
- 【用法】— 命令行参数
- 【示例】— 典型调用

### Step 5: 检索 skill 文档（第四优先）

用 `rg` 在 skills/ 目录搜索：

```powershell
& "${devroot}\venv\ripgrep\rg.exe" -i -C 2 "<关键词>" "${devroot}\references\tasks\deploy-git-isolated\skills\"
```

### Step 6: 组织回答

按优先级输出：

1. **工具名** + `path_exists` 状态
2. **entry_command**（可直接复制执行的命令）
3. **description**（一句话职责）
4. **verified_at**（最后验证时间）
5. **docstring 摘要**（意图 + 职责 + 关键参数）

## rg 参数速查

| 场景 | 推荐参数 | 原因 |
|------|---------|------|
| JSON 索引检索 | `-i -C 2` | 上下文 2 行，适合 JSON 字段 |
| Markdown 导航 | `-i -C 3` | 上下文 3 行，适合表格和列表 |
| Python docstring | `-i -A 15 --type py` | 后 15 行，覆盖多行注释 |
| skill 文档 | `-i -C 2` | 标准 Markdown 上下文 |

## 禁止行为

1. **禁止裸搜文件名**：不先用 `glob **/atomic-*.py` 推断工具列表，文件名不能反映真实职责。
2. **禁止跳过索引**：不先查 `verified-task-index.json` 就直接去读脚本文件。
3. **禁止泛化回答**：用户问具体工具时，必须给出准确的 `entry_command`，不能只说"在 py-tools 里"。
4. **禁止覆盖具体任务**：用户已明确说"执行真源检测"时，直接命中对应 mdc，不走本 skill。

## 回写索引义务

本 skill 触发后，若发现 `verified-task-index.json` 中存在未登记的脚本、或脚本信息已过期，必须向用户报告，并建议更新索引。

## 关联文档

- 真源索引：`${devroot}/references/runtime/verified-task-index.json`
- 触发条件索引：`${devroot}/references/runtime/verified-trigger-index.json`
- 脚本导航：`${devroot}/references/tasks/deploy-git-isolated/scripts/py-tools/README.md`
- 框架规范：`${devroot}/references/tasks/deploy-git-isolated/baseline/baseline-index.md`
