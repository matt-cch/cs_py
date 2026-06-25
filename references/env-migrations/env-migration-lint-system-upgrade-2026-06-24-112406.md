---
title: env-migration — lint 体系升级与规则清单引入
description: link_checker/py-sort-rules/py_lib/run-lint 版本升级、新增 lint-rules-manifest.json、AGENTS.md 思考语言锚定、入口文件修订联动
date: 2026-06-24
meta: {}
---

# lint 体系升级与规则清单引入

> **文档性质**：环境迁移指南。记录本次 session 对 `deploy-git-isolated` task 的 lint 插件体系和入口文档的变更。
> **受众**：Human + Agent。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | lint 体系升级：版本管理、覆盖度审计、规则全局清单 |
| **日期** | 2026-06-24 |
| **文件名时间戳** | `2026-06-24-112406` |
| **触发原因** | lint 路由修复 + lint 规则清单缺失 + 版本管理缺失 |
| **影响范围** | `deploy-git-isolated/task/` 下的插件代码、入口文件、schema 目录 |
| **风险等级** | 低（不影响业务代码，仅影响 lint 工具链自身） |

## 一、文本文件变更清单

### 1. 修改 `py-plugins/link_checker.py` — v1.2.0 → v1.3.0

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/link_checker.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增 `validate_file()` 方法支持单文件路由；`validate()` 新增 `dir_path` 参数兼容统一调用接口 |
| **作用** | 对齐 Plugin Result Schema 统一契约，支持 `run-lint.py --files` 单文件模式 |
| **验证方式** | 执行 `run-lint.py --files <任意 .md 文件>`，应正常调用 link_checker |

### 2. 修改 `py-sort-rules.json` — v1.0.0 → v1.1.0

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 修改 |
| **修改内容** | `lint` profile 的 `include_tags` 从 `["lint"]` 改为 `["lint", "md"]`，使 `--profile lint` 目录扫描模式也加载 `md_lint` 和 `link_checker` |
| **作用** | 修复 `--profile lint` 模式不包含 Markdown 验证插件的路由缺失 |
| **验证方式** | `run-lint.py --profile lint` 应包含 `md_lint` 和 `link_checker` 插件 |

### 3. 修改 `py_lib.py` — v1.1.0 → v1.2.0

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py_lib.py` |
| **变更类型** | 修改 |
| **新增内容** | 模块级 `__version__ = "1.2.0"`；`get_rules_version()` 函数返回 py-sort-rules.json 版本；`PluginRegistry.rules_version` 属性暴露运行时规则版本 |
| **作用** | 实现版本管理：代码可查询 py_lib 自身版本及其依赖的规则配置版本 |
| **验证方式** | `from py_lib import __version__, get_rules_version; print(__version__, get_rules_version())` |

### 4. 修改 `py-tools/run-lint.py` — v1.2.0 → v1.3.0

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | 修改 |
| **新增内容** | `--audit` 参数：读取 `schema/json/lint-rules-manifest.json` → 加载全部 lint 插件 → 交叉校验规则覆盖度 |
| **作用** | 提供 audit 模式，确保 lint 规则无遗漏 |
| **验证方式** | `run-lint.py --devroot <path> --audit`，输出应显示 7 个插件 27 条规则全匹配 |

### 5. 新增 `schema/json/lint-rules-manifest.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/json/lint-rules-manifest.json` |
| **变更类型** | 新建 |
| **内容** | 7 个 lint/validation 插件的 27 条规则全局清单，含规则 ID、严重等级、可修复性、文件类型路由、profiles 定义、fix capabilities |
| **作用** | audit 巡检对照的单一真源。新增/修改规则时必须同步更新此文件 |
| **验证方式** | `run-lint.py --files <该文件>` 应通过 JSON lint；`run-lint.py --audit` 应交叉校验通过 |

### 6. 新增 `schema/docs/lint-rules-manifest.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/docs/lint-rules-manifest.md` |
| **变更类型** | 新建 |
| **内容** | 清单结构说明、规则 ID 命名约定（7 个前缀）、联动义务 |
| **作用** | 人类可读的 manifest 说明文档 |
| **验证方式** | `run-lint.py --files <该文件>` 应通过 md_lint 和 link_checker |

### 7. 修改 `venv/.opencode/AGENTS.md` — 新增思考语言锚定机制

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | 修改 |
| **新增内容** | 「默认语言 > 思考语言锚定机制」小节：① 每轮回复第一句必须是中文 ② 发现英文思考时立即中断重置 ③ 例外仅限纯技术标识符 |
| **作用** | 防止 Agent 在连续多轮 tool call 后不自觉切回英文思考 |
| **验证方式** | 后续对话第一句应始终为中文；回复中不应出现英文思考段落 |

### 8–11. 修订联动 4 份入口文件

| 文件 | 修改内容 |
|------|---------|
| `ENTRY.json` | 追加 v0.18.0 版本历史；run-lint.py role 补充 --audit 和 manifest；py_lib.py role 补充版本管理 API |
| `TASK-TOOLS-INDEX.md` | 新增 --audit 命令速查；py_lib 依赖节补充版本管理 API；关联导航加入 manifest |
| `EXEC-CHEATSHEET.md` | Stage S6 新增覆盖度审计子节（命令 + 输出示例） |
| `README.md` | run-lint.py 描述补充 --audit；文件导航新增 manifest 和 py_lib 版本能力 |

## 二、非文本操作

无。

## 三、环境变量速查

无变更。

## 四、落盘验证

所有修改文件已通过 `run-lint.py` 全量 lint，0 违规。

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 期望结果 |
|---|---------|---------|
| 1 | `run-lint.py --audit` | 7 插件 27 规则全匹配，0 缺失 |
| 2 | `run-lint.py --files schema/json/lint-rules-manifest.json` | JSON 语法通过 |
| 3 | `run-lint.py --files schema/docs/lint-rules-manifest.md` | md_lint + link_checker 通过 |
| 4 | `python -c "from py_lib import __version__, get_rules_version; print(__version__, get_rules_version())"` | 输出 `1.2.0 1.1.0` |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 回退 `link_checker.py` | `git checkout HEAD~1 -- scripts/py-plugins/link_checker.py` |
| 回退 `py-sort-rules.json` | `git checkout HEAD~1 -- scripts/py-sort-rules.json` |
| 回退 `py_lib.py` | `git checkout HEAD~1 -- scripts/py_lib.py` |
| 回退 `run-lint.py` | `git checkout HEAD~1 -- scripts/py-tools/run-lint.py` |
| 删除 manifest | `Remove-Item schema/json/lint-rules-manifest.json schema/docs/lint-rules-manifest.md` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-24-112406 |
| **更新人** | Human + Agent Session |
| **变更触发** | lint 体系全面升级：修复路由 + 增加版本管理 + 引入规则清单 + 入口联动 |
| **下次修订条件** | 新增 lint 规则/插件时同步更新 `lint-rules-manifest.json` |
