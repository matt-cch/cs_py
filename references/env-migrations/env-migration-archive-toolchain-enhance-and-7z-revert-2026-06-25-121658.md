---
title: 归档工具链增强与默认值勘误（7z 回退 + 实时进度 + TOP20 卡点）
description: archive_compressor 插件增强实时进度输出与 TOP20 大文件卡点分析；修正昨日 zip 优于 7z 的错误结论，默认格式从 zip 回退到 7z；记录冷启动/热启动、cs_py/venv 的多维度实测对比。
date: 2026-06-25
meta: {}
---

# `env-migration-archive-toolchain-enhance-and-7z-revert-2026-06-25-121658.md`

> **文档性质**：环境迁移指南。聚焦归档工具链的代码变更、默认值回退与性能实测数据。  
> **受众**：Human + Agent。在新环境可直接复现实测命令验证归档行为。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 归档工具链增强与默认值勘误（7z 回退 + 实时进度 + TOP20 卡点） |
| **日期** | 2026-06-25 |
| **文件名时间戳** | `2026-06-25-121658` |
| **触发原因** | 昨日 env-migration 得出 "zip 优于 7z" 的错误结论，今日冷启动复测发现完全相反；同时用户要求增强 compress 阶段的可观测性 |
| **影响范围** | `scripts/py-plugins/archive_compressor.py`、`scripts/py-tools/archive_project.py` / `archive_cs_py.py` / `archive_venv.py`、`TASK-TOOLS-INDEX.md`、既有 env-migration 勘误 |
| **风险等级** | 低（仅影响归档备份流程，不影响开发环境运行） |

## 一、文本文件变更清单

### 1. 修改 `scripts/py-plugins/archive_compressor.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_compressor.py` |
| **变更类型** | 修改（功能增强） |
| **新增内容** | 1. compress 前增加文件大小统计（总原始大小、平均、中位数、TOP 20 大文件列表）  <br>2. 7z 命令增加 `-bb1` 参数，输出逐文件处理日志  <br>3. `subprocess.run` 改为 `subprocess.Popen` + 消费者线程，实时解析 stdout 中的 `+ filename` 行  <br>4. `heartbeat` 函数增强：每秒输出 `已处理 Y/Z (P%) 最近: filename` |
| **作用** | 压缩过程可观测：提前暴露潜在卡点大文件，实时知道压到哪了 |
| **验证方式** | 执行归档命令，观察 compress 阶段是否有 TOP 20 列表和实时进度 |
| **迁移方式** | 直接覆盖（插件由 py_lib 动态加载，无需注册表变更） |

### 2. 修改 `scripts/py-tools/archive_project.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive_project.py` |
| **变更类型** | 修改（默认值回退） |
| **修改内容** | `--format` 默认值从 `"zip"` 回退到 `"7z"` |
| **作用** | 修正昨日错误结论，恢复 7z 为默认格式 |
| **验证方式** | `python archive_project.py --group cs_py` 不指定 `--format` 时应输出 `format: 7z` |

### 3. 修改 `scripts/py-tools/archive_cs_py.py` / `archive_venv.py`

| 属性 | 值 |
|------|-----|
| **路径** | `scripts/py-tools/archive_cs_py.py`、`scripts/py-tools/archive_venv.py` |
| **变更类型** | 修改（注释同步） |
| **修改内容** | docstring 中的用法示例 `[--format zip]` 改为 `[--format 7z]` |
| **作用** | 文档与代码默认值保持一致 |

### 4. 修改 `TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改（速查命令同步） |
| **修改内容** | 5 处 `--format zip` 改为 `--format 7z` |
| **作用** | 速查表与代码默认值保持一致 |

### 5. 勘误既有 `env-migration-archive-cs-py-venv-zip-2026-06-24-175445.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/env-migrations/env-migration-archive-cs-py-venv-zip-2026-06-24-175445.md` |
| **变更类型** | 修改（追加勘误章节） |
| **修改内容** | frontmatter description 追加勘误说明；文档末尾新增「八、勘误（2026-06-25）」章节，含复测数据、根因分析、后续动作 |
| **作用** | 防止错误结论被后续 session 引用 |

