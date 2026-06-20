---
title: deploy-git-isolated — 标准操作流程（SOP）
description: 本 task 的标准操作流程。每个 Step 定义 Input → Process → Output → Validation 契约，支持 Ralph Loop 自闭环追踪审计。
date: 2026-06-18
meta: {}
---

# deploy-git-isolated — 标准操作流程（SOP）

> **本文件职责**：定义本 task 的「标准操作流程」。每个 Step 均包含 **Input → Process → Output → Validation** 四元契约，确保执行一致性、输出可预期、过程可追踪。
>
> **与 EXEC-CHEATSHEET 的区别**：本文件回答「流程是什么、每一步的边界在哪、怎么验收」；EXEC-CHEATSHEET 回答「命令怎么执行」。二者互补，不重叠。


## 0. Ralph Loop 自闭环框架

> **来源**：用户明确确认（2026-06-18）。本节定义最小执行单元的自闭环结构，所有 Step 均受本节约束。

每个 Step 都是一个 **Ralph Loop 节点**：

```
┌─────────────────────────────────────────┐
│  Step N                                 │
│  ├─ Input（预期输入）                    │
│  ├─ Process（执行过程）                  │
│  ├─ Output（预期输出）                   │
│  ├─ Validation（验收条件）               │
│  ├─ Audit Trail（执行记录）              │
│  │   ├─ status: pending/running/completed/failed
│  │   ├─ log_path: 执行日志路径
│  │   └─ artifacts: 输出产物清单
│  └─ Rollback（回滚路径）                 │
└─────────────────────────────────────────┘
```

**自闭环原则**：
1. **输入可预期**：每个 Step 的 Input 必须明确定义，不满足 Input 条件不得执行
2. **输出可验证**：每个 Step 的 Output 必须有对应的 Validation 规则，通过后才可进入下一步
3. **过程可追踪**：每个 Step 执行后必须留下 Audit Trail（状态、日志、产物）
4. **失败可回滚**：每个 Step 必须定义 Rollback 路径，失败时可恢复到执行前状态


## 1. Stage 路线图

| Stage | 名称 | 包含 Step | 完成标准 | 状态 |
|-------|------|-----------|---------|------|
| S1 | 初始化 | Step 0 → Step 3 | `.git/` 创建、`.gitignore` 生效、README 存在 | 按场景执行 |
| S2 | 提交 | Step 4 → Step 5 | 文件 staged、commit 成功 | 按场景执行 |
| S3 | 连接 | Step 6 → Step 8 | remote 配置、push 成功、upstream 设置 | 按场景执行 |
| S4 | 安全检查 | Safety Check | 敏感文件被屏蔽、无泄漏风险 | 每次 push 前强制 |
| S5 | 日常操作 | Daily Ops | 任意 git 子命令透传执行 | 按需执行 |
| S6 | Issue 同步 | Issue Sync | commit 历史同步到 GitHub Issue | commit 后可选 |


## 2. Step 节点契约

### Step 0: 预检（Precheck）

| 契约项 | 定义 |
|--------|------|
| **Input** | `.env` 存在且可读；`venv/git/cmd/git.exe` 存在（如已部署）；网络可用 |
| **Process** | 检测残留配置、确认网络连通、读取 `.env` 必要变量 |
| **Output** | 预检报告（环境状态、可用变量、风险提示） |
| **Validation** | `GIT_USER_NAME` 和 `GIT_USER_EMAIL` 非空；如连接 GitHub 则需 `GITHUB_REPO_URL` 和 `GITHUB_PAT` |
| **Audit Trail** | 日志：`logs/step-00-precheck.log`；状态：ENTRY.json `steps[0].status` |
| **Rollback** | 无需回滚（只读操作） |


### Step 1: 初始化（Init）

| 契约项 | 定义 |
|--------|------|
| **Input** | 预检通过；目标目录无 `.git/` 残留 |
| **Process** | `git init` + `git config --global user.name/email`（来自 `.env`） |
| **Output** | `.git/` 目录；`venv/data-git/.gitconfig` 含身份配置 |
| **Validation** | `git config --global user.name` 返回预期值；`--show-origin` 指向隔离目录 |
| **Audit Trail** | 日志：`logs/step-01-init.log`；状态：ENTRY.json `steps[1].status`；产物：`.git/`, `.gitconfig` |
| **Rollback** | `Remove-Item -Recurse .git/`；删除 `venv/data-git/.gitconfig` |


