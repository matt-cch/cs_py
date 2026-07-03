---
title: deploy-git-isolated — 插件化架构与三层模型
description: Python 插件体系三层架构（Workflow → Entry → Plugins）、命名规范、禁止越级调用、插件注册双向铁律、标准文档与实现对齐。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 插件化架构与三层模型

## 8.1 插件化架构概述

本 task 采用 `github-lib.ps1` + `lib-sort-rules.json` + `lib-plugins/` 三层插件化架构：

- **文件名冻结**：插件文件一旦命名，永不再改
- **配置与代码分离**：排序规则用独立 JSON 文件承载，不混在代码目录
- **拓扑排序加载**：Kahn 算法按依赖图自动排序，零文件重名即可插入新插件

> 详细架构说明见：`docs/PLUGIN-ARCHITECTURE.md`


## 8.3 外部工具引用铁律

本 task 执行过程中，以下通用能力**禁止自行实现**，必须调用已登记的外部工具：

| 能力 | 外部工具 | 登记位置 |
|------|---------|---------|
| JSON 语法验证 | `schema/tool/lint-json.py` | `verified-task-index.json` → `lint-json` |
| PS 语法验证 | `schema/tool/lint-ps1.ps1` | `verified-task-index.json` → `lint-ps1` |
| 文件编码检查 | `schema/tool/check-file-encoding.ps1` | `verified-task-index.json` → `check-file-encoding` |
| 文件写入 helper | `schema/tool/file-write-helper.py` | `verified-task-index.json` → `file-write-helper` |
| 时间戳生成 | `schema/tool/get-timestamp.ps1` | `verified-task-index.json` → `get-timestamp` |
| 运行时真源检测 | `references/runtime/verify-runtime.ps1` | `verified-task-index.json` → `verify-runtime` |
| 运行时工具下载 | `references/runtime/download-runtime-tool.py` | `verified-task-index.json` → `download-runtime-tool` |


## 8.4 Python 插件体系三层架构（ workflow → entry → plugins ）

> **来源**：用户与 Agent 在 2026-06-19 对话中共同确认。本节是本次 session 的核心共识沉淀，记录"禁止越级调用"的架构铁律。

### 8.4.1 问题背景

本 task 的 Python 侧已建立 `py_lib.py` + `py-plugins/` + `py-tools/` 体系。但在开发 `workflow-lint-amend-lint.py` 过程中，Agent 曾错误地采用"直接 `import lint_encoding`"的实现方式，被用户判定为**架构越级**——workflow 层直接触碰 plugin 层，绕过了 `py_lib` 统一入口，破坏了入口统一性、审计追踪能力和插件生命周期管理。

本节固化本次讨论后的**正确架构认知**。

### 8.4.2 三层 + 配置契约

> **核心认知**：本架构是**三层主体 + 配置契约**。
> - **Workflow** 负责编排，调用 Entry 前检查配置有效性
> - **Entry** 读取 Config（插件注册表），拓扑排序后加载 Plugins
> - **Plugins** 消费 Config（业务参数）执行具体能力
> - **Config** 不是独立"层"，而是 Entry 和 Plugins 的**输入契约**；其更新来源包括开发时静态编写、异步事件登记、Workflow 前置检查
> - **EXEC-CHEATSHEET** 是 Workflow 编排的命令真源，属于 Layer 3 的组成部件

