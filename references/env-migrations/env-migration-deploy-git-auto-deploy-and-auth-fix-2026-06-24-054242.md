---
title: deploy-git-isolated 自动部署完善与 GitHub 认证弹窗修复
description: workflow-deploy-full.py --auto 全链条跑通，修复 GCM/Cursor GitHub 扩展弹窗、Popen 死锁、AI 摘要为空、upstream 超时等问题
date: 2026-06-24
meta: {}
---

# deploy-git-isolated 自动部署完善与 GitHub 认证弹窗修复

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | deploy-git-isolated workflow 自动部署完善（--auto + 前置验证 + 弹窗修复 + 死锁修复） |
| **日期** | 2026-06-24 |
| **文件名时间戳** | `2026-06-24-054242` |
| **触发原因** | 用户要求"现在自动部署github"，workflow 在 Step 7/8 弹出 GitHub 选账号窗口，且 Step 8 upstream 超时卡住 |
| **影响范围** | deploy-git-isolated 脚本体系、.vscode 工作区配置、LLM 客户端参数传递 |
| **风险等级** | 中（涉及 push 认证逻辑，但修复后更稳定） |


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | v1.2.0：加 `--auto` 参数、`_preflight_check()` 前置验证、reorder（add → AI 摘要 → commit）、Popen 改为 subprocess.run |
| **插入位置** | 全局重构 |
| **作用** | `--auto` 零参数自动部署；前置验证确保 .env + config.json 配置完整；AI 摘要失败可安全回滚；消除 Popen PIPE 死锁 |
| **验证方式** | `python workflow-deploy-full.py --auto` 全链条通过，无弹窗、不卡住 |
| **迁移方式** | 直接覆盖 |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-steps/step-07-github-push.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-07-github-push.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | push 前执行 `git config --local credential.helper ""` + 环境变量 `GCM_INTERACTIVE=0`、`GIT_TERMINAL_PROMPT=0` |
| **作用** | 双重阻断 Git Credential Manager OAuth 弹窗 |
| **验证方式** | push 时无 "Select an account" 弹窗 |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-steps/step-08-github-upstream.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-08-github-upstream.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | `git push -u origin <branch>` → `git branch --set-upstream-to origin/<branch> <branch>` |
| **作用** | Step 7 已 push，Step 8 只需本地 tracking，避免再次触发网络认证导致超时 |
| **验证方式** | upstream 步骤在 1s 内完成 |
| **迁移方式** | 直接覆盖 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 删除 AgentCore 构造时的 `model=None`、`temperature=None`、`max_tokens=1024` 等硬编码参数 |
| **作用** | 全部参数从 config.json 照搬，generate-ai-summary 不创造任何参数 |
| **验证方式** | AI 摘要正常生成，不为空 |
| **迁移方式** | 直接覆盖 |

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/llm_client.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/llm_client.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | `chat()` 函数中 max_tokens 加 fallback：未显式传入时，从 `provider_cfg.context_limit` 取值 |
| **作用** | 与 temperature 同模式，max_tokens 也从 config.json 来 |
| **验证方式** | kimi-k2.6 的 thinking 模式下 AI 摘要正常输出（context_limit=256000 保证 reasoning + content 都有空间） |
| **迁移方式** | 直接覆盖 |

### 6. 修改 `.vscode/settings.json`

| 属性 | 值 |
|------|-----|
| **路径** | `.vscode/settings.json` |
| **变更类型** | `追加` |
| **新增/修改内容** | `"github.gitAuthentication": false` |
| **作用** | 工作区级别禁用 Cursor 内置 GitHub 扩展的自动认证弹窗 |
| **验证方式** | push 时无 "The extension 'GitHub' wants to sign in" 弹窗 |
| **迁移方式** | 直接追加 |

### 7. 新建 `references/tasks/deploy-git-isolated/docs/playbooks/github-auth-popup-troubleshooting.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/playbooks/github-auth-popup-troubleshooting.md` |
| **变更类型** | `新建` |
| **作用** | 记录 GitHub 认证弹窗完整排查过程（GCM → system helper → Cursor 扩展）与最终解法 |
| **迁移方式** | 直接复制 |


## 二、非文本操作

本次无文件复制/缓存迁移。


## 三、环境变量速查

无需新增环境变量。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md` | `check-file-encoding.ps1` | BOM、CRLF、LF | BOM=no, CRLF=0, LF>0 |
| `.py` | `python -m py_compile` | 语法正确 | 无 SyntaxError |


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 自动部署全链条 | `python workflow-deploy-full.py --auto` | [SUCCESS]，总耗时 < 120s |
| 2 | 无弹窗 | 目视检查 Step 7/8 | 无 "Select an account"、无 "GitHub wants to sign in" |
| 3 | 不卡住 | 目视检查流程结束 | workflow 正常退出，不阻塞 |
| 4 | Issue 评论 | 查看 GitHub Issue #1 | 有新评论，含 AI 语义摘要 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 upstream 逻辑 | step-08 改回 `git push -u origin <branch>` |
| 恢复 Popen | workflow 改回 `subprocess.Popen` + `stdout=subprocess.PIPE` |
| 删除 .vscode 配置 | 移除 `.vscode/settings.json` 中 `github.gitAuthentication` 行 |
| 恢复 generate-ai-summary 参数 | 加回 `max_tokens=1024` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-24-054242 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求自动部署 GitHub，遇到弹窗和超时问题 |
| **下次修订条件** | workflow 新增 step、认证方式变更、编辑器行为变更 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
