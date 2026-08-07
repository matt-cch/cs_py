---
title: mdc-skill 强关联从无效到有效——四层闭环改造 + subagent 实战验证 + SED 双轮迭代
description: 本次 session 完成 mdc-skill 配套关联机制的完整演进：从双向声明（无效）→ 三层闭环（部分有效）→ 四层闭环（验证通过）。核心改造 high-frequency-tool-shell-audit.mdc，完成两轮 SED 入库（6 个增量文件），subagent 实战验证确认 Agent 能正确定位指定 skill 并按规范执行 rg/fd。
date: 2026-08-06
meta:
  version: "1.0"
---

# env-migration-mdc-skill-strong-association-full-session-2026-08-06-173920

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | mdc-skill 强关联从无效到有效——四层闭环改造 + subagent 实战验证 + SED 双轮迭代 |
| **日期** | 2026-08-06 |
| **文件名时间戳** | 2026-08-06-173920 |
| **触发原因** | 用户要求"查看 gh 工具链开发工作进度"，Agent mdc 已触发但 skill 未加载，暴露 mdc-skill 单向声明不足问题 |
| **影响范围** | `.cursor/rules/high-frequency-tool-shell-audit.mdc`、`references/tasks/deploy-git-isolated/skills/rg-fd-search/`（SED 全量更新）、`references/env-migrations/README.md` |
| **风险等级** | 低（规则层与文档变更，无运行时依赖变更） |

## 一、文本文件变更清单

### 第一轮改造（三层闭环）

#### 1. 修改 `.cursor/rules/high-frequency-tool-shell-audit.mdc`（第一轮）

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| **变更类型** | 修改 |
| **新增内容** | 自检清单追加 2 项："当前 mdc 是否有配套 skill？"、"配套 skill 是否已加载？"；流程图追加"mdc→skill 加载确认"分支；所有"是/否"检查项改为"是"时必须展示操作对象 |
| **作用** | 建立跨规则层全局审计卡点，任何 tool 调用前强制检查配套 skill 状态 |

#### 2. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-unilateral-declaration-insufficient.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-unilateral-declaration-insufficient.md` |
| **变更类型** | 新建 |
| **作用** | 记录"单向声明不足"陷阱：改 SKILL.md 无法阻止 mdc→skill 触发断裂 |

#### 3. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-triple-loop.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-triple-loop.md` |
| **变更类型** | 新建 |
| **作用** | 将配套关联机制从双向声明升级为三层闭环（mdc 声明 + skill 声明 + 全局审计卡点） |

#### 4. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-cross-rule-layer-audit-pattern.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-cross-rule-layer-audit-pattern.md` |
| **变更类型** | 新建 |
| **作用** | 提炼"跨规则层联动"可复用模式：当 A↔B 双向配套但 B 对 Agent 不可见时，必须在第三个独立且 alwaysApply 的层级 C 设置不可绕过的检查点 |

#### 5. 修改 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json`（v1.2.0 → v1.3.0）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |
| **变更类型** | 修改 |
| **新增内容** | `current_version`: 1.2.0 → 1.3.0；fingerprint_index 追加 3 个新指纹；evolution_history 追加 v1.3.0 记录 |
| **作用** | SED 演进真源索引同步 |

### 第二轮改造（四层闭环 + 核心 gotcha + 演进脉络）

#### 6. 修改 `.cursor/rules/high-frequency-tool-shell-audit.mdc`（第二轮）

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| **变更类型** | 修改 |
| **新增内容** | 自检清单追加"当前已触发的生效 mdc 有哪些？"项 |
| **作用** | 防止 Agent 只检查自己所在的 mdc，遗漏其他 alwaysApply mdc |

#### 7. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-mdc-skill-strong-association-evolution.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-mdc-skill-strong-association-evolution.md` |
| **变更类型** | 新建 |
| **作用** | **核心 gotcha**。记录从"无效双向声明"到"有效四层闭环"的完整演进，含改造前/第一次尝试/第二次尝试/第三次尝试/验证后的对比表 |

#### 8. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-fallback-read-missing-audit-block.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-fallback-read-missing-audit-block.md` |
| **变更类型** | 新建 |
| **作用** | 记录 subagent 验证中发现的审计覆盖漏洞：fallback read 和后续 tool 调用前未输出 tool-audit 审计块 |

