---
title: workflow-entry-plugins 三层架构选型研究
description: 记录 deploy-git-isolated Python 插件体系从"单脚本"到"多插件"再到"三层架构"的选型演进过程，含反例分析、最终选型理由、workflow-lint-amend-lint.py 案例深度解析。
date: 2026-06-19
meta: {}
---

# workflow-entry-plugins 三层架构选型研究

> **文档性质**：深度研究记录。不是操作手册，而是记录"为什么这样设计"的决策过程。  
> **受众**：后续维护者、新增 workflow 开发者、架构评审。  
> **与 PLUGIN-ARCHITECTURE.md 的区别**：PLUGIN-ARCHITECTURE.md 回答"插件体系怎么工作"；本文回答"为什么要设计成三层、经历了哪些反例、最终选型的理由"。


## 一、问题背景

2026-06-19 session 的原始需求：在 deploy-git-isolated task 下集成一套 Python lint 工具集，覆盖 JSON / PowerShell / Python / Encoding(BOM/CRLF) 四种检测能力。

这个看似简单的需求，触发了一场关于**"调用层如何与能力层交互"**的深层架构讨论。核心问题：

> **当上层需要编排多个底层能力时，应该直接调用能力模块，还是通过统一入口获取能力后再编排？**

这个问题的答案，决定了整个 Python 插件体系是"扁平"还是"分层"，是"紧耦合"还是"可审计"。


## 二、选型演进（三阶段）

### 阶段一：单文件大脚本（直觉方案，未实施）

**思路**：把所有 lint 逻辑写进一个 `lint_all.py`，一次导入、统一扫描、统一报告。

**被否决的原因**：
- 与现有 `py_lib` 插件体系完全脱节，`py-sort-rules.json` 无法管理
- 按需加载不可能（想只检查 JSON 也得加载 PS1 逻辑）
- 其他 task 想复用 JSON lint 得复制代码
- 违反"单一职责"，一个文件同时懂 JSON/PS1/Python/BOM

**结论**：❌ 否决，与现有架构不对齐。


### 阶段二：独立插件 + 直接调用（错误路径，已纠正）

**思路**：每个 lint 类型一个插件文件（`lint_json.py` / `lint_ps1.py` / `lint_python.py` / `lint_encoding.py`），workflow 直接 `import` 所需插件。

**实施过程**：
1. 先写了一个 `workflow-lint-amend-lint.py`，内部直接 `from lint_encoding import validate`
2. 用户指出这是**架构越级**——workflow 层直接触碰 plugin 层，绕过了 `py_lib` 统一入口

**被纠正的原因**：
- 失去 `py_lib` 的统一入口、审计、追踪作用
- `py_lib` 的依赖补齐被绕过（如 `lint_encoding` 依赖 `core` 插件，直接 import 不保证加载顺序）
- `py_lib` 的 registry 注入被绕过（插件无法通过 `__plugin_registry__` 获取 devroot）
- 新增 plugin 时需要改 workflow 代码（直接 import 路径硬编码）

**结论**：❌ 纠正。workflow 禁止直接 import plugin。


### 阶段三：三层架构（最终选型）

**思路**：明确分层——workflow 只编排、py_lib 统一加载、plugins 实现能力。

```
Workflow（py-tools/）    → 步骤编排、逻辑判断、报告输出
    ↓ py_lib.load_plugins()
Entry（py_lib.py）       → 拓扑排序、依赖补齐、registry 注入
    ↓ 动态加载
Plugins（py-plugins/）   → 单一检测/修复能力、暴露 validate() 接口
```

**关键修正**：
- `workflow-lint-amend-lint.py` 删除 `from lint_encoding import validate`
- 改为 `from py_lib import load_plugins` → `registry = load_plugins(...)` → `lint_encoding = registry.lint_encoding`
- 启动时输出 `registry.list_loaded()`，展示底层插件列表

**结论**：✅ 采纳。


## 三、最终选型意图

### 3.1 为什么必须分层

| 维度 | 扁平（workflow 直接 import plugin） | 分层（workflow → py_lib → plugins） |
|------|-------------------------------------|-------------------------------------|
| **入口统一性** | ❌ 每个 workflow 自己决定加载谁 | ✅ 所有 workflow 走同一入口，入口即审计点 |
| **依赖管理** | ❌ 手动维护 import 顺序 | ✅ py_lib Kahn 拓扑排序自动补齐 |
| **能力发现** | ❌ 硬编码 import，新增 plugin 需改 workflow | ✅ py_lib 按 tags/profile 自动筛选，workflow 无感知 |
| **上下文注入** | ❌ plugin 无法获取 devroot（除非自己猜） | ✅ py_lib 将 devroot 注入 registry，plugin 通过 `__plugin_registry__` 访问 |
| **可审计性** | ❌ 执行日志看不出加载了哪些能力 | ✅ `registry.list_loaded()` 输出插件清单，日志即真源 |
| **测试性** | ❌ 直接 import 导致单元测试难以 mock | ✅ 通过 registry 访问，测试时可注入 mock registry |

