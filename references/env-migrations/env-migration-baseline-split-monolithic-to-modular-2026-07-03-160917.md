---
title: task-canonical-baseline.md 拆分重构（monolithic → 模块化多文件）
description: 将 1600+ 行的 task-canonical-baseline.md 拆分为 baseline/ 目录下的 9 个专题文件 + 导航索引，降低维护成本，提升新 Agent 定位效率
date: 2026-07-03
meta:
  version: "1.0.0"
---

# env-migration-baseline-split-monolithic-to-modular-2026-07-03-160917.md

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | task-canonical-baseline.md 拆分重构 |
| **日期** | 2026-07-03 |
| **文件名时间戳** | `2026-07-03-160917` |
| **触发原因** | task-canonical-baseline.md 已达 1600+ 行，单文件过大导致维护困难、新 Agent 定位慢、滚动查找成本高 |
| **影响范围** | `references/tasks/deploy-git-isolated/` 目录结构 + 文档体系 |
| **风险等级** | 低（向后兼容，原文件保留为跳转页） |

## 一、文本文件变更清单

### 1. 新增 `baseline/` 目录

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/` |
| **变更类型** | `新增目录` |
| **作用** | 存放拆分后的 9 个专题 baseline 文件 + 1 个导航索引 |

### 2. 新增 `baseline/baseline-index.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-index.md` |
| **变更类型** | `新增` |
| **修改内容** | 规范基线总入口，含顶层原则速查（8 条铁律）+ 8 文件导航表 + 版本历史 |
| **作用** | 取代原 monolithic baseline 的导航功能，新 Agent 首次阅读时 60 行内定位目标 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 3. 新增 `baseline/baseline-principles.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-principles.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 0.1-0.7 节：禁止现写命令行、Tool-First、Long-Content 落盘、沉淀、持续优化、Workflow 自闭环、显式优于隐性 |
| **作用** | 顶层原则独立成章，Agent 执行前必读 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 4. 新增 `baseline/baseline-semantics.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-semantics.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 1.1-1.3 节：Task/Skill 边界、Workflow vs SKILL.md 本质区别 |
| **作用** | 语义定义集中，不确定边界时查阅 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 5. 新增 `baseline/baseline-structure.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-structure.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 2.1-2.2 + 6.1-6.3 节：目录树、强制/可选文件清单、文件位置约定 |
| **作用** | 新建/移动文件时查阅 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 6. 新增 `baseline/baseline-formats.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-formats.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 3.1-3.5 节：SOP/EXEC-CHEATSHEET/TOOLS-INDEX/ENTRY/DESIGN 格式模板与强制规则 |
| **作用** | 新建/修改文档时查阅 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 7. 新增 `baseline/baseline-operations.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-operations.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 4.x + 5.x + 7.x 节：修订联动矩阵、Agent vs Human 路径、版本演进与归档 |
| **作用** | 执行变更、发布版本时查阅 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 8. 新增 `baseline/baseline-plugin-architecture.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-plugin-architecture.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 8.1-8.5 + 8.8 plugin 节：三层架构图、命名规范、越级禁止、注册双向铁律、标准文档对齐。含本次新增的 8.4.7a 插件注册双向铁律 |
| **作用** | 开发/修改 plugin 或 workflow 时查阅 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 9. 新增 `baseline/baseline-workflow-deploy.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-workflow-deploy.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 8.6 + 8.7 + 8.8 workflow/JS 节：JS 三层对称架构、全链条部署铁律、Git 空目录保留、三侧冲突仲裁 |
| **作用** | 开发 workflow、跨侧工具选型时查阅 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 10. 新增 `baseline/baseline-audit-truth.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-audit-truth.md` |
| **变更类型** | `新增` |
| **修改内容** | 原 8.2 + 8.9 + 8.10 节：Trigger 治理、外部工具引用铁律、独立审计机制、决策真源集中化 |
| **作用** | 设计审计机制、提取真源模块时查阅 |
| **验证方式** | lint 通过 |
| **迁移方式** | 新建 |

### 11. 修改 `task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | `修改` |
| **修改内容** | 1600+ 行正文全部删除，改为 frontmatter + 跳转说明 + 9 文件导航表。保留原路径防止链接断裂 |
| **作用** | 兼容性跳转页，指引人类和 Agent 前往 baseline/ 新位置 |
| **验证方式** | lint 通过 |
| **迁移方式** | 重写为跳转文件 |

### 12. 修改 `README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | `修改` |
| **修改内容** | 顶部 meta 行 `task-canonical-baseline.md` → `baseline/baseline-index.md`；文件导航表 `task-canonical-baseline.md` → `baseline/baseline-index.md` |
| **作用** | 导航链接与新 baseline 位置对齐 |
| **验证方式** | lint 通过 |
| **迁移方式** | edit 最小化修改 |

## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。

## 三、环境变量速查

无新增环境变量。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（11 个文件） | run-lint.py (md_lint + lint-encoding) | BOM、双 BOM、CRLF、frontmatter、正文 --- 污染 | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, frontmatter 合规 |

**执行命令**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\tasks\deploy-git-isolated\baseline\*.md" "${devroot}\references\tasks\deploy-git-isolated\task-canonical-baseline.md" "${devroot}\references\tasks\deploy-git-isolated\README.md"
```

**结果**：✅ 全部通过（33 次扫描，0 违规）

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | baseline 目录存在 | `Test-Path "${devroot}\references\tasks\deploy-git-isolated\baseline"` | `True` |
| 2 | 9 个专题文件齐全 | `Get-ChildItem "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-*.md"` | 9 个文件 |
| 3 | 导航索引可读取 | `read baseline/baseline-index.md` | 返回 60+ 行，含导航表 |
| 4 | 跳转文件有效 | `read task-canonical-baseline.md` | 返回跳转说明，无 1600+ 行正文 |
| 5 | lint 全量通过 | `run-lint.py --files baseline/*.md task-canonical-baseline.md README.md` | 0 违规 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 monolithic baseline | 从 Git 历史检出 `task-canonical-baseline.md` 的 v1.9 版本 |
| 删除 baseline/ 目录 | `Remove-Item -Recurse -Force "${devroot}\references\tasks\deploy-git-isolated\baseline"` |
| 恢复 README.md 链接 | `git checkout -- README.md` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-03-160917 |
| **更新人** | Human + Agent Session |
| **变更触发** | task-canonical-baseline.md 1600+ 行过大，维护困难 |
| **下次修订条件** | 新增 baseline 专题文件、调整文件组织方式 |
| **跨环境迁移参考** | 直接复制 `baseline/` 目录 + 按「验证清单」逐条执行 |
