---
title: env-migration — tavily-cli 工具链接入与 .env 环境变量配置
description: 本次 session 将 tavily-cli 接入项目隔离 Python 环境，并在 .env 中配置 TAVILY_API_KEY，同时扩展真源检测 candidate_paths 结构。
date: 2026-06-08
---

# `env-migration-tavily-cli-toolchain-2026-06-08-164500.md`

> **文档性质**：环境迁移指南。聚焦 tavily-cli 工具链的安装、配置与验证。  
> **受众**：Human + Agent。在新环境复现 tavily-cli 可用性。


## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | tavily-cli 工具链接入与 .env 环境变量配置 |
| **日期** | 2026-06-08 |
| **文件名时间戳** | `2026-06-08-164500` |
| **触发原因** | 用户注册 Tavily 账户，希望将 tavily-cli 作为隔离版搜索工具接入项目 |
| **影响范围** | 工具链（venv/py/）、环境变量（.env）、真源检测索引 |
| **风险等级** | 低（tavily-cli 为纯 Python pip 包，无系统级副作用） |


## 一、文本文件变更清单

### 1. 修改 `.env`

| 属性 | 值 |
|------|-----|
| **路径** | `.env` |
| **变更类型** | `追加` |
| **新增内容** | `TAVILY_API_KEY=tvly-xxx`（用户自行填入真实 key） |
| **插入位置** | 文件末尾，Minimax 配置之后 |
| **作用** | 为 tavily-cli 及 Tavily Python SDK 提供 API 认证 |
| **验证方式** | `tvly auth --json` 应返回 `{"authenticated": true}` |
| **迁移方式** | 仅需追加行 |

> **注意**：`.env` 中的 key 为占位符 `tvly-your_key_here`，新环境需替换为真实 API key。


### 2. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改` |
| **新增内容** | `chromium.candidate_paths` 数组（含 `exe_name: chrome.exe`）；`cursor.candidate_paths` 补全 `exe_name: Cursor.exe` |
| **作用** | 让真源检测脚本通用化，候选路径的可执行文件名随 JSON 数据携带 |
| **验证方式** | 执行 `verify-runtime.ps1`，`chromium.candidate[custom_toolchain]` 应命中 |
| **迁移方式** | 仅数据结构扩展，无需手动操作 |


### 3. 修改 `references/runtime/verify-runtime.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime.ps1` |
| **变更类型** | `修改` |
| **修改内容** | `candidate_paths` 扫描逻辑从硬编码 `"Cursor.exe"` 改为读取 `$candidate.exe_name` |
| **作用** | 消除脚本硬编码，以后新增工具的 `candidate_paths` 无需改脚本 |
| **验证方式** | 执行真源检测，所有 candidate_paths 扫描通过 |
| **迁移方式** | 直接覆盖 |


### 4. 修改 `.cursor/rules/high-frequency-verify-runtime.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-verify-runtime.mdc` |
| **变更类型** | `追加` |
| **新增内容** | 第 2 节「修订联动义务」，明确真源检测后需同步 `PROJECT-STRUCTURE.md` / `schema/` / README 导航 |
| **作用** | 规范化 Agent 执行真源检测后的后续动作 |
| **迁移方式** | 直接覆盖或追加 |


### 5. 修改 `.cursor/rules/high-frequency-update-version.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-update-version.mdc` |
| **变更类型** | `追加` |
| **新增内容** | §1.6「修订联动义务」，新增版本文件时需检查 `venv/version/` 导航 |
| **作用** | 补全版本记录任务的导航联动义务 |
| **迁移方式** | 直接追加 |


### 6. 修改 `.cursor/rules/high-frequency-project-handoff.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-project-handoff.mdc` |
| **变更类型** | `追加` |
| **新增内容** | 第 2 节「修订联动义务」，handoff 后需同步 DESIGN.md / handoffs 导航索引 |
| **作用** | 规范化 handoff 任务的文档联动 |
| **迁移方式** | 直接追加 |


### 7. 修改 `.cursor/rules/high-frequency-env-migration.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-env-migration.mdc` |
| **变更类型** | `修改` |
| **修改内容** | 升格「登记义务」为正式「修订联动义务」章节 |
| **作用** | 与 project-handoff 等 mdc 对齐，统一修订联动语义 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作（工具链安装）

本次 session 涉及 tavily-cli 的安装（用户手工执行）。

| 操作类型 | 命令 | 说明 |
|---------|------|------|
| pip 安装 | `python.exe -m pip install tavily-cli` | 安装到项目隔离 Python 环境 `venv/py/` |
| 依赖自动解决 | `tavily-python` 等 | pip 自动安装依赖 |

### 复现命令

```powershell
# 使用项目隔离 Python
& "${devroot}\venv\py\python.exe" -m pip install tavily-cli

# 验证安装
& "${devroot}\venv\py\Scripts\tvly.exe" --version
# 期望输出：tavily-cli 0.1.4

# 验证 keyless 搜索
& "${devroot}\venv\py\Scripts\tvly.exe" search "test" --json

# 验证 API key 搜索（需先设置环境变量）
$env:TAVILY_API_KEY = "tvly-你的key"
& "${devroot}\venv\py\Scripts\tvly.exe" auth --json
& "${devroot}\venv\py\Scripts\tvly.exe" search "AI agents" --json
```

> **注意**：`tvly` 命令若不在 PATH 中，需使用完整路径 `${devroot}\venv\py\Scripts\tvly.exe`。


## 三、环境变量速查

迁移到新环境后，打开 `.env` 确认以下变量已配置：

```bash
# Tavily (AI Search API)
# 注册/获取 Key: https://app.tavily.com/home
TAVILY_API_KEY=tvly-your_key_here
```

同时，`.vscode/settings.json` 中的 `terminal.integrated.env.windows` 应能自动加载 `.env`（若项目已配置 dotenv 注入）。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 tvly 命令可用 | `tvly --version` | 输出 `tavily-cli 0.1.4` |
| 2 | 确认 keyless 搜索可用 | `tvly search "test" --json` | 返回 JSON 结果（不报错） |
| 3 | 确认 API key 认证 | `tvly auth --json` | `{"authenticated": true}` |
| 4 | 确认 API key 搜索可用 | `tvly search "AI" --json` | 返回结构化搜索结果 |
| 5 | 确认 .env 变量已加载 | `$env:TAVILY_API_KEY` | 输出非空的 key 值 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 卸载 tavily-cli | `python.exe -m pip uninstall tavily-cli` |
| 移除环境变量 | 从 `.env` 中删除 `TAVILY_API_KEY` 行 |
| 清理配置（如有） | `tvly logout`（清除本地存储的凭据） |


## 六、已知限制

| 限制项 | 说明 |
|--------|------|
| **额度查询** | Tavily CLI **不支持**通过命令行查询剩余 credits，只能去 Web Dashboard (`https://app.tavily.com/home`) 查看 |
| **Free Plan 额度** | 1,000 credits/月，每月 1 号重置 |
| **keyless 限速** | 搜索和提取支持 keyless，但有 fair-use rate limit；达到上限后需登录 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-08-164500 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户注册 Tavily 账户，要求评估并接入 tavily-cli |
| **下次修订条件** | tavily-cli 升级、Tavily API 变更、或迁移到更隔离的 `venv/tavily/` 目录 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-08*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