## 二、非文本操作（文件系统/缓存迁移）

本次 session 无文件系统迁移操作，仅执行归档命令进行验证。

## 三、性能基准与实测对比

### 3.1 核心结论修正

| 指标 | zip（完整执行） | 7z | 结论 |
|------|----------------|-----|------|
| **cs_py 压缩耗时** | **296.28s** | **34.20s** | 7z 快 8.7 倍 |
| **cs_py 输出大小** | 381.4 MB | **313.2 MB** | 7z 小 18% |
| **cs_py 审计** | FAIL（差异 38） | **PASS** | 7z 正确性更优 |
| **venv 冷启动 compress** | — | **71.28s** | 小文件海量随机 IO |
| **venv 热启动 compress** | — | **18.66s** | OS 磁盘缓存命中 |

### 3.2 昨日错误结论根因

- **zip "30s" 异常快**：前一次压缩的 OS 文件系统缓存或 7z 临时文件残留导致复用，非 zip 本身性能优势
- **7z ">300s" 异常慢**：当时可能有其他高 IO 进程抢占磁盘带宽，或 7z 实例未正常退出导致锁竞争
- **今日冷启动复测**：zip 和 7z 均在无缓存干扰下执行，结果可信

### 3.3 复现命令

```powershell
# cs_py 归档（全量项目，排除 venv/）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\archive_cs_py.py" --stage all --format 7z

# venv 归档（配置骨架，白名单过滤）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\archive_venv.py" --stage all --format 7z

# 组合归档（cs_py + venv）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\archive_project.py" --group cs_py venv --stage all --format auto
```

### 3.4 磁盘缓存效应说明

| 场景 | venv compress 耗时 | 原因 |
|------|-------------------|------|
| **冷启动**（单独执行） | 71.28s | 7,121 个 node_modules 小文件，随机 IO，磁盘是瓶颈 |
| **热启动**（紧跟 cs_py） | 18.66s | OS 页缓存保留文件元数据和内容，内存直接读取 |
| **cs_py** | ~32s（稳定） | 大文件顺序 IO，瓶颈在 CPU 压缩，缓存影响小 |

## 四、落盘验证

| 文件类型 | 验证工具 | 结果 |
|---------|---------|------|
| `.py`（archive_compressor.py 等） | run-lint.py（lint_python + lint_encoding） | ✅ 通过 |
| `.md`（本文件 + TASK-TOOLS-INDEX.md + 既有 env-migration） | run-lint.py（md_lint + lint_encoding） | ✅ 通过 |

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认默认格式为 7z | `python archive_project.py --group cs_py --stage compress`（不指定 --format） | 输出 `format: 7z` |
| 2 | 确认实时进度输出 | 同上 | 心跳显示 `已处理 Y/Z (P%) ...` |
| 3 | 确认 TOP 20 卡点列表 | 同上 | compress 阶段前打印 20 个最大文件 |
| 4 | 确认审计通过 | 同上 | 输出 `审计: PASS` |
| 5 | 确认既有 env-migration 已勘误 | `Get-Content references/env-migrations/env-migration-archive-cs-py-venv-zip-2026-06-24-175445.md -Tail 20` | 包含「勘误（2026-06-25）」章节 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 zip 为默认 | `git checkout scripts/py-tools/archive_project.py`（还原 `--format` 默认值为 `"zip"`） |
| 移除实时进度增强 | `git checkout scripts/py-plugins/archive_compressor.py` |
| 恢复速查表 | `git checkout references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| 移除勘误 | `git checkout references/env-migrations/env-migration-archive-cs-py-venv-zip-2026-06-24-175445.md` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-25-121658 |
| **更新人** | Human + Agent Session |
| **变更触发** | 归档工作流实测验证与可观测性增强 |
| **下次修订条件** | archive_compressor 插件新增统计维度或格式支持变更 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-25*  
*模板版本：v2*
