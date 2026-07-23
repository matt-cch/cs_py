---
title: py-tools 脚本 docstring 与命名规范
description: deploy-git-isolated/scripts/py-tools 下全部 Python 脚本的 docstring schema、命名约定、修订联动义务、索引登记层级与迁移检查清单。
date: 2026-07-22
meta:
  version: "1.0.0"
  category: schema
---

# py-tools 脚本 docstring 与命名规范

> **文档性质**：规范定义（framework 层）。定义 py-tools 下全部 Python 脚本的命名模式、docstring 字段、修订联动义务、索引登记层级。
> **受众**：Human + Agent。新建/重构 py-tools 脚本前必须先通读本规范。


## 一、命名规范

### 1.1 三级命名模式

| 脚本类型 | 命名模式 | 示例 |
|---------|---------|------|
| **atomic**（原子脚本） | `atomic-<domain>-<action>-<target>.py` | `atomic-git-reset-staged.py` |
| **workflow**（编排脚本） | `workflow-<domain>-<action>-<target>.py` | `workflow-git-deploy-full-poly.py` |
| **workflow-phase**（阶段脚本） | `workflow-phase-<domain>-<scope>-<action>.py` | `workflow-phase-git-local-commit.py` |
| **helper**（辅助脚本） | `<domain>-<action>.py`（不加前缀） | `run-lint.py` |

#### 各段含义

| 段 | 取值范围 | 说明 |
|----|---------|------|
| `<domain>` | `git` / `gh` / `runtime` / `workspace` / `deploy` / `agent` / `security` | 能力域，对应 py-plugins/ 下的 plugin 分类 |
| `<action>` | `create` / `clone` / `push` / `reset` / `check` / `deploy` / `edit` / `verify` | 动词，描述核心动作 |
| `<target>` | `staged` / `repo` / `smoke` / `full-poly` / `json` | 动作作用对象或场景限定 |
| `<scope>` | `local` / `remote` / `preflight` / `audit` | phase 阶段的作用范围 |

#### 禁止行为

- 禁止用 `atomic-01-`、`step-` 等序号前缀（已有 `download-runtime/` 子目录下的 `atomic-01-route-probe.py` 为历史遗留，新脚本不沿用）
- 禁止用 `new-`、`tmp-`、`test-` 等临时性前缀
- 禁止复数形式（用 `repo` 而非 `repos`）

### 1.2 workflow-phase 命名细则

当长链条 workflow 需要拆分为可独立调用的 phase 时，按以下规则命名：

```
workflow-phase-<domain>-<scope>-<action>.py
```

| scope | 含义 | 示例 |
|-------|------|------|
| `local` | 仅影响本地目录，不涉及 remote | `workflow-phase-git-local-add-commit.py` |
| `remote` | 涉及 remote 交互（push / PR / upstream） | `workflow-phase-git-remote-push-upstream.py` |
| `preflight` | 前置验证阶段 | `workflow-phase-git-preflight-all.py` |
| `audit` | 审计/扫描阶段 | `workflow-phase-security-audit-staged.py` |

**phase 拆分原则**：
1. 每个 phase 必须可独立执行（exit 0/1 语义完整）
2. phase 之间通过 manifest JSON 传递上下文（不依赖内存状态）
3. 原 workflow 脚本通过 `subprocess.run()` 编排各 phase，保持向后兼容


## 二、docstring schema（统一模板）

所有 py-tools 脚本必须在文件开头包含 `r"""` 原始字符串 docstring，格式如下。

### 2.1 通用模板（atomic / helper）

