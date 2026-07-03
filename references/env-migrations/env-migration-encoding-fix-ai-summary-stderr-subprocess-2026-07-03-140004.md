---
title: 编码修复 — AI 摘要生成 stderr 乱码与 subprocess 解码错误
description: 补齐 generate-ai-summary.py 的 stderr 编码重配置，为 workflow-deploy-full.py 所有 subprocess.run 添加 errors="replace"，消除 AI 摘要生成时的 UnicodeDecodeError
date: 2026-07-03
meta:
  version: "1.0.0"
---

# env-migration-encoding-fix-ai-summary-stderr-subprocess-2026-07-03-140004.md

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 编码修复：AI 摘要生成 stderr 乱码与 subprocess 解码错误 |
| **日期** | 2026-07-03 |
| **文件名时间戳** | `2026-07-03-140004` |
| **触发原因** | workflow-deploy-full.py 调用 generate-ai-summary.py 时出现 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbf`，且中文 stderr 输出乱码 |
| **影响范围** | `py-tools/generate-ai-summary.py`、`py-tools/workflow-deploy-full.py` |
| **风险等级** | 低（纯编码修复，无业务逻辑变更） |

## 一、文本文件变更清单

### 1. 修改 `py-tools/generate-ai-summary.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py` |
| **变更类型** | `追加` |
| **新增内容** | `sys.stderr.reconfigure(encoding="utf-8")`（第 27 行） |
| **作用** | 确保子进程内部的 stderr 中文输出能被正确编码为 UTF-8，避免父进程解码时出现乱码或 UnicodeDecodeError |
| **验证方式** | lint 通过；直接调用 generate-ai-summary.py 验证中文输出正常 |
| **迁移方式** | 直接追加一行 |

### 2. 修改 `py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | `修改` |
| **修改内容** | 4 处 `subprocess.run` 添加 `errors="replace"`：① branch --show-current；② diff --cached --name-only；③ generate-ai-summary.py 子进程调用；④ rev-parse --short HEAD |
| **作用** | 当子进程输出包含非 UTF-8 字节（如 Windows 版 git.exe 输出的 GBK 字节）时，用替代字符替换而非抛出 UnicodeDecodeError，避免 reader thread 崩溃 |
| **验证方式** | lint 通过；workflow 全流程执行无编码异常 |
| **迁移方式** | 直接修改参数 |

## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。

## 三、环境变量速查

无新增环境变量。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文档） | run-lint.py (lint-encoding + md_lint) | BOM、双 BOM、CRLF、frontmatter | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, frontmatter 合规 |
| `.py`（generate-ai-summary.py） | run-lint.py (lint-python + lint-encoding) | Python 语法、编码 | 语法通过、UTF-8 无 BOM |
| `.py`（workflow-deploy-full.py） | run-lint.py (lint-python) | Python 语法 | 语法通过 |

**执行命令**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-encoding-fix-ai-summary-stderr-subprocess-2026-07-03-140004.md" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\generate-ai-summary.py" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 generate-ai-summary.py stderr 编码正确 | `python generate-ai-summary.py --cached --message test` | 无乱码输出，无 UnicodeDecodeError |
| 2 | 确认 workflow 无编码崩溃 | `workflow-deploy-full.py --auto`（有 staged 文件时） | AI 摘要生成成功，reader thread 不崩溃 |
| 3 | 确认 lint 通过 | `run-lint.py --files <修改的 py 文件>` | 全部通过 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 generate-ai-summary.py | 删除第 27 行 `sys.stderr.reconfigure(encoding="utf-8")` |
| 恢复 workflow-deploy-full.py | 从 Git 恢复，移除 4 处 `errors="replace"` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-03-140004 |
| **更新人** | Human + Agent Session |
| **变更触发** | AI 摘要生成时出现 UnicodeDecodeError，需修复编码处理 |
| **下次修订条件** | 新增 subprocess 调用时未加 `errors="replace"` |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
