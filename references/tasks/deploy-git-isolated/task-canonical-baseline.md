---
title: deploy-git-isolated — Task Canonical Baseline
description: 本 task 的认知基线与真源契约。记录 Agent 与人类共同确认的事实标准、命名约定、执行路径，以及 SOP / EXEC-CHEATSHEET / TASK-TOOLS-INDEX 三者的语义区分。
date: 2026-06-16
meta: {}
---

# deploy-git-isolated — Task Canonical Baseline

> **核心意图**：本文档不是「格式说明书」，而是 **Agent 与人类在渐进式交互中共同确认的事实标准**。  
> 它确保双方对以下问题有**归一化的理解**：
> - 什么是 Task（与 Skill 的边界在哪）
> - 真源（Single Source of Truth）存放在哪里
> - 命名约定（Naming Convention）如何消除歧义
> - Agent 执行路径与人类查阅路径如何对照
> - 如何渐进式确认、认可、固化事实
>
> **适用范围**：`references/tasks/deploy-git-isolated/` 目录下的全部文件与操作。  
> **约束性质**：框架层规范，极低变动频率；触及修改时按修订联动规则执行。
> **模板来源**：`schema/task-template/task-canonical-baseline.md`


## 0. Agent 执行哲学与工程化铁律（顶层原则）

> **来源**：用户明确确认（2026-06-18）。本节是本文档的**顶层原则声明**，所有后续章节均受本节约束。违反本节任一条款视为操作事故。

### 0.1 禁止现写命令行（No Ad-hoc Shell）

**核心原则**：Agent **不得**在任务执行过程中临时拼接命令行完成工程操作。

| 维度 | 现写命令行 | 现成脚本/工具 |
|------|-----------|--------------|
| **可靠性** | 每次现写都是一次新的 bug 引入机会，引号、转义、编码、路径四层风险叠加 | 已实践验证，边界 case 已处理，schema 输出已确认 |
| **一致性** | 同一需求在不同 session 中写法可能完全不同，无法比对审计 | 同一工具多次调用输出格式固定，可预期、可 diff |
| **成本** | 踩坑 → 排查 → 修复 → 再踩，反复消耗 token 与时间 | 一次开发，持续复用，边际成本趋近于零 |
| **知识沉淀** | 成功经验随风而散，下次 session 完全重置 | 每次成功执行都在加固工具链，形成可复用资产 |

**铁律**：
- 任何需求先查 `verified-task-index.json` → `available_scripts_and_tools`
- 任何 long-content 处理先走 `file-write-helper.py` 三步流程，禁止 `python -c` / `powershell -Command`
- 任何下载需求先走 `download-runtime-tool.py`，禁止自行拼接 `curl`/`Invoke-WebRequest`
- 任何 lint/编码检查先查 **已登记/注册的命令速查表**（`verified-task-index.json` → `available_scripts_and_tools`，或本 task `TASK-TOOLS-INDEX.md`），按索引指向的路径执行，禁止凭记忆或目录扫描直接调用

### 0.2 优先复用现成工具（Tool-First）

**核心原则**：现成工具不是「备选方案」，而是**默认方案**；现写逻辑才是需要特殊审批的例外。

**为什么已验证工具优先**：
1. **真实意图已被理解**：工具开发过程中已与用户反复确认需求边界，不是一次性猜测
2. **预期 schema 已固化**：工具输出格式受 schema 约束（如 `verify-runtime-report-*.json`），下游可稳定消费
3. **执行一致性已保证**：同一条命令在不同 session、不同 Agent 实例中行为一致
4. **错误处理已完善**：超时、重试、fallback、编码切换等边界已被前置处理

**自检清单（每次考虑现写前必须输出）**：
```
【Tool-First 自检】
- 该需求是否已有现成脚本/工具？           是/否 → 路径
- 该需求是否已有 schema 定义？             是/否 → 路径
- 现写命令与现成工具的差异点是什么？       <说明>
- 为什么现成工具无法满足？                 <说明>
结论：复用现有工具 / 申请例外（需用户确认）
```

### 0.3 Long-Content 分步落盘（Write-to-Disk Pipeline）

**核心原则**：任何多行内容、长字符串、含特殊字符（`$`、`"`、中文）的正文，**必须先落盘再执行**，禁止塞进命令行。

**历史根因**：Shell 引号层 → 编码层 → Agent 捕获层三重转义，每次必翻车。

**标准三步流程**：
```
Step 1: write/edit 工具写入正文到磁盘（不经 Shell，不经过任何转义层）
Step 2:（如需 BOM/LF 校验）file-write-helper.py --config job.ini
Step 3: Shell 执行短命令（仅含解释器路径 + 脚本路径 + 短标志）
```

**禁止行为（无例外）**：
- `python -c "..."` — 一律禁止，无论内容长短
- `powershell -Command "..."` — 一律禁止
- `echo "..." > file.txt` / `cat << 'EOF' > file` — 一律禁止
- `Set-Content file "..."` 内嵌多行 — 一律禁止

### 0.4 成功经验沉淀（Success Capture）

**核心原则**：执行过程中观察到的任何优雅解法、踩坑记录、边界洞察，**必须立即保存**，不能依赖「下次我还记得」。