```python
#!/usr/bin/env python3
r"""
<relative_path>/<filename>.py — <一句话中文标题>（<版本>）
标签：<tag1>[, <tag2>...]
版本：<语义版本，如 v1.0.0>
日期：<YYYY-MM-DD>

【意图】
<为什么会产生这个工具？解决了什么问题？
属于哪个 workflow 的哪一步？
追溯到什么痛点/踩坑记录？与哪个 env-migration 关联？>

【职责】
<1. ...>
<2. ...>
<3. ...>

【依赖】
底层能力（py-plugins/）：
  - <plugin_name>（<用途说明>）
外部工具：
  - <tool_path>（<用途说明>）
环境变量：
  - <VAR_NAME>（<来源，如 devroot/.env>）

【预检】
执行本脚本前必须满足的前置条件：
  - 文件存在性: <文件路径>
  - 目录存在性: <目录路径>
  - 进程状态: <如"目标进程未运行">
  - 网络可达: <如"GitHub API 可访问">

【调用参数】
  --devroot    <str, 可选, 默认=Path.cwd()>  工具链根路径
  --target     <str, 可选, 默认=devroot>     操作目标路径（polyrepo 场景）
  --output     <str, 可选>                   产物输出路径（workflow 调用时必须显式传入；未传时回退到 venv/tmp/{tool-name}-manifest-{timestamp}.json）
  --xxx        <类型, 必填/可选, 默认值>     <说明>

【用法示例】
    # 场景1：<一句话描述>
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\<filename>.py" `
        --devroot "${devroot}" `
        --xxx "value"

    # 场景2：<polyrepo 场景描述>
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\<filename>.py" `
        --devroot "${devroot}" `
        --target "${target}" `
        --xxx "value"

【返回】
    exit 0 = <成功语义>
    exit 1 = <失败语义>

【审计产物】
    <manifest 路径模板>: <内容结构说明（JSON 字段列表）>
    <其他产物路径模板>: <内容结构说明>

【关联】
    - workflow: <调用本脚本的 workflow 路径>
    - env-migration: <关联的 env-migration 文档路径>
    - 下游消费: <消费本脚本产物的脚本/工具>
"""
```

### 2.2 workflow 模板（扩展版）

workflow 脚本在通用模板基础上，将【预检】【调用参数】替换为以下扩展字段：

```python
r"""
...（标题、标签、版本、日期、意图、职责、依赖 同通用模板）

【执行顺序】
  1. Step 0a: <atomic_script_1>（<说明>）
  2. Step 0b: <atomic_script_2>（<说明>）
  3. Step 4: <git_cmd>（<说明>）
  ...

【安全与审计机制】
  - <安全机制1>
  - <安全机制2>

【审计产物与追踪路径】
  - Step X  <产物名>:
      `${devroot}/venv/tmp/<PREFIX>-{timestamp}.json`
      <内容结构说明>

【调用参数】
  --devroot    <str, 必填>                   工具链根绝对路径（必须与 CWD 一致）
  --target     <str, 可选, 默认=devroot>     操作目标路径（polyrepo 场景）
  --step       <str, 可选, 默认=all>         执行单步：0/4/5/.../all
  --message    <str, 可选>                   commit message

【用法示例】
    # 单仓库完整执行
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\<filename>.py" `
        --devroot "${devroot}"

    # 仅执行 preflight 阶段
    & "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\<filename>.py" `
        --devroot "${devroot}" --step 0
"""
```

### 2.3 字段设计说明

| 字段 | 来源 | 是否新增 | 必填 | 说明 |
|------|------|---------|------|------|
| 标题行 | 现有惯例 | 否 | ✅ | `路径/文件名 — 描述（版本）` |
| 标签 | 现有惯例 | 否 | ✅ | atomic 统一 `py-tools`；runtime 相关加 `runtime` |
| 版本 | 部分有 | **强化** | ✅ | 语义版本，变更时必须更新 |
| 日期 | 无 | **新增** | ✅ | 首次创建或最近重大修订日期 |
| **意图** | 仅 `atomic-git-reset-staged.py` 有 | **新增** | ✅ | 追溯"为什么有这工具" |
| 职责 | 现有惯例 | 否 | ✅ | 列表形式，不超过 5 条 |
| **依赖** | 无 | **新增** | ✅ | 含 py-plugins、外部工具、环境变量三层 |
| **预检** | 无 | **新增** | atomic/helper ✅ | 前置条件显性化；workflow 替换为【执行顺序】 |
| **调用参数** | 无（仅用法中有示例） | **新增** | ✅ | 结构化参数说明表 |
| 用法示例 | 现有惯例 | 否 | ✅ | 至少覆盖单仓库 + polyrepo 两种场景 |
| 返回 | 现有惯例 | 否 | ✅ | exit 码语义 |
| **审计产物** | 部分有 | **强化** | ✅ | manifest 路径模板 + JSON 结构说明。若脚本生成 manifest，必须在【调用参数】中登记 `--output`（见 baseline-workflow-deploy.md §8.9） |
| **关联** | 无 | **新增** | ✅ | 上下游调用链追踪 |


