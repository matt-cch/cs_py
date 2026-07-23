---
title: Tree-sitter 知识体系梳理 + 网页文章提取工具链建设
description: 调研 venv/data-opencode/opentui/tree-sitter 目录来源与 tree-sitter 核心用途；构建 Playwright+Chrome Session+Readability+Turndown 网页转 Markdown 工具链，解决 Agent 无法直接阅读需登录网页的问题。date: 2026-06-04
---

# env-migration-tree-sitter-article-pipeline-2026-06-04-175042

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Tree-sitter 知识体系梳理 + 网页文章提取工具链建设 |
| **日期** | 2026-06-04 |
| **文件名时间戳** | `2026-06-04-175042` |
| **触发原因** | 1) 用户发现 `venv/data-opencode/opentui/tree-sitter` 目录，要求调研来源与用途；2) 准备将 tree-sitter 集成到本项目工具中（tree-sitter + sqlite + fts5 + sqlite-vec 组合）；3) 需要阅读一篇需登录的头条文章，由此催生了完整的网页→Markdown 提取工具链 |
| **影响范围** | `debug/playwright/agent-verify/`（既有验证脚本重构为插件架构）、新增 `lib/` 插件目录、新增 `out/articles/` 输出目录、新增 JS 依赖（readability.js + turndown.js） |
| **风险等级** | 低（纯工具链/调试能力建设，不涉及业务代码） |


## 一、文本文件变更清单

### 1. 重构 `debug/playwright/agent-verify/run.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/run.py` |
| **变更类型** | `重写` |
| **新增/修改内容** | 从单文件臃肿脚本重构为入口编排 + 插件导入架构；新增 `--mode` 参数支持 `verify` / `interactive` / `check-session` / `extract` |
| **作用** | 入口只做流程编排，具体逻辑由 `lib/` 下各模块实现，避免入口文件持续膨胀 |
| **验证方式** | `D:\pjt\cursor\cs_py\venv\py\python.exe D:\pjt\cursor\cs_py\debug\playwright\agent-verify\run.py --mode check-session` |
| **迁移方式** | 直接替换（旧逻辑已完整迁移到 `lib/` 各模块） |

### 2. 新增 `debug/playwright/agent-verify/lib/config.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/config.py` |
| **变更类型** | `新建` |
| **作用** | 统一常量定义（BASE_URL, CHROME_EXE, USER_DATA_DIR, OUT_DIR）和日志函数 `log()` |
| **迁移方式** | 无需迁移，新环境直接存在 |

### 3. 新增 `debug/playwright/agent-verify/lib/session_checker.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/session_checker.py` |
| **变更类型** | `新建` |
| **作用** | Cookies/Session 状态实测检测：读取 Chrome `Default/Network/Cookies` SQLite DB，通过 cookie 存在性 + 字段名（sessionid, passport_auth_status 等）+ 时间戳（最近 10 分钟活跃）给出有实测依据的登录态判定 |
| **验证方式** | `run.py --mode check-session` |

### 4. 新增 `debug/playwright/agent-verify/lib/verify_agent.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/verify_agent.py` |
| **变更类型** | `新建` |
| **作用** | 原有 Agent 调试页 + ISO Agent 页验证逻辑，从 `run.py` 迁移而来 |
| **验证方式** | `run.py --mode verify` |

### 5. 新增 `debug/playwright/agent-verify/lib/interactive.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/interactive.py` |
| **变更类型** | `新建` |
| **作用** | 交互式浏览器启动：`headless=False`，打开指定 URL，等待用户导航到 `example.com` 后自动关闭，session/cookies 保留在 `venv/data-chrome` |
| **验证方式** | `run.py --mode interactive --url <URL>` |

