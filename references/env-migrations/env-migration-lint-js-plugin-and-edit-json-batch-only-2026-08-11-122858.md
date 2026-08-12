---
title: env-migration — lint_js 插件落地 + atomic-config-edit-json batch-only 重构 + 多轮踩坑复盘
description: 完整记录本 session 的三阶段时间线：前置阶段（lint_js 插件体系搭建）→ 死循环阶段（compaction 后反复重置）→ 当前阶段（剩余工作完成 + edit-json 工具重构 + vault 经验沉淀）。
date: 2026-08-11
meta:
  version: 1.0.0
  tags: [lint_js, eslint, atomic-config-edit-json, npm-isolated-install, batch-only, compaction, agent-hallucination]
---

# env-migration — lint_js 插件落地 + atomic-config-edit-json batch-only 重构

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | lint_js 插件体系搭建、atomic-config-edit-json.py 从双模式到 batch-only 重构 |
| **日期** | 2026-08-11 |
| **文件名时间戳** | `2026-08-11-122858` |
| **触发原因** | 前置 session 已完成 lint_js 插件主体开发，本 session 继续完成剩余登记联动 + 功能验证；随后 user 指出 atomic-config-edit-json.py 存在「单条 vs batch」参数歧义，要求彻底根治 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/` 工具链、`venv/eslint/` 隔离环境、`.cursor/rules/high-frequency-json-edit.mdc`、vault 经验沉淀 |
| **风险等级** | 中（涉及核心 atomic 工具接口变更，旧单条命令不再可用） |


## Session 时间线（三阶段）

### Phase 1：前置阶段（compaction 触发前）

本 session 开始前，已有一轮长 session 完成了 lint_js 插件体系的大部分搭建工作。该阶段产物包括：

| # | 操作 | 状态 |
|---|------|------|
| 1 | 修改 `atomic-npm-isolated-install.py`：Local 模式下已存在 `package.json` 时跳过 `npm init -y` | ✅ 已完成 |
| 2 | 修改 `atomic-npm-isolated-install.py`：`_test_bin_executable` 按扩展名 + shebang 路由到正确解释器 | ✅ 已完成 |
| 3 | 删除并重新隔离安装 `venv/eslint/`：`eslint` + `@eslint/js` + `typescript@5.7.3` + `typescript-eslint` | ✅ 已完成 |
| 4 | 创建 `venv/eslint/eslint.config.mjs`（flat config，支持 `.js/.jsx/.mjs/.cjs/.ts/.tsx`） | ✅ 已完成 |
| 5 | 新建 `py-plugins/lint_js.py`（调用 ESLint CLI，`can_fix=False`，只检测不自动修复） | ✅ 已完成 |
| 6 | 更新 `run-lint.py`：EXT_TO_PLUGIN 路由表追加 `.js/.ts/.jsx/.tsx → [lint_js, lint_encoding]` | ✅ 已完成 |
| 7 | 更新 `run-lint.py`：Phase 1/3 明细输出支持 `lint_js` 展示 | ✅ 已完成 |
| 8 | 更新 `py-sort-rules.json` 登记 `lint_js` 插件 | ✅ 已完成 |
| 9 | 更新 `lint_encoding.py`：NO_BOM_EXTENSIONS 追加 `.mjs/.cjs` | ✅ 已完成 |
| 10 | lint 验证全部修改文件 | ✅ 已完成 |

**关键设计决策（前置阶段已确定）**：
- JS/TS 的语义修复不由 `run-lint.py --fix` 自动执行，由编写者（Agent）根据检测报告手动修改
- `FIX_CAPABLE_PLUGINS = {"lint_encoding", "md_lint"}`，不包含 `lint_js`


### Phase 2：死循环阶段（compaction 触发 → user 终止）

**现象**：Phase 1 完成后，Agent 进入 compaction 状态。随后在继续执行剩余工作时陷入**循环重置**——反复尝试相同的操作（如更新 ENTRY.json、verified-task-index.json）而不前进，或者反复验证已完成的步骤。

**user 干预**：
> "你怎么搞的，一直在死循环，浪费token"

user 终止了当前 Agent 实例，强制重启。

**根因分析（事后复盘）**：
- compaction 后 Agent 的 todo 列表状态丢失或混乱，导致「已完成」和「待完成」边界不清
- Agent 在没有明确用户指令的情况下，自行回到之前已完成的步骤重复执行
- 缺乏对「当前真实进度」的外部校验（如直接读取 ENTRY.json 确认 version 是否已更新）


### Phase 3：当前阶段（user 重启后 → 现在）

user 重启后输入：
> "Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed."

Agent 从 Phase 1 的已有状态继续，完成了以下工作：

#### 3.1 完成 lint_js 体系的剩余登记联动

| # | 操作 | 验证 |
|---|------|------|
| 1 | 更新 `ENTRY.json`：version → `0.24.0`，version_history 追加新条目，last_updated 刷新 | ✅ lint 通过 |
| 2 | 更新 `verified-task-index.json`：file-lint-rules 中 JS/TS 的 lint_tool 更新为 `run-lint.py`；追加 `.mjs/.cjs` 条目；last_updated 刷新 | ✅ lint 通过 |
| 3 | 更新 `EXEC-CHEATSHEET.md`：追加 `--profile lint-js` 示例命令 | ✅ lint 通过 |
| 4 | 功能验证：`let y = ;` 正确检测为 Parsing error；`console.log` 不再报 no-undef | ✅ 通过 |
| 5 | 全量 lint：9 个文件，18 扫描项，0 违规 | ✅ 通过 |

#### 3.2 atomic-config-edit-json.py 重构（核心变更）

**触发**：user 观察到 Agent 多次在 batch patch 文件中写错字段名（`operation` vs `op`），要求彻底根治。

**演变过程**：

| 版本 | 改动 | 结果 |
|------|------|------|
| v1.0 | 支持「单条模式（--operation/--json-pointer/--value）」和「batch 模式（--batch）」双路径 | Agent 反复混淆字段名，单条模式 `--value` 的 Shell 转义问题导致 Subagent 宁可写临时 `.py` 绕路 |
| v1.1 | 兼容两套字段名（`op`/`path` 和 `operation`/`json_pointer` 等效） | 治标不治本，Agent 仍需思考 |
| v1.1.1 | 统一 CLI 参数为 `--op`/`--path`，与 batch 字段名一致 | 命名统一了，但单条模式的 Shell 转义陷阱依然存在 |
| **v1.1.2** | **彻底移除单条模式，只保留 `--batch` 唯一路径** | **治本**：Agent 永远只需 `write patch.json → --batch @file`，无判断、无转义、无歧义 |

**具体修改**：
- 移除 `--op`/`--path`/`--value` 参数
- `--batch` 变为 `required`
- 移除 `_smart_parse_value` 函数
- 简化主逻辑：只处理 batch 模式
- docstring 增加「意图演变」章节，记录从双模式到 batch-only 的完整决策链
- 更新 `high-frequency-json-edit.mdc`：删除单条模式分流和示例，统一为 batch-only 标准三步流程
- 更新 `ENTRY.json`：version_history 追加 `0.24.2` 条目

**验证**：
- `atomic-config-edit-json.py` lint 通过（Python + encoding）
- `high-frequency-json-edit.mdc` lint 通过（md_lint + encoding + link_checker）
- `ENTRY.json` lint 通过（lint_json + encoding）

#### 3.3 vault 经验沉淀

在 `vaults/vault-demo/wiki/learnings/` 下新建 4 篇独立文档：

| 文件 | 主题 |
|------|------|
| `eslint-isolated-install-flat-config-guide-2026-08-11-113342.md` | ESLint 隔离安装全过程 + flat config 配置 + 踩坑（TypeScript peer dependency、globals 缺失、.mjs/.cjs 覆盖） |
| `npm-isolated-install-bin-verify-fix-2026-08-11-113342.md` | `atomic-npm-isolated-install.py` 两个 bug 的复盘（npm init 非幂等、bin 验证假设所有 CLI 都是 Python 脚本） |
| `run-lint-js-plugin-integration-2026-08-11-113342.md` | `lint_js` 插件架构决策、run-lint.py 路由更新、「只检测不自动修复」职责边界设计 |
| `atomic-config-edit-json-evolution-batch-only-2026-08-11-113342.md` | 从 v1.0 双模式 → v1.1 命名统一 → v1.1.2 batch-only 的完整决策链与反面教材 |

**导航表同步**：`vaults/vault-demo/wiki/learnings/README.md` 已追加 4 个新条目。

**全部 lint 通过**：12 扫描项，0 违规。


## 一、文本文件变更清单

### 1. 修改 `atomic-npm-isolated-install.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-npm-isolated-install.py` |
| **变更类型** | 修改 |
| **修改内容** | (a) `_ensure_local_structure()` 中 `npm init -y` 移入 `if not package_json.exists()` 块内；(b) `_test_bin_executable()` 按扩展名 + shebang 路由到正确解释器 |
| **作用** | (a) 多次安装时 package.json 不再被重置；(b) `.cmd`/`.ps1`/`.js`/无扩展名 shebang 脚本可被正确验证 |
| **验证方式** | 重新安装 `venv/eslint/` 下的多个 npm 包，验证 package.json 保留已有依赖，且 bin 验证通过 |

### 2. 新建 `venv/eslint/eslint.config.mjs`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/eslint/eslint.config.mjs` |
| **变更类型** | 新建 |
| **作用** | ESLint flat config，覆盖 `.js/.jsx/.mjs/.cjs/.ts/.tsx`，含 Node.js 常用 globals |
| **验证方式** | `eslint --version` + 检测测试文件确认配置生效 |