## 三、修订联动义务清单

当在 `py-tools/` 下**新建、重命名、删除**脚本，或**修改脚本职责边界**时，必须同步更新以下文件：

### 3.1 必须联动的索引文件

| 层级 | 文件 | 职责 | 更新时机 |
|------|------|------|---------|
| **项目级** | `references/runtime/verified-task-index.json` | 全部高频任务与可用脚本的唯一真源索引 | 任何 py-tools 脚本的增删改 |
| **task 级** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` | 本 task 下全部工具的人类可读速查手册 | 任何 py-tools 脚本的增删改 |

### 3.2 必须联动的命令速查表

| 文件 | 职责 | 更新时机 |
|------|------|---------|
| `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` | 本 task 全部可执行命令的速查真源 | 新增/重命名 py-tools 脚本、变更入口命令或参数时 |

> **说明**：`.cursor/rules/high-frequency-task-index.mdc` 及对应 `high-frequency-*.mdc` 为项目级高频任务入口，**不强制**随单个 py-tools 脚本增删改联动。仅当某脚本成为新的高频任务推荐入口时才更新。

### 3.3 必须联动的配置/模板文件

| 文件 | 职责 | 更新时机 |
|------|------|---------|
| `references/runtime/verified-runtime-index.json` | 运行时真源索引 | 脚本内部引用的工具链路径发生变化时 |
| `references/runtime/runtime_config/tools_config.json` | 工具检测配置 | 新增/删除被真源检测扫描的工具时 |
| `schema/py/workflow-poly-template.py` | workflow 模板 | 模板中的 docstring 结构或 Step 编排模式发生变更时 |

### 3.4 免联动情形

以下情形**不触发**修订联动：
- 纯版本号更新（如 `v1.0.0` → `v1.0.1`，无职责变更）
- 纯 bug 修复，不新增/删除参数、不变更调用链
- 文档 typo 修正（docstring 内文字错误）
- 代码内部重构，接口契约不变


## 四、索引登记层级图

当新增一个 py-tools 脚本时，按以下层级逐级登记：

```
py-tools/ 新增脚本
    │
    ├── L1: verified-task-index.json（项目级唯一真源，必须）
    │      └── available_scripts_and_tools.<script_id>
    │          字段: name, type, path, path_exists, description,
    │                typical_scenarios, entry_command, added_at, verified_at
    │
    ├── L2: TASK-TOOLS-INDEX.md（task 级人类速查，必须）
    │      └── 在对应分类表格中追加一行
    │          字段: 脚本名, 类型, 用途, 入口命令, 关联 workflow
    │
    └── L3: EXEC-CHEATSHEET.md（命令速查，必须）
           └── 在对应 Stage 中追加命令示例
