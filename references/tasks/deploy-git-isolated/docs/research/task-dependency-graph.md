---
title: deploy-git-isolated Task 依赖图与修订联动路径
description: 以树状结构展示 task/ 根目录向下的全部文件依赖关系（PS 点源、Python import、文档引用、配置索引），作为目录重构后快速定位影响面的工具。
date: 2026-06-18
meta: {}
---

# deploy-git-isolated Task 依赖图与修订联动路径

> **本文档职责**：在 scripts/ 目录重构后，用结构化依赖图展示"谁引用了谁"。当未来再次做目录变更时，按图索骥即可定位所有需要联动的下游文件，避免遗漏。
>
> **阅读方式**：每条依赖链标注了引用类型（点源/import/路径/索引），以及变更时的自检问题。

## 1. 顶层结构（Task 根目录）

```
deploy-git-isolated/
├── ENTRY.json                    # 脚本索引真源（所有脚本在此登记 path）
├── task-scenario-triggers.json   # 场景触发器（entry_script 指向具体脚本）
├── README.md                     # 脚本索引表（人工阅读导航）
├── SOP.md                        # 流程文档（引用 Step 脚本名，无硬编码路径）
├── DESIGN.md                     # 设计文档（无脚本路径引用）
├── GOAL.md                       # 目标文档（无脚本路径引用）
├── TASK-TOOLS-INDEX.md           # 工具索引（无脚本路径引用）
├── task-canonical-baseline.md    # 规范基线（无脚本路径引用）
├── scripts/
│   ├── github-lib.ps1            # PS 聚合入口（被 10 个 .ps1 点源引用）
│   ├── lib-sort-rules.json       # PS 插件配置（被 github-lib.ps1 读取）
│   ├── py_lib.py                 # Python 聚合入口（被 py-tools/、py-examples/ import）
│   ├── py-sort-rules.json        # Python 插件配置（被 py_lib.py 读取）
│   ├── EXEC-CHEATSHEET.md        # 执行速查（引用全部可执行脚本路径）
│   ├── lib-plugins/              # PS 插件（被 github-lib.ps1 拓扑排序后点源）
│   │   ├── constants.ps1         #   被 github-lib.ps1 聚合导入
│   │   ├── encoding.ps1          #   被 github-lib.ps1 聚合导入
│   │   └── github-api.ps1        #   被 github-lib.ps1 聚合导入
│   ├── py-plugins/               # Python 插件（被 py_lib.py 拓扑排序后 import）
│   │   ├── detect_devroot.py     #   被 py_lib.py 动态 import
│   │   ├── encoding.py           #   被 py_lib.py 动态 import
│   │   ├── constants.py          #   被 py_lib.py 动态 import；import detect_devroot
│   │   ├── core.py               #   被 py_lib.py 动态 import
│   │   ├── env_config.py         #   被 py_lib.py 动态 import；import constants
│   │   ├── link_checker.py       #   被 py_lib.py 动态 import；依赖 core, constants
│   │   └── md_lint.py            #   被 py_lib.py 动态 import
│   ├── ps-steps/                 # PS Step 0-8 流程脚本
│   │   ├── github-step-01-init.ps1        # 点源 ../github-lib.ps1
│   │   ├── github-step-02-gitignore.ps1   # 点源 ../github-lib.ps1
│   │   ├── github-step-03-readme.ps1      # 点源 ../github-lib.ps1
│   │   ├── github-step-04-stage.ps1       # 点源 ../github-lib.ps1
│   │   ├── github-step-05-commit.ps1      # 点源 ../github-lib.ps1
│   │   ├── github-step-06-remote.ps1      # 点源 ../github-lib.ps1
│   │   ├── github-step-07-push.ps1        # 点源 ../github-lib.ps1
│   │   └── github-step-08-upstream.ps1    # 点源 ../github-lib.ps1
│   ├── ps-tools/                 # PS 独立工具
│   │   ├── git-clone-isolated.ps1         # 无外部点源
│   │   ├── git-config-global.ps1          # 无外部点源
│   │   ├── git-isolated.ps1               # 无外部点源（内部动态探测 devroot）
│   │   ├── git-multi-identity.ps1         # 无外部点源
│   │   ├── git-verify-isolation.ps1       # 无外部点源
│   │   ├── github-create-issue.ps1        # 无外部点源（独立执行）
│   │   ├── github-init-empty-repo.ps1     # 无外部点源
│   │   ├── github-safety-check.ps1        # 点源 ../github-lib.ps1
│   │   ├── github-sync-issue.ps1          # 点源 ../github-lib.ps1；同目录读取 github-sync-issue-config.json
│   │   └── github-sync-issue-config.json  # 被 github-sync-issue.ps1 读取
│   ├── ps-examples/              # PS 示例（当前为空，预留）
│   ├── py-steps/                 # Python 流程脚本（当前为空，预留）
│   ├── py-tools/                 # Python 独立工具
│   │   └── check-links.py        # import ../py_lib.py；fallback 直接 import ../py-plugins/link_checker
│   └── py-examples/              # Python 示例
│       └── usage-demo.py         # import ../py_lib.py；import ../py-plugins/encoding
├── docs/
│   ├── README.md                 # 登记 docs/ 子分类导航（含 research/ 新分类）
│   ├── PLUGIN-ARCHITECTURE.md    # 引用 lib-plugins/、py-plugins/（相对路径，不受子分类影响）
│   ├── TASK-GUIDE.md             # 引用 scripts/ 下文件（相对路径）
│   ├── harness/
│   │   └── delivery-checklist.md # 引用 scripts/ 下文件（相对路径）
│   ├── patterns/
│   │   ├── manifest-plugin-pattern.md    # 引用 scripts/ 下文件
│   │   └── profile-filter-pattern.md     # 引用 github-lib.ps1
│   ├── playbooks/
│   │   └── github-publish-playbook.md    # 引用 ps-tools/ 下文件路径
│   └── research/
│       └── scripts-directory-taxonomy-research.md  # 记录迁移前后路径对照
├── changelog/
│   └── *.md                      # 历史记录，含旧路径描述（历史状态，不修改）
└── gotchas/
    └── *.md                      # 历史记录，含旧路径描述
```

