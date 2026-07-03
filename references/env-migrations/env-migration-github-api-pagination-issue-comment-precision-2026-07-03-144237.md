---
title: GitHub API 分页与 Issue 评论精准定位能力增强
description: 为 github_api.py 添加分页遍历、since 时间筛选、单条 comment 精准获取能力；fetch_issue.py 新增 --all/--since/--limit/--latest/--comment-id 参数，解决 Issue 评论超过 30 条后数据丢失问题
date: 2026-07-03
meta:
  version: "1.0.0"
---

# env-migration-github-api-pagination-issue-comment-precision-2026-07-03-144237.md

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | GitHub API 分页与 Issue 评论精准定位能力增强 |
| **日期** | 2026-07-03 |
| **文件名时间戳** | `2026-07-03-144237` |
| **触发原因** | Issue #1 评论数达 43 条，fetch_issue.py 只能返回前 30 条（GitHub API 默认分页），今天的 comment 被截断不可见 |
| **影响范围** | `py-plugins/github_api.py`、`py-tools/fetch_issue.py` |
| **风险等级** | 低（向后兼容，新增功能） |

## 一、文本文件变更清单

### 1. 修改 `py-plugins/github_api.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/github_api.py` |
| **变更类型** | `修改` |
| **修改内容** | ① `invoke_api()` 新增 `return_headers` 参数（非破坏性，默认 False）；② `list_comments()` 新增 `per_page`/`since`/`page` 参数；③ 新增 `_parse_next_link()` 解析 Link header；④ 新增 `list_comments_all()` 自动遍历分页；⑤ 新增 `get_comment()` 精准单条获取 |
| **作用** | 消除 GitHub API 默认 30 条/页的分页限制，支持全量遍历、时间筛选、单条精准查询 |
| **验证方式** | lint 通过；fetch_issue.py --latest / --since / --comment-id / --all 全部测试通过 |
| **迁移方式** | 直接覆盖 |

### 2. 修改 `py-tools/fetch_issue.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/fetch_issue.py` |
| **变更类型** | `修改` |
| **修改内容** | 新增 CLI 参数：`--all`（全量遍历）、`--since`（时间筛选）、`--limit`（取最后 N 条）、`--latest`（快捷：等效于 --all --limit 1）、`--comment-id`（精准单条） |
| **作用** | 提供 5 种定位方式，覆盖"最新一条""今天全部""最近 N 条""精准 ID""全量"等场景 |
| **验证方式** | lint 通过；5 种模式实测全部通过 |
| **迁移方式** | 直接覆盖 |

## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。

## 三、环境变量速查

无新增环境变量。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文档） | run-lint.py (lint-encoding + md_lint) | BOM、双 BOM、CRLF、frontmatter | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, frontmatter 合规 |
| `.py`（github_api.py） | run-lint.py (lint-python + lint-encoding) | Python 语法、编码 | 语法通过、UTF-8 无 BOM |
| `.py`（fetch_issue.py） | run-lint.py (lint-python) | Python 语法 | 语法通过 |

**执行命令**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-github-api-pagination-issue-comment-precision-2026-07-03-144237.md" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\github_api.py" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\fetch_issue.py"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 获取最新一条评论 | `fetch_issue.py --issue-number 1 --latest` | 返回 Comment ID、时间、内容 |
| 2 | since 筛选今天 | `fetch_issue.py --issue-number 1 --since "2026-07-03T00:00:00Z"` | 只返回今天的评论 |
| 3 | 全量遍历 | `fetch_issue.py --issue-number 1 --all` | 返回全部 43 条（含 ID） |
| 4 | 精准单条 | `fetch_issue.py --issue-number 1 --comment-id 4873054704` | 返回该 ID 的具体内容 |
| 5 | 取最近 3 条 | `fetch_issue.py --issue-number 1 --all --limit 3` | 返回最后 3 条 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 github_api.py | `git checkout -- references/tasks/deploy-git-isolated/scripts/py-plugins/github_api.py` |
| 恢复 fetch_issue.py | `git checkout -- references/tasks/deploy-git-isolated/scripts/py-tools/fetch_issue.py` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-03-144237 |
| **更新人** | Human + Agent Session |
| **变更触发** | Issue #1 评论超过 30 条，fetch_issue.py 分页数据丢失 |
| **下次修订条件** | GitHub API 变更分页机制、新增评论筛选需求 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
