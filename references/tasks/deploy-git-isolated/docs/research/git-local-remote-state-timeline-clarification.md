---
title: Git 本地/Remote 生效机制时间线与 workflow 衔接关系
description: 逐命令拆解 git checkout/commit/push/pr merge/pull 的本地/Remote 生效边界，澄清 workflow-deploy 与 workflow-gh 的衔接前提与常见误判。
date: 2026-07-01
meta:
  version: 1.0.0
  category: research
---

# Git 本地/Remote 生效机制时间线与 workflow 衔接关系

## 核心结论

`workflow-deploy-full.py` 与 `workflow-gh-pr.py` 的衔接点只有一个：**remote 分支存在**。
remote 分支的产生节点是 `git push origin <branch>`，此前 remote 完全无感知。


## Phase 1：本地开发（只影响本地）

| 时间 | 命令 | 本地状态 | Remote 状态 | 说明 |
|------|------|---------|------------|------|
| T0 | `git checkout master` | 切到本地 master | 无变化 | 本地工作目录指向本地 master 分支的最新 commit |
| T1 | `git checkout -b feat/xxx` | **新建**本地分支 `feat/xxx`，指针与 master 相同 | **无此分支** | `-b` 只操作本地分支表，remote 根本不知道 |
| T2 | 编辑文件 | 工作区变动 | 无变化 | 只在磁盘上，git 尚未追踪 |
| T3 | `git add .` | 文件进入 staged/index | 无变化 | 本地仓库的暂存区 |
| T4 | `git commit -m "..."` | 本地 `feat/xxx` 前进一个新 commit | 无变化 | 提交只在本地 `.git` 数据库中 |

> **此时如果去 GitHub 网页看 branches，`feat/xxx` 不存在。** 因为从未 push。


## Phase 2：Deploy Workflow（本地 → Remote）

`workflow-deploy-full.py` 执行的 Step 5-7：

| 时间 | 命令 | 本地状态 | Remote 状态 | 说明 |
|------|------|---------|------------|------|
| T5 | `git commit ...` | 本地 `feat/xxx` 再前进 | 无变化 | 同 T4 |
| T6 | `git push origin feat/xxx` | 无变化（已是最新） | **新建** `origin/feat/xxx`，内容与本地一致 | `push` 是**本地 → Remote**的第一次同步。此后 remote 才有了这个分支 |
| T7 | `git push origin feat/xxx`（第二次） | 无变化 | 如果本地有新增 commit，remote 同步更新 | 只有本地分支领先 remote 时才有效 |

> **T6 是分水岭**：T6 之前 remote 无此分支；T6 之后 remote 有了，且 `git branch -r` 能看到 `origin/feat/xxx`。


## Phase 3：PR Workflow（Remote 已存在 → 操作 Remote）

`workflow-gh-pr.py` 的前提：**T6 已完成**，remote 分支存在。

| 时间 | 命令 | 本地状态 | Remote 状态 | 说明 |
|------|------|---------|------------|------|
| T8 | `gh pr create ...` | 无变化 | **新建 PR**，目标指向 `master`，源为 `origin/feat/xxx` | PR 是 GitHub **服务端对象**，不在本地 git 分支表中 |
| T9 | `gh pr merge ...` | 无变化 | PR 状态变 merged，`master` 前进（squash/merge/rebase） | 远端 `master` 已被改写，**但本地 `master` 仍停在原地** |
| T10 | `gh pr merge --delete-branch` | 无变化（remote 分支由 gh 删除） | remote `feat/xxx` 被删除 | gh 的 `--delete-branch` 默认只删 remote 分支，**本地分支仍残留** |

> **关键陷阱**：T9 之后，你以为代码进 master 了，但**本地 `master` 还是旧的**。因为 merge 发生在 remote（GitHub 服务端），本地 master 没自动更新。


## Phase 4：本地同步（必须手动/脚本补）

`workflow-gh-pr.py` 最后的 Step：

| 时间 | 命令 | 本地状态 | Remote 状态 | 说明 |
|------|------|---------|------------|------|
| T11 | `git checkout master` | 本地工作目录切到本地 master | 无变化 | 此时本地 master 是 T0 时的旧状态 |
| T12 | `git pull origin master` | 本地 master 强制同步 remote master 的最新状态 | 无变化 | `pull` = `fetch`（下载 remote 最新状态）+ `merge`（合并到本地当前分支） |

> **T12 之后**，本地 master 才真正包含 T9 merge 进来的代码。


## 常见误判场景

### 误判 1："merge 完了本地怎么没有？"

```powershell
gh pr merge --delete-branch  # T9
git log master --oneline     # 看不到新提交！
```

**原因**：没做 T11+T12，本地 master 还是 merge 前的老状态。

### 误判 2："checkout 一个分支怎么同事看不到？"

```powershell
git checkout -b feat/xxx  # T1
# 以为同事能看到了
```

**原因**：`-b` 只建本地分支，remote 不存在此分支，同事自然看不到。

### 误判 3："remote branch 删了本地还在？"

```powershell
gh pr merge --delete-branch  # remote 分支被 gh 删除
git branch                   # 本地 feat/xxx 还在！
```

**原因**：`gh pr merge --delete-branch` 默认只删 remote 分支，本地分支残留。workflow-gh-pr.py 的 `--delete-branch` 只影响 remote，本地仍需手动 `git branch -d` 清理。


## 一句话命令边界速查

| 命令 | 影响范围 | 类比 |
|------|---------|------|
| `git checkout -b xxx` | **仅本地** | 在自家书房新建一个文件夹 |
| `git commit` | **仅本地** | 在文件夹里写草稿，没发出去 |
| `git push origin xxx` | **本地 → Remote** | 把草稿复印一份寄到总部 |
| `gh pr create` | **仅 Remote** | 在总部系统里填了一张申请表 |
| `gh pr merge` | **仅 Remote** | 总部批准了，把文件归档到总部 master 档案柜 |
| `git checkout master` | **仅本地** | 你从 feat 房间走回 master 房间 |
| `git pull origin master` | **Remote → 本地** | 把总部 master 档案柜的最新内容复印一份带回你的房间 |


## workflow 衔接关系

```
workflow-deploy-full.py（T5-T6）
  └── git commit → git push origin feat/xxx
  └── 产出：remote 分支 origin/feat/xxx 存在

workflow-gh-pr.py（T8-T12）
  └── 前提：remote 分支 origin/feat/xxx 已存在
  └── gh pr create → gh pr merge → git checkout master → git pull
  └── 产出：本地 master 与 remote master 同步
```

**衔接点是 T6 完成**，即 `git push` 成功。此前 workflow-gh 不能启动；此后 workflow-deploy 通常不再需要对同一分支操作。
