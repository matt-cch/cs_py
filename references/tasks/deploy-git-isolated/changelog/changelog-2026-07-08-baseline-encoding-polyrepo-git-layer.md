---
title: deploy-git-isolated — baseline 增量更新：编码换行符规范 + Polyrepo Git 配置分层
description: baseline-formats.md 新增 3.7 节（文件编码与换行符跨平台一致性），baseline-structure.md 新增 2.3 节（polyrepo 嵌套仓库的 Git 配置分层），baseline-index.md 同步更新导航描述。
date: 2026-07-08
meta: {}
---

# deploy-git-isolated — baseline 增量更新：编码换行符规范 + Polyrepo Git 配置分层

## 变更概览

| 属性 | 值 |
|------|-----|
| **变更类型** | 框架层规范增补（baseline 增量） |
| **影响范围** | `baseline/baseline-formats.md`、`baseline/baseline-structure.md`、`baseline/baseline-index.md` |
| **风险等级** | 低（纯规范增补，无行为变更） |
| **触发原因** | CRLF/LF 换行符治理 session 中形成的跨平台一致性共识需要固化到 baseline |


## 变更时间线

### 2026-07-08 — 编码与换行符规范（baseline-formats.md §3.7 新增）

| 变更项 | 内容 |
|--------|------|
| **新增章节** | 3.7 文件编码与换行符规范 |
| **核心共识** | 本地 `.gitattributes` 显式声明，不依赖全局 `core.autocrlf`，确保任何平台 checkout 后字节流一致 |
| **分层策略** | `.ps1/.bat/.cmd` → CRLF 豁免；其他全部文本文件 → 强制 LF；二进制 → `binary` 声明 |
| **lint 联动** | `lint_encoding.py` 检测范围：「除 `.ps1`/`.bat`/`.cmd` 外全部文本文件」 |
| **`.gitattributes` 跟踪策略** | **不跟踪**（被 `.gitignore` 排除），仅供本地开发，避免与远程团队工作流冲突 |
| **最小配置模板** | 提供可直接复制的 `.gitattributes` 模板（含 `* text eol=lf`、`.ps1 -text`、二进制声明） |

### 2026-07-08 — Polyrepo 嵌套仓库 Git 配置分层（baseline-structure.md §2.3 新增）

| 变更项 | 内容 |
|--------|------|
| **新增章节** | 2.3 Polyrepo 嵌套仓库的 Git 配置分层 |
| **问题根因** | monorepo（cs_py）内嵌独立 polyrepo（如 jywl-lab）时，各 `.git/` 作用域独立，根级 `.gitattributes` 对嵌套仓库无效 |
| **分层原则** | 主仓库与嵌套仓库**分别独立**配置 `.gitattributes`；配置不继承、作用域不穿透、内容可差异 |
| **与 workflow 原则的关系** | 与 `baseline-principles.md` §0.7.1（workflow 多端多 devroot）形成互补：workflow 层控制「脚本操作哪个仓库」，Git 层控制「checkout 时换行符如何转换」 |
| **铁律** | Agent 操作嵌套 polyrepo 时必须分别检查各仓库的 `.gitattributes` 存在性，禁止假设根级配置对嵌套仓库有效 |

### 2026-07-08 — 隔离 Git 优先原则（baseline-principles.md §0.7.2 新增）

> **用户澄清**：本项目严格使用隔离版 Git（`venv/data-git/`），为不同的 `.git/` 配置 `.gitignore/.gitattributes`，基本不使用全局/IDE Git（但保持灵活性）。

| 变更项 | 内容 |
|--------|------|
| **新增章节** | 0.7.2 隔离 Git 优先（Isolated Git First） |
| **核心原则** | 所有 Git 操作默认使用隔离 Git，不依赖系统全局 Git 或 IDE 内置 Git |
| **为什么** | 配置可预期、跨环境一致性、polyrepo 安全、可审计 |
| **铁律** | 禁止裸 `git add .`（依赖 PATH）；必须用 `git -C <path>`（隔离 Git + 显式目录） |
| **灵活性保留** | 系统全局 Git 和 IDE Git 保留作为备选，但任何 fallback 必须显式声明 |
| **与 polyrepo 的关系** | 隔离 Git + `-C` + 独立配置，三重机制确保主仓库与嵌套仓库天然隔离 |

### 2026-07-08 — baseline-structure.md §2.3 修订（基于隔离 Git 前提）

