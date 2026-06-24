---
title: GitHub 认证弹窗排查与解法
description: deploy-git-isolated 自动部署时，push 阶段弹出的 GitHub 选账号/登录窗口的排查过程与最终解法
date: 2026-06-24
---

# GitHub 认证弹窗排查与解法

## 现象

运行 `workflow-deploy-full.py --auto` 时，Step 7 (git push) 阶段会弹出以下窗口之一：

1. **"Select an account"** — GitHub OAuth 账号选择弹窗（有两个账号 mattchoihk / matt-cch）
2. **"The extension 'GitHub' wants to sign in using GitHub."** — Cursor 编辑器 GitHub 扩展认证弹窗

用户需要手动点击 Allow / 选择账号，否则 push 会阻塞或流程卡住。

## 排查过程

### 第一轮：以为是 Git Credential Manager (GCM)

在 `step-07-github-push.py` 的 subprocess.run 中加入：

```python
env = os.environ.copy()
env["GCM_INTERACTIVE"] = "0"
env["GIT_TERMINAL_PROMPT"] = "0"
```

**结果**：弹窗仍在。

### 第二轮：发现 system 级别 credential.helper=manager

运行 `git config --list --show-origin | Select-String credential` 发现：

```
file:D:/pjt/cursor/cs_py/venv/git/etc/gitconfig  credential.helper=manager
file:C:/Users/Matt/.gitconfig                         credential.helperselector.selected=manager
file:C:/Users/Matt/.gitconfig                         credential.helper=store
```

根因：隔离 Git 的 **system 配置** 设置了 `credential.helper=manager`，而 `-c credential.helper=` 无法覆盖 system 级别（Git 会收集所有级别的 helper 依次调用，空值只是跳过，后续级别继续执行）。

在 push 前执行：

```python
subprocess.run(
    [str(git_exe), "-C", str(devroot), "config", "--local", "credential.helper", ""],
    capture_output=True
)
```

**结果**：GCM 弹窗消失，但出现了新的弹窗。

### 第三轮：发现真正来源是 Cursor 编辑器

弹窗标题变为 **"Cursor — The extension 'GitHub' wants to sign in using GitHub."**

来源不是 GCM，而是 **Cursor（VS Code 分支）内置的 GitHub 扩展模块**。当检测到 git push 到 GitHub 时，编辑器自动触发认证流程。

## 最终解法

在 **工作区级别**（`.vscode/settings.json`）禁用 GitHub 认证：

```json
{
    "github.gitAuthentication": false
}
```

**效果**：
- 仅影响当前项目（工作区级别）
- 不影响用户全局设置或其他项目
- push 不再触发任何认证弹窗

## 完整防护（脚本层）

`step-07-github-push.py` 中保留以下措施，防止其他环境出现 GCM 弹窗：

```python
# 1. local 级别覆盖空 helper，阻止 helper 链调用 GCM
subprocess.run(
    [str(git_exe), "-C", str(devroot), "config", "--local", "credential.helper", ""],
    capture_output=True
)

# 2. 环境变量兜底
env = os.environ.copy()
env["GCM_INTERACTIVE"] = "0"
env["GIT_TERMINAL_PROMPT"] = "0"

result = subprocess.run(
    [str(git_exe), "-C", str(devroot), "push", auth_url, branch],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    env=env
)
```

## 相关文件

- `references/tasks/deploy-git-isolated/scripts/py-steps/step-07-github-push.py`
- `.vscode/settings.json`

## 时间线

- 2026-06-24：问题发现，三轮排查，最终定位到 Cursor 内置 GitHub 扩展
