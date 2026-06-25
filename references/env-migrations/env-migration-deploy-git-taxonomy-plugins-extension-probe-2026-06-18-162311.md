---
title: deploy-git-isolated 脚本目录重构、Python 插件体系与扩展自动化探针
description: 本次 session 完成 deploy-git-isolated 脚本目录六向分类重构、Python 插件与工具链建设、Markdown frontmatter 边界治理、Chrome 扩展自动化触发全路径失败记录与 chrome_extension_manager 工具交付。
date: 2026-06-18
---

# env-migration-deploy-git-taxonomy-plugins-extension-probe-2026-06-18-162311

| 字段 | 值 |
|------|-----|
| **Session 主题** | deploy-git-isolated 脚本目录六向分类重构 + Python 插件体系建设 + Markdown frontmatter 边界治理 + Chrome 扩展自动化探针 |
| **日期** | 2026-06-18 |
| **文件名时间戳** | `2026-06-18-162311` |
| **触发原因** | 持续推进 deploy-git-isolated 任务工具链完善；探索 Obsidian Web Clipper 自动化触发；修复 Markdown 格式违规 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/` 目录结构、`py-plugins/` 与 `py-tools/` 工具链、AGENTS.md 搜索引擎优先级规则、临时测试产物 |
| **风险等级** | 中（涉及大量文件移动与路径变更，但已通过 Git 提交固化） |


## 一、文本文件变更清单

### 1. 重构 scripts/ 目录六向分类

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/` |
| **变更类型** | 目录重构 + 文件移动 + 内部路径修复 |
| **新增/修改内容** | 建立 `ps-steps/`、`ps-tools/`、`ps-examples/`、`py-steps/`、`py-tools/`、`py-examples/` 六个语义子目录；将原有 `.ps1` 脚本按语言+角色双语义迁入对应目录 |
| **插入位置** | 详见下方子目录说明 |
| **作用** | 解决脚本堆积根目录导致的 Agent 发现困难问题；与 github-lib.ps1 + lib-sort-rules.json 形成对称架构 |
| **验证方式** | `Get-ChildItem scripts/ps-steps/` 等子目录，确认文件存在且内部 `Join-Path` 路径指向正确 |
| **迁移方式** | Git 提交已固化（commit `ddb1fc3`），新环境直接 `git checkout` 即可恢复 |

**六向分类详情**：

| 子目录 | 角色 | 当前文件 |
|--------|------|---------|
| `ps-steps/` | PowerShell 步骤脚本（Ralph Loop 步骤） | 8 个 `github-step-*.ps1` |
| `ps-tools/` | PowerShell 工具脚本（可复用函数） | 10 个 `git-*/github-*.ps1` + `github-sync-issue-config.json` |
| `ps-examples/` | PowerShell 示例脚本 | 空（语义占位） |
| `py-steps/` | Python 步骤脚本 | 空（语义占位） |
| `py-tools/` | Python 工具脚本（CLI 工具） | `check-links.py`、`screenshot_verifier.py`、`chrome_extension_manager.py` |
| `py-examples/` | Python 示例脚本 | `usage-demo.py` |

**路径修复**：10 个迁移后的 `.ps1` 脚本内部对 `github-lib.ps1` 的引用路径已统一修复为：
```powershell
Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"
```

### 2. 提升 py_lib.py + py-sort-rules.json 到 scripts/ 根目录

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py_lib.py`<br>`references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 新建（对称于 `github-lib.ps1` + `lib-sort-rules.json`） |
| **新增/修改内容** | `py_lib.py`：Python 插件加载入口，支持拓扑排序、标签筛选、路径探测；`py-sort-rules.json`：8 个插件的依赖与标签配置 |
| **作用** | 建立 Python 侧的 "lib + sort-rules" 对称架构，Agent 可通过统一模式调用 PowerShell 或 Python 工具链 |
| **验证方式** | `python -c "import sys; sys.path.insert(0, 'scripts'); from py_lib import load_plugins; print('ok')"` |
| **迁移方式** | 直接复制提交后的文件即可 |

### 3. 新建 Python 插件体系（py-plugins/）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/*.py` |
| **变更类型** | 新建 8 个插件模块 |
| **作用** | 为 deploy-git-isolated 提供可复用的 Python 基础设施 |

