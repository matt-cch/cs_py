---
title: env-migration — ai_summary 可配置化与 polyrepo 调用契约硬化
description: 记录 diff 截断阈值可配置化改造、--target 参数强制显式化、workflow-poly 完整执行验证。
date: 2026-07-10
---

# `env-migration-ai-summary-configurable-and-target-required-2026-07-10-125144.md`

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | ai_summary 可配置化与 polyrepo 调用契约硬化 |
| **日期** | 2026-07-10（frontmatter；文件名时间戳见上表） |
| **文件名时间戳** | `2026-07-10-125144` |
| **触发原因** | ① diff 截断阈值 12000 硬编码在 256k context 模型下严重过度截断；② `--target` 参数"可省略、默认回退 devroot"的设计导致新 session 极易遗漏传入，引发 polyrepo 上下文歧义 |
| **影响范围** | `generate-ai-summary.py`（AI 摘要工具）、`workflow-git-deploy-full-poly.py`（workflow 编排器）、`atomic-deploy-preflight.py` / `atomic-polyrepo-context-manifest.py`（原子脚本）、`tools_config.json`（运行时配置） |
| **风险等级** | 中（Breaking Change：所有上游调用方必须同步传 `--target`，否则直接失败） |


## 一、文本文件变更清单

### 1. 修改 `references/runtime/runtime_config/tools_config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/tools_config.json` |
| **变更类型** | 追加 |
| **新增内容** | `ai_summary` 配置节：`{"max_diff_chars": 80000, "model_context_limit": 256000, "target_utilization_ratio": 0.2, "notes": "..."}` |
| **作用** | 将 AI 摘要 diff 截断策略外部化为可配置文件，与 `download.min_speed_mbps` 同构 |
| **验证方式** | 执行 `generate-ai-summary.py` 时 stdout 输出 `[Config] diff 截断阈值: 80000 (来源: tools_config)` |
| **迁移方式** | 直接追加到 JSON 文件（注意：此文件被 `.gitignore` 的 `/references/*` 规则忽略，**不会进入 git commit**。跨环境迁移需手动复制或重建） |

> **⚠️ 重要**：`tools_config.json` 被 `.gitignore` 忽略，属于"环境级配置"而非"源码"。新环境复现时，需手动检查此文件是否存在 `ai_summary` 配置节；若缺失，按上方内容追加。

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | ① 新增 `_load_tools_config()` 函数读取 `tools_config.json` 的 `ai_summary` 节；② `generate_summary` 新增 `max_diff_chars` 参数（默认 80000）；③ 截断逻辑改为 `effective_max = max_diff_chars if max_diff_chars > 0 else diff_len`（0 表示不截断）；④ 新增 `--max-diff-chars` CLI 参数；⑤ `--target` 改为 `required=True`，help 删除"默认等于 --devroot"；⑥ diff audit `diff_stats` 新增 `threshold`、`threshold_source`、`is_truncated_for_prompt`、`truncated_at` |
| **作用** | diff 截断阈值三层覆盖（CLI > tools_config > 默认值），消除硬编码；强制显式传 `--target` |
| **验证方式** | ① 不传 `--target` 时 argparse 直接报错；② 不传 `--max-diff-chars` 时读取 tools_config.json 的 80000 |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | ① docstring 第 10 行："省略时默认等于工具链根（单仓库场景）" → "必须传入（即使与 --devroot 相同）"；② argparse `--target` 改为 `required=True`，help 明确"polyrepo 调用契约要求，必须显式传入" |
| **作用** | 从文档和代码层面双重消除"可省略"的暗示 |
| **验证方式** | 不传 `--target` 时 argparse 报错：`error: the following arguments are required: --target` |
| **迁移方式** | 直接覆盖 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | `--target` 改为 `required=True`；移除 `if args.target else devroot` 回退逻辑 |
| **作用** | 与 workflow-poly 调用契约对齐 |
| **验证方式** | 不传 `--target` 时 argparse 报错 |
| **迁移方式** | 直接覆盖 |

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-polyrepo-context-manifest.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-polyrepo-context-manifest.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | `--target` 改为 `required=True`；移除 `if args.target else toolchain_root` 回退逻辑 |
| **作用** | 与 workflow-poly 调用契约对齐 |
| **验证方式** | 不传 `--target` 时 argparse 报错 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 不涉及文件复制、缓存迁移、目录创建等非文本操作。

运行时审计产物由 workflow-poly 自动生成到 `venv/tmp/`，不属于需要迁移的操作。


## 三、环境变量速查

本次 session 未新增或修改环境变量。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py`（全部修改） | `run-lint.py` lint_python | Python 语法解析 | 通过 |
| `.json`（tools_config.json） | `run-lint.py` lint_json | JSON 语法正确性 | 通过 |
| `.md`（本文件） | `run-lint.py` md_lint + lint_encoding | frontmatter + 编码/BOM/换行符 | 通过 |

**实际执行结果**：
```
总扫描文件: 10 个
总违规项: 0 处
结论: ✅ 全部通过
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 tools_config.json 含 ai_summary 节 | `Select-String -Path "...\tools_config.json" -Pattern "ai_summary"` | 命中 |
| 2 | 确认 generate-ai-summary.py 中 --target 为 required | `Select-String -Path "...\generate-ai-summary.py" -Pattern "required=True"` | 命中 `--target` 行 |
| 3 | 确认 workflow-poly 中 --target 为 required | `Select-String -Path "...\workflow-git-deploy-full-poly.py" -Pattern "required=True"` | 命中 `--target` 行 |
| 4 | 执行 generate-ai-summary.py 不传 --target | `python generate-ai-summary.py --devroot "${devroot}"` | argparse 报错：`--target` is required |
| 5 | 执行 workflow-poly 不传 --target | `python workflow-git-deploy-full-poly.py --devroot "${devroot}"` | argparse 报错：`--target` is required |
| 6 | 确认 diff 截断阈值读取自 tools_config | `python generate-ai-summary.py --devroot "${devroot}" --target "${devroot}" --cached` | stdout 出现 `[Config] diff 截断阈值: 80000 (来源: tools_config)` |
| 7 | 确认 diff audit 含 threshold_source | `Get-Content "...\diff-audit-*.json" | ConvertFrom-Json` | `diff_stats.threshold_source` 存在且为 `tools_config`/`cli`/`default` 之一 |
| 8 | 执行 workflow-poly 完整链路 | `python workflow-git-deploy-full-poly.py --devroot "${devroot}" --target "${devroot}"` | Step 0-10 全部通过，commit 成功，push 成功 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 tools_config.json | 删除 `ai_summary` 配置节 |
| 恢复 generate-ai-summary.py | 从 git 历史检出旧版本（v1.0.0 之前） |
| 恢复 workflow-poly.py | 从 git 历史检出 v1.2.0 之前的版本 |
| 恢复 atomic-deploy-preflight.py | 从 git 历史检出旧版本 |
| 恢复 atomic-polyrepo-context-manifest.py | 从 git 历史检出旧版本 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-10-125144 |
| **更新人** | Human + Agent Session |
| **变更触发** | diff 截断阈值硬编码导致 256k 模型能力严重浪费；--target 可省略设计导致跨 session 调用遗漏 |
| **下次修订条件** | ① 新增其他 ai_summary 配置项（如 temperature、model 切换）；② 发现新的 polyrepo 调用契约缺陷 |
| **跨环境迁移参考** | ① 复制 tools_config.json 的 ai_summary 配置节；② 确保 4 个 py 文件已更新；③ 按「验证清单」逐条执行 |


*文档生成时间：2026-07-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
