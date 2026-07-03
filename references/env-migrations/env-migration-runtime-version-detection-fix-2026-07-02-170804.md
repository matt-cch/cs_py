---
title: 运行时检测工具链修复（query_param 映射 + package-import 版本检测）
description: 修复真源检测中 opencode_cli/gh_cli 上游查询失败、llama_cpp_python 本地版本检测失败的问题，涉及 tools_config.json、runtime_version.py、atomic-detect-local.py 三处修改。
date: 2026-07-02
meta:
  version: 1.0.0
  category: env-migration
---

# env-migration-runtime-version-detection-fix-2026-07-02-170804

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 运行时检测工具链修复 |
| **日期** | 2026-07-02 |
| **文件名时间戳** | `2026-07-02-170804` |
| **触发原因** | 真源检测中 opencode_cli / gh_cli 上游查询返回"未知查询参数"；llama_cpp_python 本地版本检测返回 N/A |
| **影响范围** | `references/runtime/runtime_config/tools_config.json`、`py-plugins/runtime_version.py`、`py-tools/runtime-common/atomic-detect-local.py` |
| **风险等级** | 低（配置与参数修复，无文件系统副作用） |


***

## 一、文本文件变更清单

### 1. 修改 `references/runtime/runtime_config/tools_config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/tools_config.json` |
| **变更类型** | 修改 |
| **修改内容** | `opencode_cli.upstream.query_param`: `"anomalyco/opencode"` → `"opencode_cli"`；`gh_cli.upstream.query_param`: `"cli/cli"` → `"gh_cli"` |
| **作用** | 与 v2.0 `atomic-query-upstream.py` 内部路由对齐（按工具别名而非 owner/repo 路由） |
| **验证方式** | 执行 `wf-verify-runtime.py`，确认 opencode_cli / gh_cli 上游查询返回正确版本号 |
| **迁移方式** | 直接覆盖 |

> **根因**：`git checkout -- .` 把 `tools_config.json` 恢复到了 v1.0（`upstream-queries.ps1` 时代）的 owner/repo 格式，v2.0 原子脚本不认识。


### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py` |
| **变更类型** | 修改 |
| **修改内容** | `_detect_package_import()` 重构：移除 `python -c` 违规用法，改为同进程直接 `__import__()` + `importlib.metadata.version()`；新增 `_detect_package_import_whl()` 作为 whl 文件名兜底 |
| **作用** | 消除 `python -c` 违规；双源互相佐证（进程内 import 优先，whl 文件名兜底） |
| **验证方式** | 执行 `wf-verify-runtime.py --tool llama_cpp_python`，确认本地版本返回正确值 |
| **迁移方式** | 直接覆盖 |


### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-detect-local.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-detect-local.py` |
| **变更类型** | 修改 |
| **修改内容** | `runtime_version.detect()` 调用追加 `package_name=config.get("package_name", "")` 参数 |
| **作用** | 修复 `llama_cpp_python` 检测时 `package_name` 未传入 runtime_version plugin 的问题 |
| **验证方式** | 同上，确认 `llama_cpp_python` 本地版本不再返回 N/A |
| **迁移方式** | 直接覆盖 |


***

## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等非文本操作。


***

## 三、运行时检测结果（修复后）

| 工具 | 本地版本 | 上游版本 | 状态 |
|------|---------|---------|------|
| python | 3.13.14 | 3.13.14 | 已是最新 |
| node | 26.4.0 | 26.4.0 | 已是最新 |
| npm | 11.17.0 | — | 跳过 |
| **opencode_cli** | **1.17.7** | **1.17.13** | **可更新** |
| cursor | 3.9.16 | — | 跳过 |
| **llama_cpp_python** | **0.3.22** | **0.3.22** | **已是最新** |
| chromium | 152.0.7925.0 | 152.0.7925.0 | 已是最新 |
| git | 2.54.0.windows.1 | — | 跳过 |
| gh_cli | 2.95.0 | 2.95.0 | 已是最新 |

> **待办**：opencode_cli `1.17.7` → `1.17.13` 可更新，尚未替换。


***

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文件） | `run-lint.py` | frontmatter + 编码 + 换行符 | 全部通过 |

**执行命令**：
```powershell
${devroot}\venv\py\python.exe ${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py --devroot ${devroot} --files ${devroot}\references\env-migrations\env-migration-runtime-version-detection-fix-2026-07-02-170804.md
```


***

## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 opencode_cli 上游查询正常 | `python wf-verify-runtime.py --tool opencode_cli` | 返回上游版本号（如 1.17.13） |
| 2 | 确认 gh_cli 上游查询正常 | `python wf-verify-runtime.py --tool gh_cli` | 返回上游版本号 |
| 3 | 确认 llama_cpp_python 本地版本正常 | `python wf-verify-runtime.py --tool llama_cpp_python` | 本地版本返回 0.3.22，非 N/A |
| 4 | 全量检测无失败 | `python wf-verify-runtime.py` | 无 `未知查询参数` 错误 |


***

## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 tools_config.json | `git checkout -- references/runtime/runtime_config/tools_config.json` |
| 恢复 runtime_version.py | `git checkout -- references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py` |
| 恢复 atomic-detect-local.py | `git checkout -- references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-detect-local.py` |


***

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-02-170804 |
| **更新人** | Human + Agent Session |
| **变更触发** | 真源检测上游查询失败 + 本地版本检测失败排查 |
| **下次修订条件** | 新增工具链检测项、或 upstream query 路由逻辑变更 |
| **跨环境迁移参考** | 直接复制三处文件修改 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-02-170804*
*记录者：Agent (OpenCode / kimi-k2.6)*
