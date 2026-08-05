---
title: deploy-git-isolated 可用工具速查表
description: 本 task 全部可用工具的索引、职责、路径与边界说明。包含本地专属脚本与外部通用工具的引用链路，防止重复造轮子。
date: 2026-07-23
meta:
  version: 1.4
---

# deploy-git-isolated 可用工具速查表

> **与 EXEC-CHEATSHEET 的区别**：本文件回答「有什么工具、在哪里、什么时候用」；EXEC-CHEATSHEET 回答「命令怎么执行」。二者互补，不重叠。


## 1. 本地专属脚本（scripts/）

本 task 的核心脚本，全部位于 `references/tasks/deploy-git-isolated/scripts/`。

### 1.1 部署流水线（Step 1-8）

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `github-step-01-init.ps1` | git init + 身份配置 | 首次部署隔离 Git | ready |
| `github-step-02-gitignore.ps1` | 生成安全 .gitignore | 初始化仓库防护 | ready |
| `github-step-03-readme.ps1` | 生成 README.md | 初始化仓库文档 | ready |
| `github-step-04-stage.ps1` | 安全 add + 显示 staged | 准备提交 | ready |
| `github-step-05-commit.ps1` | git commit | 提交变更 | ready |
| `github-step-06-remote.ps1` | 添加 remote | 连接 GitHub | ready |
| `github-step-07-push.ps1` | git push（从 .env 读取 PAT） | 推送到远程 | ready |
| `github-step-08-upstream.ps1` | 设置 upstream | 建立分支追踪 | ready |

### 1.2 Issue 同步（新增）

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `github-sync-issue.ps1` | Issue 同步入口：create / update / comment / list-comments / get-issue | commit 后同步变更历史到 Issue | ready |
| `github-sync-issue-config.json` | 配置真源：模板、labels、endpoint 映射 | 调整 Issue 格式时修改此文件，不动脚本 | ready |
| `fetch_issue.py` | Python CLI：获取 Issue 完整内容（含评论） | 通过 py_lib 调用 github_api 插件查看 Issue | ready |
| `atomic-gh-issue-create.py` | **Atomic：GitHub Issue 创建**。通过 GH CLI 创建 issue，支持 --dry-run / --show-progress / --label | workflow-poly Step 9 前创建追踪 issue | ready |

> **与 github-create-issue.ps1 的区别**：`github-create-issue.ps1` 是 Phase 3 的遗留脚本，功能单一（仅 create）；`github-sync-issue.ps1` 是统一入口，覆盖全部 Issue 生命周期操作，使用插件架构（github-api.ps1），推荐新场景使用。
> **Python 版补充**：`fetch_issue.py` 走 py_lib 插件体系，与 PS 版 `github-sync-issue.ps1 -Mode get-issue/list-comments` 功能互补，输出格式对齐。

### 1.3 安全与检查

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `github-safety-check.ps1` | 综合安全检查（tracked/staged/敏感文件） | push 前必执行 | ready |
| `git-verify-isolation.ps1` | 验证隔离效果（独立使用） | 怀疑 PATH 泄漏时 | ready |

### 1.4 Lint 插件体系

**可用能力**（由 `py_lib` 插件体系动态提供）：

lint 体系覆盖 JSON / PowerShell / Python / Encoding / Markdown / Link 等验证。具体有哪些插件可用、各自的标签与职责，**通过入口 API 动态发现**，禁止在静态文档中硬编码插件清单。

```python
from py_lib import list_plugins
lint_plugins = list_plugins(tags=["lint"])
```

> **铁律**：
> 1. **`run-lint.py` 是 lint 唯一入口**，所有 lint 操作必须通过它。
> 2. 插件清单的真源是 `py-sort-rules.json`，人类速查只说明能力类别。
> 3. workflow 层禁止直接 `import` plugin。

**CLI 入口**（唯一）：

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `run-lint.py` | **Lint 唯一入口**。全量/按 `--profile`/按 `--files` 路由，支持 `--fix` 三阶段闭环、`--audit` 覆盖度审计 | 新建/更新文档后必执行；规则审计时用 `--audit` | ready |

**覆盖度审计**（新增，规则清单对照）：

```powershell
# 对照 lint-rules-manifest.json 检查规则覆盖度
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --audit
```

**规则清单真源**：`schema/json/lint-rules-manifest.json`（所有 lint 规则 ID、插件归属、可修复性、文件类型路由）

**典型工作流（一步闭环）**：
```powershell
# 单文件 lint→amend→lint 闭环（新建/更新文档后）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.md" --fix

# 目录全量 lint→amend→lint 闭环
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --fix

# 仅检测（不修复）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.py"
```

**文件类型 → 触发插件自动路由**：

| 文件 | 语法检测 | 编码检测 | 链接检测 |
|------|---------|---------|---------|
| `.md` / `.mdc` | `md_lint` | `lint_encoding` | `link_checker` |
| `.py` | `lint_python` | `lint_encoding` | — |
| `.json` / `.jsonc` | `lint_json` | `lint_encoding` | — |
| `.ps1` | `lint_ps1` | `lint_encoding` | — |
| `.js` / `.ts` / 等 | — | `lint_encoding` | — |

**可修复 vs 仅检测**：见 `scripts/EXEC-CHEATSHEET.md` Stage S6 表格。

> 依赖：`py_lib.py`（v1.2.0） + `py-sort-rules.json`（v1.1.0）拓扑排序加载。
> 版本管理 API：`from py_lib import __version__`（py_lib 自身版本）、`get_rules_version()`（py-sort-rules 版本）、`registry.rules_version`（运行时规则版本）。
> 插件通过 `__plugin_registry__` 访问 devroot。

### 1.3 版本记录更新

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `update-version.py` | **Workflow：版本记录更新**。自动发现 venv/version/ 下工具 → 调用 runtime_version 插件实测本地版本 → 对比记录版本 → 更新 .md（frontmatter date + version 表格）+ 追加 `*-history.md` | 记一版 version / 更新 venv/version | ready |

