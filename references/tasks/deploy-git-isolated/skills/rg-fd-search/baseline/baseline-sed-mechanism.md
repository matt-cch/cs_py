---
title: 审计基准 — SED（Self-Evolution Directory）机制运行规范
description: 定义 rg-fd-search skill 的 SED 目标、触发策略、实现路径、有效性检验标准，以及 Agent 自检触发 SED 的智能增强方案
date: 2026-08-07
meta:
  version: "1.0.0"
  tags: [sed, self-evolution, skill, audit, baseline, evolution, learning, gotcha]
---

# 审计基准 — SED（Self-Evolution Directory）机制运行规范

## 一、SED 目标

SED（Self-Evolution Directory）是 skill 的**自演进目录体系**，目标是将单次 session 中的认知增量（踩坑、规则变更、模式洞察）系统性地沉淀为可复用的规则补丁，最终收敛回 SKILL.md 主文档。

| 目标编号 | 目标 | 衡量方式 |
|---------|------|---------|
| G1 | **缩短认知到规则的收敛周期** | 从"踩坑 → 记录 gotcha → 提炼 evolution → 收敛回 SKILL.md"的全链路时间 |
| G2 | **降低 Human 纠偏成本** | Human 是否需要重复指出同一类问题 |
| G3 | **保持 skill 与实战的对齐** | skill 工作流是否覆盖当前实践中已验证的最佳路径 |
| G4 | **避免知识随 Agent 重置而丢失** | 重置后的新 Agent 能否通过 SED 目录快速恢复上下文 |

## 二、触发 SED 的策略与时机

### 2.1 策略总览

| 策略 | 触发方 | 触发时机 | 当前状态 | 优先级 |
|------|--------|---------|---------|--------|
| **A. Human-in-the-Loop** | Human | Human 观察 Agent 执行效果不满意，主动提出 feedback | ✅ 已运行 | P0 |
| **B. Agent 自检触发** | Agent | 每次 skill 执行完毕后执行【新认知检测】自检 | 🔄 待增强 | P1 |
| **C. 定期收敛** | Agent / Human | evolutions >= 5 或 gotchas >= 10 或距上次收敛 >= 30 天 | ✅ 已定义 | P2 |

### 2.2 策略 A：Human-in-the-Loop（当前主路径）

**运行方式**：

```
Human 观察 Agent 执行 → 不满意 → 提出 feedback
    ↓
Agent 创建 gotcha / evolution / learning
    ↓
更新 versions/manifest.json
    ↓
run-lint.py 验证
    ↓
Human 确认 → 交付
```

**当前实践中 Human 的典型 feedback 类型**：

| feedback 类型 | 对应 SED 产物 | 示例 |
|--------------|--------------|------|
| "搜索结果不完整" | evolution（workflow 扩展） | P0 扩展至 vaults/ |
| "Agent 行为偏离预期" | gotcha（陷阱记录） | mdc-skill 配对断裂 |
| "发现了一个可复用模式" | learning（认知沉淀） | vaults/ 与 env-migrations/ 分工模式 |
| "某规则需要修正" | evolution（规则补丁） | 不硬编码原则 |

**瓶颈**：Human 必须主动观察并提出 feedback。若 Human 未察觉或 Session 结束后才想起，认知增量丢失。

### 2.3 策略 B：Agent 自检触发（智能增强方案）

**核心思想**：每次 skill 执行完毕后，Agent 主动执行【新认知检测】自检，若发现 skill 文档未覆盖的异常/优化点/模式，在"下一步建议"中**显式建议用户进行 SED**。

**触发时机**：

```
skill 主工作流执行完毕
    ↓
【SED 自检触发器】自动执行
    ↓
检测结果：
    ├── 无新认知 → 正常结束
    └── 有新认知 → 在"下一步建议"中追加 SED 建议
        ↓
    Human 决策：
        ├── "记一下" → 进入 SED 落盘流程
        └── "不用" → 记录本次自检结论，不写入 SED（避免噪音）
```

**自检清单（3 维度 9 项）**：

```
【新认知检测 — SED 自检】
维度 1：异常/陷阱（→ gotcha）
  [ ] 本次执行是否遇到 SKILL.md + evolutions/ 均未覆盖的异常或边界？
  [ ] 是否有命令执行失败、输出异常、ParserError、编码问题等未预期行为？
  [ ] Human 是否在执行过程中进行了纠偏或澄清？

维度 2：规则/行为变更（→ evolution）
  [ ] 实际执行路径是否与 SKILL.md 推荐做法不同？
  [ ] 不同的做法是否更优（更简洁、更可靠、更快）？
  [ ] 是否有 SKILL.md 未声明的边界条件或例外场景？

维度 3：洞察/模式/结论（→ learning）
  [ ] 是否发现了可复用的认知、经验、基准或启发式？
  [ ] 是否识别出两个以上不同来源（文档/日志/磁盘）之间的系统性关系？
  [ ] 本次 session 的结论是否对后续同类任务有指导价值？
```

