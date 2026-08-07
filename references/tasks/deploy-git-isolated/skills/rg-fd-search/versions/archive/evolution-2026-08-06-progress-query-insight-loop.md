---
title: 增加进度/状态查询场景与搜索→洞察闭环工作流
description: 为 rg-fd-search skill 增加 T005 进度查询场景，追加磁盘验证层、env-migration 时间线补查层、洞察与建议层，建立文档层+日志层+磁盘层的双源交叉验证模式
date: 2026-08-06
type: evolution
scope: add
category: behavior
target_section: "## 触发词" 及 "## 工作流"
meta:
  version: "1.1.0"
fingerprint:
  content_sha256: "evolution-progress-query-insight-loop-20260806"
  semantic_key: "rg-fd-search-progress-insight-loop"
---

# 增加进度/状态查询场景与搜索→洞察闭环工作流

## 背景

在 2026-08-06 的实战 session 中，用户要求搜索"gh 场景的工作进度"。Agent 按 SKILL.md 现有工作流执行了 P0-P3 搜索，输出了树状文档中的状态声明（"全部 ready"），但报告被用户判定为"只有 70 分"。核心缺陷：

1. 只有文档声明，没有磁盘实证验证（文档说 ready，但文件真的在吗？）
2. 没有查 env-migration 等日志性质文档，缺乏时间线脉络
3. 没有发现"文档声称有但实际 MISSING"的矛盾
4. 没有给出下一步聚焦方向

## 变更内容

### 1. 新增触发场景 T005

在"## 触发词"节的正面触发表中追加：

| 场景 | 触发词 |
|------|--------|
| T005 — 进度/状态查询 | "到哪里了"、"进度"、"现状"、"工作状态"、"做到哪一步了"、"完成了吗" |

> **判定标准**：用户意图不是"找文件"或"搜内容"，而是"了解某主题/某任务当前的工作进展、完成度、待办事项"。

### 2. 新增 Step 4: 验证层（磁盘存在性验证）

在现有 Step 3（输出解析）之后，**如果搜索意图命中 T005（进度/状态查询）**，必须追加以下验证步骤：

```
【磁盘存在性验证】
- 文档/索引声称的文件列表：<列出>
- 逐一 Test-Path / fd 验证磁盘存在性：
  - file1 → 存在/缺失
  - file2 → 存在/缺失
- 发现 MISSING：<列出>
- 发现不一致：<描述>
```

**方法**：使用 PowerShell `Test-Path -LiteralPath` 或 `fd -e <ext>` 对文档/索引中声明的文件路径进行批量验证。

### 3. 新增 Step 5: 上下文补查层（env-migration / handoff 时间线）

在验证层之后，**必须**搜索 `references/env-migrations/` 和 `docs/projects/*/handoffs/` 中近期（通常 7~14 天内）与目标主题相关的文档：

```powershell
# 列出近期 env-migration
& "${devroot}\venv\fd\fd.exe" -e md "${devroot}\references\env-migrations" | Sort-Object

# 搜索目标主题关键词
& "${devroot}\venv\ripgrep\rg.exe" -n -i "关键词" "${devroot}\references\env-migrations"
```

**目的**：
- 获取时间线脉络（哪些 session 做过什么、何时做的）
- 发现"未改造事项"、"待后续 session"等隐性待办
- 获取 session 中的设计决策、踩坑记录、认知澄清

### 4. 新增 Step 6: 洞察与建议层

基于前面所有搜索结果，输出结构化报告：

```
## 工作进度报告

### 一、整体状态
（一句话总结当前版本/状态）

### 二、近期时间线
（按 env-migration 倒序，时间线表格）

### 三、实证验证
（文档声称 vs 磁盘实际，含 MISSING/不一致发现）

### 四、未改造/待完善事项
（从 env-migration 中提炼的"未改造事项"或"待后续 session"条目）

### 五、下一步聚焦方向
（基于缺失+待办，给出 2~3 个优先级明确的建议方向）
```

### 5. 新增 Step 4b: 示例执行验证审计（强制）

skill 中所有包含可执行代码示例（PowerShell / Python / bash）的步骤，在实际执行后**必须**输出验证审计块：

```
【Skill 示例执行验证审计】
- 执行命令：<原始命令摘要>
- 执行环境：PowerShell 5.1 / PowerShell 7+ / bash / python
- 输出状态：✅ 正常 / ❌ 异常
- 异常类型：（如有）ParserError / ExitCode 非零 / 输出为空 / 编码乱码
- 是否记录 gotcha：是 / 否
- 修复方式：（如有异常）<简述修复>
- 修复后二次验证：✅ 通过 / ⏳ 待执行
```

**根因**：本次 session 中，Step 4 的 PowerShell 示例使用了 `$($exists ? 'OK' : 'MISSING')` 三元运算符语法，该语法在 Windows PowerShell 5.1 中不支持（ParserError）。Agent 修复为 `if/else` 后**未输出验证审计块**，导致用户无法确认修复是否有效、是否已验证。

