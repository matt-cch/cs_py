---
title: deploy-git-isolated — 文件命名与主体意图表达规范
description: 规定文件名、docstring、README.md、index.json 如何协同承载主体意图，使搜索工具（rg/grep/glob）能通过文件名语义命中目标。
date: 2026-08-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 文件命名与主体意图表达规范

## 核心命题

**文件名不是附属标签，而是意图的第一载体。**

当 Agent 或用户通过 `rg`/`grep`/`glob` 搜索工具时，文件名是**最先被扫描**的信息源。如果文件名不能反映主体意图，搜索就会失效或误命中，导致 Agent 落入"凭文件名猜"的认知陷阱。

本规范定义四大意图载体的协同规则：

| 载体 | 作用 | 被谁消费 |
|------|------|---------|
| **文件名** | 主体意图的**压缩表达** | `glob`、`rg --files`、人类快速浏览 |
| **docstring** | 脚本意图的**完整展开** | `rg` 内容搜索、Agent 理解职责 |
| **README.md** | 目录意图的**导航入口** | `rg`、人类查阅、Agent 定位 |
| **index.json** | 全量意图的**聚合真源** | Agent 程序性查询、冲突裁决 |

> 铁律：**四者必须语义一致**。文件名说的、docstring 说的、README 登记的、index.json 索引的，必须是同一件事。任何不一致都视为架构层误操作。

## 1. 文件名铁律

### 1.1 文件名必须承载主体意图

文件名不是"标识符"，而是"意图的压缩包"。一个好的文件名能让搜索者在看到它的瞬间，知道**这个文件是干什么的**。

| 维度 | 规则 | 正例 | 反例 |
|------|------|------|------|
| **主体** | 文件名必须包含**动作主体**或**领域主体** | `atomic-git-push-smoke.py`（主体=git push） | `utils.py`（无主体） |
| **意图** | 文件名必须包含**核心意图** | `workflow-deploy-full.py`（意图=完整部署） | `script.py`（无意图） |
| **类型** | 文件名必须包含**文件类型/角色** | `baseline-plugin-architecture.md`（类型=基线） | `doc.md`（无类型） |

### 1.2 命名模式（按文件角色）

| 角色 | 前缀 | 示例 | 说明 |
|------|------|------|------|
| **Atomic 原子脚本** | `atomic-<领域>-<意图>.py` | `atomic-git-push-smoke.py` | 单职责，可复用 |
| **Workflow 编排器** | `workflow-<阶段>-<意图>.py` | `workflow-git-deploy-full-poly.py` | 多步骤编排 |
| **Baseline 规范** | `baseline-<主题>.md` | `baseline-human-ai-boundary.md` | 框架层规范 |
| **Env-migration** | `env-migration-<主题>-<时间戳>.md` | `env-migration-tool-discovery-skill-creation-2026-08-03-110725.md` | 环境变更记录 |
| **Skill 规范** | `<skill-name>/SKILL.md` | `tool-discovery/SKILL.md` | 技能核心规范 |

### 1.3 禁止行为

- **禁止泛化命名**：`utils.py`、`helper.py`、`script.py`、`doc.md`、`test.py` 等无法反映主体意图的文件名一律禁止。
- **禁止缩写歧义**：`wf-dep.py` 不如 `workflow-deploy-full.py` 清晰；`at-gps.py` 不如 `atomic-git-push-smoke.py` 可搜索。
- **禁止类型隐藏**：不要省略文件角色前缀（如 `git-push-smoke.py` 缺失 `atomic-` 前缀，无法被 `rg atomic-` 命中）。

## 2. docstring 铁律

### 2.1 模块注释必须自说明

Python 脚本的顶部 docstring 是文件名意图的**完整展开**。搜索工具通过 `rg -A 10` 可以命中 docstring 内容，Agent 通过读取 docstring 理解职责。

**必须包含的字段**：

```python
r"""
py-tools/atomic-git-push-smoke.py — 无弹窗安全 smoke push 原子脚本（v1.0.0）
标签：py-tools
版本：v1.0.0
日期：2026-07-21

【意图】
在自动化部署流程中，直接 `git push` 会触发 GCM 弹窗阻塞流程。本工具通过……

【职责】
  1. 从 devroot/.env 读取 PAT，构造认证 URL
  2. 阻断 GCM 弹窗
  3. 双路 preflight：检查 staged 文件 + 检查未 push 的 commit
  4. 执行 git push

【用法】
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-push-smoke.py" `
        --devroot "${devroot}" --target "${target}" --remote origin --branch main

【示例】
    # 标准调用
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-push-smoke.py" `
        --devroot "${devroot}" --target "${devroot}\apps\repos\matt-cch\jywl-settlement" `
        --remote origin --branch main
"""
```

| 字段 | 作用 | 搜索价值 |
|------|------|---------|
| **意图** | 为什么存在这个脚本 | `rg "无弹窗"` 可命中 |
| **职责** | 具体做什么 | `rg "preflight"` 可命中 |
| **用法** | 命令行参数 | `rg "--target"` 可命中 |
| **示例** | 典型调用 | `rg "jywl-settlement"` 可命中 |

