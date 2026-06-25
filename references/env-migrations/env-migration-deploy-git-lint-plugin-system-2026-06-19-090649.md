---
title: deploy-git-isolated workflow-entry-plugins 三层架构 lint 体系建设
description: 以 workflow→py_lib→plugins 三层架构为核心，在 deploy-git-isolated task 下建立 lint 能力体系。workflow 只编排、entry 统一加载、plugins 实现具体检测/修复。以 workflow-lint-amend-lint.py 为案例固化"禁止越级调用"共识。
date: 2026-06-19
---

# env-migration-deploy-git-lint-plugin-system-2026-06-19-090649

| 字段 | 值 |
|------|-----|
| **Session 主题** | deploy-git-isolated workflow-entry-plugins 三层架构 lint 体系建设 |
| **日期** | 2026-06-19 |
| **文件名时间戳** | `2026-06-19-090649` |
| **触发原因** | 用户要求检查 task/ 下已集成的 lint 功能，发现缺失 JSON/PS1/Python/Encoding 检测能力；同时澄清 workflow → entry → plugin 三层架构关系（禁止越级调用） |
| **影响范围** | deploy-git-isolated 脚本体系（py-plugins/ + py-tools/ + py-sort-rules.json + task-canonical-baseline.md） |
| **风险等级** | 低（新增能力，不影响既有功能） |


## 一、文本文件变更清单

### 1. 新建 `scripts/py-plugins/lint_json.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_json.py` |
| **变更类型** | `新建` |
| **作用** | JSON 语法验证器：使用 `json.load` 验证 `.json` / `.jsonc` 文件语法 |
| **暴露接口** | `validate(dir_path: str) -> dict` |
| **标签** | `lint`, `json` |
| **验证方式** | `python -m py_compile lint_json.py` |
| **迁移方式** | 直接复制文件到目标环境对应路径 |

### 2. 新建 `scripts/py-plugins/lint_ps1.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_ps1.py` |
| **变更类型** | `新建` |
| **作用** | PowerShell 脚本语法验证器：使用 `PSParser::Tokenize` 验证 `.ps1` |
| **暴露接口** | `validate(dir_path: str) -> dict` |
| **标签** | `lint`, `ps1` |
| **验证方式** | `python -m py_compile lint_ps1.py` |
| **迁移方式** | 直接复制 |

### 3. 新建 `scripts/py-plugins/lint_python.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_python.py` |
| **变更类型** | `新建` |
| **作用** | Python 脚本语法验证器：使用 `py_compile` 验证 `.py` |
| **暴露接口** | `validate(dir_path: str) -> dict` |
| **标签** | `lint`, `python` |
| **验证方式** | `python -m py_compile lint_python.py` |
| **迁移方式** | 直接复制 |

### 4. 新建 `scripts/py-plugins/lint_encoding.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` |
| **变更类型** | `新建` |
| **作用** | 编码/BOM/行尾符检测器 + 修复能力。检测 BOM、双 BOM、CRLF/LF；支持 `--fix` 自动修复 |
| **暴露接口** | `validate(dir_path: str, fix: bool = False) -> dict` |
| **标签** | `lint`, `encoding` |
| **验证方式** | `python -m py_compile lint_encoding.py` |
| **迁移方式** | 直接复制 |

### 5. 新建 `scripts/py-tools/run-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | `新建` |
| **作用** | **Workflow：全量 lint 聚合入口**。通过 `py_lib.load_plugins(profile="lint")` 加载全部 lint 插件，统一执行、统一报告 |
| **暴露接口** | CLI：`--devroot`, `--profile`, `--tags` |
| **验证方式** | `python -m py_compile run-lint.py` |
| **迁移方式** | 直接复制 |

### 6. 新建 `scripts/py-tools/workflow-lint-amend-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-lint-amend-lint.py` |
| **变更类型** | `新建` |
| **作用** | **Workflow：lint→amend→lint 闭环**。通过 `py_lib.load_plugins(tags=["lint", "encoding"])` 获取 `lint_encoding`，完成"检测→修复→验证" |
| **关键设计** | 启动时输出 `registry.list_loaded()`，展示底层插件列表，确保可审计可追踪 |
| **验证方式** | `python -m py_compile workflow-lint-amend-lint.py` |
| **迁移方式** | 直接复制 |

