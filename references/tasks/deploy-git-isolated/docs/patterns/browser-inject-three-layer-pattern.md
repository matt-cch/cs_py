---
title: 浏览器注入三层架构 — JS 资产体系 + Playwright 注入模式
description: 通过 js-plugins/（可复用模块）+ js-tools/（完整脚本）+ js-sort-rules.json（依赖拓扑）三层结构 + Playwright add_init_script 注入，实现跨语言（Python↔JS）、跨环境（Node CLI↔浏览器）的统一 JS 资产体系。
date: 2026-06-24
meta: {}
---

# 浏览器注入三层架构 — JS 资产体系 + Playwright 注入模式

> **来源**：deploy-git-isolated task 的 JS 工具链演进（文章下载流水线）。
> **核心洞察**：JS 资产必须同时服务 Node.js CLI（`require()`）和浏览器注入（`add_script_tag` / `add_init_script`），且依赖拓扑必须由机器可读的 JSON 驱动，不能硬编码在 Python 或 JS 源码中。

## 1. 三层结构

```
┌───────────────────────────────────────────────┐
│  入口层（Entry）                               │
│  js_lib.js (Node.js)                          │
│  js_loader.py (Python 桥接)                   │
│  职责：读取 JSON → 拓扑排序 → 返回有序路径     │
├───────────────────────────────────────────────┤
│  配置层（Registry）                            │
│  js-sort-rules.json                           │
│  职责：资产注册 + 依赖拓扑 + type 字段          │
│  type: browser | node | dual                  │
├───────────────────────────────────────────────┤
│  实现层（Implementation）                      │
│  js-plugins/ → 可复用模块（dual-mode）         │
│  js-tools/   → 完整可注入脚本（含自执行入口）   │
└───────────────────────────────────────────────┘
```

### 1.1 入口层

| 入口 | 语言 | 环境 | 入口函数 |
|------|------|------|---------|
| `js_lib.js` | Node.js | `node js_lib.js --resolve <tool>` | `require()` programmatic |
| `js_loader.py` | Python | 被 `article_extractor.py` 调用 | `resolve_script_tags()` |

`js_lib.js` 对标 `py_lib.py`，`js_loader.py` 对标 `github-lib.ps1`。三者支撑同一套 JSON 注册表。

### 1.2 配置层

`js-sort-rules.json` 的核心字段：

```json
{
  "version": "1.2.0",
  "plugins": [
    {
      "name": "url-utils",
      "file": "url-utils.js",
      "type": "dual",
      "layer": "atomic",
      "depends": [],
      "description": "URL 工具集：toAbsoluteURI、guessImageExt、isImageUrl"
    }
  ],
  "tools": [
    {
      "name": "extract-article",
      "file": "extract-article.js",
      "type": "browser",
      "layer": "workflow",
      "depends": ["readability", "turndown"],
      "description": "文章提取 workflow：浏览器注入"
    },
    {
      "name": "url-analyze",
      "file": "url-analyze.js",
      "type": "dual",
      "layer": "atomic",
      "depends": ["url-utils"],
      "description": "URL 分析工具，CLI + 浏览器双模式"
    }
  ]
}
```

| 字段 | 含义 |
|------|------|
| `plugins[]` | js-plugins/ 下的可复用模块 |
| `tools[]` | js-tools/ 下的完整脚本 |
| `.type` | `browser`（仅浏览器注入）、`node`（仅 Node.js CLI）、`dual`（双模式） |
| `.layer` | `atomic`（基础模块）、`workflow`（组合多个 atomic） |
| `.depends` | 拓扑依赖，`js_lib.resolve()` 按此排序 |

### 1.3 实现层

**js-plugins/（可复用模块，dual-mode）**：

```javascript
(function (global) {
  'use strict';
  var MyModule = { ... };
  // 浏览器
  if (typeof window !== 'undefined') global.__MY_MODULE = MyModule;
  // Node.js
  if (typeof module !== 'undefined' && module.exports) module.exports = MyModule;
})(typeof window !== 'undefined' ? window : global);
```

