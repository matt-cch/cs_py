---
title: deploy-git-isolated — SOP 重构 + Ralph Loop 自闭环框架落地
description: SOP 语义回归：scripts/SOP-CHEATSHEET.md 拆分为根目录 SOP.md（标准流程）+ scripts/EXEC-CHEATSHEET.md（执行速查）；新增 Step Manifest 结构与 Ralph Loop 自闭环框架；顶层原则声明置顶。
date: 2026-06-18
meta: {}
---

# deploy-git-isolated — SOP 重构 + Ralph Loop 自闭环框架落地

## 变更概览

| 属性 | 值 |
|------|-----|
| **变更类型** | Refactor（语义重构）+ Feature（新增框架） |
| **影响范围** | task 根目录下全部文档、ENTRY.json、scripts/ |
| **风险等级** | 中（涉及 10+ 文件的引用关系调整） |
| **触发原因** | 用户 review 发现 SOP 语义不统一（SOP-CHEATSHEET 实为纯命令速查，名不副实）；要求 SOP 回归「标准操作流程」本意，区分 SOP/EXEC-CHEATSHEET/TOOLS-INDEX 边界；要求最小执行单元 Ralph Loop 自闭环 |


## 变更时间线

### 2026-06-18 — SOP 语义重构与 Ralph Loop 框架落地

| 变更项 | 之前 | 之后 | 触发原因 |
|--------|------|------|---------|
| SOP 文件位置与命名 | `scripts/SOP-CHEATSHEET.md`（纯命令速查，名不副实） | `SOP.md`（task 根目录，标准流程：Step 契约）+ `scripts/EXEC-CHEATSHEET.md`（执行速查） | SOP 语义丢失：用户阅读顺序中 SOP 应体现标准流程，但原文件只是命令速查 |
| Step 节点契约 | 无（仅 GOAL.md 中有简单 Step 列表） | `SOP.md` 中每个 Step 定义 Input→Process→Output→Validation→Audit Trail→Rollback 六元契约 | 用户要求流程步骤可单独追踪审计校验，输出可预期一致 |
| Step Manifest（机器层） | `ENTRY.json` 只有 `scenarios` 和 `active_scripts` | `ENTRY.json` 新增 `step_manifests` 结构，每个 Step 含 input_schema/process_script/output_schema/validation_rules/audit_trail/rollback | Agent 执行一致性：机器可读真源必须与人类可读 SOP 对齐 |
| Stage 路线图 | `GOAL.md` 中只有简单 Step 列表 | `GOAL.md` 新增 Stage 表格（S1-S6），含完成标准与状态追踪 | 用户要求架构有边界、进度状态标识描述 |
| Ralph Loop 自闭环 | 无（GOAL.md 有回滚方案，但无统一框架） | `SOP.md` 第 0 节定义 Ralph Loop 框架；每个 Step 均含 Audit Trail + Rollback；`GOAL.md` 第 6 节新增 Ralph Loop 结构说明 | 用户要求最小执行单元自闭环贯彻工程化原则 |
| Agent 执行哲学 | `task-canonical-baseline.md` 第 8.4 节（末尾） | 移至第 0 节（顶层原则声明），前置到所有规范之前 | 用户要求顶层原则声明置顶，作为最高约束 |
| 调用操作符 | `powershell -ExecutionPolicy Bypass -File`（部分示例） | `& "..."`（PowerShell 调用操作符，规避引号解析歧义） | 统一 PowerShell 调用方式，避免 `cmd /c` workaround |
| 文件导航关系 | 多处引用 `SOP-CHEATSHEET.md` | 全面刷新为 `SOP.md` + `EXEC-CHEATSHEET.md`，三者语义明确区分 | 避免后续 task 演进因历史命名造成困扰 |


## 验证结果

| 检查项 | 结果 |
|--------|------|
| `ENTRY.json` JSON 语法检查（lint-json.py） | ✅ 通过 |
| `SOP.md` 已创建且可访问 | ✅ 确认 |
| `scripts/EXEC-CHEATSHEET.md` 已创建且可访问 | ✅ 确认 |
| `scripts/SOP-CHEATSHEET.md` 已删除 | ✅ 确认（Test-Path 返回 False） |
| 全 task 范围内 `SOP-CHEATSHEET` 引用扫描 | ✅ 全部替换为 `SOP.md`/`EXEC-CHEATSHEET.md`（历史记录/踩坑文件中的历史引用保留） |
| 内部相对链接有效性 | ✅ 全部验证通过（见下方链接验证详情） |


## 已知问题（待优化）

| 问题 | 说明 | 后续方向 |
|------|------|---------|
| Step Manifest 的 audit_trail.status 未与脚本实际执行联动 | 当前为静态 `pending` 占位，需后续在脚本中写入实际执行状态 | 用户确认后，在 `github-step-0N-*.ps1` 中增加 `ENTRY.json` 状态更新逻辑 |
| Ralph Loop 框架尚未在脚本层强制校验 | 当前是文档约束，脚本中未强制检查 Input/Validation | 后续可在 `github-lib.ps1` 中增加 `Assert-StepInput` / `Assert-StepOutput` 通用函数 |
| GOAL.md 的 Stage 状态未与 ENTRY.json 自动同步 | 当前为静态表格，跨 session 接续时需手动更新 | 后续可通过脚本自动同步 `ENTRY.json` → `GOAL.md` |


