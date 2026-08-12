---
title: py-tools 目录索引
description: deploy-git-isolated task 的 Python Workflow 脚本与插件目录自说明。含全部脚本清单、py-plugins 插件清单、三层调用规则与使用速查。
date: 2026-07-07
meta:
  version: 1.0.0
---

# py-tools 目录说明

本目录是 `deploy-git-isolated` task 的 **Layer 3: Workflow 层**，存放可直接执行的 Python CLI 脚本（Workflow 入口）。所有脚本遵循「三层架构」：Workflow → py_lib → Plugins，禁止越级直接 import 插件。

> **关联目录**
> - 统一入口：`../py_lib.py`（Layer 2）
> - 底座插件：`../py-plugins/`（Layer 1）
> - 配置真源：`../py-sort-rules.json`（插件注册表 + Profile 定义）
> - 命令速查：`../EXEC-CHEATSHEET.md`


## 子目录 / 文件导航

### Workflow 脚本（直接可执行）

| 脚本 | 职责 | 典型场景 |
|------|------|---------|
| `run-lint.py` | **Lint 唯一入口**。全量 / 按 `--profile` / 按 `--files` 路由，支持 `--fix` 三阶段闭环、`--audit` 覆盖度审计 | 新建 / 更新文档后必执行 |
| `workflow-lint-amend-lint.py` | **编码修复闭环 Workflow**。通过 py_lib 调用 `lint_encoding` 修复后再次验证 | 编码问题发现后修复 |
| `workflow-security-audit.py` | **部署前敏感内容巡检**。组装 `security_audit` 插件的五 Phase 流程 | commit / push 前必执行 |
| `workflow-deploy-full.py` | **全链条部署 Workflow**。编排 Step 4-9（add → commit → remote → push → upstream → issue sync）| 完整 GitHub 部署流水线 |
| `workflow-gh-pr.py` | **PR 自闭环 Workflow**。编排 `gh-pr-create.py → gh-pr-merge.py`，AI 自动生成 title + body | 一键 PR 闭环 |
| `workflow-gh-preflight-demo.py` | **gh CLI preflight 验证 Demo**。演示 `gh_preflight` 插件用法，验证后查询 PR / Issue | 检测 GitHub 状态 |

### 独立工具脚本

| 脚本 | 职责 | 典型场景 |
|------|------|---------|
| `get-timestamp.py` | 时间戳生成 CLI。输出 `local_short` / `local_iso` / `utc_iso` / `filename_safe` 等格式 | 写入 .md / .json 的 date 字段 |
| `update-version.py` | **版本记录更新 Workflow**。自动发现 `venv/version/` 下工具 → 实测版本 → 对比 → 更新 `.md` + 追加 `*-history.md` | 记一版 version |
| `generate-ai-summary.py` | AI 语义摘要生成器。读取 git diff，调用 Agent 底层能力生成中文摘要；内部先调用 `atomic-agent-preflight.py` 探活 LLM | commit message 辅助 |
| `atomic-agent-preflight.py` | **Agent / LLM 探活预检原子**。初始化 AgentCore 后发送轻量级请求确认 LLM 可达，输出 JSON + 审计 manifest | AI 摘要前门禁、LLM 可用性验证 |
| `nanobot.py` | **极简 Agent CLI**。支持 ReAct 模式 + 工具调用 | workflow 集成 LLM |
| `fetch_issue.py` | 获取 GitHub Issue 完整内容（含评论）| Issue 内容查看 |
| `check-links.py` | Markdown 内部相对链接验证 | 文档链接检查 |
| `clone-repo.py` | 隔离环境 Git Clone + 自动设置 local identity | 克隆新仓库 |
| `screenshot_verifier.py` | URL 截图验证（Playwright）| 页面截图留档 |
| `atomic-check-chrome-session.py` | 🌐 **Chrome Session 登录态检测原子 CLI**。读取 Cookies DB，检测登录态标志 + TTL + 新鲜度，输出 A/B/C/D 四级结论，支持 `--output` manifest 落盘供 pipeline 复用 | 头条/GitHub 等域名登录态验证 |
| `chrome_extension_manager.py` | Chrome 扩展管理器（搜索 / 下载 CRX / 解压）| 管理浏览器扩展 |
| `atomic-npm-isolated-install.py` | **原子：npm 隔离安装**。将 npm 包安全安装到隔离目录，支持 Local（带 package.json）和 Global（单包）双模式。内置重组安全检查、CWD 切换检查、bin 可用性验证 | 安装 node 工具到隔离目录 |
| `atomic-npm-update.py` | **原子：npm 隔离更新**。在已有 Local 安装结构的隔离目录中安全更新 npm 包。支持精确版本锁定、semver 范围更新、全量更新。与 install 成对使用 | 更新隔离目录中的 npm 包、同步 CLI 与 SDK 版本 |