### 6. 新增 `debug/playwright/agent-verify/lib/extract_article.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/extract_article.py` |
| **变更类型** | `新建` |
| **作用** | 网页文章提取插件：Playwright headless + 已有 session → 注入 Mozilla Readability.js + Turndown.js → 页面内提取正文 HTML → 转 Markdown → 下载图片到本地 assets → 输出带 frontmatter 的 `.md` 文件 |
| **关键参数** | `--mode extract --url <URL> --tags "tag1,tag2"` |
| **输出位置** | `out/articles/<slug>.md` + `out/articles/<slug>_files/`（本地图片） |
| **验证方式** | `run.py --mode extract --url "https://www.toutiao.com/article/7646900458186883619/" --tags "OpenCode,LSP,代码重构"` |

### 7. 新增 `debug/playwright/agent-verify/lib/readability.js`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/readability.js` |
| **变更类型** | `新建`（外部下载） |
| **来源** | https://raw.githubusercontent.com/mozilla/readability/main/Readability.js |
| **作用** | Firefox 阅读模式核心库，从任意网页智能提取正文 HTML（去广告、去导航、自动识别正文容器） |
| **大小** | ~91KB |

### 8. 新增 `debug/playwright/agent-verify/lib/turndown.js`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/turndown.js` |
| **变更类型** | `新建`（外部下载） |
| **来源** | https://unpkg.com/turndown@7.2.0/dist/turndown.js |
| **作用** | HTML → Markdown 转换，与 Readability 配套使用，保留图片、链接、列表、表格等结构 |
| **大小** | ~27KB |

### 9. 新增 `debug/playwright/agent-verify/lib/__init__.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/playwright/agent-verify/lib/__init__.py` |
| **变更类型** | `新建`（空文件） |
| **作用** | 符合项目 `__init__.py` 空文件约定 |


## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 目录创建 | — | `out/articles/` | 文章提取输出目录 |
| JS 库下载 | GitHub / unpkg | `debug/playwright/agent-verify/lib/readability.js` | Mozilla Readability.js |
| JS 库下载 | unpkg | `debug/playwright/agent-verify/lib/turndown.js` | Turndown.js |


## 三、Tree-sitter 知识体系（本次调研核心结论）

### 3.1 本地目录来源

`venv/data-opencode/opentui/tree-sitter/` 内容：

```
tree-sitter/
├── languages/
│   ├── tree-sitter-json.wasm   # JSON 语法解析器（WASM）
│   └── tree-sitter-python.wasm # Python 语法解析器（WASM）
└── queries/
    ├── json-256dee0a.scm       # JSON 语法高亮/查询规则
    └── python-124e65af.scm     # Python 语法高亮/查询规则
```

**来源判断**：网络搜索未找到与 `opentui` 直接对应的开源项目。结合目录位于 `data-opencode/` 下，最可能是用户本人或某次实验性工具安装的产物，非知名第三方残留。

**本质**：tree-sitter 的 **Web binding** 标准部署形态——WASM 格式解析器 + `.scm` Query 规则文件，用于浏览器/Node.js 环境中的语法高亮与结构搜索。

### 3.2 Tree-sitter 核心定位

> *A parser generator tool and an incremental parsing library.* — 官方定义

**四大特性**：通用（50+ 语言）、极速（增量解析，每按键一次就解析一次）、鲁棒（语法错误时仍产出有意义的 AST）、零依赖（纯 C11 运行时）。

**核心概念**：

```
源代码文本
    ↓
Tree-sitter Parser (按语言语法规则)
    ↓
Concrete Syntax Tree (CST) —— 包含每个 token 的完整树
    ↓
Named nodes / Anonymous nodes 区分
    ↓
Query (.scm) 模式匹配 → 提取语义信息
```

**Query 语言示例**：

```scheme
; 匹配函数定义，将函数名捕获为 @function
(function_definition
  name: (identifier) @function)

; 匹配赋值表达式左侧是成员访问的情况
(assignment_expression
  left: (member_expression
    object: (call_expression)))
```

### 3.3 主流应用场景

| 场景 | 代表项目 |
|------|---------|
| 编辑器语法高亮 | Neovim（内置）、Helix、Zed、Emacs (treesit) |
| 代码结构搜索/替换 | ast-grep（14.3k⭐） |
| 代码智能/导航 | GitHub Code Search、Sourcegraph |
| 静态分析/Lint | 自定义规则引擎 |
| 文档提取 | 从代码中提取 API 文档、函数签名 |

