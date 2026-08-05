---
title: rg-fd-search SED 自演进目录模式建设与 fd 工具链集成
description: rg-fd-search skill 引入 Self-Evolution Directory（SED）自闭环骨架，含 9 个一级子目录（scripts/ references/ assets/ templates/ examples/ versions/ gotchas/ evolutions/ learnings/），建立 skill 渐进式积累与收敛机制。同步完成 fd 工具链全链路集成与 update-version.py CRLF 根因修复。
date: 2026-08-05
meta: {}
---

# env-migration-rg-fd-search-sed-2026-08-05-172349

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | rg-fd-search SED 自演进目录模式建设 + fd 工具链全链路集成 |
| **日期** | 2026-08-05 |
| **文件名时间戳** | 2026-08-05-172349 |
| **触发原因** | 用户要求为 rg-fd-search skill 加入 self-evolution 机制；此前已完成 fd 工具链集成与 rg-fd-search skill 创建 |
| **影响范围** | skills/rg-fd-search/ 目录结构、SKILL.md 内容、项目级索引（ENTRY.json / TASK-TOOLS-INDEX.md / verified-task-index.json / verified-trigger-index.json）、tool-registration 规则 |
| **风险等级** | 低（纯目录结构与文档变更，无运行时依赖变更） |

## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/scripts/__init__.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/scripts/__init__.py` |
| **变更类型** | 新建 |
| **内容** | 空文件（项目 `__init__.py` 空文件约定） |
| **作用** | scripts/ 包标记 |
| **迁移方式** | 直接复制 |

### 2. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/scripts/helpers/__init__.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/scripts/helpers/__init__.py` |
| **变更类型** | 新建 |
| **内容** | 空文件 |
| **作用** | helpers/ 子包标记 |
| **迁移方式** | 直接复制 |

### 3. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |
| **变更类型** | 新建 |
| **内容** | SED 演进时间线 + 指纹索引 + 收敛记录 JSON Schema |
| **作用** | skill 自演进真源索引 |
| **迁移方式** | 直接复制 |

### 4. 修改 `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md` |
| **变更类型** | 追加 |
| **新增内容** | Skill 加载机制（SED 模式）、目录结构树状图、三类增量 frontmatter 规范（gotchas/evolutions/learnings）、去重与入库策略、Skill Self-Evolution 复盘自检块 |
| **插入位置** | 文件末尾（关联文档之后） |
| **作用** | 定义 skill 自闭环加载机制与演进规则 |
| **迁移方式** | 直接追加 |

### 5. 修改 `references/tasks/deploy-git-isolated/skills/rg-fd-search/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/README.md` |
| **变更类型** | 修改 |
| **新增内容** | SED 九个子目录导航表（scripts/ references/ assets/ templates/ examples/ versions/ gotchas/ evolutions/ learnings/） |
| **插入位置** | 子目录 / 文件导航节 |
| **作用** | 人类可读速查 |
| **迁移方式** | 直接覆盖导航表 |

### 6. 修改 `references/tasks/deploy-git-isolated/ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | 追加 + 修改 |
| **新增内容** | version_history 追加 v0.25.0；meta.last_updated 刷新；skills/1/role 更新为含 SED 说明 |
| **作用** | Task 级版本真源 |
| **迁移方式** | atomic-config-edit-json.py --batch |

### 7. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **新增内容** | rg-fd-search 描述追加 SED 说明；速查表版本 v1.4 → v1.5 |
| **作用** | 人类可读速查索引 |
| **迁移方式** | edit |

### 8. 修改 `references/runtime/verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | 修改 |
| **新增内容** | rg-fd-search description 更新为含 SED 说明；verified_at + meta.last_updated 刷新 |
| **作用** | 全项目 Agent 工具查询真源 |
| **迁移方式** | atomic-config-edit-json.py --batch |

### 9. 修改 `references/runtime/verified-trigger-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-trigger-index.json` |
| **变更类型** | 追加 |
| **新增内容** | rg-fd-search 冲突域（rg-fd-search）+ 7 个触发条目（T001~T004/E001~E002/mdc-T001）+ CR-008 冲突裁决规则 + source_prefix_registry 登记 |
| **作用** | 全项目触发条件统一真源 |
| **迁移方式** | atomic-config-edit-json.py --batch |