## 2. 依赖链详解（按变更场景分类）

### 2.1 场景 A：scripts/ 根下入口文件移动

**涉及文件**：`github-lib.ps1`、`lib-sort-rules.json`、`py_lib.py`、`py-sort-rules.json`

**影响面**：

```
github-lib.ps1 移动
    ├── PS 点源引用链（10 个文件）
    │   ├── ps-steps/github-step-01-init.ps1        # Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"
    │   ├── ps-steps/github-step-02-gitignore.ps1   # 同上
    │   ├── ps-steps/github-step-03-readme.ps1      # 同上
    │   ├── ps-steps/github-step-04-stage.ps1       # 同上
    │   ├── ps-steps/github-step-05-commit.ps1      # 同上
    │   ├── ps-steps/github-step-06-remote.ps1      # 同上
    │   ├── ps-steps/github-step-07-push.ps1        # 同上
    │   ├── ps-steps/github-step-08-upstream.ps1    # 同上
    │   ├── ps-tools/github-safety-check.ps1        # 同上
    │   └── ps-tools/github-sync-issue.ps1          # 同上
    ├── 文档引用链
    │   ├── README.md                               # 表格中的 scripts/github-lib.ps1
    │   ├── EXEC-CHEATSHEET.md                      # 示例中的 . "${devroot}\scripts\github-lib.ps1"
    │   ├── docs/patterns/profile-filter-pattern.md # 引用 github-lib.ps1
    │   └── docs/PLUGIN-ARCHITECTURE.md             # 引用 github-lib.ps1
    ├── 索引引用链
    │   ├── ENTRY.json                              # active_scripts[].path
    │   └── task-scenario-triggers.json             # entry_script（场景 01 触发器）
    └── 插件引用链
        └── lib-plugins/*.ps1                       # docstring 中"被 github-lib.ps1 聚合导入"

py_lib.py 移动
    ├── Python import 链
    │   ├── py-tools/check-links.py                 # sys.path.insert(0, str(_scripts_dir)) + from py_lib import ...
    │   └── py-examples/usage-demo.py               # 同上
    ├── 文档引用链
    │   ├── docs/PLUGIN-ARCHITECTURE.md             # 引用 py_lib.py
    │   └── docs/research/*.md                      # 引用 py_lib.py
    └── 索引引用链
        └── ENTRY.json                              # active_scripts[].path
```

**自检问题**：
1. 移动后，子目录中的 `Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"` 是否需要再加一级 `..`？
2. Python 工具的 `sys.path.insert(0, str(_scripts_dir))` 是否仍指向正确目录？
3. ENTRY.json 中的 `path` 字段是否同步更新？