```
┌───────────────────────────────────────────────────────────────┐
│  Layer 3: Workflow 编排层（py-tools/ + EXEC-CHEATSHEET）      │
│  ──────────────────────────────────────────────────────────   │
│  run-lint.py                    → 全量 lint 聚合             │
│  workflow-lint-amend-lint.py    → 步骤闭环                   │
│  archive_project.py             → scan → compress → verify   │
│  EXEC-CHEATSHEET.md             → 命令速查真源               │
│  （编排：检查配置 → 设计入参 → 调用 Entry；禁止 import plugin）│
└───────────────────────────────────────────────────────────────┘
                    ↓ 调用 py_lib.load_plugins(profile=...)
┌───────────────────────────────────────────────────────────────┐
│  Layer 2: 统一入口层（scripts/py_lib.py）                     │
│  ──────────────────────────────────────────────────────────   │
│  读取 py-sort-rules.json → 拓扑排序 → 依赖补齐 → 注入 registry │
│  （所有调用的唯一网关；禁止被绕过）                           │
└───────────────────────────────────────────────────────────────┘
                    ↓ 动态加载 + 传递 Config
┌───────────────────────────────────────────────────────────────┐
│  Layer 1: 能力底座层（py-plugins/）                           │
│  ──────────────────────────────────────────────────────────   │
│  lint_encoding.py · lint_json.py · lint_ps1.py               │
│  archive_config.py · archive_scanner.py · archive_compressor │
│  （单一职责，暴露标准化接口；消费 archive-groups.json 等）    │
└───────────────────────────────────────────────────────────────┘

         ╔═══════════════════════════════════════════════════════╗
         ║  Config 契约（*.json）— Entry 与 Plugins 的输入       ║
         ║  py-sort-rules.json  → 插件注册、依赖图、profile      ║
         ║  archive-groups.json → 分组策略、黑白名单             ║
         ║  task-config.json    → 任务参数、路径、场景映射       ║
         ║  （配置与代码分离；来源：开发编写 / 异步登记 / WF 检查）║
         ╚═══════════════════════════════════════════════════════╝
```

### 8.4.3 各层职责边界

| 层级 | 文件位置 | 职责 | 禁止行为 |
|------|---------|------|---------|
| **Workflow** | `py-tools/*.py` + `EXEC-CHEATSHEET.md` | 步骤编排、env 管理、报告输出；**检查配置有效性**；按速查表/schema 设计入参；调用 Entry | ❌ 禁止直接 `import` plugin；❌ 禁止重新实现检测逻辑 |
| **Entry** | `py_lib.py` | 读取 py-sort-rules.json（插件注册表）、拓扑排序、依赖补齐、registry 注入、profile 筛选、动态加载 Plugins | ❌ 禁止混入业务逻辑；❌ 禁止被绕过 |
| **Plugins** | `py-plugins/*.py` | 单一检测/修复/压缩/扫描能力、暴露标准化接口；消费业务 Config（如 archive-groups.json） | ❌ 禁止依赖 workflow 上下文；❌ 禁止直接读写配置文件 |
| **Config** | `*.json` | 插件注册契约、分组策略、任务参数 | ❌ 禁止嵌入可执行逻辑；不是独立"层"，是 Entry 和 Plugins 的输入 |

### 8.4.4 架构验证案例：archive_project.py 改造

> **来源**：用户与 Agent 在 2026-06-21 对话中确认。本节是 8.4.3 四层架构的**实证检验**，证明已有 workflow 必须回迁入四层模型。

**问题**：`archive_project.py` 原实现采用"直接 import plugin"的越级模式：
```python
# ❌ 违规：Layer 4 直接触碰 Layer 1，绕过 Layer 3 + Layer 2
sys.path.insert(0, str(_plugins_dir))
from archive_config import get_group_config, find_7z_exe
from archive_scanner import scan_group
from archive_compressor import compress_group
```

**改造后（合规）**：
```python
# ✅ 合规：Layer 4 只通过 Layer 3 (py_lib) 获取能力
from py_lib import load_plugins
registry = load_plugins(devroot=str(devroot), profile="archive")

cfg = registry.archive_config.get_group_config(group_name, devroot)
scan_result = registry.archive_scanner.scan_group(cfg)
compress_result = registry.archive_compressor.compress_group(cfg, seven_zip, fmt, force)
```

**关键收益**：
- `py_lib` 按 `py-sort-rules.json` 自动加载 `archive_config` → `archive_scanner` / `archive_compressor` 的依赖链
- `archive_config` 读取 `archive-groups.json` 获取黑白名单配置（配置与代码分离）
- workflow 只编排 scan → compress → verify 三阶段，不触碰任何底层实现

