---
title: deploy-git-isolated — 人机协同边界与分工
description: 确定性事务由配置/代码/schema/rule/workflow/pipeline 按规范执行；概率性事务才由 Agent 临场判断。明确 Agent 在什么场景下是"执行者"、什么场景下是"决策者"。
date: 2026-07-24
meta:
  version: "1.0.0"
  source: 用户明确确认（2026-07-24 session）
---

# 人机协同边界与分工

> **核心原则**：Agent 不是万能的决策者。凡是项目中已有**确定性规范**（配置、代码、schema、rule、workflow、pipeline）覆盖的事务，Agent 的角色是**忠实执行者**；只有在规范未覆盖的**概率性/不确定性**地带，Agent 才动用自身的判断能力，按约定规则执行。
>
> **违反后果**：Agent 用自身概率推断覆盖确定性规范，视为**严重操作事故**——因为它破坏了"可预期、可复现、可审计"的工程基础。


## 9.1 两类事务的区分

### 9.1.1 确定性事务（Deterministic）

**定义**：有明确、唯一的正确答案，且该答案已被项目中的某个真源文件**明文规定**。

| 真源类型 | 示例 | Agent 角色 |
|---------|------|-----------|
| **配置文件** | `.env`、`git-security.json`、`task-config.json` | 读取 → 按值执行，不质疑、不覆盖 |
| **Schema/规则** | `plugin-result-schema.json`、`.cursor/rules/*.mdc` | 遵守 → 按约束执行，不自行扩展 |
| **Workflow/Pipeline** | `workflow-deploy-full.py`、`SOP.md` 中的 Step 契约 | 编排 → 按既定步骤执行，不临场改顺序 |
| **代码逻辑** | `atomic-deploy-preflight.py` 中的分支判定 | 消费 → 调用脚本获取结果，不自行重算 |
| **Baseline** | 本目录下全部 `.md` 文件中的铁律条款 | 遵守 → 直接执行，不重新推理 |

**行为红线**：
- ✅ 读取真源 → 按真源执行
- ❌ 读取真源 → "我觉得应该不一样" → 按自己的判断执行
- ❌ 不读取真源 → "凭常识判断" → 直接执行

### 9.1.2 概率性事务（Probabilistic）

**定义**：没有唯一正确答案，或规范确实未覆盖，需要基于上下文做权衡判断。

| 场景 | 示例 | Agent 行为 |
|------|------|-----------|
| 规范未覆盖的异常处理 | workflow 返回未预料的错误码 | 分析日志 → 判断是入参问题还是 workflow 缺陷 → 修入参或修 workflow |
| 用户需求模糊 | 用户说"优化一下"但没给标准 | 基于既有模式提出假设 → 与用户确认 |
| 多规范冲突 | 两个 mdc 规则同时命中但结论矛盾 | 按 trigger-index 的冲突裁决规则执行，或向用户请示 |
| 外部信息缺失 | 网络不通，需判断重试还是切换代理 | 基于历史 gotcha 和 retry 策略临场决策 |


## 9.2 反例：git-security.json 的权限判定

> **本节是确定性规范覆盖 Agent 判断的典型案例。**

### 9.2.1 错误做法（已发生）

Agent 在操作 `cs_py`（devroot）时，基于以下**概率推断**：
- "cs_py 是我自己的项目"
- "devroot 属于 personal 级别"
- "personal repo 的写操作应该允许"

于是未读取 `git-security.json`，直接判断"可以 push"，结果：
- `cs_py` 的 `git-security.json` 中 `security_level="strict"`、`allow_direct_push_to=[]`
- 实际上 **任何分支禁止直接 push**
- 若执行了 push，将被 remote reject，或更糟——若仓库设置了分支保护，会留下失败记录

### 9.2.2 正确做法

Agent 在操作任何仓库前：
1. **无条件读取** target 目录下的 `git-security.json`
2. **无条件调用** `atomic-deploy-preflight.py`（它内部会读取并判定）
3. **以脚本输出的判定结果为准**，不以自己的"常识"覆盖

```python
# workflow 中的正确路径（确定性）
result = subprocess.run([
    python_exe, "atomic-deploy-preflight.py",
    "--devroot", str(devroot),
    "--target", str(target)
], capture_output=True, text=True)

# 以 returncode 和 stdout 中的 [OK]/[WARN]/[FAIL] 为准
# 不加入自己的 if "我觉得这是 personal repo": 判断
```

### 9.2.3 核心教训

| 维度 | 错误认知 | 正确认知 |
|------|---------|---------|
| 权限来源 | Agent"判断"仓库性质 | **`git-security.json` 自声明** |
| `cs_py` 权限 | "Personal 所以允许" | `security_level="strict"` + `allow_direct_push_to=[]` → **禁止** |
| 判定时机 | Agent 临场推断 | `atomic-deploy-preflight.py` Step 0b **强制读取并判定** |
| 执行依据 | Agent 常识 | **目标仓库的确定性配置** |

> **一句话**：即使 Agent 100% "确信"某个仓库是 personal 性质，只要该仓库的 `git-security.json` 写了 `allow_direct_push_to=[]`，**push 就是禁止的**。Agent 的判断权在确定性规范面前为零。


## 9.3 Agent 行为决策树

```
接到任务指令
    ↓
是否存在覆盖该任务的确定性规范？
    ├── ✅ 是（配置/schema/rule/workflow/baseline 已定义）
    │       ↓
    │   【执行者模式】
    │   - 读取真源
    │   - 按真源执行
    │   - 输出结果
    │   - 不加入自己的 if/else 覆盖
    │       ↓
    │   执行完成后 → 真源是否需要更新？
    │       ├── 是 → 走修订联动流程 → 更新真源
    │       └── 否 → 结束
    │
    └── ❌ 否（规范未覆盖，属于灰色地带）
            ↓
        【决策者模式】
        - 基于既有模式、gotcha、经验做概率推断
        - 提出假设或方案
        - 向用户确认（Human-in-the-Loop）
        - 执行 → 沉淀到真源（若发现可固化的模式）
```


## 9.4 与现有 baseline 的衔接

| 现有条款 | 与本节的关系 |
|---------|------------|
| `baseline-principles.md §0.6` Workflow 自闭环 | Workflow 是确定性规范的典型形态——Agent 只构造入参，不干预步骤 |
| `baseline-principles.md §0.7` 显式优于隐含 | 确定性规范本身就是"显式"的最高形态 |
| `baseline-principles.md §0.8` 仓库性质分级 | 该分级是**建议性原则**，`git-security.json` 是**执行真源**；当二者冲突时，后者优先 |
| `baseline-audit-truth.md §8.10` 决策真源集中化 | 确定性规范就是"决策真源"——Agent 只消费，不做二次判断 |
| `baseline-workflow-deploy.md §8.7.6` Polyrepo 部署架构 | `git-security.json` 的读取和消费是确定性规范的落地实例 |


## 9.5 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-07-24 | 初始创建：确定性 vs 概率性分工、git-security 反例、Agent 决策树 |