### 10. 修改 `.cursor/rules/tool-registration-revision-linkage.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/tool-registration-revision-linkage.mdc` |
| **变更类型** | 修改 |
| **新增内容** | 四件套 → 五件套（追加 verified-trigger-index.json）；执行流程插入 Step 6（trigger-index 登记）；禁止行为追加 #7/#8；自检清单追加 trigger-index 检查项 |
| **作用** | 工具登记修订联动义务规则升级 |
| **迁移方式** | edit |

### 11. 修改 `.cursor/rules/rg-fd-search-priority.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/rg-fd-search-priority.mdc` |
| **变更类型** | 追加 |
| **新增内容** | 正文开头追加 trigger-index 引用说明块 |
| **作用** | 来源文件引用索引规范 |
| **迁移方式** | edit |

### 12. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py` |
| **变更类型** | 修改 |
| **新增内容** | 两处 `pathlib.Path.write_text()` 追加 `newline="\n"` |
| **作用** | 修复 Windows 下默认产出 CRLF 的根因 |
| **迁移方式** | edit |

### 13. 新建 `.cursor/rules/rg-fd-search-priority.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/rg-fd-search-priority.mdc` |
| **变更类型** | 新建 |
| **内容** | rg/fd 搜索优先级铁律（alwaysApply 规则） |
| **作用** | 默认禁止原生 grep/glob，强制 rg/fd |
| **迁移方式** | 直接复制 |

### 14. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md` |
| **变更类型** | 新建（本轮追加 SED 内容前已存在） |
| **内容** | rg-fd-search 通用搜索能力 skill |
| **作用** | Skill 主文档 |
| **迁移方式** | 直接复制 |

## 二、非文本操作（文件系统/目录创建）

本次 session 涉及以下目录创建（无法被 git 追踪）：

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 目录创建 | — | `skills/rg-fd-search/scripts/` | skill 专属可执行脚本根目录 |
| 目录创建 | — | `skills/rg-fd-search/scripts/helpers/` | 辅助脚本子目录 |
| 目录创建 | — | `skills/rg-fd-search/references/` | 外部资料、本地索引 |
| 目录创建 | — | `skills/rg-fd-search/assets/` | 静态资源（截图、数据文件） |
| 目录创建 | — | `skills/rg-fd-search/templates/` | 可复用模板 |
| 目录创建 | — | `skills/rg-fd-search/examples/` | 使用示例、测试用例 |
| 目录创建 | — | `skills/rg-fd-search/versions/` | 演进时间线 |
| 目录创建 | — | `skills/rg-fd-search/versions/archive/` | 已收敛 evolutions 归档 |
| 目录创建 | — | `skills/rg-fd-search/gotchas/` | 踩坑记录 |
| 目录创建 | — | `skills/rg-fd-search/evolutions/` | 规则/行为演进补丁 |
| 目录创建 | — | `skills/rg-fd-search/learnings/` | 认知/洞察/基线 |
| 文件创建 | — | `skills/rg-fd-search/scripts/__init__.py` | 空文件（包标记） |
| 文件创建 | — | `skills/rg-fd-search/scripts/helpers/__init__.py` | 空文件（包标记） |
| 文件创建 | — | `skills/rg-fd-search/versions/manifest.json` | 初始演进时间线 |

## 三、Session 踩坑与纠偏记录

### 踩坑 1：update-version.py CRLF 根因

- **现象**：`venv/version/*.md` 文件在 Windows 上被写出 CRLF，导致 lint 报 `CRLF>0`
- **根因**：`pathlib.Path.write_text(newline=None)` 在 Windows 上默认将 `\n` 转为 `\r\n`
- **修复**：两处 `write_text()` 追加 `newline="\n"` 参数
- **产物**：`references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py`

### 踩坑 2：verified-trigger-index.json 追加 patch 时 `merge` 操作不支持 `None`

- **现象**：atomic-config-edit-json.py 报错 `不支持的参数类型: None`
- **根因**：patch JSON 中 `value` 为 `null`（Python None），而 `merge` 操作只接受 dict
- **修复**：调整 patch 结构，避免 `null` value 出现在 merge 操作中
- **产物**：`venv/tmp/rg-fd-search-trigger-patch.json`

### 踩坑 3：rg-fd-search skill 的 scripts/ 登记边界