### 3.2 为什么 workflow 要展示 list_loaded()

这是本次 session 中被用户特别认可的设计点：

> **workflow 启动时输出 `registry.list_loaded()`，展示底层插件列表。**

**价值**：
1. **可审计**：执行日志直接记录"本次执行依赖了哪些能力"
2. **可追踪**：后续 session 不需要猜测"上次到底加载了哪些插件"，看日志即可
3. **可调试**：如果 lint_encoding 行为异常，先检查 list_loaded 里有没有它
4. **边界清晰**：一眼就能判定 workflow 是否越级（如果代码里出现 `from lint_encoding import`，直接判违规）


## 四、反例记录

### 反例 1：直接 import plugin（已纠正）

**错误代码**（workflow-lint-amend-lint.py v1.0）：
```python
# ❌ 越级：workflow 直接 import plugin
_PLUGINS_DIR = Path(__file__).parent.parent.resolve() / "py-plugins"
if str(_PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGINS_DIR))

from lint_encoding import validate  # ← 越级！

result = validate(dir_path=target)
```

**问题**：
- 绕过 `py_lib` 的拓扑排序，`core` 插件可能未加载
- 绕过 `py_lib` 的 registry 注入，`lint_encoding` 无法通过 `__plugin_registry__` 获取 devroot
- `py-sort-rules.json` 中的 profile 筛选失效
- 新增 plugin 时 workflow 需同步修改 import 路径

**纠正后**（workflow-lint-amend-lint.py v2.0）：
```python
# ✅ 合规：workflow 通过 py_lib 统一入口获取能力
from py_lib import load_plugins

registry = load_plugins(devroot=devroot, tags=["lint", "encoding"])
print(f"[workflow] py_lib 已加载插件: {registry.list_loaded()}")

lint_encoding = registry.lint_encoding
result = lint_encoding.validate(dir_path=target)
```

**根因**：Agent 把"快速实现"放在"架构对齐"之上，直接 import 看起来省事，实际上破坏了入口统一性。


### 反例 2：fix-encoding.py 重复实现检测逻辑（已删除）

**错误设计**：单独写一个 `fix-encoding.py`（py-tools/ 下），内部自己实现 BOM/CRLF 检测 + 修复逻辑。

**问题**：
- 与 `lint_encoding.py` 的检测逻辑重复
- 两个文件可能不一致（检测规则改了，修复逻辑没同步）
- `py-sort-rules.json` 无法管理修复工具

**纠正方式**：
- 删除 `fix-encoding.py`
- 将修复能力合并到 `lint_encoding.py`（底座自带 `--fix`）
- workflow 通过 `lint_encoding.validate(fix=True)` 调用修复

**根因**：把"修复"当成独立工具，而不是底座能力的延伸。修复应该是检测能力的子集，不是平行实现。


## 五、案例深度解析：workflow-lint-amend-lint.py

### 5.1 需求

对指定目录执行"检测 → 修复 → 验证"闭环。

### 5.2 错误路径分析

如果采用"直接 import"方式，代码结构：
```python
from lint_encoding import validate  # 越级

# Step 1: 检测
result1 = validate(dir_path=target)
# Step 2: 修复
result_fix = validate(dir_path=target, fix=True)
# Step 3: 再验证
result2 = validate(dir_path=target)
```

**隐患**：
- `validate` 函数内部如果需要 `core` 插件的 `step_header()`，`core` 可能还没加载
- `validate` 如果需要 devroot 做路径解析，但 `__plugin_registry__` 为 None
- 无法通过 `py-sort-rules.json` 控制加载行为

### 5.3 正确路径分析

采用"三层架构"方式：
```python
from py_lib import load_plugins  # 统一入口

# Step 0: py_lib 加载（含拓扑排序、依赖补齐、registry 注入）
registry = load_plugins(devroot=devroot, tags=["lint", "encoding"])
lint_encoding = registry.lint_encoding

# Step 1: 检测（调用底座能力）
result1 = lint_encoding.validate(dir_path=target)

# Step 2: 判断
if result1["violations_found"] > 0:
    # Step 3: 修复（调用底座能力）
    result_fix = lint_encoding.validate(dir_path=target, fix=True)

# Step 4: 再验证（调用底座能力）
result2 = lint_encoding.validate(dir_path=target)
```

**优势**：
- `py_lib` 保证 `lint_encoding` 的依赖（`core`）已先加载
- `py_lib` 保证 `__plugin_registry__` 已注入，plugin 可获取 devroot
- `tags=["lint", "encoding"]` 精确筛选，不加载无关插件
- 启动日志输出 `registry.list_loaded()`，可审计

