---
title: scripts/ 目录子分类重构深度研究
description: 记录 deploy-git-isolated 任务 scripts/ 目录从摊平到六分法的完整决策过程，涵盖问题背景、方案对比、选型理由、实施验证与经验沉淀。date: 2026-06-18
---

# scripts/ 目录子分类重构深度研究

## 1. 问题背景

deploy-git-isolated 任务的 scripts/ 目录在重构前处于摊平状态，根下直接堆放 20 余个文件，包括：

- 8 个 Step 流程脚本（github-step-01-init.ps1 ~ github-step-08-upstream.ps1）
- 10 个独立工具脚本（git-*.ps1、github-*.ps1）
- 2 个聚合入口（github-lib.ps1、py_lib.py）
- 2 个插件配置（lib-sort-rules.json、py-sort-rules.json）
- 1 个速查文档（EXEC-CHEATSHEET.md）
- 2 个插件目录（lib-plugins/、py-plugins/）

摊平结构带来的问题：

1. **Agent 速查困难**：Agent 在执行任务时，需要快速定位正确的脚本文件。20 个文件摊平在根下，缺乏语义分组，Agent 无法通过目录名做第一层过滤，只能逐个读取文件名判断。
2. **望文生义失效**：文件名虽然有前缀（github-step-、git-），但无法通过目录层级传达"这是流程步骤还是独立工具"的元信息。
3. **同语言脚本混排**：PS 脚本与 Python 入口/配置混放，扩展时缺乏明确的落盘位置约定，容易随手丢到根下。
4. **示例与生产代码无边界**：本次新建的 py_lib 用法示例脚本，如果随手放在 venv/tmp/ 或 scripts/ 根下，无法被后续 Agent 发现，示例的价值归零。

## 2. 意图与目标

用户给出的核心意图：

> "方便 agent 速查，快速定位引用，望文生义最好。"

拆解为三个设计目标：

| 目标 | 含义 |
|------|------|
| **速查** | Agent 通过目录名即可缩小搜索范围，无需遍历全部文件 |
| **望文生义** | 目录名本身携带语义（steps、tools、examples、语言前缀），降低认知成本 |
| **对齐** | PS 侧与 Python 侧的目录结构保持对称，避免两套截然不同的组织方式 |

附加约束（用户明确）：

- entry-xx 和 sort-rules.json 放 scripts/ 根下没问题
- 分类目录名要带语言前缀（ps-、py-），避免跨语言混排

## 3. 约束条件

在提出方案前，先明确不可触碰的约束：

1. **入口与配置必须留在根下**
   - github-lib.ps1、lib-sort-rules.json
   - py_lib.py、py-sort-rules.json
   这些文件是 Agent 速查时的"锚点"，如果深埋子目录，调用路径会变长，违背速查意图。

2. **插件目录已独立**
   - lib-plugins/（PS 插件）
   - py-plugins/（Python 插件）
   这两个目录已经是良好的子分类，不动。

3. **向后兼容**
   - ENTRY.json 中的路径引用需要同步更新
   - EXEC-CHEATSHEET.md 中的命令示例需要同步更新
   - 被移动脚本内部的相对路径引用（如 `Join-Path $PSScriptRoot "github-lib.ps1"`）需要修复

4. **预留空位**
   - 某些分类当前无内容（如 py-steps/、ps-examples/），但为未来扩展预留目录

## 4. 方案探讨

### 4.1 方案 A：两分法（steps/ + tools/）

```
scripts/
├── steps/          # 所有步骤脚本
├── tools/          # 所有独立工具
└── ...
```

**优点**：简单，只有两层。

**缺点**：
- PS 与 Python 脚本混排，语言边界不清
- 无法区分"可复用工具"与"用法示例"
- 不符合用户"带语言前缀"的要求

### 4.2 方案 B：三分法（ps/、py/、shared/）

```
scripts/
├── ps/             # 所有 PowerShell 相关
│   ├── steps/
│   └── tools/
├── py/             # 所有 Python 相关
│   ├── steps/
│   └── tools/
└── shared/         # 共享配置与入口
```

**优点**：语言边界清晰。

