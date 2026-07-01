---
title: gh CLI 隔离部署与 PR merge 自动化闭环建设
description: 本次 session 完成 gh CLI 隔离部署、分支保护开启、PR create/merge 独立脚本建设、.gitignore 策略收紧、core.autocrlf 修正，实现 team mode 开发环境的本地自动化闭环。
date: 2026-06-30
meta:
  version: 1.0.0
  category: env-migration
---

# env-migration-gh-cli-pr-merge-automation-2026-06-30-173228

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | gh CLI 隔离部署与 PR merge 自动化闭环建设 |
| **日期** | 2026-06-30 |
| **文件名时间戳** | `2026-06-30-173228` |
| **触发原因** | 用户探索 PR merge 自动化闭环，需要 gh CLI 工具链支持；同时发现 .gitignore 策略不完整、core.autocrlf 配置隐患 |
| **影响范围** | settings.json、.gitignore、.git/config、gh_preflight 插件、gh-pr-create/gh-pr-merge/gh-branch-protect 脚本、workflow-deploy-full.py、step-07-github-push.py |
| **风险等级** | 中（分支保护开启后，直接 push 到 master 将被拒绝，需适应新流程） |


## 一、文本文件变更清单

### 1. 修改 `.vscode/settings.json`

| 属性 | 值 |
|------|-----|
| **路径** | `.vscode/settings.json` |
| **变更类型** | `追加` |
| **新增内容** | `"GH_CONFIG_DIR": "${workspaceFolder}\\venv\\data-gh"` 和 PATH 追加 `"${workspaceFolder}\\venv\\gh\\bin"` |
| **作用** | 终端/Agent bash 中 gh CLI 可直接调用，配置目录隔离 |
| **验证方式** | 新终端执行 `gh --version`，应输出版本号 |
| **迁移方式** | 直接追加 |

### 2. 修改 `.gitignore`

| 属性 | 值 |
|------|-----|
| **路径** | `.gitignore` |
| **变更类型** | `修改` |
| **修改内容** | `/*/` → `/*` + `!/README.md`；渐进放行逻辑保留；全局安全屏蔽保留 |
| **作用** | 真正排除根下所有文件和目录（不只是子目录），显式放行 README.md |
| **验证方式** | `git ls-files` 确认只有预期文件被追踪 |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `.git/config`

| 属性 | 值 |
|------|-----|
| **路径** | `.git/config` |
| **变更类型** | `追加` |
| **新增内容** | `core.autocrlf = false` |
| **作用** | 阻止 Git 自动 CRLF/LF 转换，保持文件原始编码 |
| **验证方式** | `git config --show-origin core.autocrlf` 显示 `file:.git/config false` |
| **迁移方式** | 仓库级配置，直接写入 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/gh_preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/gh_preflight.py` |
| **变更类型** | `新建` |
| **作用** | gh CLI 前置检测插件：验证 gh.exe 可用性、PAT 认证状态、返回 GhContext（含 run_gh 封装） |
| **验证方式** | `python workflow-gh-preflight-demo.py` 输出认证通过 |
| **迁移方式** | 直接复制 |

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | `追加` |
| **新增内容** | `gh_preflight` 插件条目（tags: `["github", "gh", "preflight"]`） |
| **作用** | 注册 gh_preflight 到 py_lib 插件体系 |
| **验证方式** | `py_lib.py list_plugins(tags=["gh"])` 包含 gh_preflight |
| **迁移方式** | 直接追加 |

### 6. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | `修改` |
| **新增内容** | Preflight 增加当前分支检测：`master` 分支直接 exit |
| **作用** | 防止在受保护分支上执行 workflow，避免 push 被拒绝 |
| **验证方式** | 在 master 分支执行 workflow，Step 0 应 exit |
| **迁移方式** | 直接覆盖 |

### 7. 修改 `references/tasks/deploy-git-isolated/scripts/py-steps/step-07-github-push.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-07-github-push.py` |
| **变更类型** | `修改` |
| **新增内容** | push 失败后检测 stderr 是否含 "rejected"/"protected"，给出明确提示 |
| **作用** | 分支保护冲突时给出业务级错误信息，而非裸 git 报错 |
| **验证方式** | 在 master 分支 push，应输出 "[HINT] 当前分支可能受保护" |
| **迁移方式** | 直接覆盖 |

### 8. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-create.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-create.py` |
| **变更类型** | `新建` |
| **作用** | 从当前分支创建 PR，支持 `--auto` AI 自动生成 title（基于 commits 聚合） |
| **验证方式** | `py gh-pr-create.py --auto --base master` 成功创建 PR |
| **迁移方式** | 直接复制 |