### 3. 新建 `py-plugins/lint_js.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_js.py` |
| **变更类型** | 新建 |
| **作用** | 调用 `venv/eslint/node_modules/.bin/eslint.cmd` 检测 JS/TS 文件，`can_fix=False` |
| **验证方式** | `run-lint.py --files test.js` 正确检测语法错误 |

### 4. 修改 `run-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | 修改 |
| **修改内容** | EXT_TO_PLUGIN 追加 `.js/.ts/.jsx/.tsx → [lint_js, lint_encoding]`；Phase 1/3 明细输出支持 lint_js |
| **作用** | JS/TS 文件自动路由到 lint_js + lint_encoding |

### 5. 修改 `lint_encoding.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` |
| **变更类型** | 修改 |
| **修改内容** | NO_BOM_EXTENSIONS 追加 `.mjs`、`.cjs` |
| **作用** | `.mjs/.cjs` 文件被纳入编码/BOM/换行符检测 |

### 6. 修改 `py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 修改 |
| **修改内容** | 登记 `lint_js` 插件依赖（depends: ["core"]） |

### 7. 修改 `ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | 修改 |
| **修改内容** | version_history 追加 `0.24.0`（lint_js 插件）和 `0.24.2`（atomic-config-edit-json batch-only）两条目；last_updated 刷新 |

