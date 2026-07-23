---
title: 7z 归档 Pipeline 全流程验证与脚本增强
description: 从头实测 cs_py + venv 两组 7z 归档全流程（扫描→压缩→解压→比对），产出 OPERATIONS.md 指南，增强所有脚本（耗时报告、心跳进度、大小显示、序号验证器）。
date: 2026-06-15
---

# env-migration-7z-archive-pipeline-full-verification-2026-06-15-001800.md

> **文档性质**：环境迁移指南。记录本次 session 对 `debug/archive-compare/` 下归档脚本体系的增强与实测验证结果。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 7z 归档 Pipeline 全流程验证与脚本增强 |
| **日期** | 2026-06-15 |
| **文件名时间戳** | `2026-06-15-001800` |
| **触发原因** | 用户要求做一次完整的 7z 归档，从下载 7z 工具链到验证比对 |
| **影响范围** | `debug/archive-compare/`（脚本增强 + 新增文件）|`D:\download\7-Zip\`（7z 工具链安装） |
| **风险等级** | 低 |


## 一、文本文件变更清单

### 1. 新增 `debug/archive-compare/OPERATIONS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/OPERATIONS.md` |
| **变更类型** | 新建 |
| **作用** | 项目归档操作指南，含 cs_py + venv 两组标准操作流程（SOP） |
| **迁移方式** | 直接复制文件 |

### 2. 新增 `debug/archive-compare/inspect-gt.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/inspect-gt.py` |
| **变更类型** | 新建 |
| **作用** | Ground Truth 分析器（size/empty/top/compare），替代临时脚本 |
| **迁移方式** | 直接复制文件 |

### 3. 新增 `debug/archive-compare/verify-scan-realtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/verify-scan-realtime.py` |
| **变更类型** | 新建 |
| **作用** | 逐条打印验证扫描器（带序号），供用户手工验证扫描真实性 |
| **迁移方式** | 直接复制文件 |

### 4. 修改 `debug/archive-compare/scan-for-backup.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/scan-for-backup.py` |
| **变更类型** | 修改 |
| **修改内容** | ① 加入 `time` 模块计时；② 输出增加原始大小和耗时报告 |
| **迁移方式** | 直接复制文件 |

### 5. 修改 `debug/archive-compare/step-4-compress.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/step-4-compress.py` |
| **变更类型** | 修改 |
| **修改内容** | ① 加入心跳线程（每 1 秒打印进度）；② 执行前打印文件数；③ 输出增加耗时报告 |
| **迁移方式** | 直接复制文件 |

### 6. 修改 `debug/archive-compare/step-extract.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/step-extract.py` |
| **变更类型** | 修改 |
| **修改内容** | ① 加入心跳线程（每 1 秒打印进度）；② 执行前打印 ZIP 大小；③ 输出增加耗时报告 |
| **迁移方式** | 直接复制文件 |

### 7. 修改 `debug/archive-compare/step-scan-extract.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/step-scan-extract.py` |
| **变更类型** | 修改 |
| **修改内容** | 加入 `time` 模块计时，输出增加耗时报告 |
| **迁移方式** | 直接复制文件 |

### 8. 修改 `debug/archive-compare/step-compare.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/step-compare.py` |
| **变更类型** | 修改 |
| **修改内容** | ① 加入 `time` 模块计时；② 报告增加 GT/Extract 总大小；③ 输出增加耗时报告 |
| **迁移方式** | 直接复制文件 |


## 二、非文本操作

### 7z 工具链安装

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 下载 | `https://www.7-zip.org/a/7zr.exe` | `D:\download\7zr.exe` | 7zr 自解压器 |
| 下载 | `https://www.7-zip.org/a/7z2601-extra.7z` | `D:\download\7z2601-extra.7z` | 7-Zip Extra 包 |
| 解压 | `D:\download\7z2601-extra.7z` | `D:\download\7-Zip\` | 用 7zr 解压 |
| 复制 | `D:\download\7-Zip\x64\7za.exe` | `D:\download\7-Zip\7z.exe` | 复制为 7z.exe 保持路径兼容 |

**验证**：
```powershell
D:
    # 应输出: 7-Zip (a) 26.01 (x64) : Copyright (c) 1999-2026 Igor Pavlov : 2026-04-27
```


## 三、环境变量速查

无新增环境变量。


## 四、验证清单

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | 确认 7z 可用 | `D:\download\7-Zip\7z.exe` | 输出版本信息 |
| 2 | 确认 scan-for-backup.py 含耗时 | `python scan-for-backup.py --help` | 帮助正常 |
| 3 | 确认 step-4-compress.py 含心跳 | 执行压缩观察 | 每 1 秒打印 `[compress] 已运行 Xs...` |
| 4 | 确认 step-extract.py 含心跳 | 执行解压观察 | 每 1 秒打印 `[extract] 已运行 Xs...` |
| 5 | 确认 step-compare.py 含大小 | 执行比对 | 报告含 `GT 总大小` / `Extract 总大小` |
| 6 | 确认 verify-scan-realtime.py | 执行并观察 | 每行含 6 位序号 |


## 五、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 恢复旧脚本 | 从 git 回滚 `debug/archive-compare/*.py` |
| 删除新建文件 | `Remove-Item 'debug/archive-compare/OPERATIONS.md', 'debug/archive-compare/inspect-gt.py', 'debug/archive-compare/verify-scan-realtime.py'` |
| 删除 7z | `Remove-Item -Recurse 'D:\download\7-Zip'`, `Remove-Item 'D:\download\7zr.exe', 'D:\download\7z2601-extra.7z'` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-15-001800 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求完整 7z 归档验证 |
| **下次修订条件** | 归档脚本架构变更、新增排除规则、验证流程调整 |
| **跨环境迁移参考** | 直接复制 `debug/archive-compare/` 目录 + 安装 7z 到 `D:\download\7-Zip\` |


*文档生成时间：2026-06-15*