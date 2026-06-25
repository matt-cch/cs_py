---
title: env-migration — Git 空目录保留归并 preflight + get-timestamp 参数勘误
description: 记录 deploy-git-isolated 工具链中 Git 空目录保留插件的落地、get-timestamp.py 参数误用修复，以及三处文档速查表的同步更新。
date: 2026-06-25
meta: {}
---

# env-migration — Git 空目录保留归并 preflight + get-timestamp 参数勘误

> **Session 主题**：deploy-git-isolated 工具链增强（空目录守卫 + 文档速查表补全）
> **文件名时间戳**：`2026-06-25-162358`
> **触发原因**：
> 1. 历史 commit `ddb1fc3` 中 Agent 偷偷 `git add` 绕过 `.gitignore`，导致 `references/env-migrations/` 有文件已在 remote 但目录结构仍可能被 Git 忽略空目录
> 2. Agent 多次误用 `get-timestamp.py --format local_compact`（该参数不存在），浪费反复试错时间
> **影响范围**：`references/tasks/deploy-git-isolated/scripts/py-plugins/`、`scripts/py-tools/workflow-deploy-full.py`、三处文档速查表
> **风险等级**：低（辅助性功能增强 + 文档修正）


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/git_keep_emptydir.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_keep_emptydir.py` |
| **变更类型** | `新建` |
| **职责** | 扫描指定目录列表，为空目录自动创建 `.gitkeep` 占位文件，使 Git 能跟踪空目录结构 |
| **暴露接口** | `ensure_empty_dirs(devroot, dir_paths)` → `{"created": [...], "skipped": [...]}` |
| **注册位置** | `py-sort-rules.json`（tags: `["git", "core"]`） |
| **验证方式** | `run-lint.py` 通过（`lint_python` + `lint_encoding`） |
| **迁移方式** | 新环境通过 `py_lib.load_plugins(devroot=..., tags=["git"])` 动态加载 |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | `修改` |
| **修改内容** | ① 删除文件顶部全局 `from py_lib import load_plugins`（避免无谓污染）；② 删除与 Step 4 同级的独立 "Step 0b" 代码块；③ 将 `git_keep_emptydir.ensure_empty_dirs()` 归并入 `_preflight_check()`，位于 agent 插件验证之后、最终通过声明之前；④ 在 `subprocess.run` 调用前增加 `sys.stdout.flush()` 修复输出顺序错乱；⑤ 局部 `from py_lib import load_plugins` 只在需要时导入 |
| **插入位置** | `_preflight_check()` 函数内部 |
| **作用** | 空目录保留成为 preflight 的一部分，不是独立 Step；stdout 顺序正确 |
| **验证方式** | `run-lint.py` 通过；`python workflow-deploy-full.py --help` 正常加载；实际部署验证通过（commit `68c2680`） |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `references/tasks/deploy-git-isolated/task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | `修改` |
| **修改内容** | 在 8.7.4 之后新增 8.7.5「Git 空目录保留规则」，记录根因、解法、架构约束、执行时序 |
| **版本更新** | `v1.6` → `v1.7` |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 直接追加 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `修改` |
| **修改内容** | Stage S5.7 `get-timestamp.py` 速查扩充：新增 CLI 参数表、格式键名与输出示例表、5 组常用命令（均带实际输出示例） |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 直接覆盖旧段落 |

### 5. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `修改` |
| **修改内容** | 1.5 节格式键名表增加「典型用途」「示例输出」两列；新增 CLI 参数表 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 直接覆盖旧段落 |

### 6. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `修改` |
| **修改内容** | `get-timestamp-py.entry_command` 更新为包含全部 7 个格式键名 + `--source` 参数 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 直接编辑 |


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等非文本操作。


## 三、环境变量速查

无新增环境变量。


## 四、落盘验证

| 文件 | 验证工具 | 验证内容 | 结果 |
|------|---------|---------|------|
| `git_keep_emptydir.py` | `run-lint.py`（`lint_python` + `lint_encoding`） | 语法、编码、BOM、换行符 | ✅ 通过 |
| `workflow-deploy-full.py` | `run-lint.py`（`lint_python` + `lint_encoding`） | 语法、编码、BOM、换行符 | ✅ 通过 |
| `task-canonical-baseline.md` | `run-lint.py`（`md_lint` + `lint_encoding`） | frontmatter、编码、换行符 | ✅ 通过 |
| `EXEC-CHEATSHEET.md` | `run-lint.py`（`md_lint` + `lint_encoding`） | frontmatter、编码、换行符 | ✅ 通过 |
| `TASK-TOOLS-INDEX.md` | `run-lint.py`（`md_lint` + `lint_encoding`） | frontmatter、编码、换行符 | ✅ 通过 |
| `verified-task-index.json` | `run-lint.py`（`lint_json` + `lint_encoding`） | JSON 语法、编码 | ✅ 通过 |


## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认空目录插件可加载 | `python -c "from py_lib import load_plugins; r=load_plugins(devroot='...', tags=['git']); print(r.git_keep_emptydir)"` | 输出模块对象，无 ImportError |
| 2 | 确认 workflow 输出顺序正确 | `python workflow-deploy-full.py --help` | Preflight 信息在步骤列表之前 |
| 3 | 确认 get-timestamp 全部格式可用 | `python get-timestamp.py --all` | 输出 7 个键值对，无 "未知格式" 错误 |
| 4 | 确认部署自闭环 | `python workflow-deploy-full.py --auto` | Step 0→9 顺序执行，Issue comment 追加成功 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除空目录插件 | 删除 `py-plugins/git_keep_emptydir.py`，从 `py-sort-rules.json` 移除对应条目 |
| 回退 workflow | `git checkout HEAD -- workflow-deploy-full.py` |
| 回退 baseline | `git checkout HEAD -- task-canonical-baseline.md` |
| 回退文档 | `git checkout HEAD -- EXEC-CHEATSHEET.md TASK-TOOLS-INDEX.md` |
| 回退索引 | `git checkout HEAD -- verified-task-index.json` |


## 七、已知问题与待优化

1. **空目录列表未配置化**：当前 `references/env-migrations` 和 `references/tasks/deploy-git-isolated` 是硬编码在 `workflow-deploy-full.py` 中的。未来应提取到 `task-config.json` 或同类 Config 契约。
2. **get-timestamp.py 曾误用 `local_compact`**：该参数从未存在，是 Agent 记忆错误。现已通过三处文档速查表全面登记正确参数，避免后续 session 再犯。


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-25-162358 |
| **更新人** | Human + Agent Session |
| **变更触发** | Git 空目录问题暴露 + get-timestamp 参数误用反复踩坑 |
| **下次修订条件** | 空目录列表配置化提取到 JSON；新增需保留空目录的目录 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-25-162358*  
*模板版本：v2*