**建议话术模板**（当自检命中时，在"下一步建议"中追加）：

```
💡 【SED 自检提示】
本次 skill 执行过程中发现以下可能值得沉淀为新认知：

- 维度：<gotcha / evolution / learning>
- 现象：<一句话描述>
- 建议：<是否应在 skill SED 中记录>

是否需要记录到 skill SED？（回复"记一下"即可触发）
```

**决策权保留**：
- Agent **只能建议**，不能自行决定写入 SED
- Human 拥有最终决策权："记一下" / "不用" / "先放放"
- 若 Human 说"不用"，Agent 应在回复中简要记录自检结论（供 Human 后续参考），但不写入磁盘

### 2.4 策略 C：定期收敛

**收敛条件**（满足任一即触发）：

| 条件 | 阈值 | 当前状态 |
|------|------|---------|
| evolutions 数量 | >= 5 | 当前 6 个（已满足） |
| gotchas 数量 | >= 10 | 当前 6 个（未满足） |
| 距上次收敛天数 | >= 30 | 上次 2026-08-05（未满足） |

**收敛流程**：

```
1. 读取 evolutions/ 下全部文件，按 target_section 分组
2. 同一 target_section 的多个 evolution 合并为统一补丁
3. 生成 SKILL.md 的新版本草稿（merge 所有补丁）
4. run-lint.py 验证新 SKILL.md
5. 将已收敛的 evolution 移入 versions/archive/
6. 更新 manifest.json convergence_history
7. Human 审阅并确认
```

## 三、SED 实现路径

### 3.1 目录结构（SED 八层架构）

```
skills/rg-fd-search/
├── SKILL.md              # 基准文件（收敛目标）
├── README.md             # 合并导航
├── baseline/             # 审计基准面（本目录）
│   ├── README.md
│   ├── baseline-no-hardcode-paths.md
│   └── baseline-sed-mechanism.md      # ← 本文件
├── scripts/              # 执行面（不对外登记）
├── references/           # 引用面
├── assets/               # 资产面
├── templates/            # 模板面
├── examples/             # 示例面
├── versions/             # 版本面
│   ├── manifest.json     # 指纹索引 + 演进历史
│   └── archive/          # 已收敛 evolution 归档
├── gotchas/              # 错误面（踩坑记录，不可变追加）
├── evolutions/           # 行为面（规则/参数/流程补丁，有序加载）
└── learnings/            # 认知面（洞察/模式/基线/结论）
```

### 3.2 文件规范

**所有写入 gotchas/ / evolutions/ / learnings/ 的 `.md` 文件必须包含标准化 frontmatter**：

| 类型 | 必填字段 | 特殊字段 |
|------|---------|---------|
| gotcha | title, date, type=gotcha, fingerprint | — |
| evolution | title, date, type=evolution, scope, category, target_section, fingerprint | scope: add/replace/append/override |
| learning | title, date, type=learning, category, confidence, evidence_count, fingerprint | category: insight/pattern/baseline/conclusion/heuristic |
| baseline | title, description, date, meta, fingerprint | — |

**fingerprint 规范**：

```yaml
fingerprint:
  content_sha256: <sha256(核心内容)>
  semantic_key: <规范化主题标识，如 search-scope-vaults>
```

### 3.3 去重策略

1. **精确去重**：计算 `fingerprint.content_sha256`，与 `versions/manifest.json` 中已有指纹比对，完全匹配则自动跳过
2. **语义去重**：计算与已有同类型文件的 trigger_condition / 现象描述 Jaccard 相似度，> 0.8 则暂停并请求用户确认
3. **手动审阅**：Human 可在"记一下"前要求 Agent 展示拟写入内容的摘要，确认非重复后再落盘

### 3.4 收敛流程（evolutions → SKILL.md）

```
触发条件满足（evolutions>=5 / gotchas>=10 / >=30天）
    ↓
读取 evolutions/ 全部文件
    ↓
按 target_section 分组排序
    ↓
合并同 target_section 的 evolution 为统一补丁
    ↓
生成 SKILL.md 新版本（内存中）
    ↓
run-lint.py 验证 SKILL.md
    ↓
将已收敛 evolution 移入 versions/archive/
    ↓
更新 manifest.json（convergence_history）
    ↓
Human 审阅确认
    ↓
write SKILL.md 新版本
```

## 四、Evolution 有效性检验

### 4.1 短期检验（单次任务）

| 检验项 | 方法 | 通过标准 |
|--------|------|---------|
| 问题是否复现 | 下次同类任务观察 | 同一问题不再出现 |
| evolution 是否被引用 | 检查后续 session 是否按 evolution 执行 | 被引用 >= 1 次 |
| 副作用 | 检查是否引入新问题 | 无新增 gotcha |

### 4.2 中期检验（累计执行）

