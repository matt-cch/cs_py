---
title: verify-runtime 重构为模块化 Python 架构 + Chromium 上游源修正
description: 将 PowerShell 真源检测脚本重构为 Python 模块化架构，新增构建号缓存机制修正 Chromium 上游源，Python 查询增加 <3.14 约束。
date: 2026-06-15
---

# verify-runtime 重构为模块化 Python 架构 + Chromium 上游源修正

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | verify-runtime 重构为模块化 Python 架构 + Chromium 上游源修正 + Python <3.14 约束 |
| **日期** | 2026-06-15 |
| **文件名时间戳** | `2026-06-15-131500` |
| **触发原因** | PowerShell 版 verify-runtime.ps1 已膨胀至 1000+ 行，维护困难；Chromium 上游源返回构建号无法与本地语义化版本比较；Python 3.14 预发布导致误报可更新 |
| **影响范围** | `references/runtime/` 脚本体系、上游查询模块、版本比较逻辑 |
| **风险等级** | 中（替换了核心检测入口，旧脚本保留未删除） |


## 一、文本文件变更清单

### 1. 新建 `references/runtime/verify-runtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime.py` |
| **变更类型** | `新建` |
| **作用** | 新主入口，约 115 行，分 3 步输出：加载配置 → 检测工具链 → GitHub 连通性 |
| **验证方式** | `D:\pjt\cursor\cs_py\venv\py\python.exe D:\pjt\cursor\cs_py\references\runtime\verify-runtime.py` |
| **迁移方式** | 直接复制到新环境 |


### 2. 新建 `references/runtime/runtime_modules/local_verifier.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/local_verifier.py` |
| **变更类型** | `新建` |
| **作用** | 本地 exe 存在性检测与版本获取，复用 `schema/tool/get-runtime-version.py` |
| **迁移方式** | 直接复制 |


### 3. 新建 `references/runtime/runtime_modules/upstream_checker.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/upstream_checker.py` |
| **变更类型** | `新建` |
| **作用** | 上游无条件查询（纯 Python，requests），支持构建号缓存（Chromium）、<3.14 约束（Python） |
| **迁移方式** | 直接复制 |


### 4. 新建 `references/runtime/runtime_modules/version_comparator.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/version_comparator.py` |
| **变更类型** | `新建` |
| **作用** | 语义化版本比较：本地 vs 上游 |
| **迁移方式** | 直接复制 |


### 5. 新建 `references/runtime/runtime_modules/report_generator.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/report_generator.py` |
| **变更类型** | `新建` |
| **作用** | stdout 进度表格 + JSON 报告落盘到 `runtime_reports/` |
| **迁移方式** | 直接复制 |


### 6. 新建 `references/runtime/runtime_config/tools_config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/tools_config.json` |
| **变更类型** | `新建` |
| **作用** | 高频变动的工具链配置（exe 路径、上游查询参数等） |
| **迁移方式** | 直接复制 |


### 7. 新建 `references/runtime/runtime_config/chromium_build_map.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/chromium_build_map.json` |
| **变更类型** | `新建` |
| **作用** | Chromium 构建号 → 语义化版本缓存，基准线 `r1627931 → 150.0.7834.0` |
| **迁移方式** | 直接复制，新环境首次运行若构建号大于缓存会自动下载更新 |


### 8. 新建 `schema/tool/get-runtime-version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-runtime-version.py` |
| **变更类型** | `新建` |
| **作用** | 通用版本检测脚本，替代 `python -c` / `node -e` 获取版本 |
| **迁移方式** | 直接复制 |


### 9. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改` |
| **作用** | 更新 python / node / opencode_cli / chromium / llama_cpp_python 版本与路径信息 |
| **迁移方式** | 在新环境运行 `verify-runtime.py` 会自动生成最新报告，无需手动复制 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 无目录迁移或缓存复制操作，全部为新文件创建。

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 目录创建 | — | `references/runtime/runtime_modules/` | 4 个 Python 模块 |
| 目录创建 | — | `references/runtime/runtime_config/` | 2 个 JSON 配置 |
| 目录创建 | — | `references/runtime/runtime_reports/` | JSON 报告输出（已存在） |


## 三、环境变量速查

无新增环境变量，所有路径通过 `tools_config.json` 中的 `${devroot}` / `${toolchainroot}` 变量解析。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 运行新 verify-runtime | `D:\pjt\cursor\cs_py\venv\py\python.exe D:\pjt\cursor\cs_py\references\runtime\verify-runtime.py` | 7 个工具全部检测完成，总耗时 < 10s |
| 2 | 确认 Python 上游过滤 | 查看 stdout 中 python 行 | 上游版本显示 `3.13.14`（而非 `3.14.6`） |
| 3 | 确认 Chromium 缓存命中 | 查看 stdout 中 chromium 行 | 上游版本 `150.0.7834.0`，耗时 < 1s，无下载 |
| 4 | 确认 report 落盘 | `Get-ChildItem "references/runtime/runtime_reports/"` | 存在 `verify-runtime-report-*.json` |
| 5 | 确认模块可导入 | `python -c "from runtime_modules.upstream_checker import UpstreamChecker"`（在 `references/runtime/` 目录下） | 无报错 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复旧入口 | 使用 `references/runtime/verify-runtime.ps1`（未删除，仍可用） |
| 删除新文件 | `Remove-Item -Recurse "references/runtime/verify-runtime.py", "references/runtime/runtime_modules", "references/runtime/runtime_config"` |
| 恢复旧索引 | 从 git 回滚 `references/runtime/verified-runtime-index.json` |


## 六、关键踩坑记录

### 6.1 Chromium 上游源陷阱

- **现象**：华为 chromedriver 镜像返回 `151.0.7891.0`，下载后发现是 chromedriver（驱动），不是 Chromium 浏览器。
- **根因**：chromedriver 和 Chromium 浏览器是两个独立产物，版本号虽接近但不同源。
- **修复**：改用淘宝 npmmirror `chromium-browser-snapshots`，建立构建号缓存机制。

### 6.2 Chrome for Testing 是另一条版本线

- **现象**：`googlechromelabs.github.io` 返回 `151.0.7891.0`（Canary），本地 snapshot `150.0.7834.0` 被误报为旧版。
- **根因**：Chrome for Testing（官方发布线）和 Chromium Snapshot（开发构建线）版本号不完全对齐。
- **修复**：上游查询锁定 snapshot 构建号，不用 Chrome for Testing API。

### 6.3 Python 3.14 误报

- **现象**：阿里云 python-release 已出现 `3.14.6` embed zip，本地 `3.13.14` 被误报可更新。
- **根因**：runtime 工具链限定 `<3.14`，但上游查询未过滤。
- **修复**：`_query_python` 增加 `tuple(int(p) for p in v.split('.')[:2]) < (3, 14)` 过滤。


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-15-131500 |
| **更新人** | Human + Agent Session |
| **变更触发** | verify-runtime.ps1 维护困难 + Chromium 上游源错误 + Python 3.14 预发布 |
| **下次修订条件** | 新增工具链工具、上游源失效、缓存基准线需更新 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-15*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