### 2.2 docstring 与文件名的一致性

文件名：`atomic-git-push-smoke.py`
docstring 首行：`无弹窗安全 smoke push 原子脚本`

二者必须语义对齐：
- 文件名中的 `git-push-smoke` → docstring 中的 `git push`、`smoke push`
- 文件名中的 `atomic` → docstring 中的 `原子脚本`
- 不一致时，以**docstring 为准**（docstring 更完整），但**文件名必须同步修正**。

## 3. README.md 铁律

### 3.1 目录必须自说明

任何包含子目录或 >=2 份文档的目录，必须放置 `README.md`。README.md 是目录意图的**导航入口**。

**必须包含的内容**：

```markdown
# py-tools 目录说明

本目录是 deploy-git-isolated task 的 Layer 3: Workflow 层……

## 文件导航

| 脚本 | 职责 | 典型场景 |
|------|------|---------|
| `run-lint.py` | Lint 唯一入口 | 新建/更新文档后必执行 |
| `workflow-git-deploy-full-poly.py` | Polyrepo 全链条部署 | 完整 GitHub 部署流水线 |

## 上级导航

- [scripts/ 目录索引](../README.md)
```

### 3.2 导航表与文件名的一致性

README.md 导航表中的**文件名**必须与磁盘实际文件名**逐字一致**。任何不一致都会导致搜索工具命中后跳转失败。

## 4. index.json 铁律

### 4.1 索引必须反映磁盘实际

`verified-task-index.json` 是全项目工具意图的**聚合真源**。每个登记条目必须与磁盘文件一一对应。

**必须包含的字段**：

```json
{
  "atomic-git-push-smoke": {
    "name": "无弹窗安全 smoke push 原子脚本",
    "type": "script",
    "path": "references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-push-smoke.py",
    "path_exists": true,
    "description": "构造 PAT 认证 URL + 阻断 GCM 弹窗 + 双路 preflight + manifest",
    "typical_scenarios": ["polyrepo 初始化验证", "workflow push 步骤"],
    "entry_command": "...",
    "verified_at": "2026-07-22T16:42:47"
  }
}
```

### 4.2 索引与文件名的一致性

| 检查项 | 规则 |
|--------|------|
| `path` 中的文件名 | 必须与磁盘实际文件名完全一致 |
| `name` | 必须与 docstring 首行语义一致 |
| `description` | 必须能从文件名 + docstring 推导出来 |
| `typical_scenarios` | 必须包含用户可能搜索的关键词 |

## 5. 四大载体的协同搜索机制

### 5.1 搜索场景：用户说"怎么安全 push"

| 步骤 | 工具 | 命中载体 | 结果 |
|------|------|---------|------|
| 1 | `rg -i "安全 push"` | **docstring**（"无弹窗安全 smoke push"） | 命中 `atomic-git-push-smoke.py` |
| 2 | `rg -i "push" verified-task-index.json` | **index.json**（`typical_scenarios` 含 "workflow push 步骤"） | 确认登记 |
| 3 | `rg -i "push" py-tools/README.md` | **README.md**（导航表含 `atomic-git-push-smoke.py`） | 获取职责说明 |
| 4 | `glob **/*push*.py` | **文件名**（`atomic-git-push-smoke.py`） | 确认路径 |

### 5.2 搜索场景：用户说"task/下有什么工具"

| 步骤 | 工具 | 命中载体 | 结果 |
|------|------|---------|------|
| 1 | `rg -i "deploy-git-isolated" verified-task-index.json` | **index.json**（`path` 字段） | 列出全部登记工具 |
| 2 | `rg -i "tool" skills/tool-discovery/SKILL.md` | **docstring/skill** | 确认 skill 规范 |
| 3 | `rg -i "py-tools" scripts/README.md` | **README.md** | 获取目录导航 |

## 6. 违规后果

| 违规行为 | 后果 | 修复义务 |
|---------|------|---------|
| 文件名泛化（`utils.py`） | `glob`/`rg` 无法命中，Agent 必须人工遍历目录 | 立即重命名，同步更新所有引用 |
| docstring 缺失【意图】 | Agent 无法理解职责，只能凭文件名猜测 | 补充 docstring，标注意图 |
| README.md 导航表与磁盘不一致 | 搜索命中后跳转断裂 | 同步更新导航表 |
| index.json `path_exists=false` | Agent 引用失效路径 | 清理失效条目或修正路径 |
| 四者语义不一致 | 搜索工具命中后信息矛盾，导致决策错误 | 以 docstring 为真源，同步修正其他三者 |

## 7. 与现有 baseline 的衔接

| 本规范 | 关联 baseline | 衔接点 |
|--------|--------------|--------|
| 文件名铁律 §1 | `baseline-structure.md` §2 | 目录结构中的文件命名 |
| docstring 铁律 §2 | `baseline-plugin-architecture.md` §8.4 | 插件 docstring 规范 |
| README.md 铁律 §3 | `baseline-operations.md` §4.x | 修订联动中的导航同步 |
| index.json 铁律 §4 | `baseline-audit-truth.md` §8.10 | 决策真源集中化 |

*文档版本：v1.0.0*  
*生成时间：2026-08-03*
