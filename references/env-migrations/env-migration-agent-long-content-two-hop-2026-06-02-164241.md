---
title: env-migration — Agent 长内容分步写入与 Shell 执行边界
description: 记录本次 session 对 long content 完整解法（依据、分步写文件、python -c 禁令、UTF-8 BOM、中文术语对照表）在 AGENTS.md 与 schema 等的落地，供新环境 Agent 复现操作约束。
date: 2026-06-02
---

# env-migration-agent-long-content-two-hop-2026-06-02-164241

> **Session 主题**：厘清 Agent 写入长内容/多行脚本时的完整数据流，固定为 **先用 Write 把正文落到 `content.txt`，再用 `file-write-helper` 生成成品，最后用短命令运行 `.ps1`/`.py`**；禁止 Shell 内嵌正文与一切 `python -c`。  
> **适用场景**：新环境拉取仓库后，OpenCode/Cursor Agent 须遵守同一套文件 I/O 与 Shell 边界，避免再出现 `Set-Content` / `python -c` / heredoc 写盘翻车。


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Agent 长内容分步写入 + Shell 执行边界 |
| **日期** | 2026-06-02 |
| **文件名时间戳** | `2026-06-02-164241` |
| **触发原因** | Agent 用 Shell 拼接 PowerShell/`python -c` 写长脚本导致截断、转义、编码错误；`AGENTS.md` 曾误写「禁止 Write 写多行」，与 `file-write-helper` 的 txt+ini 方案矛盾 |
| **影响范围** | `venv/.opencode/AGENTS.md`（主约束）；`schema/structure/`（env-migration 模板 v2、命名规范、**中英文术语对照表**）；`references/env-migrations/README.md`、`references/README.md`；本文档后续修订（用语「分步写文件」「试跑」等） |
| **风险等级** | 低（文档与 Agent 操作规范，不改业务运行时） |


## 〇、解法总览（依据 + 步骤）

### 0.1 问题本质

长内容失败通常不是「模型不懂改什么」，而是 **把磁盘文件内容当成了 Shell 命令行参数**（模型 → Shell 工具 → 终端再解析一层）。

| 层级 | 失败模式 |
|------|----------|
| Shell 传参 | 命令行长度上限；`$` `"` `` ` `` `\|` `&` 多层转义 |
| 错误路径 | `powershell -Command "…"`、`python -c "…"`、heredoc、`Set-Content` 一行写盘 |
| 无效补救 | Shell 写坏 `content.txt` → `file-write-helper` 再读 → 仍然坏 |

### 0.2 业界依据（摘要）

- **读写分离**：Shell 适合 `ls`/`grep`/短命令；改文件宜用专用 Write/patch 工具（OpenAI `apply_patch`、Claude Write/Edit、Aider SEARCH/REPLACE）。
- **Windows**：PowerShell `-File` 按字面量读脚本；`-Command` 会再解析（见 PowerShell #4024）。Agent 在 PS 下用 bash heredoc 常失败（如 Warp #7735）。
- **本项目工具链**：`schema/tool/file-write-helper.py` + ini 负责 **BOM、回读、语法检查**；不负责「生成」正文。

### 0.3 标准流程（三步）

```text
第一步：把正文写到磁盘（不经 Shell 转义）
  用 write / StrReplace → content.txt（及短的 job.ini）
  禁止：用 Shell 写 content.txt

第二步：由 helper 生成成品（Shell 只跑一条短命令）
  复制 file-write-helper.ini 到 venv/tmp/，填 target_path、content_file、encoding
  python.exe …\file-write-helper.py --config …\job.ini
  → 得到 .ps1（utf-8-sig）/ .py / .ts 等

第三步（可选）：运行成品
  powershell.exe -File …\output.ps1
  或 python.exe …\output.py
  禁止：powershell -Command / python -c 内嵌正文或逻辑
