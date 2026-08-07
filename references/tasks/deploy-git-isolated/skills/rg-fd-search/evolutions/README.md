---
title: rg-fd-search 演进脉络——从基础搜索到 mdc-skill 强关联四层闭环
description: 汇总 rg-fd-search skill 从 v1.0.0 到 v2.0.0 的历次演进与收敛历程，说明每次演进的触发成因、核心改造与验证成果。
date: 2026-08-06
meta:
  version: "2.0.0"
---

# rg-fd-search 演进脉络

> 本文档汇总 skill 自创建以来的全部 evolution，按时间顺序排列。每次演进均源于实战踩坑，而非理论推演。演进的终点不是"完美"，而是"可验证的闭环"。

## v1.0.0 — 初始创建（2026-08-05）

**成因**：项目需要统一的搜索能力封装，替代 Agent 默认使用的原生 grep/glob。

**成果**：
- SKILL.md：定义 rg/fd 标准调用模板、P0-P3 搜索优先次序、参数速查
- SED 目录骨架：scripts/ references/ assets/ templates/ examples/ versions/ gotchas/ evolutions/ learnings/
- versions/manifest.json：初始演进时间线

**局限**：仅定义了搜索规范，未涉及 skill 与配套 mdc 的关联机制。

## v1.1.0 — 进度查询场景扩展（2026-08-06）

**成因**：用户要求"查看 gh 工作进度"，发现原有触发词只覆盖"搜索/查找"，未覆盖"进度/状态查询"。

**成果**：
- 新增 T005 进度/状态查询场景（触发词：查看进度、工作进展、开发状态）
- 追加 Step 4 磁盘验证层、Step 4b 示例执行验证审计层
- 追加 Step 5 env-migration 时间线补查层、Step 6 洞察与建议层
- 建立双源交叉验证模式（文档声称 vs 磁盘实际）
- 补录 PS 5.1 三元运算符 gotcha

**局限**：进度查询场景本身不涉及 mdc-skill 关联，但为后续关联机制建设提供了实战测试场。

## v1.2.0 — 配套关联机制建立（2026-08-06）

**成因**：用户要求"查看 gh 工作进度"时，Agent mdc（rg-fd-search-priority.mdc，alwaysApply）已触发，但 Agent 声称"没有任何 skill 命中"。skill 文件存在于磁盘，但 Agent 未加载。

**核心问题**：mdc 和 skill 之间没有不可绕过的关联机制。

**成果**：
- 建立双向显式声明铁律（铁律 1-5）：
  - 铁律 1：mdc 必须显式声明配套 skill（frontmatter + 正文顶部）
  - 铁律 2：skill 必须声明配套 mdc
  - 铁律 3：mdc 自检清单必须包含"配套 skill 加载"检查项
  - 铁律 4：高频任务速查表必须登记 skill
  - 铁律 5：EXEC-CHEATSHEET 命令示例前必须增加 skill 加载提示
- 记录 gotcha：mdc 已加载但配套 skill 被遗忘（配对断裂）
- 提炼 learning：规则层 alwaysApply mdc 与配套 skill 的配对闭环模式
- 修订联动：mdc / EXEC-CHEATSHEET / high-frequency-task-index / high-frequency-task-show-trigger / manifest

**局限**：双向声明本质上是"死后验尸"——只有 Agent 同时读取两者时才有效。若 skill 不在 `<available_skills>` 列表中，Agent 不会读取，单向声明变成"只有一半生效"。

## v1.3.0 — 三层闭环升级（2026-08-06）

**成因**：用户直接指出"改 SKILL.md 有鬼用啊，都没有触发"，暴露双向声明的致命缺陷。

**核心问题**：双向声明实际只有单向生效（mdc 可见，skill 不可见），没有全局审计卡点时闭环是幻觉。

**成果**：
- 升级为三层闭环（铁律 6-8）：
  - 铁律 6：全局审计卡点必须兜底（在 `high-frequency-tool-shell-audit.mdc` 中追加配套 skill 检查项）
  - 铁律 7："是"时必须展示操作对象（可验证）
  - 铁律 8：skill 加载失败时必须 fallback 到磁盘 read
