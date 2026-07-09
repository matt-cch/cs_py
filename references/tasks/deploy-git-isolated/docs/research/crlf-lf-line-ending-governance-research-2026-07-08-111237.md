---
title: CRLF/LF 换行符治理深度研究 — 全仓库文本文件强制 LF 的决策路径
description: 从 lint_encoding.py 的 .json CRLF 漏检事件出发，全面研究各文件类型的换行符规范、系统默认行为、.gitattributes 作用域边界、core.autocrlf 机制，最终形成「除 .ps1/.bat/.cmd 外全部强制 LF」的治理决策。
date: 2026-07-08
meta:
  version: "1.0.0"
  category: research
  trigger: lint_encoding.py .json CRLF 漏检事件
---

# CRLF/LF 换行符治理深度研究

> **研究触发**：2026-07-08，`verified-runtime-index.json` 更新后出现 462 处 CRLF，`run-lint.py` 报告 `❌ CRLF 行尾符` 但汇总结论却显示 `总违规项: 0 处`，暴露 `lint_encoding.py` 对 `.json` 的 CRLF 不标记为 violation 的代码缺陷。
>
> **研究范围**：`.md/.mdc` 为何强制 LF、其他文本文件是否应扩展、`.gitattributes` 作用域、`core.autocrlf` 机制、两个独立 `.git` 仓库的差异化影响。


## 一、问题现象

### 1.1 事件回放

- Agent 用 `edit` 修改 `verified-runtime-index.json` 后，执行 `run-lint.py` 验证
- 输出显示 `❌ CRLF 行尾符 — 462 处`，但汇总报告写 `总违规项: 0 处`
- Agent 误判为「通过」，事后被用户指出才回溯修复
- 根因：`lint_encoding.py` 第 87-90 行仅对 `.md/.mdc` 标记 CRLF 为 violation，`.json` 只统计不报错

### 1.2 更深层次问题

| 问题 | 说明 |
|------|------|
| 检测与修复脱节 | `.json` 的 CRLF 被检测并显示，但不标记为 `fixable`，`--fix` 不触发 |
| 汇总报告失准 | `lint_encoding` 的违规未计入「总违规项」，导致结论误导 |
| 规范边界模糊 | 哪些文件类型应强制 LF，项目无统一真源，全凭代码硬编码 |


## 二、`.md` / `.mdc` 强制 LF 的历史原因

### 2.1 起源：2026-06-05 的 CRLF 污染事件

来源：`references/env-migrations/env-migration-md-format-plugin-and-shell-ban-2026-06-05-141555.md`

- `docs/architecture/engineering-metadata-and-docs-practices.md` 被误操作引入 CRLF，同时混入正文 `---` 分隔线，导致 Markdown 解析异常
- 修复后，在 `.cursor/rules/markdown-docs-format.mdc` 1.4 节固化规则：
  > 本仓库所有 `.md` / `.mdc` 文件必须使用 **LF (`\n`)** 换行符，禁止 `CRLF`

### 2.2 为何 Markdown 特别敏感

| 因素 | 说明 |
|------|------|
| Obsidian 兼容 | 项目要求 `.md` 纳入 Obsidian 知识库，frontmatter 解析在混合换行符时可能异常 |
| YAML frontmatter | `---` 定界符后的换行符若不统一，YAML 解析器可能误判字段边界 |
| Agent 工具链 | `run-lint.py` 的 `md_lint` 依赖逐行正则，`^`/`$` 锚点在 CRLF 下行为不一致 |
| 人读为主 | Markdown 是跨平台文档媒介，需要在 Win/Mac/Linux 间保持一致的渲染结果 |


## 三、各文件类型的换行符规范研究（多方佐证）

### 3.1 `.sh`（Shell 脚本）— 必须 LF

| 来源 | 结论 |
|------|------|
| POSIX 规范 | Shebang 脚本必须在类 Unix 系统上可执行 |
| 实测经验 | CRLF 会导致 `bad interpreter: No such file or directory` |
| Docker | `entrypoint.sh` 有 CRLF 时容器直接启动失败 |

**结论：硬性强制，无任何商量余地。**

### 3.2 `.json` / `.jsonc` — 规范允许 CRLF，但社区最佳实践是 LF

| 来源 | 结论 |
|------|------|
| RFC 8259 Section 2 | `ws = *( %x20 / %x09 / %x0A / %x0D )` — CR 是合法空白 |
| JSON 解析器 | Python `json.load()`、Node.js `JSON.parse()` 均容忍 CRLF |
| 社区实践 | npm、GitHub API、几乎所有开源项目的 `.json` 文件均使用 LF |
| Git 协作隐患 | CRLF 会导致 `git diff` 显示整行变更，影响 `git blame` |

**结论：规范允许，但从工程协作角度，统一 LF 可避免 diff 噪音。**

### 3.3 `.py`（Python）— 解释器容忍，工具链倾向 LF