| 模块 | 依赖 | 职责 |
|------|------|------|
| `detect_devroot.py` | — | 从 `__file__` 向上探测 devroot（定位到 `verified-runtime-index.json`） |
| `encoding.py` | — | `sys.stdout.reconfigure(encoding='utf-8')` 与恢复 |
| `constants.py` | `devroot` | 项目常量（路径、环境变量名） |
| `core.py` | `encoding` | 步骤头、日志、计时器、`StepContext`（Ralph Loop 审计追踪） |
| `env_config.py` | `constants` | `.env` 文件解析、必填项检查 |
| `link_checker.py` | `core`, `constants` | Markdown 内部相对链接有效性验证 |
| `md_lint.py` | — | **Markdown frontmatter 边界污染检测与修复**（检测正文 `---`） |
| `browser_session.py` | — | Chrome 持久化上下文管理器（Playwright），路径从 `verified-runtime-index.json` 读取 |

### 4. 新建 Python CLI 工具（py-tools/）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/*.py` |
| **变更类型** | 新建 3 个 CLI 工具 |

| 工具 | 职责 | 关键参数 |
|------|------|---------|
| `check-links.py` | 验证 Markdown 内部链接 | `--dir`, `--fix` |
| `screenshot_verifier.py` | URL 截图（支持全页、滚动到底部） | `--url`, `--output`, `--full-page`, `--scroll-bottom` |
| `chrome_extension_manager.py` | **Chrome 扩展 CRX 下载与解压** | `--extension-id`, `--store-url`, `--output-dir`, `--list-local`, `--search` |

**`chrome_extension_manager.py` 功能说明**：
- 支持从 Chrome Web Store 下载 CRX2/CRX3 格式扩展
- 支持 `--store-url` 自动解析扩展 ID（从 `chromewebstore.google.com/detail/<name>/<id>` 提取）
- 支持 `--list-local` 扫描本地 Chrome 扩展目录（项目隔离目录 + 系统默认目录）
- 支持 `--search` 关键词搜索（结果可能不完整，作为辅助）
- CRX 解压通过定位 ZIP 魔数 `PK\x03\x04` 实现，兼容 CRX 头部
- 代理支持：自动读取 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量
- 已验证下载：uBlock Origin (`cjpalhdlnbpafiamejdnhcphjbkeiagm`) 和 Obsidian Web Clipper (`cnjifjpddelmedmihgijeibhnjfabmlf`) 均成功

### 5. md_lint.py 修复 frontmatter 边界污染

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| **变更类型** | 新建 |
| **作用** | 检测并修复 Markdown 文件正文中的 `---` 水平分隔线（与 YAML frontmatter 定界符冲突，导致 Obsidian 解析失败） |
| **修复范围** | 13 个文件，67 处违规，全部移除正文 `---` |
| **验证方式** | `python md_lint.py --dir <目录> --fix` 后无 `BODY_HORIZON` 类型报错 |

### 6. 下游路径级联更新

| 属性 | 值 |
|------|-----|
| **路径** | `ENTRY.json`、`EXEC-CHEATSHEET.md`、`README.md`、`task-scenario-triggers.json`、`github-publish-playbook.md` |
| **变更类型** | 修改 |
| **作用** | 目录重构后，所有引用旧路径的文档必须同步更新，否则脚本/Agent 执行时会找不到文件 |
| **关键修复** | `task-scenario-triggers.json` 中 2 处失效的 `entry_script` 路径已修复（`step-07-verify.ps1` → `ps-tools/git-verify-isolation.ps1`，`step-04-config.ps1` → `ps-steps/github-step-01-init.ps1`） |

### 7. AGENTS.md 搜索引擎优先级更新

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 将 Bing（含 cn.bing）降级/禁用，提升 Google、GitHub Issues、Tavily 的优先级；明确禁止在 cn.bing 上反复重试技术 query |
| **作用** | 避免 Agent 在 Bing 上反复空转，缩短 issue 排查路径 |
| **验证方式** | `read venv/.opencode/AGENTS.md` 搜索 "搜索引擎优先级" 章节 |

