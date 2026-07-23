---
title: deploy-git-isolated — 目录结构与文件位置约定
description: Task 目录树规范、强制/可选文件清单、SOP/CHEATSHEET/TOOLS-INDEX 的固定位置约定。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 目录结构与文件位置约定

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
├── baseline/                   # 规范基线（本目录）
│   ├── baseline-index.md
│   ├── baseline-principles.md
│   ├── baseline-semantics.md
│   ├── baseline-structure.md   # 本文件
│   ├── baseline-formats.md
│   ├── baseline-operations.md
│   ├── baseline-plugin-architecture.md
│   ├── baseline-workflow-deploy.md
│   └── baseline-audit-truth.md
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
| `baseline/` | — | **规范基线**（本目录 9 个文件） | ✅ |

### 2.2 可选文件（Config 契约扩展）

| 文件 | 层级 | 职责 | 何时需要 |
|------|------|------|---------|
| `task-scenario-triggers.json` | Config 契约 | 触发条件真源（带 `$schema` 自描述） | task 有触发词映射需求时 |
| `archive-groups.json` | Config 契约 | 归档分组策略、黑白名单、输出格式 | 有 archive workflow 时 |
| `docs/PLUGIN-ARCHITECTURE.md` | — | 架构设计说明 | 有复杂共享库架构时 |


## 2.3 Polyrepo 嵌套仓库的 Git 配置分层

> **来源**：用户与 Agent 在 2026-07-08 对话中共同确认。本节基于「隔离 Git 优先」原则（见 `baseline-principles.md` §0.7.2），记录 monorepo 内嵌独立 polyrepo 时的 Git 配置隔离原则。

### 2.3.1 前提：每个 workspace repo 是独立 Git 仓库

`.code-workspace` 中的每个 `folder`（无论 devroot 还是 polyrepo）都是**独立 Git 仓库**，各自拥有完整的 Git 配置四件套：

| 文件 | 职责 | 是否强制 |
|------|------|---------|
| `.git/` | 独立版本库 | ✅ 必须 |
| `.gitignore` | 独立忽略规则 | ✅ 必须 |
| `.gitattributes` | 独立行尾符/编码策略 | ✅ 必须 |
| `git-security.json` | **Repo 身份卡**：`repo_url` + 安全策略 + 分支保护规则 | ✅ 必须 |

**铁律**：
- 每个 polyrepo **不共享、不继承** devroot 的 git 配置
- `git-security.json` 不是"安全附件"，而是每个 repo 的**身份与策略真源**
- workflow 操作 polyrepo 时，所有与该 repo 相关的元数据（`repo_url`、`security_level`、`allow_direct_push_to` 等）**必须从 target 自身的 `git-security.json` 读取**，禁止从 devroot 的 `.env` 推断

### 2.3.2 `git-security.json` —— Repo 身份卡

`git-security.json` 是每个仓库的**自描述元数据文件**，其 `repo_url` 字段是 workflow 识别"这个仓库应该推送到哪里"的**首要依据**。

**示例对照**（三个仓库各自独立）：

| 仓库 | `git-security.json` 中的 `repo_url` |
|------|--------------------------------------|
| `cs_py` (devroot) | `https://github.com/matt-cch/cs_py.git` |
| `jywl-lab` (polyrepo) | `https://github.com/jywl-team/jywl-lab.git` |
| `jywl-settlement` (polyrepo) | `https://github.com/matt-cch/jywl-settlement.git` |

**关键设计意图**：
- `repo_url` 写在各自仓库里，而不是集中在 devroot 的 `.env` 中——避免 polyrepo 操作时"拿错地址、推到别人仓库"
- `.env` 只保留**全局认证信息**（`GITHUB_PAT`、`GITHUB_USERNAME`），不保留**仓库特定信息**（`repo_url` 已被淘汰出 `.env`）
- 安全扫描规则（`required_ignore_patterns`、`sensitive_tracked_patterns`）也因仓库而异——Lab 仓有 `web/node_modules/`，Settlement 仓有 `.venv/`

### 2.3.3 分层配置原则

| 层级 | 位置 | 作用域 | 配置内容 |
|------|------|--------|---------|
| **主仓库（monorepo）** | `cs_py/.gitattributes` | 主仓库 `.git/` 管辖的全部文件 | 主仓库内所有文本文件的 LF 强制 + Windows 脚本豁免 |
| **嵌套仓库（polyrepo）** | `jywl-lab/.gitattributes` | 独立仓库 `.git/` 管辖的全部文件 | 与主仓库**相互独立**的配置，可相同也可不同 |

**关键约束**：
1. **配置不继承**：嵌套仓库**不继承**主仓库的 `.gitattributes`、`.gitignore`、`git-security.json`，必须**独立建立**
2. **内容可差异**：不同仓库可根据自身技术栈调整豁免列表（如某仓库无 `.ps1` 则可不配置 `-text` 豁免）
3. **Agent 义务**：操作嵌套 polyrepo 时必须**分别检查**各仓库的四件套存在性，禁止假设根级配置对嵌套仓库有效

### 2.3.4 与 workflow 多端多 devroot 的关系

`baseline-principles.md` §0.7.1 已规定 workflow 工具链通过 `--devroot` 参数支持多端多 polyrepo。本节是同一原则在 **Git 层面** 的具体化：

| 层面 | 机制 | 控制什么 |
|------|------|---------|
| **Workflow 执行层** | `--devroot` / `--target` 参数 | Python/PS/JS 脚本操作哪个仓库 |
| **Git 行为层** | 隔离 Git + `-C <path>` + 各仓库独立的 `.gitattributes` | `git checkout` 时换行符如何转换 |
| **环境变量层** | 隔离 Git 的 `.gitconfig`（`venv/data-git/.gitconfig`） | Git 默认行为（被 `.gitattributes` 覆盖） |
| **Repo 身份层** | 各仓库独立的 `git-security.json` | `repo_url`、安全策略、分支保护规则 |

**铁律**：
- 隔离 Git 模式下，各仓库的操作天然隔离，但**配置仍需独立维护**
- 禁止在任何脚本中使用系统全局 Git 或 IDE 内置 Git 作为默认执行器
- 禁止假设"因为操作隔离了，所以配置也自动一致"
- **禁止从 devroot `.env` 读取 `GITHUB_REPO_URL` 作为 polyrepo 的推送目标**——这是已淘汰的 anti-pattern


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


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
