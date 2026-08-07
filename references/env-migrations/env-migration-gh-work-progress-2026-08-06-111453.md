---
title: env-migration — gh 场景工作进度梳理与下游脚本改造规划
description: 本次 session 对 deploy-git-isolated task 下 gh 场景（GitHub CLI / PR / 真源验证）进行全量进度梳理，确认 atomic-gh-repo-verify.py + source_truth.py 已稳定，输出下游脚本改造清单与下一步任务安排
date: 2026-08-06
meta:
  version: "1.0.0"
---

# env-migration — gh 场景工作进度梳理与下游脚本改造规划

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | gh 场景工作进度全量梳理与下游脚本改造清单输出 |
| **日期** | 2026-08-06 |
| **文件名时间戳** | `2026-08-06-111453` |
| **触发原因** | 用户要求搜索"gh 场景的工作进度"，经 P0-P3 搜索 + 磁盘验证 + env-migration 时间线补查后，输出完整进度报告 |
| **影响范围** | deploy-git-isolated/scripts/py-tools/ 与 py-plugins/ 下的 gh 相关脚本；references/env-migrations/ 导航表；rg-fd-search skill 能力升级（SED 沉淀） |
| **风险等级** | 低（本次为分析规划型 session，无代码变更） |

## 一、文本文件变更清单

> **说明**：本次 session 为**分析规划型**，未直接修改或新建代码文件。以下列出的是当前已存在的、被分析的核心脚本真源状态。

### 1. 已稳定基石（不再改动）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/source_truth.py` |
| **变更类型** | 既有（稳定） |
| **作用** | L1-L5 Git/GitHub 真源推理链核心插件。L1 本地实测 → L2 用户声明 → L3 交叉验证 → L4 远程物理绑定（硬阻断）→ L5 远程对象绑定 |
| **验证方式** | jywl-settlement feat/demo 实执行验证通过（manifest 完整，L1-L5 全部通过） |
| **状态** | ✅ ready，v1.0.0 |

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-verify.py` |
| **变更类型** | 既有（稳定） |
| **作用** | 标准 atomic CLI 入口，调用 source_truth 插件执行 L1-L5 推理链，输出 JSON manifest 供下游 PR 创建/合并复用 |
| **调用契约** | `--devroot` + `--target` 必填；`--output`/`--dry-run`/`--show-progress` 标准可选 |
| **验证方式** | jywl-settlement feat/demo 实执行验证通过 |
| **状态** | ✅ ready，v1.0.0 |

### 2. 下游脚本现状全景

| # | 脚本 | 当前 repo_url/owner_repo 来源 | 是否调用 source_truth / atomic-gh-repo-verify | 改造必要性 | 优先级 |
|---|------|---------------------------|------------------------------------------|----------|--------|
| 1 | `atomic-gh-pr-create.py` | `gh_preflight.verify()` → `ctx.owner_repo` | ❌ 未调用 | **必须改造** | **P0（最高）** |
| 2 | `atomic-gh-pr-merge.py` | `gh_preflight.verify()` → `ctx.owner_repo` | ❌ 未调用 | **必须改造** | **P0（最高）** |
| 3 | `workflow-gh-pr.py` | 调用 gh-pr-create.py + gh-pr-merge.py，自身不做 repo 验证 | ❌ 未嵌入 repo verify | **必须改造** | **P0（最高）** |
| 4 | `atomic-deploy-preflight.py` | 内嵌 repo_url 验证（L1-L3：git-security + git-remote + GitHub API `fetch_repo_metadata`） | ❌ 未调用 atomic-gh-repo-verify | **推荐升级** | P1 |
| 5 | `atomic-gh-issue-create.py` | `gh_preflight.verify(devroot)` → `ctx.owner_repo`（不传 target） | ❌ 未调用 | **待评估** | P2 |
| 6 | `gh-pr-create.py` (legacy) | `registry.gh_preflight.check()` | ❌ 未调用 | 不改造，标注 deprecated | — |
| 7 | `gh-pr-merge.py` (legacy) | `registry.gh_preflight.check()` | ❌ 未调用 | 不改造，标注 deprecated | — |

## 二、各脚本改造详解

### P0-1: atomic-gh-pr-create.py

**当前问题**：
- 调用 `gh_preflight.verify(devroot, target)` 获取 `ctx.owner_repo`
- `gh_preflight` 只验证工具链可用性，不验证真源（L1-L5）
- PR 创建前**不确认**本地 commit 是否已推送到远程（缺少 L4 硬阻断）

**改造方案**：
1. 在 `main()` 开头、调用 `gh_preflight.verify()` 之后，追加调用 `source_truth.verify(devroot, target, gh_ctx)`
2. 检查 `stx.ok`：`ok=False` → exit 1；`ok=True` 但有 warnings → 打印 warnings 但继续
3. 使用 `stx.owner_repo` 替代 `ctx.owner_repo` 作为 `--repo` 参数

**最小改动范围**：约 5~8 行

### P0-2: atomic-gh-pr-merge.py

**当前问题**：同 atomic-gh-pr-create，只调用 `gh_preflight.verify()`，未验证真源

**改造方案**：同 P0-1，额外验证 manifest 中的 `pr_number` 和 `pr_binding_verified`

**最小改动范围**：约 5~10 行

### P0-3: workflow-gh-pr.py

**当前问题**：编排 gh-pr-create → gh-pr-merge → pull，Step 0 Preflight 只检查 git/gh 工具链

**改造方案**：
1. 在 Step 0 Preflight 后、Step 1 PR Create 前，嵌入 `atomic-gh-repo-verify.py` 调用
2. 读取 manifest 获取 `owner_repo`，传递给下游 gh-pr-create/merge
3. 若 verify exit 1 → workflow 直接 exit

**最小改动范围**：约 10~15 行

### P1: atomic-deploy-preflight.py

**当前问题**：内嵌第 131-195 行 repo_url 验证逻辑（L1-L3），**缺少 L4**（commit SHA 必须在远程）和 **L5**（PR 绑定验证）

**改造方案**：
1. 删除第 131-195 行内嵌 repo_url 验证逻辑
2. 替换为 subprocess 调用 `atomic-gh-repo-verify.py --devroot ... --target ...`
3. 读取其 manifest 获取 `repo_url` + `source_truth` 结果

**认知记录**：当前 L1-L3 已能防止"操作错仓库"和"URL 不一致"，基本够用。L4 升级是**推荐而非紧急**。

### P2: atomic-gh-issue-create.py

**待评估**：Issue 创建是否也需要 L4（commit SHA 存在性验证）？Issue 不依赖分支/PR，可能只需要 L1-L3。建议先不改，等实际使用中发现问题再评估。

## 三、非文本操作

本次 session **不涉及**文件复制、缓存迁移、目录创建等非文本操作。全部为分析规划型工作。

## 四、环境变量速查

本次 session **不涉及** `.vscode/settings.json` 或 `.env` 的新增环境变量。现有变量已满足：

- `GITHUB_PAT`（devroot/.env）
- `GITHUB_USERNAME`（devroot/.env）

## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 source_truth.py 存在 | `Test-Path "references/tasks/deploy-git-isolated/scripts/py-plugins/source_truth.py"` | True |
| 2 | 确认 atomic-gh-repo-verify.py 存在 | `Test-Path "references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-verify.py"` | True |
| 3 | 确认 source_truth 语法 | `run-lint.py --profile lint-python --files source_truth.py` | 通过 |
| 4 | 确认 atomic-gh-repo-verify 语法 | `run-lint.py --profile lint-python --files atomic-gh-repo-verify.py` | 通过 |
| 5 | 确认 jywl-settlement 实执行通过 | `atomic-gh-repo-verify.py --devroot ... --target ...` | manifest 输出完整，L1-L5 全部通过 |

## 六、下一步任务安排（推荐执行顺序）

```
Step 1: 改造 atomic-gh-pr-create.py（P0）
    └─ 追加 source_truth.verify() 调用，L4 硬阻断
    └─ run-lint.py 验证
    └─ 实执行业务验证（dry-run + 真实 PR 创建测试）