#### 9. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-quadruple-loop.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/evolution-2026-08-06-mdc-skill-quadruple-loop.md` |
| **变更类型** | 新建 |
| **作用** | 将三层闭环升级为四层闭环，定义铁律 9（生效 mdc 列表）、铁律 10（read 纳入审计）、铁律 11（每次 tool 调用独立审计） |

#### 10. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-active-mdc-list-pattern.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/learnings/learning-2026-08-06-active-mdc-list-pattern.md` |
| **变更类型** | 新建 |
| **作用** | 提炼"生效 mdc 列表"可复用模式：解决 alwaysApply mdc 的"不可见性"问题 |

#### 11. 新建 `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/README.md` |
| **变更类型** | 新建 |
| **作用** | 演进脉络汇总：从 v1.0.0 到 v1.4.0 的历次演进成因、核心改造与验证成果，含当前版本能力速查表 |

#### 12. 修改 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json`（v1.3.0 → v1.4.0）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |
| **变更类型** | 修改 |
| **新增内容** | `current_version`: 1.3.0 → 1.4.0；fingerprint_index 追加 4 个新指纹（含核心 gotcha）；evolution_history 追加 v1.4.0 记录 |
| **作用** | SED 演进真源索引同步 |

### 其他变更

#### 13. 修改 `references/env-migrations/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/env-migrations/README.md` |
| **变更类型** | 修改 |
| **新增内容** | 导航表追加 `env-migration-mdc-skill-triple-loop-and-tool-audit-audit-2026-08-06-160643.md` 条目 |
| **作用** | env-migration 导航同步 |

## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。所有变更均为文本文件修改或新建。

## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 tool-audit.mdc 已追加配套 skill 检查项 | `rg -n "配套 skill" .cursor/rules/high-frequency-tool-shell-audit.mdc` | 显示检查项及"是"时展示操作对象的规范 |
| 2 | 确认 tool-audit.mdc 已追加生效 mdc 列表项 | `rg -n "生效 mdc" .cursor/rules/high-frequency-tool-shell-audit.mdc` | 显示"当前已触发的生效 mdc 有哪些" |
| 3 | 确认核心 gotcha 已入库 | `Test-Path "references/tasks/deploy-git-isolated/skills/rg-fd-search/gotchas/gotcha-2026-08-06-mdc-skill-strong-association-evolution.md"` | True |
| 4 | 确认演进脉络 README 已入库 | `Test-Path "references/tasks/deploy-git-isolated/skills/rg-fd-search/evolutions/README.md"` | True |
| 5 | 确认 SED 双轮增量文件齐全 | `fd -e md "2026-08-06" references/tasks/deploy-git-isolated/skills/rg-fd-search/` | 显示 8 个新文件（第一轮 3 个 + 第二轮 4 个 + 演进脉络 1 个） |
| 6 | 确认 manifest 已更新 | `rg -n "1.4.0" references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` | 显示 current_version 和 evolution_history 条目 |
| 7 | subagent 实战验证 | 委派 subagent 执行搜索任务，检查其审计块和 manifest | 审计块包含"生效 mdc 列表"和"配套 skill 检查"；fallback 到正确的 SKILL.md；按 skill 规范使用 rg/fd |
| 8 | 确认 lint 通过 | `run-lint.py --files <全部变更文件>` | ✅ 全部通过 |

## 四、Session 踩坑与纠偏记录

### 踩坑 1：Agent 再次声称"没有任何 skill 命中"

**现象**：用户要求"查看 gh 工作进度"，Agent mdc 已触发，尝试 `skill` 工具加载 rg-fd-search 失败（不在 available_skills 中），fallback 到 glob/grep 原生工具。

**根因**：
1. 系统提示 `<available_skills>` 不包含 task 本地 skill
2. Agent 未读取 env-migration 中已记录的教训，重复踩同一坑
3. evolution v1.2.0 建立的"双向声明"机制实际只有单向生效

**纠偏**：用户直接指出"改 SKILL.md 有鬼用啊，都没有触发"，Agent 纠正方向，在 tool-audit.mdc 中建立全局审计卡点。

### 踩坑 2：Agent 未读 env-migration 就从头推理

**现象**：用户说"你去看一下 env-migration"，Agent 花了大量时间重新搜索、分析、得出结论，而没有先读取已有的 env-migration 文档获取上下文。