### 8.4.5 铁律：禁止越级调用

> **一句话**：Workflow 禁止直接 `import` Plugin。所有能力必须通过 `py_lib.load_plugins()` 获取。

**错误示范（已纠正）**：
```python
# ❌ 越级：workflow 直接 import plugin
from lint_encoding import validate
result = validate(dir_path=target)
```

**正确示范**：
```python
# ✅ 合规：workflow 通过 py_lib 统一入口获取能力
from py_lib import load_plugins
registry = load_plugins(devroot=devroot, tags=["lint", "encoding"])
lint_encoding = registry.lint_encoding
result = lint_encoding.validate(dir_path=target)
```

### 8.4.6 铁律延伸：文档层面也不暴露插件文件名

> **来源**：用户与 Agent 在 2026-06-20 对话中共同确认。本节是 8.4.5「禁止越级调用」的自然延伸。

**问题**：即使代码层面禁止了 `import plugin`，如果人类速查表（如 `TASK-TOOLS-INDEX.md`）以静态表格形式列出每个插件的文件名、路径和职责，上层调用者（包括 Agent 和人类开发者）仍会**按图索骥**，直接 `import` 或引用具体插件文件，导致越级调用在文档的「诱导」下持续发生。

**判定标准**：
- ❌ 违规：在索引/速查表中直接列出 `lint_json.py`、`md_lint.py` 等具体插件文件名，形成「可用的插件清单」
- ✅ 合规：只说明「有哪些能力类别」（如 JSON lint / Markdown frontmatter 校验 / 编码检测），插件发现通过入口 API 动态获取

**正确示范（文档写法）**：
```markdown
**可用能力**（由 `py_lib` 插件体系动态提供）：

lint 体系覆盖 JSON / PowerShell / Python / Encoding / Markdown / Link 等验证。
具体有哪些插件可用、各自的标签与职责，**通过入口 API 动态发现**。

```python
# 发现全部可用插件（正规入口）
from py_lib import list_plugins
for p in list_plugins():
    print(f"{p['name']}: {p['description']} (tags: {p['tags']})")
```

> **铁律**：插件清单的唯一真源是 `py-sort-rules.json`（机器可读）。人类速查表只说明「有哪些能力类别」，不列出具体插件文件名。
```

**错误示范（已纠正）**：
```markdown
| 插件 | 标签 | 职责 | 状态 |
|------|------|------|------|
| `lint_json.py` | `lint`, `json` | JSON 语法验证 | ready |
| `md_lint.py` | `md`, `validation` | Markdown frontmatter 校验 | ready |
```

### 8.4.7 工具命名规范：workflow- 与 atomic- 前缀，及 Phase / Atomic / Workflow 边界

> **来源**：用户与 Agent 在 2026-06-22 对话中共同确认。本节固化 `py-tools/` 目录下脚本文件的分层命名契约，以及 Atomic、Phase、Workflow 三者的语义边界。

**问题 1**：`py-plugins/security_audit.py` 与 `py-tools/security-audit.py` 同名（仅下划线 vs 连字符差异），造成维护混淆，Agent 和人类都容易搞混哪一个是插件、哪一个是入口。

**问题 2**：一个 Workflow 如果全部由 Phase 组成（没有调用任何 Atomic 脚本），是否还配叫 Workflow？

**命名铁律（文件系统层面）**：

| 层级 | 文件位置 | 命名格式 | 示例 |
|------|---------|---------|------|
| **Plugin** | `py-plugins/*.py` | 下划线蛇形，`{domain}_{capability}.py` | `security_audit.py`, `lint_json.py` |
| **Workflow Tool** | `py-tools/workflow-*.py` | `workflow-{verb}-{slug}.py`，kebab-case | `workflow-security-audit.py`, `workflow-deploy-full.py` |
| **Atomic Tool** | `py-tools/atomic-*.py` | `atomic-{verb}-{slug}.py`，kebab-case | `atomic-generate-ai-summary.py`, `atomic-fetch-issue.py` |

**语义区分（架构层面）**：