**缺点**：
- 入口文件（github-lib.ps1、py_lib.py）如果放在 shared/，则打破了"入口在根下"的速查习惯
- 如果入口留在根下，而 ps/ 和 py/ 子目录中也有 steps/tools，会导致 Agent 需要同时查根下和两级子目录
- 目录层级过深（scripts/ps/steps/），路径冗长

### 4.3 方案 C：六分法（ps-steps、ps-tools、ps-examples、py-steps、py-tools、py-examples）

```
scripts/
├── ps-steps/       # PS 流程步骤
├── ps-tools/       # PS 独立工具
├── ps-examples/    # PS 示例
├── py-steps/       # Python 流程步骤
├── py-tools/       # Python 独立工具
├── py-examples/    # Python 示例
└── ...
```

**优点**：
- 语言 + 职责双重语义，完全望文生义
- 扁平层级（scripts 下直接是分类目录），不深于两级
- 预留 examples 空位，示例脚本有明确的持久化归属
- 与用户"带语言前缀"的要求完全对齐

**缺点**：
- 空目录当前无内容（py-steps/、ps-examples/），可能被误认为"多余"
- 目录数量较多（6 个），但这是语义清晰度的代价

### 4.4 方案对比表

| 维度 | 两分法 | 三分法 | 六分法 |
|------|--------|--------|--------|
| 速查效率 | 中（需遍历 steps/ 或 tools/ 内部） | 低（需先判语言，再判职责） | 高（目录名即语义） |
| 望文生义 | 弱（steps/tools 无语言信息） | 中（需进入二级目录） | 强（ps-tools 一目了然） |
| 路径长度 | 短 | 长 | 中 |
| 预留扩展 | 无 examples 位置 | 有 examples 位置 | 有，且职责清晰 |
| 用户要求满足度 | 不满足语言前缀 | 部分满足 | 完全满足 |

## 5. 选型决策

**选定方案：六分法（方案 C）**

核心理由：

1. **语义密度最高**：目录名 `ps-tools` 同时携带"语言=PS"和"职责=工具"两个维度，Agent 无需进入目录即可做出正确判断。
2. **对称性**：PS 侧有 steps/tools/examples，Python 侧也有 steps/tools/examples，两套语言体系的组织方式完全一致，降低心智负担。
3. **示例有归宿**：本次新建的 usage-demo.py 和 check-links.py，如果放在 py-tools/ 下，是"可复用工具"；如果放在 py-examples/ 下，是"用法示范"。二者职责不同，分开放置避免混淆。
4. **预留空位不是负担**：py-steps/ 和 ps-examples/ 当前为空，但它们是语义占位符，告诉后续 Agent"Python 流程脚本放这里"、"PS 示例放这里"，防止随手摊平。

## 6. 实施过程

### 6.1 目录创建

创建 6 个分类子目录：

```
scripts/ps-steps/
scripts/ps-tools/
scripts/ps-examples/
scripts/py-steps/
scripts/py-tools/
scripts/py-examples/
```

### 6.2 文件迁移

| 原路径 | 新路径 | 迁移理由 |
|--------|--------|---------|
| scripts/github-step-0N-*.ps1 | scripts/ps-steps/ | 流程步骤，PS 语言 |
| scripts/github-safety-check.ps1 | scripts/ps-tools/ | 独立工具，PS 语言 |
| scripts/github-sync-issue.ps1 | scripts/ps-tools/ | 独立工具，PS 语言 |
| scripts/git-*.ps1 | scripts/ps-tools/ | 独立工具，PS 语言 |
| scripts/github-create-issue.ps1 | scripts/ps-tools/ | 独立工具，PS 语言 |
| scripts/github-init-empty-repo.ps1 | scripts/ps-tools/ | 独立工具，PS 语言 |
| scripts/github-sync-issue-config.json | scripts/ps-tools/ | 配置文件，归属同步工具 |

### 6.3 路径修复

被移动的 10 个 .ps1 脚本内部引用了 `github-lib.ps1`，原路径假设二者平级：

```powershell
# 旧（平级）
$libPath = Join-Path $PSScriptRoot "github-lib.ps1"
```

迁移后，脚本位于 ps-steps/ 或 ps-tools/ 子目录中，需要向上回退一级：

```powershell
# 新（子目录 → 上级）
$libPath = Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"
```

