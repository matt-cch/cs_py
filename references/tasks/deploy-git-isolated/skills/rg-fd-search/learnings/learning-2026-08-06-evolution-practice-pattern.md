---
title: Evolution 实践示范——从用户缺陷反馈到 SED 入库的完整闭环
description: 记录 2026-08-06 rg-fd-search skill 首次 evolution 的完整实践路径，作为后续所有 skill evolution 的示范模板与诊断 checklist
date: 2026-08-06
type: learning
category: pattern
confidence: high
evidence_count: 1
meta:
  version: "1.1.0"
  related_evolution: "evolutions/evolution-2026-08-06-progress-query-insight-loop.md"
fingerprint:
  content_sha256: "learning-evolution-practice-pattern-20260806"
  semantic_key: "rg-fd-search-evolution-practice-pattern"
---

# Evolution 实践示范——从用户缺陷反馈到 SED 入库的完整闭环

## 一、触发条件（什么情况下 skill 需要 evolution？）

| 信号类型 | 典型表现 | 本次案例 |
|---------|---------|---------|
| **用户明确评分/否定** | "只能给你 70 分"、"有缺陷"、"完全没提到" | 用户指出报告只有树状信息、无实证、无时间线、无方向 |
| **输出与预期差距** | 用户说"下一步想做什么依然不清晰" | 报告缺乏"下一步聚焦方向" |
| **用户追加要求** | "你应该去查 env-migration"、"你应该验证文件存在性" | 用户明确给出补查指令 |

> **判定标准**：不是"用户不满意"就 evolution，而是用户指出的缺陷属于**skill 结构性能力缺失**（本次是"进度查询场景完全没被 skill 覆盖"），而非单次执行参数错误。

## 二、诊断路径（怎么定位问题根因？）

### 阶段 1：复现缺陷

- **重读用户反馈原文**，逐条标注缺陷编号
- **对比当前 skill 输出 vs 用户期望输出**，找出 gap

本次 gap 映射：

| 用户期望 | skill 当前输出 | gap 类型 |
|---------|---------------|---------|
| 磁盘实证验证 | 只有文档声明 | **能力缺失**（无 Step 4） |
| env-migration 时间线 | 完全未提及 | **能力缺失**（无 Step 5） |
| 下一步聚焦方向 | 没有 | **能力缺失**（无 Step 6） |
| 发现 MISSING 文件 | 没有 | **认知盲区**（文档=真源误区） |

### 阶段 2：根因分析

- **不是"这次搜少了"，而是"skill 没有定义这种场景"**
- 识别：用户意图是"进度查询"（T005），但 skill 只定义了"文件查找"（T001~T004）
- 识别：skill 只有 P0-P3 搜索，没有"验证→补查→洞察"闭环

### 阶段 3：借鉴现有模式

- 查其他 skill 或 mdc 是否有类似闭环模式可复用
- 本次借鉴：`.cursor/rules/high-frequency-verify-runtime.mdc` 的"检测→报告→索引回写"闭环

## 三、解法设计（怎么设计 evolution？）

### 3.1 能力分层设计

不要一次性把缺陷全塞进现有步骤。按层次追加：

```
现有层（P0-P3）：搜索层 → 保持不变
新增层 Step 4：验证层（磁盘存在性）→ 解决"文档≠真源"
新增层 Step 5：上下文层（env-migration 时间线）→ 解决"缺乏脉络"
新增层 Step 6：洞察层（矛盾发现 + 方向建议）→ 解决"没有下一步"
```

### 3.2 触发条件设计

- 不是所有搜索都走 6 步，只有命中 T005（进度/状态查询）时才触发 Step 4-6
- 保持现有 T001~T004 的轻量行为不变

### 3.3 输出模板设计

为 Step 6 预定义结构化报告模板，避免每次临时发挥：

```
## 工作进度报告
### 一、整体状态
### 二、近期时间线
### 三、实证验证（文档 vs 磁盘）
### 四、未改造/待完善事项
### 五、下一步聚焦方向
```

## 四、验证闭环（怎么验证 evolution 有效？）

### 4.1 单文件验证

- evolution 文档写完后 → `run-lint.py` 验证 frontmatter + encoding
- learning 文档写完后 → 同上
- manifest.json 更新后 → `lint_json` 验证

### 4.2 能力验证（模拟测试）

- 自问：如果下一次遇到"某某场景的工作进度"，按新 skill 能输出什么？
- 检查是否包含：时间线 + 实证 + MISSING + 方向

### 4.3 用户验收

- 向用户汇报 evolution 设计，确认是否覆盖其反馈
- 本次：用户进一步追问"是否可以作为示范"，说明 evolution 设计方向正确，但元认知层（本 learning）尚未沉淀

## 五、SED 入库流程（怎么把 evolution 落盘？）

### 5.1 决策：evolution vs learning vs gotcha

| 类型 | 判定标准 | 本次归属 |
|------|---------|---------|
| evolution | skill 行为/规则/参数/工作流发生变更 | **evolution**：新增 T005 + Step 4/5/6 |
| learning | 发现可复用的认知/模式/洞察 | **learning**：文档≠真源的双源交叉验证模式 |
| gotcha | 踩坑记录 | 本次无新踩坑（是能力缺失，不是执行错误） |

### 5.2 并行写入

```
1. 写 evolution/xxx.md
2. 写 learning/xxx.md（与 evolution 配套，解释"为什么这样改"）
3. 更新 versions/manifest.json（版本号 + fingerprint + history）
4. run-lint.py 验证全部
5. 如需登记到项目级索引，走 tool-registration-revision-linkage.mdc
```

### 5.3 版本号策略

- 新增 evolution → minor 版本 +1（1.0.0 → 1.1.0）
- 收敛回 SKILL.md → patch 版本 +1（如 1.1.0 → 1.1.1）
- 重大重构 → major 版本 +1

## 六、对下一次 evolution 的指导 checklist

下次任何 skill 被用户指出缺陷时，按以下 checklist 执行：

```
【Evolution 触发诊断】
- [ ] 用户反馈是否属于结构性能力缺失？（是 → evolution，否 → 单次修正）
- [ ] 是否已逐条映射用户期望 vs 当前输出 gap？
- [ ] 根因是"没定义场景"还是"定义了但没执行"？

【Evolution 设计】
- [ ] 新增能力是追加层（向后兼容）还是修改层（破坏兼容）？
- [ ] 触发条件是否精确？（避免所有场景都触发新增层）
- [ ] 输出模板是否预定义？（避免临时发挥）

【Evolution 验证】
- [ ] evolution/learning/manifest 全部 lint 通过？
- [ ] 模拟测试：按新 skill 执行一次，输出是否覆盖用户反馈？
- [ ] 用户是否确认 evolution 方向？

【Evolution 入库】
- [ ] 判断类型正确（evolution/learning/gotcha）？
- [ ] manifest.json 版本号 + fingerprint + history 更新？
- [ ] 项目级索引登记（verified-task-index / verified-trigger-index）？
```

## 七、关联文件

- **本次 evolution**：`evolutions/evolution-2026-08-06-progress-query-insight-loop.md`
- **本次 learning（认知层）**：`learnings/learning-2026-08-06-tree-docs-vs-disk-reality-gap.md`
- **本次 learning（实践层）**：本文件
