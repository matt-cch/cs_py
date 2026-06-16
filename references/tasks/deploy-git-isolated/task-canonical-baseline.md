---
title: deploy-git-isolated — Task Canonical Baseline
description: 本 task 的认知基线与真源契约。记录 Agent 与人类共同确认的事实标准、命名约定、执行路径，以及 SOP-CHEATSHEET 与 TASK-TOOLS-INDEX 的语义区分。
date: 2026-06-16
---

# deploy-git-isolated — Task Canonical Baseline

> **核心意图**：本文档不是「格式说明书」，而是 **Agent 与人类在渐进式交互中共同确认的事实标准**。  
> 它确保双方对以下问题有**归一化的理解**：
> - 什么是 Task（与 Skill 的边界在哪）
> - 真源（Single Source of Truth）存放在哪里
> - 命名约定（Naming Convention）如何消除歧义
> - Agent 执行路径与人类查阅路径如何对照
> - 如何渐进式确认、认可、固化事实
>
> **适用范围**：`references/tasks/deploy-git-isolated/` 目录下的全部文件与操作。  
> **约束性质**：框架层规范，极低变动频率；触及修改时按修订联动规则执行。
> **模板来源**：`schema/task-template/task-canonical-baseline.md`

---

## 1. 语义定义

### 1.1 什么是 Task

Task 是**将一次可复用的工程操作固化为标准化骨架**的单元。特征：

- **有明确生命周期**：预检 → 扫描 → 处理 → 验证 → 比对 → 清理（6 步闭环）。
- **有真源索引**：`ENTRY.json` 是机器唯一入口，人类通过 `README.md` 和 `SOP-CHEATSHEET.md` 进入。
- **有设计文档**：`DESIGN.md` 记录决策、SOP、踩坑，供跨 session 接续。
- **有脚本化调用**：速查表中的每条命令对应磁盘上的独立 `.ps1` / `.py` 文件，禁止现写。

### 1.2 Task 与 Skill 的区别

| 维度 | Task | Skill |
|------|------|-------|
| **定位** | 一次性/周期性工程操作 | 可复用的 Agent 能力扩展 |
| **载体** | `references/tasks/` 目录 | `.agents/skills/` 或 `.opencode/skills/` |
| **入口** | `ENTRY.json` + `run-entry.py` | `SKILL.md` |
| **调用方** | Agent / 人类终端 | 仅 Agent（OpenCode subagent） |
| **生命周期** | 执行完可归档 | 长期驻留 |

---

## 2. 目录结构规范

```
references/tasks/deploy-git-isolated/
├── README.md                   # 人类入口：任务总览、当前状态、待办、版本
├── DESIGN.md                   # 设计文档：决策记录、SOP、踩坑
├── ENTRY.json                  # 机器入口：真源索引、脚本清单、状态追踪、版本演进
├── task-config.json            # 任务配置：路径、工具链、分组、参数
├── task-scenario-triggers.json # 触发条件真源：5 场景 trigger 映射
├── TASK-TOOLS-INDEX.md         # 工具速查表：本地脚本 + 外部通用工具引用 + 边界矩阵
├── scripts/                    # 独立调用脚本（.ps1 / .py / .sh）
│   ├── github-lib.ps1          # 共享库聚合入口（拓扑排序加载插件）
│   ├── lib-sort-rules.json     # 插件排序真源
│   ├── lib-plugins/            # 共享函数插件
│   ├── github-step-01-init.ps1 # Step 1-8: 部署流水线
│   ├── ...                     # ...
│   ├── github-safety-check.ps1 # 安全检查
│   ├── git-isolated.ps1        # 通用包装器
│   ├── SOP-CHEATSHEET.md       # 命令速查表：Agent + 人类共享同一真源
│   └── ...
├── docs/                       # 补充文档
│   └── PLUGIN-ARCHITECTURE.md  # 插件化点源架构设计文档
├── skeleton/                   # 骨架脚本（Python）
│   ├── step-00-precheck.py
│   └── ...
├── changelog/                  # 变更记录（迭代历史）
├── gotchas/                    # 踩坑记录（反面教材）
└── archive/                    # 归档目录
```

### 2.1 强制文件