### 8. 修改 `verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 修改 |
| **修改内容** | file-lint-rules 中 JS/TS 的 lint_tool 更新为 `run-lint.py`；追加 `.mjs/.cjs` 条目；last_updated 刷新 |

### 9. 修改 `EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | 修改 |
| **修改内容** | 追加 `--profile lint-js` 示例命令 |

### 10. 修改 `atomic-config-edit-json.py`（核心变更）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py` |
| **变更类型** | 修改（破坏性接口变更） |
| **修改内容** | 彻底移除单条模式（--op/--path/--value），只保留 --batch 唯一路径；--batch 变为 required；移除 `_smart_parse_value`；docstring 增加「意图演变」章节 |
| **作用** | 消除 Agent 在单条 vs batch 间的选择歧义，以及 --value 的 Shell 转义陷阱 |
| **风险** | 旧单条命令不再可用，但 batch 模式完全兼容 |

### 11. 修改 `high-frequency-json-edit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-json-edit.mdc` |
| **变更类型** | 修改 |
| **修改内容** | 删除「单条简单修改」分流和单条命令示例；统一为 batch-only 标准三步流程 |

### 12-15. 新建 vault 经验沉淀（4 篇）

| 路径 | 主题 |
|------|------|
| `vaults/vault-demo/wiki/learnings/eslint-isolated-install-flat-config-guide-2026-08-11-113342.md` | ESLint 隔离安装 + flat config |
| `vaults/vault-demo/wiki/learnings/npm-isolated-install-bin-verify-fix-2026-08-11-113342.md` | npm init 幂等性 + bin 验证路由 |
| `vaults/vault-demo/wiki/learnings/run-lint-js-plugin-integration-2026-08-11-113342.md` | lint_js 插件架构与职责边界 |
| `vaults/vault-demo/wiki/learnings/atomic-config-edit-json-evolution-batch-only-2026-08-11-113342.md` | edit-json 从双模式到 batch-only 的决策链 |


## 二、非文本操作

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 隔离安装 | npm registry | `venv/eslint/node_modules/` | `eslint` + `@eslint/js` + `typescript@5.7.3` + `typescript-eslint` |
| 目录创建 | — | `venv/eslint/` | ESLint 隔离环境根目录 |
| 临时文件（已清理） | — | `venv/tmp/test-*.json` / `venv/tmp/*-patch.json` | 功能验证和 edit-json 验证用的测试文件，已清理 |
| 备份文件 | `ENTRY.json` | `venv/tmp/atomic-config-edit-json-ENTRY-*.bak` | atomic-config-edit-json.py --backup 产生的备份 |