> **与 5 个独立 get-*-version.ps1 的区别**：`update-version.py` 是统一 Workflow 入口，自动发现、自动对比、自动更新文件；`schema/tool/get-*-version.ps1` 是单工具实测脚本（遗留，仍可用作 fallback）。
> **架构**：update-version.py（Workflow）→ py_lib.load_plugins(tags=["core", "utility"]) → registry.runtime_version.detect() / registry.timestamp.get_now() / registry.detect_devroot.get_devroot()。runtime_version 插件已在 py-sort-rules.json 登记。

**CLI 用法**：
```powershell
# 全量自动检测与更新
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}"

# 仅检测指定工具
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}" --tool node

# 仅检测对比，不写入文件（dry-run）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\update-version.py" --devroot "${devroot}" --dry-run
```

### 1.4 运行时域（Runtime / 真源检测与下载）

**新增架构**：将 `references/runtime/` 下的 `verify-runtime.py` 和 `download-runtime-tool.py` 拆分为 task 原子脚本体系。

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `verify-runtime/wf-verify-runtime.py` | **Workflow：真源检测**。编排 detect → query → compare → report | 替代 `references/runtime/verify-runtime.py` | ready |
| `download-runtime/wf-download-runtime.py` | **Workflow：运行时下载**。编排 detect → query → compare → route → download → extract → backup → replace → cleanup | 替代 `references/runtime/download-runtime-tool.py` | ready |
| `runtime-common/wf-runtime-full.py` | **Workflow：检测+下载一体化**。串接 detect → query → compare → download → extract verify，全程带时间戳和进度条 | 批量检测+下载 node/opencode 等 | ready |
| `runtime-common/atomic-detect-local.py` | **公共原子**：本地 exe 检测 + candidate_paths 兜底 + 版本提取 | 被 wf-verify-runtime / wf-download-runtime 调用 | ready |
| `runtime-common/atomic-query-upstream.py` | **公共原子**：上游版本查询（python/node/opencode/chromium/llama） | 被 wf-verify-runtime / wf-download-runtime 调用 | ready |
| `runtime-common/atomic-compare-version.py` | **公共原子**：版本对比（up_to_date/outdated/unknown） | 被 wf-verify-runtime / wf-download-runtime 调用 | ready |
| `runtime-common/atomic-generate-report.py` | **公共原子**：报告生成（stdout 表格 + JSON 落盘） | 被 wf-verify-runtime 调用 | ready |
| `download-runtime/atomic-01-route-probe.py` | **原子**：HEAD 探测直连+代理，返回最优路由 | 被 wf-download-runtime 调用 | ready |
| `download-runtime/atomic-02-download-file.py` | **原子**：流式下载 + 进度条 + 代理支持 | 被 wf-download-runtime 调用 | ready |
| `download-runtime/atomic-03-extract-verify.py` | **原子**：ZIP 解压 + 定位 exe + 版本验证 | 被 wf-download-runtime 调用 | ready |
| `download-runtime/atomic-04-backup-replace.py` | **原子**：进程检测 + 备份旧版 + 替换新版 | 被 wf-download-runtime 调用 | ready |
| `download-runtime/atomic-05-cleanup-temp.py` | **原子**：清理解压目录和 ZIP 文件 | 被 wf-download-runtime 调用 | ready |

**CLI 用法**：
```powershell
# 真源检测（全量）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}"

# 真源检测（单工具）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}" --tool node

# 检测+下载一体化（全链路自动，带进度条）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\runtime-common\wf-runtime-full.py" --devroot "${devroot}" --tools node,opencode_cli

# 运行时下载（检测+下载，不替换）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py" --devroot "${devroot}" --tool-name node

# 运行时下载（强制替换）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py" --devroot "${devroot}" --tool-name node --force
```

> **目录结构**：`runtime-common/`（公共原子，跨 workflow 复用）、`verify-runtime/`（真源检测编排）、`download-runtime/`（下载编排 + 独有原子）。

### 1.5 安全审计（Security Audit）

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `workflow-security-audit.py` | **Workflow：部署前敏感内容巡检**。组装 security_audit 插件的五 Phase 流程（pattern_scan / git_tracking），输出人类可读报告 + JSON 报告 | commit/push 前必执行，确保无 API key / PAT / 私钥泄露 | ready |
| `security_audit.py` | 底层插件：提供 pattern scan、git tracking 验证、报告聚合能力 | 被 workflow 调用，不直接作为 CLI 入口 | ready |

**架构**：
```
workflow-security-audit.py（Workflow）→ py_lib.load_plugins(profile="validation") → security_audit 插件
  Phase 1: pattern_scan → 对 tracked 文件正则扫描敏感模式
  Phase 4: git_tracking → 验证 .env / config.json / key.txt 未被 git 追踪
  Phase 5: summary → 聚合报告，输出 pass / warn / fail
```

**CLI 用法**：
```powershell
# 完整审计（默认 HEAD~10..HEAD）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}"

# 指定 commit 范围
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}" --commit-range "HEAD~5..HEAD"

# 仅执行特定 phase
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}" --phases pattern_scan git_tracking

# 输出 JSON 报告（自动落盘到 venv/tmp/）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-security-audit.py" --devroot "${devroot}" --output "${devroot}\venv\tmp\audit.json"
```

> **关联规范**：`schema/docs/security-audit-spec.md`（审计流程、敏感模式定义、严重等级）
> **关联 schema**：`schema/json/security-audit-schema.json`（报告数据结构契约）

### 1.5 时间戳生成

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `get-timestamp.py` | Workflow CLI：通过 py_lib 调用 timestamp + time_source 插件，输出格式化时间 | Agent 写入 .md / .json 的 date/frontmatter 字段时获取标准格式 | ready |
| `timestamp.py` | 底层插件：接收 datetime 对象，格式化为多种字符串 | py_lib 插件体系内调用，只做格式化不生产时间 | ready |
| `time_source.py` | 底层插件：**统一时间来源**。默认当前时间，也支持解析外部时间字符串 | 被 timestamp 依赖；也可独立调用解析时间 | ready |

