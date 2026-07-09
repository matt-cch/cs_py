---
title: deploy-git-isolated — 文件格式规范
description: SOP.md / EXEC-CHEATSHEET.md / TASK-TOOLS-INDEX.md / ENTRY.json / DESIGN.md 的格式模板、强制规则与互斥边界。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 文件格式规范

## 3.1 SOP.md（标准操作流程）

> **核心原则**：每个 Step 定义 **Input → Process → Output → Validation** 四元契约，支持 Ralph Loop 自闭环追踪审计。

### 格式模板

```markdown
### Step N: 步骤名称

| 契约项 | 定义 |
|--------|------|
| **Input** | 预期输入条件（环境变量、前置步骤、文件状态） |
| **Process** | 执行过程描述（调用哪个脚本、关键操作） |
| **Output** | 预期输出（文件、日志、返回值） |
| **Validation** | 验收条件（通过标准、失败标准） |
| **Audit Trail** | 执行记录（状态、日志路径、产物清单） |
| **Rollback** | 回滚路径（失败时如何恢复） |
```

### 强制规则

1. **输入可预期**：不满足 Input 条件不得执行
2. **输出可验证**：必须通过 Validation 后才可进入下一步
3. **过程可追踪**：执行后必须留下 Audit Trail（状态、日志、产物）
4. **失败可回滚**：每个 Step 必须定义 Rollback 路径
5. **禁止混杂命令细节**：SOP 只管「流程是什么、怎么验收」，不管「命令怎么敲」。命令细节见 `EXEC-CHEATSHEET.md`。
6. **禁止混杂工具索引**：SOP 只管「标准流程」，不管「有什么工具、边界在哪」。工具索引见 `TASK-TOOLS-INDEX.md`。


## 3.2 EXEC-CHEATSHEET.md（执行速查表）

> **核心原则**：涵盖命令、配置、参数等所有可执行/可操作内容，不限定于命令行格式。Agent/人类/终端共享同一真源。

### 格式模板

```markdown
## Stage SX: 阶段名称（Step N-M）

### Step N: 步骤名称

**Agent:**
```powershell
& "${devroot}\...\script.ps1" <args>
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\...\script.ps1 <args>
```

> 前置：`.env` 中已配置 `XXX`
```

### 强制规则

1. **真源唯一**：速查表中所有命令指向 `scripts/` 下的同一 `.ps1` 文件，Agent/人类/终端共享。
2. **上下对照**：每个功能区块内先写 Agent 格式，紧接写终端格式，用 `---` 分隔不同功能。
3. **变量约定**：Agent 格式使用 `${devroot}` 等变量；终端格式使用相对路径 `.\references\...`。
4. **执行策略**：Agent 使用 `&` 调用操作符；终端用 `Set-ExecutionPolicy -Scope Process ...;` 前缀。
5. **禁止表格罗列命令**：速查表的主体是**对照代码块**，不是表格。
6. **禁止混杂流程说明**：EXEC-CHEATSHEET 只管「命令怎么执行」，不管「流程是什么、怎么验收」。流程说明见 `SOP.md`。
7. **禁止混杂工具索引**：EXEC-CHEATSHEET 只管「命令怎么执行」，不管「有什么工具、边界在哪」。工具索引见 `TASK-TOOLS-INDEX.md`。


## 3.3 TASK-TOOLS-INDEX.md（工具索引表）

> **核心原则**：回答「这个 task 有什么工具？在哪里？什么时候用？边界是什么？」。
> **与 EXEC-CHEATSHEET 的本质区别**：EXEC-CHEATSHEET 面向「执行者」（知道要做什么，想知道怎么敲命令）；TOOLS-INDEX 面向「规划者」（想知道有哪些能力、该调哪个工具、是否已有现成轮子、能否用外部通用工具替代）。

### 必须包含的章节

1. **本地专属脚本清单**：按职责分类（部署流水线 / 安全检查 / 通用包装器 / 共享库），每项含 `脚本名 | 职责 | 典型场景 | 状态`
2. **外部通用工具引用**：明确列出本 task 可能用到的 `runtime/`、`schema/tool/` 下的通用工具，每项含 `工具名 | 全局路径 | 登记索引 | 本 task 中的用途 | 边界说明`
3. **边界矩阵**：8+ 个典型场景的首选工具、次选/备选、禁止行为
4. **速查命令**：本地脚本 + 外部通用工具的典型调用命令

### 强制规则

1. **禁止重复造轮子**：外部已存在且已登记的工具（如 `lint-json.py`、`lint-ps1.ps1`、`check-file-encoding.ps1`），必须在「外部通用工具引用」中列出，并在「边界矩阵」中规定「禁止自行实现同类功能」。
2. **铁律声明**：外部工具引用节必须包含一句铁律——「以上工具已存在且已登记，本 task 禁止自行实现同类功能。新增需求时先查 `verified-task-index.json` → `available_scripts_and_tools`。」
3. **关联文件导航**：底部必须列出与本 task 相关的全部文档的「文件 | 用途」对照表。


