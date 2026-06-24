---
title: deploy-git-isolated — 统一三源工具登记 + 修复文件分类逻辑
description: 统一 TASK-TOOLS-INDEX.md、verified-task-index.json、EXEC-CHEATSHEET.md 三处对 run-lint.py / workflow-deploy-full.py / get-timestamp.py 的登记信息；修复 workflow-deploy-full.py 中 .md 文件被误判为"脚本改造"的分类逻辑。
date: 2026-06-24
meta: {}
---

# deploy-git-isolated — 统一三源工具登记 + 修复文件分类逻辑

## 变更概览

| 属性 | 值 |
|------|-----|
| **变更类型** | Refactor（登记信息对齐）+ Bugfix（分类逻辑） |
| **影响范围** | `references/runtime/verified-task-index.json`、`TASK-TOOLS-INDEX.md`、`EXEC-CHEATSHEET.md`、`workflow-deploy-full.py` |
| **风险等级** | 低（纯文档/逻辑对齐，无行为变更） |
| **触发原因** | 用户发现三处登记源对同一工具的描述不一致；Issue comment 中 .md 文件被误分类为"脚本改造" |


## 变更时间线

### 2026-06-24 — 三源统一

| 变更项 | 之前 | 之后 | 触发原因 |
|--------|------|------|---------|
| verified-task-index.json 缺 run-lint | 未登记 | 新增 `run-lint` 条目，含 `--profile`/`--files`/`--fix`/`--audit` 能力说明 | TASK-TOOLS-INDEX 和 EXEC-CHEATSHEET 均已详述，但 JSON 索引缺失 |
| verified-task-index.json 缺 workflow-deploy-full | 未登记 | 新增 `workflow-deploy-full` 条目，含 `--auto`/`--step`/`--issue` 能力说明 | 同上 |
| get-timestamp PS1 版状态 | 普通登记，无状态标记 | 名称加 "legacy"，新增 `status: "legacy"`，description 注明已替代 | Python 版是当前推荐，PS1 仅 fallback |
| get-timestamp Python 版描述 | 未强调"禁止现写" | 强调 Agent 必须用它生成时间戳，禁止现写时间字符串 | AGENTS.md 铁律要求 |
| TASK-TOOLS-INDEX.md section 2 | 含 `get-timestamp.ps1` 外部工具行 | **移除**该行（该工具是 task 本地工具，已在 section 1.5 详述） | 避免重复登记、避免误导 |
| TASK-TOOLS-INDEX.md 边界矩阵 | `生成时间戳文件名` → `get-timestamp.ps1`（通用） | 改为 `get-timestamp.py`（本地 workflow） | 与当前推荐对齐 |
| EXEC-CHEATSHEET.md Stage S5.3 | 缺 `--auto` 示例 | 补充 `--auto` 全自动发布示例（Agent + 终端各一份） | 用户高频使用 `--auto` |
| EXEC-CHEATSHEET.md 缺 Stage S5.7 | 无 | 新增 Stage S5.7 `get-timestamp.py` 速查（`local_iso` / `filename_safe` / `--all` / `--json`） | 禁止现写铁律需要速查入口 |

### 2026-06-24 — 分类逻辑修复

| 变更项 | 之前 | 之后 | 触发原因 |
|--------|------|------|---------|
| workflow-deploy-full.py 第 194 行 | 纯按路径关键词判断：`"scripts/" in p` → 脚本改造 | **扩展名优先**：`.md`/`.mdc`/`.txt`/`.rst` 先判定为"文档更新"，再按路径判断脚本 | `scripts/EXEC-CHEATSHEET.md` 被误分类为"脚本改造"，实际为 Markdown 文档 |


## 验证结果

| 检查项 | 结果 |
|--------|------|
| 三文件 lint 验证（verified-task-index.json + TASK-TOOLS-INDEX.md + EXEC-CHEATSHEET.md） | ✅ 全部通过，0 违规 |
| workflow-deploy-full.py 语法检查（py_compile） | ✅ 通过 |
| 自动部署验证（`--auto`） | ✅ 通过，总耗时 81.07s，无弹窗不卡住 |
| Issue #1 评论追加 | ✅ 通过，Comment ID 4786679844 |
| 文件分类正确性 | ✅ `EXEC-CHEATSHEET.md` 不再被误判为"脚本改造" |


## 关联文件

| 文件 | 变更状态 |
|------|---------|
| `references/runtime/verified-task-index.json` | ✅ 修改（新增 2 条目、更新 2 条目） |
| `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` | ✅ 修改（移除 1 行、修正 1 处） |
| `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` | ✅ 修改（新增 Stage S5.7、补充 `--auto`） |
| `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` | ✅ 修改（分类逻辑扩展名优先） |


*变更日期: 2026-06-24*  
*记录人: Agent*  
*下次触发条件: 新增/删除工具条目、分类逻辑进一步细化*