### 2.2 场景 B：ps-steps/ 或 ps-tools/ 子目录移动/重命名

**涉及文件**：全部 18 个 .ps1 和 1 个 .json

**影响面**：

```
ps-steps/ 移动
    ├── 索引引用链
    │   ├── ENTRY.json                              # step_manifests[].process_script
    │   ├── ENTRY.json                              # step_manifests[].rollback_script
    │   └── task-scenario-triggers.json             # entry_script（场景 01、04）
    ├── 文档引用链
    │   ├── EXEC-CHEATSHEET.md                      # 全部 8 个 Step 的命令示例
    │   ├── README.md                               # 脚本索引表
    │   └── SOP.md                                  # Step 引用（仅脚本名，无路径）
    └── 下游无内部引用（Step 脚本不互相引用）

ps-tools/ 移动
    ├── 索引引用链
    │   ├── ENTRY.json                              # maintenance_scripts[].path
    │   ├── ENTRY.json                              # issue_sync.scripts
    │   └── task-scenario-triggers.json             # entry_script（场景 02、03）
    ├── 文档引用链
    │   ├── EXEC-CHEATSHEET.md                      # 工具命令示例
    │   ├── README.md                               # 脚本索引表
    │   └── docs/playbooks/github-publish-playbook.md # github-create-issue.ps1 路径
    └── 内部引用
        └── github-sync-issue.ps1                   # 同目录读取 github-sync-issue-config.json
            └── （如果 ps-tools/ 改名，ConfigPath 的 Join-Path $PSScriptRoot 自动适配，无需修改）
```

**自检问题**：
1. github-sync-issue.ps1 的 `$ConfigPath = Join-Path $PSScriptRoot 'github-sync-issue-config.json'` 是否仍正确？（是，因为 .json 与 .ps1 同目录移动）
2. EXEC-CHEATSHEET.md 中所有 `& "${devroot}\scripts\ps-steps\..."` 是否同步？
3. task-scenario-triggers.json 中的 `entry_script` 是否指向正确的新路径？

### 2.3 场景 C：py-plugins/ 插件目录移动

**涉及文件**：7 个 Python 插件 + 2 个 py-tools + 1 个 py-examples

**影响面**：

```
py-plugins/ 移动
    ├── Python import 链
    │   ├── py_lib.py                               # _PY_PLUGINS_DIR = _SCRIPTS_DIR / "py-plugins"
    │   ├── py_lib.py                               # sys.path.insert(0, str(_PY_PLUGINS_DIR))
    │   ├── py-tools/check-links.py                 # fallback: _plugins_dir = _scripts_dir / "py-plugins"
    │   └── py-examples/usage-demo.py               # from encoding import EncodingGuard（通过 py_lib 入口，或 fallback 直接 import）
    ├── 配置引用链
    │   └── py-sort-rules.json                      # meta.description 中提到 "py-plugins/ 目录下"
    ├── 文档引用链
    │   ├── docs/PLUGIN-ARCHITECTURE.md             # 引用 py-plugins/ 下文件
    │   └── ENTRY.json                              # active_scripts[].path 中的 py-plugins/ 路径
    └── 插件间引用（内部 import，不受目录移动影响）
        ├── constants.py                            # from detect_devroot import ...
        ├── env_config.py                           # from constants import ...
        ├── link_checker.py                         # （无内部 import，纯函数）
        └── md_lint.py                              # （无内部 import，纯函数）
```

**自检问题**：
1. py_lib.py 中的 `_PY_PLUGINS_DIR` 常量是否同步更新？
2. py-sort-rules.json 的 `meta.description` 是否提到正确的目录名？
3. 如果插件间直接 import（如 `from detect_devroot import ...`），是否依赖 sys.path 包含 py-plugins/？

### 2.4 场景 D：py-tools/ 或 py-examples/ 移动

**涉及文件**：2 个 Python 工具/示例

**影响面**：

```
py-tools/ 移动
    ├── Python import 链
    │   └── check-links.py                          # from py_lib import load_plugins（依赖 sys.path 包含 scripts/）
    ├── 索引引用链
    │   └── ENTRY.json                              # active_scripts[].path
    └── 文档引用链
        └── （当前无文档直接引用 py-tools/ 路径）

py-examples/ 移动
    ├── Python import 链
    │   └── usage-demo.py                           # from py_lib import load_plugins
    ├── 索引引用链
    │   └── ENTRY.json                              # active_scripts[].path
    └── 文档引用链
        └── （当前无文档直接引用 py-examples/ 路径）
```