**沉淀路径**：

| 观察到什么 | 保存到哪 | 格式 |
|-----------|---------|------|
| 优雅的脚本/工具解法 | `schema/tool/` 或 task `scripts/` | `.py` / `.ps1` + 登记 `verified-task-index.json` |
| 踩坑记录 | `gotchas/` 目录 | `gotcha-<主题>.md`（YAML frontmatter + 现象 + 根因 + 修复） |
| 设计决策变更 | `DESIGN.md` | 新增章节或修订现有决策 |
| 任务演进历史 | `changelog/` | `changelog-YYYY-MM-DD-<slug>.md` |
| 通用触发条件/规则 | `verified-trigger-index.json` | 按 trigger-index-schema 登记 |

**触发时机**：
- 成功完成一个复杂步骤后 → 检查是否有可提取的通用能力
- 用户说「这个做法很好，以后按这个来」→ 立即固化到 baseline 或工具
- 发现「上次 session 也遇到过」→ 说明早该写入 gotcha，现在补录

### 0.5 动态持续优化（Continuous Improvement）

**核心原则**：Task 不是静态交付物，而是**持续演进的活系统**。每次交互都在增强或削弱这个系统。

**优化循环**：
```
执行 → 观察（成功/失败/异常） → 沉淀（工具/gotcha/决策） → 更新 baseline → 下次执行更优
```

**反模式（禁止）**：
- ❌ 「这次先这么跑通，下次再说」→ 没有下次，session 丢失后完全重置
- ❌ 「改动太小，不值得记录」→ 小改动累积成大混乱，且无法追溯
- ❌ 「baseline 已经定了，不动它」→ baseline 是活的，发现缺陷立即修

**正模式（鼓励）**：
- ✅ 每次 session 结束时自问：「这次有哪些发现应该固化？」
- ✅ 用户指出缺陷时，不仅修复，还要问：「这个缺陷模式是否可能出现在其他 task？」
- ✅ 新工具开发完成后，立即更新 `verified-task-index.json`，让后续 Agent 能发现它


## 1. 语义定义

### 1.1 什么是 Task

Task 是**将一次可复用的工程操作固化为标准化骨架**的单元。特征：

- **有明确生命周期**：预检 → 扫描 → 处理 → 验证 → 比对 → 清理（6 步闭环）。
- **有真源索引**：`ENTRY.json` 是机器唯一入口，人类通过 `README.md`、`SOP.md` 和 `EXEC-CHEATSHEET.md` 进入。
- **有设计文档**：`DESIGN.md` 记录决策、SOP、踩坑，供跨 session 接续。
- **有脚本化调用**：速查表中的每条命令对应磁盘上的独立 `.ps1` / `.py` 文件，禁止现写。

### 1.2 Task 与 Skill 的区别

| 维度 | Task | Skill |
|------|------|-------|
| **定位** | 一次性/周期性工程操作 | 可复用的 Agent 能力扩展 |
| **载体** | `references/tasks/` 目录 | `.agents/skills/` 或 `.opencode/skills/` |
| **入口** | `ENTRY.json` + `run-entry.py` | `SKILL.md` |
| **调用方** | Agent / 人类终端 | 仅 Agent（OpenCode subagent） |
| **生命周期** | 执行完可归档 | 长期驻留 |


## 2. 目录结构规范

```
references/tasks/deploy-git-isolated/
├── README.md                   # 人类入口：任务总览、当前状态、待办、版本
├── GOAL.md                     # 目标闭环
├── SOP.md                      # 标准操作流程
├── DESIGN.md                   # 设计文档
├── ENTRY.json                  # 机器入口：真源索引、脚本清单、Step Manifest
├── task-config.json            # 配置契约：任务级参数、路径、工具链、场景映射
├── task-scenario-triggers.json # 配置契约：触发条件真源
├── TASK-TOOLS-INDEX.md         # 工具索引
├── task-canonical-baseline.md  # 规范基线
│
├── scripts/                    # Python 插件体系三层 + 执行速查
│   │
│   ├── py_lib.py               # Layer 2: Entry（统一入口）
│   │                             拓扑排序 · 依赖补齐 · registry 注入 · profile 筛选
│   │                             所有 workflow 调用的唯一网关
│   │
│   ├── py-plugins/             # Layer 1: Plugins（能力底座）
│   │   ├── archive_config.py       # 归档配置解析（消费 archive-groups.json）
│   │   ├── archive_scanner.py      # 磁盘扫描、黑白名单过滤
│   │   ├── archive_compressor.py   # 7z 压缩、心跳进度
│   │   ├── lint_encoding.py        # BOM/CRLF/LF 检测+修复
│   │   ├── lint_json.py            # JSON 语法验证
│   │   ├── lint_ps1.py             # PS 语法验证
│   │   ├── lint_python.py          # Python 语法验证
│   │   └── ...                     # 单一职责，暴露标准化接口
│   │
│   ├── py-sort-rules.json      # Config 契约：插件注册、依赖图、标签、profile
│   ├── archive-groups.json     # Config 契约：归档分组策略、黑白名单、输出格式
│   │                             （Entry 读取插件注册表；Plugins 消费业务参数）
│   │
│   ├── py-tools/               # Layer 3: Workflow（编排层）
│   │   ├── run-lint.py             # 全量 lint 聚合 workflow
│   │   ├── workflow-lint-amend-lint.py  # lint→amend→lint 闭环 workflow
│   │   ├── archive_project.py      # scan→compress→verify 归档 workflow
│   │   ├── archive_cs_py.py        # 快捷入口：归档 cs_py 分组
│   │   └── archive_venv.py         # 快捷入口：归档 venv 分组
│   │                             职责：编排、env 管理、检查配置、调用 Entry
│   │                             禁止：直接 import plugin；重新实现底层逻辑
│   │
│   ├── EXEC-CHEATSHEET.md      # Workflow 编排的命令真源（Layer 3 组成部件）
│   │                             Agent/人类共享的可执行命令速查
│   │
│   └── ...                     # PS 侧脚本（部署流水线、安全检查等）
│
├── docs/                       # 补充文档
├── changelog/                  # 变更记录
├── gotchas/                    # 踩坑记录
└── archive/                    # 归档目录
```