涉及的 10 个文件：8 个 step 脚本 + github-safety-check.ps1 + github-sync-issue.ps1。

### 6.4 新建 Python 工具与示例

| 文件 | 位置 | 职责 |
|------|------|------|
| check-links.py | scripts/py-tools/ | Markdown 链接验证 CLI，走 py_lib 正规入口 |
| usage-demo.py | scripts/py-examples/ | py_lib 插件体系用法示范 |

### 6.5 下游同步

同步更新以下文件中的路径引用：

- ENTRY.json：active_scripts / step_manifests / maintenance_scripts / issue_sync，共 20+ 处
- EXEC-CHEATSHEET.md：所有命令示例中的脚本路径
- README.md：脚本索引表
- task-scenario-triggers.json：entry_script 路径
- changelog：追加重构记录

## 7. 踩坑与修复

### 7.1 踩坑 1：Python 模块命名与文件命名冲突

最初尝试将入口文件命名为 `py-lib.py`（与 `lib-sort-rules.json` 对齐，使用连字符），但 Python 的 `import` 语句不支持连字符模块名：`import py-lib` 会报语法错误。

**修复**：改回下划线命名 `py_lib.py`，与 Python 模块规范一致。配置名仍用连字符 `py-sort-rules.json`（JSON 文件不受 import 限制）。

### 7.2 踩坑 2：py_lib.py 最初放在 py-plugins/ 子目录中

最初将 `py_lib.py` 和 `py-sort-rules.json` 放在 `scripts/py-plugins/` 下，导致：
- 入口与配置和插件混排，层级不对称（PS 入口在 scripts/ 根下，Python 入口却在子目录中）
- 测试脚本 import 路径混乱：`sys.path.insert(0, r"...\scripts\py-plugins")`

**修复**：将入口和配置提升到 `scripts/` 根下，插件留在 `py-plugins/` 中，与 PS 的 `github-lib.ps1 + lib-sort-rules.json`（根下）和 `lib-plugins/`（子目录）完全对称。

### 7.3 踩坑 3：原始字符串中的反斜杠导致 SyntaxWarning

`py_lib.py` 的 docstring 示例中使用了 `r"...\scripts"`，其中 `\s` 被 Python 解析器识别为无效的转义序列，触发 `SyntaxWarning`。

**修复**：将 docstring 示例中的 Windows 路径反斜杠替换为正斜杠，或双写反斜杠：`r"...\\scripts"` 或 `".../scripts"`。

### 7.4 踩坑 4：Markdown 正文中的 --- 分隔线污染 frontmatter

在编写 SOP.md、EXEC-CHEATSHEET.md 等文档时，习惯性地使用 `---` 作为 section 之间的视觉分隔线。这导致正文中出现大量 `---`，与 YAML frontmatter 的定界符冲突，任何依赖 `---` 做区块分割的解析器（Obsidian、frontmatter 提取器）都会将正文误判为新的 YAML 区块。

**修复**：
1. 删除本次创建/修改的文档中的所有正文 `---`，改用空行或 `##` 标题做分隔
2. 增强 `link_checker.py`，新增 `_check_frontmatter_dashes()` 函数，检测 frontmatter 之后是否还有独立的 `---` 行
3. 返回结果扩展 `format_violations` 字段，使格式违规可被自动检测

## 8. 验证结论

重构完成后，执行以下验证：

### 8.1 JSON lint

| 文件 | 结果 |
|------|------|
| ENTRY.json | 通过 |
| task-scenario-triggers.json | 通过 |

### 8.2 链接与格式验证

运行 `py-tools/check-links.py`：

| 指标 | 结果 |
|------|------|
| 扫描文件 | 19 个 .md |
| 检查链接 | 15 个 |
| 断裂链接 | 0 个 |
| 格式违规（--- 污染） | 0 个（本次修复后） |

### 8.3 插件加载验证

运行 `py-examples/usage-demo.py`：

| 测试项 | 结果 |
|--------|------|
| core profile 加载 | 5 个基础设施插件 |
| md-validation profile 加载 | 4 个（含依赖自动补齐） |
| devroot 探测 | D:/pjt/cursor/cs_py |
| link_checker 链接验证 | checked=15, broken=0 |
| EncodingGuard 编码切换 | 通过 |