**自检问题**：
1. 工具/示例内部的 `_scripts_dir = Path(__file__).parent.parent` 是否仍指向正确的 scripts/ 根？（当前结构：py-tools/check-links.py → parent.parent = scripts/，正确）

### 2.5 场景 E：lib-plugins/ 移动

**涉及文件**：3 个 PS 插件

**影响面**：

```
lib-plugins/ 移动
    ├── PS 点源链
    │   └── github-lib.ps1                          # $script:pluginDir = Join-Path $PSScriptRoot "lib-plugins"
    ├── 配置引用链
    │   └── lib-sort-rules.json                     # 插件 file 路径（相对 lib-plugins/）
    ├── 文档引用链
    │   ├── docs/PLUGIN-ARCHITECTURE.md             # 引用 lib-plugins/
    │   └── ENTRY.json                              # active_scripts[].path
    └── 插件间引用（无，各插件独立，由 github-lib.ps1 按 sort-rules 排序后点源）
```

**自检问题**：
1. github-lib.ps1 的 `$script:pluginDir` 是否同步更新？
2. lib-sort-rules.json 中的 `file` 字段（如 `"file": "constants.ps1"`）是相对于 pluginDir 的，pluginDir 变更后是否仍正确？（是，因为 file 是相对 pluginDir 的basename）

## 3. 关键依赖矩阵（快速查表）

### 3.1 按"被引用方"索引

| 被引用文件 | 引用方类型 | 引用方数量 | 关键自检项 |
|-----------|-----------|-----------|-----------|
| `github-lib.ps1` | PS 点源 | 10 个 .ps1 | 子目录中的 `Split-Path -Parent $PSScriptRoot` 是否正确 |
| `github-lib.ps1` | 文档 | 5+ 处 | EXEC-CHEATSHEET、README、patterns、PLUGIN-ARCHITECTURE |
| `github-lib.ps1` | JSON 索引 | 2 处 | ENTRY.json、task-scenario-triggers.json |
| `py_lib.py` | Python import | 2 个 .py | py-tools/、py-examples/ 的 sys.path |
| `py_lib.py` | 文档 | 3+ 处 | PLUGIN-ARCHITECTURE、research |
| `py_lib.py` | JSON 索引 | 1 处 | ENTRY.json |
| `lib-sort-rules.json` | PS 读取 | 1 个 .ps1 | github-lib.ps1 的 `$script:rulesFile` |
| `py-sort-rules.json` | Python 读取 | 1 个 .py | py_lib.py 的 `_RULES_FILE` |
| `github-sync-issue-config.json` | PS 读取 | 1 个 .ps1 | github-sync-issue.ps1 的 `Join-Path $PSScriptRoot`（同目录，自动适配） |
| `github-step-0N-*.ps1` | 文档 | 多处 | EXEC-CHEATSHEET、README、ENTRY.json、task-scenario-triggers |
| `ps-tools/*.ps1` | 文档 | 多处 | EXEC-CHEATSHEET、README、ENTRY.json、task-scenario-triggers、playbooks |

### 3.2 按"引用方"索引

| 引用方 | 被引用文件 | 引用方式 | 变更时影响 |
|--------|-----------|---------|-----------|
| `ps-steps/*.ps1` (8个) | `../github-lib.ps1` | PS 点源 | 点源路径需随 github-lib.ps1 位置调整 |
| `ps-tools/github-safety-check.ps1` | `../github-lib.ps1` | PS 点源 | 同上 |
| `ps-tools/github-sync-issue.ps1` | `../github-lib.ps1` | PS 点源 | 同上；同目录 .json 自动适配 |
| `py-tools/check-links.py` | `../py_lib.py` | Python import | sys.path 需包含 scripts/ 根 |
| `py-examples/usage-demo.py` | `../py_lib.py` | Python import | 同上 |
| `py_lib.py` | `py-plugins/*` | 动态 import | `_PY_PLUGINS_DIR` 需同步 |
| `github-lib.ps1` | `lib-plugins/*` | 动态点源 | `$pluginDir` 需同步 |

## 4. 目录重构后的修订联动 Checklist（通用模板）

当任何 scripts/ 下的目录发生移动/重命名时，按以下清单逐项检查：

### Step 1：脚本内部引用