| 变更项 | 之前 | 之后 |
|--------|------|------|
| 前提假设 | 基于非隔离 Git 模式描述（"根级 `.gitattributes` 对嵌套仓库完全无效"） | 明确基于**隔离 Git 优先**前提（"隔离 Git 模式下操作天然隔离，但配置仍需独立维护"） |
| 问题根因 | 强调 `.gitattributes` 作用域限制 | 强调**配置缺失**风险（无 `.gitattributes` 时退回到隔离 Git 全局配置或默认值） |
| 与 workflow 关系 | 仅提及 Git 行为层 | 明确三层：Workflow 执行层 / Git 行为层（隔离 Git + `-C`）/ 环境变量层（隔离 `.gitconfig`） |

### 2026-07-08 — baseline-formats.md §3.7.4 修订（更新不跟踪理由）

| 变更项 | 之前 | 之后 |
|--------|------|------|
| 不跟踪原因 | "远程团队可能使用不同的编辑器/操作系统" | 更新为隔离 Git 语境：配置与业务代码解耦、不同 polyrepo 技术栈差异、隔离 Git `.gitconfig` 兜底 |
| 新增内容 | 无 | 明确 `.gitattributes`（仓库级）与隔离 Git `.gitconfig`（工具级）的优先级关系：`.gitattributes` > `.gitconfig` > Git 默认值 |

### 2026-07-08 — 命令行纯粹原则与路径入参铁律（baseline-principles.md §0.7.3 新增）

> **用户明确确认**：命令行必须是"最纯粹的调用形态"，只含解释器+脚本路径+常规入参；`--devroot` / `--target` 强制必填，不传示警退出。

| 变更项 | 内容 |
|--------|------|
| **新增章节** | 0.7.3 命令行纯粹原则与路径入参铁律 |
| **核心原则** | 命令行不携带任何逻辑：禁止 `cd`、禁止环境变量设置、禁止字符串拼接/JSON 构造、禁止路径检测/条件判断 |
| **正确形态** | `解释器 + 脚本路径 + 入参`（如 `python.exe script.py --devroot "xxx"`） |
| **入参铁律** | `--devroot` 始终必填；polyrepo 场景 `--target` 必填；不传直接报错退出 |
| **脚本内部义务** | `Path.cwd()` 推导工具链根（CWD 入参确定后保持不变）；工具链根与操作目标根相互独立（可为同一路径） |
| **纠偏** | 否定了 `Path(__file__)` 回溯推导工具链根的做法（回溯层数不确定）；否定了"工具链根与操作目标根必须不同"的矫枉过正 |

### 2026-07-08 — 导航索引同步更新（baseline-index.md）

| 变更项 | 之前 | 之后 |
|--------|------|------|
| 顶层原则速查 | 9 条 | 10 条（新增第 6 条"命令行纯粹原则"、第 7 条"`--devroot` 强制必填"） |


## 验证结果

| 检查项 | 结果 |
|--------|------|
| baseline-formats.md lint（md_lint + lint_encoding + link_checker） | ✅ 全部通过，0 违规 |
| baseline-structure.md lint（md_lint + lint_encoding + link_checker） | ✅ 全部通过，0 违规 |
| baseline-principles.md lint（md_lint + lint_encoding + link_checker） | ✅ 全部通过，0 违规 |
| baseline-index.md lint（md_lint + lint_encoding + link_checker） | ✅ 全部通过，0 违规 |
| workflow-git-security-demo.py lint（lint_python + lint_encoding） | ✅ 全部通过，0 违规 |
| 新增章节编号连续性 | ✅ 3.6 → 3.7，2.2 → 2.3，0.7.1 → 0.7.2 → 0.7.3，无跳号/重号 |
| 交叉引用有效性 | ✅ `baseline-principles.md` §0.7.1/§0.7.2/§0.7.3 引用可达，`baseline-index.md` 链接有效 |


## 关联文件

| 文件 | 变更状态 |
|------|---------|
| `references/tasks/deploy-git-isolated/baseline/baseline-principles.md` | ✅ 新增 §0.7.2（+45 行）、§0.7.3（+35 行） |
| `references/tasks/deploy-git-isolated/baseline/baseline-formats.md` | ✅ 新增 §3.7（+78 行），修订 §3.7.4 |
| `references/tasks/deploy-git-isolated/baseline/baseline-structure.md` | ✅ 新增 §2.3（+35 行），修订前提描述 |
| `references/tasks/deploy-git-isolated/baseline/baseline-index.md` | ✅ 修改（导航描述 + 原则速查表 8→10 条） |
| `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-security-demo.py` | ✅ 新建（验证脚本，单仓库+polyrepo 双场景扫描） |


*变更日期: 2026-07-08*  
*记录人: Agent*  
*下次触发条件: 新增文件类型需要调整 CRLF 豁免列表、新增嵌套 polyrepo 需要独立 .gitattributes、隔离 Git 配置路径变更、命令行纯粹原则新增禁止行为*