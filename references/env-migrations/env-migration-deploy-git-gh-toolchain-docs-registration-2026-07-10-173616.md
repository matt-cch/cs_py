---
title: deploy-git-isolated gh 工具链文档补登记
description: 补登记 gh 工具链到 deploy-git-isolated 顶层 4 个文档（README/TASK-TOOLS-INDEX/EXEC-CHEATSHEET/scripts-README），为 workflow-gh-pr.py 补 docstring，并新建 team-docs 新建仓库 playbook。
date: 2026-07-10
meta: {}
---

# env-migration-deploy-git-gh-toolchain-docs-registration-2026-07-10-173616

> **文档性质**：环境迁移指南。记录单次 session 对 deploy-git-isolated task 文档体系的补登记变更。  
> **受众**：Human + Agent。在新环境或后续 session 中理解本次 gh 工具链文档补全的上下文与复现方式。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | deploy-git-isolated gh 工具链文档补登记与 team-docs playbook 新建 |
| **日期** | 2026-07-10（frontmatter；文件名时间戳 2026-07-10-173616） |
| **文件名时间戳** | `2026-07-10-173616` |
| **触发原因** | task/ 下 4 个顶层入口文件（README.md、TASK-TOOLS-INDEX.md、EXEC-CHEATSHEET.md、scripts/README.md）缺失 gh 工具链登记，导致 Agent 无法从顶层文档发现 gh 集成能力；workflow-gh-pr.py docstring 不够详细，未对齐 poly workflow 风格 |
| **影响范围** | deploy-git-isolated task 文档体系（4 个 .md 修改 + 1 个 .py docstring 修改 + 1 个 .md 新建） |
| **风险等级** | 低（仅文档补登与 docstring 增强，不涉及业务代码或环境配置变更） |

## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-gh-pr.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-gh-pr.py` |
| **变更类型** | 修改（docstring 重写） |
| **新增/修改内容** | 补全 docstring：版本演进意图（v1.1.1→v1.2.0）、执行顺序（preflight → title/body 生成 → create → merge → 本地同步）、认证隔离机制（GH_TOKEN+GH_CONFIG_DIR headless）、审计产物、多场景调用示例（含 gh repo create 建仓库边界示例） |
| **插入位置** | 替换模块顶部第 2-36 行原有 docstring |
| **作用** | 对齐 `workflow-git-deploy-full-poly.py` v1.2.0 docstring 风格，使 Agent 和用户能从 docstring 直接获取完整用法 |
| **验证方式** | `run-lint.py` lint_python 通过（Python 语法解析无误） |
| **迁移方式** | 可直接覆盖（docstring 纯注释，不影响运行时行为） |

### 2. 修改 `references/tasks/deploy-git-isolated/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | 修改（多处追加） |
| **新增/修改内容** | ① py-plugins 结构树补 `gh_preflight.py`；② py-tools 结构树补 `workflow-gh-pr.py` / `gh-pr-create.py` / `gh-pr-merge.py` / `gh-branch-protect.py` / `workflow-gh-preflight-demo.py`；③ 场景快速决策表新增场景 J（GitHub PR 自闭环）；④ 新增场景 J 详细执行链（含 headless 认证示例与 repo create 边界说明）；⑤ 文件导航表补 gh 脚本行；⑥ 当前状态表补 gh CLI 隔离部署与 PR 自闭环状态 |
| **作用** | 让 task 顶层自说明文档完整呈现 gh 工具链，消除"4 个入口文件看不到 gh"的问题 |
| **验证方式** | `run-lint.py` md_lint + link_checker + lint_encoding 通过 |
| **迁移方式** | 可直接追加 |

