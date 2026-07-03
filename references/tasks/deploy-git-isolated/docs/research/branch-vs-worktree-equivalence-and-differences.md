---
title: Branch 与 Worktree 模式在 PR 闭环中的等价性与差异
description: 精炼确认 checkout branch（逻辑切换）与 worktree（物理隔离）两种模式在本地/Remote 生效机制上的等价原理，以及物理目录管理的差异。
date: 2026-07-01
meta:
  version: 1.0.0
  category: research
---

# Branch 与 Worktree 模式在 PR 闭环中的等价性与差异

## 核心结论

> **checkout branch 是「逻辑切换」，worktree 是「物理隔离」。**
> 两者最终都通过同一个 remote 完成 PR merge 闭环，只是本地的工作方式不同。


## 模式对比

```
checkout branch 模式:
  物理: cs_py/ (唯一目录)
  逻辑: master ↔ feat/xxx (checkout 切换)
  remote: origin/master, origin/feat/xxx
  push/pr: 在同一目录内完成
  清理: git branch -d feat/xxx

worktree 模式:
  物理: cs_py/ (master) + cs_py-feat-xxx/ (feat/xxx)
  逻辑: master (固定) + feat/xxx (固定)
  remote: origin/master, origin/feat/xxx (完全相同)
  push/pr: 在 cs_py-feat-xxx/ 目录内完成 (或 git -C <path> ...)
  清理: git worktree remove cs_py-feat-xxx/ + git branch -d feat/xxx (如需)
```


## 等价性

| 维度 | checkout branch | worktree | 结论 |
|------|----------------|----------|------|
| **remote 感知** | `origin/feat/xxx` | `origin/feat/xxx` | ✅ 相同 |
| **PR 闭环路径** | push → pr create → pr merge | push → pr create → pr merge | ✅ 相同 |
| **merge 结果** | master 前进 | master 前进 | ✅ 相同 |
| **本地同步方式** | `git checkout master && git pull` | `cd cs_py/ && git pull` | ✅ 等效 |


## 差异点

| 维度 | checkout branch | worktree |
|------|----------------|----------|
| **分支切换成本** | 需要 stash/pop（有未提交修改时） | 无需切换，cd 即可 |
| **并行开发能力** | 单线程 | 多线程（多个目录各自独立） |
| **workflow 执行目录** | 固定为 `cs_py/` | 必须指向 worktree 物理目录 |
| **物理目录清理** | 无 | 必须执行 `git worktree remove` |
| **Git 内部记录清理** | 无 | 建议执行 `git worktree prune` |


## 关键细节：worktree 的 workflow 执行路径

worktree 模式下，`workflow-deploy-full.py` 的 `--devroot` 必须指向 worktree 物理目录：

```powershell
# 错误：在 master 目录执行，看到的是 master 分支内容
python workflow-deploy-full.py --devroot D:\pjt\cursor\cs_py --auto

# 正确：在 worktree 目录执行，看到的是 feat/xxx 分支内容
python workflow-deploy-full.py --devroot D:\pjt\cursor\cs_py-feat-xxx --auto
```


## 清理差异

| 清理对象 | checkout branch | worktree |
|---------|----------------|----------|
| 本地逻辑分支 | `git branch -d feat/xxx` | 同左（`remove` 可能已自动删除） |
| Remote 分支 | gh `--delete-branch` 自动 | 同左 |
| **物理工作目录** | 无（一直用同一个） | **`git worktree remove <path>`** |
| **Git 内部 worktree 记录** | 无 | **`git worktree prune`** |
| 未提交修改的处理 | 必须先 stash/commit | `remove --force` 或手动处理 |


## worktree 机制澄清（三个常见误解）

### 1. 目标目录必须手工指定

`git worktree add` 不会自动起名或选址，路径参数必填：

```powershell
# 正确：你指定目录名和位置
git worktree add -b feat/xxx ../cs_py-feat-xxx

# 错误：缺少路径参数，git 报错
git worktree add -b feat/xxx
```

路径可以是同级目录、任意绝对路径，git 只负责在该路径下检出文件。

### 2. worktree 不"读取 .gitignore 后选择性拷贝"

worktree 的行为是"从 `.git` 数据库中检出已追踪文件"，而非"读取 .gitignore 后过滤拷贝"。

- 已追踪文件 → 在 `.git` 数据库中 → worktree 会检出
- 未追踪/被忽略文件 → 不在 `.git` 数据库中 → worktree **自然不存在**

因此 `__pycache__/`、`venv/` 等被忽略目录不会出现在 worktree 中，不是因为 git "读到了 .gitignore 规则后跳过"，而是因为它们**从未进入过 Git 数据库**。

### 3. 开发工具链不是 git 的责任

git worktree 只提供**文件系统层面的分支隔离**，开发工具链（venv、IDE、环境变量）需要 human 自行解决。

#### 陷阱 A：settings.json 的 `${workspaceFolder}` 漂移

VS Code 的 `settings.json` 中配置了：
```json
"PATH": "...;${workspaceFolder}\\venv\\gh\\bin;${env:Path}"
```

如果在 worktree 目录打开为新 workspace：
- `${workspaceFolder}` = `cs_py-feat-xxx/`
- `PATH` 追加的是 `cs_py-feat-xxx/venv/gh/bin` → **不存在**
- gh CLI 调用失败

**解决方式**：
- 终端中 `cd` 进 worktree 执行，保持 `${workspaceFolder}` 仍指向主目录
- 或在 settings.json 中使用**绝对路径**而非 `${workspaceFolder}` 相对路径

#### 陷阱 B：脚本中的相对路径

```python
venv_py = Path("../../venv/py/python.exe")
```

在主目录 `cs_py/` 中执行：路径正确。
在 worktree `cs_py-feat-xxx/` 中执行：`../../venv/` 指向 worktree 外某处，**大概率错误**。

**解决方式**：所有工具链调用使用**绝对路径**或通过配置文件注入，禁止脚本内写死相对路径。

#### 陷阱 C：venv 共享

worktree 目录下没有 `venv/`。如果需要在 worktree 中运行 Python：
- **方案 1**：脚本中写**绝对路径**调用主目录的 venv Python（推荐，当前已实现）
- **方案 2**：在 worktree 下新建独立 venv（隔离但冗余）
- **方案 3**：符号链接 `mklink /D venv D:\pjt\cursor\cs_py\venv`（共享，但 Windows 软链接有权限要求）


## 选择建议

| 场景 | 推荐模式 |
|------|---------|
| 单线程开发，一次只做一件事 | checkout branch |
| Agent 跑 feature workflow，Human 同时查 master 代码 | worktree |
| 需要在多个分支间频繁对比文件 | worktree |
| 磁盘空间紧张 | checkout branch |