- 记录 gotcha：单向声明不足——改 SKILL.md 无法阻止 mdc→skill 触发断裂
- 提炼 learning：跨规则层联动模式——当 A↔B 双向配套但 B 对 Agent 不可见时，必须在第三个独立且 alwaysApply 的层级 C 设置不可绕过的检查点
- 修订联动：tool-audit.mdc / manifest / gotcha / evolution / learning

**验证**：subagent 执行搜索任务时，tool-audit 审计块成功触发了配套 skill 检查，并 fallback 到磁盘 read SKILL.md。

**局限**：审计覆盖不完整——fallback read 和后续 tool 调用前未输出审计块；Agent 只检查了自己所在的 mdc，未检查其他 alwaysApply mdc。

## v1.4.0 — 四层闭环 + 生效 mdc 列表（2026-08-06）

**成因**：subagent 实战验证中发现两个漏洞：
1. Agent 只扫描 tool-audit 自己的高频任务列表，未扫描 rg-fd-search-priority.mdc 的触发词
2. fallback read 和后续 bash/read/write 调用前未输出审计块

**核心问题**：三层闭环的审计卡点只覆盖了"有没有配套 skill"，但没有覆盖"当前有哪些 mdc 生效"和"每次 tool 调用是否独立审计"。

**成果**：
- 升级为四层闭环（铁律 9-11）：
  - 铁律 9：生效 mdc 列表必须显式列出（防止 Agent 只检查自己所在的 mdc）
  - 铁律 10：read 纳入审计范围（tool-audit.mdc 适用范围从 bash/write/edit 扩展到 read）
  - 铁律 11：每次 tool 调用必须独立审计（禁止以"这是上一步的延续"为由跳过）
- 记录核心 gotcha：mdc-skill 强关联从"无效双向声明"到"有效四层闭环"的演进
- 记录 gotcha：fallback read 前遗漏审计块
- 提炼 learning：生效 mdc 列表模式——解决 alwaysApply mdc 的"不可见性"问题
- 修订联动：tool-audit.mdc（追加生效 mdc 列表项 + read 纳入审计）/ manifest / gotcha / evolution / learning

**验证结果**（subagent 实战测试）：

| 验证项 | 改造前 | 改造后 |
|--------|--------|--------|
| 识别到 rg-fd-search-priority.mdc 已触发 | ❌ 无 | ✅ 列出生效 mdc |
| 检测到配套 skill rg-fd-search | ❌ 声称"无 skill 命中" | ✅ 明确写出 skill 名称 |
| fallback 到正确 SKILL.md | ❌ 未发生 | ✅ `skills/rg-fd-search/SKILL.md` |
| 按 skill 规范执行 rg/fd | ❌ 用 glob/grep | ✅ `fd -e md` + `rg -n -i -C 3` |

**核心洞察**：
> mdc-skill 强关联的关键不是"互相声明"，而是"不可绕过的检查点"。只有当 Agent **无法在不检查的情况下继续执行**时，配套关联才真正生效。

## v1.5.0 — P0 搜索范围扩展至 vaults/（2026-08-07）

**成因**：用户搜索 "gh 工作进度" 时，Agent 仅搜索了 env-migrations/（工程变更记录），遗漏了 devroot/vaults/ 下的进度看板、架构设计、踩坑记录等认知资产，导致上下文断裂。

**成果**：
- P0 树状自说明搜索范围扩展：task 内部文档 → devroot/vaults/（若存在）
- 建立不硬编码原则：探测 → HITL → 动态引用（多端多根对齐）
- 建立 vaults/ 与 env-migrations/ 互补查询模式
- 产出 evolution + learning

## v1.5.1 — baseline/ 审计基准层建立（2026-08-07）

**成因**：用户要求增加 skill/baseline/ 目录，沉淀审计基准约定、Human/Agent 共同理解、工程偏好。

**成果**：
- 新建 baseline/ 目录及 README.md 导航
- 落盘 baseline-no-hardcode-paths.md（路径引用不硬编码原则）
- 验证 baseline/ 层可用于沉淀审计基准

## v1.5.2 — SED 机制运行规范 baseline（2026-08-07）

**成因**：用户要求记录 SED 机制的目标、触发策略、实现路径、有效性检验标准。

**成果**：
- 落盘 baseline-sed-mechanism.md
- 定义三大触发策略（Human-in-the-Loop / Agent 自检 / 定期收敛）
- 定义智能自检触发方案（3 维度 9 项 + 建议话术模板 + Human 决策权保留）

