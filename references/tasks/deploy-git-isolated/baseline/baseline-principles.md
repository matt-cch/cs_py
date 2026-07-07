---
title: deploy-git-isolated — Agent 执行哲学与工程化铁律
description: 顶层原则声明：禁止现写命令行、Tool-First、Long-Content 落盘、成功经验沉淀、动态持续优化、Workflow 自闭环、显式优于隐性。所有后续章节均受本文件约束。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# Agent 执行哲学与工程化铁律

> **来源**：用户明确确认（2026-06-18 起陆续确认）。本文档是**顶层原则声明**，所有后续 baseline 文件均受本文件约束。违反本节任一条款视为操作事故。


## 0.1 禁止现写命令行（No Ad-hoc Shell）

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


## 0.2 优先复用现成工具（Tool-First）

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


## 0.3 Long-Content 分步落盘（Write-to-Disk Pipeline）

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


## 0.4 成功经验沉淀（Success Capture）

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


## 0.5 动态持续优化（Continuous Improvement）

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


## 0.6 Workflow 自闭环执行铁律（No Ad-hoc Intervention）

> **来源**：用户明确确认（2026-06-25）。本节定义 workflow 与 SKILL.md 的本质边界，以及 Agent 在执行 workflow 时的行为红线。

### 0.6.1 Workflow 的本质

Workflow 是 **human 与 AI 共同设计、审核、验证过的既定步骤集合**。它的核心特征是**步骤已固化**，执行时不需要 AI 再做任何判断、分支选择或事前验证。

| 特征 | Workflow | SKILL.md |
|------|---------|----------|
| **设计方式** | human + AI 共同讨论、审核、验证后固化 | AI 单方面实现，human 事后 review |
| **执行主体** | 代码控制（脚本按既定顺序执行） | AI 持续在场，每轮判断、调整、决策 |
| **preflight** | 代码内置（workflow 自己的 step-00） | AI 临场判断是否需要检查 |
| **分支判断** | 代码内置（if/else，配置文件驱动） | AI 根据上下文临场决定走哪条路径 |
| **事后总结** | 代码输出（日志、报告、meta 文件） | AI 生成自然语言总结 |
| **AI 角色** | **不在场** — 只负责构造入参、执行命令、等待结果 | **在场** — 持续介入每一步的判断 |

### 0.6.2 Agent 执行 workflow 时的行为红线

**铁律**：

1. **执行前禁止预检**
   - ❌ 禁止在调用 workflow 之前，现写 bash 命令检查 `.env` / `config.json` / 文件存在性
   - ✅ workflow 自己的 `step-00-preflight` 或内联 `_preflight_check()` 已经做了这些检查
   - 如果 preflight 不生效，**修 workflow**，而不是绕过它

2. **执行中禁止干预**
   - ❌ 禁止在 workflow 执行过程中，根据中间输出判断「要不要继续」「要不要改参数」「要不要跳过某步」
   - ✅ workflow 内部的判断逻辑（returncode 检查、超时处理、fallback）由代码控制
   - ✅ **workflow 可以包含调用 AI 服务的步骤**（如 `generate-ai-summary.py`），但必须是**预先设计验证好的固定步骤**，调用方式由代码控制（`subprocess.run` 或 `py_lib` 插件调用）
   - AI 只负责：构造完整准确的入参 → 执行一条命令 → 等待最终输出

3. **执行后禁止替代总结**
   - ❌ 禁止在 workflow 已经输出完整报告后，AI 再「用自己的话重新总结一遍」
   - ✅ workflow 的日志、meta 文件、stdout 就是最终输出
   - AI 可以复述结果，但不得替代 workflow 本身的报告机制

4. **失败时禁止绕过**
   - ❌ workflow 失败后，禁止用 bash 手动补做 workflow 该做的事
   - ✅ 读取 workflow 的错误输出 → 判断是入参问题还是 workflow 缺陷 → 修入参或修 workflow → 重新执行

### 0.6.3 正确示范 vs 错误示范

**错误示范（已发生）**：
```
用户：执行一遍自动部署
Agent：先让我检查一下 .env 配置...（现写 bash 检查 GIT_USER_NAME）
Agent：再检查一下 config.json...（现写 bash 检查 api_key）
Agent：好，现在执行 workflow...
```

**正确示范**：
```
用户：执行一遍自动部署
Agent：构造入参 → 执行 workflow-deploy-full.py --auto → 等待结果
```

