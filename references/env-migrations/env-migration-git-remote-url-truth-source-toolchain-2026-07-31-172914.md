---
title: Git Remote URL 真源检测工具链改造
description: 修复 atomic-deploy-preflight.py 的 repo_url 审计逻辑缺陷，引入 GitHub API 远程真源验证、URL 规范化比对、manifest 落盘，并统一 atomic-gh-repo-create.py 的 URL 格式。
date: 2026-07-31
meta:
  version: "1.0.0"
  category: env-migration
---

# env-migration-git-remote-url-truth-source-toolchain-2026-07-31-172914

> **文档性质**：环境级变更记录。聚焦工具链审计逻辑缺陷修复与真源验证能力引入。
> **受众**：Human + Agent。新环境复现时按「文本文件变更清单」逐条复制即可。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Git Remote URL 真源检测工具链改造 |
| **日期** | 2026-07-31 |
| **文件名时间戳** | `2026-07-31-172914` |
| **触发原因** | 检查 jywl-settlement 进度时，atomic-deploy-preflight.py 的 repo_url 审计报 FAIL（git-remote 与 git-security 不匹配），经多轮讨论发现是工具链设计缺陷 |
| **影响范围** | py-plugins/github_api.py、py-tools/atomic-deploy-preflight.py、py-tools/atomic-gh-repo-create.py、EXEC-CHEATSHEET.md、verified-task-index.json、wiki 知识库 |
| **风险等级** | 中（触及核心审计脚本，但只增加能力、不改变原有成功路径） |


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/github_api.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/github_api.py` |
| **变更类型** | `修改`（新增方法） |
| **新增内容** | `_canonicalize_url()` + `fetch_repo_metadata()` |
| **作用** | 新增从 GitHub REST API 获取仓库服务端真源元数据的能力；提供 URL 规范化辅助函数 |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接复制文件（新增方法不破坏既有调用） |

#### 新增方法详情

```python
def _canonicalize_url(url: str) -> str:
    """URL 规范化：去掉尾部斜杠和 .git 后缀，统一小写。"""


def fetch_repo_metadata(owner: str, repo: str, pat: str) -> Dict[str, Any]:
    """
    从 GitHub REST API 获取仓库服务端真源元数据（server-side canonical truth）。
    返回包含 clone_url（带 .git）、html_url（不带 .git）、default_branch 等字段。
    注意：这是网络请求，不是读取本地 .git/config 或 git remote get-url。
    """
```

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py` |
| **变更类型** | `修改`（核心逻辑升级） |
| **作用** | repo_url 审计从"两本地字符串严格相等"升级为"三方验证 + 规范化比对 + manifest 落盘" |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过；实测 jywl-settlement + cs_py 均通过 |
| **迁移方式** | 直接覆盖（向后兼容，新增 `--output` 参数为可选） |

#### 核心改造点

1. **新增 `--output` 参数**：支持显式指定 manifest 输出路径（workflow 调用契约）
2. **新增 `_canonicalize_url()`**：URL 规范化（去 `.git` + 去尾部斜杠 + 小写）
3. **新增 `_save_manifest()`**：preflight 结果落盘到 JSON，供下游 workflow 消费
4. **三方验证逻辑**：
   - `git-security.json` 的 `repo_url`（预期声明）
   - `git remote get-url origin`（本地历史记录）
   - `github_api.fetch_repo_metadata()`（远程真源）
5. **所有 exit 出口均落盘 manifest**：成功/失败均可追溯

#### manifest 结构示例

```json
{
  "atomic_tool": "atomic-deploy-preflight",
  "version": "1.1.0",
  "repo_url_audit": {
    "security_url": "https://github.com/matt-cch/jywl-settlement.git",
    "local_remote_url": "https://github.com/matt-cch/jywl-settlement",
    "github_clone_url": "https://github.com/matt-cch/jywl-settlement.git",
    "github_html_url": "https://github.com/matt-cch/jywl-settlement",
    "canonical_security": "https://github.com/matt-cch/jywl-settlement",
    "canonical_local": "https://github.com/matt-cch/jywl-settlement",
    "canonical_github": "https://github.com/matt-cch/jywl-settlement",
    "method": "github_api.fetch_repo_metadata",
    "audit_result": "pass"
  }
}
```

### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-create.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-create.py` |
| **变更类型** | `修改`（单行修复） |
| **变更前** | `repo_url = f"https://github.com/{full_name}"` |
| **变更后** | `repo_url = f"https://github.com/{full_name}.git"` |
| **作用** | 与 GitHub 网页 Clone URL 标准对齐，避免后续新仓库的 `.git/config` 中遗留不带 `.git` 的 URL |
| **验证方式** | `run-lint.py lint_python + lint_encoding` 通过 |
| **迁移方式** | 直接覆盖 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `修改`（用法示例更新） |
| **作用** | atomic-deploy-preflight 用法示例更新为含 `--devroot --target --output` 的完整命令 |
| **迁移方式** | 直接覆盖对应段落 |

