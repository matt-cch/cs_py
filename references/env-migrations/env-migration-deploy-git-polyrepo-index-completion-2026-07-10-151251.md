---
title: deploy-git-isolated polyrepo 脚本索引补全与 staged 回滚能力建设
description: 补全 deploy-git-isolated task 中 polyrepo 脚本体系的索引登记，修复 poly.py 语法错误，消除 Step 4.5 越级调用，新增 staged 回滚原子能力。
date: 2026-07-10
meta: {}
---

# env-migration-deploy-git-polyrepo-index-completion-2026-07-10-151251

> **文档性质**：环境迁移指南。聚焦 deploy-git-isolated task 的 polyrepo 脚本体系索引登记、代码修复与规范基线补全。  
> **受众**：Human + Agent。在新环境解压项目后，Agent 可直接阅读此文档并执行复现步骤。


## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | deploy-git-isolated polyrepo 脚本索引补全与 staged 回滚能力建设 |
| **日期** | 2026-07-10（frontmatter；文件名时间戳见上表） |
| **文件名时间戳** | `2026-07-10-151251`（与磁盘文件名后缀一致） |
| **触发原因** | 上一版 env-migration（2026-07-09）声称 poly.py 已消除越级调用，但实际 Step 4.5 仍存在内嵌 `import py_lib` + `registry.git_security.scan_git_security()` 的越级调用；poly.py 第230-238行存在重复 `except Exception` 块的语法错误；polyrepo 脚本体系未进入 ENTRY.json active_scripts / scenarios 及 TASK-TOOLS-INDEX.md 工具表 |
| **影响范围** | deploy-git-isolated task 的脚本源码、规范基线、索引文档、版本记录 |
| **风险等级** | 低（仅索引登记和脚本修复，不涉及业务代码或环境变量变更） |


## 一、文本文件变更清单

### 1. 修复 `workflow-git-deploy-full-poly.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | ① 删除第230-238行重复 `except Exception` 块（Python 语法错误）；② Step 4.5 删除内嵌 `import py_lib` + `registry.git_security.scan_git_security()`，改为 subprocess 调用 `atomic-check-staged-after-add.py --devroot --target --git-exe` |
| **插入位置** | 第230-238行修复重复 except；Step 4.5 逻辑重构 |
| **作用** | 消除语法错误 + 消除越级调用，使 poly.py 符合「Layer 3 Workflow 禁止直接 import plugin」的架构约束 |
| **验证方式** | `run-lint.py --files workflow-git-deploy-full-poly.py` 通过（lint_python + lint_encoding） |
| **迁移方式** | 直接覆盖即可（无环境依赖） |

### 2. 扩展 `atomic-check-staged-after-add.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-check-staged-after-add.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 `--target` / `--git-exe` CLI 参数，支持 polyrepo 调用契约 |
| **作用** | 使 staged 扫描原子可被 poly workflow 通过 subprocess 调用，传入目标仓库和 git 可执行文件路径 |
| **验证方式** | `run-lint.py --files atomic-check-staged-after-add.py` 通过 |
| **迁移方式** | 直接覆盖 |

### 3. 新建 `git_reset.py`（Layer 1 插件）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_reset.py` |
| **变更类型** | `新建` |
| **新增/修改内容** | 三层封装 staged 回滚：`reset_staged()` 锁定 `reset HEAD`（无 `--hard`），操作前审计（list staged 文件）+ 操作后验证（确认 unstaged），返回结构化结果字典 |
| **作用** | 提供安全的 staged 回滚底座能力，禁止裸 `git reset` 调用 |
| **验证方式** | `run-lint.py --files git_reset.py` 通过 |
| **迁移方式** | 新建文件，需在 `py-sort-rules.json` 中登记（见下条） |

### 4. 新建 `atomic-git-reset-staged.py`（Layer 3 CLI）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-reset-staged.py` |
| **变更类型** | `新建` |
| **新增/修改内容** | CLI 入口：解析 `--devroot/--target/--git-exe`，调用 `py_lib.load_plugins()` 获取 `git_reset` 插件，执行回滚并输出人类可读结果 |
| **作用** | 原子 CLI，供外部调用 staged 回滚（README 场景 H 首选工具） |
| **验证方式** | `run-lint.py --files atomic-git-reset-staged.py` 通过；实测 4 文件成功 unstage |
| **迁移方式** | 新建文件 |

### 5. 登记 `git_reset` 到 `py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | 在 plugins 数组追加 `git_reset` 条目（tags: `["git","core"]`，deps: `[]`） |
| **作用** | 使 py_lib 拓扑排序能发现 git_reset 插件 |
| **迁移方式** | 直接追加 |

