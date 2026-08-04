---
title: PR 自闭环 Atomic 脚本组与 Issue Sync 工具链建设
description: 本次 session 完成了 polyrepo worktree 场景下的 PR 创建/合并/主仓库同步 atomic 脚本组建设，以及 Issue Sync 前置工具的补齐。
date: 2026-08-03
meta:
  version: "1.0.0"
---

# env-migration-pr-closed-loop-atomic-toolchain-2026-08-03-145515

> **Session 主题**：PR 自闭环 Atomic 脚本组与 Issue Sync 工具链建设  
> **日期**：2026-08-03（文件名时间戳：2026-08-03-145515）  
> **触发原因**：jywl-settlement worktree 部署 workflow-poly 时 Step 9 issue sync 404 失败，且现有 gh-pr-create.py / gh-pr-merge.py 不支持 --target polyrepo 契约  
> **影响范围**：deploy-git-isolated/scripts/py-tools/ 新增 4 个脚本 + 2 个修复 + 索引修订联动  
> **风险等级**：低（新增脚本，不破坏既有功能）


## 一、文本文件变更清单

### 1. 新建 `atomic-gh-issue-create.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-issue-create.py` |
| **变更类型** | 新建 |
| **作用** | 通过 GH CLI 创建 GitHub Issue，填补 workflow-poly Step 9 前缺少 issue 的缺口 |
| **关键参数** | `--repo`（owner/repo）、`--title`、`--body`、`--label`（可多次传入）、`--dry-run`、`--show-progress`、`--output` |
| **验证方式** | `python atomic-gh-issue-create.py --devroot ... --repo matt-cch/jywl-settlement --title "xxx" --dry-run` |
| **迁移方式** | 直接复制文件到目标环境，无需额外配置 |

### 2. 新建 `atomic-gh-pr-create.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-pr-create.py` |
| **变更类型** | 新建 |
| **作用** | polyrepo worktree 场景中创建 GitHub Pull Request，支持 `--target` 指向 worktree 目录 |
| **关键参数** | `--target`（worktree 路径）、`--title`、`--body`、`--base`（默认 main）、`--draft`、`--dry-run`、`--show-progress`、`--output` |
| **预检项** | 当前分支 ≠ base、远程分支已存在（已 push） |
| **验证方式** | `python atomic-gh-pr-create.py --devroot ... --target ... --title "xxx" --dry-run` |
| **迁移方式** | 直接复制文件到目标环境 |

### 3. 新建 `atomic-gh-pr-merge.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-pr-merge.py` |
| **变更类型** | 新建 |
| **作用** | polyrepo worktree 场景中 squash merge PR，支持 `--target` 指向 worktree 目录 |
| **关键参数** | `--target`、`--strategy`（squash/merge/rebase，默认 squash）、`--admin`（绕过分支保护）、`--delete-branch`（默认 False，保留分支）、`--dry-run`、`--show-progress`、`--output` |
| **验证方式** | `python atomic-gh-pr-merge.py --devroot ... --target ... --dry-run` |
| **迁移方式** | 直接复制文件到目标环境 |

### 4. 新建 `atomic-git-sync-main.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-sync-main.py` |
| **变更类型** | 新建 |
| **作用** | PR merge 后在主仓库中 checkout main + pull origin main，同步最新代码 |
| **关键参数** | `--repo`（主仓库路径，非 worktree）、`--remote`（默认 origin）、`--branch`（默认 main）、`--dry-run`、`--show-progress`、`--output` |
| **验证方式** | `python atomic-git-sync-main.py --devroot ... --repo ... --dry-run` |
| **迁移方式** | 直接复制文件到目标环境 |

### 5. 新建 `workflow-git-pr-poly.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-pr-poly.py` |
| **变更类型** | 新建 |
| **作用** | 编排 atomic-gh-pr-create → atomic-gh-pr-merge → atomic-git-sync-main 三步自闭环 |
| **关键参数** | `--devroot`、`--target`（worktree）、`--repo`（主仓库）、`--base`（默认 main）、`--strategy`、`--admin`、`--delete-branch`、`--auto`（AI 生成 title/body）、`--title`、`--body` |
| **验证方式** | `python workflow-git-pr-poly.py --devroot ... --target ... --repo ... --dry-run` |
| **迁移方式** | 直接复制文件到目标环境 |

