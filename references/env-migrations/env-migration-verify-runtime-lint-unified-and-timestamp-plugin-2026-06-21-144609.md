---
title: env-migration — 真源检测验证统一化 + timestamp 插件体系 + py-tools 分层模式
description: 本次 session 将真源检测后的验证工具统一为 task 本地 run-lint.py（混合类型自动路由），新增 timestamp 插件体系（统一时间来源 + 格式化器），并明确 py-tools 原子型/编排型分层模式。同步修正 baseline 铁律。
date: 2026-06-21
meta: {}
---

# env-migration-verify-runtime-lint-unified-and-timestamp-plugin-2026-06-21-144609

| 字段 | 值 |
|------|-----|
| **Session 主题** | 真源检测验证统一化 + timestamp 插件体系 + py-tools 原子型/编排型分层 |
| **日期** | 2026-06-21 |
| **文件名时间戳** | `2026-06-21-144609` |
| **触发原因** | ① 真源检测后验证工具过期（仍引用 schema/tool/lint-json.py 而非 task 本地 run-lint.py）；② 写入 .md/.json 时间字段缺乏标准化时间戳工具；③ py-tools/ 内原子型与编排型 workflow 混为一谈，导致 JSON 配置决策混乱 |
| **影响范围** | .cursor/rules/*.mdc、references/tasks/deploy-git-isolated/scripts/、references/runtime/verified-task-index.json、task-canonical-baseline.md |
| **风险等级** | 低（工具链增强，不涉及业务代码或运行时环境变更） |


## 一、文本文件变更清单

### 1. 修改 .cursor/rules/high-frequency-verify-runtime.mdc

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-verify-runtime.mdc` |
| **变更类型** | 修改 |
| **作用** | 真源检测执行后，验证工具从 `schema/tool/lint-json.py` 统一改为 task 本地 `run-lint.py`（支持 JSON + Markdown + PowerShell + Python + Encoding 混合类型自动路由） |
| **关键变更** | ① 执行后动作第 3 步表述更新；② 新增「验证铁律」章节含自动路由扩展名映射表；③ 验证命令首选 `run-lint.py --files`，fallback `lint-json.py` |
| **验证方式** | `run-lint.py` 扫描本文件 → `md_lint` 插件通过 |

### 2. 修改 .cursor/rules/high-frequency-env-migration.mdc

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-env-migration.mdc` |
| **变更类型** | 修改 |
| **作用** | env-migration 落盘验证步骤统一化：从「.md 用 check-file-encoding.ps1；.json 用 lint-json.py」改为「统一用 `run-lint.py` 验证混合类型」 |
| **验证方式** | `run-lint.py` 扫描本文件 → `md_lint` 插件通过 |

### 3. 修改 task-canonical-baseline.md

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | 修改 |
| **作用** | 修正铁律：从「优先使用 schema/tool/ 下已登记工具」改为「优先查已登记/注册的命令速查表（verified-task-index.json → available_scripts_and_tools，或本 task TASK-TOOLS-INDEX.md），按索引指向的路径执行」 |
| **关键变更** | 第 0.1 节铁律第 4 条；新增第 8.4.9 节（Layer 3 内部细分：原子型 vs 编排型） |
| **验证方式** | `run-lint.py` 扫描本文件 → `md_lint` 插件通过 |

### 4. 新增 py-plugins/time_source.py

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/time_source.py` |
| **变更类型** | 新建 |
| **作用** | **统一时间来源**底层插件：默认返回当前时间，支持解析外部时间字符串（ISO 8601 及常见格式），输出 `(dt_local, dt_utc)` 二元组 |
| **核心函数** | `parse_time(source=None) -> (dt_local, dt_utc)` |
| **验证方式** | `python -m py_compile` 语法通过；`run-lint.py` → `lint_python` 通过；CLI `--source "2026-06-21" --json` 输出正确 |

### 5. 重写 py-plugins/timestamp.py

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/timestamp.py` |
| **变更类型** | 重写（v1.0.0 → v1.1.0） |
| **作用** | **时间戳格式化器**：从「自己生成时间」改为「接收 time_source 输出的 datetime，只做格式化」。新增 `format_timestamp(dt_local, dt_utc)` 主入口，保留 `get_now()` 兼容方法 |
| **支持格式** | `local_short`、`local_long`、`local_iso`、`utc_short`、`utc_long`、`utc_iso`、`filename_safe` |
| **验证方式** | `python -m py_compile` 语法通过；`run-lint.py` → `lint_python` 通过；CLI `--source "2026-06-21T14:30:00" --format utc_iso` 输出 `2026-06-21T06:30:00Z` |

### 6. 更新 py-tools/get-timestamp.py

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/get-timestamp.py` |
| **变更类型** | 重写（v1.0.0 → v1.1.0） |
| **作用** | Workflow CLI：新增 `--source` 参数支持指定时间来源；通过 `py_lib` 同时加载 `timestamp` + `time_source` 插件 |
| **验证方式** | `python -m py_compile` 语法通过；`run-lint.py` → `lint_python` 通过；`--all`、`--json`、`--source` 均测试通过 |

### 7. 修改 py-sort-rules.json

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 修改 |
| **作用** | 登记 `time_source` 插件（tags: core, utility）和 `timestamp` 插件（新增 `depends: ["time_source"]`） |
| **验证方式** | `run-lint.py` → `lint_json` 通过 |

### 8. 修改 run-lint.py

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | 修改 |
| **作用** | `EXT_TO_PLUGIN` 路由表追加 `.mdc` → `md_lint`，使 `.cursor/rules/*.mdc` 文件可被统一验证 |
| **验证方式** | `python -m py_compile` 语法通过；`run-lint.py` → `lint_python` 通过 |

### 9. 修改 py-plugins/md_lint.py

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| **变更类型** | 修改 |
| **作用** | `_is_excluded_file()` 增加 `.mdc` 扩展名豁免（Cursor Rules 自有 frontmatter 规范，不强制要求 `meta` 字段） |
| **验证方式** | `python -m py_compile` 语法通过；`run-lint.py` → `lint_python` 通过；`.mdc` 文件实测通过 |

### 10. 新增 docs/patterns/atomic-vs-orchestration-workflow.md

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/patterns/atomic-vs-orchestration-workflow.md` |
| **变更类型** | 新建 |
| **作用** | 完整记录 py-tools/ Layer 3 内部两档形态（原子型 vs 编排型）的定义、差异、JSON 配置外化决策逻辑、层级关系总图 |
| **验证方式** | `run-lint.py` → `md_lint` 通过 |

### 11. 修改 TASK-TOOLS-INDEX.md

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **作用** | 新增 1.3 时间戳生成章节（含 time_source + timestamp + get-timestamp 三层架构、格式键名速查表、CLI 与插件用法） |
| **验证方式** | `run-lint.py` → `md_lint` 通过 |

### 12. 修改 verified-task-index.json

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 修改 |
| **作用** | 新增 `get-timestamp-py` 条目（task 本地 Python 版时间戳工具），保留原有 `get-timestamp`（PowerShell 版） |
| **验证方式** | `run-lint.py` → `lint_json` 通过 |


## 二、非文本操作

本次 session **无**文件系统/缓存迁移等非文本操作。全部变更为代码/文档/配置文件的修改。


## 三、环境变量速查

无新增环境变量。本次变更不涉及 `.vscode/settings.json` 或 `.env` 修改。


## 四、落盘验证

### 4.1 验证命令

使用 `run-lint.py` 对本次全部 12 个新建/修改文件执行统一混合类型验证：

```powershell
# 命令格式：run-lint.py --devroot ${devroot} --files <文件列表>
# 按扩展名自动路由：.md/.mdc → md_lint, .py → lint_python, .json → lint_json
```

### 4.2 验证结果

| 被测文件 | 路由插件 | 结果 |
|---------|---------|------|
| `high-frequency-verify-runtime.mdc` | `md_lint` | 通过 |
| `high-frequency-env-migration.mdc` | `md_lint` | 通过 |
| `task-canonical-baseline.md` | `md_lint` | 通过 |
| `time_source.py` | `lint_python` | 通过 |
| `timestamp.py` | `lint_python` | 通过 |
| `get-timestamp.py` | `lint_python` | 通过 |
| `py-sort-rules.json` | `lint_json` | 通过 |
| `run-lint.py` | `lint_python` | 通过 |
| `md_lint.py` | `lint_python` | 通过 |
| `atomic-vs-orchestration-workflow.md` | `md_lint` | 通过 |
| `TASK-TOOLS-INDEX.md` | `md_lint` | 通过 |
| `verified-task-index.json` | `lint_json` | 通过 |

**结论：全部通过，总扫描 12 个文件，总违规项 0 处。**


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | timestamp 插件体系 CLI 测试 | `get-timestamp.py --source "2026-06-21" --all` | 输出 `local_short=2026-06-21`、`utc_short=2026-06-20` 等 |
| 2 | timestamp 插件体系 py_lib 测试 | `registry.time_source.parse_time("2026-01-15T09:00:00")` | `local_iso=2026-01-15T09:00:00`、`utc_iso=2026-01-15T01:00:00Z` |
| 3 | run-lint.py 混合类型验证 | `run-lint.py --files "a.json" "b.md" "c.ps1"` | 按扩展名自动路由到对应插件，全部通过 |
| 4 | .mdc 文件验证 | `run-lint.py --files ".cursor/rules/*.mdc"` | `md_lint` 识别并豁免 `.mdc`，通过 |
| 5 | 真源检测验证路径 | 执行真源检测后调用 `run-lint.py --files verified-runtime-index.json` | `lint_json` 通过 |


## 六、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 恢复验证工具引用 | 将 `.cursor/rules/high-frequency-verify-runtime.mdc` 中验证命令改回 `schema/tool/lint-json.py` |
| 移除 timestamp 插件 | 从 `py-sort-rules.json` 中删除 `time_source` 和 `timestamp` 条目；删除 `py-plugins/time_source.py`、`py-plugins/timestamp.py`、`py-tools/get-timestamp.py` |
| 恢复 run-lint.py 路由表 | 从 `EXT_TO_PLUGIN` 中移除 `.mdc` 条目 |
| 恢复 md_lint.py 豁免 | 从 `_is_excluded_file()` 中移除 `.mdc` 判断 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-21-144609 |
| **更新人** | Human + Agent Session |
| **变更触发** | ① 真源检测后验证工具引用过期；② 缺乏标准化时间戳生成工具；③ py-tools 形态混淆导致 JSON 配置决策混乱 |
| **下次修订条件** | 新增 py-tools workflow 需按原子型/编排型分类；新增验证类型需扩展 run-lint.py 路由表 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-21-144609*  
*模板来源：schema/structure/env-migration-template.md*  
*关联 baseline：references/tasks/deploy-git-isolated/task-canonical-baseline.md 第 8.4.9 节*  
*关联 patterns：references/tasks/deploy-git-isolated/docs/patterns/atomic-vs-orchestration-workflow.md*