```

> **不在强制联动层级**：`schema/README.md`（schema 目录导航，仅规范文档变更时更新）、`high-frequency-task-index.mdc` / `high-frequency-*.mdc`（项目级高频任务入口，仅当脚本成为新推荐入口时更新）。

### 4.1 登记字段规范（verified-task-index.json）

```json
"<script_id>": {
    "name": "<人类可读中文名>",
    "type": "script | helper | workflow | skill | skill_python",
    "path": "<相对于 devroot 的相对路径>",
    "path_exists": true,
    "description": "<一句话说明>",
    "typical_scenarios": ["<场景1>", "<场景2>"],
    "entry_command": "<标准命令模板，含 ${devroot} 占位符>",
    "added_at": "YYYY-MM-DDTHH:MM:SS",
    "verified_at": "YYYY-MM-DDTHH:MM:SS",
    "status": "current | legacy | deprecated"
}
```

### 4.2 type 取值规范

| type | 适用对象 |
|------|---------|
| `script` | 独立可执行的 atomic / helper Python 脚本 |
| `workflow` | 编排多个 atomic 的长链条脚本 |
| `helper` | 被其他脚本调用的工具脚本（不直接面向终端用户） |
| `skill` | SKILL.md 描述的 skill |
| `skill_python` | skill 附带的 Python 脚本 |


## 五、本次迁移检查清单

### 5.1 源文件（venv/tmp/ → py-tools/）

| # | 原文件 | 新文件名 | 状态 |
|---|--------|---------|------|
| 1 | `venv/tmp/atomic-create-github-repo.py` | `py-tools/atomic-gh-repo-create.py` | ⏳ 待迁移 |
| 2 | `venv/tmp/atomic-clone-repo.py` | `py-tools/atomic-git-repo-clone.py` | ⏳ 待迁移 |
| 3 | `venv/tmp/atomic-smoke-push.py` | `py-tools/atomic-git-push-smoke.py` | ⏳ 待迁移 |
| 4 | `venv/tmp/edit-json-workspace.py` | `py-tools/atomic-workspace-edit-json.py` | ⏳ 待迁移 |

### 5.2 每个脚本迁移时必须完成的检查项

| 检查项 | 说明 |
|--------|------|
| ☐ 路径推导逻辑更新 | `venv/tmp/` → `py-tools/`，确保 `py-plugins` 目录推导正确 |
| ☐ docstring 补全 | 按本规范 2.1 模板补全全部字段 |
| ☐ 编码闭环检查 | `sys.stdout.reconfigure(encoding="utf-8")` 存在 |
| ☐ lint 验证 | `run-lint.py` lint_python + lint_encoding 通过 |
| ☐ 单仓库场景测试 | `--devroot "${devroot}"` 可正常执行 |
| ☐ polyrepo 场景测试 | `--target "${target}"` 可正常执行（如适用） |
| ☐ `--output` 参数合规 | 若脚本生成 manifest，必须提供 `--output` CLI 参数；workflow 调用时必须显式传入（见 baseline-workflow-deploy.md §8.9） |

### 5.3 索引与文档联动

| 检查项 | 说明 |
|--------|------|
| ☐ verified-task-index.json | 追加 4 个条目到 `available_scripts_and_tools` |
| ☐ TASK-TOOLS-INDEX.md | 追加 4 个脚本到对应分类表格 |
| ☐ EXEC-CHEATSHEET.md | 在对应 Stage 中追加 4 个脚本的命令示例 |
| ☐ 上游引用检查 | `workflow-git-deploy-full-poly.py` 等是否硬编码引用旧路径 |

### 5.4 迁移后清理

| 检查项 | 说明 |
|--------|------|
| ☐ 删除原文件 | `venv/tmp/atomic-create-github-repo.py` 等 4 个文件 |
| ☐ 验证旧路径失效 | 确认无其他脚本/配置引用 `venv/tmp/atomic-*.py` |


## 六、附：命名速查卡

| 你想表达的概念 | 推荐命名段 | 示例 |
|---------------|-----------|------|
| GitHub CLI 操作 | `gh-` | `atomic-gh-repo-create.py` |
| git 工具操作 | `git-` | `atomic-git-reset-staged.py` |
| 运行时检测/下载 | `runtime-` | `atomic-runtime-detect-local.py` |
| 工作区/IDE 配置 | `workspace-` | `atomic-workspace-edit-json.py` |
| 安全审计 | `security-` | `atomic-security-audit-staged.py` |
| Agent/LLM 相关 | `agent-` | `atomic-agent-preflight.py` |
| 本地目录操作 | `local-` | `workflow-phase-git-local-commit.py` |
| remote 交互操作 | `remote-` | `workflow-phase-git-remote-push.py` |
| 前置验证 | `preflight-` | `workflow-phase-git-preflight-all.py` |
| smoke 测试 | `smoke-` | `atomic-git-push-smoke.py` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-22 |
| **更新人** | OpenCode Agent Session |
| **变更触发** | 用户要求将 venv/tmp/ 下的 4 个 atomic 脚本正式化迁移到 py-tools/ |
| **下次修订条件** | 新增第 5 种脚本类型；workflow-phase 命名模式实际落地后复盘 |
| **关联文档** | `schema/py/workflow-poly-template.py`、`high-frequency-task-index.mdc` |