## 关联文件

| 文件 | 变更状态 |
|------|---------|
| `SOP.md` | ✅ 新建（标准流程 + Step 契约 + Ralph Loop） |
| `scripts/EXEC-CHEATSHEET.md` | ✅ 新建（执行速查，从 SOP-CHEATSHEET 更名） |
| `scripts/SOP-CHEATSHEET.md` | ✅ 已删除（内容拆分至 SOP.md + EXEC-CHEATSHEET.md） |
| `ENTRY.json` | ✅ 已修改（v0.8.0，新增 step_manifests、sop、exec_cheatsheet 字段） |
| `GOAL.md` | ✅ 已修改（新增 Stage 路线图、Ralph Loop 结构） |
| `README.md` | ✅ 已修改（导航刷新、当前状态表更新） |
| `task-canonical-baseline.md` | ✅ 已修改（目录结构、格式规范、联动规则、执行路径全面刷新；顶层原则置顶） |
| `TASK-TOOLS-INDEX.md` | ✅ 已修改（顶部区别说明、底部关联导航） |
| `docs/TASK-GUIDE.md` | ✅ 已修改（真源契约、执行路径对照） |
| `docs/patterns/manifest-plugin-pattern.md` | ✅ 已修改（关联文件导航） |
| `docs/harness/delivery-checklist.md` | ✅ 已修改（交付清单） |
| `docs/playbooks/github-publish-playbook.md` | ✅ 已修改（发布手册） |
| `scripts/py_lib.py` | ✅ 新建（Python 插件聚合入口：拓扑排序 + 标签筛选 + devroot 路径解析） |
| `scripts/py-sort-rules.json` | ✅ 新建（Python 插件配置） |
| `scripts/py-plugins/link_checker.py` | ✅ 新建（Markdown 链接验证插件） |
| `scripts/py-tools/check-links.py` | ✅ 新建（Markdown 链接验证 CLI 工具，走 py_lib 入口示范） |
| `scripts/py-examples/usage-demo.py` | ✅ 新建（py_lib 插件体系用法示例） |
| `ENTRY.json` | ✅ 已修改（新增 Python 插件登记，目录重构后路径更新） |
| `scripts/EXEC-CHEATSHEET.md` | ✅ 已修改（所有脚本路径更新为 ps-steps/ / ps-tools/） |
| `README.md` | ✅ 已修改（脚本路径更新） |
| `task-scenario-triggers.json` | ✅ 已修改（entry_script 路径更新） |


## scripts/ 目录子分类重构

> 触发原因：用户 review 指出 scripts/ 根下 20+ 文件摊平，Agent 速查困难，要求按 `ps-steps/`, `ps-tools/`, `ps-examples/`, `py-steps/`, `py-tools/`, `py-examples/` 分类。

### 分类后结构

```
scripts/
├── github-lib.ps1              # PS 入口（保留根下）
├── lib-sort-rules.json         # PS 配置（保留根下）
├── py_lib.py                   # Python 入口（保留根下）
├── py-sort-rules.json          # Python 配置（保留根下）
├── EXEC-CHEATSHEET.md          # 执行速查表
├── lib-plugins/                # PS 插件
├── py-plugins/                 # Python 插件
├── ps-steps/                   # Step 0-8 流程脚本
├── ps-tools/                   # PS 独立工具
├── ps-examples/                # PS 示例（预留）
├── py-steps/                   # Python 流程脚本（预留）
├── py-tools/                   # Python 独立工具
└── py-examples/                # Python 示例
```

### 影响文件

| 原路径 | 新路径 | 内部路径修复 |
|--------|--------|-------------|
| `scripts/github-step-0N-*.ps1` | `scripts/ps-steps/` | `Join-Path $PSScriptRoot "github-lib.ps1"` → `Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"` |
| `scripts/github-safety-check.ps1` | `scripts/ps-tools/` | 同上 |
| `scripts/github-sync-issue.ps1` | `scripts/ps-tools/` | 同上 |
| `scripts/git-*.ps1` | `scripts/ps-tools/` | 无内部引用变更 |
| `scripts/github-create-issue.ps1` | `scripts/ps-tools/` | 无内部引用变更 |
| `scripts/github-init-empty-repo.ps1` | `scripts/ps-tools/` | 无内部引用变更 |
| `scripts/github-sync-issue-config.json` | `scripts/ps-tools/` | 无内部引用变更 |

### 下游同步

- `ENTRY.json`：active_scripts / step_manifests / maintenance_scripts 全部路径更新；新增 `check-links.py` 和 `usage-demo.py` 登记
- `EXEC-CHEATSHEET.md`：所有命令示例路径更新
- `README.md`：脚本索引表路径更新
- `task-scenario-triggers.json`：entry_script 路径更新

*变更日期: 2026-06-18*  
*记录人: Agent*  
*下次触发条件: Step Manifest 与脚本执行联动 / Ralph Loop 在脚本层强制校验 / Python 插件成熟后提升为 schema/tool/py-lib/*