### 5.4 关键日志输出

```
[workflow] 通过 py_lib 加载 lint_encoding 插件 ...
[workflow] py_lib 已加载插件: ['encoding', 'core', 'lint_encoding', 'lint_json', 'lint_ps1', 'lint_python']

[Step 1] 首次 lint 检测（lint_encoding.validate）
  扫描文件: 80 个
  违规文件: 0 个
  违规项: 0 处
[Step Done] 巡检结论
  ✅ 首次检测即通过，无需修复
```

注意：虽然 workflow 只请求了 `tags=["lint", "encoding"]`，但 `py_lib` 自动补齐了 `core` 和 `encoding` 依赖。`list_loaded()` 完整展示了这个事实，消除了"到底加载了谁"的不确定性。


## 六、设计原则提炼

### 6.1 一句话铁律

> **所有 Workflow 必须通过 `py_lib.load_plugins()` 获取能力，禁止直接 `import` Plugin。越级即违规。**

### 6.2 三层职责口诀

| 层级 | 口诀 |
|------|------|
| **Workflow** | "只编排，不实现；问 py_lib 要能力" |
| **py_lib** | "统一入口，排序加载，注入上下文" |
| **Plugins** | "单一职责，暴露接口，不依赖上层" |

### 6.3 新增 Workflow 的检查清单

```
【Workflow 合规自检】
- 是否直接 import 了 py-plugins/ 下的模块？        是 → ❌ 违规，改道 py_lib
- 是否通过 py_lib.load_plugins() 获取 registry？    否 → ❌ 违规，必须走入口
- 是否在启动时输出 registry.list_loaded()？         否 → ⚠️ 建议补，增强可审计性
- 是否重新实现了 plugin 已有的检测/修复逻辑？      是 → ❌ 违规，复用底座能力
- 是否修改了 py-sort-rules.json 登记新 plugin？     否 → 如是新增 plugin，必须登记
```

### 6.4 与其他架构模式的对比

| 模式 | 典型场景 | 与本文档模式的区别 |
|------|---------|-------------------|
| **直接 import**（反例） | 小型脚本、一次性工具 | 无统一入口、无依赖管理、不可审计 |
| **依赖注入容器**（如 Spring DI） | 大型企业应用 | 本文档的 py_lib 是轻量级版本，无反射、无 AOP，只有拓扑排序和 registry 注入 |
| **管道/流水线**（如 GitHub Actions） | CI/CD | 本文档的 workflow 是"步骤编排"而非"流水线"，每一步都在同一个 Python 进程内调用底座能力 |
| **事件总线**（如 EventEmitter） | 松散耦合模块通信 | 本文档不使用事件驱动，workflow 显式调用 registry 方法，行为可预测 |


## 七、何时可以打破规则

> **原则**：规则存在的目的是防止"默认路径出错"，不是制造教条。

**允许例外的场景**（需用户明确确认）：

1. **纯本地工具脚本**：不进入 py_lib 体系的独立 `.py`（如临时调试脚本），可自由 import。
2. **跨语言调用**：Python workflow 需要调用 PowerShell 插件（如 `github-lib.ps1`），这是体系间的调用，不受 Python 侧 py_lib 约束。
3. **测试代码**：单元测试可直接 import plugin 进行 mock/白盒测试。

**不允许例外的场景**：
- 任何进入 `py-tools/` 的正式 workflow
- 任何被 `TASK-TOOLS-INDEX.md` 登记的脚本
- 任何供 Agent/用户反复调用的工具入口


## 八、关联文档

| 文档 | 用途 | 与本研究的衔接 |
|------|------|--------------|
| `docs/PLUGIN-ARCHITECTURE.md` | 插件化点源架构设计 | 本文回答"为什么要三层"，PLUGIN-ARCHITECTURE 回答"插件体系怎么工作" |
| `task-canonical-baseline.md` 第 8.4 节 | 规范基线中的架构铁律 | 本文是 8.4 节的"研究过程与反例展开" |
| `scripts/py_lib.py` | 统一入口实现 | 本文解释 py_lib 在三层中的位置和价值 |
| `scripts/py-sort-rules.json` | 插件依赖真源 | 本文解释为什么 workflow 依赖 py-sort-rules 而不直接 import |
| `scripts/py-tools/workflow-lint-amend-lint.py` | 本文的案例 | 本文深度解析了它的错误 v1.0 和正确 v2.0 |


*研究文档版本: v1.0*  
*记录时间: 2026-06-19*  
*决策参与者: Human + Agent*  
*下次修订条件: 新增 workflow 类型、py_lib 架构升级、发现新的反例模式*