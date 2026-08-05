---
name: rg-fd-search
description: 通用搜索能力封装——文件查找（fd）+ 内容搜索（rg），覆盖目录/文件/内容/docstring。搜索优先次序：树状自说明 > JSON 索引 > docstring > 关键词搜索。默认禁止原生 grep/glob。触发词：搜索、查找、列出文件、找文件、搜内容、grep、glob、rg、fd。
---

# rg-fd-search — 通用搜索能力

> **触发条件索引**：本文档中的触发条件受 `verified-trigger-index.json` 统一管理。
> 新增/修改触发条件时，必须先更新索引。索引真源：`${devroot}/references/runtime/verified-trigger-index.json`
> 冲突裁决与边界判断以索引中的 `conflict_domains` 和 `conflict_resolution_rules` 为准。

## 本质

当你需要**查找文件**或**搜索内容**时，本 skill 提供 rg（ripgrep）和 fd 的标准调用模板，强制遵循搜索优先次序（P0-P3），避免默认使用原生 grep/glob。

## 适用范围

- 文件查找（按扩展名、按文件名 pattern）
- 内容搜索（全文搜索、正则搜索）
- docstring 搜索（Python 模块注释）
- 组合搜索（先找文件再搜内容）

## 不适用范围

- **找工具/查用法** → 命中 `tool-discovery` skill，不走本 skill
- **真源检测** → 命中 `high-frequency-verify-runtime.mdc`
- **版本更新** → 命中 `high-frequency-update-version.mdc`

## 触发词

### 正面触发（T）

| 场景 | 触发词 |
|------|--------|
| T001 — 文件查找 | "列出文件"、"找文件"、"有哪些 .py"、"glob"、"fd" |
| T002 — 内容搜索 | "搜一下"、"查找"、"grep"、"rg"、"ripgrep"、"搜索内容" |
| T003 — 组合搜索 | "在所有 .py 中搜"、"找包含 xx 的文件" |
| T004 — docstring 搜索 | "查一下 docstring"、"这个脚本是干嘛的"、"模块注释" |

### 排他触发（E）

| 场景 | 触发词 | 说明 |
|------|--------|------|
| E001 — 工具发现 | "有什么工具"、"查一下 deploy-git-isolated 的工具"、"这个脚本怎么用" | 命中 `tool-discovery` |
| E002 — 高频任务 | "检查真源"、"记一版 version" | 命中对应 mdc |

## 工作流

### Step 1: 搜索优先级审计（必须输出）

```
【rg/fd 搜索优先级审计】
搜索意图：<一句话说明>

- P0 树状自说明是否命中？          是/否 → <文档路径>
- P1 JSON 索引是否命中？            是/否 → <ENTRY.json / verified-task-index.json>
- P2 docstring 是否命中？           是/否 → <脚本路径>
- P3 关键词搜索是否必要？           是/否
- 是否用户显式要求原生工具？        是/否
- 结论：<使用 rg/fd / fallback 到原生（需 HITL）>
```

### Step 2: 按优先次序执行搜索

#### P0 — 树状自说明文档

**适用**：搜索 deploy-git-isolated 内部工具、脚本、流程。

```powershell
# README.md 导航
& "${devroot}\venv\ripgrep\rg.exe" -n -C 3 "关键词" "${devroot}\references\tasks\deploy-git-isolated\scripts\README.md"

# TASK-TOOLS-INDEX.md 速查
& "${devroot}\venv\ripgrep\rg.exe" -n -C 3 "关键词" "${devroot}\references\tasks\deploy-git-isolated\TASK-TOOLS-INDEX.md"

# EXEC-CHEATSHEET.md 命令速查
& "${devroot}\venv\ripgrep\rg.exe" -n -C 3 "关键词" "${devroot}\references\tasks\deploy-git-isolated\scripts\EXEC-CHEATSHEET.md"
```

#### P1 — JSON 真源索引（并列查询）

**适用**：需要工具路径、版本状态、验证时间等机器可读信息。

```powershell
# ENTRY.json（task 内部真源）
& "${devroot}\venv\ripgrep\rg.exe" -n -C 2 "关键词" "${devroot}\references\tasks\deploy-git-isolated\ENTRY.json"

# verified-task-index.json（全局真源）
& "${devroot}\venv\ripgrep\rg.exe" -n -C 2 "关键词" "${devroot}\references\runtime\verified-task-index.json"
```

