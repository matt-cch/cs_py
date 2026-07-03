---
title: Playwright + Chrome 持久化 Session + 扩展自动化环境变更
description: 本次 session 建立了完整的 Playwright + Chrome 异步事件驱动浏览器自动化工具链，覆盖持久化 Session、扩展加载、文章提取、环境预检等模块。含大量踩坑记录。
date: 2026-06-08
---

# env-migration-playwright-chrome-session-extension-2026-06-08-080427

> **文档性质**：环境迁移指南。聚焦本次 session 对开发环境本身的修改（Playwright 工具链、Chrome 扩展机制、文档体系）。
> **受众**：Human + Agent。在新环境解压项目后，Agent 可直接阅读此文档并执行复现步骤。

### 元信息

| 字段 | 填写 |
|------|------|
| **Session 主题** | Playwright + Chrome 持久化 Session + 扩展自动化工具链建设 |
| **日期** | 2026-06-08 |
| **文件名时间戳** | `2026-06-08-080427` |
| **触发原因** | 需要自动化访问需登录网页（头条）并提取文章，同时支持浏览器扩展（Obsidian Web Clipper）自动化 |
| **影响范围** | `debug/playwright/agent-verify/` 工具链、`docs/playbooks/` 文档、`references/runtime/verified-runtime-index.json` |
| **风险等级** | 中（涉及外部 Chrome 路径、扩展目录引用，跨环境需调整） |


## 一、文本文件变更清单

### 1. 新增 `debug/playwright/agent-verify/lib/interactive.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/interactive.py` |
| **变更类型** | 新建 |
| **作用** | 交互式浏览器启动逻辑（异步事件驱动），支持扩展加载、事件检测 example.com 退出、Session 持久化 |
| **核心配置** | `ignore_default_args=["--disable-extensions"]` — 仅此一行即可恢复 Chrome 扩展能力 |
| **关键参数** | `user_data_dir=USER_DATA_DIR`（`venv/data-chrome`）+ `headless=False` |
| **验证方式** | 执行 `run.py --mode interactive --url <URL>`，浏览器正常打开，扩展图标出现，导航到 example.com 自动关闭 |
| **迁移方式** | 直接复制文件；若 Chrome 路径不同，修改 `lib/config.py` 中的 `CHROME_EXE` |

### 2. 修改 `debug/playwright/agent-verify/lib/extract_article.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/extract_article.py` |
| **变更类型** | 修改（同步 → 异步） |
| **修改内容** | `sync_playwright` → `async_playwright`；所有 `page.goto`/`page.evaluate` 等加 `await`；`asyncio.run()` 调用入口 |
| **作用** | 文章正文提取（Readability + Turndown + 图片下载），与交互模式统一异步架构 |
| **迁移方式** | 直接覆盖文件 |

### 3. 修改 `debug/playwright/agent-verify/lib/verify_agent.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/verify_agent.py` |
| **变更类型** | 修改（同步 → 异步） |
| **修改内容** | `sync_playwright` → `async_playwright`；截图/点击操作加 `await` |
| **作用** | 调试页验证逻辑，统一异步风格 |
| **迁移方式** | 直接覆盖文件 |

### 4. 修改 `debug/playwright/agent-verify/run.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/run.py` |
| **变更类型** | 修改 |
| **修改内容** | 交互/验证/提取分支统一用 `asyncio.run()` 调用异步函数；新增 `env-check`、`session-ttl`、`manifest` 模式 |
| **作用** | 统一入口，支持多种模式调用 |
| **迁移方式** | 直接覆盖文件 |

### 5. 新增 `debug/playwright/agent-verify/lib/playwright_env_check.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/playwright_env_check.py` |
| **变更类型** | 新建 |
| **作用** | 替代临时 `python -c` 检查，验证 playwright 包及 Chrome 可执行文件是否就绪 |
| **迁移方式** | 直接复制文件 |

### 6. 新增 `debug/playwright/agent-verify/lib/session_ttl_analyzer.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/session_ttl_analyzer.py` |
| **变更类型** | 新建 |
| **作用** | 分析 Chrome Cookies 有效期，输出保守有效期和续期窗口 |
| **迁移方式** | 直接复制文件 |

### 7. 新增 `debug/playwright/agent-verify/lib/manifest_reporter.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/manifest_reporter.py` |
| **变更类型** | 新建 |
| **作用** | 生成结构化 JSON manifest，归档每次执行结果到 `out/reports/` |
| **迁移方式** | 直接复制文件 |

### 8. 新增 `debug/playwright/agent-verify/lib/session_checker.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/session_checker.py` |
| **变更类型** | 新建（或修改，若之前已有） |
| **作用** | 读取 Chrome Cookies DB，检测头条系登录态标志 cookie |
| **迁移方式** | 直接复制文件 |

### 9. 新增 `docs/playbooks/playwright-chrome-extension-async-playbook.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/playbooks/playwright-chrome-extension-async-playbook.md` |
| **变更类型** | 新建 |
| **作用** | 完整操作指南：MVP 配置、异步事件驱动代码、扩展加载机制、7 个踩坑记录 |
| **迁移方式** | 直接复制文件；注意 LF 换行符 |

### 10. 修改 `docs/playbooks/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/playbooks/README.md` |
| **变更类型** | 修改 |
| **修改内容** | 导航表中新增 playbook 条目 |
| **迁移方式** | 编辑追加 |

### 11. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改 |
| **修改内容** | 更新 OpenCode 版本至 1.16.2；更新 Chrome 路径至 `D:\download\chrome-win64\chrome.exe`（后验证 Snapshot 也支持扩展，路径可回退） |
| **迁移方式** | 根据新环境实际路径调整；运行 `verify-runtime.ps1` 重新检测 |