### 2.1 强制文件

| 文件 | 层级 | 职责 | 是否强制 |
|------|------|------|---------|
| `README.md` | — | 任务总览、状态、待办 | ✅ |
| `GOAL.md` | — | 目标闭环、Stage 路线图、成功标准 | ✅ |
| `SOP.md` | — | **标准流程**（Step 契约 + Ralph Loop） | ✅ |
| `DESIGN.md` | — | 设计决策、踩坑 | ✅ |
| `ENTRY.json` | — | 机器可读真源索引（含 Step Manifest） | ✅ |
| `task-config.json` | **Config 契约** | 任务级参数、路径、工具链、场景映射 | ✅ |
| `py-sort-rules.json` | **Config 契约** | 插件注册表：依赖图、标签、profile 定义 | ✅ |
| `py_lib.py` | **Layer 2: Entry** | 统一入口、拓扑排序、registry 注入 | ✅ |
| `py-plugins/` | **Layer 1: Plugins** | 能力底座（lint、archive、api 等） | ✅ |
| `py-tools/` | **Layer 3: Workflow** | 编排脚本（lint、archive 等 workflow） | ✅ |
| `EXEC-CHEATSHEET.md` | **Layer 3 部件** | Workflow 编排的命令真源 | ✅ |
| `TASK-TOOLS-INDEX.md` | — | **工具索引**（本地 + 外部引用 + 边界） | ✅ |
| `task-canonical-baseline.md` | — | 规范基线、命名约定、修订联动 | ✅ |

### 2.2 可选文件（Config 契约扩展）

| 文件 | 层级 | 职责 | 何时需要 |
|------|------|------|---------|
| `task-scenario-triggers.json` | Config 契约 | 触发条件真源（带 `$schema` 自描述） | task 有触发词映射需求时 |
| `archive-groups.json` | Config 契约 | 归档分组策略、黑白名单、输出格式 | 有 archive workflow 时 |
| `docs/PLUGIN-ARCHITECTURE.md` | — | 架构设计说明 | 有复杂共享库架构时 |


## 3. 文件格式规范

### 3.1 SOP.md（标准操作流程）

> **核心原则**：每个 Step 定义 **Input → Process → Output → Validation** 四元契约，支持 Ralph Loop 自闭环追踪审计。

#### 格式模板

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

#### 强制规则

1. **输入可预期**：不满足 Input 条件不得执行
2. **输出可验证**：必须通过 Validation 后才可进入下一步
3. **过程可追踪**：执行后必须留下 Audit Trail（状态、日志、产物）
4. **失败可回滚**：每个 Step 必须定义 Rollback 路径
5. **禁止混杂命令细节**：SOP 只管「流程是什么、怎么验收」，不管「命令怎么敲」。命令细节见 `EXEC-CHEATSHEET.md`。
6. **禁止混杂工具索引**：SOP 只管「标准流程」，不管「有什么工具、边界在哪」。工具索引见 `TASK-TOOLS-INDEX.md`。

### 3.2 EXEC-CHEATSHEET.md（执行速查表）

> **核心原则**：涵盖命令、配置、参数等所有可执行/可操作内容，不限定于命令行格式。Agent/人类/终端共享同一真源。

#### 格式模板

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

#### 强制规则

1. **真源唯一**：速查表中所有命令指向 `scripts/` 下的同一 `.ps1` 文件，Agent/人类/终端共享。
2. **上下对照**：每个功能区块内先写 Agent 格式，紧接写终端格式，用 `---` 分隔不同功能。
3. **变量约定**：Agent 格式使用 `${devroot}` 等变量；终端格式使用相对路径 `.\references\...`。
4. **执行策略**：Agent 使用 `&` 调用操作符；终端用 `Set-ExecutionPolicy -Scope Process ...;` 前缀。
5. **禁止表格罗列命令**：速查表的主体是**对照代码块**，不是表格。
6. **禁止混杂流程说明**：EXEC-CHEATSHEET 只管「命令怎么执行」，不管「流程是什么、怎么验收」。流程说明见 `SOP.md`。
7. **禁止混杂工具索引**：EXEC-CHEATSHEET 只管「命令怎么执行」，不管「有什么工具、边界在哪」。工具索引见 `TASK-TOOLS-INDEX.md`。