Step 2: 改造 atomic-gh-pr-merge.py（P0）
    └─ 同上
    └─ run-lint.py 验证
    └─ 实执行业务验证

Step 3: 改造 workflow-gh-pr.py（P0）
    └─ Step 0 后嵌入 atomic-gh-repo-verify.py 调用
    └─ run-lint.py 验证
    └─ 端到端 workflow 验证（create → merge → pull）

Step 4: 升级 atomic-deploy-preflight.py（P1，可选）
    └─ 删除内嵌 repo_url 验证，替换为 atomic-gh-repo-verify 调用
    └─ run-lint.py 验证
    └─ 与 workflow-deploy-full-poly.py 联调

Step 5: 修订联动
    └─ 更新 ENTRY.json / TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md
    └─ 更新 verified-task-index.json
    └─ 更新 env-migration 中的"未改造事项"状态
```

## 七、回滚方案

本次 session 为纯分析规划型，无代码变更。若需要撤销本次规划：

| 回滚步骤 | 操作 |
|---------|------|
| 删除本 env-migration | `Remove-Item "references/env-migrations/env-migration-gh-work-progress-2026-08-06-111453.md"` |
| 恢复 README.md 导航表 | 从 git 历史恢复 `references/env-migrations/README.md` |

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-06-111453 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求搜索"gh 场景的工作进度" |
| **下次修订条件** | P0 改造（atomic-gh-pr-create/merge + workflow-gh-pr）完成后更新改造状态 |
| **跨环境迁移参考** | 直接阅读本文档即可复现分析结论，无需额外操作 |

*文档生成时间：2026-08-06*  
*模板版本：env-migration-template.md v2*