| 概念 | 定义 | 是否可独立运行 | 判断标准 |
|------|------|---------------|---------|
| **Atomic** | 独立可执行的最小单元 | ✅ 是 | `python atomic-xxx.py` 即可运行，输出自包含，可被多个 Workflow 复用 |
| **Phase** | Workflow 内部的逻辑分段 | ❌ 否 | 脱离 Workflow 上下文无意义，通常没有自己的 CLI 入口 |
| **Workflow** | 编排多个 Phase（其中一些可能调用 Atomic） | ✅ 是 | 有阶段流转（phase1 → phase2 → ...）、条件判断、报告聚合 |

**关键判定原则**：

1. **Atomic 的充要条件**：单一职责 + 可独立运行 + 可复用。
2. **Workflow 的充要条件**（满足任一）：
   - 组装 ≥2 个 Atomic
   - 组装 ≥1 个 Atomic + ≥1 个不可独立运行的 Phase
   - **内部有明确的阶段编排（≥2 个 Phase），即使全部 Phase 都直接调用 Plugin**
3. **Phase ≠ Atomic**：Phase 是 Workflow 的"内部步骤"，不可独立运行。即使某个 Phase 只调用一个 Plugin，只要它没有独立的 CLI 入口和自包含输出，就不是 Atomic。

**实例对照**：

| 脚本 | 类型 | 理由 |
|------|------|------|
| `generate-ai-summary.py` | **Atomic** | 独立可运行：`python atomic-generate-ai-summary.py --devroot ...` 即可生成摘要并落盘 |
| `workflow-deploy-full.py` | **Workflow** | 组装 step-04~09（其中 step-09 是 atomic-fetch-issue 的调用）+ 条件判断 + 报告聚合 |
| `workflow-security-audit.py` | **Workflow**（方案 A） | 5 个 Phase 直接调用 `security_audit` plugin，无 Atomic 组装，但有明确的阶段编排和报告聚合 |

**方案 A 决策（2026-06-22 确认）**：

> `workflow-security-audit.py` 保持为 Workflow，不强行拆分 Atomic。
> 
> 理由：
> 1. 5 个 Phase 中真正能独立运行的只有 Phase 1/4，但它们单独运行意义有限（人工复核 Phase 2/3 不可跳过）
> 2. 安全审计的核心价值是"五 Phase 完整流程"，不是某个单 Phase
> 3. 过度拆分会降低可维护性
> 
> **例外触发条件**：若未来某个 Phase 被多个 Workflow 复用（如 `scan-patterns` 被 lint workflow 也用），则提取为 `atomic-scan-patterns.py`。

**禁止行为**：
- ❌ `py-plugins/foo.py` + `py-tools/foo.py`（同名，任何变体）
- ❌ `py-tools/foo.py` 直接 import `py-plugins/foo.py`（越级调用，见 8.4.5）
- ❌ 在 `py-tools/` 下使用与 `py-plugins/` 相同的下划线命名（如 `security_audit.py`）
- ❌ 把不可独立运行的 Phase 错误命名为 `atomic-xxx.py`（名称承诺与实际能力不符）

### 8.4.8 产出文件默认落盘到 `venv/tmp/`

> **来源**：用户与 Agent 在 2026-06-22 对话中共同确认。

**规则**：任何脚本（workflow / atomic / plugin 的 CLI 入口）生成的**产出文件**（报告、日志、中间产物），若用户**没有显式指定输出路径**，默认落盘到 `${devroot}/venv/tmp/`。

**原因**：
1. `venv/` 已在 `.gitignore` 中，产出文件不会被意外提交到 GitHub
2. `tmp/` 是公认的临时目录，用户清楚里面的内容可被随时清理
3. 避免 task 目录被中间产物污染，保持仓库整洁

**实现要求**：

