---
title: Git CWD 陷阱 — 命令中的 . 与 --devroot 参数不一致
description: workflow 传 --devroot 但 git 命令未显式 -C 切换目录时，. 指向 shell CWD 而非 devroot，导致跨目录 workflow 执行出现偏差。
date: 2026-07-01
meta:
  version: 1.0.0
  category: gotcha
---

# Git CWD 陷阱 — 命令中的 `.` 与 `--devroot` 参数不一致

## 现象

`workflow-deploy-full.py` 接收 `--devroot` 参数，理论上操作指定目录的 git 仓库。但在 worktree 模式下，如果人在 `cs_py/` (master) 目录执行：

```powershell
python workflow-deploy-full.py --devroot D:\pjt\cursor\cs_py-feat-xxx --auto
```

如果 step 脚本内部写成：

```python
# 错误：没有 -C，. 指向当前 shell 的 CWD（cs_py/ 而非 cs_py-feat-xxx/）
subprocess.run([git_exe, "add", "."])
```

结果：`git add .` 实际添加的是 `cs_py/` 下的文件，而非 `cs_py-feat-xxx/` 下的文件。

## 根因

`--devroot` 只是 Python 脚本的参数，**不改变 shell 的当前工作目录（CWD）**。
`git add .` 中的 `.` 由 shell/CWD 解析，与 `--devroot` 参数无关。

## 修复方式

### 方式 1：脚本内部显式 `-C`（当前已实现）

```python
# 正确：-C 强制 git 以 devroot 为执行目录
subprocess.run([git_exe, "-C", str(devroot), "add", "-A"])
```

### 方式 2：脚本内部 `os.chdir(devroot)`

```python
# 正确：改变当前进程 CWD
os.chdir(devroot)
subprocess.run([git_exe, "add", "."])
```

### 方式 3：执行前 cd（用户侧最佳实践）

```powershell
# 最保险：先 cd，让 CWD 和 --devroot 一致
cd D:\pjt\cursor\cs_py-feat-xxx
python workflow-deploy-full.py --auto
```

> 方式 3 是推荐实践。即使脚本有 bug（漏了 `-C`），cd 后 `git add .` 的 `.` 也必然指向正确目录。

## 验证

检查 step 脚本是否合规：

```powershell
# 搜索 git 命令是否带 -C 参数
Select-String -Path "references/tasks/deploy-git-isolated/scripts/py-steps/*.py" -Pattern "git.*-C.*devroot"
```

## 当前状态

`step-04-github-deploy-add.py` 第 47 行已正确实现：
```python
[str(git_exe), "-C", str(devroot), "add", "-A"]
```

但此陷阱仍需记录，供后续新增 step 脚本时参考。