**js-tools/（完整脚本）**：

| 子类型 | 特征 | 示例 |
|--------|------|------|
| `browser` | 通过 `add_init_script` 注入，注册 `window.__xxx` | `readability.js`, `turndown.js`, `extract-article.js` |
| `dual` | 浏览器注入 + Node.js CLI 双入口 | `url-analyze.js` |
| `node` | 仅 Node.js CLI，使用 `require('js_lib.js')` | — |

## 2. Playwright 注入策略

### 2.1 CSP 处理矩阵

| 站点 CSP | Playwright API | 条件 |
|---------|---------------|------|
| 宽松（允许 unsafe-inline） | `page.add_script_tag(path=)` | 直接可用 |
| 严格（禁止 script-src-elem inline） | `context.add_init_script(合并JS)` | **必须合并全部 JS 为单次调用**（见 gotcha） |

### 2.2 标准注入流程

```python
# layer 1: py-plugins/article_extractor.py
js_paths = js_loader.resolve_script_tags(tool_names=["extract-article"])
# → [js-plugins/url-utils.js, js-plugins/markdown-rules.js,
#    js-tools/readability.js, js-tools/turndown.js,
#    js-tools/extract-article.js]

# 合并全部 JS → 单次 init script（绕过 CSP + 避免作用域隔离）
combined = "\n".join(Path(p).read_text() for p in js_paths)
await context.add_init_script(combined)

# 导航后执行
await page.goto(url)
result = await page.evaluate("window.__extractArticle()")
```

### 2.3 加载顺序

拓扑排序确保依赖先加载：

1. js-plugins/url-utils.js（注册 `window.__URL_UTILS`）
2. js-plugins/markdown-rules.js（注册 `window.__MARKDOWN_RULES`）
3. js-tools/readability.js（注册 `window.Readability`）
4. js-tools/turndown.js（注册 `window.TurndownService`）
5. js-tools/extract-article.js（注册 `window.__extractArticle`，引用 Readability + TurndownService）

## 3. 跨语言桥接

```
Python side                        JS side (Chrome)
─────────────────                  ────────────────
article_extractor.py ──→ context.add_init_script(合并JS)
    ↕ js_loader.py                      ↕
    ↕ js-sort-rules.json                ↕
    ↕ js_paths 列表                      ↕
                          page.goto(url)
                          page.evaluate("__extractArticle()")
                          ↑ 返回值 ← extract-article.js
```

`js_loader.py` 是纯 Python 桥接，读取同一份 JSON，做拓扑排序，返回绝对路径列表。不执行任何 JS，不做任何网络请求。

## 4. 适用范围

| 场景 | 推荐方案 | 说明 |
|------|---------|------|
| 需要从 URL 提取正文 | `download-article.py` | CLI 入口，走三层注入 |
| 需要分析 URL 图片属性 | `url-analyze.js` CLI 或 `__URL_ANALYZE()` | 纯 JS，Node/browser 均可 |
| 新增 JS 工具脚本 | 放 js-tools/ + 登记 js-sort-rules.json | 沿用现有拓扑排序 |
| 新增 JS 可复用模块 | 放 js-plugins/ + 登记 js-sort-rules.json | 要求 dual-mode |
| 从 Python 调用 JS 工具（浏览器场景） | `js_loader.resolve_script_tags()` → `add_init_script` | 不要硬编码路径 |

## 5. 关联文档

- `gotchas/browser-add-init-script-scope-isolation.md` — `add_init_script` 作用域隔离踩坑记录
- `docs/patterns/manifest-plugin-pattern.md` — 三元索引（ENTRY + TOOLS-INDEX + plugins）基础模式
- `scripts/js_lib.js` — Node.js 侧入口
- `scripts/py-plugins/js_loader.py` — Python 侧桥接
- `scripts/js-sort-rules.json` — JS 资产注册表
- `scripts/py-plugins/article_extractor.py` — 浏览器注入编排


*模式版本: v1.0*
*创建时间: 2026-06-24*