| 场景 | 行为 | 示例 |
|------|------|------|
| 用户显式传 `--output /path/to/file.json` | 写到指定路径 | `--output out/audit.json` → `out/audit.json` |
| 用户未传 `--output` | 自动写到 `venv/tmp/{script-name}-{timestamp}.{ext}` | 无参数 → `venv/tmp/security-audit-report-20260622-094202.json` |
| 用户传 `--output-dir /custom/dir` | 在该目录下自动生成文件名 | `--output-dir debug/` → `debug/security-audit-report-20260622-094202.json` |

**禁止行为**：
- ❌ 默认写到 task 根目录或 `scripts/` 子目录（可能被 git 追踪）
- ❌ 默认覆盖已有文件（应使用时间戳或序号避免冲突）

### 8.4.9 案例讲解：workflow-lint-amend-lint.py 的正确实现

**需求**：对指定目录执行"检测 → 修复 → 验证"闭环。

**错误路径（第一次实现）**：
1. workflow 直接 `import lint_encoding`
2. 直接调用 `lint_encoding.validate()`
3. 问题：绕过 `py_lib`，失去统一入口的审计、追踪、依赖管理

**正确路径（修正后）**：
1. workflow `from py_lib import load_plugins`
2. `registry = load_plugins(devroot=..., tags=["lint", "encoding"])`
3. `lint_encoding = registry.lint_encoding`
4. Step 1: `lint_encoding.validate(dir_path=target)` → 检测
5. Step 2: `lint_encoding.validate(dir_path=target, fix=True)` → 修复
6. Step 3: `lint_encoding.validate(dir_path=target)` → 再验证
7. 输出闭环报告

**关键收益**：
- `py_lib` 自动处理 `lint_encoding` 的依赖（如 `core` 插件）
- `py_lib` 自动按 `py-sort-rules.json` 拓扑排序加载
- `py_lib` 将 `devroot` 注入 registry，plugin 可通过 `__plugin_registry__` 访问
- 新增 plugin 只需登记 `py-sort-rules.json`，workflow 无需改代码

### 8.4.10 扩展新 workflow 的标准模板

```python
#!/usr/bin/env python3
"""
workflow-<name>.py — <描述>
标签：py-tools

职责：通过 py_lib 统一入口加载所需插件，完成 <workflow 目标>。
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).parent.parent.resolve()
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from py_lib import load_plugins


def main():
    # 1. 通过 py_lib 获取能力（禁止直接 import plugin）
    registry = load_plugins(devroot=devroot, tags=["<tag1>", "<tag2>"])
    plugin = registry.<plugin_name>

    # 2. 编排 workflow 步骤
    # ...


if __name__ == "__main__":
    main()
```

### 8.4.11 插件间通信规则：同层插件允许直接 import

> **来源**：用户与 Agent 在 2026-06-21 对话中共同确认。本节是 8.4.5「禁止越级调用」的边界补充，明确"禁止越级"不等于"禁止插件间协作"。

**核心规则**：

| 通信方向 | 是否允许 | 理由 |
|---------|---------|------|
| Workflow → Plugin | ❌ 禁止 | 必须经 py_lib 统一入口，保持入口唯一性 |
| Plugin → Plugin（同层） | ✅ 允许 | 不暴露给 Workflow，属于底座层内部通信 |
| Plugin → Workflow | ❌ 禁止 | 插件禁止反向依赖上层 |

**判定标准**：
- **是否暴露给 Workflow**：如果 Plugin A 直接 import Plugin B，而 Workflow 完全不知道这个调用关系，则属于同层通信，许可。
- **是否破坏入口统一性**：同层 import 不涉及 py_lib 入口，不破坏 workflow → entry → plugin 的单向调用链。

**正确示范**：
```python
# archive_scanner.py (Plugin) 直接 import archive_empty_handler.py (Plugin)
# ✅ 合规：同层通信，不暴露给 workflow
from archive_empty_handler import (
    cleanup_emptydirs,
    detect_empty_dirs,
    detect_zero_byte_files,
    fill_emptydirs,
    write_detail_list,
)

def scan_group(cfg):
    # ... 扫描逻辑 ...
    empty_dirs = detect_empty_dirs(entries)  # 调用同层插件能力
    fill_emptydirs(empty_dirs, src, arcname)  # 调用同层插件能力
```

