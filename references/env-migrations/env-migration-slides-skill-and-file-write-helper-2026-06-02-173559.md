---
title: env-migration — Slides Skill 评估 + file-write-helper 工作流集中化
description: 记录本次 session 对 Slides Skill（PptxGenJS）与 ppt-master 的评估对比、module.paths.unshift 依赖注入发现、以及 file-write-helper 工作流文档集中化与 AGENTS.md 触发链路建立
date: 2026-06-02
---

# env-migration-slides-skill-and-file-write-helper-2026-06-02-173559

> **Session 主题**：评估 OpenCode Slides Skill（PptxGenJS）与 ppt-master（SVG→DrawingML）两条 PPT 生成路径的对比，完成评估报告与回顾文档；将 file-write-helper 工作流知识从 JS/TS 专属文档迁入 schema/tool/ 权威文档，并在 AGENTS.md 建立触发链路。  
> **适用场景**：新环境 Agent 需了解 PPT 生成能力选型、隔离 Node.js 依赖注入标准做法、以及长文本文件写入的标准操作流程。


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Slides Skill 评估 + file-write-helper 工作流集中化 |
| **日期** | 2026-06-02 |
| **文件名时间戳** | `2026-06-02-173559` |
| **触发原因** | 需要验证 PptxGenJS vs ppt-master 两条 PPT 生成路径的优劣势；Agent 长文本写入流程散落在 JS/TS 文档中，需集中化并建立触发索引 |
| **影响范围** | `debug/slides-eval/`（评估产物）、`docs/tooling/opencode/`（回顾文档）、`schema/encoding/js-ts-scripting-best-practices.md`（精简）、`schema/tool/file-write-helper-workflow.md`（新建）、`schema/tool/README.md`（导航）、`venv/.opencode/AGENTS.md`（触发框） |
| **风险等级** | 低（评估产物和文档，不改业务运行时） |


## 〇、Session 总览

### 0.1 第一段：Slides Skill 评估（10:59–12:54）

**目标**：评估 OpenCode Slides Skill（PptxGenJS）生成可编辑 PPTX 的能力，并与 ppt-master（SVG → Native DrawingML）对比。

**执行过程**：

1. 阅读 Slides Skill `SKILL.md` 及其 `assets/pptxgenjs_helpers/`，确认 PptxGenJS 是 JS 库，python-pptx 仅用于验证
2. 编写 3 页季度回顾需求文档 `debug/slides-eval/requirements.md`
3. 生成两套 PPTX：
   - **Slides Skill**：JS 脚本 → PptxGenJS → `slides-skill-output.pptx`（3 页，可编辑文本）
   - **ppt-master**：3 页 SVG → Native DrawingML → `.pptx`（2 个备份：纯原生 + SVG 内嵌）
4. 用 `python-pptx` 验证两套 PPTX：每页文本字段均可编辑
5. 撰写对比评估报告 `debug/slides-eval/evaluation_report.md`
6. 撰写回顾文档 `docs/tooling/opencode/slides-skill-usage-retrospective.md`

**关键发现：`module.paths.unshift()`**

在执行 Slides Skill 的 `build.js` 时，发现 PptxGenJS 在隔离的 `venv/pptxgenjs/node_modules/` 下，Agent 无法直接用 `require('pptxgenjs')` 找到。

解决方案：`module.paths.unshift('D:/.../venv/pptxgenjs/node_modules')`，其优势：
- **文件级作用域**：只影响当前 JS 文件
- **零环境污染**：不修改 `process.env`
- **子依赖自动解析**：如 `pptxgenjs` 内部的 `jszip` 自动向上查找
- **支持多路径**：可 `unshift` 多个 `node_modules` 目录

禁止替代方案：
- `$env:NODE_PATH`：进程级副作用，影响当前 Shell 所有 Node 子进程
- `require('绝对路径')`：子依赖需逐层手动注入，断裂风险高

### 0.2 第二段：文件写入工作流集中化（16:40–17:29）

**目标**：将散落在 `js-ts-scripting-best-practices.md` 中的 file-write-helper 通用工作流迁入 `schema/tool/` 权威文档，在 AGENTS.md 建立触发链路，使 Agent 能在 session 初始化时直接索引到正确操作流程。

**执行过程**：

1. 新建 `schema/tool/file-write-helper-workflow.md` — 跨语言权威工作流文档
   - 铁律：禁止 Shell 命令行拼接正文
   - 5 种禁止写法清单（-Command、python -c、heredoc、echo>、Set-Content -Value）
   - 允许的唯一路径（write → content.txt → ini → helper）
   - 编码选择表（引用 script-encoding-conventions.md）
   - 前置约束（引用 AGENTS.md 四节）
   - 6 项总检清单 + 8 步流程图

2. 更新 `schema/tool/README.md` — 顶加 ⚠️ 先读提示，workflow doc 列导航首行

