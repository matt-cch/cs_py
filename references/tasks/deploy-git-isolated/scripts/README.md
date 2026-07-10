---
title: scripts 目录索引
description: deploy-git-isolated task 的 scripts/ 目录总览与导航。串接 PowerShell / Python / JS 三层工具链入口。
date: 2026-07-07
meta:
  version: 1.0.0
---

# scripts 目录说明

本目录是 `deploy-git-isolated` task 的**脚本资产根**，按技术栈分为 PowerShell、Python、JS 三条线，各有一套「统一入口 + 配置真源 + 插件/工具」的对称结构。


## 目录总览

```
scripts/
├── py_lib.py              # Python 统一入口（Layer 2）
├── py-sort-rules.json     # Python 插件注册表 + Profile 定义
├── py-plugins/            # Python 底座插件（Layer 1）
├── py-steps/              # Python 版 Step 脚本（被 workflow 调用）
├── py-tools/              # Python Workflow 脚本（Layer 3）← 主要可执行入口
│
├── github-lib.ps1         # PowerShell 统一入口（对称于 py_lib.py）
├── lib-sort-rules.json    # PS 插件注册表 + Profile 定义
├── lib-plugins/           # PS 共享函数插件
├── ps-steps/              # PS 版 Step 1-8 脚本
├── ps-tools/              # PS 工具脚本（安全检查、Issue 同步等）
│
├── js_lib.js              # JS 统一入口（对称于 py_lib.py）
├── js-sort-rules.json     # JS 资产注册表
├── js-plugins/            # JS 可复用模块（dual-mode）
├── js-tools/              # JS 浏览器注入工具 / CLI 工具
│
├── py-examples/           # Python 示例代码
├── ps-examples/           # PowerShell 示例代码
└── EXEC-CHEATSHEET.md     # 执行速查（命令 + 配置 + 参数）
```


## 各层导航

| 入口 / 目录 | 职责 | 进一步阅读 |
|------------|------|-----------|
| `py-tools/` | **Python Workflow 脚本**（lint、部署、归档、运行时、PR、Agent 等） | [py-tools/README.md](py-tools/README.md) |
| `py-tools/workflow-gh-pr.py` | 🔀 **GitHub PR 自闭环**（gh CLI 编排：create→merge→cleanup→pull） | [EXEC-CHEATSHEET.md](EXEC-CHEATSHEET.md) Stage S7.2 |
| `py-tools/gh-pr-create.py` / `gh-pr-merge.py` / `gh-branch-protect.py` | 🔀 **PR 子脚本**（创建/合并/分支保护） | [EXEC-CHEATSHEET.md](EXEC-CHEATSHEET.md) Stage S7.2 |
| `py-tools/gh_preflight.py`（py-plugins） | 🔀 **gh CLI 前置检测插件**（gh.exe + PAT + 认证 → GhContext） | [TASK-TOOLS-INDEX.md](../TASK-TOOLS-INDEX.md) 1.10 |
| `py-plugins/` | Python 底座插件（34 个），**禁止越级直接 import** | 通过 `py_lib.load_plugins()` 访问 |
| `ps-steps/` | PowerShell Step 1-8（Git init → upstream） | [task 总索引](../README.md) 场景 A |
| `ps-tools/` | PS 工具（安全检查、Issue 同步、通用包装器） | [task 总索引](../README.md) 场景 C-F |
| `js-tools/` | JS 浏览器注入工具（Readability、Turndown、文章提取） | [py-tools/README.md](py-tools/README.md) 文章下载节 |
| `py-tools/atomic-check-chrome-session.py` | 🌐 **Chrome Session 检测**：登录态 / TTL / 新鲜度 / manifest 落盘 | [EXEC-CHEATSHEET.md](EXEC-CHEATSHEET.md) Stage S6.5 |
| `py-tools/download-article.py` | 🌐 **文章下载**：Playwright + Chrome 持久化上下文提取头条文章 | [EXEC-CHEATSHEET.md](EXEC-CHEATSHEET.md) 文章下载 |
| `py-tools/screenshot_verifier.py` | 🌐 **截图验证**：Playwright + 已保存 Chrome Session | [EXEC-CHEATSHEET.md](EXEC-CHEATSHEET.md) 截图验证 |
| `EXEC-CHEATSHEET.md` | 命令速查真源（复制粘贴即用） | [EXEC-CHEATSHEET.md](EXEC-CHEATSHEET.md) |


## 三层架构速查（Python 侧）

```
Layer 3: Workflow  →  py-tools/    → 直接执行
Layer 2: Entry     →  py_lib.py    → 统一加载插件
Layer 1: Plugins   →  py-plugins/  → 禁止越级直接 import
```

> 铁律：`py-plugins/` 下的插件只能通过 `py_lib.load_plugins()` 调用，Workflow 禁止直接 `import`。


## 上级导航

- [task 总索引](../README.md)
- [deploy-git-isolated 设计文档](../DESIGN.md)
- [TASK-TOOLS-INDEX.md](../TASK-TOOLS-INDEX.md)