```

### 0.4 长字符串「在哪」

| 阶段 | 载体 | 转义谁负责 |
|------|------|------------|
| 生成 | 模型输出 | — |
| 落盘 | Write 的 `content` → IDE 写文件 | **IDE/协议**，不经过 PowerShell |
| helper | `open(content_file).read()` | 普通文件读取，无 Shell |
| 运行 | `-File` / `python.exe script.py` | 命令行只有路径等短参数 |

**结论**：不要用 PowerShell 把长正文塞进命令行去写 txt；应 **用 Write 工具写 `content.txt`**。

### 0.5 与「.ps1 必须 UTF-8 BOM」的关系（无冲突）

| 规则 | 管什么 |
|------|--------|
| UTF-8 BOM | **磁盘上** `.ps1` 文件编码（PS 5.1 解析中文） |
| Shell 边界 | **命令行里**不得带脚本全文或 `python -c` |

达标方式（任选）：

1. **推荐**：helper + `encoding=utf-8-sig` 一次写出。  
2. `write` 出 `.ps1` 后，**仅含路径**的 PS 一行 `WriteAllText`（正文不进命令行）。  
3. 单独写 `add-bom.ps1` / `add-bom.py`，再 `-File` / `python.exe …\add-bom.py`。

**禁止**：任何 `python -c "…"`（含一行 BOM、改大段 py）。

### 0.6 `python -c` 全面禁止

- 需要 Python → **先 write 出 `.py`**，再 `python.exe path\to\script.py`。  
- 不值得写 `.py` → **不要用 Shell 跑 Python**。  
- **允许**：`python.exe -m py_compile file.py`（`-m` 模块方式，**不是** `-c`）。


## 一、文本文件变更清单

### 1. 修改 `venv/.opencode/AGENTS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | 重写章节 + 局部修正 |
| **修改点** | ① 章节「长字符串 / Shell 执行边界（**分步写文件**）」：Write 可写多行；禁止 Shell 承载正文；禁止一切 `python -c`；允许 `powershell -File`、`python.exe *.py`、helper `--config`  <br>② 「文件编码：所有 .ps1 必须是 UTF-8 + BOM」：原则不变，与 Shell 边界无冲突  <br>③ 「Agent write 工具的行为」注释与上对齐 |
| **作用** | OpenCode Agent 在本仓库的统一操作约束 |
| **验证方式** | 检索 `python -c` 仅出现在禁止说明中；存在「分步写文件」与 `content.txt` |
| **迁移方式** | 从 git 拉取对应提交或按本节 0.3 手工合并 |

### 2. 修改 `schema/structure/env-migration-template.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/env-migration-template.md` |
| **变更类型** | 命名规范升级 |
| **修改点** | 文件名由 `YYYY-MM-DD` 改为 **`YYYY-MM-DD-HHmmss`**；模板 v2 |
| **作用** | 同日多场 env-migration 不撞名 |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `schema/structure/doc-naming-conventions.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/doc-naming-conventions.md` |
| **变更类型** | 命名示例更新 |
| **修改点** | 所有 `env-migration-*-YYYY-MM-DD.md` → `*-YYYY-MM-DD-HHmmss.md` |
| **迁移方式** | 直接覆盖 |

### 4. 修改 `references/env-migrations/README.md`、`references/README.md`

| 属性 | 值 |
|------|-----|
| **变更类型** | 导航与格式说明 |
| **修改点** | 登记新时间戳格式；链到 env-migration 模板 |
| **迁移方式** | 直接覆盖 |

### 5. 新建本文档

| 属性 | 值 |
|------|-----|
| **路径** | `references/env-migrations/env-migration-agent-long-content-two-hop-2026-06-02-164241.md` |
| **变更类型** | 新建（同 session 内续修订：用语通俗化、登记术语表） |
| **作用** | 本次 session 的完整依据与复现清单（即本文件） |

