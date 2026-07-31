---
name: docstring-quality-harness
description: 通过委派 subagent 模拟陌生 Agent 初次接触工具的场景，检验工具 docstring 的自说明质量，输出审计 manifest 并渐进式积累 docstring 质量 baseline。触发词：测试工具文档、检验 docstring、工具自说明测试、验证工具用法说明、工具文档质量、文档质量巡检、docstring baseline。
---

# 工具文档自说明质量测试 Harness

## 本质

本 skill 不是单纯的"命令行审计"，而是**以 subagent 为探针，以 docstring 为被测对象，以 baseline 为进化目标**的质量保障体系。

核心命题：当 Agent 在 `/new` 后首次接触某个工具，仅凭其 docstring（模块注释、参数表、调用示例），能否在不依赖外部记忆的前提下，准确构建出可执行的命令行？

## 长期目标

通过多次反复测试，**渐进式地得出一套 docstring quality baseline**，作为后续自定义 toolchains 文档规范的**基准评价巡检判断标准**，达到迭代优化升级的目标。

每次测试的审计结论都会被纳入 baseline，形成可对比、可量化的演进轨迹。

## 目录结构

本 skill 遵循标准目录约定：

```
docstring-quality-harness/
├── SKILL.md                          # 核心规范（本文件）
├── README.md                         # 目录结构与导航
├── schema/                           # 数据契约（JSON Schema）
│   └── audit-manifest-schema.json
├── baseline/                         # 渐进式质量基准
│   └── docstring-quality-baseline.md
└── examples/                         # 示例文件
    └── example-audit-manifest.json
```

| 子目录 | 职责 | 更新时机 |
|--------|------|---------|
| `schema/` | 存放 Audit Manifest 的 JSON Schema 定义，约束输出格式 | manifest 结构扩展时 |
| `baseline/` | 存放渐进式积累的质量评价基准，记录评价维度、评分标准、已知问题 | 每次测试发现新问题时追加 |
| `examples/` | 存放示例文件，供 Agent 和人类理解输出格式 | 新增典型测试场景时 |

## 触发词

| 类别 | 触发词 |
|------|--------|
| 单次测试 | "测试工具文档"、"检验 docstring"、"工具自说明测试"、"验证工具用法说明" |
| 质量巡检 | "工具文档质量"、"文档质量巡检"、"docstring 巡检" |
| baseline | "docstring baseline"、"文档基线"、"更新文档质量基准" |

> **触发条件索引**：本文档中的触发条件受 `verified-trigger-index.json` 统一管理。索引真源：`${devroot}/references/runtime/verified-trigger-index.json`

## 单次测试流程（Dry-Run 探针）

### Step 1: 选定被测工具

用户显式指定或从当前任务上下文推断目标工具脚本路径（`.py` / `.ps1` 等可执行脚本）。

### Step 2: 委派 Subagent（零上下文注入）

向 subagent 发送的 prompt **必须是普通用户视角**，禁止包含以下信息：
- 禁止告知"这个参数是必填的""示例漏了某个参数"等外部理解
- 禁止提前纠正 docstring 中的已知问题
- 禁止给 subagent 任何超出 docstring 本身的信息

**标准 prompt 模板**：

```
你是 OpenCode Agent，当前工作目录是 {devroot}。

用户提出了这个需求：

---
用 {tool_relative_path} 做 {用户意图描述}，帮我构造正确的命令行。
---

**你的任务**：
1. 读取脚本文件 {tool_absolute_path} 的内容。
2. 根据脚本自身的文档，自行判断如何构造正确的命令行。
3. **只构建命令行，不执行任何命令**。
4. 在最终回复中，必须同时输出：
   - 你构建的完整命令行
   - 你的判断理由（逐条说明你为什么要传哪些参数、引用了文档中的哪句话作为依据）

**注意**：你没有其他上下文，只能依据脚本文件本身的内容来判断。不要假设任何未写入脚本文档的信息。
```

### Step 3: 收集 Subagent 输出

收集以下信息：
- `subagent_command_line`: subagent 构建的命令行
- `subagent_reasoning`: subagent 的判断理由（逐条）
- `docstring_quotes`: subagent 引用的 docstring 原文摘录

### Step 4: 审计员比对（当前 Agent 执行）

当前 Agent 作为审计员，独立阅读同一工具的 docstring，构建自己认为的"正确命令行"（`expected_command_line`），然后与 subagent 的输出比对。

**审计维度**（见 `baseline/docstring-quality-baseline.md`）：

| 维度 | 检查项 |
|------|--------|
| **必填性一致性** | 参数表标记的"必填/可选"是否与代码 `required=True/False` 一致 |
| **示例完整性** | 调用示例是否覆盖了所有必填参数 |
| **默认值准确性** | 参数表中的默认值是否与代码 `default=` 一致 |
| **描述清晰性** | 参数说明是否足以让陌生 Agent 理解其用途和约束 |
| **路径显式性** | 示例是否使用绝对路径、是否包含 `--devroot`/`--target` 等多端参数 |

### Step 5: 生成 Audit Manifest

按 `schema/audit-manifest-schema.json` 格式输出 JSON manifest。

### Step 6: 更新 Baseline

将本次发现的共性问题、改进建议、评价维度调整建议，追加到 `baseline/docstring-quality-baseline.md`。

## 输出产物

| 产物 | 路径 | 说明 |
|------|------|------|
| Audit Manifest | 由 `atomic-get-manifest-path.py` 决定 | 单次测试的完整记录 |
| Baseline | `baseline/docstring-quality-baseline.md` | 渐进式积累的质量基准 |

## 与现有体系的衔接

- **真源检测**：被测工具的 docstring 变更后，应重新执行本 skill 进行回归测试
- **版本记录**：docstring 质量 baseline 的迭代历史可记入 task changelog
- **规范基线**：本 skill 产出的 baseline 可反哺 `baseline/baseline-principles.md` 的文档规范章节
