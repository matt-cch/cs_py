---
title: archive_project.py 全量备份 cs_py + venv
description: 执行项目归档脚本，对 devroot 下 cs_py 分组（排除 venv/ 等隔离目录）和 venv 分组（白名单子目录）分别生成 7z 压缩包，并逐一通过审计验证。
date: 2026-07-30
meta:
  version: 1.0.0
---

# env-migration-archive-project-cs-py-venv-backup-2026-07-30-172705

> **文档性质**：单次 session 的环境级变更记录。聚焦归档产物生成，非业务功能交付。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | archive_project.py 全量备份 cs_py + venv |
| **日期** | 2026-07-30（frontmatter；文件名时间戳见上表） |
| **文件名时间戳** | `2026-07-30-172705` |
| **触发原因** | 用户要求执行项目归档备份，更新本地 7z 包 |
| **影响范围** | `D:\pjt\cursor\cs_py\cs_py.7z`、`D:\pjt\cursor\cs_py\venv.7z`（旧包被覆盖） |
| **风险等级** | 低（纯归档产物生成，不修改源码或配置） |

## 一、文本文件变更清单

本次 session **未修改任何文本文件**，仅生成归档产物。

## 二、非文本操作（归档产物生成）

### 操作明细

| 操作类型 | 分组 | 源路径/范围 | 输出文件 | 说明 |
|---------|------|-----------|---------|------|
| 7z 压缩 | cs_py | `D:\pjt\cursor\cs_py`（排除 venv/、.git/、*.7z 等黑名单） | `D:\pjt\cursor\cs_py\cs_py.7z` | 覆盖旧包（`--force`） |
| 7z 压缩 | venv | `D:\pjt\cursor\cs_py\venv`（白名单：.opencode/、data-opencode/、data-git/、version/；黑名单排除缓存） | `D:\pjt\cursor\cs_py\venv.7z` | 覆盖旧包（`--force`） |

### 执行命令

```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\archive_project.py" `
    --group cs_py venv `
    --stage all `
    --format 7z `
    --devroot "${devroot}" `
    --force
```

> `--force` 用于覆盖已存在的同名 7z 文件。`--stage all` 实际执行 scan + compress（verify 需显式传入或在压缩包已存在时独立执行）。

## 三、环境变量速查

本次 session 未新增或修改环境变量注入项。

## 四、落盘验证

本次 session 生成的 7z 文件不属于文本/JSON/Markdown，不适用 `run-lint.py` 验证。以脚本内置审计机制为准。

## 五、验证清单（新环境可执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---|---------|---------|
| 1 | 确认 cs_py.7z 存在 | `Test-Path "${devroot}\cs_py.7z"` | `True` |
| 2 | 确认 cs_py.7z 大小合理 | `Get-Item "${devroot}\cs_py.7z"` | 约 27 MB |
| 3 | 确认 venv.7z 存在 | `Test-Path "${devroot}\venv.7z"` | `True` |
| 4 | 确认 venv.7z 大小合理 | `Get-Item "${devroot}\venv.7z"` | 约 8 MB |
| 5 | 可选：验证压缩包完整性 | `7z t "${devroot}\cs_py.7z"` | `Everything is Ok` |
| 6 | 可选：对比 listfile 条目数 | 与 `venv/tmp/archive-cs_py/listfile-cs_py.txt` 行数对比 | 一致 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除本次产物 | `Remove-Item "${devroot}\cs_py.7z"`; `Remove-Item "${devroot}\venv.7z"` |
| 恢复旧包 | 从外部备份复制旧版 cs_py.7z / venv.7z 回 devroot 根目录 |

## 七、审计摘要

| 分组 | 文件数 | 原始大小 | 压缩后大小 | 审计结果 |
|------|--------|---------|-----------|---------|
| cs_py | 1,898 | 94.7 MB | 27.3 MB | ✅ PASS |
| venv | 6,949 | 97.4 MB | 8.4 MB | ✅ PASS |

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-30-172705 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求执行 archive_project.py 全量备份 |
| **下次修订条件** | 当归档策略（黑名单/白名单/格式）发生变更时 |
| **跨环境迁移参考** | 直接复制 7z 文件到目标 devroot，或在新环境重新执行相同命令 |

*文档生成时间：2026-07-30-172705*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