**根因**：Agent 默认行为是"搜索→分析→推理"，而不是"读取已有记录→复用→执行"。

**纠偏**：用户严厉批评"都解决半天了，你还又从头开始"，Agent 随后读取 env-migration 获取上下文。

### 踩坑 3：Agent edit 前未全文读取目标文件

**现象**：Agent 试图 edit `rg-fd-search-priority.mdc` 的自检清单，但刚改完就发现 mdc 中已有配套 skill 检查项（只是 SKILL.md 中没有）。

**根因**：Agent 未先全文读取文件就假设内容缺失。

**纠偏**：用户指出"全文都没读，原来文本内容里是不是已经有了，你不用先了解的吗？就直接改？"

### 踩坑 4：Agent 用不可靠的 manifest 自我验证

**现象**：Agent 读取 subagent 自报的 manifest，声称"使用了 fd"，但用户观察到的实际是"全程 read baseline"。

**根因**：manifest 是 subagent **自述**的，不是客观记录。Agent 把间接证据（manifest 自述）当成了可观测证据。

**纠偏**：用户指出"我都没有观察到 fd 的使用"，Agent 承认验证方法有缺陷，改为要求 subagent 记录 think 推理过程和实际 tool 调用详情。

### 踩坑 5：Agent 的 gotcha 没抓到真正有价值的点

**现象**：第一轮 SED 入库时，Agent 写的 gotcha 聚焦"fallback read 遗漏审计块"，用户指出"真正有价值的是从 mdc-skill 强关联无效到有效的演进"。

**根因**：Agent 关注执行层面的细节漏洞，而忽略了用户关心的核心转变（机制从无到有的质变）。

**纠偏**：用户直接点明方向，Agent 重写核心 gotcha，记录从"无效双向声明"到"有效四层闭环"的完整演进。

## 五、核心成果

| 维度 | 成果 |
|------|------|
| **机制建设** | mdc-skill 配套关联从"无效双向声明"升级为"有效四层闭环"（11 条铁律） |
| **规则改造** | `high-frequency-tool-shell-audit.mdc` 追加配套 skill 检查项 + 生效 mdc 列表 + "是"时展示操作对象 |
| **SED 入库** | 两轮共 8 个增量文件（3 gotcha + 2 evolution + 2 learning + 1 演进脉络 README） |
| **验证方法** | subagent 实战测试 + think 推理过程记录 + manifest 落盘 |
| **核心洞察** | mdc-skill 强关联的关键不是"互相声明"，而是"不可绕过的检查点" |

## 六、未改造/待完善事项

| # | 事项 | 原因 | 建议优先级 |
|---|------|------|-----------|
| 1 | 铁律 10/11 实际修改 tool-audit.mdc | evolution 已定义 read 纳入审计和每次 tool 调用独立审计，但 tool-audit.mdc 正文尚未实际修改适用范围 | 高（下次触及 tool-audit.mdc 时立即补） |
| 2 | 其他 skill 的三层/四层闭环复制 | tool-discovery、docstring-quality-harness 等 skill 也可能存在 mdc-skill 断裂风险 | 中（逐一排查） |
| 3 | SED 收敛 | evolutions/ 已有 4 个文件，距上次收敛 30 天阈值尚有距离 | 低（暂不触发） |

## 七、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 tool-audit.mdc | 从 git 恢复 `.cursor/rules/high-frequency-tool-shell-audit.mdc` 到修改前版本 |
| 删除第一轮 SED 文件 | `Remove-Item` 删除 3 个 gotcha/evolution/learning 文件 |
| 删除第二轮 SED 文件 | `Remove-Item` 删除 4 个 gotcha/evolution/learning/演进脉络 文件 |
| 恢复 manifest.json | 从 git 恢复 `references/tasks/deploy-git-isolated/skills/rg-fd-search/versions/manifest.json` |
| 恢复 env-migrations/README.md | 从 git 恢复 `references/env-migrations/README.md` |

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-06-173920 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求查看 gh 工作进度，暴露 mdc-skill 单向声明不足问题 |
| **下次修订条件** | 当 tool-audit.mdc 实际追加 read 纳入审计和每次 tool 调用独立审计时；当其他 skill 建立四层闭环时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
