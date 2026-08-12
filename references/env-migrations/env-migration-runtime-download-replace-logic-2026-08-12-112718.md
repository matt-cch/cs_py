---
title: 运行时下载替换逻辑层级对齐改造
description: atomic-04-backup-replace.py 目录推导从 exe 父目录改为按 venv 层级深度对齐，解决 Git 等多层目录工具替换不完整问题，经 Git + Chrome 双工具实证通过。
date: 2026-08-12
meta: {}
---

# env-migration-runtime-download-replace-logic-2026-08-12-112718

## 元信息

| 字段 | 值 |
|------|-----|
| Session 主题 | 运行时下载替换逻辑层级对齐改造 |
| 日期 | 2026-08-12 |
| 文件名时间戳 | 2026-08-12-112718 |
| 触发原因 | Git 更新时 `atomic-04-backup-replace.py` 推导出的 `tool_dir` 为 `venv/git/cmd`，仅替换子目录，MinGit 其他目录（bin/libexec 等）未被更新 |
| 影响范围 | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-04-backup-replace.py`、`wf-download-runtime.py` Step 7 |
| 风险等级 | 中（涉及工具链目录覆盖替换，已备份） |

## 一、文本文件变更清单

### 1. 修改 `atomic-04-backup-replace.py`

| 属性 | 值 |
|------|-----|
| 路径 | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-04-backup-replace.py` |
| 变更类型 | 重构 |
| 作用 | 替换逻辑全部收归内部，调用者零推导；新增 `derive_tool_dir` 和 `derive_source_dir` 按层级深度对齐 |
| 验证方式 | Git 2.55.0.windows.3 → 2.55.0.windows.4 替换成功；Chrome 153.0.8000.0 → 153.0.8002.0 替换成功 |
| 迁移方式 | 直接覆盖 |

**核心变更**：
- 新增 `derive_tool_dir(exe_path)`：exe_path 去掉 venv 后的第一级目录。`venv/git/cmd/git.exe` → `venv/git`
- 新增 `derive_source_dir(exe_path, found_exe)`：按 exe_path 去掉 venv 后的目录层级深度，从 found_exe 父目录往上回溯同样层数
  - `venv/node/node.exe`（1 层）→ found_exe 父目录即 source_dir
  - `venv/git/cmd/git.exe`（2 层）→ found_exe 父目录往上 1 层
- `backup_and_replace` 内部推导 tool_dir 和 source_dir，外部调用者只传 `--exe-path` 和 `--found-exe`
- 备份后 `rmtree(tool_dir)` + `copytree(source_dir, tool_dir)` 完整目录覆盖
- CLI 参数从 `--tool-dir/--source-dir/--exe-path` 改为 `--exe-path/--found-exe`

### 2. 修改 `wf-download-runtime.py` Step 7

| 属性 | 值 |
|------|-----|
| 路径 | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` |
| 变更类型 | 修改 |
| 作用 | 调用方不再推导 tool_dir/source_dir，直接传 `--exe-path` 和 `--found-exe` |
| 验证方式 | 同上 |
| 迁移方式 | 直接覆盖 |

## 二、非文本操作

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 工具更新 | `download/git-2.55.0.windows.4-extracted` | `venv/git` | MinGit 2.55.0.windows.3 → 2.55.0.windows.4，完整目录覆盖 |
| 工具更新 | `download/chromium-153.0.8002.0-extracted/chrome-win64` | `download/chrome-win64` | Chrome for Testing 153.0.8000.0 → 153.0.8002.0，完整目录覆盖 |
| 备份生成 | `venv/git` | `venv/git-backup-20260812112353` | Git 旧版本备份 |
| 备份生成 | `download/chrome-win64` | `download/chrome-win64-backup-20260812112556` | Chrome 旧版本备份 |

## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | Git 版本确认 | `venv\git\cmd\git.exe --version` | `git version 2.55.0.windows.4` |
| 2 | Git 目录完整性 | `Get-ChildItem venv\git` | 存在 cmd/bin/libexec/etc/share 等完整目录 |
| 3 | Chrome 版本确认 | `download\chrome-win64\chrome.exe --version` | `153.0.8002.0` |
| 4 | 备份存在性 | `Test-Path venv\git-backup-20260812112353` | True |
| 5 | lint 通过 | `run-lint.py --files atomic-04-backup-replace.py wf-download-runtime.py` | 0 违规 |

## 四、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 Git | `Remove-Item -Recurse venv\git`; `shutil.move(venv\git-backup-20260812112353, venv\git)` |
| 恢复 Chrome | `Remove-Item -Recurse download\chrome-win64`; `shutil.move(download\chrome-win64-backup-20260812112556, download\chrome-win64)` |
| 恢复脚本 | `git checkout atomic-04-backup-replace.py wf-download-runtime.py` |

## 五、文档元信息

| 属性 | 值 |
|------|-----|
| 最后更新 | 2026-08-12-112718 |
| 更新人 | Agent Session |
| 变更触发 | Git 替换不完整缺陷 |
| 下次修订条件 | 新增非 venv 工具链目录结构或 exe 层级超过 2 层时 |
| 跨环境迁移参考 | 直接替换脚本文件 + 按验证清单执行 |
