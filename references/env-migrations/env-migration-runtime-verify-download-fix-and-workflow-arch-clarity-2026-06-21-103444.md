---
title: runtime 检测下载修复 + workflow 架构明晰
description: verify-runtime candidate_paths 兜底修复、download-runtime-tool 切 py 版、workflow 三层+配置契约架构固化、archive_project.py 迁入 py-lib 模式
date: 2026-06-21
---

# env-migration-runtime-verify-download-fix-and-workflow-arch-clarity-2026-06-21-103444

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | runtime 检测下载修复 + workflow 架构明晰 |
| **日期** | 2026-06-21 |
| **文件名时间戳** | `2026-06-21-103444` |
| **触发原因** | 1) cursor 检测失败但 candidate_paths 实际命中，发现 verify-runtime 逻辑缺陷；2) download-runtime-tool 误用 ps1 版本而非已存在的 py 版；3) workflow 架构认知模糊（三层 vs 四层 vs 配置契约） |
| **影响范围** | `references/runtime/*.py`、`references/tasks/deploy-git-isolated/scripts/py-tools/`、`references/tasks/deploy-git-isolated/scripts/py-plugins/`、`.cursor/rules/*.mdc`、`references/runtime/verified-task-index.json` |
| **风险等级** | 中（修改核心 runtime 检测/下载脚本，涉及索引真源） |


## 一、文本文件变更清单

### 1. 修改 `references/runtime/verify-runtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime.py` |
| **变更类型** | 追加 |
| **新增内容** | `load_candidate_paths_from_index()` 函数；主循环中 exe_exists=False 时加载 candidate_paths 重新检测 |
| **作用** | 主路径 + fallback_paths 全 miss 后，从 `verified-runtime-index.json` 读取 candidate_paths 兜底扫描 |
| **验证方式** | 执行 verify-runtime.py，cursor 应从"失败"变为"candidate 命中: D:\tools\cursor\" |
| **迁移方式** | 可直接覆盖 |

### 2. 修改 `references/runtime/runtime_modules/local_verifier.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/local_verifier.py` |
| **变更类型** | 修改 |
| **修改内容** | `resolve_path()` 新增 `os.path.expandvars()`；`check()` 新增 `candidate_paths` 参数；`_get_cursor_version()` 优先尝试 `cursor.cmd --version` |
| **作用** | 支持 `%LOCALAPPDATA%` 展开；支持索引 candidate_paths 兜底；cursor 版本检测优先无 GUI 副作用的 cmd |
| **验证方式** | `python -m py_compile local_verifier.py` 通过 |
| **迁移方式** | 可直接覆盖 |

### 3. 修改 `references/runtime/download-runtime-tool.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-runtime-tool.py` |
| **变更类型** | 修改 |
| **修改内容** | 进程检测从"检测摘要后"后移到"用户确认 Y 后"；Step 4 增加 `[DECISION] 版本不一致，需要下载更新` 明确输出；新增 `load_candidate_paths_from_index()` 和 candidate_paths 兜底逻辑 |
| **作用** | 默认 `"N" |` 模式不再执行无意义的 Get-Process 扫描；版本对比决策可视化；cursor 本地检测支持 candidate fallback |
| **验证方式** | 执行 `"N" | python download-runtime-tool.py --tool-name opencode_cli ...`，确认无 `[WARN] 检测到该工具正在运行` |
| **迁移方式** | 可直接覆盖 |

### 4. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 修改 |
| **修改内容** | `download-runtime-tool` 的 `path` 和 `entry_command` 从 `.ps1` 切到 `.py`；新增 `download-runtime-tool-legacy` 保留 ps1 作为 fallback |
| **作用** | 索引真源与磁盘实际对齐（py 版本是当前推荐，ps1 是 legacy） |
| **验证方式** | `python -c "import json; json.load(open('...'))"` 通过 |
| **迁移方式** | 可直接覆盖 |

### 5. 修改 `.cursor/rules/high-frequency-download-runtime.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-download-runtime.mdc` |
| **变更类型** | 修改 |
| **修改内容** | 全部标准命令从 `powershell.exe -File download-runtime-tool.ps1` 切到 `python.exe download-runtime-tool.py`；入口脚本、能力说明、禁止行为清单同步更新 |
| **作用** | 高频任务 mdc 与磁盘实际对齐，Agent 触发时走 py 版本 |
| **验证方式** | 读取 mdc 确认所有命令示例含 `download-runtime-tool.py` 而非 `.ps1` |
| **迁移方式** | 可直接覆盖 |