**错误示范**：
```python
# ❌ 违规：workflow 直接 import plugin（越级）
from archive_empty_handler import detect_empty_dirs
```

**边界说明**：
- 同层 import 必须是"按需、最小化"的：Plugin A 只 import Plugin B 中它需要的函数，不 import 整个模块。
- 如果同层通信涉及多个插件的复杂编排，应评估是否需要将逻辑上提到 Entry 层或拆分为新的独立插件。

### 8.4.12 插件注册双向铁律（禁止孤儿文件与孤儿注册）

> **来源**：用户与 Agent 在 2026-07-03 对话中共同确认。本节是 8.4 节「三层架构」的完整性补充，防止"文件在磁盘但 registry 不认识"或"registry 有登记但磁盘无文件"的双向不一致。

**核心原则**：`py-plugins/` 目录与 `py-sort-rules.json` 注册表必须**严格一一对应**，任何方向的 orphan（孤儿）都是架构缺陷。

**铁律**：

| 方向 | 规则 | 违反后果 |
|------|------|---------|
| **磁盘 → 注册表** | `py-plugins/` 下的每个 `.py` 文件（除 `__init__.py` 外）**必须**在 `py-sort-rules.json` 中注册 | 该文件成为"隐形插件"——registry 不加载它，但它可能通过目录扫描或同层 import 被偶然发现，破坏统一入口原则 |
| **注册表 → 磁盘** | `py-sort-rules.json` 中注册的每个插件**必须**在 `py-plugins/` 目录下有对应的 `.py` 文件 | `load_plugins()` 执行时 import 失败，抛出 RuntimeError，workflow 崩溃 |
| **命名一致性** | 注册表的 `module` 字段必须与磁盘文件名一致（不含 `.py` 扩展名） | import 失败或加载到错误模块 |

**判定方法**：
```python
# 正规入口：通过 py_lib 自检发现不一致
from py_lib import list_plugins
import os

registered = {p["module"] for p in list_plugins()}
disk = {f[:-3] for f in os.listdir("py-plugins/") if f.endswith(".py") and f != "__init__.py"}

orphan_files = disk - registered      # 磁盘有但注册表无 → 需补注册
orphan_regs = registered - disk       # 注册表有但磁盘无 → 需删注册或补文件
```

**正确示范（补注册）**：
```json
// py-sort-rules.json 追加
{
  "name": "archive_empty_handler",
  "module": "archive_empty_handler",
  "depends": [],
  "tags": ["archive", "core"],
  "description": "空目录与零字节文件处理器"
}
```

**错误示范（已纠正）**：
```
磁盘: py-plugins/archive_empty_handler.py 存在
注册表: py-sort-rules.json 中无此条目
→ 结果：archive_scanner.py 直接 import 它，绕过 py_lib，形成隐性依赖
```

**修订联动**：
- 新增/删除/重命名 `py-plugins/*.py` → **必须**同步更新 `py-sort-rules.json`
- 修改 `py-sort-rules.json` → **必须**验证对应 `.py` 文件存在
- 两者任一改版 → 执行 `py_lib.py` 自检确认零 orphan

### 8.4.13 修订联动

新增/修改 workflow 时，必须同步更新：

| 联动文件 | 更新内容 |
|---------|---------|
| `EXEC-CHEATSHEET.md` | 新增 workflow 调用命令示例 |
| `TASK-TOOLS-INDEX.md` | 在 CLI 入口表登记新 workflow |
| `README.md` | 文件导航表和当前状态表追加 |
| `py-sort-rules.json` | 如需新增 plugin，登记插件定义和 profile |

### 8.4.14 Layer 3 内部细分：原子型 vs 编排型

> **来源**：用户与 Agent 在 2026-06-21 对话中共同确认。本节是 8.4 节「三层架构」的边界补充，明确 Layer 3（py-tools/）内部的两档形态差异。

**核心认知**：py-tools/ 下的脚本**全部属于 Layer 3**，但形态和引用方式截然不同，必须区分：