### 3.3 TASK-TOOLS-INDEX.md（工具索引表）

> **核心原则**：回答「这个 task 有什么工具？在哪里？什么时候用？边界是什么？」。
> **与 EXEC-CHEATSHEET 的本质区别**：EXEC-CHEATSHEET 面向「执行者」（知道要做什么，想知道怎么敲命令）；TOOLS-INDEX 面向「规划者」（想知道有哪些能力、该调哪个工具、是否已有现成轮子、能否用外部通用工具替代）。

#### 必须包含的章节

1. **本地专属脚本清单**：按职责分类（部署流水线 / 安全检查 / 通用包装器 / 共享库），每项含 `脚本名 | 职责 | 典型场景 | 状态`
2. **外部通用工具引用**：明确列出本 task 可能用到的 `runtime/`、`schema/tool/` 下的通用工具，每项含 `工具名 | 全局路径 | 登记索引 | 本 task 中的用途 | 边界说明`
3. **边界矩阵**：8+ 个典型场景的首选工具、次选/备选、禁止行为
4. **速查命令**：本地脚本 + 外部通用工具的典型调用命令

#### 强制规则

1. **禁止重复造轮子**：外部已存在且已登记的工具（如 `lint-json.py`、`lint-ps1.ps1`、`check-file-encoding.ps1`），必须在「外部通用工具引用」中列出，并在「边界矩阵」中规定「禁止自行实现同类功能」。
2. **铁律声明**：外部工具引用节必须包含一句铁律——「以上工具已存在且已登记，本 task 禁止自行实现同类功能。新增需求时先查 `verified-task-index.json` → `available_scripts_and_tools`。」
3. **关联文件导航**：底部必须列出与本 task 相关的全部文档的「文件 | 用途」对照表。


### 3.4 SOP vs EXEC-CHEATSHEET vs TASK-TOOLS-INDEX 对比总结

| 对比维度 | SOP.md | EXEC-CHEATSHEET.md | TASK-TOOLS-INDEX.md |
|---------|--------|-------------------|---------------------|
| **核心问题** | 「流程是什么、怎么验收？」 | 「命令怎么执行、参数怎么填？」 | 「有什么工具、边界在哪？」 |
| **内容形式** | Step 契约表格（Input/Process/Output/Validation） | Agent/终端双格式代码块 | 表格清单 + 边界矩阵 + 引用链路 |
| **是否含外部工具** | ❌ 否 | ❌ 否（只含本 task 脚本调用） | ✅ **是**（必须引用 runtime/ 和 schema/tool/ 通用工具） |
| **读者角色** | 流程设计者（确认边界与验收） | 执行者（复制粘贴命令） | 规划者（选择工具、判断边界） |
| **更新时机** | 新增/修改 Step、变更验收条件时 | 新增/修改脚本命令时 | 新增/删除工具、发现外部通用工具可替代时 |
| **典型错误** | 把命令细节塞进来 | 把流程说明塞进来 | 把命令执行细节塞进来 |

> **一句话区分**：SOP 是「流程契约」，EXEC-CHEATSHEET 是「执行手册」，TOOLS-INDEX 是「能力地图」。


### 3.4 ENTRY.json

#### 字段说明

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

#### `sop`、`cheatsheet` 与 `tools_index` 字段语义

- `sop`：指向**标准操作流程**（SOP.md），回答「流程是什么、怎么验收」。
- `cheatsheet`：指向**执行速查表**（EXEC-CHEATSHEET.md），回答「命令怎么执行」。
- `tools_index`：指向**工具索引表**（TASK-TOOLS-INDEX.md），回答「有什么工具、边界在哪」。
- 三者互补，不可互相替代。`ENTRY.json` 必须同时登记三者。


### 3.5 DESIGN.md

- 必须包含「背景」「设计决策」「目标目录结构」「SOP」「踩坑记录」章节。
- 设计决策必须记录「问题 → 方案 → 效果」三步。
- SOP 章节必须与 `SOP.md` 内容一致，但可更详细（含解释性文字）。
- **新增**：Trigger 治理设计意图（第 6 节），记录 trigger 体系的六维元原则（治理、参照、边界、协调、审计、重建）。


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


## 6. 文件位置约定

### 6.1 SOP.md

- **固定位置**：`references/tasks/<task-name>/SOP.md`（task 根目录下，与 README.md/ENTRY.json 同级）
- **原因**：标准操作流程是 task 级别的「流程契约」，不属于 `scripts/`（执行层）也不属于 `docs/`（补充层），应放在 task 根目录作为核心文件之一
- `ENTRY.json` 的 `sop` 字段必须登记路径

### 6.2 EXEC-CHEATSHEET.md

- **默认**：`scripts/EXEC-CHEATSHEET.md`（对齐本 task 的 scripts/ 强绑定风格，因内容与脚本强绑定）
- `ENTRY.json` 的 `cheatsheet` 字段必须如实登记路径

### 6.3 TASK-TOOLS-INDEX.md

