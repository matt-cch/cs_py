---
title: Polyrepo Workspace 改造第一步 — cs-py.code-workspace 创建与验证
description: 本次 session 完成 devroot 的 .code-workspace 改造第一步，创建 Multi-root Workspace 文件，验证 devroot git 状态、GH CLI 认证、apps/ 隔离边界，为后续 jywl-lab clone 做准备。
date: 2026-07-06
meta:
  version: 1.0.0
  category: env-migration
---

# env-migration-polyrepo-workspace-setup-2026-07-06-125559

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Polyrepo Workspace 改造第一步 — cs-py.code-workspace 创建与验证 |
| **日期** | 2026-07-06 |
| **文件名时间戳** | `2026-07-06-125559` |
| **触发原因** | 用户需要在同一 Cursor IDE 中并行开发 devroot（monorepo）与外部 Polyrepo（jywl-team/jywl-lab），第一步先创建 .code-workspace |
| **影响范围** | devroot 根目录（新增 `.code-workspace` 文件）、验证状态确认 |
| **风险等级** | 低（仅新增 IDE 配置文件，不涉及 git 追踪变更） |


## 一、文本文件变更清单

### 1. 新建 `cs-py.code-workspace`

| 属性 | 值 |
|------|-----|
| **路径** | `cs-py.code-workspace`（devroot 根目录） |
| **变更类型** | `新建` |
| **新增内容** | Multi-root Workspace 定义，注册 devroot + api-demo + web-demo 三个 folder root |
| **作用** | 为 Cursor/VS Code 提供统一的多模块开发视图，后续可追加外部 repo |
| **验证方式** | JSON 语法验证通过；不影响 `git status` |
| **迁移方式** | 直接复制 |

内容：

```json
{
  "folders": [
    {
      "name": "cs_py (devroot)",
      "path": "."
    },
    {
      "name": "api-demo",
      "path": "apps/api-demo"
    },
    {
      "name": "web-demo",
      "path": "apps/web-demo"
    }
  ],
  "settings": {
    "files.autoSave": "afterDelay"
  }
}
```


## 二、非文本操作

无。本次 session 仅新建 `.code-workspace` 文件，无文件系统迁移或缓存操作。


## 三、环境变量速查

无变更。`.vscode/settings.json` 未修改。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.code-workspace` | Python json 模块 | JSON 语法 | 解析成功，无异常 |
| `.code-workspace` | git check-ignore | 是否被 .gitignore 排除 | `.gitignore:6:/*` 已排除，不影响 git 状态 |

验证命令及结果：

```powershell
# JSON 语法验证
python -c "import json; json.load(open('cs-py.code-workspace'))"
# ✅ JSON valid

# git 状态验证
git status --short
# 输出：仅显示 references/tasks/deploy-git-isolated/docs/research/...md（预期内的未追踪报告文件）
# ✅ .code-workspace 不在 git status 中
```


## 五、验证清单（本环境执行结果）

| # | 验证步骤 | 命令/操作 | 期望结果 | 实际结果 |
|---|---------|----------|---------|---------|
| 1 | 确认 .code-workspace 存在 | `Test-Path cs-py.code-workspace` | `True` | ✅ `True` |
| 2 | 确认 JSON 语法正确 | `python -c "import json; ..."` | 无异常 | ✅ 无异常 |
| 3 | 确认不影响 git 状态 | `git status --short` | 不显示 `.code-workspace` | ✅ 未显示 |
| 4 | 确认当前分支 | `git branch --show-current` | `task/deploy-git-isolated` | ✅ `task/deploy-git-isolated` |
| 5 | 确认工作区干净 | `git status` | 无未提交修改 | ✅ 无修改，仅 1 个未追踪文件（research 报告） |
| 6 | 确认 local/remote 对齐 | `git branch -vv` | 追踪 `origin/task/deploy-git-isolated` | ✅ 追踪正常 |
| 7 | 确认本地领先 remote | `git log --oneline HEAD...origin/task/deploy-git-isolated` | 5 commits ahead | ✅ ahead 5 commits（待 push） |
| 8 | 确认 apps/ 隔离边界 | `git check-ignore -v apps/api-demo` | `.gitignore:6:/*` 已排除 | ✅ 已排除 |
| 9 | 确认 api-demo 无独立 .git | `Test-Path apps/api-demo/.git` | `False` | ✅ `False` |
| 10 | 确认 web-demo 无独立 .git | `Test-Path apps/web-demo/.git` | `False` | ✅ `False` |
| 11 | 确认 GH CLI 可执行 | `Test-Path venv/gh/bin/gh.exe` | `True` | ✅ `True` |
| 12 | 确认 GH CLI 认证 | `workflow-gh-preflight-demo.py` | `matt-cch` 已登录 | ✅ `matt-cch` 已登录，Issue #1 可见 |
| 13 | 确认 apps/repos/ 预留 | `Get-ChildItem apps/repos` | `.emptydir` 存在 | ✅ 已预留 |


## 六、关键状态说明

### 6.1 devroot git 状态

- **当前分支**：`task/deploy-git-isolated`
- **Remote 追踪**：`origin/task/deploy-git-isolated` ✅
- **本地领先**：ahead 5 commits（commit `b0e826b` 为最新）
- **待 push**：建议后续执行 `git push` 同步 remote
- **未追踪文件**：`references/tasks/deploy-git-isolated/docs/research/multi-repo-dev-workflow-analysis-2026-07-06-104341.md`（本次 session 的研究报告，预期内）

### 6.2 GH CLI 认证状态

- **裸命令 `gh auth status`**：显示未登录（预期行为，因未注入 `GH_TOKEN`）
- **`gh_preflight` 验证**：✅ 通过，`matt-cch` 已认证，`GITHUB_PAT` 已读取
- **认证机制**：环境变量驱动（`GH_TOKEN` + `GH_CONFIG_DIR`），非持久化登录
- **Issue #1**：`[Task Tracking] deploy-git-isolated`，最后更新 2026-07-03，45 条评论

### 6.3 apps/ 隔离边界

- `apps/api-demo/` 和 `apps/web-demo/`：**无 `.git`**，属于 devroot monorepo 的子模块
- `apps/repos/`：**已预留**，`.emptydir` 占位，待后续 `jywl-lab` clone
- `.gitignore`：`/*` 排除根下所有，`apps/` 整体被排除，devroot git 不追踪其内容


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 .code-workspace | `Remove-Item cs-py.code-workspace` |
| 恢复无 Workspace 状态 | 直接打开 devroot 文件夹即可 |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-06-125559 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户需要改造 devroot 以支持 Polyrepo + Monorepo 混合并行开发 |
| **下次修订条件** | jywl-lab clone 完成后追加 folder root；或 .gitignore 渐进放开 apps/ 后调整 Workspace 结构 |
| **跨环境迁移参考** | 直接复制 `cs-py.code-workspace` + 按「验证清单」逐条执行 |