- **现象**：讨论 skill 自闭环时，用户指出我遗漏了 `scripts/`、`references/` 等标准子目录
- **根因**：SED 设计只关注增量记录（gotchas/evolutions/learnings），忽略了 skill 作为自闭环单元必须具备的标准子目录骨架
- **修复**：补全 9 个一级子目录，并明确 `scripts/` 与 `py-plugins/` 同等待遇（不对外登记）
- **产物**：`skills/rg-fd-search/` 完整目录骨架

### 踩坑 4：Agent 在 SED 设计初期遗漏「认知面」分类

- **现象**：evolutions/ 只覆盖「行为面」，遗漏了「洞察/模式/基线/结论」等认知增量
- **根因**：将 env-migration 狭义理解为「改环境变量、迁缓存」，未充分说明 learnings/ 的覆盖范围
- **修复**：补全 learnings/ 目录及五个 category（insight/pattern/baseline/conclusion/heuristic）
- **产物**：`skills/rg-fd-search/learnings/` + SKILL.md 中 frontmatter 规范

## 四、产物路径全量清单

| 路径 | 类型 | 说明 |
|------|------|------|
| `.cursor/rules/rg-fd-search-priority.mdc` | 新建 | alwaysApply 执法规则 |
| `.cursor/rules/tool-registration-revision-linkage.mdc` | 修改 | 五件套升级（追加 trigger-index） |
| `references/runtime/verified-trigger-index.json` | 修改 | rg-fd-search 触发条件登记 |
| `references/runtime/verified-task-index.json` | 修改 | rg-fd-search 描述更新为含 SED |
| `references/tasks/deploy-git-isolated/ENTRY.json` | 修改 | v0.25.0 追加 |
| `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` | 修改 | v1.5 更新 |
| `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py` | 修改 | CRLF 根因修复 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/SKILL.md` | 修改 | SED 加载机制 + frontmatter + 复盘自检 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/README.md` | 修改 | SED 目录导航表 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/scripts/__init__.py` | 新建 | 空文件 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/scripts/helpers/__init__.py` | 新建 | 空文件 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` | 新建 | 初始演进时间线 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/references/.gitkeep` | 新建 | 空目录占位 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/assets/.gitkeep` | 新建 | 空目录占位 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/templates/.gitkeep` | 新建 | 空目录占位 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/examples/.gitkeep` | 新建 | 空目录占位 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/archive/.gitkeep` | 新建 | 空目录占位 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/.gitkeep` | 新建 | 空目录占位 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/.gitkeep` | 新建 | 空目录占位 |
| `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/.gitkeep` | 新建 | 空目录占位 |

## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认目录结构完整 | `Get-ChildItem "references/tasks/deploy-git-isolated/skills/rg-fd-search/"` | 显示 9 个一级子目录 + SKILL.md + README.md |
| 2 | 确认 manifest.json 存在 | `Test-Path "references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json"` | True |
| 3 | 确认 lint 通过 | `run-lint.py --files rg-fd-search/SKILL.md rg-fd-search/README.md ...` | 全部通过 |
| 4 | 确认索引已登记 | 读取 ENTRY.json / verified-task-index.json / verified-trigger-index.json | rg-fd-search 条目存在且字段正确 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 SED 子目录 | `Remove-Item -Recurse "skills/rg-fd-search/scripts"`, `references/`, `assets/`, `templates/`, `examples/`, `versions/`, `gotchas/`, `evolutions/`, `learnings/` |
| 恢复 SKILL.md | 从 git 恢复 `skills/rg-fd-search/SKILL.md` 到 SED 追加前版本 |
| 恢复 README.md | 从 git 恢复 `skills/rg-fd-search/README.md` 到 SED 追加前版本 |
| 恢复索引 | 从备份恢复 ENTRY.json / verified-task-index.json / verified-trigger-index.json |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-05-172349 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求为 rg-fd-search skill 加入 self-evolution 机制 |
| **下次修订条件** | rg-fd-search skill 执行后触发 Self-Evolution 复盘，产生新 gotcha/evolution/learning 时 |
| **跨环境迁移参考** | 直接复制 `skills/rg-fd-search/` 完整目录 + 按「验证清单」逐条执行 |

*文档生成时间：2026-08-05*  
*模板版本：env-migration-template.md v2*
