---
title: deploy-git-isolated — 审计机制、真源治理与决策集中化
description: Trigger 治理、外部工具引用铁律、独立审计机制（审计者不能审计自己）、决策真源集中化原则（下游只消费、不判断）。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# 审计机制、真源治理与决策集中化

## 8.2 Trigger 治理

本 task 的 trigger 索引遵循全局 `verified-trigger-index.json` 的治理规则：

- **新增三步流程**：查重 → 分配 ID → 登记索引 → 回写来源
- **来源文件引用**：task 级触发真源 `task-scenario-triggers.json` 顶部声明 `$schema`
- **边界定义**：`conflict_domains` 节明确定义与 proxy-downloader、download-runtime、project-handoff 的边界

> 治理设计意图见：`DESIGN.md` 第 6 节


## 8.9 独立审计机制：审计者不能审计自己

> **来源**：用户与 Agent 在 2026-07-03 对话中共同确认。本节固化"audit/巡检必须是独立机制"的架构原则，防止"自检即免责"的系统性盲区。

### 8.9.1 核心原则

**审计者与被审计对象必须物理隔离**。类比现实世界的审计准则：
- 会计不能审计自己的账簿
- 运动员不能当自己的裁判
- 被检测的系统不能出具自己的检测报告

在 task/ 工具链体系中的体现：**任何验证、巡检、一致性检查操作，必须由独立于被检查对象的机制执行**，不能依赖被检查对象的自我报告或内置自检。

### 8.9.2 判定标准（四项必须同时满足）

| 维度 | 独立审计的要求 | 反例（不独立） |
|------|---------------|---------------|
| **执行上下文隔离** | 审计代码与被审计代码不在同一进程/同一调用栈 | 插件 A 在 `__main__` 里写自检逻辑，运行自己时顺便检查自己 |
| **触发机制独立** | 审计由外部事件触发（人类指令、定时任务、CI 流水线），不是被审计对象完成后的"顺便检查" | workflow 执行完后在末尾加一段"自我验证"代码 |
| **数据源交叉** | 审计方从独立数据源获取被审计对象的状态，不读取被审计对象的自我报告 | lint 插件自己输出"我已通过"，审计方直接采信 |
| **结果不可篡改** | 审计结果写入独立存储（外部文件、独立数据库、跨进程通信），被审计对象无权修改 | 被审计的脚本把检测结果写进自己的日志文件 |

### 8.9.3 在 task/ 体系中的具体实践

**案例 1：Lint 验证**
- ✅ 独立：`run-lint.py` 作为独立入口，读取 `py-sort-rules.json` 发现 lint 插件，动态加载后扫描目标文件
- ❌ 不独立：`lint_encoding.py` 在模块末尾加 `if __name__ == "__main__": self_validate()`，运行自己时自检

**案例 2：插件注册表一致性检查**
- ✅ 独立：`py_lib.py` 的 `if __name__ == "__main__"` 自检块列出所有插件（这是入口层的全局视角，不是某个插件自检）
- ✅ 更独立：未来可开发 `audit-plugin-registry.py`，独立扫描 `py-plugins/` 与 `py-sort-rules.json` 的双向一致性
- ❌ 不独立：`archive_scanner.py` 在运行时检查"我是不是被 registry 加载的"（这是运行时断言，不是审计）

**案例 3：工具指引有效性验证**
- ✅ 独立：delegate 新 Agent，只给 task 目录入口和任务目标，让它自主发现工具、自主调用、自主报告（今天 session 的做法）
- ❌ 不独立：当前 Agent 自己读文档、自己执行、自己宣布"指引有效"（这是自证，不是审计）

**案例 4：真源索引更新**
- ✅ 独立：`update-version.py` workflow 作为独立入口，调用 `runtime_version` 插件检测各工具，对比后更新 `venv/version/*.md`
- ❌ 不独立：`runtime_version.py` 插件在检测到版本变化后，直接写入 `verified-runtime-index.json`（插件越权修改索引）

### 8.9.4 独立审计的触发时机

