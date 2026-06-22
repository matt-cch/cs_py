---
title: deploy-git-isolated — Python 步骤脚本化（Step 5-9）+ Workflow 全链路编排 + 归档配置分离
description: 将 PS1 版 Step 5-9 改造为 Python 版 step 脚本；workflow-deploy-full.py 编排 4-9 全链路；archive 黑白名单配置从 py-plugins 硬编码分离到 py-tools JSON。
date: 2026-06-20
meta: {}
---

# deploy-git-isolated — Python 步骤脚本化 + Workflow 全链路编排 + 归档配置分离

## 变更概览

| 属性 | 值 |
|------|-----|
| **变更类型** | Feature（新增 py-steps 5-9）+ Refactor（archive 配置分离） |
| **影响范围** | `scripts/py-steps/`、`scripts/py-tools/`、`scripts/py-plugins/archive_config.py` |
| **风险等级** | 低（新增文件，不破坏既有 PS1 流程） |
| **触发原因** | 用户要求"做 step 5 以后的 python 改造并逐步验证执行"；后续要求 archive 黑白名单配置与代码分离 |


## 变更时间线

### 2026-06-20 — Python Step 脚本化与 Workflow 编排

| 变更项 | 之前 | 之后 | 触发原因 |
|--------|------|------|---------|
| Step 5: commit | 仅 PS1 `github-step-05-commit.ps1` | 新增 `py-steps/step-05-github-commit.py`，与 PS1 逻辑对齐 | Python 版全链路需要 |
| Step 6: remote | 仅 PS1 `github-step-06-remote.ps1` | 新增 `py-steps/step-06-github-remote.py`，Read-EnvConfig 严格校验、SKIP 逻辑对齐 | Python 版全链路需要 |
| Step 7: push | 仅 PS1 `github-step-07-push.ps1` | 新增 `py-steps/step-07-github-push.py`，PAT URL 构造、不修改 remote origin | Python 版全链路需要 |
| Step 8: upstream | 仅 PS1 `github-step-08-upstream.ps1` | 新增 `py-steps/step-08-github-upstream.py`，`git push -u origin <branch>` | Python 版全链路需要 |
| Step 9: issue sync | 仅 PS1 `github-sync-issue.ps1 -Mode comment` | 新增 `py-steps/step-09-github-sync-issue.py`，优先走 py_lib github_api 插件，fallback urllib | Python 版全链路需要 Issue 同步闭环 |
| Workflow 编排 | 仅支持 Step 4 | `py-tools/workflow-deploy-full.py` 支持 Step 4-9 编排，`--step` 新增 `9` | 用户要求 workflow 全链路执行 |
| archive 配置 | `py-plugins/archive_config.py` 硬编码 GROUPS_SPEC | 新增 `py-tools/archive-groups.json`，archive_config.py 从 JSON 加载配置 | 用户要求"黑白名单改配置即可，不动 plugins" |
| venv whitelist | `[".opencode", "data-opencode", "version"]` | `[".opencode", "data-opencode", "data-git", "version"]` | 用户要求 data-git 纳入归档 |


## 验证结果

| 检查项 | 结果 |
|--------|------|
| workflow Step 4-9 全链路（proxy 环境） | ✅ 通过，总耗时 11.89s |
| Issue #1 评论追加验证（py 版 fetch_issue.py） | ✅ 通过，Comment ID 4756645300 |
| cs_py 归档 scan→compress→verify | ✅ PASS（40727 文件，311.8 MB） |
| venv 归档 scan→compress→verify（含 data-git） | ✅ PASS（7167 文件，10.9 MB） |
| archive 配置分离后 venv 重新归档 | ✅ 配置从 JSON 读取，py-plugins 未改动 |
| 新建 `.py` 语法检查（py_compile） | ✅ 全部通过 |


## 已知问题（待优化）

| 问题 | 说明 | 后续方向 |
|------|------|---------|
| workflow 中断后需手动补执行剩余 step | Step 8 网络失败导致 workflow 整体退出，未自动继续 Step 9 | 可增加 `--continue-on-error` 参数或单 step 重试机制 |
| archive compress 耗时较长（cs_py 138s） | 40727 文件压缩是瓶颈 | 可评估降低压缩级别 `-mx=3` 或异步执行 |


## 关联文件

| 文件 | 变更状态 |
|------|---------|
| `scripts/py-steps/step-05-github-commit.py` | ✅ 新建 |
| `scripts/py-steps/step-06-github-remote.py` | ✅ 新建 |
| `scripts/py-steps/step-07-github-push.py` | ✅ 新建 |
| `scripts/py-steps/step-08-github-upstream.py` | ✅ 新建 |
| `scripts/py-steps/step-09-github-sync-issue.py` | ✅ 新建 |
| `scripts/py-tools/workflow-deploy-full.py` | ✅ 修改（v1.1.2，支持 Step 4-9） |
| `scripts/py-tools/archive-groups.json` | ✅ 新建（配置分离） |
| `scripts/py-plugins/archive_config.py` | ✅ 修改（`_load_groups_spec()` 从 JSON 加载） |
| `env-migration-deploy-git-py-steps-and-workflow-validation-2026-06-20-060000.md` | ✅ 新建（环境迁移记录） |


*变更日期: 2026-06-20*  
*记录人: Agent*  
*下次触发条件: 新增 Step 10+ / workflow 参数扩展 / archive 配置进一步细化*