### 3.4 Tree-sitter + SQLite + FTS5 + sqlite-vec 组合应用架构

**各组件职责**：

| 组件 | 职责 | 在本项目中的角色 |
|------|------|----------------|
| **Tree-sitter** | 解析源码 → CST/AST → 提取结构化信息（函数、类、调用关系、变量等） | **数据生产端** |
| **SQLite** | 轻量级关系型存储 | **统一存储层** |
| **FTS5** | SQLite 内置全文搜索引擎 | **文本级检索**（函数名、变量名、注释、文档字符串） |
| **sqlite-vec** | SQLite 向量搜索扩展（KNN、相似度搜索） | **语义级检索**（代码嵌入向量的相似度匹配） |

**组合架构设计**：

```
代码库目录 (Python/JS/TS/Java/C++/... 混合项目)
    ↓
1. Tree-sitter 解析层
   • 遍历每个源码文件
   • Query 提取：函数定义、类定义、导入语句、调用图、注释
   • 输出结构化记录：{file, line, col, node_type, text, ...}
    ↓
2. Embedding 层 (可选)
   • 对函数体/类体生成代码嵌入向量
   • 可用本地模型 (sentence-transformers/code-bert) 或远程 API (OpenAI/Ollama)
    ↓
3. SQLite 存储层
   ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐
   │ symbols 表   │  │ fts5 虚表    │  │ vec0 虚表          │
   │ (结构化信息) │  │ (全文索引)   │  │ (向量索引)         │
   └──────────────┘  └──────────────┘  └────────────────────┘
    ↓
4. 查询层
   • 精确查询 → SQL 直接查 symbols
   • 文本模糊 → MATCH 'fts5_query'
   • 语义相似 → vec0 KNN search
   • 混合搜索 → 先 fts5 粗筛 + vec0 精排 / reciprocal rank
```

**具体应用方案**：

- **方案 A：本地代码搜索引擎（类小型 Sourcegraph）**
  - Tree-sitter 提取所有函数定义 + 函数体文本 + docstring
  - FTS5 对函数名/docstring/注释建立全文索引
  - sqlite-vec 将函数体通过代码嵌入模型转为向量，支持语义查询

- **方案 B：代码知识图谱**
  - Tree-sitter Query 提取 import 语句、函数调用关系
  - SQLite 存储符号表 + 边表（调用图）
  - 支持跨文件依赖分析

- **方案 C：智能代码补全/上下文检索（RAG for Code）**
  - 用户输入查询 → sqlite-vec 语义召回 Top-K 相关代码块
  - FTS5 做关键词召回（补充精确匹配）
  - Tree-sitter 校验召回代码块的语法完整性
  - 将上下文注入 LLM Prompt

### 3.5 可参考的开源项目

| 项目 | 说明 | 与本项目的关联 |
|------|------|-------------|
| **ast-grep** (14.3k⭐) | 基于 tree-sitter 的代码结构搜索/替换 CLI | 直接学习其 Query 用法和 AST 遍历模式 |
| **sqlite-vec** (7.7k⭐) | SQLite 向量搜索扩展 | 本组合方案的核心向量检索组件 |
| **sqlite-lembed** | 本地 GGUF 模型嵌入生成 | 若想在 SQLite 内直接生成代码嵌入，无需外部 Python |
| **tree-sitter 官方文档** | 权威参考 | Query 语法、Node API、WASM binding |


## 四、网页文章提取工具链详情

### 4.1 为什么需要这个工具链

头条文章（`https://www.toutiao.com/article/...`）有严格反爬虫机制，Agent 通过程序化 HTTP 请求（`webfetch`）无法获取正文内容（返回空白）。

解决方案：**Playwright + 持久化 Chrome Profile（`--user-data-dir`）+ 用户手动登录 → Session 保留 → 后续 headless 自动访问**。

### 4.2 Session 持久化机制