### Step 2: .gitignore（Security）

| 契约项 | 定义 |
|--------|------|
| **Input** | Step 1 完成；`.gitignore` 不存在或允许覆盖 |
| **Process** | 生成白名单模式 `.gitignore`（屏蔽 `.env` / `venv/` / `*.pem` / 敏感文件） |
| **Output** | `.gitignore` 文件 |
| **Validation** | `git check-ignore -v .env` 返回匹配规则；`git check-ignore -v venv/` 返回匹配规则 |
| **Audit Trail** | 日志：`logs/step-02-gitignore.log`；状态：ENTRY.json `steps[2].status`；产物：`.gitignore` |
| **Rollback** | `git checkout -- .gitignore`（如已跟踪）或 `Remove-Item .gitignore` |


### Step 3: README（Documentation）

| 契约项 | 定义 |
|--------|------|
| **Input** | Step 2 完成；`README.md` 不存在或允许覆盖 |
| **Process** | 生成项目 README.md（含项目描述、快速开始、贡献指南占位） |
| **Output** | `README.md` 文件 |
| **Validation** | `Test-Path README.md`；文件内容非空 |
| **Audit Trail** | 日志：`logs/step-03-readme.log`；状态：ENTRY.json `steps[3].status`；产物：`README.md` |
| **Rollback** | `Remove-Item README.md`（如未跟踪）或 `git checkout -- README.md` |


### Step 4: 暂存（Stage）

| 契约项 | 定义 |
|--------|------|
| **Input** | Step 3 完成；有文件需要提交 |
| **Process** | `git add`（仅已跟踪文件 + 新文件安全确认），排除 `.env` 和敏感文件 |
| **Output** | Staged 文件清单 |
| **Validation** | `git diff --cached --name-only` 返回预期文件；`.env` 不在列表中 |
| **Audit Trail** | 日志：`logs/step-04-stage.log`；状态：ENTRY.json `steps[4].status`；产物：staged 文件列表 |
| **Rollback** | `git reset HEAD`（取消所有 staged） |


### Step 5: 提交（Commit）

| 契约项 | 定义 |
|--------|------|
| **Input** | Step 4 完成；有 staged 文件；commit 消息非空 |
| **Process** | `git commit -m "消息"`（规范化消息模板） |
| **Output** | Commit hash；提交记录 |
| **Validation** | `git log -1 --oneline` 返回预期消息；commit hash 存在 |
| **Audit Trail** | 日志：`logs/step-05-commit.log`；状态：ENTRY.json `steps[5].status`；产物：commit hash |
| **Rollback** | `git reset --soft HEAD~1`（撤销最近一次 commit，保留 staged） |


### Step 6: Remote（Connect）

| 契约项 | 定义 |
|--------|------|
| **Input** | Step 5 完成；`.env` 中 `GITHUB_REPO_URL` 已配置 |
| **Process** | `git remote add origin <GITHUB_REPO_URL>` |
| **Output** | Remote 配置 |
| **Validation** | `git remote -v` 返回 origin 配置；URL 与 `.env` 一致 |
| **Audit Trail** | 日志：`logs/step-06-remote.log`；状态：ENTRY.json `steps[6].status`；产物：remote 配置 |
| **Rollback** | `git remote remove origin` |


### Step 7: Push（Upload）

| 契约项 | 定义 |
|--------|------|
| **Input** | Step 6 完成；安全检查通过；`.env` 中 `GITHUB_PAT` 已配置 |
| **Process** | `git push -u origin main`（使用 PAT 认证） |
| **Output** | Push 成功消息；GitHub 提交记录 |
| **Validation** | GitHub 仓库可见提交记录；`git log --graph --oneline` 显示远程分支 |
| **Audit Trail** | 日志：`logs/step-07-push.log`；状态：ENTRY.json `steps[7].status`；产物：GitHub commit URL |
| **Rollback** | `git push --force-with-lease origin HEAD^:main`（谨慎使用）或 GitHub Web 删除提交 |


### Step 8: Upstream（Track）