- **固定位置**：`references/tasks/<task-name>/TASK-TOOLS-INDEX.md`（task 根目录下，与 README.md/ENTRY.json 同级）
- **原因**：工具索引是 task 级别的「能力地图」，不属于 `scripts/`（执行层）也不属于 `docs/`（补充层），应放在 task 根目录作为核心文件之一
- `ENTRY.json` 的 `tools_index` 字段必须登记路径

> **禁止**：`TASK-TOOLS-INDEX.md`、`SOP.md`、`EXEC-CHEATSHEET.md` 三者内容互相渗透——SOP 管「流程与验收」，EXEC-CHEATSHEET 管「命令执行」，TOOLS-INDEX 管「有什么工具」。


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


## 8. 本 Task 的特殊约定

### 8.1 插件化架构

本 task 采用 `github-lib.ps1` + `lib-sort-rules.json` + `lib-plugins/` 三层插件化架构：

- **文件名冻结**：插件文件一旦命名，永不再改
- **配置与代码分离**：排序规则用独立 JSON 文件承载，不混在代码目录
- **拓扑排序加载**：Kahn 算法按依赖图自动排序，零文件重名即可插入新插件

> 详细架构说明见：`docs/PLUGIN-ARCHITECTURE.md`

### 8.2 Trigger 治理

本 task 的 trigger 索引遵循全局 `verified-trigger-index.json` 的治理规则：

- **新增三步流程**：查重 → 分配 ID → 登记索引 → 回写来源
- **来源文件引用**：task 级触发真源 `task-scenario-triggers.json` 顶部声明 `$schema`
- **边界定义**：`conflict_domains` 节明确定义与 proxy-downloader、download-runtime、project-handoff 的边界

> 治理设计意图见：`DESIGN.md` 第 6 节

### 8.3 外部工具引用铁律

本 task 执行过程中，以下通用能力**禁止自行实现**，必须调用已登记的外部工具：

| 能力 | 外部工具 | 登记位置 |
|------|---------|---------|
| JSON 语法验证 | `schema/tool/lint-json.py` | `verified-task-index.json` → `lint-json` |
| PS 语法验证 | `schema/tool/lint-ps1.ps1` | `verified-task-index.json` → `lint-ps1` |
| 文件编码检查 | `schema/tool/check-file-encoding.ps1` | `verified-task-index.json` → `check-file-encoding` |
| 文件写入 helper | `schema/tool/file-write-helper.py` | `verified-task-index.json` → `file-write-helper` |
| 时间戳生成 | `schema/tool/get-timestamp.ps1` | `verified-task-index.json` → `get-timestamp` |
| 运行时真源检测 | `references/runtime/verify-runtime.ps1` | `verified-task-index.json` → `verify-runtime` |
| 运行时工具下载 | `references/runtime/download-runtime-tool.py` | `verified-task-index.json` → `download-runtime-tool` |


### 8.4 Python 插件体系三层架构（ workflow → entry → plugins ）

> **来源**：用户与 Agent 在 2026-06-19 对话中共同确认。本节是本次 session 的核心共识沉淀，记录"禁止越级调用"的架构铁律。

#### 8.4.1 问题背景

本 task 的 Python 侧已建立 `py_lib.py` + `py-plugins/` + `py-tools/` 体系。但在开发 `workflow-lint-amend-lint.py` 过程中，Agent 曾错误地采用"直接 `import lint_encoding`"的实现方式，被用户判定为**架构越级**——workflow 层直接触碰 plugin 层，绕过了 `py_lib` 统一入口，破坏了入口统一性、审计追踪能力和插件生命周期管理。

本节固化本次讨论后的**正确架构认知**。

#### 8.4.2 三层 + 配置契约

> **核心认知**：本架构是**三层主体 + 配置契约**。
> - **Workflow** 负责编排，调用 Entry 前检查配置有效性
> - **Entry** 读取 Config（插件注册表），拓扑排序后加载 Plugins
> - **Plugins** 消费 Config（业务参数）执行具体能力
> - **Config** 不是独立"层"，而是 Entry 和 Plugins 的**输入契约**；其更新来源包括开发时静态编写、异步事件登记、Workflow 前置检查
> - **EXEC-CHEATSHEET** 是 Workflow 编排的命令真源，属于 Layer 3 的组成部件