| 来源 | 结论 |
|------|------|
| Python 官方 | CPython 解析器接受 CRLF，PEP 8 未指定换行符 |
| `py_compile` | 对 CRLF 无报错 |
| Black / Ruff | 默认不检测换行符类型，除非显式配置 |
| 社区实践 | PyPI、Django、Flask 等源码几乎全是 LF |

**结论：解释器不排斥 CRLF，统一 LF 是「协作约定」而非「技术强制」。**

### 3.4 `.js` / `.ts` / `.jsx` / `.tsx` — 工具链强制 LF 趋势明显

| 来源 | 结论 |
|------|------|
| Prettier 官方 | `endOfLine` 默认值从 v1.x 的 `auto` 改为 **v2.0+ 的 `lf`** |
| ESLint | `prettier/prettier` 插件在 Windows + CRLF 环境下高频报错 `Delete CR`（Stack Overflow 浏览量 829k+） |
| Node.js | 运行时容忍 CRLF，但 `npm`/`yarn` 的 shell 脚本在 Linux 上执行时要求 LF |

**结论：现代 JS/TS 工具链已默认强制 LF。不统一会导致持续的工具报错。**

### 3.5 `.ps1`（PowerShell）— Windows 原生，容忍 CRLF

| 来源 | 结论 |
|------|------|
| PowerShell 5.1 / 7+ | 解析器对 CRLF 和 LF 均正常执行 |
| AGENTS.md | 要求 `.ps1` 含中文时必须 UTF-8 with BOM，但未指定换行符 |
| 生态定位 | 唯一「原生就活在 Windows 生态」的脚本类型 |

**结论：强制 LF 的必要性最低。项目最终决策 `.ps1` 不纳入强制范围。**

### 3.6 `.yml` / `.yaml` / `.toml` / `.html` / `.css` — 解析器容忍，最佳实践 LF

| 类型 | 说明 |
|------|------|
| YAML | PyYAML、ruamel.yaml 均容忍 CRLF，但 K8s / Docker Compose 社区全用 LF |
| TOML | `toml` 库容忍 CRLF，但 Rust Cargo、Python Poetry 的配置文件均用 LF |
| HTML/CSS | 浏览器完全容忍 CRLF，但现代构建工具（Vite、PostCSS）通常输出 LF |


## 四、系统默认行为的影响分析

### 4.1 Windows 的 CRLF 默认行为

| 层面 | 行为 | 对项目的影响 |
|------|------|-------------|
| Notepad（旧版） | 不支持 LF，显示为一行 | 人读体验差（但本项目用 VS Code/Cursor，不影响） |
| PowerShell 5.1 | `Out-File`、`>` 重定向默认 UTF-16LE + CRLF | Agent 写 `.ps1` 时需显式控制编码 |
| Git for Windows | 安装时默认建议 `core.autocrlf=true` | 已设置 `core.autocrlf=false` |
| VS Code / Cursor | 默认跟随系统，但可配置 `files.eol` | 可通过 `.vscode/settings.json` 统一 |

### 4.2 Linux/macOS 的 LF 默认行为

| 层面 | 行为 | 对项目的影响 |
|------|------|-------------|
| Shell 工具链 | `cat`、`sed`、`awk`、`grep` 处理 CRLF 时会产生 `\r` 残留 | 脚本处理文件时可能引入隐形 bug |
| Docker | 容器内执行 Windows 风格的脚本（CRLF）会直接失败 | `.sh` 和 `entrypoint` 脚本必须是 LF |
| Python/Node | 运行时本身容忍 CRLF，但社区工具链（Black/Prettier）默认 LF | 不统一会导致 CI/CD lint 失败 |


## 五、`.gitattributes` 的作用域与独立性

### 5.1 核心原则

> `.gitattributes` 只作用于**所在目录及其子目录**，只匹配**该目录所在的 `.git/` 跟踪范围**，对**其他独立的 `.git/` 作用范围无效**。

### 5.2 本项目的分层结构

| 作用域 | `.gitattributes` 位置 | 所属 `.git/` | 相互关系 |
|--------|----------------------|-------------|---------|
| `cs_py` 主仓库 | 根级 `.gitattributes` | `cs_py/.git/` | 独立，只服务本地 |
| `jywl-lab` polyrepo | `jywl-lab/.gitattributes` | `jywl-lab/.git/` | 独立，不继承父级 |
| 其他 polyrepo | 暂无（按需自行添加） | 各自 `.git/` | 完全独立 |

### 5.3 与 `.gitignore` 的关系

`.gitattributes` 是「普通文件」，受 `.gitignore` 规则约束：

- **被跟踪时**：随仓库分发，所有开发者共享换行符规则
- **不被跟踪时**：本地 Git 仍会读取，但 clone 后其他开发者**没有这个文件**，规则失效

本项目决策：**`.gitattributes` 不跟踪**，仅供本地开发使用，不干涉 remote team。