3. 更新 `AGENTS.md`「长字符串 / Shell 执行边界」节 — 顶加 🔔 触发框 + 5 步速查

4. 精简 `schema/encoding/js-ts-scripting-best-practices.md`
   - 移除第 0 节前置阅读（通用前置阅读不属 JS/TS 专属）
   - 第 3 节重写为短引用，指向 `schema/tool/file-write-helper-workflow.md`
   - description 字段聚焦 JS/TS 特有内容

**文档体系最终状态**：

```
AGENTS.md（session 必读）
  └── 🔔 触发：写文件 → schema/tool/file-write-helper-workflow.md
       ├── 铁律 + 禁止清单
       ├── 5 步速查
       ├── 编码选择 + 前置约束
       └── 总检清单 + 流程图
            ↓
schema/encoding/js-ts-scripting-best-practices.md（引用权威文档，不重复）
schema/tool/README.md（⚠️ 先读提示）
```


## 一、文本文件变更清单

### 1. 新建 `debug/slides-eval/requirements.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/slides-eval/requirements.md` |
| **变更类型** | 新建 |
| **作用** | 3 页季度回顾 PPT 需求文档，供 Slides Skill 和 ppt-master 双线生成使用 |
| **迁移方式** | 从 git 拉取即可 |

### 2. 新建 `debug/slides-eval/slides-skill/build.js`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/slides-eval/slides-skill/build.js` |
| **变更类型** | 新建 |
| **技术要点** | PptxGenJS 直接构建；使用 `module.paths.unshift()` 注入依赖路径；输出 3 页季度回顾 PPTX |
| **作用** | Slides Skill 的验证脚本，展示隔离环境 JS 依赖注入标准写法 |
| **迁移方式** | 从 git 拉取；若需在新的 Node 环境运行，先确认 `venv/pptxgenjs/` 已安装 |

### 3. 新建 `debug/slides-eval/slides-skill/slides-skill-output.pptx`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/slides-eval/slides-skill/slides-skill-output.pptx` |
| **变更类型** | 新建（二进制产物） |
| **作用** | Slides Skill 的验证输出，供 python-pptx 验证文本可编辑性 |
| **迁移方式** | 重新运行 `build.js` 生成，或从 git 拉取 |

### 4. 新建 `debug/slides-eval/evaluation_report.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/slides-eval/evaluation_report.md` |
| **变更类型** | 新建 |
| **作用** | Slides Skill vs ppt-master 全面对比：生成方式、文本可编辑性、布局灵活性、外部依赖、学习成本 |
| **迁移方式** | 从 git 拉取即可 |

### 5. 新建 `docs/tooling/opencode/slides-skill-usage-retrospective.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/slides-skill-usage-retrospective.md` |
| **变更类型** | 新建 |
| **作用** | 回顾文档：包含 `module.paths.unshift()` 发现过程、三种依赖注入方案对比、long content 写入经验、未来改进项 |
| **迁移方式** | 从 git 拉取 |

### 6. 更新 `docs/tooling/opencode/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/README.md` |
| **变更类型** | 修改 |
| **修改点** | 添加 slides-skill-usage-retrospective.md 导航链接 |
| **迁移方式** | 从 git 拉取 |

### 7. 新建 `schema/tool/file-write-helper-workflow.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/file-write-helper-workflow.md` |
| **变更类型** | 新建 |
| **作用** | 跨语言/跨场景长文本文件写入标准操作流程权威文档 |
| **迁移方式** | 从 git 拉取 |

### 8. 修改 `schema/tool/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/README.md` |
| **变更类型** | 修改 |
| **修改点** | 顶加 ⚠️ 先读提示；file-write-helper-workflow.md 列导航首行；file-write-helper.py/ini 注释指向 workflow doc |
| **迁移方式** | 从 git 拉取 |

### 9. 修改 `venv/.opencode/AGENTS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | 修改 |
| **修改点** | 「长字符串 / Shell 执行边界」节顶加 🔔 触发框：先读 file-write-helper-workflow.md + 5 步速查 |
| **迁移方式** | 从 git 拉取或按触发框内容手工合并 |

### 10. 修改 `schema/encoding/js-ts-scripting-best-practices.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/encoding/js-ts-scripting-best-practices.md` |
| **变更类型** | 修改 |
| **修改点** | 移除第 0 节前置阅读；第 3 节从重复通用工作流改为短引用；description 收紧为 JS/TS 专属 |
| **迁移方式** | 从 git 拉取 |

### 11. 修改 `schema/encoding/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/encoding/README.md` |
| **变更类型** | 修改 |
| **修改点** | 添加 js-ts-scripting-best-practices.md 导航链接 |
| **迁移方式** | 从 git 拉取 |

### 12. 关联文档（本 session 前已存在，本次引用/联动）