| 检验项 | 方法 | 通过标准 |
|--------|------|---------|
| evolution 执行次数 | manifest.json 中统计 | 被引用 >= 3 次 |
| Human feedback 频率 | 同类问题 feedback 是否减少 | 减少 50% 以上 |
| 认知沉淀质量 | learnings/ 中是否有衍生 learning | 有 >= 1 个关联 learning |

### 4.3 长期检验（收敛质量）

| 检验项 | 方法 | 通过标准 |
|--------|------|---------|
| 收敛后 SKILL.md 完整性 | 新 Agent 重置后能否独立执行 | 无需 Human 额外指导即可正确执行 |
| 收敛损失率 | 收敛过程中是否有 evolution 内容丢失 | 0 丢失 |
| 可读性 | SKILL.md 是否过度膨胀 | 单文件行数 <= 500 行（超限则考虑拆分） |

## 五、智能触发 SED 的具体方案

### 5.1 自检触发器嵌入位置

**当前 SKILL.md 已有自检机制**（第296-313行），但为可选软性提示。智能增强方案将其提升为**强制审计基准**：

```
skill 主工作流（P0-P3 搜索 → 输出报告）
    ↓
【强制】SED 自检触发器（必须在"下一步建议"之前执行）
    ↓
输出"下一步建议"
    ↓
若自检命中 → 在"下一步建议"末尾追加 SED 建议
    ↓
等待 Human 反馈
```

### 5.2 自检与 skill 执行过程的联动

自检不是孤立步骤，而是**贯穿整个 skill 执行过程**的持续观察：

| 执行阶段 | 观察点 | 可能触发的 SED 类型 |
|---------|--------|-------------------|
| P0 树状自说明搜索 | 文档声明 vs 实际执行是否一致 | evolution / gotcha |
| P1 JSON 索引搜索 | 索引与磁盘是否一致 | gotcha |
| P2 docstring 搜索 | 模块注释是否过时 | evolution |
| P3 关键词搜索 | 搜索结果是否完整、是否有遗漏范围 | evolution |
| 搜索后验证 | 命令是否异常、输出是否符合预期 | gotcha / learning |
| 报告输出 | 报告结构是否满足用户需求 | evolution |

### 5.3 与 vaults/ 深度研究的联动

当自检发现的认知具有**跨项目通用性**时，建议分流：

| 认知范围 | 沉淀位置 | 示例 |
|---------|---------|------|
| 仅适用于本 skill | skill/evolutions/ 或 skill/learnings/ | rg-fd-search 的 P0 搜索范围扩展 |
| 适用于多个 skill | vaults/*/wiki/conclusions/ 或 vaults/*/baseline/ | "不硬编码路径"原则（跨所有 skill 适用） |
| 属于项目级工程决策 | references/env-migrations/ | workflow 改造清单 |
| 属于通用架构原则 | vaults/*/wiki/conclusions/ | L1-L5 真源推理链设计 |

**联动方式**：
- skill 本地 SED 记录**具体执行规则**（怎么做）
- vaults/ 深度研究记录**通用原理**（为什么这么做、历史决策脉络）
- 两者通过关联链接互指（如 evolution 中引用 vaults/ 结论文档）

### 5.4 Human 决策权保留（硬性）

无论自检多么确定，Agent **永远**不能自行写入 SED。必须等待 Human 亲口确认：

| Human 反馈 | Agent 动作 |
|-----------|-----------|
| "记一下" / "沉淀一下" / "写到 SED" | 进入标准 SED 落盘流程 |
| "不用" / "跳过" | 在回复中记录自检摘要，不写入磁盘 |
| "先放放" / "以后再说" | 记录自检摘要，标记为"待处理"，不写入 SED |
| 无反馈（静默） | 默认不写入，仅在回复中展示自检结果 |

## 六、反面教材：不执行 SED 自检的后果

| 场景 | 后果 |
|------|------|
| Agent 踩坑后不记录 gotcha | 下次重置后新 Agent 重复踩同一坑 |
| 实际路径优于 SKILL.md 但不记录 evolution | 后续 Agent 继续按次优路径执行 |
| Human 纠偏后不沉淀 learning | 同一认知需要 Human 多次重复解释 |
| evolutions 堆积但不收敛 | SKILL.md 与实际脱节，新 Agent 读 SKILL.md 反而被误导 |

## 七、关联文档

| 文档 | 路径 | 说明 |
|------|------|------|
| SKILL.md SED 加载机制 | `rg-fd-search/SKILL.md` §Skill Self-Evolution 复盘 | 原始自检定义 |
| 当前 manifest | `rg-fd-search/versions/manifest.json` | 指纹索引与演进历史 |
| 不硬编码 baseline | `rg-fd-search/baseline/baseline-no-hardcode-paths.md` | SED 产生的 baseline 示例 |
| vaults/ HITL baseline | `vaults/vault-demo/baseline/baseline-hitl-decision-authority.md` | 跨项目 HITL 决策权基线 |

## 八、版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-08-07 | 初始创建：SED 目标、触发策略（A/B/C）、实现路径、有效性检验、智能触发方案、vaults/ 联动 |