### GitHub PR / 分支管理

| 脚本 | 职责 | 典型场景 |
|------|------|---------|
| `gh-pr-create.py` | 创建 GitHub PR，支持 `--auto` AI 生成 title | 从 feature 分支提 PR |
| `gh-pr-merge.py` | 合并 GitHub PR，默认 squash，支持 `--admin` 绕过 | PR 合并 |
| `gh-branch-protect.py` | 设置 GitHub 分支保护规则（Require PR reviews）| 模拟 team mode |

### 归档

| 脚本 | 职责 | 典型场景 |
|------|------|---------|
| `archive_project.py` | 项目归档主编排：scan → compress → verify 三阶段闭环 | 归档 cs_py / venv 分组 |
| `archive_cs_py.py` | 快捷入口：归档 cs_py 分组 | 调用 `archive_project.py --group cs_py` |
| `archive_venv.py` | 快捷入口：归档 venv 分组 | 调用 `archive_project.py --group venv` |

### 🌐 浏览器 / Chrome / Session 工具聚合

| 脚本 | 职责 | 典型场景 |
|------|------|---------|
| `atomic-check-chrome-session.py` | 🌐 **Chrome Session 登录态检测原子 CLI**。读取 Cookies DB，检测登录态标志 + TTL + 新鲜度，输出 A/B/C/D 四级结论，支持 `--output` manifest 落盘 | 头条 / GitHub 等域名登录态验证、pipeline 前置门禁 |
| `download-article.py` | 🌐 **文章下载 CLI 入口**。Playwright + Chrome 持久化上下文 + Readability/Turndown 注入提取文章 | 头条文章下载为 Markdown |
| `screenshot_verifier.py` | 🌐 **URL 截图验证**。Playwright + 已保存 Chrome Session 对目标页面截图 | 页面截图留档、前端验证 |
| `chrome_extension_manager.py` | Chrome 扩展管理器（搜索 / 下载 CRX / 解压）| 管理浏览器扩展 |

> **底层插件支撑**（Layer 1，通过 `py_lib.load_plugins()` 访问）：
> - `browser_session.py` — Chrome 持久化上下文管理器（交互式登录 / headless 上下文创建）
> - `chrome_session.py` — Cookies DB 读取器（登录态检测 / TTL 分析 / 新鲜度判定）
> - `article_extractor.py` — 文章提取编排（Playwright + JS 注入 Readability + Turndown）
> - `js_loader.py` — JS 资产发现与拓扑排序（注入顺序真源）


### 文章下载

| 脚本 | 职责 | 典型场景 |
|------|------|---------|
| `download-article.py` | **文章下载 CLI 入口**。URL → Markdown + JSON | 下载在线文章 |

### 运行时域（子目录）

| 脚本 / 目录 | 职责 | 典型场景 |
|-------------|------|---------|
| `verify-runtime/wf-verify-runtime.py` | **Workflow：真源检测**。编排 detect → query → compare → report | 执行真源检测 |
| `download-runtime/wf-download-runtime.py` | **Workflow：运行时下载**。编排路由探测 → 下载 → 解压 → 备份替换 | 下载 / 更新运行时 |
| `runtime-common/wf-runtime-full.py` | **检测 + 下载一体化**。串接 detect → query → compare → download → extract verify | 批量检测 + 下载 |
| `runtime-common/atomic-*.py` | 公共原子脚本（detect-local / query-upstream / compare-version / generate-report）| 被 wf 调用 |
| `download-runtime/atomic-*.py` | 下载原子脚本（route-probe / download-file / extract-verify / backup-replace / cleanup-temp）| 被 wf-download-runtime 调用 |


## py-plugins 底座插件清单（Layer 1）

> **⚠️ 三层调用铁律：py-plugins/ 下的插件禁止被 Workflow 直接 import。必须通过 `py_lib.load_plugins()` 获取 registry 后访问。**
> 
> ```python
> # ✅ 正确做法
> from py_lib import load_plugins
> registry = load_plugins(devroot="...", tags=["lint"])
> registry.lint_json.validate(path="...")
> 
> # ❌ 禁止行为
> import lint_json  # 越级直接 import Layer 1 插件
> ```

### 基础设施（core）

| 插件 | 职责 |
|------|------|
| `detect_devroot.py` | Devroot 探测与真源验证 |
| `encoding.py` | 编码处理：stdout 重配置、UTF-8 切换与恢复 |
| `process_runner.py` | 进程执行器：封装 subprocess 流式输出 |
| `constants.py` | 项目常量：devroot、git 路径、env 文件等 |
| `core.py` | 核心工具：步骤头、日志、计时器、StepContext |
| `env_config.py` | 环境配置读取：.env 文件解析、必填项检查 |
| `time_source.py` | 统一时间来源：解析时间字符串或返回当前时间 |
| `timestamp.py` | 时间戳格式化器：多种字符串格式输出 |