### 6. 更新 `baseline-principles.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-principles.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 §0.8.5「裸 git reset 禁令」：任何 staged 回滚必须经过 `atomic-git-reset-staged.py`（或更高层封装），禁止直接调用 `git reset HEAD` 及其任何变体 |
| **作用** | 规范基线层面固化 staged 回滚的强制路径 |
| **迁移方式** | 直接追加 |

### 7. 更新 `baseline-workflow-deploy.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-workflow-deploy.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | §8.7.4 新增第 5 条（Step 4.5 禁止内嵌 import plugin）和第 6 条（polyrepo 调用契约中 `--target` 强制必填） |
| **作用** | 部署流程契约层面消除越级调用 |
| **迁移方式** | 直接追加 |

### 8. 更新 `README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | ① 版本记录表追加 v0.21.1 和 v0.22.0；② Task 结构概览树形图追加 git_reset.py / atomic-git-reset-staged.py；③ Agent 快速决策表新增场景 H（staged 回滚）；④ 新增「场景 I: Polyrepo 部署」完整执行章节 |
| **作用** | 场景化决策入口补全 polyrepo 和 staged 回滚路径 |
| **迁移方式** | 直接覆盖 |

### 9. 更新 `TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | ① 1.9 节编排 Workflow 表格追加 `workflow-git-deploy-full-poly.py`、`atomic-polyrepo-context-manifest.py`、`generate-ai-summary.py`；② 边界矩阵追加 staged 回滚首选 `atomic-git-reset-staged.py`；③ 速查命令追加 staged 回滚示例；④ 关联导航追加 5 个新条目 |
| **作用** | 工具索引真源补全 polyrepo 体系 |
| **迁移方式** | 直接覆盖 |

### 10. 更新 `ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | ① `active_scripts` 追加 3 个条目（poly.py / manifest / generate-ai-summary）；② `scenarios` 追加 `polyrepo-deploy` 场景；③ `version_history` 追加 v0.21.1 和 v0.22.0；④ `meta.version` 更新为 0.22.0，`last_updated` 更新为 2026-07-10T14:30:00 |
| **作用** | 机器真源索引与版本历史同步 |
| **迁移方式** | 直接覆盖 |

### 11. 更新 `EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 Stage S5.4「Polyrepo 部署（Python Workflow）」，含单仓库 / polyrepo / 指定 message / Step 0 审计 / Step 4 等调用示例 |
| **作用** | 执行速查真源补全 poly.py 命令 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session **不涉及**文件复制、缓存迁移、目录创建等非文本操作。所有变更均为文本文件修改/新建，可被 git 追踪。


## 三、环境变量速查

本次 session **未修改**任何环境变量、`.vscode/settings.json`、`.env` 或终端配置。无需核对外部环境变量。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py`（lint_encoding + md_lint） | BOM、双 BOM、CRLF、LF、frontmatter | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, frontmatter 完整 |
| `.json`（ENTRY.json） | `run-lint.py`（lint_json + lint_encoding） | JSON 语法、编码、换行符 | JSON 解析通过、BOM=no、CRLF=0 |

**执行示例**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-deploy-git-polyrepo-index-completion-2026-07-10-151251.md"
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 poly.py 语法正确 | `run-lint.py --files workflow-git-deploy-full-poly.py` | lint_python 通过，无语法错误 |
| 2 | 确认 staged 回滚可用 | `"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-reset-staged.py" --devroot "${devroot}" --target "${devroot}" --git-exe "${devroot}\venv\git\cmd\git.exe"` | 输出 staged 文件列表 → reset HEAD → 验证 unstaged |
| 3 | 确认索引已登记 | 读取 `ENTRY.json` 的 `active_scripts` 和 `scenarios` | 包含 workflow-git-deploy-full-poly / atomic-polyrepo-context-manifest / generate-ai-summary / polyrepo-deploy |
| 4 | 确认规范基线已更新 | 读取 `baseline-principles.md` §0.8.5 | 存在「裸 git reset 禁令」条款 |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 撤销脚本修改 | `git checkout -- references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` 等 |
| 撤销索引登记 | `git checkout -- references/tasks/deploy-git-isolated/ENTRY.json` 等 |
| 删除新建文件 | `git rm references/tasks/deploy-git-isolated/scripts/py-plugins/git_reset.py` 等（如需完全回滚） |
| 恢复规范基线 | `git checkout -- references/tasks/deploy-git-isolated/baseline/baseline-principles.md` 等 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-10-151251 |
| **更新人** | Human + Agent Session |
| **变更触发** | polyrepo 脚本体系索引缺漏 + poly.py 语法错误 + Step 4.5 越级调用未消除 |
| **下次修订条件** | 新增 polyrepo 脚本或变更 poly.py 架构时同步更新本 env-migration |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