| 场景 | 审计机制 | 触发方式 |
|------|---------|---------|
| 新增/修改 plugin | 注册表一致性检查 | `py_lib.py` 自检或独立 `audit-registry.py` |
| 新增/修改 workflow | 端到端执行验证 | delegate 新 Agent 或 CI 流水线 |
| 修改 baseline/标准文档 | 标准 ↔ 实现双向对齐检查 | 人工 review + lint 工具验证 |
| 发布前 | 全链条自闭环验证 | `workflow-deploy-full.py --auto`（workflow 自身是独立的，不是被部署对象的自检） |

### 8.9.5 与 Workflow 自闭环的关系

[baseline-principles.md](baseline-principles.md) 0.6 节规定 workflow 必须有内置 preflight（Step 0），这与 8.9 节的"独立审计"不矛盾：
- **Workflow preflight** = 被审计对象（workflow）在执行前的**前置条件检查**，属于"自我负责"
- **独立审计** = 外部机制对"workflow 的设计、工具指引、注册表一致性"的**事后或并行验证**

类比：飞行员起飞前做 checklist（preflight），地面工程师定期审查 checklist 本身是否完整准确（独立审计）。

### 8.9.6 铁律

> **一句话**：自检只能证明"我按我的逻辑运行了"，不能证明"我的逻辑是对的"。证明"逻辑对"必须依赖外部独立审计。

**禁止行为**：
- ❌ 任何插件/脚本在 `__main__` 块中执行覆盖自身的验证（如"我是否正确加载了自己"）
- ❌ 任何 workflow 在末尾追加"自我评分"或"自我宣告成功"的逻辑
- ❌ 任何索引文件（`verified-task-index.json`、`verified-runtime-index.json`）由被索引的工具自己更新

**鼓励行为**：
- ✅ 为 registry/索引/配置开发独立的 `audit-*.py` 脚本
- ✅ 定期 delegate 新 Agent 验证工具自发现能力
- ✅ CI 流水线中设置独立 job 执行一致性检查


## 8.10 决策真源集中化原则（唯一真源的泛化）

> **来源**：用户与 Agent 在 2026-07-03 对话中共同确认。本节是 `runtime_naming.py` 设计意图的泛化沉淀——唯一真源不限于"命名"，任何可能产生分支判断的决策点都必须集中管理。

### 8.10.1 核心原则

**下游环节禁止产生新的真源判断**。所有可能改变执行路径的决策（文件名怎么拼、目录怎么建、旧文件清不清、版本超没超阈值）必须上溯到统一的真源模块或配置契约，由它输出唯一结论，下游只消费、不判断。

**为什么必须集中化**：
- 如果 5 个脚本各自拼接下载文件名，任何命名规则变更都要改 5 处，必漏
- 如果 3 个步骤各自决定"要不要清理旧文件"，清理策略会漂移，有的清有的不清
- 如果 preflight 和 workflow 各自判断"版本是否过时"，判断逻辑会分叉，同一版本在不同环节结论相反

### 8.10.2 决策点的分类与真源归属

| 决策类型 | 分散风险 | 真源归属 | 当前实例 |
|---------|---------|---------|---------|
| **产物命名** | 5 个脚本各自拼接文件名 → 命名不一致 | `runtime_naming.py`（命名真源） | ZIP 文件名、解压目录名、exe 路径 |
| **路径生成** | download 和 extract 各自决定"下到哪""解到哪" → 路径错位 | `runtime_naming.get_download_paths()` | 下载路径、解压路径、备份路径 |
| **清理策略** | preflight 清一遍、workflow 开端清一遍、atomic 结束再清一遍 → 策略冲突 | 应由 workflow 统一决策，通过参数显式传递 | `atomic-05-cleanup-temp.py` 接收 `--extract-dir` 和 `--zip-file`，不自行推断 |
| **版本阈值** | detect 脚本说"过时"，compare 脚本说"最新" → 判断分叉 | `list_upstream_versions.py` + `atomic-compare-version.py`（版本对比真源） | `version_constraint` 规则统一判断是否需更新 |
| **黑白名单** | scanner 和 compressor 各自维护过滤规则 → 结果不一致 | `archive-groups.json`（配置契约真源） | 归档分组的黑白名单 |
| **时间格式** | 3 个脚本各自写 `datetime.now().strftime(...)` → 格式漂移 | `timestamp.py`（时间格式化真源） | `get-timestamp.py` 统一输出所有格式 |