**互补逻辑**：
- ENTRY.json 侧重**职责描述**（`active_scripts[].role` 字段非常详细）
- verified-task-index.json 侧重**状态验证**（`verified_at`、`path_exists`）
- **两者都要查**，信息互补

#### P2 — docstring

**适用**：需要了解 Python 模块的意图、职责、用法参数。

```powershell
# Python 脚本 docstring
& "${devroot}\venv\ripgrep\rg.exe" -n -A 20 "关键词" --type py "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\"

# Python 插件 docstring
& "${devroot}\venv\ripgrep\rg.exe" -n -A 20 "关键词" --type py "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\"
```

#### P3 — 关键词全文搜索（兜底）

**适用**：P0-P2 均未命中，需要全文盲搜。

```powershell
# 全文搜索
& "${devroot}\venv\ripgrep\rg.exe" -n "关键词" "${devroot}\目标目录"

# 文件查找
& "${devroot}\venv\fd\fd.exe" -e 扩展名 "${devroot}\目标目录"
```

### Step 3: 输出解析

rg 输出格式：`path/to/file:line:content`

```python
import re
pattern = r"^(.+):(\d+):(.*)$"
```

fd 输出格式：每行一个文件路径（含 `-0` 时用 `\0` 分隔）

```python
# 标准模式
paths = output.strip().split("\n")

# -0 null 分隔模式
paths = output.split("\0")
```

## rg 参数速查

| 场景 | 参数 | 说明 |
|------|------|------|
| 基础搜索 | `-n` | 显示行号 |
| 忽略大小写 | `-i` | 大小写不敏感 |
| 上下文 | `-C 3` | 前后各 3 行 |
| 后文 | `-A 15` | 后 15 行（docstring） |
| 按类型 | `-t py` | 仅 Python 文件 |
| 组合管道 | `-f -` | 从 stdin 读取文件列表 |
| null 分隔 | `--null -0` | 配合 fd `-0` 使用 |

## fd 参数速查

| 场景 | 参数 | 说明 |
|------|------|------|
| 按扩展名 | `-e py` | 查找 .py 文件 |
| 按 glob | `-g "*.test.py"` | glob 模式匹配 |
| 隐藏文件 | `-H` | 包含隐藏文件 |
| 忽略文件 | `-I` | 不遵守 .gitignore |
| 最大深度 | `-d 3` | 仅搜索 3 层目录 |
| 执行命令 | `-x cmd` | 对每个结果执行命令 |
| 批处理 | `-X cmd` | 一次性传所有结果 |
| null 分隔 | `-0` | 输出用 \0 分隔 |

## 组合搜索示例

### 示例 1：在所有 .py 文件中搜索 pattern

```powershell
& "${devroot}\venv\fd\fd.exe" -e py "${devroot}\apps\api-demo\src" | & "${devroot}\venv\ripgrep\rg.exe" -n "pattern" -f -
```

### 示例 2：在 Markdown 文件中搜索关键词（含空格路径安全）

```powershell
& "${devroot}\venv\fd\fd.exe" -0 -e md "${devroot}\docs" | & "${devroot}\venv\ripgrep\rg.exe" --null -0 -f - "关键词"
```

### 示例 3：查找所有 test 文件并统计行数

```powershell
& "${devroot}\venv\fd\fd.exe" -g "test_*.py" -X wc -l
```

## 禁止行为

1. **默认使用原生 grep/glob**：必须先执行搜索优先级审计，确认 rg/fd 更合适
2. **跳过 P0/P1 直接全文搜索**：丢失已整理的上下文和避坑指南
3. **未审计即调用 bash**：必须在回复中显式输出审计块
4. **只查一个 JSON 索引**：ENTRY.json 和 verified-task-index.json 必须并列查询

## 与 tool-discovery 的分工

| 用户意图 | 命中 skill | 搜索策略 |
|----------|-----------|---------|
| "找工具"、"查用法" | `tool-discovery` | 内部按 P0-P3 搜索 ENTRY.json / verified-task-index.json / README / docstring |
| "搜文件"、"搜内容" | `rg-fd-search`（本 skill） | 按 P0-P3 执行 rg/fd 通用搜索 |

> **关键区别**：tool-discovery 输出的是"工具名 + entry_command + 职责描述"；rg-fd-search 输出的是"文件路径 + 匹配行号 + 匹配内容"。

## 关联文档

- 执法规则：`.cursor/rules/rg-fd-search-priority.mdc`
- 工具发现：`references/tasks/deploy-git-isolated/skills/tool-discovery/SKILL.md`
- 真源索引：`references/runtime/verified-task-index.json`
- Task 真源：`references/tasks/deploy-git-isolated/ENTRY.json`

