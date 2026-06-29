---
title: 运行时域原子脚本重构
description: 将 references/runtime/ 下的 verify-runtime 与 download-runtime-tool 拆分为 task 插件体系原子脚本，含架构决策、踩坑修复与误操作恢复记录。
date: 2026-06-26
meta:
  version: 1.0.0
---

# env-migration-runtime-atomic-refactor-2026-06-26-231301

| 字段 | 值 |
|------|-----|
| **Session 主题** | 运行时域原子脚本重构（verify-runtime / download-runtime-tool → task 插件体系） |
| **日期** | 2026-06-26 |
| **文件名时间戳** | `2026-06-26-231301` |
| **触发原因** | 单体脚本职责混杂、步骤黑盒、不可独立测试；需走 atomic 原子脚本体系 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/` 下新增 runtime-common/、verify-runtime/、download-runtime/ 子目录；`verified-task-index.json`；`TASK-TOOLS-INDEX.md`；`EXEC-CHEATSHEET.md`；`docs/research/` |
| **风险等级** | 中（涉及工具链目录操作，误操作可导致 venv/node/ 被意外重命名） |


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/wf-runtime-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/wf-runtime-full.py` |
| **变更类型** | 新建 |
| **作用** | 检测+下载一体化 Workflow：串接 detect → query → compare → download → extract verify，全程带时间戳和进度条 |
| **验证方式** | `python wf-runtime-full.py --devroot "D:	pjt	scode	sc_py" --tools node,opencode_cli` |
| **迁移方式** | 直接复制 |

### 2. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-detect-local.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-detect-local.py` |
| **变更类型** | 新建 |
| **作用** | 本地 exe 存在性检测 + candidate_paths 兜底 + 版本提取 |
| **验证方式** | `python atomic-detect-local.py --config-json '{...}' --devroot "..." --tool-name node` |

### 3. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-query-upstream.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-query-upstream.py` |
| **变更类型** | 新建 |
| **作用** | 上游版本查询（python/node/opencode/chromium/llama） |
| **验证方式** | `python atomic-query-upstream.py --tool-name node --query-param node` |

### 4. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-compare-version.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-compare-version.py` |
| **变更类型** | 新建 |
| **作用** | 版本对比（up_to_date/outdated/unknown） |
| **验证方式** | `python atomic-compare-version.py --local-ver 26.4.0 --upstream-ver 26.4.0` |

### 5. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-generate-report.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-generate-report.py` |
| **变更类型** | 新建 |
| **作用** | 报告生成（stdout 表格 + JSON 落盘） |
| **验证方式** | `python atomic-generate-report.py --results-json '[...]' --output-dir "..."` |

### 6. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py` |
| **变更类型** | 新建 |
| **作用** | 真源检测 Workflow：编排 detect → query → compare → report |
| **验证方式** | `python wf-verify-runtime.py --devroot "..." --tool node` |

### 7. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` |
| **变更类型** | 新建 |
| **作用** | 运行时下载 Workflow：编排 detect → query → compare → route → download → extract → cleanup |
| **验证方式** | `python wf-download-runtime.py --devroot "..." --tool-name node --show-progress` |

### 8. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-01-route-probe.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-01-route-probe.py` |
| **变更类型** | 新建 |
| **作用** | 路由探测：HEAD 探测直连+代理，并发返回最优路由 |
| **验证方式** | `python atomic-01-route-probe.py --url "https://github.com/.../release.zip"` |

### 9. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-02-download-file.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-02-download-file.py` |
| **变更类型** | 新建 |
| **作用** | 流式下载 + stderr 进度条 + 代理支持 |
| **验证方式** | `python atomic-02-download-file.py --url ... --out-file ... --show-progress` |

### 10. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-03-extract-verify.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-03-extract-verify.py` |
| **变更类型** | 新建 |
| **作用** | ZIP 解压 + 定位 exe + 版本验证 |
| **验证方式** | `python atomic-03-extract-verify.py --zip-file ... --tool-name node` |

### 11. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-04-backup-replace.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-04-backup-replace.py` |
| **变更类型** | 新建 |
| **作用** | 进程检测 + 备份旧版 + 替换新版（默认不调用，需显式执行） |
| **验证方式** | `python atomic-04-backup-replace.py --tool-dir ... --source-dir ... --exe-path ...` |

### 12. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-05-cleanup-temp.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-05-cleanup-temp.py` |
| **变更类型** | 新建 |
| **作用** | 清理解压目录和 ZIP 文件 |
| **验证方式** | `python atomic-05-cleanup-temp.py --extract-dir ... --zip-file ...` |

### 13. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/process_runner.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/process_runner.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | `sys.stderr.reconfigure(encoding="utf-8")` + `_ORIGINAL_STDERR_ENCODING` + `atexit.register(_restore_encoding)` |
| **作用** | 子进程 stderr 编码切换 + 退出时必恢复 |
| **验证方式** | 调用任何 py-tools 脚本，中文无乱码 |

