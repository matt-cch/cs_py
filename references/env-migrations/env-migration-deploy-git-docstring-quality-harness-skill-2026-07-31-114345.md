---
title: deploy-git-isolated 新增 docstring-quality-harness skill 与 docstring 修正
description: 在 deploy-git-isolated 任务下新建 docstring-quality-harness skill，检验工具 docstring 自说明质量，渐进式积累 baseline。同时修正 workflow-git-deploy-full-poly.py 的 docstring 歧义。
date: 2026-07-31
meta:
  version: 0.1.0
---

# deploy-git-isolated 新增 docstring-quality-harness skill 与 docstring 修正

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 新建 docstring-quality-harness skill，检验工具文档自说明质量并渐进式积累 baseline |
| **日期** | 2026-07-31 |
| **文件名时间戳** | `2026-07-31-114345` |
| **触发原因** | 实测发现 workflow-git-deploy-full-poly.py 的 docstring 中 --target 参数标记与代码 required=True 矛盾，导致 Agent 误判 |
| **影响范围** | deploy-git-isolated 任务目录（新增 skills/ 子目录）、verified-trigger-index.json、verified-task-index.json、ENTRY.json、README.md |
| **风险等级** | 低（纯文档/规范建设，无业务代码变更） |

## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/SKILL.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/SKILL.md` |
| **变更类型** | `新建` |
| **作用** | 定义 docstring 质量测试 Harness 的核心规范：触发词、测试流程、目录结构、与现有体系衔接 |
| **迁移方式** | 直接复制（新建文件） |

### 2. 新建 `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/README.md` |
| **变更类型** | `新建` |
| **作用** | 目录结构与导航说明，列出 schema/、baseline/、examples/ 各子目录职责 |
| **迁移方式** | 直接复制（新建文件） |

### 3. 新建 `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/schema/audit-manifest-schema.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/schema/audit-manifest-schema.json` |
| **变更类型** | `新建` |
| **作用** | Audit Manifest 的 JSON Schema 定义，约束单次测试的输出格式 |
| **迁移方式** | 直接复制（新建文件） |

### 4. 新建 `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/baseline/docstring-quality-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/baseline/docstring-quality-baseline.md` |
| **变更类型** | `新建` |
| **作用** | 渐进式质量基准，记录 5 个评价维度、评分标准、已知问题、迭代历史 |
| **迁移方式** | 直接复制（新建文件），后续每次测试追加 |

### 5. 新建 `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/examples/example-audit-manifest.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/examples/example-audit-manifest.json` |
| **变更类型** | `新建` |
| **作用** | 基于 workflow-git-deploy-full-poly.py 实测的 Audit Manifest 示例 |
| **迁移方式** | 直接复制（新建文件） |

### 6. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 参数表第 71 行：`--target` 必填标记从 `❌` 改为 `✅`，默认值从 `--devroot` 改为 `无`；调用示例第 80 行补全 `--target "${devroot}"` |
| **作用** | 消除 docstring 与代码 `required=True` 的矛盾，使陌生 Agent 能准确判断 --target 为必填 |
| **验证方式** | 委派 subagent 零上下文测试，成功构建正确命令行 |
| **迁移方式** | `edit` 最小化修改 |

### 7. 修改 `references/runtime/verified-trigger-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-trigger-index.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 `skill-docstring-quality` source_prefix、trigger_source、3 个 trigger 条目（T001-T003）、`docstring-quality` 冲突域 |
| **作用** | 将 skill 触发词纳入全项目统一索引治理 |
| **迁移方式** | `atomic-config-edit-json.py --batch` |

### 8. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | `available_scripts_and_tools` 新增 `docstring-quality-harness` 条目 |
| **作用** | 供 Agent tool 调用前审计时查询现成工具 |
| **迁移方式** | `atomic-config-edit-json.py --batch` |

### 9. 修改 `references/tasks/deploy-git-isolated/ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 `skills` 数组（含 docstring-quality-harness），版本号 0.22.0 → 0.23.0，追加 version_history 条目 |
| **作用** | 机器真源索引同步目录结构变化 |
| **迁移方式** | `atomic-config-edit-json.py --batch` |

### 10. 修改 `references/tasks/deploy-git-isolated/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | 目录结构概览中新增 `skills/` 说明 |
| **作用** | 目录自说明与导航联动 |
| **迁移方式** | `edit` 最小化修改 |

### 11. 修改 `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/baseline/docstring-quality-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/docstring-quality-harness/baseline/docstring-quality-baseline.md` |
| **变更类型** | `修改` |
| **新增/修改内容** | 迭代历史追加 v0.1.0-regression 回归验证记录 |
| **作用** | 记录修正后的 docstring 通过回归测试 |
| **迁移方式** | `edit` 追加行 |

## 二、非文本操作

无。本次 session 不涉及文件复制、缓存迁移、目录创建等操作。

## 三、环境变量速查

无新增环境变量。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 结果 |
|---------|---------|---------|------|
| `.md` | `run-lint.py` | frontmatter + encoding + link | ✅ 全部通过 |
| `.json` | `run-lint.py` | JSON 语法 + encoding | ✅ 全部通过 |
| `.py` | `run-lint.py` | Python 语法 + encoding | ✅ 全部通过 |

验证命令：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "..."
```

## 五、验证清单（新环境复现）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 skill 目录存在 | `Test-Path "${devroot}\references\tasks\deploy-git-isolated\skills\docstring-quality-harness\SKILL.md"` | `True` |
| 2 | 确认索引已登记 | `Get-Content "${devroot}\references\runtime\verified-trigger-index.json" | Select-String "skill-docstring-quality"` | 命中 |
| 3 | 确认 ENTRY.json 已更新 | `Get-Content "${devroot}\references\tasks\deploy-git-isolated\ENTRY.json" | Select-String "docstring-quality-harness"` | 命中 |
| 4 | 确认 docstring 修正有效 | 委派 subagent 测试 workflow-git-deploy-full-poly.py | 构建的命令行包含 `--target` |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 skill 目录 | `Remove-Item -Recurse "${devroot}\references\tasks\deploy-git-isolated\skills\docstring-quality-harness"` |
| 还原 poly.py docstring | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py"` |
| 还原索引 | 从备份 `.bak` 恢复 verified-trigger-index.json、verified-task-index.json、ENTRY.json |
| 还原 README.md | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\README.md"` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-31-114345 |
| **更新人** | Human + Agent Session |
| **变更触发** | 测试 docstring 自说明质量时发现参数表歧义 |
| **下次修订条件** | 对新的工具执行 docstring-quality-harness 测试并发现新问题时 |
| **跨环境迁移参考** | 直接复制 skills/ 目录 + 按「验证清单」逐条执行 |