### 8.10.3 已发生的反例与修正

**反例 1：下载文件名分散拼接（已修正）**
```python
# ❌ 违规：wf-download-runtime.py 自己拼文件名
zip_name = f"{tool_name}-{version}-windows.zip"

# ❌ 违规：atomic-03-extract-verify.py 又拼一遍
extract_dir = f"{tool_name}-{version}-extracted"

# → 结果：两个地方命名规则不同，wf 下的文件 extract 找不到
```

**修正后**：
```python
# ✅ 合规：统一调用命名真源
from py_lib import load_plugins
registry = load_plugins(devroot=devroot, tags=["runtime", "naming"])
paths = registry.runtime_naming.get_download_paths(tool_name, version, platform="windows")
# paths.download_file, paths.extract_dir, paths.final_exe 一次性产出
```

**反例 2：清理策略分散决策（已修正）**
```python
# ❌ 违规：atomic-03-extract-verify.py 自己决定"解压完顺手删了 ZIP"
os.remove(zip_file)  # 这里删了，但 workflow 可能还想留着做校验

# ❌ 违规：wf-download-runtime.py 开头自己判断"如果旧目录存在就删掉"
shutil.rmtree(old_dir, ignore_errors=True)  # 策略与 atomic 不一致
```

**修正后**：
```python
# ✅ 合规：清理策略由 workflow 统一决策，通过参数显式传入
# atomic-03-extract-verify.py 只做解压，不自行清理
# atomic-05-cleanup-temp.py 接收 --extract-dir 和 --keep-zip 参数，按指令执行
# workflow 在编排层决定"什么时候清、清什么"
```

### 8.10.4 对 Workflow 编排的要求

当 workflow 串接多个 atomic 脚本时，**路径和策略决策必须在编排层完成**，作为参数显式传入每个 atomic，禁止让 atomic 各自推断。

**正确示范**：
```python
# workflow-download-runtime.py 编排层
registry = load_plugins(devroot=devroot, tags=["runtime", "naming"])
paths = registry.runtime_naming.get_download_paths(tool_name, version, platform)

# 决策在编排层完成，参数显式传递
subprocess.run([
    python, "atomic-02-download-file.py",
    "--url", upstream_url,
    "--out-file", paths.download_file,  # 真源生成的路径
])

subprocess.run([
    python, "atomic-03-extract-verify.py",
    "--zip-file", paths.download_file,
    "--extract-dir", paths.extract_dir,  # 真源生成的路径
    "--tool-name", tool_name,
])

# 清理策略由 workflow 统一决策
if not keep_download:
    subprocess.run([
        python, "atomic-05-cleanup-temp.py",
        "--zip-file", paths.download_file,
        "--extract-dir", paths.extract_dir,
    ])
```

### 8.10.5 铁律

> **一句话**：凡是"可能有人会有不同做法"的决策点，都必须集中到真源；下游只做"按给定参数执行"，不做"按自己的理解判断"。

**禁止行为**：
- ❌ 两个以上的脚本各自拼接同一份路径/文件名
- ❌ atomic 脚本自行推断"默认路径是什么"
- ❌ preflight 和 workflow 对同一条件（如"版本是否过时"）各自独立判断
- ❌ 配置契约（JSON）中只定义了部分规则，剩余逻辑散落在代码中

**鼓励行为**：
- ✅ 新增决策点时，先问"这个判断是否有其他脚本也在做"
- ✅ 将判断逻辑提取为独立插件（如 `runtime_naming`、`list_upstream_versions`）或配置契约
- ✅ atomic 脚本的 CLI 参数全部显式必填，不设"智能默认值"
- ✅ workflow 编排层是"决策中心"，atomic 是"执行终端"


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
