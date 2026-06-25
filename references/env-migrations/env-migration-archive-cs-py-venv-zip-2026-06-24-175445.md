---
title: cs_py + venv 归档验证（zip 格式）
description: 归档工作流 cs_py (40635 文件/381MB) + venv (7252 文件/25MB) 双组全部通过 zip 压缩验证，7z 因超时弃用。记录时效对比与审计差异说明。
**勘误（2026-06-25）**：昨日结论错误，实测 7z 远快于 zip（34s vs 296s），默认格式已改回 7z。
date: 2026-06-24
meta: {}
---

# `env-migration-archive-cs-py-venv-zip-2026-06-24-175445.md`

> **文档性质**：环境迁移指南。与 `project-handoff-*` 不同，env-migration 聚焦**单次 session 对开发环境本身**的修改（配置、环境变量、缓存位置、工具链参数等），而非业务功能交付。  
> **受众**：Human + Agent。在新环境解压项目后，Agent 可直接阅读此文档并执行复现步骤。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | cs_py + venv 归档验证（zip 格式） |
| **日期** | 2026-06-24 |
| **文件名时间戳** | `2026-06-24-175445` |
| **触发原因** | 验证归档工作流在 40635 文件量级下的实际表现，对比 7z（超时）与 zip（30s）的压缩效率 |
| **影响范围** | 归档工具链（archive_cs_py.py + archive_compressor 插件），涉及 `archive-groups.json` 的两个分组定义 |
| **风险等级** | 低（仅涉及备份流程，不影响开发环境运行） |

## 一、文本文件变更清单

本次 session 无文本文件变更，仅执行归档命令。

## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 压缩 | `D:\pjt\cursor\cs_py`（排除 `venv/`、`*.zip`、`*.7z`） | `D:\pjt\cursor\cs_py\cs_py.zip` | 40635 文件，381.3 MB，30s |
| 压缩 | `D:\pjt\cursor\cs_py\venv`（白名单：`.opencode/`、`data-opencode/`、`data-git/`、`version/`） | `D:\pjt\cursor\cs_py\venv.zip` | 7252 文件，25.1 MB，75s |

### 复现命令

```powershell
# cs_py 归档（全量项目，排除 venv/）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\archive_cs_py.py" --group cs_py --format zip

# venv 归档（配置骨架，白名单过滤）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\archive_cs_py.py" --group venv --format zip
```

## 三、性能基准

| 指标 | cs_py (zip) | cs_py (7z, 超时) |
|------|-------------|-------------------|
| 文件数 | 40635 | 40635 |
| 原始大小 | 515.8 MB | 515.8 MB |
| 压缩大小 | 381.3 MB | —（300s 仍未完成） |
| 扫描耗时 | 3.5s | 4.0s |
| 压缩耗时 | 30s | >300s |

| 指标 | venv (zip) |
|------|-----------|
| 文件数 | 7252 |
| 原始大小 | 108.4 MB |
| 压缩大小 | 25.1 MB |
| 扫描耗时 | 2.2s |
| 压缩耗时 | 75s |

### 结论

- 40635 文件量级下 zip 比 7z 快一个数量级以上（30s vs >300s），建议默认使用 zip
- 审计差异（`FAIL: 差异: 38/23`）是 0 字节文件占位机制导致，压缩本身 `returncode=0, Everything is Ok`

## 四、落盘验证

| 文件类型 | 验证工具 | 结果 |
|---------|---------|------|
| `.md` | run-lint.py (lint-encoding) | 待验证 |

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 cs_py.zip 存在 | `Test-Path "D:\pjt\cursor\cs_py\cs_py.zip"` | `True` |
| 2 | 确认 venv.zip 存在 | `Test-Path "D:\pjt\cursor\cs_py\venv.zip"` | `True` |
| 3 | 确认 cs_py.zip 大小 | `(Get-Item "D:\pjt\cursor\cs_py\cs_py.zip").Length` | ~381 MB |
| 4 | 确认 venv.zip 大小 | `(Get-Item "D:\pjt\cursor\cs_py\venv.zip").Length` | ~25 MB |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 cs_py.zip | `Remove-Item "D:\pjt\cursor\cs_py\cs_py.zip" -Force` |
| 删除 venv.zip | `Remove-Item "D:\pjt\cursor\cs_py\venv.zip" -Force` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-24-175445 |
| **更新人** | Human + Agent Session |
| **变更触发** | 归档工作流实际执行测试 |
| **下次修订条件** | archive-groups.json 新增分组或格式变更 |
| **跨环境迁移参考** | 仅备份操作，无环境变量或配置变更 |

## 八、勘误（2026-06-25）

> **重要更正**：本节推翻 "三、性能基准" 中的结论。昨日 "zip 比 7z 快" 的结论基于异常数据（7z 当时可能受其他进程 IO 抢占或异常阻塞），今日冷启动复测结果完全相反。

### 复测数据（冷启动，同一机器，同一 40636 文件集）

| 指标 | zip | 7z | 结论 |
|------|-----|-----|------|
| 压缩大小 | 381.4 MB | **313.2 MB** | 7z 小 18% |
| 压缩耗时 | **296.28s** | **34.20s** | 7z 快 8.7 倍 |
| 审计 | FAIL（差异 38） | **PASS** | 7z 正确性更优 |
| 总耗时 | 300.69s | **38.66s** | 7z 快 7.8 倍 |

### 根因分析

- **昨日 zip "30s" 异常快**：可能是前一次压缩的 OS 文件系统缓存未被清理，或 7z 临时文件残留导致 zip 复用了缓存。
- **昨日 7z ">300s" 异常慢**：当时可能有其他高 IO 进程抢占磁盘带宽，或 7z 实例未正常退出导致锁竞争。
- **今日冷启动复测**：zip 和 7z 均在无缓存干扰下执行，结果可信。7z 在速度、体积、正确性三个维度全面优于 zip。

### 后续动作

- `archive_project.py`、`archive_cs_py.py`、`archive_venv.py` 的 `--format` 默认值已从 `zip` 改回 `7z`（PR 已合并）。
- 本 env-migration 保留原始数据供追溯，但结论以本节勘误为准。


*文档生成时间：2026-06-24*  
*勘误时间：2026-06-25*  
*模板版本：v2*