## v1.5.3 — SEAS 审计 schema 落地（2026-08-07）

**成因**：用户指出"命中次数检验"等有效性标准缺乏落地实现。

**成果**：
- 落盘 baseline-skill-audit-schema.md（SEAS 规范）
- 创建 versions/audit-trail.jsonl（JSON Lines 审计轨迹载体）
- 将抽象检验标准落地为可追加、可聚合、可查询的审计轨迹系统

## v1.5.4 — SED 自检实战验证（2026-08-07）

**成因**：用户要求"触发一个 skill sed 自检，看执行效果"。

**成果**：
- 执行完整 SED 自检（9 项中 7 项命中，召回率 78%）
- 产出 5 条 SED 记录：1 gotcha + 1 evolution + 3 learnings
- 验证自检流程有效性
- 用户反馈"逐项记录"，100% 转化率

## v2.0.0 — 收敛（2026-08-07）

**成因**：evolutions 数量达到收敛阈值（6 >= 5），用户建议"可以考虑把目前版本归档，既是安全考量，也是 diff 版本追踪的举措"。

**收敛内容**：
- 归档原 SKILL.md：`versions/archive/SKILL-v1.0.0-20260807-convergence-backup.md`
- 将 6 个 evolution 合并回 SKILL.md：
  - T005 进度查询触发场景 + Step 4-6
  - P0 vaults/ 扩展 + 不硬编码 HITL 原则
  - Step 7-8（SED 自检 + SEAS 审计记录）
  - 配套 skill 关联机制（铁律 1-11）
  - 目录结构扩展（baseline/ + audit-trail.jsonl + metrics.json）
  - frontmatter 规范扩展（description + meta 四类型通用）
- 已收敛 evolution 移入 `versions/archive/`
- manifest.json 更新：`current_version` → `2.0.0`，`convergence_history` 追加记录

**当前状态**：
- evolutions/ 已清空（保留 README.md 作为演进脉络历史记录）
- 新 evolution 将继续在此目录积累，达到阈值后再次触发收敛

## 当前版本能力速查（v2.0.0）

| 能力 | 状态 | 说明 |
|------|------|------|
| rg/fd 标准调用 | ready | 强制 P0-P3 搜索优先次序 |
| mdc-skill 强关联 | ready | 四层闭环：mdc 声明 + skill 声明 + 全局审计卡点 + 生效 mdc 列表 |
| SED 自演进 | ready | gotchas/ evolutions/ learnings/ baseline/ 持续积累，manifest.json 真源索引 |
| 进度/状态查询 | ready | T005 场景，支持磁盘验证 + env-migration 时间线补查 + vaults/ 扩展 |
| SED 自检触发 | ready | 3 维度 9 项自检清单 + 建议话术模板 + Human 决策权保留 |
| SEAS 审计轨迹 | ready | audit-trail.jsonl 只增不改，metrics.json 定期聚合 |
| 跨规则层联动 | ready | 当单向声明失效时，用第三个 alwaysApply 层级兜底 |
| 版本归档 | ready | 收敛前 SKILL.md 备份到 archive/，支持 diff 追踪 |

## 待完善事项

1. **铁律 10/11 实施**：tool-audit.mdc 的 read 纳入审计和每次 tool 调用独立审计，需在下次触及 tool-audit.mdc 时实际修改
2. **其他 skill 的三层/四层闭环复制**：tool-discovery、docstring-quality-harness 等 skill 是否也存在 mdc-skill 断裂风险，需逐一排查
3. **metrics.json 聚合脚本**：当 audit-trail.jsonl 积累 >= 10 条时，创建 scripts/aggregate-audit.py 生成 metrics.json
4. **下次收敛准备**：当前 evolutions/ 已清空，新 evolution 积累中

## 关联索引

- [rg-fd-search 总览](../README.md)：返回 skill 根目录自说明
- [SKILL.md](../SKILL.md)：skill 主文档与执行手册（v2.0.0）
- [evolutions/](.)：演进脉络历史记录（当前无活跃补丁）
- [gotchas/](../gotchas)：全部踩坑记录
- [learnings/](../learnings)：全部认知模式
- [baseline/](../baseline)：审计基准与机制规范
- [versions/manifest.json](../versions/manifest.json)：演进时间线真源
- [versions/archive/](../versions/archive)：已收敛 evolution 与 SKILL.md 备份归档