### 3. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改（新增节 + 追加行） |
| **新增/修改内容** | ① 新增 §1.10 "GitHub CLI / PR 自闭环"（含脚本职责表、headless 认证示例、认知澄清）；② 边界矩阵追加 4 行（PR 创建/合并、gh preflight、新建仓库）；③ 速查命令区追加 gh 调用示例 |
| **作用** | 工具索引回答"有什么工具、在哪里、什么时候用"时覆盖 gh 侧 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 可直接追加 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | 修改（新增 Stage） |
| **新增/修改内容** | 新增 Stage S7.2 "GitHub CLI / PR 自闭环（gh）"，含全自动 PR 闭环、仅 create、仅 merge、gh preflight demo、headless 认证（repo create）的命令速查 |
| **作用** | 执行速查回答"命令怎么执行"时覆盖 gh 侧 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 可直接追加 |

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/README.md` |
| **变更类型** | 修改（导航表追加） |
| **新增/修改内容** | 各层导航表追加 `workflow-gh-pr.py` / `gh-pr-create.py` / `gh-pr-merge.py` / `gh-branch-protect.py` / `workflow-gh-preflight-demo.py` / `gh_preflight.py` 条目 |
| **作用** | scripts 目录索引完整呈现 gh 资产 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 可直接追加 |

### 6. 新建 `references/tasks/deploy-git-isolated/docs/playbooks/create-github-repo-team-docs-playbook.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/playbooks/create-github-repo-team-docs-playbook.md` |
| **变更类型** | 新建 |
| **新增/修改内容** | 完整 playbook：背景（task 不封装 repo create、cs_py .env 不能复用）、意图（全程本机、先私后转、对齐 jywl-lab）、关键认知（账号 public≠仓库 public、remote 对应问题）、Step 0-4 详细命令（含绝对路径）、执行前核查项、前置条件清单 |
| **作用** | 把本次 session 中"新建 GitHub 仓库 team-docs"的实施方案固化为可复用操作手册 |
| **验证方式** | `run-lint.py` md_lint + link_checker + lint_encoding 通过 |
| **迁移方式** | 新建文件，无回滚冲突 |

## 二、非文本操作（文件系统/缓存迁移）

本次 session **无非文本操作**。全部为文本文件编辑（.md 修改 / .py docstring 修改 / .md 新建），无目录创建、缓存迁移、文件复制等操作。

## 三、环境变量速查

本次 session **未新增环境变量**。复用已有变量：

| 变量 | 来源 | 用途 |
|------|------|------|
| `GITHUB_PAT` | `.env` | gh headless 认证（`$env:GH_TOKEN = $env:GITHUB_PAT`） |
| `GH_CONFIG_DIR` | 执行时注入 | gh CLI 配置隔离（`venv/data-gh`） |
| `GIT_USER_NAME` / `GIT_USER_EMAIL` | `.env` | 隔离 git init 身份配置 |

## 四、落盘验证（写入后已执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（5 个修改 + 1 个新建） | `run-lint.py`（md_lint + lint_encoding + link_checker） | frontmatter 合规性、编码/BOM/换行符、内部链接有效性 | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, link_checker 通过 |
| `.py`（1 个 docstring 修改） | `run-lint.py`（lint_python + lint_encoding） | Python 语法解析、编码/BOM/换行符 | py_compile 通过, BOM=no, CRLF=0 |

**执行记录**：
```powershell
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "D:\pjt\cursor\cs_py" --files "<6 个文件路径>"
# 结果：总扫描文件 14 个，总违规项 0 处，结论 ✅ 全部通过
```

> 注：模板要求使用 `check-file-encoding.ps1`，但项目当前标准 lint 入口已统一为 `run-lint.py`（自动路由 md_lint / lint_encoding / lint_python / link_checker / lint_json 等），故按实际标准执行。

## 五、验证清单（新环境复现后建议执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 gh CLI 隔离部署 | `Test-Path "D:\pjt\cursor\cs_py\venv\gh\bin\gh.exe"` | `True` |
| 2 | 确认 gh preflight 插件可用 | `py_lib.load_plugins(devroot="...", tags=["gh"])` 后访问 `registry.gh_preflight.check()` | 返回 GhContext，ok=True |
| 3 | 确认 4 个顶层文档已登记 gh | 搜索 `workflow-gh-pr.py` 在 README.md / TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md / scripts/README.md 中是否存在 | 4 个文件均命中 |
| 4 | 确认 playbook 已落盘 | `Test-Path "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\docs\playbooks\create-github-repo-team-docs-playbook.md"` | `True` |
| 5 | 确认 playbook 链接有效 | `run-lint.py --files "create-github-repo-team-docs-playbook.md"` | link_checker 通过 |

## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 删除新建 playbook | `Remove-Item "references\tasks\deploy-git-isolated\docs\playbooks\create-github-repo-team-docs-playbook.md"` |
| 回退 workflow-gh-pr.py docstring | 用 `edit` 工具将 docstring 恢复为原 v1.2.0 精简版（保留参数表 + 2 个调用示例） |
| 回退 4 个 .md 的 gh 补登内容 | 逐文件 `edit` 删除新增的 gh 相关行/段（结构树、场景表、场景 J 段、导航表、状态表、§1.10、边界矩阵行、Stage S7.2） |
| 回退导航表 | 从 `references/env-migrations/README.md` 中删除本 env-migration 对应行 |

> 回滚工作量评估：6 个文件，纯文本删除，约 10 处 edit。无环境副作用。

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-10-173616 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户询问"task/ 已集成的 git/gh 工具"，发现 4 个顶层入口文件缺失 gh 登记 |
| **下次修订条件** | ① gh 工具链纳入主部署 workflow（当前为可行性验证阶段）；② 新增 gh 子脚本（如 gh-pr-close.py）需同步登记到 4 个顶层文档 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |

*文档生成时间：2026-07-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