## 三、Agent 系统性失误与纠偏记录

### 失误 1：compaction 后死循环

| 项 | 内容 |
|----|------|
| **现象** | Phase 1 完成后，Agent 反复尝试已完成的操作（如重复更新 ENTRY.json），不前进 |
| **根因** | compaction 后 todo 状态丢失，已完成/待完成边界不清 |
| **纠偏** | user 强制终止 Agent，重启后继续 |
| **教训** | compaction 是高风险节点，重启后应首先读取关键索引文件（ENTRY.json、磁盘文件状态）确认真实进度，而非依赖内存中的 todo 列表 |

### 失误 2：atomic-config-edit-json.py 字段名反复混淆

| 项 | 内容 |
|----|------|
| **现象** | Agent 在 batch patch 文件中反复写错字段名（`operation` vs `op`、`json_pointer` vs `path`） |
| **根因** | 单条模式 CLI 参数（--operation/--json-pointer）与 batch 标准字段（op/path）命名不一致 |
| **第一轮修复** | 代码兼容两套字段名（`_apply_op` 同时识别 `op`/`operation` 和 `path`/`json_pointer`） |
| **user 反馈** | "兼容只是治标，Agent 下次还是要思考" |
| **第二轮修复** | 统一 CLI 参数为 `--op`/`--path`，与 batch 字段名一致 |
| **user 反馈** | "单条模式 Subagent 验证时仍需写临时脚本绕路，--value 的 Shell 转义问题没解决" |
| **最终修复** | 彻底移除单条模式，只保留 `--batch` 唯一路径 |
| **教训** | 兼容两套命名是「掩盖设计缺陷」而非「解决设计缺陷」。当两种路径在本质上有不同风险特征（Shell 转义 vs 文件落盘）时，应该移除高风险路径，而非让调用者做选择 |

### 失误 3：vault 经验沉淀混为一谈

| 项 | 内容 |
|----|------|
| **现象** | Agent 试图将 atomic-config-edit-json 的意图演变追加到 `npm-isolated-install-bin-verify-fix` 文档中 |
| **根因** | 未区分两个完全无关的主题（npm-install bug 修复 vs edit-json 设计演变） |
| **纠偏** | user 指出后，新建独立文档 `atomic-config-edit-json-evolution-batch-only-*.md` |
| **教训** | 经验沉淀必须「一主题一文档」，禁止把无关内容硬塞进已有文档 |


## 四、落盘验证

| 文件类型 | 验证工具 | 结果 |
|---------|---------|------|
| `.md`（env-migration 正文） | `run-lint.py --files <path>` | ✅ md_lint + lint_encoding + link_checker，0 违规 |
| 全部修改文件 | `run-lint.py` 全量扫描 | ✅ 通过 |


## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | ESLint 版本 | `venv/eslint/node_modules/.bin/eslint.cmd --version` | 输出版本号 |
| 2 | lint_js 插件加载 | `run-lint.py --files test.js` | 正确检测 JS 语法错误 |
| 3 | edit-json batch-only | `atomic-config-edit-json.py --file x.json --batch @patch.json --dry-run` | 预览修改结果 |
| 4 | 旧单条命令不可用 | `atomic-config-edit-json.py --file x.json --op replace ...` | argparse 报错（--batch required） |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 edit-json 旧接口 | 从 git 恢复 `atomic-config-edit-json.py` v1.0 版本（如确实需要旧单条模式） |
| 移除 lint_js 插件 | 从 `py-sort-rules.json` 中移除 lint_js 条目；删除 `py-plugins/lint_js.py` |
| 移除 ESLint 隔离环境 | `Remove-Item -Recurse "venv/eslint"` |
| 恢复 ENTRY.json / verified-task-index.json | 从 git 恢复或手动删除 version_history 末尾两条目 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-11-122858 |
| **更新人** | Human + Agent Session |
| **变更触发** | lint_js 插件体系搭建完成后的登记联动；user 指出 atomic-config-edit-json.py 参数歧义要求彻底根治 |
| **下次修订条件** | 新增 lint 插件类型需要更新 run-lint.py 路由表；atomic-config-edit-json.py 接口再次变更 |
| **跨环境迁移参考** | 复制 `venv/eslint/` 目录 + 按「验证清单」逐条执行 |