### 6. 新建/修改 `references/tasks/deploy-git-isolated/scripts/py-tools/archive_project.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive_project.py` |
| **变更类型** | 重写（v1.1.2 → v2.0.0） |
| **修改内容** | 移除直接 `import archive_config/archive_scanner/archive_compressor`；改为 `from py_lib import load_plugins` → `registry = load_plugins(profile="archive")` |
| **作用** | 从越级调用改造为合规 py-lib 入口模式；archive_cs_py.py / archive_venv.py 保持不变（快捷入口） |
| **验证方式** | `python -m py_compile archive_project.py` 通过 |
| **迁移方式** | 可直接覆盖 |

### 7. 修改 `references/tasks/deploy-git-isolated/task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | 修改（8.4 节 + 2. 目录结构 + 外部工具引用） |
| **修改内容** | 8.4 节从"三层"改为"三层 + 配置契约"；Config 不是独立层而是 Entry 和 Plugins 的输入契约；EXEC-CHEATSHEET 纳入 Layer 3；目录结构按四层标注；download-runtime 引用从 ps1 切到 py |
| **作用** | 固化 workflow → entry → plugins 架构认知；明确 Config 契约的定位 |
| **验证方式** | 读取 8.4 节确认含"Config 契约"、"EXEC-CHEATSHEET 是 Layer 3 组成部件" |
| **迁移方式** | 可直接覆盖 |

### 8. 修改 `references/tasks/deploy-git-isolated/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | 修改（架构图 + 导航表 + 状态表） |
| **修改内容** | Python 插件体系架构图从三层改为三层+配置契约；文件导航表新增 archive_project.py / archive_cs_py.py / archive_venv.py 及 archive plugins；当前状态表新增 Archive 插件体系 |
| **作用** | 人类/Agent 入口与最新架构对齐 |
| **迁移方式** | 可直接覆盖 |

### 9. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **修改内容** | 1.6 节新增"归档 Workflow"（archive_project.py / archive_cs_py.py / archive_venv.py）；边界矩阵新增 archive 条目；速查命令新增 archive 示例；外部工具引用 download-runtime-tool 从 ps1 切到 py |
| **作用** | 工具索引与新增 workflow 对齐；与 runtime py 版本对齐 |
| **迁移方式** | 可直接覆盖 |


## 二、非文本操作

无（本次全部为代码/文档修改，无文件复制、缓存迁移、目录创建）。


## 三、环境变量速查

无新增环境变量。本次变更不涉及 `.vscode/settings.json` 或 `.env` 修改。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py`（修改的脚本） | `python -m py_compile` | 语法正确性 | 无 SyntaxError |
| `.json`（索引） | `lint-json.py` | JSON 语法正确性 | `[OK]` 无解析错误 |
| `.md`（本文档） | `check-file-encoding.ps1` | BOM、CRLF、LF | BOM=no, CRLF=0, LF>0 |


## 五、验证清单（新环境/新 session 必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | verify-runtime candidate_paths 兜底 | `python verify-runtime.py` | cursor 显示 "candidate 命中" 而非 "失败" |
| 2 | download-runtime-tool 默认不扫描进程 | `"N" | python download-runtime-tool.py --tool-name opencode_cli ...` | 无 "检测到该工具正在运行" 输出 |
| 3 | archive_project 合规加载 | `python archive_project.py --group cs_py --stage scan` | py_lib 已加载插件列表含 archive_config / archive_scanner |
| 4 | 索引 JSON 有效 | `python -c "import json; json.load(open('verified-task-index.json'))"` | 无异常 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| verify-runtime.py 回滚 | 从 git 历史恢复 `verify-runtime.py` 和 `local_verifier.py` 的旧版本 |
| download-runtime-tool.py 回滚 | 恢复旧版本；将 `verified-task-index.json` 中 download-runtime-tool 改回 ps1 路径 |
| archive_project.py 回滚 | 恢复 v1.1.2 版本（直接 import plugin 模式） |
| baseline/README/TOOLS-INDEX 回滚 | 恢复旧版本 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-21-103444 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指出 cursor 检测逻辑缺陷、download 误用 ps1、workflow 架构认知模糊 |
| **下次修订条件** | 新增 workflow 未走 py-lib 入口；runtime 脚本新增功能未同步索引；Config 契约新增字段 |
| **跨环境迁移参考** | 直接覆盖文件 + 按「验证清单」逐条执行 |
