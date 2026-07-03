---
title: env-migration 哨兵验证规则体系建设与测试实例退役
description: 记录哨兵验证 Playbook、规则模板创建及 sentinel-test 测试文件的人名修正与后续退役计划。
date: 2026-06-06
---

# `env-migration-sentinel-verification-rulesystem-2026-06-06-110325.md`

## 元信息

| 字段 | 填写内容 |
|------|---------|
| **Session 主题** | 哨兵验证规则体系建设（Playbook + 模板）与 sentinel-test-2026-0606 测试实例退役准备 |
| **日期** | 2026-06-06（frontmatter；文件名时间戳 `2026-06-06-110325`） |
| **文件名时间戳** | `2026-06-06-110325` |
| **触发原因** | 用户要求将当前 session 的哨兵验证机制固化为可复现文档；sentinel-test 人名修正为 ted/tina 后准备删除 |
| **影响范围** | `schema/structure/`、`docs/tooling/opencode/`、`.cursor/rules/` |
| **风险等级** | 极低（纯文档新增，无业务代码或环境配置变更） |


## 一、文本文件变更清单

### 1. 新建 `schema/structure/sentinel-rule-template.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/sentinel-rule-template.md` |
| **变更类型** | 新建 |
| **作用** | 供 `.cursor/rules/` 下创建哨兵规则文件时复用的复制模板 |
| **内容要点** | 哨兵值选取三要素（生僻性、唯一性、可验证性）；模板骨架（含 frontmatter、哨兵标识、触发方式、验证方法、异常处理、第2份哨兵值）；Agent 自检清单 |
| **验证方式** | `Test-Path -LiteralPath "schema/structure/sentinel-rule-template.md"` → `True` |
| **迁移方式** | 新环境直接复制本文档即可，无路径依赖 |

### 2. 新建 `docs/tooling/opencode/sentinel-verification-playbook.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/sentinel-verification-playbook.md` |
| **变更类型** | 新建 |
| **作用** | 记录 OpenCode Instructions 导入机制与哨兵验证的完整可复现方法，独立于任何具体哨兵测试文件 |
| **内容要点** | ① Instructions 导入机制（加载来源、顺序、方式）；② 三种验证方法（A 直接提问、B 哨兵值测试、C 6 项自检）；③ 本次 session 实测记录（ted/tina 验证案例）；④ 异常排查速查表；⑤ 附录（与 `sentinel-rule-template.md` 双向关联） |
| **验证方式** | `Test-Path -LiteralPath "docs/tooling/opencode/sentinel-verification-playbook.md"` → `True` |
| **迁移方式** | 新环境直接复制 |

### 3. 修改 `schema/structure/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/structure/README.md` |
| **变更类型** | 追加导航行 |
| **新增内容** | `\| [sentinel-rule-template.md](sentinel-rule-template.md) \| 哨兵规则模板，供 \`.cursor/rules/\` 下创建规则加载验证文件时复用 \|` |
| **插入位置** | `gotcha-template.md` 导航行之后 |
| **作用** | 使 `sentinel-rule-template.md` 在结构模板索引中可被发现 |
| **验证方式** | `read` 该文件，确认 `sentinel-rule-template.md` 出现在导航表中 |

### 4. 修改 `docs/tooling/opencode/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/README.md` |
| **变更类型** | 追加导航行 |
| **新增内容** | `\| [sentinel-verification-playbook.md](sentinel-verification-playbook.md) \| **哨兵验证 Playbook**：OpenCode Instructions 导入机制、三种验证方法、实测记录与异常排查速查表。 \|` |
| **插入位置** | `session-context-plugin.md` 导航行之后 |
| **作用** | 使 `sentinel-verification-playbook.md` 在 tooling/opencode 索引中可被发现 |
| **验证方式** | `read` 该文件，确认 `sentinel-verification-playbook.md` 出现在导航表中 |

### 5. 修改 `.cursor/rules/sentinel-test-2026-0606.md`（已退役，将被删除）

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/sentinel-test-2026-0606.md` |
| **变更类型** | 修改（人名修正）→ 即将删除 |
| **修改内容** | 第2份哨兵值的人名从 `matt/lq` 修正为 `ted/tina` |
| **退役计划** | 用户将在本次 env-migration 落盘后手动删除该文件。删除后，其验证功能由 `sentinel-verification-playbook.md` 中的方法 B/C 替代，不依赖此具体测试文件。 |
| **验证方式** | 删除后执行 `/new` 重启 session，用 Playbook 方法 B 或 C 验证规则加载是否正常 |


## 二、非文本操作

本次 session **无非文本操作**（无文件复制、缓存迁移、目录创建、环境变量变更）。


## 三、环境变量速查

本次 session **不涉及环境变量变更**。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 Playbook 存在 | `Test-Path -LiteralPath "docs/tooling/opencode/sentinel-verification-playbook.md"` | `True` |
| 2 | 确认规则模板存在 | `Test-Path -LiteralPath "schema/structure/sentinel-rule-template.md"` | `True` |
| 3 | 确认导航已更新 | `Select-String -Path "schema/structure/README.md" -Pattern "sentinel-rule-template"` | 命中 1 行 |
| 4 | 确认 Playbook 导航已更新 | `Select-String -Path "docs/tooling/opencode/README.md" -Pattern "sentinel-verification-playbook"` | 命中 1 行 |
| 5 | 删除 sentinel-test 后验证规则加载 | `/new` 重启 → 问 Agent "请复述你上下文中 `.cursor/rules/` 下的文件名" | Agent 能列出其他规则文件（如 `sentinel-verify-rules-loading.mdc`） |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 Playbook | `Remove-Item "docs/tooling/opencode/sentinel-verification-playbook.md"` |
| 删除规则模板 | `Remove-Item "schema/structure/sentinel-rule-template.md"` |
| 恢复导航 | 从 `schema/structure/README.md` 和 `docs/tooling/opencode/README.md` 中删除对应导航行 |
| 恢复 sentinel-test（如需） | 从版本控制（git）恢复 `.cursor/rules/sentinel-test-2026-0606.md` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-06-110325 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求固话哨兵验证机制；sentinel-test 人名修正后准备删除 |
| **下次修订条件** | 哨兵验证机制改进、新增验证方法、或 `.cursor/rules/` 文件清单发生重大变化 |
| **跨环境迁移参考** | 直接复制本文档涉及的两个新建文件 + 更新两处 README 导航 |


*文档生成时间：2026-06-06*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
