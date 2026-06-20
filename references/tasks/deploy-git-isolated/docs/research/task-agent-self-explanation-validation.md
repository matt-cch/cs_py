---
title: Task Agent 自说明能力验证 — 从零上下文到自主执行的探索实验
description: 记录通过 task 子进程验证 deploy-git-isolated 目录自说明能力的完整实验过程，含上下文审计、自主探索测试、关键发现与改进建议。
date: 2026-06-19
meta: {}
---

# Task Agent 自说明能力验证 — 从零上下文到自主执行的探索实验

> **文档性质**：深度研究记录 / 验证实验报告。  
> **受众**：task 文档维护者、后续验证者、架构评审。  
> **实验时间**：2026-06-19  
> **实验执行者**：主 Agent（当前 session）→ task 子进程（零上下文 Agent）


## 一、实验背景与动机

### 1.1 为什么要做这个验证

deploy-git-isolated task 目录经过多轮迭代，已形成相当完整的文档体系（6 层文档结构）和工具链（双层插件化体系）。一个自然产生的问题是：

> **如果一个完全零上下文的 Agent 拿到这个 task 目录，它能否仅通过阅读目录内的文档，就理解工作方式并正确执行任务？**

这个问题不是学术好奇，而是直接关系到：
- 当未来有新人（或新 Agent session）接手这个 task 时，学习成本有多低
- task 文档的「自说明能力」是否足以替代口头交接
- 文档与代码之间是否存在「知行 gap」——文档写得清楚，但执行路径没有被遵守

### 1.2 实验目标

| 目标 | 验证点 |
|------|--------|
| 文档可读性 | 零上下文 Agent 能否通过阅读 README → GOAL → SOP → DESIGN 等文档，理解 task 全貌 |
| 工具可发现性 | Agent 能否自主找到 `py_lib.py`、`py-plugins/` 等已有工具，而非重新造轮子 |
| 架构遵守度 | Agent 在理解「workflow → py_lib → plugins 三层架构」后，是否会在执行中遵守「禁止越级调用」 |
| 规则执行力 | Agent 在拥有完整 `.mdc` 规则体系的情况下，是否会违反 Shell 禁令、编码规范等硬性约束 |


## 二、实验设计

### 2.1 两步验证法

实验分为两个阶段：

**阶段一：上下文审计**  
先让一个 task 子进程落盘它启动时能感知到的全部初始上下文，确认「零上下文」到底有多「零」。

**阶段二：自主探索测试**  
给另一个 task 子进程一个模糊 prompt（不透露技术细节），观察它能否：
1. 先读 README.md 理解 task 结构
2. 找到已有的 lint 工具和 workflow
3. 通过 `py_lib.load_plugins()` 加载插件（而非直接 import）
4. 执行 lint 并输出报告
5. 遵守所有 `.mdc` 硬性约束

### 2.2 Prompt 设计原则

Prompt 刻意保持「自然人类式」，不透露任何技术实现细节：

> "阅读理解 @task 目录，根据目录可提供的示例和工具，写一个 tmp 下的 py 脚本，lint 这个 task 目录下的所有 md 文档的内容格式，结果输出到 tmp 下。"

**测试点**：
- 是否会先读 README.md？
- 是否会找到 py_lib 体系？
- 是否会通过 `py_lib.load_plugins()` 加载插件？
- 是否会更新修订联动？
- 是否会跑 lint 验证？


## 三、阶段一：上下文审计

### 3.1 审计方法

调用 `task` 工具创建子进程，指令：将启动时能感知到的所有初始上下文信息写入 `venv/tmp/subagent-context-audit-*.txt`。

### 3.2 审计结果

子进程落盘的审计文件（337 行）揭示了以下关键事实：

#### 子进程拥有什么