| 文件 | 职责 | 是否强制 |
|------|------|---------|
| `README.md` | 任务总览、状态、待办 | ✅ |
| `DESIGN.md` | 设计决策、SOP、踩坑 | ✅ |
| `ENTRY.json` | 机器可读真源索引 | ✅ |
| `task-config.json` | 配置（路径、工具链、分组） | ✅ |
| `SOP-CHEATSHEET.md` | **命令速查表**（Agent + 人类） | ✅ |
| `TASK-TOOLS-INDEX.md` | **工具索引**（本地 + 外部引用 + 边界） | ✅ |

### 2.2 可选文件

| 文件 | 职责 | 何时需要 |
|------|------|---------|
| `task-scenario-triggers.json` | 触发条件真源（带 `$schema` 自描述） | task 有触发词映射需求时 |
| `docs/PLUGIN-ARCHITECTURE.md` | 架构设计说明（本 task 有插件化体系） | 有复杂共享库架构时 |

---

## 3. 文件格式规范

### 3.1 SOP-CHEATSHEET.md（命令速查表）

> **核心原则**：同一功能只出现一次，Agent 格式与人类格式上下对照，**禁止分成两大段落**。

#### 格式模板

```markdown
## N. 功能标题

**Agent:**
```powershell
powershell -ExecutionPolicy Bypass -File "${devroot}\...\script.ps1" <args>
```

**终端:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\...\script.ps1 <args>
```
```

#### 强制规则

1. **真源唯一**：速查表中所有命令指向 `scripts/` 下的同一 `.ps1` 文件，Agent/人类/终端共享。
2. **上下对照**：每个功能区块内先写 Agent 格式，紧接写终端格式，用 `---` 分隔不同功能。
3. **变量约定**：Agent 格式使用 `${devroot}` 等变量；终端格式使用相对路径 `.\references\...`。
4. **执行策略**：Agent 必须显式指定 `-ExecutionPolicy Bypass`；终端用 `Set-ExecutionPolicy -Scope Process ...;` 前缀。
5. **禁止表格罗列命令**：速查表的主体是**对照代码块**，不是表格。
6. **禁止混杂工具索引**：SOP-CHEATSHEET 只管「命令怎么执行」，不管「有什么工具、边界在哪」。工具索引见 `TASK-TOOLS-INDEX.md`。

---

### 3.2 TASK-TOOLS-INDEX.md（工具索引表）

> **核心原则**：回答「这个 task 有什么工具？在哪里？什么时候用？边界是什么？」。
> **与 SOP-CHEATSHEET 的本质区别**：SOP 面向「执行者」（知道要做什么，想知道怎么敲命令）；TOOLS-INDEX 面向「规划者」（想知道有哪些能力、该调哪个工具、是否已有现成轮子、能否用外部通用工具替代）。

#### 必须包含的章节

1. **本地专属脚本清单**：按职责分类（部署流水线 / 安全检查 / 通用包装器 / 共享库），每项含 `脚本名 | 职责 | 典型场景 | 状态`
2. **外部通用工具引用**：明确列出本 task 可能用到的 `runtime/`、`schema/tool/` 下的通用工具，每项含 `工具名 | 全局路径 | 登记索引 | 本 task 中的用途 | 边界说明`
3. **边界矩阵**：8+ 个典型场景的首选工具、次选/备选、禁止行为
4. **速查命令**：本地脚本 + 外部通用工具的典型调用命令

#### 强制规则

1. **禁止重复造轮子**：外部已存在且已登记的工具（如 `lint-json.py`、`lint-ps1.ps1`、`check-file-encoding.ps1`），必须在「外部通用工具引用」中列出，并在「边界矩阵」中规定「禁止自行实现同类功能」。
2. **铁律声明**：外部工具引用节必须包含一句铁律——「以上工具已存在且已登记，本 task 禁止自行实现同类功能。新增需求时先查 `verified-task-index.json` → `available_scripts_and_tools`。」
3. **关联文件导航**：底部必须列出与本 task 相关的全部文档的「文件 | 用途」对照表。

---

### 3.3 SOP-CHEATSHEET vs TASK-TOOLS-INDEX 对比总结

| 对比维度 | SOP-CHEATSHEET | TASK-TOOLS-INDEX |
|---------|---------------|------------------|
| **核心问题** | 「这条命令怎么执行？」 | 「这个 task 有什么工具？在哪里？边界是什么？」 |
| **内容形式** | Agent/终端双格式代码块 | 表格清单 + 边界矩阵 + 引用链路 |
| **是否含外部工具** | ❌ 否（只含本 task 脚本调用） | ✅ **是**（必须引用 runtime/ 和 schema/tool/ 通用工具） |
| **读者角色** | 执行者（复制粘贴命令） | 规划者（选择工具、判断边界） |
| **更新时机** | 新增/修改脚本命令时 | 新增/删除工具、发现外部通用工具可替代时 |
| **典型错误** | 把插件架构说明塞进来 | 把命令执行细节塞进来 |

> **一句话区分**：SOP 是「命令手册」，TOOLS-INDEX 是「能力地图」。

---

### 3.4 ENTRY.json

#### 字段说明

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
| `cheatsheet` | string | **SOP-CHEATSHEET.md 路径** |
| `changelog_dir` | string | changelog 目录路径 |
| `gotchas_dir` | string | gotchas 目录路径 |

#### `cheatsheet` 与 `tools_index` 字段语义

- `cheatsheet`：指向**命令速查表**（SOP-CHEATSHEET.md），回答「怎么执行」。
- `tools_index`：指向**工具索引表**（TASK-TOOLS-INDEX.md），回答「有什么工具、边界在哪」。
- 二者互补，不可互相替代。`ENTRY.json` 必须同时登记两者。

---

### 3.5 DESIGN.md

- 必须包含「背景」「设计决策」「目标目录结构」「SOP」「踩坑记录」章节。
- 设计决策必须记录「问题 → 方案 → 效果」三步。
- SOP 章节必须与 `SOP-CHEATSHEET.md` 内容一致，但可更详细（含解释性文字）。
- **新增**：Trigger 治理设计意图（第 6 节），记录 trigger 体系的六维元原则（治理、参照、边界、协调、审计、重建）。

---

## 4. 修订联动规则

当 task 目录发生以下变更时，必须同步更新关联文件：

| 触发条件 | 必须联动 | 更新内容 |
|---------|---------|---------|
| 新增/修改骨架脚本（`skeleton/*.py`） | `scripts/*.ps1` | 新增或更新对应调用脚本 |
| 新增/修改任何脚本 | `SOP-CHEATSHEET.md` | 新增/修改对照命令块 |
| 新增/重命名脚本 | `TASK-TOOLS-INDEX.md` | 更新本地脚本清单 |
| 发现外部通用工具可替代本 task 功能 | `TASK-TOOLS-INDEX.md` | 在外部引用节追加，更新边界矩阵 |
| 变更 `active_scripts[].status` | `ENTRY.json` | 同步状态字段 |
| 新增踩坑 | `gotchas/*.md` + `DESIGN.md` 第 7 章 | 记录现象/根因/修复 |
| 里程碑完成 | `changelog/` | 追加条目 |
| 新增/修改 trigger | `task-scenario-triggers.json` + 全局 `verified-trigger-index.json` | 同步登记 |

---

## 5. Agent vs Human 执行路径

### 5.1 Agent 调用

```
1. 读取 ENTRY.json 确认当前入口和脚本状态
2. 读取 TASK-TOOLS-INDEX.md 判断「该用哪个工具、有没有现成轮子」
3. 读取 SOP-CHEATSHEET.md 获取具体命令格式
4. 通过 bash 调用：powershell -ExecutionPolicy Bypass -File "<abs-path>" <args>
5. 执行后验收输出，更新 ENTRY.json 状态
```

### 5.2 Human 调用

```
1. 查看 README.md 了解任务总览
2. 查看 TASK-TOOLS-INDEX.md 了解本 task 有哪些工具、边界在哪
3. 查看 SOP-CHEATSHEET.md 复制具体命令
4. 在 VS Code/Cursor 终端内粘贴执行（相对路径格式）
5. 如需了解设计决策，阅读 DESIGN.md
```

### 5.3 核心差异

| 维度 | Agent | Human |
|------|-------|-------|
| 路径风格 | 绝对路径 `${devroot}\...` | 相对路径 `.\references\...` |
| 执行前缀 | `powershell -ExecutionPolicy Bypass -File` | `Set-ExecutionPolicy -Scope Process ...;` |
| 信息来源 | ENTRY.json（机器） | README.md + TASK-TOOLS-INDEX.md + SOP-CHEATSHEET.md（人类） |
| 状态追踪 | 自动更新 ENTRY.json | 手动阅读 README.md 待办 |

---

## 6. 文件位置约定

### 6.1 SOP-CHEATSHEET.md

- **默认**：`scripts/SOP-CHEATSHEET.md`（对齐本 task 的 scripts/ 强绑定风格）
- `ENTRY.json` 的 `cheatsheet` 字段必须如实登记路径

### 6.2 TASK-TOOLS-INDEX.md

- **固定位置**：`references/tasks/<task-name>/TASK-TOOLS-INDEX.md`（task 根目录下，与 README.md/ENTRY.json 同级）
- **原因**：工具索引是 task 级别的「能力地图」，不属于 `scripts/`（执行层）也不属于 `docs/`（补充层），应放在 task 根目录作为核心文件之一
- `ENTRY.json` 的 `tools_index` 字段必须登记路径

> **禁止**：`TASK-TOOLS-INDEX.md` 与 `SOP-CHEATSHEET.md` 内容互相渗透——前者管「有什么」，后者管「怎么执行」。

---

## 7. 版本演进与归档机制

### 7.1 版本语义

Task 采用 **SemVer-like** 三段式版本号：`MAJOR.MINOR.PATCH`

| 段位 | 递增条件 | 示例 |
|------|---------|------|
| **MAJOR** | 架构级重构、目录结构重排、职责边界变更 | `v1.x → v2.0` |
| **MINOR** | 新增功能/脚本、新增 Step、扩展配置、新增工具索引 | `v1.0 → v1.1` |
| **PATCH** | 修复、文档更新、状态变更（ready/pending）、真源刷新 | `v1.0.0 → v1.0.1` |

### 7.2 版本登记位置

| 文件 | 字段 | 说明 |
|------|------|------|
| `README.md` | 文末 `*任务版本: vX.Y.Z*` | 人类速览当前版本 |
| `ENTRY.json` | `meta.version` | 机器读取的真源版本 |
| `ENTRY.json` | `meta.version_history[]` | 演进历史记录 |
| `changelog/*.md` | 文件名含日期/版本 | 详细变更内容 |

### 7.3 演进示例（ENTRY.json）

```json
{
  "meta": {
    "version": "0.4.0",
    "version_history": [
      {"version": "0.1.0", "date": "2026-06-16", "note": "骨架创建，设计冻结"},
      {"version": "0.2.0", "date": "2026-06-16", "note": "Step 1-8 执行通过，插件架构就绪"},
      {"version": "0.3.0", "date": "2026-06-16", "note": "新增 task-scenario-triggers.json 触发真源"},
      {"version": "0.4.0", "date": "2026-06-16", "note": "拆分 TASK-TOOLS-INDEX.md，SOP 精简为纯命令速查"}
    ]
  }
}
```

### 7.4 Changelog 记录规范

> **共识来源**：用户与 Agent 在 2026-06-16 对话中共同确认。禁止自由发挥，必须按本格式记录。

#### 7.4.1 记录时机

- 任何对 task 文件的实质性修改（新增、重构、修复）完成后，必须立即记录 changelog
- 禁止「先改代码，等有空再补 changelog」—— changelog 是修改的**必要组成部分**

#### 7.4.2 文件格式

- **命名**：`changelog-YYYY-MM-DD-<slug>.md`（kebab-case slug，简短可识别）
- **位置**：`references/tasks/<task-name>/changelog/`
- **Frontmatter**：必须含 `title`、`description`、`date`

#### 7.4.3 正文结构（强制）

| 章节 | 是否强制 | 说明 |
|------|---------|------|
| **变更概览** | ✅ | 表格：类型、影响范围、风险等级、触发原因 |
| **变更时间线** | ✅ | 表格：变更项、之前、之后、触发原因 |
| **验证结果** | ✅ | 表格/列表：逐项确认（lint、执行、扫描等） |
| **已知问题** | 有则必填 | 本次变更暴露的待优化项，不可隐瞒 |
| **关联文件** | ✅ | 哪些文件被修改，状态标记 |

#### 7.4.4 禁止行为

- ❌ **禁止自由发挥**：不写「变更概览」直接罗列修改；不写「验证结果」直接声称「已验证」
- ❌ **禁止无时间线**：changelog 文件名和正文中都必须有明确的日期标识
- ❌ **禁止无触发原因**：每个变更项必须说明「为什么改」，不能只写「改了什么」
- ❌ **禁止隐瞒已知问题**：如果用户指出了缺陷或待优化方向，必须在「已知问题」中如实记录

#### 7.4.5 示例

见 `changelog/changelog-2026-06-16-git-isolated-devroot-probing.md`

---

### 7.5 归档机制

> **自包含原则**：每个 task 的归档历史存放在自身的 `archive/` 子目录下，不集中到 `references/tasks/` 根目录，方便 task 内直接检索。

**触发条件**：
- Task 进入长期冻结（6 个月无活跃变更）
- MAJOR 版本升级（架构重构），旧版本保留历史
- 人类明确指令「归档此 task」

**归档路径**：
```
references/tasks/deploy-git-isolated/archive/deploy-git-isolated-vN/
```

**归档内容**：
- 完整复制 task 根目录所有文件（保留历史真源）
- 归档目录内的 `README.md` 顶部标注 `**已归档**` + 归档日期 + 替代版本路径
- 原 `references/tasks/deploy-git-isolated/` 继续承载当前版本

**归档后当前版本处理**：
- 当前版本的 `README.md` 中增加「历史版本」导航链接
- `ENTRY.json` 的 `meta.archived_versions` 记录归档路径

---

## 8. 本 Task 的特殊约定

### 8.1 插件化架构

本 task 采用 `github-lib.ps1` + `lib-sort-rules.json` + `lib-plugins/` 三层插件化架构：

- **文件名冻结**：插件文件一旦命名，永不再改
- **配置与代码分离**：排序规则用独立 JSON 文件承载，不混在代码目录
- **拓扑排序加载**：Kahn 算法按依赖图自动排序，零文件重名即可插入新插件

> 详细架构说明见：`docs/PLUGIN-ARCHITECTURE.md`

### 8.2 Trigger 治理

本 task 的 trigger 索引遵循全局 `verified-trigger-index.json` 的治理规则：

- **新增三步流程**：查重 → 分配 ID → 登记索引 → 回写来源
- **来源文件引用**：task 级触发真源 `task-scenario-triggers.json` 顶部声明 `$schema`
- **边界定义**：`conflict_domains` 节明确定义与 proxy-downloader、download-runtime、project-handoff 的边界

> 治理设计意图见：`DESIGN.md` 第 6 节

### 8.3 外部工具引用铁律

本 task 执行过程中，以下通用能力**禁止自行实现**，必须调用已登记的外部工具：

| 能力 | 外部工具 | 登记位置 |
|------|---------|---------|
| JSON 语法验证 | `schema/tool/lint-json.py` | `verified-task-index.json` → `lint-json` |
| PS 语法验证 | `schema/tool/lint-ps1.ps1` | `verified-task-index.json` → `lint-ps1` |
| 文件编码检查 | `schema/tool/check-file-encoding.ps1` | `verified-task-index.json` → `check-file-encoding` |
| 文件写入 helper | `schema/tool/file-write-helper.py` | `verified-task-index.json` → `file-write-helper` |
| 时间戳生成 | `schema/tool/get-timestamp.ps1` | `verified-task-index.json` → `get-timestamp` |
| 运行时真源检测 | `references/runtime/verify-runtime.ps1` | `verified-task-index.json` → `verify-runtime` |
| 运行时工具下载 | `references/runtime/download-runtime-tool.ps1` | `verified-task-index.json` → `download-runtime-tool` |

---

*规范版本: v1.0*  
*模板来源: schema/task-template/task-canonical-baseline.md*  
*创建时间: 2026-06-16*  
*本 task 定制内容: 第 3.2/3.3 节（SOP vs TOOLS-INDEX 区分）、第 6.2 节（TASK-TOOLS-INDEX 位置约定）、第 8 节（本 task 特殊约定）*
