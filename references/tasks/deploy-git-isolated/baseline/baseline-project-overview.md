---
title: 项目整体架构理解 — cs_py 工程基座
description: 对 devroot 整体架构、治理体系、应用层现状的系统性理解，供 Agent 快速建立上下文。
date: 2026-07-06
meta:
  version: "1.0.0"
---

# 项目整体架构理解

> **性质**：全局上下文基线。记录对 devroot 整体架构的系统性理解，供新 Agent 快速建立上下文，避免 session 间重复摸索。
> **范围**：devroot 级别（不深入 task 或应用内部）。

## 一、项目本质

这是一个**工程化程度极高的个人/小团队开发基座**，不是单纯的"一个应用"。它的核心目标不是交付某个业务功能，而是**建立一套可复现、可审计、跨 session 可持续的 Agent-Human 协作开发环境**。

项目自我定位为 **"monorepo + polyrepo 混合工作流"**：
- 内部用 monorepo（`apps/api-demo`、`apps/web-demo` 等在同一仓库）
- 外部用 polyrepo（通过 `.code-workspace` 挂载其他仓库如 `jywl-lab`）

## 二、架构骨架：三根 + 隔离工具链

| 根 | 路径 | 职责 |
|---|------|------|
| **devroot** | `D:\pjt\cursor\cs_py` | 开发根，workspaceFolder，所有源码/配置/构建产物的锚点 |
| **vaultroot** | `D:\bak\vault` | Obsidian 知识库，文档资产独立挂载 |
| **toolchainroot** | `D:\download` | 外部二进制（Chrome 等），与 devroot 物理隔离 |

**隔离工具链**是项目的核心基础设施，全部收束在 `${devroot}/venv/` 下：

```
venv/
├── py/           → Python 3.13.14（embed 版，不污染系统）
├── node/         → Node.js 26.4.0 + npm 11.17.0
├── opencode/     → OpenCode CLI 1.17.13
├── gh/           → GitHub CLI 2.96.0（配置隔离在 data-gh）
├── git/          → MinGit 2.55.0（cmd 级隔离）
├── zig/          → Zig 编译器
├── data-*/       → 各工具运行时数据目录（状态隔离）
└── tmp/          → 临时工作区
```

**铁律**：所有工具调用必须用绝对路径，禁止依赖 PATH/CWD；禁止任何 `activate`、`shell` 类环境切换命令。

## 三、治理体系：四层规则嵌套

项目不是"有规范"，而是"规范本身是可执行的代码"：

| 层级 | 载体 | 作用 |
|------|------|------|
| **P0 禁令层** | `.cursor/rules/strictly-forbid-command-str-content.mdc` | 绝对禁止 Shell 内嵌字符串内容，任何 `python -c`、`powershell -Command` 一律封杀 |
| **P1 高频任务层** | `high-frequency-*.mdc`（7+ 个） | 将用户高频口头指令固化为"触发词 → 执行路径"映射，Agent 不得重新推理 |
| **P2 框架约束层** | `AGENTS.md` + `.cursor/rules/*.mdc` | 编码规范、文件写入前强制检查、lint 交付验证、Human-in-the-Loop 等 |
| **P3 真源层** | `verified-runtime-index.json` + `verified-task-index.json` + `verified-trigger-index.json` | 机器可读的索引真源，Agent 执行时的速查依据 |

**关键设计**：框架层（mdc）只指向"去哪查"，不复制"有什么"；动态数据由 JSON 索引承载，高频更新不触及框架层。

## 四、质量体系：lint 插件 + 交付验证

项目内置了一套完整的 **task 本地 lint 插件体系**：

| 插件 | 检测内容 | 覆盖文件类型 |
|------|---------|-------------|
| `lint_json` | JSON 语法 | `.json`、`.jsonc`、`.code-workspace` |
| `md_lint` | frontmatter 8 项 + `---` 污染 | `.md`、`.mdc` |
| `lint_encoding` | BOM/双BOM/CRLF/LF/UTF-8 | 所有文本文件 |
| `lint_python` | `py_compile` 语法 | `.py` |
| `lint_ps1` | `PSParser::Tokenize` 语法 | `.ps1` |

**交付铁律**：写完任何脚本/配置 → 先跑 lint → 不通过不交付。

## 五、文档与交接体系

项目有严格的文档分类规则：

| 类型 | 存放位置 | 用途 | 示例 |
|------|---------|------|------|
| **env-migration** | `references/env-migrations/` | 阶段性任务、工具链配置、数据处理 | Workspace 改造、lint 增强 |
| **handoff** | `docs/projects/<project>/handoffs/` | 项目级业务功能交付，跨 session 增量交接 | `apps/api-demo/` 等 |
| **DESIGN.md** | `docs/projects/<project>/` | 项目级设计基准，接口约定、技术选型 | — |
| **gotcha** | `docs/tooling/gotchas/` | 踩坑记录，反面教材 | PowerShell 长字符串陷阱、双 BOM 陷阱等 |

**所有 `.md` 必须**：
- Obsidian 兼容
- YAML frontmatter（title/description/date/meta 必填）
- LF 换行符（禁止 CRLF）
- UTF-8 无 BOM（`.ps1` 除外，必须 UTF-8 with BOM）

## 六、应用层现状

| 模块 | 位置 | 状态 |
|------|------|------|
| **api-demo** | `apps/api-demo/` | Python 后端（FastAPI + Poetry），`pyproject.toml` 存在 |
| **web-demo** | `apps/web-demo/` | 前端，子目录 html/static/src，无 package.json |
| **jywl-lab** | `apps/repos/jywl-team/jywl-lab/` | 外部 polyrepo，独立 `.git`，已 clone 并注册到 `.code-workspace` |

**历史遗留**：原 `backend/`、`frontend/` 已迁移至 `apps/` 下，旧目录不再维护。

## 七、Workspace 结构

当前 `.code-workspace` 共 **4 个 folder root**：

1. `cs_py (devroot)` → `.`
2. `api-demo` → `apps/api-demo`
3. `web-demo` → `apps/web-demo`
4. `jywl-lab` → `apps/repos/jywl-team/jywl-lab`

**关键配置**：
- `terminal.integrated.env.windows` 在 Workspace 级别注入隔离工具链 PATH
- `python.analysis.extraPaths` / `cursorpyright.analysis.extraPaths` 指向 `d:\yidongyunpan`
- `terminal.integrated.profiles.windows` 自定义 PowerShell prompt，自动 cd 到 devroot

## 八、真源检测现状

真源检测入口：`references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py`

索引：`references/runtime/verified-runtime-index.json`

| 工具 | 版本 | 状态 |
|------|------|------|
| Python | 3.13.14 | ✅ 最新 |
| Node.js | 26.4.0 | ✅ 最新 |
| OpenCode CLI | 1.17.13 | ✅ 最新 |
| Cursor | 3.10.11 | ⚪ 无法自动查上游 |
| Chromium | 152.0.7933.0 | ⚠️ 上游有 152.0.7934.0 |
| Git | 2.55.0.windows.2 | ✅ 最新 |
| GH CLI | 2.96.0 | ✅ 最新 |

GitHub 直连可用，API + Web 全 PASS。

## 九、一句话总结

> 这不是一个"项目"，而是一个**自举式的开发环境操作系统**——用代码定义规范，用规范约束行为，用行为沉淀经验，用经验反哺代码。Agent 在其中不是"写代码的工具"，而是"规则的执行者"和"上下文的接力者"。