| 类别 | 内容 | 评价 |
|------|------|------|
| **通用系统提示** | OpenCode Agent 完整行为准则 | 标准配置 |
| **项目规则体系** | `AGENTS.md` + **18 个 `.mdc` 规则文件** 全部内嵌 | **非常关键** — 知道所有硬性约束 |
| **可用工具** | `bash`, `edit`, `glob`, `grep`, `read`, `skill`, `webfetch`, `write` | 标准工具集 |
| **可用技能目录** | 12 个 skills 的名称 + 路径 + 描述 | 仅目录，内容不会自动加载 |
| **项目结构概览** | `PROJECT-STRUCTURE.md` 内嵌 | 知道目录组织意图 |
| **环境元数据** | 工作目录、平台、日期 | 基础上下文 |

#### 子进程没有什么

| 缺失项 | 影响 |
|--------|------|
| **对话历史** | 完全不知道 deploy-git-isolated task 的存在、workflow-entry-plugins 架构决策、lint 插件体系等 |
| **当前任务状态** | 不知道已完成哪些步骤、next steps 是什么 |
| **技能内容** | 知道有 `github-proxy-downloader`，但不知道具体流程 |
| **文件系统缓存** | 没有 `read` 过任何文件，一切从零开始 |

### 3.3 关键结论

**子进程是一个「规则完整、业务空白」的起点。**

它内嵌了全部 18 个 `.mdc` 和 `AGENTS.md`，意味着它：
- 知道必须 `read` 后再 `write`
- 知道禁止 `python -c`、`powershell -Command`
- 知道工具链必须使用绝对路径
- 知道任何 `bash`/`write`/`edit` 调用前要输出【Tool 调用规则层审计】
- 知道高频任务触发词（真源检测、记 version 等）

**这为后续自主探索测试提供了基础：子进程有规则约束，但业务知识完全依赖 task 文档。**


## 四、阶段二：自主探索测试

### 4.1 实验执行

调用 `task` 子进程，给它模糊 prompt，让它：
1. 阅读 `deploy-git-isolated` 目录
2. 写一个 Python 脚本 lint 所有 `.md` 文件
3. 输出报告到 `venv/tmp/`

### 4.2 子进程的关键发现（来自其回复摘要）

子进程在阅读目录后，产出了以下**非常准确**的理解：

| 维度 | 子进程的发现 |
|------|-------------|
| **文档体系** | 识别出 6 层文档结构：`README.md` → `GOAL.md` → `SOP.md` → `DESIGN.md` → `TASK-TOOLS-INDEX.md` → `task-canonical-baseline.md` |
| **机器真源** | 发现 `ENTRY.json` 是机器唯一入口，`task-config.json` 含路径配置，`task-scenario-triggers.json` 含触发条件 |
| **脚本架构** | 准确描述双层插件化体系：PS 侧（`github-lib.ps1` + `lib-sort-rules.json` + `lib-plugins/`）与 Python 侧（`py_lib.py` + `py-sort-rules.json` + `py-plugins/`） |
| **架构铁律** | 明确提到「拓扑排序 + Profile 筛选 + 依赖自动补齐」的三层架构，并指出「**禁止越级调用**」 |
| **lint 体系** | 发现已内置 `md_lint.py`、`lint_encoding.py`、`lint_json.py`、`lint_ps1.py`、`lint_python.py`，全部通过 `py_lib.load_plugins()` 加载 |
| **格式规范** | 准确列出 `.md` 文件的 5 项格式要求：YAML frontmatter、`title`/`description`/`date`、禁止 `---` 分隔线、LF、UTF-8 无 BOM |

### 4.3 子进程的实际产出

| 产物 | 路径 | 状态 |
|------|------|------|
| Python lint 脚本 | `venv/tmp/task-md-lint-test.py` | ✅ 语法通过 `python -m py_compile`，执行成功 |
| Markdown 报告 | `venv/tmp/task-md-lint-report.md` | ✅ 内容完整，21 个文件，16 通过，5 失败 |

### 4.4 检测结果验证

子进程报告 **5 个文件失败**，主 Agent 逐一手动验证：