### 9. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-merge.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-merge.py` |
| **变更类型** | `新建` |
| **作用** | 合并 PR，默认 `--squash` 策略复用 PR title，支持 `--admin` 绕过分支保护 |
| **验证方式** | `py gh-pr-merge.py --admin --delete-branch` 成功 merge |
| **迁移方式** | 直接复制 |

### 10. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/gh-branch-protect.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/gh-branch-protect.py` |
| **变更类型** | `新建` |
| **作用** | 为指定分支开启 "Require pull request reviews before merging" 保护规则 |
| **验证方式** | `py gh-branch-protect.py --include-admin` 后 `gh api repos/.../branches/master/protection` 返回 200 |
| **迁移方式** | 直接复制 |


## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 下载 | GitHub Release cli/cli v2.95.0 | `D:\download\gh_cli-2.95.0.zip` | 14.13 MB，直连下载 |
| 解压 | `D:\download\gh_cli-2.95.0.zip` | `D:\download\gh_cli-2.95.0-extracted` | 临时解压 |
| 复制 | `D:\download\gh_cli-2.95.0-extracted\bin\gh.exe` | `D:\pjt\cursor\cs_py\venv\gh\bin\gh.exe` | 隔离部署 |
| 目录创建 | — | `D:\pjt\cursor\cs_py\venv\data-gh` | gh CLI 隔离配置目录 |
| 清理 | 临时解压目录 + zip | — | 删除 |
| API 调用 | GitHub REST API | `matt-cch/cs_py/branches/master/protection` | 开启分支保护（require PR reviews + include admin） |


## 三、环境变量速查

终端/Agent bash 中 gh CLI 调用需注入：

```powershell
$env:GH_TOKEN = $env:GITHUB_PAT              # 从 .env 读取
$env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"  # 隔离配置目录
```

settings.json 已配置：

```json
"terminal.integrated.env.windows": {
    "PATH": "...;${workspaceFolder}\\venv\\gh\\bin;${env:Path}",
    "GH_CONFIG_DIR": "${workspaceFolder}\\venv\\data-gh"
}
```


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py --fix` | frontmatter、CRLF/LF、BOM | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.json`（tools_config.json / verified-runtime-index.json） | `run-lint.py` | JSON 语法正确性 | `[OK]` 无解析错误 |
| `.py`（所有新建/修改脚本） | `run-lint.py` | Python 语法 + 编码 | `[OK]` 无解析错误 |

**执行结果**：全部通过，0 违规。


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 gh.exe 存在 | `Test-Path "${devroot}\venv\gh\bin\gh.exe"` | `True` |
| 2 | 确认 gh.exe 版本 | `& "${devroot}\venv\gh\bin\gh.exe" --version` | `gh version 2.95.0` |
| 3 | 确认认证状态 | `gh auth status`（GH_TOKEN + GH_CONFIG_DIR 已注入） | `Logged in to github.com` |
| 4 | 确认分支保护 | `gh api repos/{owner}/{repo}/branches/master/protection` | 返回 200，含 required_pull_request_reviews |
| 5 | 确认 master push 被拒绝 | 在 master 分支执行 `git push origin master` | `remote rejected: protected branch` |
| 6 | 确认 workflow preflight 拦截 | 在 master 分支执行 `workflow-deploy-full.py` | Step 0 exit，提示分支受保护 |
| 7 | 确认 autocrlf 关闭 | `git config --show-origin core.autocrlf` | `file:.git/config false` |
| 8 | 确认 .gitignore 排除根下所有 | `git ls-files` | 根下只有 .gitignore、README.md 等显式放行文件 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 gh_cli 索引 | 从 `verified-runtime-index.json` 的 `toolchain` 节删除 `gh_cli` 条目 |
| 移除 gh_cli 配置 | 从 `tools_config.json` 的 `tools` 数组删除 `gh_cli` 条目 |
| 删除隔离部署 | `Remove-Item -Recurse "${devroot}\venv\gh"` |
| 删除隔离配置 | `Remove-Item -Recurse "${devroot}\venv\data-gh"` |
| 关闭分支保护 | GitHub Web 端 Settings -> Branches -> 删除 master 保护规则 |
| 恢复 .gitignore | 回退到 `/*/` 版本（排除子目录但不排除根级文件） |
| 恢复 autocrlf | `git config --local core.autocrlf true`（如需恢复默认行为） |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-30-173228 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户探索 PR merge 自动化闭环，触发 gh CLI 部署需求；同步发现 .gitignore 策略不完整和 autocrlf 隐患 |
| **下次修订条件** | gh CLI 版本更新、分支保护规则调整、PR merge 策略变更 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