### 7. 修改 `scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | `修改` |
| **新增内容** | 4 个 lint 插件定义（lint_json / lint_ps1 / lint_python / lint_encoding）+ 5 个 profile（lint / lint-json / lint-ps1 / lint-python / lint-encoding） |
| **作用** | py_lib 加载真源，决定插件拓扑排序和 profile 筛选 |
| **验证方式** | `python -c "import json; json.load(open(...))"` |
| **迁移方式** | 直接覆盖 |

### 8. 修改 `task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | `修改` |
| **新增内容** | 第 8.4 节「Python 插件体系三层架构（ workflow → entry → plugins ）」 |
| **作用** | 固化本次 session 核心共识：workflow 禁止直接 import plugin，必须通过 py_lib 统一入口；以 workflow-lint-amend-lint.py 为案例讲解 |
| **迁移方式** | 直接覆盖 |

### 9. 修改 `scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `修改` |
| **新增内容** | Stage S6 Lint 检查章节（含架构层级说明、全量 lint、按需 lint、workflow 示例、新增 workflow 模板） |
| **迁移方式** | 直接覆盖 |

### 10. 修改 `TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `修改` |
| **新增内容** | 1.4 Lint 插件体系章节、lint + fix 典型工作流、速查命令 |
| **迁移方式** | 直接覆盖 |

### 11. 修改 `README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | `修改` |
| **新增内容** | 文件导航表新增 run-lint.py / workflow-lint-amend-lint.py / lint_*.py；当前状态表新增 Lint 插件体系；新增「Python 插件体系架构（三层）」章节 |
| **迁移方式** | 直接覆盖 |

### 12. 修改历史 `.md` 文件（CRLF → LF）

| 属性 | 值 |
|------|-----|
| **路径** | task 目录下 18 个 `.md` 文件 |
| **变更类型** | `修改` |
| **作用** | 将 CRLF 换行符批量替换为 LF，符合 AGENTS.md `.md` 文件必须使用 LF 的规定 |
| **操作方式** | `lint_encoding.py --fix` 自动修复 |
| **迁移方式** | 无需手动操作，lint 工具自动处理 |


## 二、非文本操作

本次 session 无文件复制、缓存迁移、目录创建等非文本操作。


## 三、环境变量速查

无需新增环境变量。所有工具通过 `py_lib` 内部推导 devroot。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 结果 |
|---------|---------|---------|------|
| `.py`（全部 6 个新建） | `python -m py_compile` | 语法正确性 | ✅ 全部通过 |
| `.json`（py-sort-rules.json） | `json.load` | JSON 语法 | ✅ 通过 |
| `.md`（task 目录 21 个） | `lint_encoding.py` | BOM、CRLF | ✅ 0 违规 |

执行命令：
```powershell
# 全量 lint 验证
D:\pjt\cursor\cs_py\venv\py\python.exe `
  D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py `
  --devroot "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated" --profile lint
```

结果：139 个文件扫描，0 违规。


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | py_lib 加载全部 lint 插件 | `python run-lint.py --devroot <devroot> --profile lint` | 加载 4 个 lint 插件，扫描完成 |
| 2 | lint_encoding 检测能力 | `python lint_encoding.py --dir <devroot>` | 扫描文本文件，报告 BOM/CRLF 违规 |
| 3 | lint_encoding 修复能力 | `python lint_encoding.py --dir <devroot> --fix` | 修复违规，回读验证 |
| 4 | workflow 闭环 | `python workflow-lint-amend-lint.py --devroot <devroot> --dir <subdir>` | 检测→修复→验证三步完成 |
| 5 | py_sort-rules.json 有效 | `python -c "import json; json.load(open('py-sort-rules.json'))"` | 无异常 |


## 六、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 移除 lint 插件 | 删除 `scripts/py-plugins/lint_*.py` |
| 恢复 py-sort-rules.json | 从 Git 历史恢复变更前的版本 |
| 移除 workflow 入口 | 删除 `scripts/py-tools/run-lint.py` 和 `workflow-lint-amend-lint.py` |
| 恢复 baseline | 从 Git 历史恢复 `task-canonical-baseline.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-19-090649 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求检查 task/ lint 功能并建设完整体系 |
| **下次修订条件** | 新增 lint 插件类型（如 lint_yaml）、workflow 扩展、py_lib 架构升级 |
| **跨环境迁移参考** | 直接复制 `scripts/py-plugins/` + `scripts/py-tools/` + `scripts/py-sort-rules.json` + 修订联动文档 |


*文档生成时间：2026-06-19*  
*模板版本：v2*