**追加规则到 SKILL.md**：
- skill 中所有 PowerShell 示例必须使用 Windows PowerShell 5.1 兼容语法
- 执行任何 skill 示例后，必须输出上述审计块，无论成功或失败
- 失败时必须立即记录 gotcha，不等待 session 结束

### 6. 代码示例准入标准（硬性规则）

skill 中任何包含可执行代码的示例（PowerShell / Python / bash / Node.js 等），在写入 skill 之前**必须**同时满足以下两项准入条件，缺一不可：

**条件 A：run-lint.py 统一入口验证（唯一路径）**

> **硬性规则**：所有 lint 验证**必须**通过 `run-lint.py` 统一入口执行。**禁止**直接调用任何底层 lint 插件（如 `lint_json.py`、`md_lint`、`lint_encoding` 等）。`run-lint.py` 按文件扩展名自动路由到对应插件，无需、也不应人工指定。

标准命令示例（混合类型批量验证）：

```powershell
# 单文件验证
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.py"

# 多文件混合类型验证（.ps1 + .py + .json 自动路由）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "a.ps1" "b.py" "c.json"

# 三阶段闭环：检测 → 修复 → 再验证
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.md" --fix
```

- 独立 `.py` / `.ps1` / `.json` / `.md` 文件 → 统一走 `--files` 参数
- 混合类型批量验证 → 多个文件路径依次列出，`run-lint.py` 自动按扩展名路由
- **不通过不入 skill**

**条件 B：业务逻辑验证通过（Agent 亲自执行）**

Agent 必须在当前 session 中**实际执行**该示例代码，确认：

1. **无异常**：不触发 ParserError、不触发 ExitCode 非零、不产生未捕获异常
2. **输出符合预期**：输出内容与示例声称的行为一致
3. **环境兼容**：在 Windows PowerShell 5.1 / 项目指定 Python 解释器等标准环境下可正常运行

```
【代码示例业务验证审计】
- 示例代码：<摘要或文件路径>
- 执行命令：<实际执行的完整命令>
- 执行环境：<PowerShell 5.1 / python 3.x / bash>
- run-lint 结果：✅ 通过 / ❌ 未通过
- 业务执行结果：✅ 输出符合预期 / ❌ 异常
- 异常详情：（如有）<错误信息>
- 修复后重验：✅ 通过 / ⏳ 待修复
```

**禁止行为**：
- ❌ **禁止**将未经验证的示例代码直接写入 skill（"先写上，后面的人用的时候再验证"）
- ❌ **禁止**在 skill 示例中使用未经验证的语法（如 PS 7+ 独占语法、未测试的第三方库 API）
- ❌ **禁止**用"这是示例，实际执行请根据环境调整"等说辞绕过验证义务

**反例：绕过 run-lint.py 统一入口的错误表述**

以下表述曾在本 skill 初稿中出现，属于**严重错误示范**，必须作为反面教材记录：

> ~~"若示例内嵌在 `.md` 文档中 → lint 整个 `.md` 文件（md_lint + lint_encoding）"~~

**为什么错误**：
1. 提到底层插件名 `md_lint`、`lint_encoding`，等于在 skill 中教人**直接调用底层插件**，绕过 `run-lint.py` 统一入口
2. 这种表述会让后续 Agent 误以为"按文件类型分 lint 工具"是正确的做法，破坏统一入口原则
3. `run-lint.py` 已经内置了扩展名自动路由，人工指定底层插件既多余又危险

**正确表述应为**：
> "若示例内嵌在 `.md` 文档中 → 统一走 `run-lint.py --files path/to/file.md`，由 `run-lint.py` 自动路由到对应插件"

**本次违规记录**：
- 违规示例：`"$($exists ? 'OK' : 'MISSING')"`（PS 5.1 不支持三元运算符）
- 违规原因：Agent 在 skill 工作流中直接编写了该 PowerShell 示例，未先执行验证
- 后果：首次执行即触发 ParserError，用户被迫介入纠偏
- 修复：改为 `if/else` 语法，执行验证通过后才写入 evolution

## 影响范围

- SKILL.md "## 触发词"节追加 T005
- SKILL.md "## 工作流"节追加 Step 4/5/6（仅 T005 命中时触发）
- 现有 P0-P3 搜索逻辑不变，保持向后兼容

## 与现有规则的衔接

- 新增 Step 4/5/6 中涉及 bash 调用时，仍需遵守 `.cursor/rules/high-frequency-shell-guard-content.mdc`
- 新增 Step 5 中读取 `.md` 文件后，如产生新文件写入，需遵守 `.cursor/rules/strictly-forbid-manual-lint-bypass.mdc`

## 验收标准

下次遇到"搜索某任务进度"类请求时，Agent 输出的报告必须包含：
1. 树状文档中的状态声明
2. 磁盘文件存在性验证结果
3. env-migration 时间线脉络
4. 发现的 MISSING/不一致项
5. 明确的下一步聚焦方向