### 8.4 PS 路径引用验证

通过 `read` 检查 10 个被移动的 .ps1 脚本：

```powershell
$libPath = Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"
```

全部 10 个文件已正确更新，无残留平级引用。

## 9. 最终目录结构

```
scripts/
├── github-lib.ps1              # PS 聚合入口（根下锚点）
├── lib-sort-rules.json         # PS 插件配置（根下锚点）
├── py_lib.py                   # Python 聚合入口（根下锚点）
├── py-sort-rules.json          # Python 插件配置（根下锚点）
├── EXEC-CHEATSHEET.md          # 执行速查表
├── lib-plugins/                # PS 插件目录
│   ├── constants.ps1
│   ├── encoding.ps1
│   └── github-api.ps1
├── py-plugins/                 # Python 插件目录
│   ├── __init__.py
│   ├── detect_devroot.py
│   ├── encoding.py
│   ├── constants.py
│   ├── core.py
│   ├── env_config.py
│   └── link_checker.py
├── ps-steps/                   # PS Step 0-8 流程脚本
│   ├── github-step-01-init.ps1
│   ├── ...
│   └── github-step-08-upstream.ps1
├── ps-tools/                   # PS 独立工具
│   ├── git-clone-isolated.ps1
│   ├── git-config-global.ps1
│   ├── git-isolated.ps1
│   ├── git-multi-identity.ps1
│   ├── git-verify-isolation.ps1
│   ├── github-create-issue.ps1
│   ├── github-init-empty-repo.ps1
│   ├── github-safety-check.ps1
│   ├── github-sync-issue.ps1
│   └── github-sync-issue-config.json
├── ps-examples/                # PS 示例（预留）
├── py-steps/                   # Python 流程脚本（预留）
├── py-tools/                   # Python 独立工具
│   └── check-links.py          # Markdown 链接验证 CLI
└── py-examples/                # Python 示例
    └── usage-demo.py           # py_lib 用法示范
```

## 10. 经验沉淀

### 10.1 目录命名原则

- **双重语义**：目录名同时携带"语言"和"职责"两个维度（ps-tools > tools）
- **扁平优先**：不超过两级目录（scripts/ → ps-tools/），路径长度可控
- **预留空位**：即使当前为空，也要创建语义占位目录，防止未来摊平

### 10.2 迁移 checklist

移动脚本文件时，必须同步检查以下四类引用：

1. **脚本内部相对路径**：被移动脚本引用根下文件的路径（如 `Join-Path $PSScriptRoot "github-lib.ps1"`）
2. **ENTRY.json 路径登记**：所有被移动文件在索引中的 `path` 字段
3. **文档命令示例**：EXEC-CHEATSHEET.md、README.md 中的调用路径
4. **触发器入口**：task-scenario-triggers.json 中的 `entry_script`

### 10.3 Markdown 格式铁律

- YAML frontmatter 的 `---` 定界符有且仅有一对，位于文件开头
- 正文中绝对禁止出现独立的 `---` 行
- 视觉分隔改用空行、`##` 二级标题或 `***`（水平规则备选）
- lint 工具必须覆盖此规则（已纳入 link_checker.py）

### 10.4 Python 模块命名与文件命名分离

- Python 模块名（用于 import）只能包含下划线，不能用连字符
- 配置文件名可以用连字符，与模块名解耦
- 当需要"文件命名对齐"与"Python import 规范"冲突时，优先满足 import 规范

## 11. 后续建议

1. **统一清理存量文档中的 --- 污染**：当前 task 根目录下还有大量历史文档（README.md、GOAL.md、task-canonical-baseline.md 等）含有正文 `---`，建议另开一次专门任务批量清理。
2. **将 link_checker 的 format_violations 纳入 CI/交付门禁**：在交付前强制运行 check-links.py，如有 format_violations 则阻断交付。
3. **py-steps/ 填充**：当 Python 侧也需要 Step 流程脚本时，直接落入 py-steps/，无需重新设计目录结构。
4. **ps-examples/ 填充**：当 PS 侧需要用法示例脚本时，直接落入 ps-examples/，与 py-examples/ 对称。