| 组件 | 路径 |
|------|------|
| Chrome 可执行文件 | `D:\download\chrome-win\chrome.exe` |
| 用户数据目录 | `D:\pjt\cursor\cs_py\venv\data-chrome` |
| Cookies DB | `venv/data-chrome/Default/Network/Cookies` |

**Session 生效的实测依据**（非猜测）：

- `sessionid`、`sessionid_ss`、`passport_auth_status`、`passport_csrf_token`、`odin_tt` 等登录态标志 cookie 存在
- `last_access_utc` 时间戳在 10 分钟内（证明是本次操作生成，非历史残留）
- Headless 模式下访问头条文章 URL 未被重定向，页面标题正确，无登录提示

### 4.3 提取流程

```
URL → Playwright headless → 已有 session 自动登录
    → 滚动触发懒加载（5 次 scroll + 1.5s 等待）
    → 注入 Readability.js + Turndown.js
    → 页面内执行：Readability.parse() → 正文 HTML
    → Turndown.turndown() → Markdown
    → 提取所有图片 URL
    → Playwright page.request.get() 下载图片（自动带 cookies/referer）
    → Markdown 中图片链接替换为相对路径
    → 输出：out/articles/<slug>.md + <slug>_files/（本地图片）
```

### 4.4 输出格式示例

```markdown
title: OpenCode系统性入门 06 | LSP神器加持：代码重构从未如此简单
description: 引言：告别"到处搜代码"的痛苦...
date: 2026-06-04
source: https://www.toutiao.com/article/7646900458186883619/
tags: ["OpenCode", "LSP", "代码重构"]

# OpenCode系统性入门 06 | LSP神器加持：代码重构从未如此简单

> 来源: [URL](URL)
> 提取时间: 2026-06-04T09:41:16+0000

## 引言：告别"到处搜代码"的痛苦
...
![](./slug_files/img-001.jpeg)
```


## 五、环境变量速查

无新增环境变量。所有路径硬编码在 `lib/config.py` 中：

```python
CHROME_EXE = r"D:\download\chrome-win\chrome.exe"
USER_DATA_DIR = r"D:\pjt\cursor\cs_py\venv\data-chrome"
OUT_DIR = Path(r"D:\pjt\cursor\cs_py\out\articles")
```


## 六、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | Session 检测 | `run.py --mode check-session` | 输出头条系 cookie 数量、登录态标志、时间戳 |
| 2 | 交互式登录 | `run.py --mode interactive --url <头条文章URL>` | 浏览器弹出，手动登录后导航到 example.com 自动关闭 |
| 3 | 文章提取 | `run.py --mode extract --url <头条文章URL> --tags "test"` | `out/articles/` 下生成 `.md` + `_files/` 目录，图片非 0 bytes |
| 4 | Markdown 预览 | 在 Cursor/VS Code 中打开生成的 `.md`，按 `Ctrl+Shift+V` | 图片正常显示，正文结构完整 |


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增 JS 库 | `Remove-Item "debug\playwright\agent-verify\lib\readability.js"`、`Remove-Item "debug\playwright\agent-verify\lib\turndown.js"` |
| 恢复旧 `run.py` | 从 git 回滚（旧逻辑已完整保留在 `verify_agent.py` 中，但入口调度逻辑是新增） |
| 删除提取输出 | `Remove-Item -Recurse "out\articles"` |
| 清理 Chrome session | 删除 `venv\data-chrome\Default\Network\Cookies`（或整个 `data-chrome` 目录重建） |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-04-175042 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求调研 tree-sitter 目录来源 + 阅读需登录的头条文章 |
| **下次修订条件** | 1) 开始实施 tree-sitter + sqlite + fts5 + sqlite-vec 组合方案；2) 提取工具链需要支持更多站点（如微信公众号、知乎等） |
| **跨环境迁移参考** | 复制 `lib/readability.js` + `lib/turndown.js` + `lib/*.py` 到目标环境，按验证清单执行 |


*文档生成时间：2026-06-04*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