### 14. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 删除冗余 `sys.stdout.reconfigure(encoding="utf-8")`（已由 process_runner 统一处理） |
| **作用** | 避免重复编码设置 |

### 15. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增 `wf-verify-runtime`、`wf-download-runtime`、6 个 atomic、`wf-runtime-full`；修复旧条目 `\v` 未转义导致的 JSONDecodeError |
| **作用** | 登记新工具到统一索引 |

### 16. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 追加运行时域工具表格（12 个条目）+ CLI 用法示例 |
| **作用** | 工具速查索引 |

### 17. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | Stage S8 追加 `wf-runtime-full` 推荐命令 |
| **作用** | 执行速查表 |

### 18. 新建 `references/tasks/deploy-git-isolated/docs/research/runtime-atomic-integration-experience.md`

| 属性 | 值 |
| **路径** | `references/tasks/deploy-git-isolated/docs/research/runtime-atomic-integration-experience.md` |
| **变更类型** | 新建 |
| **作用** | 集成经验文档：7 个踩坑点 + 架构决策 + 可复用经验表 |
| **迁移方式** | 直接复制 |


## 二、非文本操作（文件系统变更）

### 误操作：备份替换原子意外执行导致工具链目录被重命名

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 误重命名 | `venv/node/` | `venv/node-backup-20260626221443/` | 误跑 `atomic-04-backup-replace.py` 导致 |
| 误重命名 | `venv/opencode/` | `venv/opencode-backup-20260626221446/` | 同上 |
| 恢复 | `venv/node-backup-20260626221443/` | `venv/node/` | 手动恢复 |
| 恢复 | `venv/opencode-backup-20260626221446/` | `venv/opencode/` | 手动恢复 |
| 删除 | `D:\download\node-v26.4.0-win-x64.zip` | — | 清理下载临时文件 |
| 删除 | `D:\download\opencode-windows-arm64.zip` | — | 清理下载临时文件 |
| 删除 | `D:\download\node-extracted/` | — | 清理解压临时目录 |
| 删除 | `D:\download\opencode_cli-extracted/` | — | 清理解压临时目录 |

> **教训**：`atomic-04-backup-replace.py` 默认不应在 workflow 中自动调用；任何会修改文件系统的操作必须先检查前置条件，失败时无副作用。本次误操作已修复脚本逻辑（先检查 source_dir 再备份）。


## 三、环境变量速查

本次 session 未新增环境变量，保持现有配置不变。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md` | `run-lint.py` (md_lint + lint_encoding) | frontmatter、BOM、CRLF、LF | BOM=no, CRLF=0, LF>0 |
| `.json` | `run-lint.py` (lint_json) | JSON 语法正确性 | `[OK]` 无解析错误 |
| `.py` | `run-lint.py` (lint_python + lint_encoding) | 语法、编码 | 无 SyntaxError |

**执行结果**：全部通过 ✅


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 node 存在 | `Test-Path "venv\node\node.exe"` | `True` |
| 2 | 确认 opencode 存在 | `Test-Path "venv\opencode\opencode.exe"` | `True` |
| 3 | 确认无残留 backup 目录 | `Get-ChildItem venv\ | Where-Object { $_.Name -like '*backup*' }` | 无输出 |
| 4 | 运行检测 workflow | `python wf-verify-runtime.py --devroot "..." --tool node` | 输出 version=26.4.0 |
| 5 | 运行一体化 workflow | `python wf-runtime-full.py --devroot "..." --tools node,opencode_cli` | 检测→下载→验证完成 |
| 6 | 确认索引已登记 | `grep -i "wf-runtime-full" references/runtime/verified-task-index.json` | 命中条目 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增脚本 | `Remove-Item -Recurse scripts/py-tools/runtime-common/ scripts/py-tools/verify-runtime/ scripts/py-tools/download-runtime/`（注意：会删除本次全部新增文件） |
| 恢复 process_runner.py | 从 git 历史恢复 `scripts/py-plugins/process_runner.py` |
| 恢复 runtime_version.py | 从 git 历史恢复 `scripts/py-plugins/runtime_version.py` |
| 恢复索引 | 从 git 历史恢复 `references/runtime/verified-task-index.json` |
| 恢复文档 | 从 git 历史恢复 `TASK-TOOLS-INDEX.md`、`EXEC-CHEATSHEET.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-26-231301 |
| **更新人** | Human + Agent Session |
| **变更触发** | 单体脚本拆分为原子脚本体系 |
| **下次修订条件** | 新增更多 runtime 工具（如 bun、zig）或 upstream_checker 提取为 py-plugins |
| **跨环境迁移参考** | 直接复制新增脚本 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-26*  
*模板版本：v2*