- [ ] 被移动脚本中的 `$PSScriptRoot` 相对路径引用是否需要调整级数（`..` 的数量）？
- [ ] Python 工具/示例中的 `Path(__file__).parent.parent` 是否仍指向正确的父目录？
- [ ] 同目录配套文件（如 .json 配置）是否一并移动？

### Step 2：聚合入口配置

- [ ] github-lib.ps1 的 `$pluginDir` 是否指向正确的 `lib-plugins/` 位置？
- [ ] py_lib.py 的 `_PY_PLUGINS_DIR` 是否指向正确的 `py-plugins/` 位置？
- [ ] py_lib.py 的 `_RULES_FILE` 是否指向正确的 `py-sort-rules.json` 位置？

### Step 3：索引文件

- [ ] ENTRY.json 中所有涉及变更目录的 `path` 字段是否更新？
- [ ] task-scenario-triggers.json 中的 `entry_script` 是否更新？
- [ ] py-sort-rules.json / lib-sort-rules.json 中的 `meta.description` 是否仍描述正确目录？

### Step 4：速查与文档

- [ ] EXEC-CHEATSHEET.md 中所有命令示例路径是否更新？
- [ ] README.md 脚本索引表中的路径是否更新？
- [ ] docs/playbooks/ 中涉及的操作路径是否更新？
- [ ] docs/patterns/ 中引用的实现文件路径是否更新？

### Step 5：验证

- [ ] 运行 `md_lint.py` 扫描，确保无新增 `---` 污染
- [ ] 运行 `check-links.py` 扫描，确保文档链接无断裂
- [ ] 运行 `py_lib` 自检，确保全部插件可加载
- [ ] 抽样运行 1-2 个被移动的 PS 脚本，确保点源无报错

## 5. 本次重构的实际影响验证

| 检查项 | 验证方式 | 结果 |
|--------|---------|------|
| PS 点源路径修复 | `grep "Join-Path (Split-Path -Parent"` 全部 10 个文件 | ✅ 已修复 |
| Python import 路径 | `py_lib.py` 中 `_SCRIPTS_DIR` 和 `_PY_PLUGINS_DIR` | ✅ 正确 |
| py-tools/ 相对导入 | `check-links.py` 中 `_scripts_dir = Path(__file__).parent.parent` | ✅ 正确 |
| py-examples/ 相对导入 | `usage-demo.py` 中 `_scripts_dir = Path(__file__).parent.parent` | ✅ 正确 |
| ENTRY.json 路径更新 | `grep "ps-steps\|ps-tools"` 在 ENTRY.json 中 | ✅ 20+ 处已更新 |
| task-scenario-triggers.json | `entry_script` 字段 | ✅ 5 处已更新 |
| EXEC-CHEATSHEET.md | 全部命令示例路径 | ✅ 已更新 |
| README.md | 脚本索引表 | ✅ 已更新 |
| docs/playbooks/ | github-publish-playbook.md | ✅ 已更新 |
| JSON lint | `lint-json.py` | ✅ 全部通过 |
| 链接检查 | `check-links.py` | ✅ 16 个链接，0 断裂 |
| 格式检查 | `md_lint.py` | ✅ 20 个文件，0 违规 |
| 插件加载 | `usage-demo.py` | ✅ core + md-validation 全部通过 |

## 6. 设计意图（为什么需要这张依赖图）

本次 scripts/ 子分类重构暴露了之前"摊平结构"下隐藏的问题：文件之间的引用关系是隐式的，分布在 `.ps1` 的 `Join-Path`、`.py` 的 `sys.path.insert`、`.md` 的代码块、`.json` 的 `path` 字段中。当目录结构变化时，这些隐式引用就像地雷，逐一引爆。

依赖图的价值在于：

1. **显式化隐式引用**：把"谁引用了谁"从代码中抽出来，以结构化方式呈现
2. **变更前预判**：在移动目录前，先看这张图，预判影响面
3. **事后核对**：重构完成后，按图逐项打勾，确保无遗漏
4. **新人 onboarding**：新 Agent 不需要逐行读代码，看图即可理解引用关系

## 7. 后续维护建议

1. **将本依赖图纳入交付 checklist**：每次涉及 scripts/ 目录的变更，必须更新本图对应章节
2. **自动化检测**：在 `md_lint.py` 和 `link_checker.py` 之外，增加一个 `path_consistency_checker.py`，扫描 ENTRY.json 中的 path 是否与磁盘实际一致
3. **版本控制**：本文件随目录结构变化同步更新，changelog 中登记 "依赖图已同步"