### 8. docs/research/ 文档新建

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/research/scripts-directory-taxonomy-research.md`<br>`references/tasks/deploy-git-isolated/docs/research/task-dependency-graph.md` |
| **变更类型** | 新建 |
| **作用** | 记录目录分类决策依据（为何选择六向分类而非二向/三向）与完整依赖图谱，供后续目录变更时参考 |


## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| Git 提交 | — | — | commit `ddb1fc3`，55 files changed (+3,706 / -433)，branch `task/deploy-git-isolated` |
| Issue 评论更新 | — | GitHub Issue #1 | 通过 `github-sync-issue.ps1` 更新任务进度评论（Comment ID 4738904557） |
| 扩展目录新建 | — | `D:/download/obsidian-web-clipper` | 之前 session 已手动解压 Obsidian Web Clipper v1.7.0 |
| 扩展 CRX 下载测试 | Chrome Web Store | `venv/tmp/obsidian-test/` | 通过 `chrome_extension_manager.py` 验证性下载 Obsidian Web Clipper |
| 临时测试脚本 | — | `venv/tmp/test-clipper-*.py` | 3 个临时探针脚本（键盘事件、CDP context、DOM 扫描），已废弃可清理 |

### 复现命令（扩展管理器验证）

**全新扩展的标准操作流程**（不知道 ID 时）：

```powershell
# 第 1 步：搜索扩展名并验证候选 ID 的可下载性
${devroot}\venv\py\python.exe ${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\chrome_extension_manager.py `
  --search "Obsidian Web Clipper" --verify-search

# 第 2 步：从输出中复制验证通过的 ID（如 cnjifjpddelmedmihgijeibhnjfabmlf）
# 第 3 步：用该 ID 下载
${devroot}\venv\py\python.exe ${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\chrome_extension_manager.py `
  -e cnjifjpddelmedmihgijeibhnjfabmlf `
  -o "${env:TEMP}\obsidian-web-clipper"
```

**其他常用模式**：

```powershell
# 验证指定 ID 是否可下载（不实际下载）
${devroot}\venv\py\python.exe ${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\chrome_extension_manager.py `
  --verify-id cjpalhdlnbpafiamejdnhcphjbkeiagm

# 列出本地已安装扩展（仅适用于更新已有扩展）
${devroot}\venv\py\python.exe ${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\chrome_extension_manager.py --list-local

# 从 Web Store URL 解析 ID（注意：URL 中的 ID 可能无法下载）
${devroot}\venv\py\python.exe ${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\chrome_extension_manager.py `
  --store-url "https://chromewebstore.google.com/detail/obsidian-web-clipper/cphffgbbpfalkegcmnkdkdngdngfghdi" `
  -o "${env:TEMP}\obsidian-web-clipper"
```

> **重要**：`cphffgbbpfalkegcmnkdkdngdngfghdi` 是 Chrome Web Store 页面 URL 中的 ID，但实测该 ID 在 CRX 下载接口返回 404。正确的公开下载 ID 为 `cnjifjpddelmedmihgijeibhnjfabmlf`（通过 `--search --verify-search` 从搜索结果中验证获得）。这证明 **URL 中的 ID 与实际 CRX 下载 ID 可能不一致**。


## 三、环境变量速查

本次 session **未新增**环境变量。但涉及以下既有变量的使用：

- `HTTP_PROXY` / `HTTPS_PROXY`：`chrome_extension_manager.py` 自动读取用于 Chrome Web Store 下载
- `LOCALAPPDATA`：`chrome_extension_manager.py --list-local` 扫描系统 Chrome 扩展目录时使用


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `check-file-encoding.ps1` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.py`（新增脚本） | `python -m py_compile` | 语法正确性 | 无 SyntaxError |

**执行示例**：
```powershell
# Markdown 编码检查
powershell -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" `
  -Path "${devroot}\references\env-migrations\env-migration-deploy-git-taxonomy-plugins-extension-probe-2026-06-18-162311.md"

# Python 语法检查
${devroot}\venv\py\python.exe -m py_compile "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\chrome_extension_manager.py"
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认六向目录结构 | `Get-ChildItem ${devroot}\references\tasks\deploy-git-isolated\scripts\` | 存在 6 个子目录 + 4 个根锚点文件 |
| 2 | 确认 py_lib 可导入 | `python -c "import sys; sys.path.insert(0, 'scripts'); from py_lib import load_plugins; print('ok')"` | 输出 `ok` |
| 3 | 确认 md_lint 可运行 | `python scripts/py-plugins/md_lint.py --help` | 显示帮助 |
| 4 | 确认 browser_session 可运行 | `python scripts/py-plugins/browser_session.py --help` | 显示帮助 |
| 5 | 确认 chrome_extension_manager 功能完整 | `python scripts/py-tools/chrome_extension_manager.py --list-local` | 列出本地扩展 |
| 6 | 确认 Git 提交存在 | `git log --oneline -5` | 看到 `ddb1fc3` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 撤销目录重构 | `git revert ddb1fc3` 或 `git reset --hard <previous-commit>` |
| 恢复旧路径引用 | 重新运行路径修复脚本，或手动改回 `ENTRY.json` / `EXEC-CHEATSHEET.md` 等文档中的旧路径 |
| 清理临时测试脚本 | `Remove-Item -Recurse "${devroot}\venv\tmp\test-clipper-*"` |
| 清理下载测试产物 | `Remove-Item -Recurse "${devroot}\venv\tmp\extension-test*", "${devroot}\venv\tmp\obsidian-test"` |


## 七、关键踩坑记录（gotcha）

### 7.1 Chrome 扩展自动化触发 — 全路径失败

本次 session 对 Obsidian Web Clipper 进行了 6 种自动化触发尝试，**全部失败**，记录如下供后续参考：

| # | 方案 | 失败原因 | 结论 |
|---|------|---------|------|
| 1 | Playwright 点击扩展图标 | 浏览器工具栏在页面 DOM 之外 | **架构上不可行** |
| 2 | CDP `Input.dispatchKeyEvent` 模拟快捷键 | 扩展快捷键由 Chrome 扩展系统处理，不走页面键盘事件流 | **架构上不可行** |
| 3 | `Runtime.evaluate` 调用 `chrome.runtime.sendMessage` | 页面上下文无法访问 `chrome.runtime`（跨源隔离） | **安全模型限制** |
| 4 | 直接打开 `chrome-extension://popup.html` | Popup 需要活动标签页上下文，独立打开拿不到页面引用 | **缺少 tab 绑定** |
| 5 | CDP `Runtime.getExecutionContexts` | Playwright 的 CDP 封装层未暴露此方法 | **API 封装限制** |
| 6 | DOM 扫描注入元素 + 自定义事件 | 扩展内容脚本不注入可见 DOM 元素；自定义事件无响应 | **扩展设计如此** |

**最终转向方案**：不自动化扩展本身，而是自建剪藏逻辑（直接用 Playwright 提取页面内容生成 Markdown），或接受手动触发扩展。

### 7.2 扩展 ID 不一致与 "新扩展无本地 ID" 缺陷

**原始缺陷**：`chrome_extension_manager.py` 初版仅支持三种 ID 获取方式：直接指定、URL 解析、本地扫描（`--list-local`）。对于**全新扩展**（本地未安装），用户无法获取正确 ID，导致无法下载。

**扩展 ID 不一致陷阱**：Chrome Web Store 详情页 URL 中的 ID（`cphffgbbpfalkegcmnkdkdngdngfghdi`）与本地实际安装扩展的 ID（`cnjifjpddelmedmihgijeibhnjfabmlf`）不一致，且前者在 CRX 下载接口返回 404。原因可能是页面重定向、地区分发差异或 URL ID 与下载 ID 属于不同标识体系。

**修复措施**：
1. 增强 `--search`：解析搜索结果页提取候选 ID，并尝试从 URL slug 推断扩展名称
2. 新增 `--verify-search`：对每个候选 ID 发送 Range 请求（`bytes=0-1`）验证可下载性，过滤无效 ID
3. 新增 `--verify-id`：单独验证指定 ID 是否可下载，不实际下载
4. 下载前预验证：`-e` 模式自动先 Range 探测，确认有效后再全量下载，避免下载 4MB 后才发现 404
5. 强化错误提示：404 时自动提示"用 --search 搜索扩展名确认正确 ID"

**新的标准操作流程（全新扩展）**：
```powershell
# 第 1 步：搜索并验证
python chrome_extension_manager.py --search "Obsidian Web Clipper" --verify-search
# 第 2 步：从输出中复制验证通过的 ID
# 第 3 步：下载
python chrome_extension_manager.py -e <验证通过的ID> -o <输出目录>
```

**实测结果**：`--search "Obsidian Web Clipper" --verify-search` 返回 10 个候选，全部验证通过，其中 `cnjifjpddelmedmihgijeibhnjfabmlf` 为正确的 Obsidian Web Clipper ID。

### 7.3 Markdown frontmatter `---` 污染

Obsidian 使用 `---` 作为 YAML frontmatter 的定界符。正文中的 `---` 水平分隔线会导致解析器混淆。本次 session 在 13 个文件中发现了 67 处此类违规，全部移除（不替换为 `***`，避免任何类似语法继续引发歧义）。


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-18-162311 |
| **更新人** | Human + Agent Session |
| **变更触发** | deploy-git-isolated 任务持续推进 + Obsidian Web Clipper 自动化需求 |
| **下次修订条件** | 若目录结构再次变更、新增 py-tools 工具、扩展自动化取得突破 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 + 运行 `chrome_extension_manager.py --list-local` 确认本地扩展 ID |


*文档生成时间：2026-06-18*  
*模板版本：v2*