## 3.4 SOP vs EXEC-CHEATSHEET vs TASK-TOOLS-INDEX 对比总结

| 对比维度 | SOP.md | EXEC-CHEATSHEET.md | TASK-TOOLS-INDEX.md |
|---------|--------|-------------------|---------------------|
| **核心问题** | 「流程是什么、怎么验收？」 | 「命令怎么执行、参数怎么填？」 | 「有什么工具、边界在哪？」 |
| **内容形式** | Step 契约表格（Input/Process/Output/Validation） | Agent/终端双格式代码块 | 表格清单 + 边界矩阵 + 引用链路 |
| **是否含外部工具** | ❌ 否 | ❌ 否（只含本 task 脚本调用） | ✅ **是**（必须引用 runtime/ 和 schema/tool/ 通用工具） |
| **读者角色** | 流程设计者（确认边界与验收） | 执行者（复制粘贴命令） | 规划者（选择工具、判断边界） |
| **更新时机** | 新增/修改 Step、变更验收条件时 | 新增/修改脚本命令时 | 新增/删除工具、发现外部通用工具可替代时 |
| **典型错误** | 把命令细节塞进来 | 把流程说明塞进来 | 把命令执行细节塞进来 |

> **一句话区分**：SOP 是「流程契约」，EXEC-CHEATSHEET 是「执行手册」，TOOLS-INDEX 是「能力地图」。


## 3.5 ENTRY.json

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `meta.description` | string | task 一句话描述 |
| `meta.last_updated` | string | 最后更新日期 `YYYY-MM-DD` |
| `meta.source_of_truth` | string | 人类权威文档路径（通常是 `DESIGN.md`） |
| `meta.trigger_index` | string | 触发条件真源路径（`task-scenario-triggers.json`） |
| `meta.tools_index` | string | 工具索引路径（`TASK-TOOLS-INDEX.md`） |
| `current_workflow.entry_script` | string | 统一入口脚本名 |
| `current_workflow.usage` | string | 典型调用示例 |
| `active_scripts` | array | 活跃脚本清单，每项含 `name`、`role`、`path`、`status` |
| `active_scripts[].status` | string | `pending` / `ready` / `deprecated` |
| `design_doc` | string | DESIGN.md 路径 |
| `sop` | string | **SOP.md 路径**（标准流程） |
| `cheatsheet` | string | **EXEC-CHEATSHEET.md 路径**（执行速查） |
| `changelog_dir` | string | changelog 目录路径 |
| `gotchas_dir` | string | gotchas 目录路径 |

### `sop`、`cheatsheet` 与 `tools_index` 字段语义

- `sop`：指向**标准操作流程**（SOP.md），回答「流程是什么、怎么验收」。
- `cheatsheet`：指向**执行速查表**（EXEC-CHEATSHEET.md），回答「命令怎么执行」。
- `tools_index`：指向**工具索引表**（TASK-TOOLS-INDEX.md），回答「有什么工具、边界在哪」。
- 三者互补，不可互相替代。`ENTRY.json` 必须同时登记三者。


## 3.6 DESIGN.md

- 必须包含「背景」「设计决策」「目标目录结构」「SOP」「踩坑记录」章节。
- 设计决策必须记录「问题 → 方案 → 效果」三步。
- SOP 章节必须与 `SOP.md` 内容一致，但可更详细（含解释性文字）。
- **新增**：Trigger 治理设计意图（第 6 节），记录 trigger 体系的六维元原则（治理、参照、边界、协调、审计、重建）。


## 3.7 文件编码与换行符规范

> **来源**：用户与 Agent 在 2026-07-08 对话中共同确认。本节记录跨平台（Win/Linux）与 GitHub Remote 之间保持预期一致性的编码与换行符治理共识。

### 3.7.1 核心共识：本地预期一致性优先

**问题**：Windows 默认使用 CRLF (`\r\n`)，Linux/macOS 默认使用 LF (`\n`)。若依赖开发者各自的全局 `core.autocrlf` 配置，同一文件在不同平台 checkout 后的字节流不一致，导致 lint 检测、哈希校验、diff 比对全部失效。

**解法**：**本地 `.gitattributes` 显式声明**，使仓库在任何平台 checkout 时都产生相同的换行符预期。不依赖全局 Git 配置，不假设操作系统的默认行为。

### 3.7.2 换行符分层策略

