---
title: 7z Zip 可靠备份方案验证与脚本落地
description: 验证 7z zip（listfile + -scsUTF-8）能否完整无损备份 cs_py 和 venv 两组目录。产出通用备份扫描器 scan-for-backup.py，修复两个 bug，验证通过并记录设计文档。
date: 2026-06-13
---

# env-migration-reliable-backup-2026-06-13-151421.md

> **文档性质**：环境迁移指南。记录本次 session 在 `debug/archive-compare/` 下新增的可复用脚本、修复的 bug、以及备份方案设计决策。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 7z Zip 可靠备份方案验证与通用脚本落地 |
| **日期** | 2026-06-13 |
| **文件名时间戳** | 2026-06-13-151421 |
| **触发原因** | 需要可靠的备份方案验证 7z listfile 方式能否完整无损备份项目目录 |
| **影响范围** | `debug/archive-compare/`（新增脚本与设计文档）、`venv/tmp/scan-for-backup/`（清理冗余） |
| **风险等级** | 低 |


## 一、文本文件变更清单

### 1. 新建 `debug/archive-compare/scan-for-backup.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/scan-for-backup.py` |
| **变更类型** | 新建 |
| **作用** | 通用备份扫描器，替代旧版 `gen-manifest.py` + `gen-listfile.py` 两步流程 |
| **核心功能** | 支持 whitelist（白名单子目录）+ blacklist（排除模式）+ 空目录占位 + listfile 导出 |
| **迁移方式** | 直接复制文件 |

### 2. 新建 `debug/archive-compare/step-4-compress.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/step-4-compress.py` |
| **变更类型** | 新建 |
| **作用** | 参数化 7z 压缩脚本（`--cwd`/`--zip`/`--listfile`），替代旧版硬编码压缩脚本 |
| **迁移方式** | 直接复制文件 |

### 3. 新建 `debug/archive-compare/BACKUP-DESIGN.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/BACKUP-DESIGN.md` |
| **变更类型** | 新建 |
| **作用** | 备份方案设计文档，含脚本架构、设计决策、操作流程、踩坑记录 |
| **迁移方式** | 直接复制文件 |

### 4. 修改 `debug/archive-compare/scan-for-backup.py`（两次 bug 修复）

| 属性 | 值 |
|------|-----|
| **路径** | `debug/archive-compare/scan-for-backup.py` |
| **变更类型** | 修改 |
| **修复 1** | `match_blacklist` 中 `dir/*` 模式不跨层级匹配的问题——`log/*` 无法排除 `venv/data-opencode/opencode/log/opencode.log`，修复后 `/*` 后缀等效于目录树排除 |
| **修复 2** | 白名单模式下不记录子目录自身 DIR 条目（如 `venv/.opencode`）——扫描后补齐缺失的根目录 |
| **迁移方式** | 直接复制文件 |

### 5. 清理 `venv/tmp/scan-for-backup/`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/tmp/scan-for-backup/` |
| **变更类型** | 删除 |
| **删除的文件** | `run-compress.py`、`run-compress-venv.py`、`step-1-validate.py`、`step-2-scan.py`、`step-3-placeholder.py`（均为临时现写的硬编码脚本，已有通用版本替代） |
| **保留的文件** | CSV 数据、listfile、summary 报告等中间产物 |
| **迁移方式** | 无需迁移 |


## 二、非文本操作

无。


## 三、验证结论

| 分组 | 文件数 | 压缩包 | 比对结果 |
|------|--------|--------|---------|
| **cs_py** | 28,557 文件 | 253 MB | GT 独有 1（验证中修改）、字段不符 1（验证中编辑），均属预期 |
| **venv** | 6,982 文件 | 25 MB | **完全匹配（0 差异）** |

结论：7z zip（listfile + `-scsUTF-8`）可完整无损备份两组目录。


## 四、脚本架构速查

所有可复用脚本位于 `debug/archive-compare/`：

| 脚本 | 用途 | 调用方式 |
|------|------|---------|
| `scan-for-backup.py` | 扫描目录生成 GT CSV + listfile | `python scan-for-backup.py --src ... --arcname ...` |
| `step-4-compress.py` | 7z 压缩 | `python step-4-compress.py --cwd ... --zip ... --listfile ...` |
| `step-extract.py` | 7z 解压 | `python step-extract.py <zip> <dst>` |
| `step-scan-extract.py` | 扫描解压目录 | `python step-scan-extract.py <extract_dir> <output_csv>` |
| `step-compare.py` | GT vs Extract 比对 | `python step-compare.py <gt_csv> <extract_csv> <report>` |
| `BACKUP-DESIGN.md` | 设计文档，含 SOP | 阅读参考 |


## 五、环境变量速查

无新增环境变量。


## 六、验证清单

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | 确认脚本存在 | `Test-Path 'debug/archive-compare/scan-for-backup.py'` | True |
| 2 | 确认脚本存在 | `Test-Path 'debug/archive-compare/BACKUP-DESIGN.md'` | True |
| 3 | 确认旧临时脚本已清理 | `Test-Path 'venv/tmp/scan-for-backup/run-compress.py'` | False |


## 七、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 删除新建脚本 | `Remove-Item 'debug/archive-compare/scan-for-backup.py', 'debug/archive-compare/step-4-compress.py', 'debug/archive-compare/BACKUP-DESIGN.md'` |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-13-151421 |
| **更新人** | Human + Agent Session |
| **变更触发** | 需要可靠的 7z zip 备份方案 |
| **下次修订条件** | backup 脚本架构变更、新增排除规则、验证流程调整 |
| **跨环境迁移参考** | 直接复制 `debug/archive-compare/` 目录即可迁移全部脚本 |


*文档生成时间：2026-06-13*