### 5.4 `.gitattributes` 内容设计

```
* text eol=lf
*.ps1 -text
*.bat -text
*.cmd -text
```

- `* text eol=lf`：所有文本文件 checkout 时保持 LF
- `*.ps1 -text`：PowerShell 脚本不参与换行符转换（保持系统默认）
- `*.bat -text` / `*.cmd -text`：批处理文件不参与转换


## 六、`core.autocrlf` 机制与两个独立 `.git` 的差异化状态

### 6.1 `core.autocrlf` 的三档行为

| 值 | check-in（add/commit） | check-out（checkout/clone/pull） |
|----|------------------------|---------------------------------|
| `true` | CRLF → LF | LF → CRLF |
| `input` | CRLF → LF | 不转换 |
| `false` | **不转换** | **不转换** |

### 6.2 为什么设置 `core.autocrlf = false`

来源：`env-migration-gh-cli-pr-merge-automation-2026-06-30-173228.md`

- 本项目的换行符治理策略是「编辑器/工具生成什么就是什么，不经过 Git 二次转换」
- 换行符合规由 `lint_encoding.py` + `--fix` 在**落盘时**保证
- Git 的自动转换是**隐式的、不可见的**，容易引发工作树与仓库 diff 不一致的困惑
- 关闭后，换行符的**真源就是磁盘上的实际字节**，所见即所得

### 6.3 两个仓库的差异化状态

| 仓库 | `core.autocrlf` | `.gitattributes` | 实际 checkout 行为 |
|------|-----------------|-----------------|-------------------|
| `cs_py` | `false`（仓库级 `.git/config`） | 有（根级） | **LF**（不转换 + `.gitattributes` 兜底） |
| `jywl-lab` | `true`（全局 `gitconfig`） | 有（内部） | **LF**（`.gitattributes` 优先级覆盖 `autocrlf`） |

### 6.4 `jywl-lab` 的潜在冲突

`.gitattributes` 优先级高于 `core.autocrlf`，所以 `jywl-lab` 当前 checkout 为 LF。但若 `.gitattributes` 不被跟踪，clone 后丢失，则 `core.autocrlf=true` 生效，工作树变为 CRLF。

**建议**（可选）：在 `jywl-lab` 内部也设置 `core.autocrlf = false`，消除对优先级的依赖。


## 七、最终决策与执行

### 7.1 决策结论

| 扩展名 | 强制 LF？ | 理由 |
|--------|----------|------|
| `.md` / `.mdc` | ✅ | 历史规则，Obsidian + frontmatter 兼容 |
| `.json` / `.jsonc` | ✅ | 避免 diff 噪音，统一协作 |
| `.py` | ✅ | 与 Black 等工具链默认对齐 |
| `.js` / `.ts` / `.jsx` / `.tsx` | ✅ | Prettier/ESLint 默认 LF |
| `.html` / `.css` | ✅ | 构建工具链默认 LF |
| `.sh` | ✅ | POSIX / Docker 硬性要求 |
| `.yml` / `.yaml` / `.toml` | ✅ | K8s/Docker/Poetry 社区实践 |
| `.txt` / `.ini` / `.cfg` / `.log` | ✅ | 通用文本文件统一 |
| `.ps1` | ❌ | Windows 原生生态，完全兼容 CRLF |
| `.bat` / `.cmd` | ❌ | GBK 批处理文件，不做换行符干预 |

### 7.2 执行清单

| 文件 | 操作 |
|------|------|
| `cs_py/.gitattributes` | 新建，`* text eol=lf`，`.ps1/.bat/.cmd` 豁免 |
| `jywl-lab/.gitattributes` | 新建，同上（独立仓库，不继承） |
| `lint_encoding.py` | 修改 CRLF 检测逻辑：`CRLF_EXEMPT_EXTENSIONS = {".ps1", ".bat", ".cmd"}` |
| `verified-runtime-index.json` | CRLF → LF（已由工具 `--fix` 修复） |


## 八、关联文档

| 文档 | 关系 |
|------|------|
| `.cursor/rules/markdown-docs-format.mdc` | `.md/.mdc` 强制 LF 的原始规则来源 |
| `references/env-migrations/env-migration-md-format-plugin-and-shell-ban-2026-06-05-141555.md` | CRLF 污染事件的起源记录 |
| `references/env-migrations/env-migration-gh-cli-pr-merge-automation-2026-06-30-173228.md` | `core.autocrlf = false` 的决策记录 |
| `references/env-migrations/env-migration-run-lint-routing-fix-and-archive-timeout-analysis-2026-06-23-180826.md` | `lint_encoding.py` 路由修复历史 |
| `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` | 被修改的检测引擎 |


*文档生成时间：2026-07-08*  
*证据来源：RFC 8259、Prettier 官方文档、Git 官方文档、Stack Overflow、项目 env-migration 历史记录、AGENTS.md、markdown-docs-format.mdc*