### 6. 新建 `schema/structure/doc-terminology-zh-en.md`（同 session 续增）

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/doc-terminology-zh-en.md` |
| **变更类型** | 新建 |
| **修改点** | 中英文术语对照总表（如 two-hop→**分步写文件**、smoke→**快速试跑**、dry-run→**只检查不写盘**）；固定三步流程用语；与 AGENTS 对齐的交叉引用 |
| **作用** | 中文落盘文档的统一表述参照，避免「两跳」「冒烟」等别扭直译 |
| **验证方式** | 文件存在；`doc-naming-conventions.md` 文首链到本表 |
| **迁移方式** | 从 git 拉取即可 |

### 7. 修改 `schema/structure/README.md`、`schema/README.md`（术语表导航）

| 属性 | 值 |
|------|-----|
| **变更类型** | 导航登记 |
| **修改点** | 增加 `doc-terminology-zh-en.md` 条目 |
| **迁移方式** | 直接覆盖 |

### 8. 续修订：用语通俗化（同 session，非新规则）

| 路径 | 变更 |
|------|------|
| `venv/.opencode/AGENTS.md` | 「两跳」→「分步写文件」；补充第一步/第二步/第三步标题 |
| 本文档 | 「冒烟」→「试跑示例」；`smoke_*` 文件名→`trial_*`（仅示例） |

> **说明**：§6–§8 不改变 §0 的技术规则，只统一**中文怎么写**。新环境拉 git 后应同时拿到术语表与修订后 AGENTS/本文档。

### 9. 未改但相关的稳定模板（复现时须存在）

| 路径 | 用途 |
|------|------|
| `schema/tool/file-write-helper.py` | 第二步：读 ini+txt，写成品，回读+语法检查 |
| `schema/tool/file-write-helper.ini` | 模板：复制到 `venv/tmp/` 再填路径 |
| `schema/encoding/script-encoding-conventions.md` | `.ps1` BOM、复杂文本优先 Python |


## 二、非文本操作（文件系统/缓存迁移）

本次 session **无** 缓存迁移、目录批量复制或环境变量注入变更。

| 操作类型 | 说明 |
|---------|------|
| — | 仅文档与 Agent 规范更新 |


## 三、环境变量速查

本次 **未修改** `.vscode/settings.json` 或终端注入项。long content 解法不依赖新环境变量。


## 四、验证清单（新环境 Agent 自检）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | AGENTS 含分步写文件说明 | 在 `venv/.opencode/AGENTS.md` 搜索 `分步写文件` | 有匹配 |
| 2 | 禁止 python -c | 搜索 `python -c` 与「禁止」同段出现 | 有硬性禁止表述 |
| 3 | 允许 Write 写 content | 搜索 `禁止用 Shell 生成或写入 content.txt` 且**无**「禁止 write 写多行」 | 旧歧义已删除 |
| 4 | helper 存在 | `Test-Path schema\tool\file-write-helper.py` | True |
| 5 | 完整流程试跑（可选） | 见下「五、试跑示例」 | helper 返回 `success: true`，`.ps1` 带 BOM |
| 6 | 术语对照表存在 | `Test-Path schema\structure\doc-terminology-zh-en.md` | True；文内含「分步写文件」「快速试跑」 |
| 7 | 命名规范链到术语表 | 打开 `schema/structure/doc-naming-conventions.md` 文首 | 有 `doc-terminology-zh-en.md` 链接 |


## 五、试跑示例（可选：从头走一遍流程）

在 `<devroot>` 下按顺序做（路径换成你的 devroot）。目的是**确认规范在真机上能跑通**，不是正式业务脚本。

**1. 用 Write 工具（Agent）或手工创建** `venv/tmp/trial_content.txt`：

```powershell
Write-Host "Hello 世界"
```

**2. 创建** `venv/tmp/trial_job.ini`（从 `schema/tool/file-write-helper.ini` 复制后改）：

```ini
[write]
target_path   = <devroot>\venv\tmp\trial_output.ps1
content_file  = <devroot>\venv\tmp\trial_content.txt
encoding      = utf-8-sig
verify_syntax = true
backup_existing = false
```

**3. 第二步：只跑 helper（命令行里不要带脚本正文）**：

```text
<devroot>\venv\py\python.exe <devroot>\schema\tool\file-write-helper.py --config <devroot>\venv\tmp\trial_job.ini
```

**4. 检查 BOM 是否带上**：

```powershell
$bytes = [System.IO.File]::ReadAllBytes("<devroot>\venv\tmp\trial_output.ps1")
$bytes[0..2] -join ','  # 期望 239,187,191（即 EF BB BF）
```

**5. 第三步（可选）：运行生成的 ps1**：

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<devroot>\venv\tmp\trial_output.ps1"
```

试跑完成后可删除 `venv/tmp/trial_*` 文件。

> **说明**：`file-write-helper` 若支持 dry-run（只检查、不写盘），以脚本内文档为准；本仓库当前以「执行后回读比对」为主，无单独 dry-run 开关时按上表完整执行即可。


## 六、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 恢复 AGENTS 旧版 | 从 git 回退 `venv/.opencode/AGENTS.md` 至本 migration 之前 |
| 恢复命名模板 | 回退 `schema/structure/env-migration-template.md`、`doc-naming-conventions.md` |
| 删除本文档 | 若整次规范被否决，删除本文件并更新 `references/env-migrations/README.md` 导航 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-02-164241 |
| **更新人** | Human + Agent Session（long content 讨论与 AGENTS 修订） |
| **变更触发** | 明确 long content 从模型到磁盘的完整链路，消除 Write 禁止歧义，禁止 `python -c`；补充中文术语对照 |
| **下次修订条件** | Cursor/Cloud Agent Write 故障有官方修复策略变更；或 `file-write-helper` 接口变更；新增 Agent 常用英文词时更新术语表 |
| **跨环境迁移参考** | 拉 git + 读本节 0.3 + 第四节验证清单；OpenCode 以 `venv/.opencode/AGENTS.md` 为准；写中文 doc 前查术语表 |
| **中文术语** | [`schema/structure/doc-terminology-zh-en.md`](../../schema/structure/doc-terminology-zh-en.md)（§一 变更清单 §6） |


## 八、相关外部参考（阅读用）

| 来源 | 要点 |
|------|------|
| [Why File Editing Is the Hardest Part of Building a Coding Agent](https://dev.to/youssefmejdi/why-file-editing-is-the-hardest-part-of-building-a-coding-agent-24k8) | 传输格式常是失败点；由运行时做校验与守卫 |
| [OpenAI apply_patch](https://developers.openai.com/api/docs/guides/tools-apply-patch/) | 结构化 diff，不宜用 shell heredoc 改文件 |
| [PowerShell #4024](https://github.com/PowerShell/PowerShell/issues/4024) | `-File` 字面量 vs `-Command` 再解析 |
| [Warp #7735](https://github.com/warpdotdev/Warp/issues/7735) | Agent heredoc 易失败 |


*文档生成时间：2026-06-02*  
*对应文件名时间戳：2026-06-02-164241*