### 5. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `修改`（条目更新） |
| **作用** | `atomic-deploy-preflight` 条目的 description、typical_scenarios、entry_command、verified_at 同步更新 |
| **迁移方式** | 直接覆盖对应 JSON 对象 |

### 6. 新建 `vaults/vault-demo/wiki/learnings/git-remote-url-truth-source-audit-2026-07-31-165721.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/learnings/git-remote-url-truth-source-audit-2026-07-31-165721.md` |
| **变更类型** | `新建` |
| **作用** | 知识库沉淀：记录从"两个本地字符串打架"到"真源在 remote 网页"的认知跃迁过程 |
| **迁移方式** | 直接复制 |


## 二、非文本操作

本次 session 未涉及文件系统/缓存迁移等非文本操作。


## 三、环境变量速查

本次 session **未新增**环境变量，复用既有配置：

| 变量 | 来源 | 用途 |
|------|------|------|
| `GITHUB_PAT` | `devroot/.env` | GitHub API / GH CLI 认证 |
| `GITHUB_USERNAME` | `devroot/.env` | git config user.name / 认证 URL 构造 |


## 四、落盘验证

| 文件 | 验证工具 | 结果 |
|------|---------|------|
| `github_api.py` | `run-lint.py lint_python + lint_encoding` | ✅ 通过 |
| `atomic-deploy-preflight.py` | `run-lint.py lint_python + lint_encoding` | ✅ 通过 |
| `atomic-gh-repo-create.py` | `run-lint.py lint_python + lint_encoding` | ✅ 通过 |
| `EXEC-CHEATSHEET.md` | `run-lint.py lint_md + lint_encoding` | ✅ 通过 |
| `verified-task-index.json` | `run-lint.py lint_json + lint_encoding` | ✅ 通过 |
| `wiki 知识库文章` | `run-lint.py lint_md + lint_encoding` | ✅ 通过 |


## 五、验证清单（新环境可执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 preflight 对 jywl-settlement 通过 | `atomic-deploy-preflight.py --devroot "${devroot}" --target "${devroot}\apps\repos\matt-cch\jywl-settlement"` | `[OK] repo_url 审计通过: git-remote、git-security、GitHub 真源三方一致` |
| 2 | 确认 manifest 已落盘 | `Test-Path "${devroot}\venv\tmp\deploy-preflight-manifest-*.json"` | `True` |
| 3 | 确认 manifest 含 repo_url_audit | `Select-String -Path "${devroot}\venv\tmp\deploy-preflight-manifest-*.json" -Pattern "repo_url_audit"` | 有匹配 |
| 4 | 确认 github_api 新增方法可用 | `python -c "import github_api; print('fetch_repo_metadata' in dir(github_api))"` | `True` |
| 5 | 确认 gh-repo-create 构造 URL 带 .git | `Select-String -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-create.py" -Pattern "\.git\"$"` | 有匹配 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 preflight 旧版本 | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-deploy-preflight.py"` |
| 恢复 github_api 旧版本 | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\github_api.py"` |
| 恢复 gh-repo-create 旧版本 | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-create.py"` |
| 删除知识库文章 | `Remove-Item "${devroot}\vaults\vault-demo\wiki\learnings\git-remote-url-truth-source-audit-2026-07-31-165721.md"` |


## 七、关联文档

| 文档 | 说明 |
|------|------|
| `vaults/vault-demo/wiki/learnings/git-remote-url-truth-source-audit-2026-07-31-165721.md` | 知识库：认知跃迁过程与真源对比 |
| `references/env-migrations/env-migration-jywl-settlement-polyrepo-init-2026-07-21-173210.md` | jywl-settlement 初始化记录 |
| `references/env-migrations/env-migration-polyrepo-structure-and-git-security-alignment-2026-07-24-171616.md` | git-security 语义对齐 + worktree 规划 |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-31-172914 |
| **更新人** | Human + Agent Session |
| **变更触发** | jywl-settlement 的 atomic-deploy-preflight repo_url 审计失败 → 工具链改造 |
| **下次修订条件** | atomic-git-worktree-link-config.py 开发完成；或 preflight 发现新的审计边界情况 |
| **跨环境迁移参考** | 直接复制本文档「文本文件变更清单」中的全部文件到新环境对应路径 |
