---
title: gh_cli 集成与运行时工具链泛化重构
description: 本次 session 完成 gh_cli 隔离部署，并对 upstream_checker/download-runtime-tool 进行泛化重构，实现 GitHub Release 类工具零代码注册
date: 2026-06-30
meta:
  version: 1.0.0
  category: env-migration
---

# env-migration-gh-cli-runtime-toolchain-generalization-2026-06-30-113721

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | gh_cli 集成与运行时工具链泛化重构 |
| **日期** | 2026-06-30 |
| **文件名时间戳** | `2026-06-30-113721` |
| **触发原因** | 用户探索 PR merge 自动化闭环，需要先部署 gh CLI；发现现有下载工具 choices 硬编码，新增工具必须改 py |
| **影响范围** | 运行时工具链（upstream_checker.py、download-runtime-tool.py、tools_config.json）、verified-runtime-index.json、venv/gh/ 隔离部署 |
| **风险等级** | 中（重构上游查询逻辑，需验证既有工具行为一致） |


## 一、文本文件变更清单

### 1. 修改 `references/runtime/runtime_modules/upstream_checker.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/upstream_checker.py` |
| **变更类型** | `重构` |
| **新增/修改内容** | 新增 `_query_github_release(owner, repo, target_version)` 通用方法；`query()` 方法新增 `elif "/" in query_param:` 分支识别 `owner/repo` 格式；`_query_opencode()` 简化为 wrapper 调用通用方法 |
| **作用** | GitHub Release 类工具（gh_cli、opencode_cli、llama_cpp_python 等）无需硬编码即可查询上游版本 |
| **验证方式** | 单元测试：分别查询 `cli/cli`、`anomalyco/opencode`、`llama_cpp_python`，确认返回版本号和 asset 正确 |
| **迁移方式** | 直接覆盖 |

### 2. 修改 `references/runtime/runtime_config/tools_config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/tools_config.json` |
| **变更类型** | `修改 + 追加` |
| **新增/修改内容** | `opencode_cli.upstream.query_param` 从 `"opencode_cli"` 改为 `"anomalyco/opencode"`（走通用路径）；新增 `gh_cli` 完整条目 |
| **作用** | 将工具注册信息外化到 JSON，download-runtime-tool.py 启动时动态读取 |
| **验证方式** | `download-runtime-tool.py --help` 显示 choices 包含 gh_cli |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `references/runtime/download-runtime-tool.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-runtime-tool.py` |
| **变更类型** | `重构` |
| **新增/修改内容** | 新增 `_load_tools_config()` 动态读取工具列表；`choices` 从硬编码 7 项改为动态 `valid_tool_names`；`FIXED_VERSIONS` 硬编码移除，改为从 `tools_config.json` 的 `upstream.target_version` 读取；修复 `preferred_proxy = args.proxy` 回归 |
| **作用** | 新增工具只需在 tools_config.json 中登记，无需修改 Python 代码 |
| **验证方式** | `--help` 显示全部 9 个工具；下载 gh_cli 成功 |
| **迁移方式** | 直接覆盖 |

### 4. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `追加` |
| **新增/修改内容** | 在 `toolchain` 节追加 `gh_cli` 完整条目（含 executable、version、download_url_template、upstream_sources、candidate_paths 等） |
| **作用** | 登记 gh CLI 为运行时工具链成员，供 Agent 速查引用 |
| **验证方式** | run-lint.py 验证 JSON 语法通过 |
| **迁移方式** | 直接追加 |


## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 下载 | GitHub Release cli/cli v2.95.0 | `D:\download\gh_cli-2.95.0.zip` | 14.13 MB，直连下载 36.2s |
| 解压 | `D:\download\gh_cli-2.95.0.zip` | `D:\download\gh_cli-2.95.0-extracted` | 临时解压目录 |
| 复制 | `D:\download\gh_cli-2.95.0-extracted\bin\gh.exe` | `D:\pjt\cursor\cs_py\venv\gh\bin\gh.exe` | 隔离部署 |
| 目录创建 | — | `D:\pjt\cursor\cs_py\venv\data-gh` | gh CLI 隔离配置目录 |
| 清理 | `D:\download\gh_cli-2.95.0-extracted` + `.zip` | — | 临时文件删除 |


## 三、环境变量速查

gh CLI headless 调用时需在进程环境注入：

```powershell
$env:GH_TOKEN = $env:GITHUB_PAT                    # 从 .env 读取 PAT
$env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"     # 隔离配置目录
```


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py --fix` | frontmatter、CRLF/LF、BOM | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.json`（tools_config.json / verified-runtime-index.json） | `run-lint.py` | JSON 语法正确性 | `[OK]` 无解析错误 |
| `.py`（upstream_checker.py / download-runtime-tool.py） | `run-lint.py` | Python 语法 + 编码 | `[OK]` 无解析错误 |

**执行结果**：全部通过，0 违规。


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 gh.exe 存在 | `Test-Path "${devroot}\venv\gh\bin\gh.exe"` | `True` |
| 2 | 确认 gh.exe 版本 | `& "${devroot}\venv\gh\bin\gh.exe" --version` | `gh version 2.95.0` |
| 3 | 确认上游查询泛化 | `python -c "from upstream_checker import UpstreamChecker; print(UpstreamChecker().query('gh_cli', 'cli/cli'))"` | `upstream_version: 2.95.0` |
| 4 | 确认 choices 动态 | `download-runtime-tool.py --help` | 列表包含 `gh_cli` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 gh_cli 索引 | 从 `verified-runtime-index.json` 的 `toolchain` 节删除 `gh_cli` 条目 |
| 移除 gh_cli 配置 | 从 `tools_config.json` 的 `tools` 数组删除 `gh_cli` 条目 |
| 删除隔离部署 | `Remove-Item -Recurse "${devroot}\venv\gh"` |
| 删除隔离配置 | `Remove-Item -Recurse "${devroot}\venv\data-gh"` |
| 恢复旧 choices（如需） | 回退 `download-runtime-tool.py` 到硬编码 choices 版本 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-30-113721 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户探索 PR merge 自动化闭环，触发 gh CLI 部署需求；同时发现运行时下载工具 choices 硬编码问题 |
| **下次修订条件** | 新增更多 GitHub Release 类工具时验证泛化是否仍有效；或 gh CLI 版本更新时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
