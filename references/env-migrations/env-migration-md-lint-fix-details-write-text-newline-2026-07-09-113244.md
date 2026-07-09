---
title: env-migration — md-lint 修复明细输出改造与 write_text 换行符陷阱修复
description: md_lint 插件增加修复明细输出能力，run-lint Phase 2 展示改造；发现并修复 Python write_text/open 在 Windows 下默认把 LF 转回 CRLF 的根因缺陷。
date: 2026-07-09
meta:
  version: "1.0.0"
  timestamp: "2026-07-09-113244"
---

# env-migration-md-lint-fix-details-write-text-newline-2026-07-09-113244

| 字段 | 值 |
|------|-----|
| **Session 主题** | md-lint 修复明细输出改造 + write_text 换行符陷阱修复 |
| **日期** | 2026-07-09 |
| **文件名时间戳** | 2026-07-09-113244 |
| **触发原因** | 版本记录更新后 `--fix` 修复 CRLF 异常增加，排查发现 md_lint write_text 在 Windows 下默认把 LF 转回 CRLF |
| **影响范围** | py-plugins/md_lint.py、py-tools/run-lint.py、baseline/baseline-formats.md |
| **风险等级** | 中（影响多插件串行修复的一致性，已修复） |


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| **变更类型** | 修改（功能增强 + 缺陷修复） |
| **版本** | v1.3.0 → v1.4.0 |
| **新增能力** | `_fix_frontmatter_fields` / `_fix_content` 返回 `(fixed_content, fix_actions)` 二元组，记录每行修复动作 |
| **新增字段** | `metadata.fix_details`：按文件聚合的修复明细列表 |
| **缺陷修复** | 两处 `write_text` 追加 `newline="\n"`，防止 Windows 下 LF 被转回 CRLF |
| **作用** | Phase 2 修复时输出精确到行号的修复明细；消除多插件串行修复的换行符覆盖问题 |
| **验证方式** | `run-lint.py --files md_lint.py` → lint_python / lint_encoding 全部通过 |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | 修改（输出增强） |
| **版本** | v1.4.0 → v1.5.0 |
| **新增输出** | Phase 2 增加【待修复文件】列表和【修复明细】按文件分组展示 |
| **输出示例** | `📄 test.md`<br>`  └─ [md_lint] 第 5 行: 插入 meta: {}` |
| **作用** | 修复后可直接看到每个文件改了什么，便于定位修复缺陷 |
| **验证方式** | `run-lint.py --files run-lint.py` → lint_python / lint_encoding 全部通过 |

### 3. 修改 `references/tasks/deploy-git-isolated/baseline/baseline-formats.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-formats.md` |
| **变更类型** | 追加章节 |
| **新增章节** | 3.7.4「Python `write_text` / `open` 的换行符陷阱（Windows）」 |
| **内容** | 记录 `pathlib.write_text()` / `open()` 在 Windows 下默认 `newline=None` 把 `\n` 转 `\r\n` 的根因、影响范围、硬性规定、代码示例 |
| **章节调整** | 原 3.7.4「`.gitattributes` 的跟踪策略」→ 顺延为 3.7.5 |
| **验证方式** | `run-lint.py --files baseline-formats.md` → md_lint / lint_encoding 全部通过 |


## 二、非文本操作

本次 session 无不涉及文件复制、缓存迁移等非文本操作。


## 三、环境变量速查

无新增或变更环境变量。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py --profile lint-encoding` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.py` | `run-lint.py --profile lint` | Python 语法 + encoding | py_compile 通过, CRLF=0 |

执行示例：
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-md-lint-fix-details-write-text-newline-2026-07-09-113244.md"
```


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 md_lint 版本 | 读取 `md_lint.py` 头部注释 | 版本号 ≥ v1.4.0 |
| 2 | 确认 run-lint 版本 | 读取 `run-lint.py` 头部注释 | 版本号 ≥ v1.5.0 |
| 3 | 修复明细输出测试 | 创建缺少 meta 的 `.md` 文件，执行 `run-lint.py --fix` | Phase 2 输出包含【修复明细】，精确到行号 |
| 4 | CRLF 修复一致性 | 创建纯 CRLF 的 `.md` 文件（缺少 meta），执行 `--fix` | Phase 3 CRLF=0，LF>0，无残留 CRLF |
| 5 | baseline 记录完整性 | 打开 `baseline-formats.md` 搜索「write_text」 | 存在 3.7.4 章节，含现象/根因/硬性规定/代码示例 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 还原 md_lint.py | `git checkout -- references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| 还原 run-lint.py | `git checkout -- references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| 还原 baseline | `git checkout -- references/tasks/deploy-git-isolated/baseline/baseline-formats.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-09-113244 |
| **更新人** | Human + Agent Session |
| **变更触发** | 版本记录更新后 `--fix` CRLF 异常增加，排查发现 md_lint write_text 覆盖前序插件 LF 修复成果 |
| **下次修订条件** | 新增需要修复明细输出的插件；发现新的 write_text/open 换行符边界场景 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