**区别**：workflow 自己的 `_preflight_check()` 已经检查了 `.env` 和 `config.json`。Agent 先手动检查一遍，然后 workflow 自己又检查一遍，完全重复，浪费 token，且破坏了 workflow 的自闭环原则。

### 0.6.4 与 SKILL.md 的本质区别

详见 [baseline-semantics.md](baseline-semantics.md) 1.3 节。


## 0.7 显式优于隐含（Explicit over Implicit）

> **来源**：用户明确确认（2026-07-01）。本节定义所有脚本执行时的路径与上下文管理铁律。

**核心原则**：绝不依赖任何默认行为、隐式解析、或当前环境的"恰好正确"。一切执行上下文必须显式设定、显式验证。

**为什么必须显式**：
- 默认行为会随调用环境（shell CWD、PATH、终端编码）变化，不可预期
- 隐式解析（如 `git add .` 的 `.`、相对路径的基准点）在跨目录调用时必然出错
- 显式设定使行为可审计、可复现、可跨 session 一致

**铁律**：

| 场景 | 隐含做法（禁止） | 显式做法（必须） |
|------|---------------|---------------|
| 指定执行目录 | `git add .`（依赖 shell CWD） | `os.chdir(devroot)` + `git add -A`；或 `git -C <absolute_path> add -A` |
| 调用解释器 | `python script.py`（依赖 PATH） | `absolute_path/python.exe absolute_path/script.py` |
| 指定工作目录 | `--devroot` 参数但不切换 CWD | `--devroot` + 入口处显式 `chdir` |
| 路径解析 | 相对路径 `./xxx` | 绝对路径拼接 `devroot / "subdir" / "file"` |
| 验证执行环境 | 假设当前目录正确 | `assert Path.cwd() == devroot` 或等价验证 |

**对 workflow 的要求**：
- 所有 workflow 脚本（`workflow-*.py`）的 `main()` 入口必须在参数解析后立即执行 `os.chdir(devroot)`，确保整个进程 CWD 与 `--devroot` 一致
- 所有 step 脚本在执行文件操作前，必须显式传入绝对路径或使用 `-C` 切换目录
- 禁止在任何脚本中使用裸 `./` 或 `.` 指代目标目录
- **多端多 devroot 支持**：`--devroot` 默认值必须是 `Path.cwd()`（或等效机制），禁止硬编码为任何固定路径。同一套 workflow 工具链必须能通过 `--devroot` 切换服务于多个独立仓库（polyrepo）
- **文档示例必须显式传 `--devroot`**：所有命令示例包含 `--devroot "${devroot}"`，禁止展示省略简写形式，防止 Agent 或用户因 CWD 不同而操作错误仓库

### 0.7.1 多端多 devroot 多 polyrepo 架构

> **来源**：用户明确确认（2026-07-07）。本节是"显式优于隐含"原则在 workflow 工具层面的具体化。

**三层约束**：

| 层级 | 规则 | 原因 |
|------|------|------|
| **代码实现** | `--devroot` 默认值必须是 `Path.cwd()`，禁止硬编码 | 支持多端执行：用户在任意目录打开终端，workflow 自动操作当前目录的仓库 |
| **CLI 调用** | 实际执行时必须显式传入 `--devroot` | 贯彻"显式优于隐含"，避免 CWD 与预期不一致导致的隐式错误 |
| **文档示例** | 所有命令示例必须包含 `--devroot "${devroot}"` | 防止 Agent 或用户复制命令时因 CWD 不同而操作错误仓库 |

**多 polyrepo 支持**：
同一套 workflow 工具链可服务于多个独立仓库，只需通过 `--devroot` 切换目标仓库。Agent 在 workspace 模式下必须显式指定 `--devroot`，禁止依赖 IDE 隐式工作目录。

**错误示例**：
```powershell
# ❌ 硬编码 devroot（禁止）
python workflow-deploy-full.py --auto

# ❌ 依赖 CWD 隐式解析（文档示例中禁止）
python workflow-deploy-full.py --message "feat: xxx"
```

**正确示例**：
```powershell
# ✅ 显式传入 devroot
python workflow-deploy-full.py --devroot "${devroot}" --auto

# ✅ 指向另一个 polyrepo
python workflow-deploy-full.py --devroot "D:\workspace\other-repo" --auto
```


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
