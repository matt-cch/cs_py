---
title: deploy-git-isolated GitHub 发布 — 从本地 task 到远程仓库的完整迁移
description: 记录将 deploy-git-isolated task 发布到 GitHub 仓库的完整环境级变更，包括 .gitignore 白名单策略、.gitattributes LF 强制、动态 devroot 探测、自动化 Issue 脚本及踩坑记录。
date: 2026-06-17
---

# env-migration-deploy-git-isolated-github-publish-2026-06-17-013059

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | deploy-git-isolated task 发布到 GitHub 仓库（matt-cch/cs_py） |
| **日期** | 2026-06-17 |
| **文件名时间戳** | `2026-06-17-013059` |
| **触发原因** | 用户要求将 `references/tasks/deploy-git-isolated/` 发布到 GitHub，其他目录保持不 push；借鉴 GBrain/goal/Tolaria 三篇文章原理设计发布策略 |
| **影响范围** | `.gitignore`（全局白名单策略）、task 目录内 `.gitattributes` + `constants.ps1` + `github-create-issue.ps1` + `github-publish-playbook.md` |
| **风险等级** | 中（涉及全局 .gitignore 重写，可能误排除未来目录） |


## 一、文本文件变更清单

### 1. 修改 `.gitignore`（根级白名单策略）

| 属性 | 值 |
|------|-----|
| **路径** | `D:\pjt\cursor\cs_py\.gitignore` |
| **变更类型** | 重写 |
| **新增/修改内容** | 从"黑名单排除敏感文件"改为"白名单只放行目标目录"：`/*/` 排除所有根级子目录，逐层 `!` 放行 `references/tasks/deploy-git-isolated/` |
| **作用** | 确保 push 时只上传目标目录，其他路径（venv/、apps/、schema/ 等）保持不跟踪 |
| **验证方式** | `git check-ignore -v references/tasks/deploy-git-isolated/README.md` → 未忽略；`git check-ignore -v apps/api-demo/pyproject.toml` → 被忽略 |
| **迁移方式** | 直接覆盖 `.gitignore`，后续渐进式放开其他目录时追加 `!` 规则 |

### 2. 新建 `.gitattributes`（LF 换行符强制）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/.gitattributes` |
| **变更类型** | 新增 |
| **新增内容** | `* text eol=lf` + 二进制文件豁免（*.png、*.zip 等） |
| **作用** | 确保 Windows / Linux / GitHub 三者换行符一致，防止 CRLF 污染 |
| **验证方式** | clone 后检查文件字节：`CRLF=0, LF>0` |
| **迁移方式** | 直接复制文件到目标目录 |

### 3. 修改 `constants.ps1`（动态 devroot 探测）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/lib-plugins/constants.ps1` |
| **变更类型** | 修改 |
| **新增/修改内容** | 从硬编码 `$devroot = 'D:\pjt\cursor\cs_py'` 改为从 `$PSScriptRoot` 向上遍历，探测包含 `references/` 目录的路径作为 devroot |
| **作用** | 实现跨机器可复用，clone 到其他路径后脚本仍能正确定位 devroot |
| **验证方式** | 在 `venv/tmp/github-pull-test/cs_py/`（clone 路径）下执行 `git-isolated.ps1 status`，确认不穿透到外层 devroot |
| **迁移方式** | 直接覆盖文件 |

### 4. 新建 `github-create-issue.ps1`（自动化 Issue 创建）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-create-issue.ps1` |
| **变更类型** | 新增 |
| **作用** | 调用 GitHub REST API 自动创建带 `task-active` label 的追踪 Issue，从 `.env` 读取 PAT，提取当前 commit 信息生成结构化 body |
| **验证方式** | 执行后访问 `https://github.com/matt-cch/cs_py/issues/1`，确认中文正常显示 |
| **迁移方式** | 直接复制文件，修改 `$issueTitle` 和 body 模板可为其他 task 复用 |

### 5. 新建 `github-publish-playbook.md`（发布手册）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/github-publish-playbook.md` |
| **变更类型** | 新增 |
| **作用** | 记录发布前因后果（三篇文章原理启发）、实施时间线、形成的脚本、踩坑记录、后续操作指引 |
| **迁移方式** | 直接复制文件 |


## 二、非文本操作（Git 操作与 GitHub 交互）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 分支创建 | `master` | `task/deploy-git-isolated` | 长期运行分支，承载 task 全部变更历史 |
| git add | `references/tasks/deploy-git-isolated/` | staged | 精确添加目标目录（43 个文件） |
| git commit | working tree | local repo | 5 个 commits，记录完整演进 |
| git push | local repo | `origin/task/deploy-git-isolated` | 推送到远程仓库 |
| GitHub API | local script | `matt-cch/cs_py/issues` | 创建 Issue #1，用于变更追踪 |