**架构**：
```
time_source.parse_time(source) → (dt_local, dt_utc)
                ↓
timestamp.format_timestamp(dt_local, dt_utc) → {local_short, local_iso, utc_iso, ...}
```

**CLI 用法**：
```powershell
# 默认当前时间
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --format local_iso

# 指定时间来源（ISO 8601 格式）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --source "2026-06-21" --format utc_short
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --source "2026-06-21T14:30:00" --format utc_iso

# 输出全部格式
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --all
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\get-timestamp.py" --json
```

**插件用法（通过 py_lib）**：
```python
registry = load_plugins(devroot="...", tags=["utility"])

# 默认当前时间
ts = registry.timestamp.get_now()
print(ts["local_iso"])

# 指定时间来源
dt_local, dt_utc = registry.time_source.parse_time("2026-01-15T09:00:00")
ts = registry.timestamp.format_timestamp(dt_local, dt_utc)
print(ts["local_iso"])   # 2026-01-15T09:00:00
print(ts["utc_iso"])     # 2026-01-15T01:00:00Z
```

**格式键名速查（含示例输出）**：

| 键名 | 说明 | 典型用途 | 示例输出 |
|------|------|---------|---------|
| `local_short` | 本地日期 | `.md` frontmatter `date` | `2026-06-25` |
| `local_long` | 本地时间（紧凑，无分隔符） | 日志文件名 | `2026-06-25T162111` |
| `local_iso` | 本地时间（ISO 扩展） | `.md` 内联时间戳、验证时间 | `2026-06-25T16:21:11` |
| `utc_short` | UTC 日期 | 跨时区日期标记 | `2026-06-25` |
| `utc_long` | UTC 时间（紧凑，Z 后缀） | GitHub Release 文件名 | `2026-06-25T082111Z` |
| `utc_iso` | UTC 时间（ISO 扩展，Z 后缀） | API 时间戳、日志时间 | `2026-06-25T08:21:11Z` |
| `filename_safe` | 文件名安全（日期-时间-秒） | env-migration 文件名后缀 | `2026-06-25-162111` |

