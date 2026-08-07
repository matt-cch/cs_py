---
title: env-migration — JSON Lines (.jsonl) 纳入 run-lint 编码与语法检测体系
description: 本次 session 完成 .jsonl 文件格式的 lint 规则建设：编码/BOM/换行符由 lint_encoding 覆盖，语法/结构由 lint_json 逐行验证（标准库+jsonlines 双重检测），audit-trail.jsonl 通过 run-lint --fix 三阶段闭环修复
date: 2026-08-07
meta:
  version: "1.0.0"
  tags: [jsonl, lint, run-lint, jsonlines, audit-trail]
---

# env-migration — JSON Lines (.jsonl) 纳入 run-lint 编码与语法检测体系

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | `.jsonl` 文件格式 lint 规则建设与 audit-trail.jsonl 修复 |
| **日期** | 2026-08-07 |
| **文件名时间戳** | `2026-08-07-123115` |
| **触发原因** | 用户指出 rg-fd-search skill 演进涉及 `audit-trail.jsonl` 创建，引出 run-lint 应将 `.jsonl` 纳入 lint-fix 体系；用户明确要求多方搜索规范后给出建议，review 后落盘 |
| **影响范围** | `lint_encoding.py`、`lint_json.py`、`run-lint.py`、`.jsonl` 文件全项目 |
| **风险等级** | 低（纯检测增强，无破坏性操作） |

## 一、文本文件变更清单

### 1. 新建 `references/env-migrations/env-migration-jsonl-lint-integration-2026-08-07-123115.md`

| 属性 | 值 |
|------|-----|
| **变更类型** | 新建 |
| **作用** | 本文件，记录本次 session 完整变更 |

### 2. 修改 lint 插件体系

| # | 文件路径 | 变更类型 | 说明 |
|---|---------|---------|------|
| 1 | `scripts/py-plugins/lint_encoding.py` | 修改 | `NO_BOM_EXTENSIONS` 追加 `.jsonl`（1 行），使 `.jsonl` 获得 UTF-8 no BOM + LF 强制检测 |
| 2 | `scripts/py-plugins/lint_json.py` | 修改 | 新增 `_check_jsonl_file()`：标准库 `json.loads` 逐行验证 + `jsonlines.Reader` 双重检测；支持注释行（`#` 开头）跳过；目录扫描 `rglob("*.jsonl")` 追加 |
| 3 | `scripts/py-tools/run-lint.py` | 修改 | `EXT_TO_PLUGIN` 追加 `.jsonl: ["lint_json", "lint_encoding"]`（1 行），语法+编码双重检查 |

### 3. 修复文件

| # | 文件路径 | 变更类型 | 说明 |
|---|---------|---------|------|
| 1 | `skills/rg-fd-search/versions/audit-trail.jsonl` | 修复 | 通过 `run-lint.py --fix` 三阶段闭环：CRLF=1 → CRLF=0，LF=6 → LF=7，编码+语法全部通过 |

## 二、非文本操作

| 操作类型 | 说明 |
|---------|------|
| 规范调研 | jsonlines.org 官方规范、ndjson/ndjson-spec、wbolster/jsonlines Python 库文档，3 渠道交叉验证 |
| 包安装 | `jsonlines` Python 库已安装（用户手工执行） |

## 三、Session 踩坑与纠偏记录

| # | 踩坑 | 现象 | 纠偏 |
|---|------|------|------|
| 1 | **手写临时脚本修复 `.jsonl` CRLF** | 未使用 run-lint --fix，而是写 `venv/tmp/fix-jsonl-crlf.py` 直接修改文件 | **用户严厉批评**："自己的事自己决定，不要依赖别人是怎么做的"，且违反 lint-fix 铁律。改为用 run-lint --fix 三阶段闭环修复 |
| 2 | lint_json 的 `.jsonl` 验证未跳过注释行 | 首次实现时 `_check_jsonl_file` 未处理 `#` 开头的注释行，导致 `audit-trail.jsonl` 前 4 行注释被报语法错误 | 标准库验证分支追加 `if line.strip().startswith("#"): continue`；jsonlines 层改为先过滤注释行再传给 Reader |
| 3 | jsonlines.Reader 直接读文件时含注释行报错 | `jsonlines.open(filepath)` 不识别注释行，会把 `# audit-trail.jsonl` 当作 JSON value 解析 | 改为手动 `open()` 读取并过滤注释行后，用 `jsonlines.Reader(lines)` 验证 |

## 四、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 lint_encoding 认识 `.jsonl` | `rg "jsonl" lint_encoding.py` | 命中 `NO_BOM_EXTENSIONS` |
| 2 | 确认 lint_json 认识 `.jsonl` | `rg "jsonl" lint_json.py` | 命中 `_check_jsonl_file` + `rglob` |
| 3 | 确认 run-lint 路由 `.jsonl` | `rg "jsonl" run-lint.py` | 命中 `EXT_TO_PLUGIN` |
| 4 | audit-trail 三阶段闭环 | `run-lint.py --files audit-trail.jsonl --fix` | Phase1 报 CRLF → Phase2 修复 → Phase3 全部通过 |
| 5 | lint 插件自身合规 | `run-lint.py --files lint_encoding.py lint_json.py run-lint.py` | 全部通过 |

## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 lint_encoding.py | 从 `NO_BOM_EXTENSIONS` 中删除 `".jsonl"` |
| 恢复 lint_json.py | 删除 `_check_jsonl_file()`、`_check_file()`、还原 `rglob` 列表、还原循环体调用 |
| 恢复 run-lint.py | 从 `EXT_TO_PLUGIN` 中删除 `".jsonl"` 条目 |
| 恢复 audit-trail.jsonl | 无法精确回滚（CRLF 已修复），但修复前版本在 git 历史中存在 |

## 六、.jsonl lint 规则速查（沉淀为规范）

| 检查项 | 负责插件 | 合规标准 | 自动修复 |
|--------|---------|---------|---------|
| UTF-8 no BOM | lint_encoding | BOM=no, DOUBLE_BOM=no | 去 BOM |
| LF 换行符 | lint_encoding | CRLF=0, LF>0 | CRLF→LF |
| UTF-8 完整性 | lint_encoding | 无截断/损坏字节 | 不可自动修复 |
| 每行有效 JSON | lint_json | 无 JSONDecodeError | 不可自动修复 |
| 无空行 | lint_json | blank line → 违规 | 不可自动修复 |
| 注释行 | lint_json | `#` 开头行允许跳过 | N/A |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-07-123115 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指出 skill SED 演进产生 `.jsonl` 文件，要求 run-lint 纳入 `.jsonl` lint-fix 体系 |
| **下次修订条件** | 当 `.jsonl` 规范新增检查项或 jsonlines 库版本升级时 |
| **跨环境迁移参考** | 直接复制 lint_encoding.py / lint_json.py / run-lint.py 的改动；确保 `jsonlines` 库已安装 |

*文档生成时间：2026-08-07*
*模板版本：env-migration-template.md v2*