### 复现命令

```powershell
# Step 1: 创建分支
& "${devroot}\venv\git\cmd\git.exe" -C "${devroot}" checkout -b task/deploy-git-isolated

# Step 2: 精确添加目标目录
& "${devroot}\venv\git\cmd\git.exe" -C "${devroot}" add "references/tasks/deploy-git-isolated/"

# Step 3: Commit
& "${devroot}\venv\git\cmd\git.exe" -C "${devroot}" commit -m "feat: deploy-git-isolated v0.5.0"

# Step 4: Push
& "${devroot}\venv\git\cmd\git.exe" -C "${devroot}" push -u origin task/deploy-git-isolated

# Step 5: 自动化创建 Issue
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-create-issue.ps1"
```


## 三、环境变量速查

本次 session 依赖 `.env` 中的以下配置：

```
GITHUB_USERNAME=matt-cch
GITHUB_REPO_URL=https://github.com/matt-cch/cs_py.git
GITHUB_PAT=ghp_...
```

> **注意**：PAT 需为 `classic` 类型且含 `repo` 权限，GitHub 已不支持密码认证。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `check-file-encoding.ps1` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认分支存在 | `git branch -a` | 显示 `task/deploy-git-isolated` |
| 2 | 确认文件已 push | `git ls-tree -r --name-only origin/task/deploy-git-isolated` | 包含 `references/tasks/deploy-git-isolated/` 下全部文件 |
| 3 | 确认其他目录未 push | `git ls-tree -r --name-only origin/task/deploy-git-isolated \| grep "^apps/"` | 无输出 |
| 4 | 确认 Issue 已创建 | 访问 `https://github.com/<user>/<repo>/issues/1` | 显示中文正常的追踪 Issue |
| 5 | 确认换行符为 LF | `git show origin/task/deploy-git-isolated:references/tasks/deploy-git-isolated/README.md \| file -` | 显示 `ASCII text`（无 `CRLF`） |
| 6 | 确认动态探测正确 | 在 clone 路径下执行 `git-isolated.ps1 status` | 不穿透到外层 devroot |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除远程分支 | `git push origin --delete task/deploy-git-isolated` |
| 删除本地分支 | `git branch -D task/deploy-git-isolated` |
| 恢复 .gitignore | `git checkout master -- .gitignore`（或从 git history 恢复） |
| 删除 GitHub Issue | 在 Web 界面手动关闭 Issue #1 |


## 七、踩坑记录（本次 session 独有）

### 7.1 PowerShell 5.1 Invoke-RestMethod 编码陷阱

| 维度 | 详情 |
|------|------|
| **现象** | `github-create-issue.ps1` 首次执行后，GitHub Issue 中文全部显示为 `????` |
| **根因** | PowerShell 5.1 `Invoke-RestMethod` 的 `-Body` 参数传入字符串时，默认使用系统 ANSI 编码（GBK）发送 HTTP body |
| **修复** | 显式 `[System.Text.Encoding]::UTF8.GetBytes($bodyJson)` + `ContentType: 'application/json; charset=utf-8'` |
| **教训** | PowerShell 5.1 的 HTTP 客户端层默认编码与脚本文件编码（UTF-8 BOM）不一致，发送中文时必须手动干预编码层 |

### 7.2 .ps1 文件 UTF-8 BOM 双保险

| 维度 | 详情 |
|------|------|
| **现象** | 编写 `github-create-issue.ps1` 时，初次落盘未加 BOM，PowerShell 5.1 解析中文注释时语法错误 |
| **修复** | 通过 `[System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding $true))` 重写 |
| **教训** | 含中文的 `.ps1` 必须 UTF-8 with BOM，这是项目硬性规则 |

### 7.3 动态探测 devroot 的嵌套穿透

| 维度 | 详情 |
|------|------|
| **现象** | 在 `venv/tmp/github-pull-test/cs_py/`（clone 路径）下执行 `git-isolated.ps1`，探测到外层原始 devroot `D:\pjt\cursor\cs_py` |
| **根因** | 早期探测逻辑依赖 `venv\git\cmd\git.exe` 存在，但 clone 目录无 `venv/`（被 .gitignore 排除），导致向上穿透 |
| **修复** | 改为固定目录深度探测：从 `$PSScriptRoot` 向上遍历直到找到 `references/` 目录（task 标志性路径），不依赖 `venv/` 是否存在 |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-17-013059 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求将 deploy-git-isolated task 发布到 GitHub，借鉴三篇文章原理设计发布策略 |
| **下次修订条件** | 新增 task 需要 GitHub 发布、或优化 devroot 探测逻辑、或 .gitignore 渐进式放开其他目录时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 + 核对 `.env` 中 GITHUB_PAT 有效性 |


*文档生成时间：2026-06-17*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