### 12. 新增 `docs/tooling/gotchas/python-docstring-backslash-syntaxwarning.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/gotchas/python-docstring-backslash-syntaxwarning.md` |
| **变更类型** | 新建 |
| **作用** | 记录 docstring 中 Windows 路径反斜杠触发 SyntaxWarning 的陷阱 |
| **迁移方式** | 直接复制文件 |

### 13. 修改 `docs/tooling/gotchas/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/gotchas/README.md` |
| **变更类型** | 修改 |
| **修改内容** | 导航表中新增 gotcha 条目 |
| **迁移方式** | 编辑追加 |


## 二、非文本操作（文件系统/缓存迁移）

### 2.1 Chrome 扩展文件

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 扩展解压 | Obsidian Web Clipper ZIP | `venv/tmp/obsidian-web-clipper-clean/` | 扩展源文件（通过 Chrome UI 或 `--load-extension=` 注册到 Secure Preferences） |
| 扩展解压 | Test Extension ZIP | `venv/tmp/test-extension/` | 测试扩展源文件 |

> **关键验证**：Secure Preferences 记录的是**路径引用**，不是文件复制。原始目录必须持续存在。
> - 原始目录存在 → 扩展正常加载
> - 原始目录删除/改名 → 扩展消失（路径失效）
> - 重新指定 `--load-extension=` 新路径 → 扩展重新注册

### 2.2 Chrome 用户数据目录

| 操作类型 | 路径 | 说明 |
|---------|------|------|
| 目录使用 | `venv/data-chrome/` | Chrome `--user-data-dir`，持久化 Cookie、Session、扩展注册信息 |
| 子目录 | `venv/data-chrome/Default/` | Chrome Profile 默认目录 |
| 子目录 | `venv/data-chrome/Default/Extensions/` | **为空** — 未通过 Web Store 正式安装的扩展不会复制到此 |
| 文件 | `venv/data-chrome/Default/Secure Preferences` | 扩展注册信息（路径引用） |


## 三、环境变量速查

本次 session **未新增** `.vscode/settings.json` 环境变量，但涉及以下外部路径依赖：

```json
// lib/config.py 中硬编码（或从 verified-runtime-index.json 读取）
CHROME_EXE = r"D:\download\chrome-win\chrome.exe"
USER_DATA_DIR = r"D:\pjt\cursor\cs_py\venv\data-chrome"
```

跨环境迁移时，必须根据 `verify-runtime.ps1` 输出调整 `CHROME_EXE`。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 验证 Chrome 路径 | `Test-Path "D:\download\chrome-win\chrome.exe"` | `True` |
| 2 | 验证 Playwright 包 | `python -m py_compile debug/playwright/agent-verify/lib/interactive.py` | 无错误 |
| 3 | 启动交互模式 | `python run.py --mode interactive --url "https://example.com"` | 浏览器打开，example.com 自动关闭 |
| 4 | 验证扩展加载 | 观察地址栏右侧扩展图标 | Obsidian Web Clipper 图标出现 |
| 5 | 验证事件检测 | 导航到 example.com | 脚本自动关闭浏览器 |
| 6 | 验证 Session 保留 | 检查 `venv/data-chrome/Default/Network/Cookies` | 文件有更新 |
| 7 | 验证文章提取 | `python run.py --mode extract --url "<文章URL>"` | 生成 `.md` 文件到 `out/articles/` |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除新增 Python 模块 | 删除 `debug/playwright/agent-verify/lib/` 下新增/修改的 `.py` 文件 |
| 恢复同步版本 | 从 git history 恢复 `extract_article.py` 和 `verify_agent.py` 的同步版本 |
| 移除 playbook | 删除 `docs/playbooks/playwright-chrome-extension-async-playbook.md` 并从 README 移除导航条目 |
| 清理扩展记录 | 手动编辑 `venv/data-chrome/Default/Secure Preferences` 移除对应扩展条目（不推荐） |
| 删除 gotcha | 删除 `docs/tooling/gotchas/python-docstring-backslash-syntaxwarning.md` 并更新导航 |


## 六、核心踩坑记录（必须阅读）

本次 session 产生 7 个关键踩坑，详见 playbook 第 6 节：

1. **误把 "UI 不支持" 当作 "运行时不可用"** — Snapshot 不能通过 UI 安装扩展，但 `--load-extension=` 可以加载
2. **过度堆砌 `ignore_default_args`** — 实际上只需要 `ignore_default_args=["--disable-extensions"]` 一行
3. **同步轮询 vs 事件驱动** — 应该用 `page.on("load")` + `asyncio.Event`，不能用 `while True` 轮询
4. **`wait_for_url` 遇扩展操作崩溃就弃用正确架构** — 应隔离异常，而非弃用事件驱动
5. **docstring 反斜杠 SyntaxWarning** — 含反斜杠的 docstring 必须用 `r"""`
6. **每次启动重复指定 `--load-extension=` 导致重复实例** — 路径固定后无需重复指定
7. **自创 `extensions/` 目录是多此一举** — 扩展可以放在任何地方，`--load-extension=` 只认指定路径


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-08-080427 |
| **更新人** | Human + Agent Session |
| **变更触发** | 需要自动化访问需登录网页并提取文章，同时支持浏览器扩展 |
| **下次修订条件** | Chrome 路径变更、扩展机制新发现、Playwright 版本升级 |
| **跨环境迁移参考** | 直接复制相关文件 + 按「验证清单」逐条执行 + 调整 `CHROME_EXE` 路径 |


*文档生成时间：2026-06-08*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
