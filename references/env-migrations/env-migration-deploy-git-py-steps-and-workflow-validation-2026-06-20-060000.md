---
title: deploy-git-isolated Python 步骤脚本化与全链路 workflow 验证
description: 将 PS1 版 Step 5-9 改造为 Python 版 step 脚本，workflow-deploy-full.py 编排 4-9 全链路，proxy 环境验证通过。
date: 2026-06-20
meta:
  version: "1.0.0"
---

# env-migration-deploy-git-py-steps-and-workflow-validation-2026-06-20-060000

> **Session 主题**：deploy-git-isolated Python 步骤脚本化（Step 5-9）+ workflow 全链路编排验证
> **触发原因**：PS1 版步骤脚本已就绪，需建设对称的 Python 版 step 脚本及 workflow 编排器
> **影响范围**：`references/tasks/deploy-git-isolated/scripts/py-steps/`、`py-tools/workflow-deploy-full.py`
> **风险等级**：低（新增文件，不破坏既有 PS1 流程）


## 一、文本文件变更清单

### 1. 新建 `scripts/py-steps/step-05-github-commit.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-05-github-commit.py` |
| **变更类型** | 新建 |
| **作用** | Step 5: git commit，与 PS1 `github-step-05-commit.ps1` 逻辑对齐 |
| **关键行为** | 直接 `git commit -m <msg>`，不检查 staged，不配置 identity |
| **迁移方式** | 直接复制 |

### 2. 新建 `scripts/py-steps/step-06-github-remote.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-06-github-remote.py` |
| **变更类型** | 新建 |
| **作用** | Step 6: remote 配置，读取 .env `GITHUB_REPO_URL`，存在则 SKIP |
| **对齐** | 与 PS1 `github-step-06-remote.ps1` 严格对齐（Read-EnvConfig 校验、SKIP 逻辑） |
| **迁移方式** | 直接复制 |

### 3. 新建 `scripts/py-steps/step-07-github-push.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-07-github-push.py` |
| **变更类型** | 新建 |
| **作用** | Step 7: push，构造 `https://<Username>:<Pat>@github.com/<repoPath>` 直接 push |
| **关键行为** | 不修改 remote origin，与 PS1 对齐 |
| **迁移方式** | 直接复制 |

### 4. 新建 `scripts/py-steps/step-08-github-upstream.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-08-github-upstream.py` |
| **变更类型** | 新建 |
| **作用** | Step 8: `git push -u origin <branch>` |
| **迁移方式** | 直接复制 |

### 5. 新建 `scripts/py-steps/step-09-github-sync-issue.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-09-github-sync-issue.py` |
| **变更类型** | 新建 |
| **作用** | Step 9: Issue 同步，追加 commit 记录到 GitHub Issue |
| **实现方式** | 优先走 `py_lib.load_plugins(tags=["github"])` → `github_api.new_issue_comment()`；fallback 到 urllib |
| **迁移方式** | 直接复制 |

### 6. 更新 `scripts/py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | 修改（v1.1.2） |
| **变更内容** | 支持 Step 4-9 编排；新增 `--step 9` 和 `--issue N` 参数 |
| **作用** | Python 版全链条部署 workflow，调用 py-steps 脚本，失败即停 |
| **验证** | 纯 py 版全链路验证通过（11.89s） |


## 二、非文本操作

本次 session 不涉及文件系统/缓存迁移操作。


## 三、环境变量速查

无需新增环境变量。依赖既有 `.env`：
- `GITHUB_REPO_URL`
- `GITHUB_PAT`
- `GITHUB_USERNAME`
- `GIT_USER_NAME`
- `GIT_USER_EMAIL`


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文件） | `check-file-encoding.ps1` | BOM、CRLF、LF | BOM=no, CRLF=0, LF>0 |
| `.py`（6 个新建/1 个修改） | `python -m py_compile` | 语法无错误 | 全部通过 |


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | 执行 workflow 全链路 | `python workflow-deploy-full.py --message "test"` | Step 4-9 全部 [OK] |
| 2 | 验证 Issue 评论追加 | `python fetch_issue.py --issue-number 1` | 最新评论为本次 commit |
| 3 | 检查 .gitignore 白名单合规 | `git diff --cached --name-only` | 无 `references/` 外文件 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建 step 脚本 | `Remove-Item scripts/py-steps/step-05*.py ... step-09*.py` |
| 恢复 workflow | `git checkout -- scripts/py-tools/workflow-deploy-full.py` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-20-060000 |
| **更新人** | Agent Session |
| **变更触发** | 用户要求"做 step 5 以后的 python 改造并逐步验证执行" |
| **下次修订条件** | 新增 Step 10+ 或 workflow 参数扩展 |
| **跨环境迁移参考** | 直接复制 py-steps/ + workflow-deploy-full.py，按「验证清单」执行 |


*文档生成时间：2026-06-20*  
*模板版本：v2*
