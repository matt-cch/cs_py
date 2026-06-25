---
title: deploy-git-isolated Python 生态增强 — Issue 查看、Schema 契约、md_lint 对齐与架构规范沉淀
description: 记录本次 session 对 deploy-git-isolated task 的 Python 侧插件体系、lint 规则、架构规范所做的多项增强与修正。
date: 2026-06-20
meta:
  version: 1.0
---

# deploy-git-isolated Python 生态增强

> **Session 主题**：查看 GitHub Issue #1 评论 → 集成 Python 版 GitHub API → 统一 Plugin Result Schema → 增强 md_lint 对齐 mdc 标准 → 修正插件暴露问题 → 沉淀架构规范
> **日期**：2026-06-20
> **文件名时间戳**：2026-06-20-102656
> **触发原因**：用户要求查看 deploy-git-isolated task 的 GitHub Issue #1 最新评论，并将有复用价值的产物集成到 py-tools/
> **影响范围**：deploy-git-isolated task 的 Python 插件体系、lint 规则、.cursor/rules/*.mdc、task-canonical-baseline.md
> **风险等级**：低（纯代码/文档增强，无环境配置变更）


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/github_api.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/github_api.py` |
| **变更类型** | `新建` |
| **作用** | Python 插件：GitHub REST API 封装（get_credentials / invoke_api / get_issue / list_comments / create_issue / update_issue / create_comment），urllib 实现，自动 UTF-8 |
| **验证方式** | 通过 fetch_issue.py 调用，获取 Issue #1 完整内容（含 6 条评论），与 PS 版输出一致 |
| **迁移方式** | 新环境直接复制文件即可，无需额外配置 |

### 2. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/fetch_issue.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/fetch_issue.py` |
| **变更类型** | `新建` |
| **作用** | Python CLI：获取 GitHub Issue 完整内容（含评论），通过 py_lib 加载 github_api 插件，输出与 PS 版对齐 |
| **验证方式** | `python fetch_issue.py --owner ... --repo ... --issue 1` 输出完整 Issue |
| **迁移方式** | 新环境直接复制文件即可 |

### 3. 新建 `references/tasks/deploy-git-isolated/schema/json/plugin-result-schema.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/json/plugin-result-schema.json` |
| **变更类型** | `新建` |
| **作用** | Plugin Result Schema 机器真源（v1.0.0），定义插件返回格式的 JSON Schema |
| **验证方式** | 5 个 lint 插件返回结构经 run-lint 验证符合此 schema |
| **迁移方式** | 直接复制 |

### 4. 新建 `references/tasks/deploy-git-isolated/schema/docs/plugin-result-schema.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/docs/plugin-result-schema.md` |
| **变更类型** | `新建` |
| **作用** | Plugin Result Schema 人类可读规范文档，含默认 Dict + Pydantic 备选实现说明 |
| **迁移方式** | 直接复制 |

### 5. 新建 `references/tasks/deploy-git-isolated/schema/py/models.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/py/models.py` |
| **变更类型** | `新建` |
| **作用** | Pydantic / Dataclass 备选 Model 实现，与 plugin-result-schema.json 共享同一契约 |
| **迁移方式** | 直接复制 |

### 6. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| **变更类型** | `修改`（v1.1.1 → v1.2.0） |
| **新增/修改内容** | 1. docstring 与 mdc 逐条对齐（实现状态矩阵）<br>2. 新增 frontmatter 必须从第 1 行开始检测<br>3. 新增代码块内 `---` 例外（通过 ` ``` ` 配对追踪）<br>4. 保留 SKILL.md / AGENTS.md 例外文件机制 |
| **验证方式** | run-lint 语法通过；4 场景功能测试全部通过（正常/不在开头/代码块内/正文污染） |
| **迁移方式** | 直接覆盖 |

### 7. 修改 `.cursor/rules/markdown-docs-format.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/markdown-docs-format.mdc` |
| **变更类型** | `修改` |
| **新增/修改内容** | 1. frontmatter 示例新增 `meta: version: 1.0.0`<br>2. 新增 `meta` 必填字段说明<br>3. 新增 description 与 date 禁止拼接同一行<br>4. 新增 1.5 frontmatter 机器可读校验章节（引用 md_lint.py） |
| **验证方式** | md_lint 扫描通过（0 违规） |
| **迁移方式** | 直接覆盖 |

### 8. 修改 `references/tasks/deploy-git-isolated/scripts/py_lib.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py_lib.py` |
| **变更类型** | `修改`（v1.0.0 → v1.1.0） |
| **新增/修改内容** | 新增 `list_plugins(tags=None)` API：从 `py-sort-rules.json` 动态读取插件元数据，不加载、只返回元数据 |
| **验证方式** | `python py_lib.py` 自检输出全部 16 个插件清单 |
| **迁移方式** | 直接覆盖 |

### 9. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | 删除静态插件层表格（6 行插件明细），改为能力概览 + `list_plugins()` 用法示例 + 铁律说明；meta version 1.0 → 1.1 |
| **验证方式** | md_lint 扫描通过（0 违规） |
| **迁移方式** | 直接覆盖 |

### 10. 修改 `references/tasks/deploy-git-isolated/task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | 1. 新增 8.4.5：文档层面也不暴露插件文件名<br>2. 新增 8.5：标准文档与实现代码的真源对齐原则（标准文档是唯一真源，实现代码是忠实实现） |
| **验证方式** | md_lint 扫描通过（0 违规） |
| **迁移方式** | 直接覆盖 |

### 11. 修改 `references/tasks/deploy-git-isolated/ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | `修改`（v0.10.0 → v0.15.0） |
| **新增/修改内容** | 追加 version_history 条目（0.11.0 / 0.12.0 / 0.13.0 / 0.14.0 / 0.15.0），记录本轮全部变更 |
| **验证方式** | lint_json 验证通过 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等非文本操作。


## 三、环境变量速查

本次 session 未新增或修改环境变量。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 结果 |
|---------|---------|---------|------|
| `.md`（env-migration 正文） | `md_lint.py` | frontmatter、--- 污染 | ✅ 通过 |
| `.py` | `lint_python.py` | py_compile 语法 | ✅ 通过 |
| `.json` | `lint_json.py` | JSON 语法 | ✅ 通过 |


## 五、验证清单（新环境建议执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | py_lib list_plugins 正常工作 | `python scripts/py_lib.py` | 输出 16 个插件清单 |
| 2 | md_lint frontmatter 检测正常 | `python scripts/py-plugins/md_lint.py --dir <test_dir>` | 能检测出 frontmatter 缺失/位置错误/--- 污染 |
| 3 | fetch_issue 可获取 Issue | `python scripts/py-tools/fetch_issue.py --owner <o> --repo <r> --issue 1` | 输出 Issue 标题 + 评论列表 |
| 4 | run-lint 全量通过 | `python scripts/py-tools/run-lint.py --devroot <devroot> --profile lint` | 0 违规 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除新增文件 | 删除 `py-plugins/github_api.py`、`py-tools/fetch_issue.py`、`schema/json/plugin-result-schema.json`、`schema/docs/plugin-result-schema.md`、`schema/py/models.py` |
| 恢复旧版本 | 从 git 历史恢复 `md_lint.py` v1.1.1、`py_lib.py` v1.0.0、`TASK-TOOLS-INDEX.md`、`task-canonical-baseline.md` |
| 恢复 mdc | 从 git 历史恢复 `.cursor/rules/markdown-docs-format.mdc` 旧版本 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-20-102656 |
| **更新人** | Human + Agent Session |
| **变更触发** | 查看 GitHub Issue #1 评论并集成复用产物 |
| **下次修订条件** | 新增 lint 插件、修改 frontmatter 规则、调整插件架构 |
| **跨环境迁移参考** | 直接复制本文档列出的文件 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-20*  
*模板版本：v2*