```
┌───────────────────────────────────────────────────────────────┐
│  Layer 3: Workflow 编排层（py-tools/ + EXEC-CHEATSHEET）      │
│  ──────────────────────────────────────────────────────────   │
│  run-lint.py                    → 全量 lint 聚合             │
│  workflow-lint-amend-lint.py    → 步骤闭环                   │
│  archive_project.py             → scan → compress → verify   │
│  EXEC-CHEATSHEET.md             → 命令速查真源               │
│  （编排：检查配置 → 设计入参 → 调用 Entry；禁止 import plugin）│
└───────────────────────────────────────────────────────────────┘
                    ↓ 调用 py_lib.load_plugins(profile=...)
┌───────────────────────────────────────────────────────────────┐
│  Layer 2: 统一入口层（scripts/py_lib.py）                     │
│  ──────────────────────────────────────────────────────────   │
│  读取 py-sort-rules.json → 拓扑排序 → 依赖补齐 → 注入 registry │
│  （所有调用的唯一网关；禁止被绕过）                           │
└───────────────────────────────────────────────────────────────┘
                    ↓ 动态加载 + 传递 Config
┌───────────────────────────────────────────────────────────────┐
│  Layer 1: 能力底座层（py-plugins/）                           │
│  ──────────────────────────────────────────────────────────   │
│  lint_encoding.py · lint_json.py · lint_ps1.py               │
│  archive_config.py · archive_scanner.py · archive_compressor │
│  （单一职责，暴露标准化接口；消费 archive-groups.json 等）    │
└───────────────────────────────────────────────────────────────┘

         ╔═══════════════════════════════════════════════════════╗
         ║  Config 契约（*.json）— Entry 与 Plugins 的输入       ║
         ║  py-sort-rules.json  → 插件注册、依赖图、profile      ║
         ║  archive-groups.json → 分组策略、黑白名单             ║
         ║  task-config.json    → 任务参数、路径、场景映射       ║
         ║  （配置与代码分离；来源：开发编写 / 异步登记 / WF 检查）║
         ╚═══════════════════════════════════════════════════════╝
```

#### 8.4.3 各层职责边界

| 层级 | 文件位置 | 职责 | 禁止行为 |
|------|---------|------|---------|
| **Workflow** | `py-tools/*.py` + `EXEC-CHEATSHEET.md` | 步骤编排、env 管理、报告输出；**检查配置有效性**；按速查表/schema 设计入参；调用 Entry | ❌ 禁止直接 `import` plugin；❌ 禁止重新实现检测逻辑 |
| **Entry** | `py_lib.py` | 读取 py-sort-rules.json（插件注册表）、拓扑排序、依赖补齐、registry 注入、profile 筛选、动态加载 Plugins | ❌ 禁止混入业务逻辑；❌ 禁止被绕过 |
| **Plugins** | `py-plugins/*.py` | 单一检测/修复/压缩/扫描能力、暴露标准化接口；消费业务 Config（如 archive-groups.json） | ❌ 禁止依赖 workflow 上下文；❌ 禁止直接读写配置文件 |
| **Config** | `*.json` | 插件注册契约、分组策略、任务参数 | ❌ 禁止嵌入可执行逻辑；不是独立"层"，是 Entry 和 Plugins 的输入 |

#### 8.4.4 架构验证案例：archive_project.py 改造

> **来源**：用户与 Agent 在 2026-06-21 对话中确认。本节是 8.4.3 四层架构的**实证检验**，证明已有 workflow 必须回迁入四层模型。

**问题**：`archive_project.py` 原实现采用"直接 import plugin"的越级模式：
```python
# ❌ 违规：Layer 4 直接触碰 Layer 1，绕过 Layer 3 + Layer 2
sys.path.insert(0, str(_plugins_dir))
from archive_config import get_group_config, find_7z_exe
from archive_scanner import scan_group
from archive_compressor import compress_group
```

**改造后（合规）**：
```python
# ✅ 合规：Layer 4 只通过 Layer 3 (py_lib) 获取能力
from py_lib import load_plugins
registry = load_plugins(devroot=str(devroot), profile="archive")

cfg = registry.archive_config.get_group_config(group_name, devroot)
scan_result = registry.archive_scanner.scan_group(cfg)
compress_result = registry.archive_compressor.compress_group(cfg, seven_zip, fmt, force)
```

**关键收益**：
- `py_lib` 按 `py-sort-rules.json` 自动加载 `archive_config` → `archive_scanner` / `archive_compressor` 的依赖链
- `archive_config` 读取 `archive-groups.json` 获取黑白名单配置（配置与代码分离）
- workflow 只编排 scan → compress → verify 三阶段，不触碰任何底层实现

#### 8.4.5 铁律：禁止越级调用

> **一句话**：Workflow 禁止直接 `import` Plugin。所有能力必须通过 `py_lib.load_plugins()` 获取。

**错误示范（已纠正）**：
```python
# ❌ 越级：workflow 直接 import plugin
from lint_encoding import validate
result = validate(dir_path=target)
```

**正确示范**：
```python
# ✅ 合规：workflow 通过 py_lib 统一入口获取能力
from py_lib import load_plugins
registry = load_plugins(devroot=devroot, tags=["lint", "encoding"])
lint_encoding = registry.lint_encoding
result = lint_encoding.validate(dir_path=target)
```

#### 8.4.6 铁律延伸：文档层面也不暴露插件文件名

> **来源**：用户与 Agent 在 2026-06-20 对话中共同确认。本节是 8.4.5「禁止越级调用」的自然延伸。

**问题**：即使代码层面禁止了 `import plugin`，如果人类速查表（如 `TASK-TOOLS-INDEX.md`）以静态表格形式列出每个插件的文件名、路径和职责，上层调用者（包括 Agent 和人类开发者）仍会**按图索骥**，直接 `import` 或引用具体插件文件，导致越级调用在文档的「诱导」下持续发生。

**判定标准**：
- ❌ 违规：在索引/速查表中直接列出 `lint_json.py`、`md_lint.py` 等具体插件文件名，形成「可用的插件清单」
- ✅ 合规：只说明「有哪些能力类别」（如 JSON lint / Markdown frontmatter 校验 / 编码检测），插件发现通过入口 API 动态获取

