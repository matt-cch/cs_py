---
title: env-migration — deploy-git-isolated lint 插件体系建设与自说明验证
description: 记录 deploy-git-isolated task 下 Python lint 插件体系建设 session 的全部环境级变更，含 4 个 lint 底座插件、2 个 workflow、py_lib 入口层扩展、文档体系更新与 frontmatter 缺陷修复。
date: 2026-06-19
---

# env-migration — deploy-git-isolated lint 插件体系建设与自说明验证

> **文档性质**：环境迁移指南。记录单次 session 对 deploy-git-isolated task 目录产生的全部新增与修改。  
> **受众**：Human + Agent。在新环境复现时，可按本文档逐项核对文件状态。  
> **关联研究**：`references/tasks/deploy-git-isolated/docs/research/workflow-entry-plugins-architecture-research.md`、`task-agent-self-explanation-validation.md`


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | deploy-git-isolated task 下 Python lint 插件体系建设与自说明验证 |
| **日期** | 2026-06-19 |
| **文件名时间戳** | `2026-06-19-105144` |
| **触发原因** | 在 deploy-git-isolated task 下建设覆盖 JSON/PS1/Python/Encoding 四种检测能力的 lint 插件体系，固化 workflow-entry-plugins 三层架构共识，并验证 task 文档的自说明能力 |
| **影响范围** | deploy-git-isolated task 目录（`references/tasks/deploy-git-isolated/`）下的 scripts/、docs/、根级文档 |
| **风险等级** | 低（纯新增工具/文档，不影响既有业务逻辑） |


## 一、文本文件变更清单

### 新建文件

#### 1. `scripts/py-plugins/lint_json.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_json.py` |
| **变更类型** | 新建 |
| **作用** | JSON 语法检测插件，支持 `--fix` 自动修复 |
| **验证方式** | `python lint_json.py --fix <json-file>`，应输出 `[OK]` 或修复后重写文件 |
| **迁移方式** | 直接复制 |

#### 2. `scripts/py-plugins/lint_ps1.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_ps1.py` |
| **变更类型** | 新建 |
| **作用** | PowerShell 脚本编码/BOM/语法检测插件，支持 `--fix` 自动修复 |
| **验证方式** | `python lint_ps1.py --fix <ps1-file>`，应输出 `[OK]` 或修复后重写文件 |
| **迁移方式** | 直接复制 |

#### 3. `scripts/py-plugins/lint_python.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_python.py` |
| **变更类型** | 新建 |
| **作用** | Python 语法检测插件，支持 `--fix` 自动修复 |
| **验证方式** | `python lint_python.py --fix <py-file>`，应输出 `[OK]` 或修复后重写文件 |
| **迁移方式** | 直接复制 |

#### 4. `scripts/py-plugins/lint_encoding.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` |
| **变更类型** | 新建 |
| **作用** | 文件编码/BOM/CRLF 检测插件，支持 `--fix` 自动修复 |
| **验证方式** | `python lint_encoding.py --fix <file>`，应输出 `[OK]` 或修复后重写文件 |
| **迁移方式** | 直接复制 |

#### 5. `scripts/py-tools/run-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | 新建 |
| **作用** | 全量 lint 聚合入口（Workflow 层），通过 `py_lib.load_plugins()` 加载所有插件并执行 |
| **验证方式** | `python run-lint.py`，应输出所有文件的 lint 结果 |
| **迁移方式** | 直接复制 |

#### 6. `scripts/py-tools/workflow-lint-amend-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-lint-amend-lint.py` |
| **变更类型** | 新建 |
| **作用** | lint → amend → lint 闭环 workflow，确保修复后再次验证 |
| **验证方式** | `python workflow-lint-amend-lint.py`，应执行完整闭环并输出报告 |
| **迁移方式** | 直接复制 |

#### 7. `docs/research/workflow-entry-plugins-architecture-research.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/research/workflow-entry-plugins-architecture-research.md` |
| **变更类型** | 新建 |
| **作用** | 记录 workflow → entry → plugins 三层架构选型演进与反例分析 |
| **验证方式** | `read` 确认文件存在且 frontmatter 完整 |
| **迁移方式** | 直接复制 |

#### 8. `docs/research/task-agent-self-explanation-validation.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/research/task-agent-self-explanation-validation.md` |
| **变更类型** | 新建 |
| **作用** | Task Agent 自说明能力验证实验报告，含知行 gap 分析与改进建议 |
| **验证方式** | `read` 确认文件存在且 frontmatter 完整 |
| **迁移方式** | 直接复制 |

### 修改文件

#### 9. `scripts/py_lib.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py_lib.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 增加 `load_plugins()` 统一入口、Profile 筛选、拓扑排序、依赖自动补齐 |
| **作用** | 作为 Python 侧的统一入口层，明令禁止越级调用 |
| **验证方式** | `python -c "import py_lib; py_lib.load_plugins()"`，应正常加载 |
| **迁移方式** | 需与 `py-sort-rules.json` 同步更新 |

#### 10. `scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | 增加 `lint_json`、`lint_ps1`、`lint_python`、`lint_encoding` 4 个插件定义，以及 5 个 profile |
| **作用** | 插件拓扑排序与 profile 筛选的真源 |
| **验证方式** | `python -m json.tool py-sort-rules.json`，应无解析错误 |
| **迁移方式** | 直接覆盖 |

