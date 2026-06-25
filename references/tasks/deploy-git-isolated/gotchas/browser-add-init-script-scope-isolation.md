---
title: Playwright add_init_script 作用域隔离踩坑记录
description: 多次 add_init_script 调用各自独立作用域，var 声明不共享。必须合并全部 JS 为单次调用。
date: 2026-06-24
meta: {}
---

# Playwright add_init_script 作用域隔离踩坑记录

## 现象

使用 `page.add_script_tag(path=` 向 CSP 严格站点注入 JS 时被拦截。改为 `context.add_init_script()` 后，`window.__extractArticle` 可用但调用的 `Readability` / `TurndownService` 未定义：

```
Page.evaluate: ReferenceError: Readability is not defined
    at window.__extractArticle (<anonymous>:5:18)
```

`window.__extractArticle` 正常注册（extract-article.js 用 `window.__extractArticle = fn`），但 `Readability` 未定义（readability.js 用 `var Readability = fn`）。

## 根因

Playwright 的 `add_init_script()` 每次调用创建一个**独立的 V8 内容脚本（content script）作用域**：

```python
# ❌ 错误：三个独立作用域
await context.add_init_script(readability_js)   # 作用域 A：var Readability
await context.add_init_script(turndown_js)      # 作用域 B：var TurndownService
await context.add_init_script(extract_js)       # 作用域 C：var __extractArticle
```

作用域 A/B/C 互相隔离——`__extractArticle` 在 C 中引用的 `Readability` / `TurndownService` 是**自由变量**，不在 C 的作用域链内，因此 `ReferenceError`。

这与 `page.evaluate()` 每次调用独立上下文同理。

## 修复方式

合并全部 JS 源文件为**一个字符串**，单次 `add_init_script` 调用：

```python
# ✅ 正确：合并为单一作用域
combined_js = "\n".join(
    Path(p).read_text(encoding="utf-8") for p in js_paths
)
await context.add_init_script(combined_js)
```

同一作用域内，`var Readability` / `var TurndownService` / `window.__extractArticle` 共享变量环境，相互可见。

## 适用范围

| 场景 | 适用方案 |
|------|---------|
| **CSP 宽松站点** | `add_script_tag(path=)` 或 `add_script_tag(content=)` 均可 |
| **CSP 严格站点**（script-src 无 unsafe-inline） | `add_init_script(合并JS)` |
| **必须在 DOM 就绪后注入** | `add_init_script` in context → `goto()`（注入在页面脚本执行前） |
| **需要注入后立即导航** | 同上，init script 在每次导航时自动重跑 |

## 涉事脚本

- `article_extractor.py` — 调用线：`extract_article()` → `js_paths` → `add_init_script(combined_js)` → `goto()` → `evaluate("__extractArticle()")`

## 验证方式

```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-article.py" --url "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction" --headless --devroot "${devroot}"
```

正常输出 `✅ 文章已保存`。

## 反模式

- ❌ 多次 `add_init_script()` 分别加载 JS 文件
- ❌ 期望 `var` 跨 `add_init_script` 调用可见（违背 content script 设计）
- ❌ CSP 被拦截后直接放弃注入（改用 `add_init_script` 非 `add_script_tag`）

## 关联

- [`docs/patterns/browser-inject-three-layer-pattern.md`](../docs/patterns/browser-inject-three-layer-pattern.md) — 浏览器注入三层架构
- `article_extractor.py` — 本次修复的编排插件
- `js-plugins/` / `js-tools/` — JS 资产目录


*记录时间: 2026-06-24*
*教训等级: 高（2 次迭代浪费）*
*避免方式: 合并全部 JS → 单次 add_init_script*