| 路径 | 关系 |
|------|------|
| `references/env-migrations/env-migration-agent-long-content-two-hop-2026-06-02-164241.md` | 同日较早的 env-migration，覆盖 long content + Shell 边界 + 术语表 |
| `schema/structure/env-migration-template.md` | env-migration 文档模板（本次按此格式撰写） |
| `schema/structure/doc-terminology-zh-en.md` | 中英文术语对照表 |
| `schema/structure/doc-naming-conventions.md` | 命名规范 |
| `schema/encoding/script-encoding-conventions.md` | 编码矩阵（workflow doc 引用） |
| `schema/tool/file-write-helper.py` | 写入引擎（workflow doc 引用） |
| `schema/tool/file-write-helper.ini` | ini 模板（workflow doc 引用） |


## 二、非文本操作（文件系统/缓存迁移）

本次 session **无** 文件系统级别操作。


## 三、环境变量速查

本次 session **未修改** `.vscode/settings.json` 或终端注入项。


## 四、验证清单（新环境 Agent 自检）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | AGENTS 含 file-write-helper 触发框 | 搜索 `🔔` 在「长字符串 / Shell 执行边界」节 | 存在，含先读 schema/tool/file-write-helper-workflow.md |
| 2 | AGENTS 含 5 步速查 | 同上节 5 步清单存在 | 1-5 步骤完整 |
| 3 | workflow 权威文档存在 | `Test-Path schema/tool/file-write-helper-workflow.md` | True |
| 4 | workflow 文档包含铁律/禁止/编码/流程图 | 读取前 10 行确认章节结构 | 铁律、禁止写法、编码选择表、流程图均存在 |
| 5 | schema/tool/README 含 ⚠️ 先读提示 | 搜索 `⚠️` 在 schema/tool/README.md | 存在 |
| 6 | JS/TS 文档无前置阅读节 | 在 js-ts-scripting-best-practices.md 搜索 `前置阅读` | 无匹配 |
| 7 | JS/TS 文档第 3 节为引用 | 搜索 `引用权威文档` | 存在 |
| 8 | 评估报告存在 | `Test-Path debug/slides-eval/evaluation_report.md` | True |
| 9 | 回顾文档存在 | `Test-Path docs/tooling/opencode/slides-skill-usage-retrospective.md` | True |
| 10 | module.paths.unshift 记录在回顾文档中 | 搜索 `module.paths` | 有分析内容 |


## 五、试跑示例

### 5.1 验证隔离环境 JS 依赖注入

```powershell
# 确认 venv/pptxgenjs/ 存在
Test-Path "D:\pjt\cursor\cs_py\venv\pptxgenjs\node_modules"

# 运行 slides skill build.js
& "D:\pjt\cursor\cs_py\venv\node\node.exe" "D:\pjt\cursor\cs_py\debug\slides-eval\slides-skill\build.js"

# 验证输出
Test-Path "D:\pjt\cursor\cs_py\debug\slides-eval\slides-skill\slides-skill-output.pptx"
```

### 5.2 验证 file-write-helper 工作流

按 `schema/tool/file-write-helper-workflow.md` 第 4 节标准工作流操作：

```powershell
# Step 1: 拷贝模板
Copy-Item "D:\pjt\cursor\cs_py\schema\tool\file-write-helper.py" "D:\pjt\cursor\cs_py\venv\tmp\"
Copy-Item "D:\pjt\cursor\cs_py\schema\tool\file-write-helper.ini" "D:\pjt\cursor\cs_py\venv\tmp\job.ini"

# Step 2: write 工具直写 content.txt（不使用 Shell 命令行）

# Step 3: edit 工具修改 job.ini（填 target_path / content_file / encoding）

# Step 4: 运行 helper
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\venv\tmp\file-write-helper.py" --config "D:\pjt\cursor\cs_py\venv\tmp\job.ini"
```


## 六、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 恢复 AGENTS.md | 从 git 回退 `venv/.opencode/AGENTS.md` 至本 migration 之前 |
| 恢复 schema/tool/README.md | 从 git 回退 |
| 删除 schema/tool/file-write-helper-workflow.md | 若整个 workflow 文档被否决 |
| 恢复 js-ts-scripting-best-practices.md | 从 git 回退（内容已精简） |
| 删除 debug/slides-eval/ 评估产物 | Agent 评估用，非业务关键路径，可整体删除 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-02-173559 |
| **更新人** | Human + Agent Session |
| **变更触发** | Slides Skill 能力验证需求 + file-write-helper 工作流分散需集中化 |
| **下次修订条件** | OpenCode Slides Skill 接口变更；file-write-helper.py 功能变化；新增 PPT 生成路径 |
| **跨环境迁移参考** | 拉 git + 第 0 节总览 + 第四节验证清单；新环境 Agent 先读 AGENTS.md 触发框 |


*文档生成时间：2026-06-02*
*对应文件名时间戳：2026-06-02-173559*