#### 11. `scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 更新插件列表和 workflow 路径 |
| **作用** | 执行速查手册 |
| **验证方式** | `read` 确认内容完整 |
| **迁移方式** | 直接覆盖 |

#### 12. `scripts/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 更新工具索引，登记新增插件和 workflow |
| **作用** | 工具能力地图 |
| **验证方式** | `read` 确认内容完整 |
| **迁移方式** | 直接覆盖 |

#### 13. `README.md`（task 根级）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 更新任务概览，补充 lint 体系说明 |
| **作用** | 任务速查入口 |
| **验证方式** | `read` 确认内容完整 |
| **迁移方式** | 直接覆盖 |

#### 14. `task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 增加第 8.4 节「三层架构铁律」，固化「禁止越级调用」约定 |
| **作用** | 规范基线 |
| **验证方式** | `read` 确认第 8.4 节存在 |
| **迁移方式** | 直接覆盖 |

### 修复文件（frontmatter 缺陷）

以下 5 个文件的 `date` 字段被错误拼接到 `description` 行末尾，已修复为独立行：

| # | 文件 | 修复内容 |
|---|------|---------|
| 15 | `docs/harness/delivery-checklist.md` | `date: 2026-06-17` 独立成行 |
| 16 | `docs/patterns/profile-filter-pattern.md` | `date: 2026-06-17` 独立成行 |
| 17 | `docs/README.md` | `date: 2026-06-18` 独立成行 |
| 18 | `docs/research/scripts-directory-taxonomy-research.md` | `date: 2026-06-18` 独立成行 |
| 19 | `docs/research/task-dependency-graph.md` | `date: 2026-06-18` 独立成行 |


## 二、非文本操作

本次 session **不涉及**文件复制、缓存迁移、目录创建等非文本操作。所有变更均为代码/文档文件的增删改。


## 三、环境变量速查

本次 session **未新增或修改**环境变量。所有工具链调用均使用绝对路径，无需额外环境变量。


## 四、落盘验证

### 4.1 Markdown 文件编码检查

```powershell
# 示例：检查本文档
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" -Path "${devroot}\references\env-migrations\env-migration-deploy-git-lint-plugins-2026-06-19-105144.md"
```

**预期结果**：BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0

### 4.2 lint 脚本验证

```powershell
# 验证 task 目录下所有 md 文件 frontmatter 格式
"${devroot}\venv\py\python.exe" "${devroot}\venv\tmp\task-md-lint-test.py"
```

**预期结果**：`总计: 22 个文件 | 通过: 22 | 失败: 0`

### 4.3 py_lib 插件加载验证

```powershell
# 验证 py_lib 能正常加载所有插件
"${devroot}\venv\py\python.exe" -c "
import sys
sys.path.insert(0, r'${devroot}\references\tasks\deploy-git-isolated\scripts')
import py_lib
plugins = py_lib.load_plugins()
print(f'Loaded plugins: {list(plugins.keys())}')
"
```

**预期结果**：`Loaded plugins: ['lint_json', 'lint_ps1', 'lint_python', 'lint_encoding', ...]`


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 4 个 lint 插件存在 | `Get-ChildItem "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\lint_*.py"` | 返回 4 个文件 |
| 2 | 确认 2 个 workflow 存在 | `Get-ChildItem "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\*.py"` | 返回 `run-lint.py`、`workflow-lint-amend-lint.py` |
| 3 | 确认 py_lib 可加载 | `"${devroot}\venv\py\python.exe" -c "import sys; sys.path.insert(0, r'${devroot}\references\tasks\deploy-git-isolated\scripts'); import py_lib; print(py_lib.load_plugins().keys())"` | 输出插件键列表 |
| 4 | 确认 task md lint 通过 | `"${devroot}\venv\py\python.exe" "${devroot}\venv\tmp\task-md-lint-test.py"` | `22/22 通过` |
| 5 | 确认研究文档存在 | `Test-Path "${devroot}\references\tasks\deploy-git-isolated\docs\research\workflow-entry-plugins-architecture-research.md"` | `True` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增插件 | `Remove-Item "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\lint_*.py"` |
| 删除新增 workflow | `Remove-Item "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py"`、`workflow-lint-amend-lint.py` |
| 恢复 py_lib.py | 从 git 历史或备份恢复变更前版本 |
| 恢复 py-sort-rules.json | 从 git 历史或备份恢复变更前版本 |
| 删除研究文档 | `Remove-Item "${devroot}\references\tasks\deploy-git-isolated\docs\research\workflow-entry-plugins-architecture-research.md"`、`task-agent-self-explanation-validation.md` |
| 恢复 frontmatter 修复 | 手动将 5 个文件的 `date` 重新拼接到 `description` 行末尾（不推荐） |

> ⚠️ **注意**：回滚前请确认没有后续 session 依赖本次新增的文件。


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-19-105144 |
| **更新人** | Agent Session（主 Agent + task 子进程） |
| **变更触发** | deploy-git-isolated task lint 插件体系建设需求 |
| **下次修订条件** | 新增 lint 插件、修改 py_lib 接口、变更 workflow 逻辑 |
| **跨环境迁移参考** | 直接复制 deploy-git-isolated task 目录下所有变更文件 |


*文档生成时间：2026-06-19*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