**CLI 参数**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--format <键名>` | 输出指定格式（默认 `local_iso`） | `--format filename_safe` |
| `--source <时间>` | 指定时间来源（默认当前时间，支持 ISO 8601） | `--source "2026-06-21"` `--source "2026-06-21T14:30:00"` |
| `--all` | 输出全部格式键值对 | — |
| `--json` | 以 JSON 输出全部格式 | — |

### 1.4 通用包装器

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `git-isolated.ps1` | 隔离 Git 通用包装器（透传 git 子命令） | 日常 git status/log/diff 等 | ready |
| `git-clone-isolated.ps1` | 隔离方式 Clone | 克隆新仓库 | ready |
| `git-config-global.ps1` | 设置隔离全局身份（独立使用） | 仅需改身份时 | ready |
| `git-multi-identity.ps1` | 多身份切换演示 | 教学/验证 | ready |

### 1.5 共享库体系

| 文件 | 职责 | 扩展方式 |
|------|------|---------|
| `github-lib.ps1` | 共享库聚合入口（拓扑排序 + Profile 筛选 + 依赖自动补齐） | 不直接修改，通过 JSON 驱动 |
| `lib-sort-rules.json` | 插件依赖图、加载顺序真源、**Profile 定义** | 追加条目 / 新增 profile |
| `lib-plugins/*.ps1` | 6 个共享函数插件 | 新建 `.ps1` + 登记 JSON + 可选绑定 profile |

**Profile 用法速查**：
```powershell
# 默认（向后兼容，加载全部）
. $libPath

# 使用预设 profile（deploy/issue-sync/minimal）
. $libPath -Profile "issue-sync"

# 命令行覆盖（最高优先级）
. $libPath -Profile "issue-sync" -Exclude @("git-checks")
```

> 插件架构详情见：`docs/PLUGIN-ARCHITECTURE.md`
> PS 插件：`github-api.ps1`（GitHub REST API 封装，自动 UTF-8 encoding）
> Python 插件：`github_api.py`（GitHub REST API 封装，urllib 实现，与 PS 版功能对等）

### 1.6 归档 Workflow

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `archive_project.py` | 项目归档主编排：scan → compress → verify 三阶段闭环 | 归档 cs_py / venv 分组 | ready |
| `archive_cs_py.py` | 快捷入口：归档 cs_py 分组 | `python archive_cs_py.py --format 7z` | ready |
| `archive_venv.py` | 快捷入口：归档 venv 分组 | `python archive_venv.py --format 7z` | ready |

> 架构：三层 + 配置契约。Workflow 通过 `py_lib.load_plugins(profile="archive")` 调用 `archive_config` / `archive_scanner` / `archive_compressor` 插件。
> 配置真源：`py-tools/archive-groups.json`（黑白名单、输出格式）

### 1.8 JS 工具链 / 文章下载流水线

三层对称架构的 JS 侧：`js_lib.js`（入口）+ `js-sort-rules.json`（配置）+ `js-plugins/`（可复用模块）+ `js-tools/`（完整脚本）。Python 侧通过 `js_loader.py` 桥接。

**JS 入口与配置**：

| 文件 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `js_lib.js` | **JS 入口**（对标 `py_lib.py`）：`--list` 列出全部资产、`--resolve <tool>` 输出拓扑排序路径 | Node.js CLI 加载 js-tools 前检查依赖完整性 | ready |
| `js-sort-rules.json` | JS 资产注册表：含 `type` 字段（`browser`/`node`/`dual`）、依赖拓扑 | 新增 js-plugin/js-tool 后在本文登记 | ready |

**JS 可复用模块（js-plugins/）**：

| 文件 | 职责 | 类型 | 状态 |
|------|------|------|------|
| `url-utils.js` | URL 工具集：`toAbsoluteURI`、`guessImageExt`、`isImageUrl`（受 readability.js 启发提取） | dual | ready |
| `markdown-rules.js` | Turndown 规则预设：`articlePreset`、`githubPreset`、`cleanPreset`（受 turndown 规则系统启发提取） | dual | ready |

**JS 工具脚本（js-tools/）**：

| 文件 | 职责 | 类型 | 典型场景 | 状态 |
|------|------|------|---------|------|
| `readability.js` | Mozilla Readability —— 浏览器注入：`new Readability(doc).parse()` | browser | 在 Chrome 中提取文章内容（被 extract-article.js 依赖） | ready |
| `turndown.js` | Turndown —— 浏览器注入：`new TurndownService(opts)` | browser | HTML → Markdown 转换 | ready |
| `extract-article.js` | 浏览器注入：注册 `window.__extractArticle()`，内部调用 readability + turndown | browser | 从 URL 提取→解析→转 MD 全流程（被下游 Python CLI 调用） | ready |
| `url-analyze.js` | URL 分析工具：CLI 模式通过 `js_lib` 加载 `url-utils`；浏览器注入注册 `window.__URL_ANALYZE` | dual | 分析 URL 的绝对地址、图片扩展名、图片类型判定 | ready |

**Python 侧桥接插件（py-plugins/）**：

| 文件 | 职责 | 依赖 | 典型场景 | 状态 |
|------|------|------|---------|------|
| `js_loader.py` | **Python 侧 JS 资产发现桥梁**：读取 `js-sort-rules.json` → 拓扑排序 → 返回有序文件绝对路径列表。提供 `resolve()`、`resolve_script_tags()`、`validate()` 接口 | `py_lib` 插件体系（注册在 `py-sort-rules.json`） | Python CLI 调用 extract-article 时先通过 `js_loader.resolve()` 获取 js 文件注入顺序 | ready |
| `article_extractor.py` | **文章提取编排插件**：调用 `browser_session` 创建 Chrome 上下文 → `js_loader.resolve()` 注入 JS → 执行 `window.__extractArticle()` → 返回 {title, content, excerpt, byline} | `browser_session` + `js_loader` | Python CLI 入口 `download-article.py` 的底层实现 | ready |

**Python CLI 入口（py-tools/）**：

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `download-article.py` | **文章下载 CLI 入口**（Layer 3 Workflow）：调用 `article_extractor.py` → 从 URL 提取文章 → 输出 Markdown + 元数据 JSON | 下载在线文章为本地 Markdown 文件 | ready |
| `workflow-download-article-to-vault.py` | **文章下载到 Vault Workflow**（Layer 3 Workflow）：编排 validate → download → verify → extract → mkdir → move → nav → cleanup 8 步闭环。自动维护 `clippings/README.md` 导航表 | 头条文章下载并直接归档到 vault-demo/raw/clippings/ | ready |
| `atomic-chrome-login-interactive.py` | **Chrome 交互式登录 CLI**（Layer 3 原子）：启动持久化 Chrome 窗口让用户手动完成登录/续期，`--output` 必填，manifest 供 pipeline 复用 | 头条/其他网站 Session 续期、首次登录 | ready |

**调用链路（用于排查）**：
```
download-article.py (py-tools, CLI)
  → article_extractor.py (py-plugins, 编排)
    → browser_session.py (py-plugins, Chrome 上下文)
    → js_loader.py (py-plugins, JS 资产发现)
      → js-sort-rules.json (拓扑排序)
        → js-tools/extract-article.js (browser inject)
          → js-tools/readability.js (parse)
          → js-tools/turndown.js (html→md)
  → 输出 Markdown + JSON
```

### 1.9 部署编排 Workflow（Python 版）

Python 版部署流水线，与 PS 版 Step 1-8 功能对等。`workflow-deploy-full.py` 编排 Step 4-9（add → commit → remote → push → upstream → issue sync），按序调用 `py-steps/` 下的独立 step 脚本，任何一步失败立即停止。

**底座脚本**（`py-steps/`，被 workflow 按序调用）：

| 脚本 | 职责 | 对应 PS 版 |
|------|------|-----------|
| `step-04-github-deploy-add.py` | 安全 add + 显示 staged | `github-step-04-stage.ps1` |
| `step-04-github-init-only.py` | 仅 init（部分场景） | — |
| `step-05-github-commit.py` | git commit | `github-step-05-commit.ps1` |
| `step-06-github-remote.py` | 添加 remote | `github-step-06-remote.ps1` |
| `step-07-github-push.py` | git push（从 .env 读取 PAT） | `github-step-07-push.ps1` |
| `step-08-github-upstream.py` | 设置 upstream | `github-step-08-upstream.ps1` |
| `step-09-github-sync-issue.py` | Issue 同步 | `github-sync-issue.ps1` |

**编排 Workflow**：

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `workflow-deploy-full.py` | **全链条部署 Workflow**：编排 Step 4-9，调用 py-steps 分步执行。支持 `--step` 单步执行、`--message` 自定义提交信息、`--issue` 指定 Issue 编号。自动生成 AI 语义摘要和 Issue comment meta。 | 执行完整 GitHub 部署流水线 | ready |
| `atomic-git-preflight.py` | **原子：Git 前置验证**。整合 git_env + git_security 插件，提供 check()/verify() + GitContext（含 run_git）。可独立执行或被子 workflow 调用。 | 任何 git 业务脚本开头的前置验证 | ready |
| `atomic-deploy-preflight.py` | **原子：部署特有前置验证**。验证 .env PAT、分支保护、agent 插件加载、git 空目录保留。workflow 的 Step 0b。 | workflow-deploy-full 部署前验证 | ready |
| `atomic-check-staged-after-add.py` | **原子：Staged 内容安全扫描**。必须在 git add 后执行，强制扫描 staged 文件敏感模式。无 staged 文件时报错。 | workflow Step 4.5（add 后 commit 前） | ready |
| `atomic-git-reset-staged.py` | **原子：Git Staged 回滚**。安全取消暂存区全部 staged 文件，操作前审计+操作后验证，锁定 `reset HEAD`（无 `--hard`）。支持 `--target/--git-exe` polyrepo 契约。 | staged 回滚、unstage、reset HEAD | ready |
| `workflow-git-deploy-full-poly.py` | **Polyrepo 全链条部署 Workflow**：纯编排器，支持单仓库与 polyrepo 两种场景。--target 强制必填（polyrepo 调用契约），--devroot 仅验证与 CWD 一致。编排 Step 0a/0b/0c → 4 → 4.5 → 5 → 6 → 7 → 8 → 9 → 10 | 跨仓库/多根部署、polyrepo 流水线 | ready |
| `atomic-polyrepo-context-manifest.py` | **原子：PolyrepoContext manifest 生成**。从 toolchain_root + target 构造 PolyrepoContext 并序列化（repo_url/branch/is_polyrepo 等），供 workflow Step 0c 与 Step 7/9/10 复用。--target 强制必填 | poly workflow Step 0c、运行时上下文登记 | ready |
| `generate-ai-summary.py` | **Workflow 内嵌能力：AI 语义摘要生成器**。读取 git diff（--target 指定仓库，--cached 用 staged），调用 agent 插件体系生成中文摘要并落盘，被 poly workflow Step 4→5 之间调用。--target 强制必填 | 自动生成 commit 语义摘要、注入部署 meta | ready |
| `atomic-gh-repo-create.py` | **原子：GitHub 远程仓库创建**。通过 GH CLI 创建仓库，自动注入 PAT、脱敏 stdout、生成 manifest。支持 --public/--private/--add-readme/--description | polyrepo 初始化 Step 0（创建远程仓库） | ready |
| `atomic-git-repo-clone.py` | **原子：本地仓库 clone 与身份配置**。隔离 git.exe clone + local git config（user.name/email）+ 验证 remote/branch/status + manifest | polyrepo 初始化 Step 1（clone 远程仓库到本地） | ready |
| `atomic-git-push-smoke.py` | **原子：无弹窗安全 smoke push**。构造 PAT 认证 URL + 阻断 GCM 弹窗 + 双路 preflight（staged + 未 push commit）+ manifest | polyrepo 初始化验证、workflow Step 7 push | ready |
| `workflow-phase-git-local-diff-add-commit.py` | **Phase：本地 diff + add + commit**。输出 diff 审阅 → git add（-A 或 --files）→ git commit（自动生成或 --message）。执行后进入「已 commit 未 push」状态，下游接 atomic-git-push-smoke.py | 本地变更提交（独立 phase，不触及 remote） | ready |
| `atomic-config-edit-json.py` | **原子：JSON 配置结构化编辑**。RFC 6902 JSON Pointer + JSON Patch，支持单条/批量（@file）、add/replace/remove/merge、强制 LF、备份、dry-run | 修订 JSON 索引/配置文件（替代手敲 edit） | ready |
| `atomic-csv-column-transform.py` | **原子：CSV 列无损转换**。读取源 CSV，按配置规则对指定列进行无损转换（today_ymd / today_iso / fixed / regex_replace / empty），写入新 CSV，生成 manifest。配置驱动，改 JSON 配置即可适配新场景，py 框架不变。源于 feiliks-invoice-csv 工具的泛化 | CSV 列内容转换、Invoice date 批量更新、CSV 数据处理 | ready |
| `atomic-npm-isolated-install.py` | **原子：npm 隔离安装**。将 npm 包安全安装到隔离目录，支持 Local（带 package.json）和 Global（单包）双模式。内置重组安全检查、CWD 切换检查、--show-progress 实时输出、bin 可用性验证（--version/--help）。生成 JSON manifest。 | 安装 node 工具到隔离目录、scriptc 等 npm 包隔离安装 | ready |

**架构**：
```
workflow-deploy-full.py（Workflow 编排）
  ├── [Step 0a] atomic-git-preflight.py（通用 git 验证）
  ├── [Step 0b] atomic-deploy-preflight.py（部署特有验证）
  ├── py-steps/step-04-github-deploy-add.py
  ├── [Step 4.5] atomic-check-staged-after-add.py（staged 内容扫描）
  ├── generate-ai-summary.py（Step 4→5 之间，使用 --cached）
  ├── py-steps/step-05-github-commit.py
  ├── [更新 meta commit hash]
  ├── py-steps/step-06-github-remote.py
  ├── py-steps/step-07-github-push.py
  ├── py-steps/step-08-github-upstream.py
  └── py-steps/step-09-github-sync-issue.py（接收 --meta）

atomic-git-reset-staged.py（独立原子，非 workflow 编排内步骤）
  └── 供外部调用：staged 回滚、unstage、reset HEAD
```

**CLI 用法**（显式传 `--devroot`，禁止省略）：
```powershell
# 全自动发布（从 staged 文件自动生成 commit message）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --auto

# 完整全链条部署（指定 commit message）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx"

# 仅执行单步（如仅 push，调试用）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --step 7 --message "feat: xxx"

# 指定 Issue 编号（Step 9 用）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx" --issue 1
```

> **与 PS 版的关系**：PS 版（`github-step-0N-*.ps1`）为原始实现，功能完备；Python 版（`py-steps/step-0N-*.py` + `workflow-deploy-full.py` 编排）为同能力重构版，提供更灵活的编排参数和自动化（AI 摘要、动态 meta）。**凡涉及 Step 4-9 的操作，必须使用 Python 版 workflow，禁止手动逐条调用 ps-steps。**


### 1.10 GitHub CLI / PR 自闭环

> **集成现状**：gh CLI（`venv/gh/bin/gh.exe`）已隔离部署，配置于 `venv/data-gh`（通过 `GH_CONFIG_DIR`）。本 task 主部署流水线（workflow-deploy-full*.py）走 GitHub REST API + PAT 模式；gh CLI 当前用于 **PR 自动化闭环**（可行性验证阶段）。

| 脚本 | 职责 | 典型场景 | 状态 |
|------|------|---------|------|
| `workflow-gh-pr.py` | **Workflow：PR 自闭环**。编排 gh-pr-create → gh-pr-merge → 本地同步（checkout base + pull） | 已 push feature 分支后一键 PR 闭环 | ready |
| `gh-pr-create.py` | 子脚本：创建 PR，支持 `--auto` AI 生成 title + `--body/--base/--draft` | PR 创建（可独立调用） | ready |
| `gh-pr-merge.py` | 子脚本：合并 PR，squash/merge/rebase + `--admin` 绕过保护 + `--delete-branch` | PR 合并（可独立调用） | ready |
| `gh-branch-protect.py` | 子脚本：分支保护规则管理 | 配置 Require reviews 等 | ready |
| `workflow-gh-preflight-demo.py` | 演示：gh CLI 前置验证（gh.exe + PAT + 认证状态） | gh 可用性自检 | ready |
| `gh_preflight.py`（py-plugins） | 前置检测插件：验证 gh.exe / PAT / 认证状态，返回 `GhContext`（含 `run_gh` 封装） | 被 workflow-gh-pr / gh-pr-* 调用 | ready |
| `atomic-gh-repo-verify.py` | **原子：GitHub 仓库真源验证**。L1-L5 推理链（intent→local-git→worktree→remote→PR），输出 manifest 供下游 PR 创建/合并复用 | PR 创建前验证本地-远程一致性 | ready |
| `source_truth.py`（py-plugins） | **真源推理链插件**：L1-L5 层式验证，修正 gh_preflight 真源认知误区（gh_preflight 是工具链验证，非真源验证） | 被 atomic-gh-repo-verify 调用 | ready |

> **L1-L5 推理链**：L1 intent-config（git-security.json）→ L2 local-git（.git/config + HEAD SHA）→ L3 worktree（分支/跟踪/上游一致性）→ L4 remote-HEAD（commit SHA 是否在远程）→ L5 PR-status（当前分支关联的 PR 状态）。唯一阻断条件：L4 commit SHA 不在远程。

**headless 认证**（自动化无需 `gh auth login`）：
```powershell
$env:GH_TOKEN = $env:GITHUB_PAT                       # 复用 .env 的 PAT
$env:GH_CONFIG_DIR = "${devroot}\venv\data-gh"        # 隔离配置目录
& "${devroot}\venv\gh\bin\gh.exe" repo create my-new-project --private --source . --push
```

> **认知澄清**：`gh pr merge` 本质是 GitHub REST API 的命令行封装，代码合并发生在**远端服务器**，本地 master 需 `pull` 才同步。PR 自动化是否纳入主部署流水线，取决于用户仓库分支保护策略。


## 2. 外部通用工具引用（runtime / schema/tool）

本 task 执行过程中**不应自行实现**以下能力，应直接调用已登记的通用工具。

| 工具名 | 全局路径 | 登记索引 | 本 task 中的用途 | 边界说明 |
|--------|---------|---------|----------------|---------|
| **lint-json.py** | `schema/tool/lint-json.py` | `verified-task-index.json` → `lint-json` | 验证 `.json` 文件语法（如 `task-scenario-triggers.json`、`ENTRY.json` 修改后） | JSON lint 是通用能力，不在 task 本地实现 |
| **lint-ps1.ps1** | `schema/tool/lint-ps1.ps1` | `verified-task-index.json` → `lint-ps1` | 验证本 task 下所有 `.ps1` 脚本语法 | PS 语法检查是通用能力 |
| **check-file-encoding.ps1** | `schema/tool/check-file-encoding.ps1` | `verified-task-index.json` → `check-file-encoding` | 检查所有落盘文件的 BOM/CRLF/LF | 编码检查统一走此工具 |
| **file-write-helper.py** | `schema/tool/file-write-helper.py` | `verified-task-index.json` → `file-write-helper` | 写入含中文的 `.ps1` 时处理 UTF-8 BOM | 文件写入 helper 是通用能力 |
| **wf-verify-runtime.py** | `references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py` | `verified-task-index.json` → `wf-verify-runtime` | 真源检测时扫描 `venv/git/` 是否存在 | 运行时真源检测能力已迁入 task 原子脚本体系 |
| **wf-download-runtime.py** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` | `verified-task-index.json` → `wf-download-runtime` | 如需升级 MinGit 版本时使用 | 运行时下载能力已迁入 task 原子脚本体系 |
| **trigger-index** | `references/runtime/verified-trigger-index.json` | `verified-task-index.json` → `trigger-index` | 查询 trigger 归属、注册新 trigger | trigger 治理是全局能力 |

> **铁律**：以上工具已存在且已登记，本 task 禁止自行实现同类功能。新增需求时先查 `verified-task-index.json` → `available_scripts_and_tools`。


## 3. 边界矩阵（什么时候用什么）

| 需求 | 首选工具 | 次选/备选 | 禁止行为 |
|------|---------|----------|---------|
| 验证 JSON 语法 | `lint_json.py`（本地，py_lib 插件） | `schema/tool/lint-json.py`（通用） | 禁止用 `python -c` 内嵌验证 |
| 验证 PS 语法 | `lint_ps1.py`（本地，py_lib 插件） | `schema/tool/lint-ps1.ps1`（通用） | 禁止不验证直接交付 `.ps1` |
| 验证 Python 语法 | `lint_python.py`（本地，py_lib 插件） | — | 禁止不验证直接交付 `.py` |
| 检查文件编码 | `lint_encoding.py`（本地，py_lib 插件） | `schema/tool/check-file-encoding.ps1`（通用） | 禁止现写编码检查命令 |
| 写入含中文 `.ps1` | `file-write-helper.py`（通用） | — | 禁止 Shell 重定向写 `.ps1` |
| 生成时间戳文件名 | `get-timestamp.py`（本地 workflow） | — | 禁止内嵌 `Get-Date` 拼文件名 |
| git init / push | `github-step-01/07.ps1`（本地） | — | 禁止裸命令操作 Git |
| push 前安全检查 | `github-safety-check.ps1`（本地） | — | 禁止跳过安全检查直接 push |
| staged 回滚 / unstage | `atomic-git-reset-staged.py`（本地） | — | **禁止现写 `git reset HEAD` 或任何 `git reset` 变体**（见 baseline-principles.md §0.8.5） |
| 日常 git 操作 | `git-isolated.ps1`（本地） | — | 禁止裸 `git` 调用（可能命中系统版） |
| 真源扫描 | `wf-verify-runtime.py`（本地 workflow） | — | 禁止自行实现文件存在性扫描 |
| 下载 MinGit | `wf-download-runtime.py`（本地 workflow） | — | 禁止自行写 `curl`/`Invoke-WebRequest` 下载 |
| Issue 同步（create/update/comment） | `github-sync-issue.ps1`（本地） | — | 禁止裸 API 调用，禁止重复造轮子 |
| Issue 内容查看（body + 评论） | `fetch_issue.py`（本地，py_lib 插件） | `github-sync-issue.ps1 -Mode get-issue/list-comments` | 禁止裸 API 调用 |
| 插件筛选加载 | `github-lib.ps1` -Profile（本地） | — | 禁止全量加载冗余插件 |
| 项目归档（cs_py） | `archive_cs_py.py`（本地 workflow） | `archive_project.py --group cs_py` | 禁止裸 `7z`/`zip` 命令归档 |
| 项目归档（venv） | `archive_venv.py`（本地 workflow） | `archive_project.py --group venv` | 禁止裸 `7z`/`zip` 命令归档 |
| 版本记录更新 | `update-version.py`（本地 workflow） | — | 禁止自行写 `python -c` 测版本 |
| 获取时间戳 | `get-timestamp.py`（本地 workflow） | — | 禁止内嵌 `Get-Date` 拼文件名 |
| 全链条部署（Step 4-9） | `workflow-deploy-full.py`（本地 workflow） | PS 版 Step 1-8 | 禁止手动逐条调用 ps-steps |
| 在线文章下载（URL → Markdown） | `download-article.py`（本地 workflow） | — | 禁止自行写 Playwright 下载文章 |
| URL 分析（isImage/toAbsoluteURI） | `url-analyze.js`（本地 js-tool） | `node url-analyze.js --url ...` | 禁止现写 URL 解析正则 |
| JS 资产依赖发现 | `js_lib.js`（本地入口） | `node js_lib.js --resolve <tool>` | 禁止手动翻 js-sort-rules.json 拼路径 |
| 浏览器桥接（Python → JS inject） | `js_loader.py`（本地 py-plugin） | — | 禁止硬编码 JS 文件路径 |
| Chrome Session 登录态检测 | `atomic-check-chrome-session.py`（本地原子） | `chrome_session.py`（py-plugin） | 禁止直接读 Cookies DB（走 atomic CLI 或 py_lib 插件） |
| 头条文章下载（Playwright + Chrome） | `download-article.py`（本地 workflow） | `article_extractor.py` + `browser_session.py` | 禁止自行写 Playwright 脚本 |
| URL 截图验证 | `screenshot_verifier.py`（本地 workflow） | `browser_session.py` | 禁止自行写 Playwright 截图 |
| PR 创建（已 push feature 分支） | `workflow-gh-pr.py --auto` / `gh-pr-create.py` | — | 禁止裸 `gh pr create`（绕过 preflight 与 AI 生成） |
| PR 合并（绕过保护） | `gh-pr-merge.py --admin` | — | 禁止裸 `gh pr merge`（绕过 preflight 与审计） |
| gh CLI 前置验证 | `workflow-gh-preflight-demo.py` / `gh_preflight.py` | — | 禁止裸 `gh auth status` 替代 |
| 新建 GitHub 仓库 | `gh.exe repo create`（headless: GH_TOKEN+GH_CONFIG_DIR） | — | 禁止网页手动建仓后再切回命令行（可全本机） |


## 4. 速查命令

### 4.1 本地脚本调用（Agent 格式）

```powershell
# Step 1-8
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# 安全检查
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-safety-check.ps1"

# Staged 回滚（取消全部暂存，不丢弃工作区修改）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-git-reset-staged.py" --devroot "${devroot}" --target "${devroot}" --git-exe "${devroot}\venv\git\cmd\git.exe"

# 通用包装器（示例：git status）
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\git-isolated.ps1" status

# Issue 同步（示例：追加评论记录 commit）
powershell -ExecutionPolicy Bypass -File "${devroot}\references\tasks\deploy-git-isolated\scripts\github-sync-issue.ps1" -Mode comment -IssueNumber 1 -Body "commit abc123: 新增 GOAL.md"

# 获取 Issue 完整内容（Python 版，含评论）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\fetch_issue.py" --issue-number 1

# 全链条部署（Python Workflow）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx"

# 文章下载
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://example.com/article"

# JS 资产列表
"${devroot}\venv\node\node.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\js_lib.js" --list

# JS 资产依赖解析
"${devroot}\venv\node\node.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\js_lib.js" --resolve extract-article

# URL 分析 CLI
"${devroot}\venv\node\node.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\js-tools\url-analyze.js" --url "/img/banner.webp" --base "https://site.com/blog/"

# Chrome Session 登录态检测（默认检测 devroot/venv/data-chrome 头条系）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py"

# Chrome Session 检测 + 指定 manifest 输出路径（pipeline 复用）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py" --output "${devroot}\venv\tmp\pipeline-manifest.json"

# Chrome Session 检测 + 指定 Profile 路径
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-check-chrome-session.py" --user-data-dir "D:\custom\chrome-profile"

# GitHub PR 自闭环（全自动，需先 deploy push 到 feature 分支）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-pr.py" --auto --admin

# 仅创建 PR（不自动 merge，留人工 review）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\gh-pr-create.py" --auto --base master

# 仅合并 PR（已存在）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\gh-pr-merge.py" --strategy rebase --admin

# gh CLI 前置验证演示
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-gh-preflight-demo.py"
```

> 完整命令见：`scripts/EXEC-CHEATSHEET.md`
> 标准流程与验收条件见：`SOP.md`

### 4.2 外部通用工具调用

```powershell
# 全量 lint（交付前必执行，推荐）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}"

# 按需 lint
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-json
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-ps1
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-python
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-encoding

# JSON lint（修改 task-scenario-triggers.json / ENTRY.json 后必执行）
"${devroot}\venv\py\python.exe" "${devroot}\schema\tool\lint-json.py" -v "${devroot}\references\tasks\deploy-git-isolated\task-scenario-triggers.json"

# PS lint（修改 .ps1 后必执行）
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# lint→amend→lint 工作流（workflow → py_lib → lint_encoding）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-lint-amend-lint.py" --devroot "${devroot}" --dir "references\tasks\deploy-git-isolated"

# 编码检查（落盘后必执行）
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-step-01-init.ps1"

# 文件写入 helper（含中文 .ps1）
"${devroot}\venv\py\python.exe" "${devroot}\schema\tool\file-write-helper.py" --config "${devroot}\venv\tmp\job.ini"

# 归档 cs_py（快捷入口）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\archive_cs_py.py" --stage all --format 7z

# 归档 venv（快捷入口）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\archive_venv.py" --stage all --format 7z

# 归档全量（主编排层）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\archive_project.py" --group cs_py venv --stage all --format 7z

# 全链条部署（Python Workflow）
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-deploy-full.py" --devroot "${devroot}" --message "feat: xxx"
```


## 5. 关联文件导航

| 文件 | 用途 |
|------|------|
| `README.md` | 场景化决策入口（5 个场景速查） |
| `ENTRY.json` | 机器真源（脚本清单、状态、版本历史） |
| `task-scenario-triggers.json` | 触发条件真源（5 场景 trigger 映射） |
| `SOP.md` | 标准流程（Step 契约 + Ralph Loop） |
| `scripts/EXEC-CHEATSHEET.md` | 执行速查（命令+配置+参数） |
| `scripts/py-tools/run-lint.py` | 统一 lint CLI 入口（JSON/PS1/Python/Encoding，支持 `--files` 单文件列表） |
| `scripts/py-tools/update-version.py` | 版本记录更新 Workflow（自动发现 → 实测 → 更新 .md + history） |
| `scripts/py-tools/fetch_issue.py` | 获取 GitHub Issue 完整内容（含评论） |
| `scripts/py-tools/workflow-deploy-full.py` | **全链条部署 Workflow**：编排 Step 4-9，支持 --step/--issue 参数 |
| `scripts/py-tools/download-article.py` | **文章下载 CLI 入口**：URL → Markdown + JSON |
| `scripts/py-tools/atomic-check-staged-after-add.py` | **原子：Staged 内容安全扫描**。必须在 git add 后执行 |
| `scripts/py-tools/atomic-git-reset-staged.py` | **原子：Git Staged 回滚**。安全取消暂存，操作前审计+验证，禁止现写 `git reset` |
| `scripts/py-plugins/git_reset.py` | **Git Reset 封装插件**。锁定 `reset HEAD`（无 `--hard`），三层封装 |
| `scripts/py-plugins/lint_*.py` | Lint 插件（json/ps1/python/encoding） |
| `scripts/py-plugins/js_loader.py` | **Python ↔ JS 桥接**：读取 js-sort-rules.json 拓扑排序 |
| `scripts/py-plugins/article_extractor.py` | **文章提取编排**：browser_session + js_loader → extractArticle |
| `scripts/js_lib.js` | **JS 入口**（Node.js）：--list/--resolve，对标 py_lib.py |
| `scripts/js-sort-rules.json` | JS 资产注册表（拓扑 + type 字段） |
| `scripts/js-plugins/url-utils.js` | JS 可复用模块：URL 工具（dual-mode） |
| `scripts/js-plugins/markdown-rules.js` | JS 可复用模块：Markdown 规则预设（dual-mode） |
| `scripts/js-tools/readability.js` | JS browser 工具：文章解析 |
| `scripts/js-tools/turndown.js` | JS browser 工具：HTML→MD |
| `scripts/js-tools/extract-article.js` | JS browser 工具：文章提取 workflow |
| `scripts/js-tools/url-analyze.js` | JS dual 工具：URL 分析 |
| `scripts/py-plugins/github_api.py` | GitHub REST API 封装（Python 插件） |
| `schema/json/lint-rules-manifest.json` | Lint 规则全局清单（7 插件、27 规则、5 可修复，审计时对照） |
| `schema/json/plugin-result-schema.json` | 插件返回格式 JSON Schema 真源（v1.0.0） |
| `schema/docs/plugin-result-schema.md` | 插件返回格式规范文档（人类可读） |
| `schema/py/models.py` | Pydantic / Dataclass 备选 Model 实现 |
| `docs/PLUGIN-ARCHITECTURE.md` | 插件化架构设计文档 |
| `DESIGN.md` | 设计决策与踩坑记录 |


| `skills/rg-fd-search/SKILL.md` | **通用搜索能力**：rg + fd 标准调用，强制搜索优先次序，默认禁止原生 grep/glob。采用 SED 自演进目录模式（scripts/ references/ assets/ templates/ examples/ versions/ gotchas/ evolutions/ learnings/） |
| `skills/tool-discovery/SKILL.md` | **工具发现**：在 deploy-git-isolated 内定位工具、查询用法、获取 entry_command |
| `skills/docstring-quality-harness/SKILL.md` | **docstring 质量 Harness**：委派 subagent 检验工具自说明质量 |

*速查表版本: v1.5*  
*创建时间: 2026-06-16*  
*更新时间: 2026-08-05*  
*关联全局索引: `references/runtime/verified-task-index.json`*