### Lint（lint）

| 插件 | 职责 |
|------|------|
| `lint_json.py` | JSON 语法验证器 |
| `lint_ps1.py` | PowerShell 脚本语法验证器 |
| `lint_python.py` | Python 脚本语法验证器 |
| `lint_encoding.py` | 文件编码 / BOM / 行尾符检测器 |
| `md_lint.py` | Markdown 格式 Linter：frontmatter 边界检测 |
| `link_checker.py` | Markdown 内部相对链接验证 |

### 归档（archive）

| 插件 | 职责 |
|------|------|
| `archive_config.py` | 归档配置：GROUPS 定义、7z 路径、输出目录 |
| `archive_scanner.py` | 归档扫描器：磁盘扫描、黑白名单过滤 |
| `archive_compressor.py` | 归档压缩器：7z 压缩封装、心跳进度 |
| `archive_empty_handler.py` | 空目录与零字节文件处理器 |
| `git_keep_emptydir.py` | Git 空目录保留：自动创建 .gitkeep |

### GitHub（github / gh）

| 插件 | 职责 |
|------|------|
| `gh_preflight.py` | **gh CLI 前置检测**：验证 gh.exe / PAT / 认证状态，返回 GhContext |
| `github_api.py` | GitHub REST API 封装：Issue / Comment 查询与创建 |

### 浏览器（browser）

| 插件 | 职责 |
|------|------|
| `browser_session.py` | Browser Session 管理器：Chrome 持久化上下文 |
| `chrome_session.py` | Chrome Session 检测器：读取 Cookies DB，检测登录态 |
| `js_loader.py` | JS 资产加载器：读取 js-sort-rules.json 拓扑排序 |
| `article_extractor.py` | 文章正文提取：Playwright 注入 Readability + Turndown |

### Agent（agent / llm）

| 插件 | 职责 |
|------|------|
| `provider_config.py` | Provider 配置真源：LLM 配置统一读取 |
| `llm_client.py` | LLM HTTP 客户端：OpenAI 兼容格式 Chat Completions |
| `agent_tools.py` | Agent 工具注册框架：@tool 装饰器、execute_tool |
| `agent_context.py` | Agent 上下文管理器：消息历史、上下文压缩 |
| `agent_core.py` | Agent 核心引擎：标准 ReAct 循环 |

### 运行时（runtime / utility）

| 插件 | 职责 |
|------|------|
| `runtime_version.py` | 运行时工具版本检测器 |
| `list_upstream_versions.py` | 上游版本列表查询器 |
| `runtime_naming.py` | 运行时产物命名唯一真源 |

### 安全（validation）

| 插件 | 职责 |
|------|------|
| `security_audit.py` | 安全审计插件：部署前敏感内容巡检 |


## 三层架构与调用规则

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 3: Workflow（本目录 py-tools/）                        │
│  直接可执行的 CLI 脚本，编排业务步骤                            │
│  禁止直接 import Layer 1 插件                                  │
└──────────────────────────────────────────────────────────────┘
                    ↓ 调用 py_lib.load_plugins(profile=...)
┌──────────────────────────────────────────────────────────────┐
│  Layer 2: 统一入口（../py_lib.py）                            │
│  读取 py-sort-rules.json → 拓扑排序 → 标签筛选 → 动态 import   │
│  所有调用的唯一网关；禁止被绕过                                │
└──────────────────────────────────────────────────────────────┘
                    ↓ 动态加载 + 传递 Config
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: 底座插件（../py-plugins/）                          │
│  单一职责，暴露标准化接口；不直接对外暴露                       │
└──────────────────────────────────────────────────────────────┘
```

### Profile 速查

| Profile | 加载的插件标签 | 用途 |
|---------|---------------|------|
| `core` | `core` | 基础设施 |
| `lint` | `lint`, `md` | 全量 lint |
| `lint-json` | `lint`, `json` | 仅 JSON lint |
| `lint-ps1` | `lint`, `ps1` | 仅 PowerShell lint |
| `lint-python` | `lint`, `python` | 仅 Python lint |
| `lint-encoding` | `lint`, `encoding` | 仅编码 lint |
| `archive` | `archive` | 归档 |
| `agent` | `agent` | Agent 全量 |
| `validation` | `validation` | 安全审计 |
| `md-validation` | `md`, `validation` | Markdown 验证 |
| `_default` | 全部 | 向后兼容 |


## 上级导航

- [scripts/ 目录索引](../README.md)
- [task 总索引](../../README.md)
- [deploy-git-isolated 设计文档](../../DESIGN.md)