| 维度 | 原子型 Workflow（Atomic Tool） | 编排型 Workflow（Orchestration Script） |
|------|------------------------------|----------------------------------------|
| **定位** | 封装单一原子操作，可被上层引用 | 串联多步骤的完整剧本，顶层入口 |
| **职责** | 只做一件事，输出标准化 | 完成一个完整目标，含步骤编排 |
| **被引用** | ✅ 可被其他 Workflow 通过 subprocess 调用 | ❌ 禁止被引用，避免流程嵌套 |
| **副作用** | 无或可控 | 通常有不可逆副作用（push、压缩） |
| **JSON 配置** | 通常 **不配**（参数驱动） | 步骤可能变动时 **必须外化** |
| **范例** | `get-timestamp.py`、`run-lint.py`、`fetch_issue.py` | `workflow-deploy-full.py`、`archive_project.py` |

**铁律**：
1. 编排型 Workflow 禁止被其他 Workflow 引用。
2. 原子型 Workflow 通过 subprocess 调用，禁止 import，保持层间隔离。
3. JSON 配置只给"数据会变、代码不想变"的场景配。

> 详细决策逻辑与范例见：`docs/patterns/atomic-vs-orchestration-workflow.md`


## 8.5 标准文档与实现代码的真源对齐原则

> **来源**：用户与 Agent 在 2026-06-20 对话中共同确认。本节解决「标准文档 vs 实现代码不一致时以谁为准」的裁决问题。

### 8.5.1 问题背景

本 task 存在多组「标准文档 + 实现代码」的配对关系：

| 标准文档（What：规则是什么） | 实现代码（How：如何检测/执行） |
|---------------------------|------------------------------|
| `.cursor/rules/markdown-docs-format.mdc` | `md_lint.py` |

此前未明确两者的主从关系，导致 Agent 在修改时可能：
- 只改实现代码，不同步标准文档 → 标准过期
- 只改标准文档，不同步实现代码 → 实现与标准脱节
- 实现代码自行扩展规则 → 标准文档失去唯一真源地位

### 8.5.2 铁律：标准文档是唯一真源

**层级定义**：
- **标准文档**（如 `.mdc` 规则文件）：人类可读的真源标准，定义「应该是什么」
- **实现代码**（如 `.py` 插件）：标准文档的**忠实实现**，定义「如何检测/执行」

**裁决规则**：
1. **标准 vs 实现不一致 → 以标准文档为准，修正实现代码**
2. **实现代码发现标准文档未覆盖的边界 → 先修订标准文档，再同步实现**
3. **禁止实现代码自行扩展规则而不更新标准文档**

**错误示范（已纠正）**：
```python
# md_lint.py 自行增加 frontmatter 字段检测
# 但 markdown-docs-format.mdc 中未定义该字段
# → 实现超前于标准，形成双轨制
```

**正确示范**：
```markdown
# Step 1: 修订标准文档（markdown-docs-format.mdc）
# 新增 meta 必填字段、description/date 拼接禁忌

# Step 2: 同步实现代码（md_lint.py）
# 按 mdc 新增的规则实现对应检测逻辑

# Step 3: 双向验证
# mdc 描述的规则 ↔ md_lint 实现的校验 ↔ 实际扫描结果 三者一致
```

### 8.5.3 应用到本 task

| 标准文档 | 实现代码 | 同步检查清单 |
|---------|---------|------------|
| `.cursor/rules/markdown-docs-format.mdc` | `md_lint.py` | mdc 中每条规定是否有对应的检测逻辑？md_lint 的每个检测项是否在 mdc 中有出处？ |

**修订联动触发条件**：
- 修改 `markdown-docs-format.mdc` → **必须**检查 `md_lint.py` 是否需要同步更新
- 增强 `md_lint.py` 检测能力 → **必须**检查 `markdown-docs-format.mdc` 是否需要补充规则定义
- 两者任一改版 → 在 `md_lint.py` 的 docstring 中更新版本号，并注明「与 mdc X.X 对齐」


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