**正确示范（文档写法）**：
```markdown
**可用能力**（由 `py_lib` 插件体系动态提供）：

lint 体系覆盖 JSON / PowerShell / Python / Encoding / Markdown / Link 等验证。
具体有哪些插件可用、各自的标签与职责，**通过入口 API 动态发现**。

```python
# 发现全部可用插件（正规入口）
from py_lib import list_plugins
for p in list_plugins():
    print(f"{p['name']}: {p['description']} (tags: {p['tags']})")
```

> **铁律**：插件清单的唯一真源是 `py-sort-rules.json`（机器可读）。人类速查表只说明「有哪些能力类别」，不列出具体插件文件名。
```

**错误示范（已纠正）**：
```markdown
| 插件 | 标签 | 职责 | 状态 |
|------|------|------|------|
| `lint_json.py` | `lint`, `json` | JSON 语法验证 | ready |
| `md_lint.py` | `md`, `validation` | Markdown frontmatter 校验 | ready |
```

#### 8.4.6 案例讲解：workflow-lint-amend-lint.py 的正确实现

**需求**：对指定目录执行"检测 → 修复 → 验证"闭环。

**错误路径（第一次实现）**：
1. workflow 直接 `import lint_encoding`
2. 直接调用 `lint_encoding.validate()`
3. 问题：绕过 `py_lib`，失去统一入口的审计、追踪、依赖管理

**正确路径（修正后）**：
1. workflow `from py_lib import load_plugins`
2. `registry = load_plugins(devroot=..., tags=["lint", "encoding"])`
3. `lint_encoding = registry.lint_encoding`
4. Step 1: `lint_encoding.validate(dir_path=target)` → 检测
5. Step 2: `lint_encoding.validate(dir_path=target, fix=True)` → 修复
6. Step 3: `lint_encoding.validate(dir_path=target)` → 再验证
7. 输出闭环报告

**关键收益**：
- `py_lib` 自动处理 `lint_encoding` 的依赖（如 `core` 插件）
- `py_lib` 自动按 `py-sort-rules.json` 拓扑排序加载
- `py_lib` 将 `devroot` 注入 registry，plugin 可通过 `__plugin_registry__` 访问
- 新增 plugin 只需登记 `py-sort-rules.json`，workflow 无需改代码

#### 8.4.6 扩展新 workflow 的标准模板

```python
#!/usr/bin/env python3
"""
workflow-<name>.py — <描述>
标签：py-tools

职责：通过 py_lib 统一入口加载所需插件，完成 <workflow 目标>。
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def main():
    # 1. 通过 py_lib 获取能力（禁止直接 import plugin）
    registry = load_plugins(devroot=devroot, tags=["<tag1>", "<tag2>"])
    plugin = registry.<plugin_name>

    # 2. 编排 workflow 步骤
    # ...


if __name__ == "__main__":
    main()
```

#### 8.4.7 插件间通信规则：同层插件允许直接 import

> **来源**：用户与 Agent 在 2026-06-21 对话中共同确认。本节是 8.4.5「禁止越级调用」的边界补充，明确"禁止越级"不等于"禁止插件间协作"。

**核心规则**：

| 通信方向 | 是否允许 | 理由 |
|---------|---------|------|
| Workflow → Plugin | ❌ 禁止 | 必须经 py_lib 统一入口，保持入口唯一性 |
| Plugin → Plugin（同层） | ✅ 允许 | 不暴露给 Workflow，属于底座层内部通信 |
| Plugin → Workflow | ❌ 禁止 | 插件禁止反向依赖上层 |

**判定标准**：
- **是否暴露给 Workflow**：如果 Plugin A 直接 import Plugin B，而 Workflow 完全不知道这个调用关系，则属于同层通信，许可。
- **是否破坏入口统一性**：同层 import 不涉及 py_lib 入口，不破坏 workflow → entry → plugin 的单向调用链。

**正确示范**：
```python
# archive_scanner.py (Plugin) 直接 import archive_empty_handler.py (Plugin)
# ✅ 合规：同层通信，不暴露给 workflow
from archive_empty_handler import (
    cleanup_emptydirs,
    detect_empty_dirs,
    detect_zero_byte_files,
    fill_emptydirs,
    write_detail_list,
)

def scan_group(cfg):
    # ... 扫描逻辑 ...
    empty_dirs = detect_empty_dirs(entries)  # 调用同层插件能力
    fill_emptydirs(empty_dirs, src, arcname)  # 调用同层插件能力
```

**错误示范**：
```python
# ❌ 违规：workflow 直接 import plugin（越级）
from archive_empty_handler import detect_empty_dirs
```

**边界说明**：
- 同层 import 必须是"按需、最小化"的：Plugin A 只 import Plugin B 中它需要的函数，不 import 整个模块。
- 如果同层通信涉及多个插件的复杂编排，应评估是否需要将逻辑上提到 Entry 层或拆分为新的独立插件。

#### 8.4.8 修订联动

新增/修改 workflow 时，必须同步更新：