| 契约项 | 定义 |
|--------|------|
| **Input** | Step 7 完成；远程分支存在 |
| **Process** | `git branch --set-upstream-to=origin/main main` |
| **Output** | Upstream 追踪配置 |
| **Validation** | `git branch -vv` 显示 `[origin/main]` 追踪关系 |
| **Audit Trail** | 日志：`logs/step-08-upstream.log`；状态：ENTRY.json `steps[8].status`；产物：upstream 配置 |
| **Rollback** | `git branch --unset-upstream main` |


## 3. 安全检查（Safety Check）—— 独立 Stage

| 契约项 | 定义 |
|--------|------|
| **Input** | 任意时刻，尤其是 push 前 |
| **Process** | 扫描已跟踪文件、staged 文件、未跟踪文件；验证敏感文件被 `.gitignore` 屏蔽 |
| **Output** | 安全检查报告（4 个 section） |
| **Validation** | `.env` 被屏蔽；`*.pem` / `venv/` 等被屏蔽；无敏感文件在 staged 中 |
| **Audit Trail** | 日志：`logs/safety-check.log`；状态：ENTRY.json `safety_checks[]`；产物：检查报告 |
| **Rollback** | 无需回滚（只读操作）；但如发现敏感文件 staged，必须执行 `git reset HEAD <file>` |

**输出格式**：
```
[1] 已跟踪文件（会随 push 上传）：
  - .gitignore
  - README.md
[2] 已 staged 文件（即将 commit）：
  - xxx
[3] 未跟踪文件：
  - yyy
[4] 敏感文件屏蔽验证：
  [OK] .env -> 被 .gitignore 屏蔽
  [FAIL] secrets.pem -> 未被屏蔽！
```


## 4. 日常操作（Daily Ops）—— 按需 Stage

| 契约项 | 定义 |
|--------|------|
| **Input** | 隔离 Git 已部署；任意 git 子命令 |
| **Process** | `git-isolated.ps1 <子命令>`（透传 + HOME 重定向） |
| **Output** | Git 命令输出 |
| **Validation** | 命令 exit code = 0；输出无乱码（UTF-8） |
| **Audit Trail** | 日志：`logs/git-ops.log`；状态：按需记录 |
| **Rollback** | 依具体子命令而定（如 `git reset` / `git checkout` 等） |


## 5. Issue 同步（Issue Sync）—— 可选 Stage

| 契约项 | 定义 |
|--------|------|
| **Input** | Commit 完成；`.env` 中 `GITHUB_PAT` 已配置；`github-sync-issue-config.json` 存在 |
| **Process** | `github-sync-issue.ps1 -Mode <create/update/comment/list-comments/get-issue>` |
| **Output** | Issue 状态 / 评论列表 / 新建 Issue URL |
| **Validation** | GitHub API 返回 HTTP 200；返回数据符合预期 schema |
| **Audit Trail** | 日志：`logs/issue-sync.log`；状态：ENTRY.json `issue_syncs[]`；产物：Issue URL / 评论 ID |
| **Rollback** | `github-sync-issue.ps1 -Mode delete-comment`（如支持）或 GitHub Web 手动删除 |


## 6. 关联文件

| 文件 | 职责 | 何时读 |
|------|------|--------|
| `README.md` | 任务总览、场景化决策入口 | 每次进入 task |
| `GOAL.md` | 目标闭环、Stage 路线图、成功标准 | 首次接触 / 跨 session 接续 |
| `task-canonical-baseline.md` | 规范基线、命名约定、修订联动规则 | 需要理解文件组织时 |
| `DESIGN.md` | 设计决策、踩坑记录 | 需要理解「为什么这样设计」时 |
| `ENTRY.json` | 机器真源（Step manifest、脚本状态、版本历史） | Agent 工具调用前 |
| `TASK-TOOLS-INDEX.md` | 工具索引（能力地图） | 规划「该调哪个工具」时 |
| `scripts/EXEC-CHEATSHEET.md` | 执行速查（命令+配置+参数） | 需要复制具体命令时 |


*SOP 版本: v1.0*  
*创建时间: 2026-06-18*  
*关联: GOAL.md v1.1, ENTRY.json v0.8.0, task-canonical-baseline.md v1.1*