## Skill 加载机制（SED 模式）

本 skill 采用 Self-Evolution Directory（SED）模式，执行时按以下顺序加载：

1. **SKILL.md**（基准文件，始终加载）
2. **evolutions/*.md**（按文件名字典序，按 `scope` merge 到执行上下文）
3. **learnings/*.md**（加载为认知上下文，不修改执行逻辑，供 Agent 推理参考）
4. **scripts/**（内部脚本，通过 entry_command 或 import 调用，不对外暴露）

> **封装边界**：`scripts/` 下的脚本为本 skill 私有实现，不单独登记到项目级工具索引（verified-task-index.json）。用户应通过 SKILL.md 声明的入口调用，而非直接执行 scripts/ 下的单个文件。

### 目录结构

```
skills/rg-fd-search/
├── SKILL.md              # 基准文件（本文件）
├── README.md             # 合并导航（聚合视图）
├── scripts/              # 执行面：skill 专属可执行脚本（不对外登记）
│   ├── __init__.py
│   └── helpers/
│       └── __init__.py
├── references/           # 引用面：外部资料、本地索引
├── assets/               # 资产面：截图、数据文件
├── templates/            # 模板面：可复用模板
├── examples/             # 示例面：使用示例、测试用例
├── versions/             # 版本面：演进时间线 + 收敛归档
│   ├── manifest.json
│   └── archive/
├── gotchas/              # 错误面：踩坑记录（时间线，不可变追加）
├── evolutions/           # 行为面：规则/参数/流程演进补丁
└── learnings/            # 认知面：洞察/模式/基线/结论
```

### 增量内容 frontmatter 规范

所有写入 `gotchas/`、`evolutions/`、`learnings/` 的 `.md` 文件必须包含标准化 frontmatter：

#### gotchas/ 模板

```yaml
---
title: <一句话标题>
date: YYYY-MM-DD
type: gotcha
fingerprint:
  content_sha256: <sha256(trigger_condition + 根因 + 修复)>
  semantic_key: <规范化主题标识，如 fd-path-space>
---
```

#### evolutions/ 模板

```yaml
---
title: <一句话标题>
date: YYYY-MM-DD
type: evolution
scope: add              # add | replace | append | override
category: parameter     # parameter | behavior | workflow | rule
target_section: "## <目标章节标题>"
fingerprint:
  content_sha256: <sha256(变更内容)>
  semantic_key: <规范化主题标识>
---
```

#### learnings/ 模板

```yaml
---
title: <一句话标题>
date: YYYY-MM-DD
type: learning
category: conclusion    # insight | pattern | baseline | conclusion | heuristic
confidence: high        # high | medium | low
evidence_count: 1       # 支持该结论的实测/执行次数
fingerprint:
  content_sha256: <sha256(核心结论)>
  semantic_key: <规范化主题标识>
---
```

### 去重与入库策略

1. **精确去重**：计算 `fingerprint.content_sha256`，与 `versions/manifest.json` 中已有指纹比对，完全匹配则自动跳过。
2. **语义去重**：计算与已有同类型文件的 `trigger_condition` Jaccard 相似度，大于 0.8 则暂停并请求用户确认。
3. **收敛**：当 `evolutions/` >= 5 或 `gotchas/` >= 10 或距上次收敛 >= 30 天，触发收敛流程，将 `evolutions/` 合并回 `SKILL.md`，已收敛补丁移入 `versions/archive/`。

## Skill Self-Evolution 复盘

每次执行本 skill 后，Agent 必须执行以下自检：

【新认知检测】
- [ ] 新踩坑（gotcha）：遇到 SKILL.md + evolutions/ 均未覆盖的异常或边界
- [ ] 新规则/行为变更（evolution）：实际执行路径与 SKILL.md 推荐做法不同，且更优
- [ ] 新洞察/模式/结论（learning）：发现了可复用的认知、经验、基准

【入库判断】
- 任意勾选 → 计算 fingerprint → 比对 `versions/manifest.json`
  - 完全匹配 → 去重跳过
  - 语义重复（Jaccard > 0.8）→ 暂停，请求用户确认
  - 新认知 → 按类型分流：
    - 错误/陷阱 → `gotchas/`
    - 规则/参数/流程变更 → `evolutions/`
    - 洞察/模式/基线/结论 → `learnings/`
- 全部未勾选 → 不操作