| 文件 | 子进程报告的问题 | 实际验证结果 |
|------|-----------------|-------------|
| `docs/harness/delivery-checklist.md` | 缺少 `date` 字段 | ✅ 属实 — `date: 2026-06-17` 被拼接到 `description` 行末尾 |
| `docs/patterns/profile-filter-pattern.md` | 缺少 `date` 字段 | ✅ 属实 — 同上 |
| `docs/README.md` | 缺少 `date` 字段 | ✅ 属实 — 同上 |
| `docs/research/scripts-directory-taxonomy-research.md` | 缺少 `date` 字段 | ✅ 属实 — 同上 |
| `docs/research/task-dependency-graph.md` | 缺少 `date` 字段 | ✅ 属实 — 同上 |

**所有 5 处失败均属实**，这是此前 task 全量 lint（0 违规）未覆盖到的 frontmatter 格式缺陷。


## 五、关键发现：知行 Gap

### 5.1 子进程「读懂了规范，但没有遵守执行路径」

这是最核心的发现。

子进程在回复中**准确描述**了 workflow-entry-plugins 三层架构：

> "Python 侧（`py_lib.py` + `py-sort-rules.json` + `py-plugins/`）均采用「拓扑排序 + Profile 筛选 + 依赖自动补齐」的三层架构（Workflow → Entry → Plugins），并明令**禁止越级调用**。"

然而它写的 `task-md-lint-test.py` 却**完全没有使用**这个体系：
- ❌ 没有 `import py_lib` 或调用 `py_lib.load_plugins()`
- ❌ 没有复用已有的 `lint_encoding.py`（BOM/CRLF/LF 检测）
- ❌ 没有复用已有的 `md_lint.py`（frontmatter 检测）
- ❌ 自己重新实现了全部 5 项检测逻辑

**这是一个典型的「理解规范但不执行规范」案例。**

### 5.2 根本原因分析：Task 文档的约束力盲区

| 层级 | 当前状态 | 问题 |
|------|---------|------|
| **规则层**（AGENTS.md、.mdc） | ✅ 完整加载 | 子进程知道"禁止越级调用" |
| **文档层**（README、DESIGN） | ✅ 子进程读懂了 | 知道有三层架构 |
| **契约层**（task 入口约定） | ⚠️ **薄弱** | README 没有**强制要求**"任何 lint 任务必须通过 `py_lib` 加载插件" |
| **示例层**（已有 workflow） | ⚠️ 不足 | `run-lint.py` 存在，但子进程没有把它当作"唯一正确路径" |

**结论**：task 文档告诉 agent「这是什么」，但**没有足够强的机制**阻止 agent 走捷径。

### 5.3 对比：子进程 vs 当前会话

| 行为 | 子进程（零上下文） | 当前会话（有上下文） |
|------|------------------|-------------------|
| 是否知道 deploy-git-isolated | 从零阅读 | 全程参与建设 |
| 是否使用 py_lib 体系 | ❌ 未使用 | ✅ 强制使用 |
| 是否遵守"禁止越级调用" | ❌ 未触发 | ✅ 遵守 |
| 检测结果 | 5 个文件失败 | 此前 task 全量 lint 通过（0 违规） |
| 原因 | 独立实现的检测逻辑更严格 | 此前的 lint 可能未覆盖 frontmatter 字段拼接问题 |

**意外收获**：子进程独立实现的 frontmatter 解析逻辑恰好发现了此前 lint 体系的盲区 — `date` 字段被拼接到 `description` 行末尾，而不是独立成行。


## 六、洞见与改进建议

### 6.1 洞见一：规则继承 ≠ 行为继承

Subagent 拥有完整的规则体系（18 个 `.mdc` + AGENTS.md），这保证了它不会：
- 用 `python -c` 写脚本
- 用 `powershell -Command` 内嵌逻辑
- 忘记 `read` 就 `write` 覆盖文件
- 使用相对路径调用工具链

但规则体系**不能**保证它会：
- 优先复用已有插件而非重新造轮子
- 把 `run-lint.py` 当作 lint 任务的唯一入口
- 遵守「禁止越级调用」的架构铁律

**规则管的是「不能做什么」，架构管的是「应该怎么做」。后者需要更强的契约约束。**

