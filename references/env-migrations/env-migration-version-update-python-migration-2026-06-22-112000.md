---
title: 版本记录更新 Python 化迁移
description: 新增 py-plugins/runtime_version.py 版本检测插件和 py-tools/update-version.py Workflow CLI，替代 5 个独立 get-*-version.ps1 脚本，并修订联动 ENTRY.json / README.md / TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md。
date: 2026-06-22
meta: {}
---

# env-migration-version-update-python-migration-2026-06-22-112000

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 版本记录更新 Python 化迁移（新增 runtime_version 插件 + update-version Workflow） |
| **日期** | 2026-06-22 |
| **文件名时间戳** | `2026-06-22-112000` |
| **触发原因** | high-frequency-update-version.mdc 仍依赖 5 个独立 PowerShell 脚本（get-*-version.ps1），需要 Python 化统一入口 |
| **影响范围** | py-plugins/（新增 runtime_version.py）、py-tools/（新增 update-version.py）、4 个 task 文档修订联动 |
| **风险等级** | 低（新增文件，不修改现有 PS 脚本，保留 fallback） |


## 一、文本文件变更清单

### 1. 新建 `py-plugins/runtime_version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py` |
| **变更类型** | 新建 |
| **新增内容** | 通用版本检测插件，5 种检测模式：subprocess-version / file-version（ctypes 优先）/ cursor-special / package-import / python-self |
| **插入位置** | 新文件 |
| **作用** | 为 update-version.py 提供版本检测能力，供 py_lib 插件体系加载 |
| **验证方式** | `python runtime_version.py` 模块自测试通过 |
| **迁移方式** | 直接复制文件 |

### 2. 新建 `py-tools/update-version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py` |
| **变更类型** | 新建 |
| **新增内容** | Workflow CLI：自动发现 venv/version/*.md → 读取记录版本 → 调用 runtime_version.detect() 实测 → 对比 → 更新 .md + 追加 history |
| **插入位置** | 新文件 |
| **作用** | 统一版本记录更新入口，替代 5 个独立 get-*-version.ps1 |
| **验证方式** | `python update-version.py --dry-run` 全量检测通过 |
| **迁移方式** | 直接复制文件 |

### 3. 修改 `ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | version 0.15.0 → 0.16.0；version_history 追加 v0.16.0 条目；active_scripts 新增 update-version.py 条目；last_updated 刷新 |
| **插入位置** | meta.version、meta.version_history[]、active_scripts[] |
| **作用** | 机器真源登记新增 Workflow |
| **验证方式** | lint_json 通过 |
| **迁移方式** | 按 diff 修改 |

### 4. 修改 `README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 文件导航表新增 update-version.py 行；当前状态表新增「版本记录更新 ✅」 |
| **插入位置** | 文件导航表格、当前状态表格 |
| **作用** | Agent 快速决策时可见新工具 |
| **验证方式** | md_lint 通过 |
| **迁移方式** | 按 diff 修改 |

### 5. 修改 `TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增 1.3 版本记录更新节（含表格、CLI 用法）；边界矩阵新增「版本记录更新」行；关联文件导航表新增 update-version.py |
| **插入位置** | 1.3 节（时间戳生成之前）、边界矩阵、关联文件导航 |
| **作用** | 工具索引暴露对外入口 |
| **验证方式** | md_lint 通过 |
| **迁移方式** | 按 diff 修改 |

### 6. 修改 `EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增 Stage S5.5 版本记录更新节（全量更新、指定工具、dry-run 三种命令） |
| **插入位置** | Stage S5 和 Stage S6 之间 |
| **作用** | 执行速查提供可复制命令 |
| **验证方式** | md_lint 通过 |
| **迁移方式** | 按 diff 修改 |

### 7. 修改 `high-frequency-update-version.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-update-version.mdc` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增顶部绝对路径替换提示；实测命令从 PS 改为 Python CLI；保留 PS fallback 说明 |
| **插入位置** | 全文重写 |
| **作用** | 高频任务 mdc 指向新的 Python 入口 |
| **验证方式** | md_lint 通过 |
| **迁移方式** | 全文替换 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 不涉及文件复制、缓存迁移等无法被 git 追踪的操作。


## 三、环境变量速查

无新增环境变量。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py --profile lint-md` | frontmatter、description/date 拼接 | 通过 |
| `.json`（ENTRY.json） | `run-lint.py --profile lint-json` | JSON 语法 | 通过 |

**执行示例**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-version-update-python-migration-2026-06-22-112000.md"
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 runtime_version.py 语法正确 | `python -m py_compile runtime_version.py` | 无错误 |
| 2 | 确认 update-version.py 语法正确 | `python -m py_compile update-version.py` | 无错误 |
| 3 | 确认 dry-run 模式全量检测通过 | `python update-version.py --devroot "${devroot}" --dry-run` | 5 个工具全部检测到，无 ERROR |
| 4 | 确认 lint 通过 | `run-lint.py` 验证新增/修改文件 | 全部通过 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增文件 | `Remove-Item "references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py"`；`Remove-Item "references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py"` |
| 恢复 mdc | 从 git 恢复 `.cursor/rules/high-frequency-update-version.mdc` 到修改前版本 |
| 恢复 task 文档 | 从 git 恢复 `ENTRY.json`、`README.md`、`TASK-TOOLS-INDEX.md`、`EXEC-CHEATSHEET.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-22-112000 |
| **更新人** | Human + Agent Session |
| **变更触发** | high-frequency-update-version.mdc 仍使用 PS 脚本，需 Python 化统一入口 |
| **下次修订条件** | 新增检测模式、新增工具到 venv/version/、py-plugins 接口变更 |
| **跨环境迁移参考** | 直接复制 runtime_version.py + update-version.py + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-22*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