### 6. 修改 `polyrepo_context.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/polyrepo_context.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 导入 `canonicalize_url()` 共享函数，替换 URL 字符串直接比较 |
| **插入位置** | 文件顶部 import 区 + `_resolve_repo_url()` 方法内 |
| **作用** | 修复 git-security.json URL 带 `.git` 后缀与 git remote URL 不带后缀导致的 mismatch |
| **验证方式** | `python -c "from py_plugins.polyrepo_context import PolyrepoContext; ..."` |
| **迁移方式** | 直接覆盖文件 |

### 7. 修改 `atomic-deploy-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 删除内嵌 `_canonicalize_url()` 函数，改为 `from git_url_utils import canonicalize_url` |
| **作用** | 与 polyrepo_context.py 共用同一套 URL 规范化逻辑，消除重复代码 |
| **验证方式** | `run-lint.py --files atomic-deploy-preflight.py` 通过 |
| **迁移方式** | 直接覆盖文件 |

### 8. 新建 `git_url_utils.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_url_utils.py` |
| **变更类型** | 新建 |
| **作用** | 提供 `canonicalize_url()` 共享函数（去掉 `.git` 后缀、尾部斜杠、统一小写） |
| **验证方式** | `python -c "from git_url_utils import canonicalize_url; print(canonicalize_url('https://github.com/a/b.git'))"` |
| **迁移方式** | 直接复制文件到目标环境 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session **不涉及**文件复制、缓存迁移、目录创建等非文本操作。全部为代码文件新建/修改。


## 三、环境变量速查

本次 session **不涉及** `.vscode/settings.json` 或 `.env` 的新增环境变量。现有变量已满足：

- `GITHUB_PAT`（devroot/.env）
- `GITHUB_USERNAME`（devroot/.env）


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py`（新建/修改） | `run-lint.py` | lint_python + lint_encoding | 语法通过、无 BOM、无 CRLF |
| `.md`（env-migration 正文） | `run-lint.py` | md_lint + lint_encoding | frontmatter 合规、无 CRLF |

**执行命令**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "atomic-gh-issue-create.py" "atomic-gh-pr-create.py" "atomic-gh-pr-merge.py" "atomic-git-sync-main.py" "workflow-git-pr-poly.py" "polyrepo_context.py" "atomic-deploy-preflight.py" "git_url_utils.py"
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | Issue 创建预演 | `python atomic-gh-issue-create.py --devroot ... --repo owner/repo --title "test" --dry-run` | 输出构造的命令，exit 0 |
| 2 | PR 创建预演 | `python atomic-gh-pr-create.py --devroot ... --target ... --title "test" --dry-run` | 输出构造的命令，exit 0 |
| 3 | PR 合并预演 | `python atomic-gh-pr-merge.py --devroot ... --target ... --dry-run` | 输出构造的命令，exit 0 |
| 4 | 主仓库同步预演 | `python atomic-git-sync-main.py --devroot ... --repo ... --dry-run` | 输出构造的命令，exit 0 |
| 5 | workflow 预演 | `python workflow-git-pr-poly.py --devroot ... --target ... --repo ... --dry-run` | 三步均预演，exit 0 |
| 6 | jywl-settlement 端到端 | 实际创建 PR → merge → 同步 main | PR 创建成功、merge 成功、main 最新 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建脚本 | `Remove-Item atomic-gh-issue-create.py, atomic-gh-pr-create.py, atomic-gh-pr-merge.py, atomic-git-sync-main.py, workflow-git-pr-poly.py, git_url_utils.py` |
| 恢复 polyrepo_context.py | 从 git 历史恢复修改前的版本 |
| 恢复 atomic-deploy-preflight.py | 从 git 历史恢复修改前的版本 |
| 清理索引登记 | 从 verified-task-index.json / TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md 中移除对应条目 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-03-145515 |
| **更新人** | OpenCode Agent Session |
| **变更触发** | jywl-settlement worktree 部署时 issue sync 404 + 现有 PR 脚本不支持 polyrepo --target |
| **下次修订条件** | 新增 PR 相关 atomic 脚本、workflow 参数变更、gh CLI 版本升级导致行为变化 |
| **跨环境迁移参考** | 直接复制 py-tools/ 下新建脚本 + py-plugins/ 下 git_url_utils.py + 修订联动索引 |


*文档生成时间：2026-08-03*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