### 6.2 洞见二：Task 文档需要「执行路径守卫」

当前 task 文档是「描述性」的（这是什么、为什么这样设计），缺乏「指令性」的约定（任何新增工具/脚本必须怎么做）。

建议在 `task-canonical-baseline.md` 中增加条款：

> **新增工具/脚本的强制检索义务**：在任何新增检测能力、工具脚本或 workflow 之前，必须先检查 `py-sort-rules.json` 和 `py-plugins/` 下是否已有能力覆盖相同需求。禁止在未检索已有插件的情况下重新实现相同功能。若确有新增必要，须在 `DESIGN.md` 或相关研究文档中记录「为何不复用已有能力」。

### 6.3 洞见三：入口脚本需要「自检宣言」

`run-lint.py` 不应只是"聚合入口"，还应在启动时输出「能力地图」：

```python
# 在 run_lint() 开头增加
print("=" * 50)
print("deploy-git-isolated Lint 入口")
print("=" * 50)
print("本次将加载以下插件：")
for p in sorted(plugins.keys()):
    print(f"  - {p}")
print("\n若你需要新增检测项，请先确认上述插件是否已覆盖。")
print("新增插件请遵循 workflow → py_lib → plugins 三层架构。")
print("=" * 50)
```

这样，即使未来有 agent 直接阅读 `run-lint.py` 源码，也能被引导到正确的执行路径。

### 6.4 洞见四：验证本身的价值被低估

本次实验意外发现了 5 个 frontmatter 格式缺陷，这说明：
- **已有的 lint 体系有盲区**：`md_lint.py` 或 `lint_encoding.py` 没有覆盖「`date` 被拼接到 `description` 行」的场景
- **独立实现有独立价值**：子进程从零实现的解析逻辑，恰好补上了这个盲区
- **定期用「陌生 agent」验证文档，是发现盲区的有效手段**

建议将「agent 自说明能力验证」纳入 task 的周期性质量门禁，类似 `workflow-lint-amend-lint.py` 的闭环逻辑。


## 七、待办与后续行动

| # | 行动 | 优先级 | 负责人 |
|---|------|--------|--------|
| 1 | 修复 5 个 frontmatter 缺陷（`date` 字段独立成行） | 高 | 主 Agent |
| 2 | 在 `task-canonical-baseline.md` 中增加「强制检索已有插件」条款 | 高 | 主 Agent |
| 3 | 在 `run-lint.py` 中增加「能力地图」自检宣言 | 中 | 后续 session |
| 4 | 增强 `md_lint.py` 或 frontmatter 检测逻辑，覆盖「字段被拼接到前一行」的场景 | 中 | 后续 session |
| 5 | 将「agent 自说明能力验证」纳入周期性质量门禁 | 低 | 后续维护者 |


## 八、实验复盘

### 8.1 实验成功之处

- ✅ 验证了 subagent 的初始上下文状态（规则完整、业务空白）
- ✅ 验证了 task 文档的可读性（子进程能准确理解 6 层文档结构和三层架构）
- ✅ 验证了 task 文档的约束力（子进程遵守了所有 `.mdc` 硬性约束）
- ✅ 意外发现了 5 个 frontmatter 格式缺陷和 lint 体系盲区

### 8.2 实验局限

- ⚠️ 仅测试了一个 subagent 实例，样本量有限
- ⚠️ Prompt 设计较为宽泛，未测试「更明确的约束性 prompt」是否能引导子进程使用 `py_lib`
- ⚠️ 未测试 `opencode serve` + `run` 的独立进程模式，无法确认其与子进程的差异

### 8.3 经验沉淀

> **一句话总结**：文档能教会 agent「这是什么」，但不能保证 agent「会这么做」。执行路径的约束需要文档、代码、入口自检三层合力。


***

*实验报告版本: v1.0*  
*生成时间: 2026-06-19*  
*实验产物: `venv/tmp/task-md-lint-test.py`, `venv/tmp/task-md-lint-report.md`, `venv/tmp/subagent-context-audit-*.txt`*