| 文件类型 | 换行符 | 原因 |
|----------|--------|------|
| `.ps1` / `.bat` / `.cmd` | **CRLF**（豁免强制 LF） | Windows 原生脚本生态完全兼容 CRLF；强制 LF 可能破坏与系统工具（如批处理解析器）的互操作 |
| `.py` / `.js` / `.ts` / `.json` / `.md` / `.mdc` / `.yml` / `.yaml` / `.toml` / `.sh` / `.html` / `.css` | **强制 LF** | 跨平台一致性、JSON 规范（RFC 8259 禁止 BOM，默认 LF）、前端工具链默认 LF、POSIX shell 默认 LF |
| 二进制文件（`.exe` / `.zip` / `.png` / `.pptx` 等） | **不参与转换** | `binary` 声明，Git 不做换行符处理 |

**`.gitattributes` 最小配置模板**：

```gitattributes
# 所有文本文件默认 LF
* text eol=lf

# Windows 原生脚本豁免
*.ps1 -text
*.bat -text
*.cmd -text

# 二进制文件明确声明
*.exe binary
*.zip binary
*.png binary
*.pptx binary
```

### 3.7.3 lint 检测与自动修复

**检测范围**：`lint_encoding.py` 的 CRLF 强制检测范围为「除 `.ps1`/`.bat`/`.cmd` 外全部文本文件」。

**修复路径**：
```powershell
# 单文件修复
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "path/to/file.json" --fix

# 全量扫描
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --profile lint-encoding --fix
```

### 3.7.4 Python `write_text` / `open` 的换行符陷阱（Windows）

> **来源**：2026-07-09 实测踩坑。`run-lint.py --fix` 在多插件串行修复时，CRLF 数量反而增加。

#### 现象

`lint_encoding` 插件先把 `.md` 文件的 CRLF 修复为 LF，`md_lint` 插件随后修改 frontmatter 并写回，Phase 3 重新检测时发现 CRLF 从 9 处增加到 10 处。

#### 根因

Python 的 `pathlib.Path.write_text()` 和内置 `open()` 在 Windows 上有一个隐蔽的默认行为：

- **`newline=None`（默认）**：写入时自动把字符串中的每个 `\n` 转换为操作系统默认换行符，Windows 下即 `\r\n`
- **这意味着**：即使传入的字符串里只有 `\n`，落盘后也会变成 `\r\n`

在多插件串行修复的架构中：
1. `lint_encoding` 用 `write_bytes()` 把文件修成纯 LF
2. `md_lint` 读取文件 → 修改内容 → `write_text(content, encoding="utf-8")` 写回
3. `write_text` 默认 `newline=None`，在 Windows 上把 LF 全部转回 CRLF
4. 前序插件的修复成果被**静默覆盖**

#### 硬性规定

任何 Python 代码写入**强制 LF 的文件**（`.md` / `.py` / `.js` / `.json` / `.yml` / `.yaml` / `.toml` / `.sh` / `.html` / `.css`）时，**必须**显式指定 `newline="\n"`：

```python
# ✅ 正确：强制 LF 输出，不受操作系统影响
path.write_text(content, encoding="utf-8", newline="\n")

with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

# ❌ 错误：Windows 下会产生 CRLF
path.write_text(content, encoding="utf-8")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
```

#### 排查要点

- 不要假设 `write_text` 会按字面量写入——它在 Windows 上有平台相关的转换层
- 多插件/多阶段修复时，每个写回文件的插件都必须独立遵守此规定
- `lint_encoding` 使用 `write_bytes()` 不受此影响（字节直接落盘），但其他插件若改用 `write_text` 必须加 `newline="\n"`

### 3.7.5 `.gitattributes` 的跟踪策略

**不跟踪原则**：`.gitattributes` 文件**不纳入 Git 版本跟踪**（被 `.gitignore` 的 `/*` 排除），仅供**本地开发**使用。

**原因**（在隔离 Git 优先模式下）：
1. 隔离 Git 的配置（`.gitconfig`、`.gitattributes`、`.gitignore`）是**本地环境约定**，与业务代码解耦
2. 不同 polyrepo 可能使用不同的技术栈（如某仓库纯前端无 `.ps1`），需要差异化的 `.gitattributes`
3. 隔离 Git 的 `.gitconfig` 已提供基础默认行为，`.gitattributes` 是对该仓库的局部覆盖，不应强制同步到 remote
4. 保持灵活性：每个开发环境/CI 实例可独立调整，不阻塞其他环境

**例外**：若某 polyrepo 明确要求全团队统一换行符行为，可在该仓库内跟踪 `.gitattributes`，但须显式声明为团队级决策。

**与隔离 Git 的关系**：
- `.gitattributes` 是**仓库级**配置（落在 `.git/` 同级目录）
- 隔离 Git 的 `.gitconfig` 是**工具级**配置（落在 `venv/data-git/`）
- 两者共同决定换行符行为：`.gitattributes` 优先级 > `.gitconfig` > Git 默认值
- 即使 `.gitattributes` 不跟踪，隔离 Git 的 `.gitconfig` 仍可全局设置 `core.autocrlf=false` 作为安全兜底


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