| 联动文件 | 更新内容 |
|---------|---------|
| `EXEC-CHEATSHEET.md` | 新增 workflow 调用命令示例 |
| `TASK-TOOLS-INDEX.md` | 在 CLI 入口表登记新 workflow |
| `README.md` | 文件导航表和当前状态表追加 |
| `py-sort-rules.json` | 如需新增 plugin，登记插件定义和 profile |

#### 8.4.9 Layer 3 内部细分：原子型 vs 编排型

> **来源**：用户与 Agent 在 2026-06-21 对话中共同确认。本节是 8.4 节「三层架构」的边界补充，明确 Layer 3（py-tools/）内部的两档形态差异。

**核心认知**：py-tools/ 下的脚本**全部属于 Layer 3**，但形态和引用方式截然不同，必须区分：

| 维度 | 原子型 Workflow（Atomic Tool） | 编排型 Workflow（Orchestration Script） |
|------|------------------------------|----------------------------------------|
| **定位** | 封装单一原子操作，可被上层引用 | 串联多步骤的完整剧本，顶层入口 |
| **职责** | 只做一件事，输出标准化 | 完成一个完整目标，含步骤编排 |
| **被引用** | ✅ 可被其他 Workflow 通过 subprocess 调用 | ❌ 禁止被引用，避免流程嵌套 |
| **副作用** | 无或可控 | 通常有不可逆副作用（push、压缩） |
| **JSON 配置** | 通常 **不配**（参数驱动） | 步骤可能变动时 **必须外化** |
| **范例** | `get-timestamp.py`、`run-lint.py`、`fetch_issue.py` | `workflow-deploy-full.py`、`archive_project.py` |

**铁律**：
1. 编排型 Workflow 禁止被其他 Workflow 引用。
2. 原子型 Workflow 通过 subprocess 调用，禁止 import，保持层间隔离。
3. JSON 配置只给"数据会变、代码不想变"的场景配。

> 详细决策逻辑与范例见：`docs/patterns/atomic-vs-orchestration-workflow.md`

### 8.5 标准文档与实现代码的真源对齐原则

> **来源**：用户与 Agent 在 2026-06-20 对话中共同确认。本节解决「标准文档 vs 实现代码不一致时以谁为准」的裁决问题。

#### 8.5.1 问题背景

本 task 存在多组「标准文档 + 实现代码」的配对关系：

| 标准文档（What：规则是什么） | 实现代码（How：如何检测/执行） |
|---------------------------|------------------------------|
| `.cursor/rules/markdown-docs-format.mdc` | `md_lint.py` |

此前未明确两者的主从关系，导致 Agent 在修改时可能：
- 只改实现代码，不同步标准文档 → 标准过期
- 只改标准文档，不同步实现代码 → 实现与标准脱节
- 实现代码自行扩展规则 → 标准文档失去唯一真源地位

#### 8.5.2 铁律：标准文档是唯一真源

**层级定义**：
- **标准文档**（如 `.mdc` 规则文件）：人类可读的真源标准，定义「应该是什么」
- **实现代码**（如 `.py` 插件）：标准文档的**忠实实现**，定义「如何检测/执行」

**裁决规则**：
1. **标准 vs 实现不一致 → 以标准文档为准，修正实现代码**
2. **实现代码发现标准文档未覆盖的边界 → 先修订标准文档，再同步实现**
3. **禁止实现代码自行扩展规则而不更新标准文档**

**错误示范（已纠正）**：
```python
# md_lint.py 自行增加 frontmatter 字段检测
# 但 markdown-docs-format.mdc 中未定义该字段
# → 实现超前于标准，形成双轨制
```

**正确示范**：
```markdown
# Step 1: 修订标准文档（markdown-docs-format.mdc）
# 新增 meta 必填字段、description/date 拼接禁忌

# Step 2: 同步实现代码（md_lint.py）
# 按 mdc 新增的规则实现对应检测逻辑

# Step 3: 双向验证
# mdc 描述的规则 ↔ md_lint 实现的校验 ↔ 实际扫描结果 三者一致
```

#### 8.5.3 应用到本 task

| 标准文档 | 实现代码 | 同步检查清单 |
|---------|---------|------------|
| `.cursor/rules/markdown-docs-format.mdc` | `md_lint.py` | mdc 中每条规定是否有对应的检测逻辑？md_lint 的每个检测项是否在 mdc 中有出处？ |

**修订联动触发条件**：
- 修改 `markdown-docs-format.mdc` → **必须**检查 `md_lint.py` 是否需要同步更新
- 增强 `md_lint.py` 检测能力 → **必须**检查 `markdown-docs-format.mdc` 是否需要补充规则定义
- 两者任一改版 → 在 `md_lint.py` 的 docstring 中更新版本号，并注明「与 mdc X.X 对齐」


*规范版本: v1.3*  
*模板来源: schema/task-template/task-canonical-baseline.md*  
*创建时间: 2026-06-16*  
*本 task 定制内容: 第 3.2/3.3 节（SOP vs TOOLS-INDEX 区分）、第 6.2 节（TASK-TOOLS-INDEX 位置约定）、第 8 节（本 task 特殊约定）*  
*本次修订: 2026-06-20，新增第 8.4.5 节（文档不暴露插件文件名）、第 8.5 节（标准文档与实现代码真源对齐）*
