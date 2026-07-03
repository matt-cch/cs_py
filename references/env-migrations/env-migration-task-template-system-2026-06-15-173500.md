---
title: env-migration — task-template 任务模板体系建设
description: 将 debug/archive-compare/ 的 7z 备份验证实践固化为可复用的 schema/task-template/ 任务模板体系
date: 2026-06-15
---

# env-migration — task-template 任务模板体系建设

| 字段 | 值 |
|------|-----|
| **Session 主题** | task-template 任务模板体系建设 |
| **日期** | 2026-06-15 |
| **文件名时间戳** | 2026-06-15-173500 |
| **触发原因** | debug/archive-compare/ 的 7z 备份验证实践已成功跑通（0 差异），需抽象为可复用模板 |
| **影响范围** | schema/task-template/ 目录（新建）、docs/ 模板、scripts/ 调用脚本、reference/ 配置 |
| **风险等级** | 低（纯新增，不影响既有运行环境） |


## 一、文本文件变更清单

### 1. 新建 `schema/task-template/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/task-template/README.md` |
| **变更类型** | 新建 |
| **作用** | 模板总览与使用指南，含目录结构、核心原则、使用方式 |
| **验证方式** | `read schema/task-template/README.md`，确认目录树与实际文件一致 |

### 2. 新建 `schema/task-template/task-lifecycle-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/task-template/task-lifecycle-schema.md` |
| **变更类型** | 新建 |
| **作用** | 任务生命周期规范（Precheck→Scan→Process→Verify→Compare→Cleanup）、真源层级、自检清单、Manifest 规范、交付标准、修订联动义务 |
| **验证方式** | 确认包含联动矩阵和交付前自检 |

### 3. 新建 `schema/task-template/run-entry.py`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/task-template/run-entry.py` |
| **变更类型** | 新建 |
| **作用** | 统一入口，参数化驱动完整 SOP（`--config` + `--stage`） |
| **验证方式** | `python -m py_compile schema/task-template/run-entry.py` |

### 4. 新建骨架脚本（skeleton/，6 步闭环）

| 路径 | 作用 |
|------|------|
| `schema/task-template/skeleton/step-00-precheck.py` | Step 0：空状态检测与清理 |
| `schema/task-template/skeleton/step-01-scan.py` | Step 1：扫描源状态（GT） |
| `schema/task-template/skeleton/step-02-process.py` | Step 2：执行处理/转换 |
| `schema/task-template/skeleton/step-03-verify.py` | Step 3：还原结果 + 扫描 |
| `schema/task-template/skeleton/step-04-compare.py` | Step 4：GT vs Result 比对 |
| `schema/task-template/skeleton/step-05-cleanup.py` | Step 5：清理临时产物与副作用 |

**验证方式**：`python -m py_compile skeleton/step-*.py`

### 5. 新建调用脚本（scripts/，可 lint/audit）

| 路径 | 作用 |
|------|------|
| `schema/task-template/scripts/run-backup.ps1` | 一键执行完整流程 |
| `schema/task-template/scripts/compress.ps1` | 单步：压缩 |
| `schema/task-template/scripts/extract.ps1` | 单步：解压验证 |
| `schema/task-template/scripts/cleanup-extract.ps1` | 单步：清理 extract 临时目录 |
| `schema/task-template/scripts/verify-toolchain.ps1` | 诊断：验证工具链 |
| `schema/task-template/scripts/check-exists.ps1` | 诊断：检查产物是否存在 |

**验证方式**：`PSParser::Tokenize` 语法检查

### 6. 新建文档模板（docs/）

| 路径 | 作用 |
|------|------|
| `schema/task-template/docs/DESIGN-template.md` | 设计文档模板（决策记录、踩坑、SOP） |
| `schema/task-template/docs/SOP-CHEATSHEET-template.md` | 一页纸命令速查（硬性规则：每条命令必须对应 scripts/ 下的独立文件） |
| `schema/task-template/docs/ENTRY-template.json` | 机器可读真源索引 |

### 7. 新建配置模板（reference/）

| 路径 | 作用 |
|------|------|
| `schema/task-template/reference/task-config-template.json` | 任务配置文件模板（分组、路径、工具链、排除规则） |

### 8. 新建实例归档（examples/）

| 路径 | 作用 |
|------|------|
| `schema/task-template/examples/archive-compare/README.md` | 首个实例：7z 备份验证的完整落地索引 |


## 二、非文本操作

本次 session 无文件复制/迁移/缓存操作，全部为新建文本文件。


## 三、环境变量速查

无需变更环境变量。所有工具链路径均通过 `reference/task-config-template.json` 显式声明。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | Python 骨架脚本语法 | `python -m py_compile schema/task-template/skeleton/step-*.py` + `run-entry.py` | 全部 PASS |
| 2 | PowerShell 调用脚本语法 | `PSParser::Tokenize` 检查 `scripts/*.ps1` | 全部 PASS |
| 3 | JSON 配置模板有效 | `ConvertFrom-Json reference/task-config-template.json` | VALID |
| 4 | 换行符检查 | 字节检查 `0x0D` 出现次数 | CRLF=0 |
| 5 | 目录结构一致性 | 比对 `README.md` 目录树 vs 实际磁盘文件 | 完全一致 |
| 6 | 速查表命令落盘检查 | 确认 `SOP-CHEATSHEET-template.md` 中每条命令都指向 `scripts/` 下存在的文件 | 全部命中 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 task-template 目录 | `Remove-Item -Recurse "schema/task-template"` |
| 无其他副作用 | — |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-15-173500 |
| **更新人** | Agent Session |
| **变更触发** | 7z 备份验证实践成功，需固化为可复用模板 |
| **下次修订条件** | 新增骨架脚本时，需同步更新调用脚本、速查表、README 目录树（修订联动义务） |
| **跨环境迁移参考** | 直接复制 `schema/task-template/` 目录即可使用 |


*文档生成时间：2026-06-15*  
*模板版本：v2*
