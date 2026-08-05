---
title: source-truth L1-L5 真源推理链建设与 gh 真源认知纠偏
description: 新建 source_truth.py 插件与 atomic-gh-repo-verify.py 原子 CLI，建立以 git-security.json 为起点的 local-remote 多层真源推理链，修正 gh_preflight 真源认知误区，统一 URL .git 后缀规范。
date: 2026-08-05
meta:
  version: 1.0.0
  session_ts: "2026-08-05-133038"
---

# source-truth L1-L5 真源推理链建设与 gh 真源认知纠偏

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 新建 source_truth.py 真源推理链 + atomic-gh-repo-verify.py 原子 CLI + gh 真源认知纠偏 |
| **日期** | 2026-08-05 |
| **文件名时间戳** | `2026-08-05-133038` |
| **触发原因** | 用户要求复盘昨日 env-migration 中关于 gh 真源检测的讨论，深入分析 local-remote 真源对应逻辑 |
| **影响范围** | `py-plugins/` 新增 1 个插件，`py-tools/` 新增 1 个原子脚本，`git-security.json` schema 扩展，vaults 知识沉淀 |
| **风险等级** | 中（涉及真源验证核心逻辑，下游 atomic 脚本依赖） |


## 一、文本文件变更清单

### 1. 新建 `source_truth.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/source_truth.py` |
| **变更类型** | 新建 |
| **作用** | 执行 L1-L5 完整真源推理链，输出 SourceTruthContext（含经过验证的 owner_repo + 完整 manifest 数据） |
| **版本** | v1.0.0 |
| **验证方式** | `run-lint.py` lint_python + lint_encoding 通过；jywl-settlement feat/demo 实执行验证 |

**核心设计要点**:

- L1 本地实测推断层：从 `.git/` 数据库读取物理状态（分支、HEAD SHA、remote URL）
- L2 用户声明审计层：读取 `target/git-security.json`，验证自洽性
- L3 交叉验证层：L1 推断 vs L2 声明 vs `.git/config` 佐证对碰
- L4 远程物理绑定层：本地 HEAD commit SHA 必须存在于远程仓库（核心防线）
- L5 远程对象绑定层：分支 ↔ PR / Issue 物理对应验证（仅提供信息，不阻断 ok）
- 冲突时以 `git-security.json` 为准，`.git/config` 仅作佐证

### 2. 新建 `atomic-gh-repo-verify.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-verify.py` |
| **变更类型** | 新建 |
| **作用** | 标准 atomic CLI，调用 `source_truth.verify()` 执行真源验证并落盘 manifest |
| **polyrepo 契约** | `--devroot` + `--target`，所有 gh 命令显式 `--repo` |
| **版本** | v1.0.0 |
| **标准参数** | `--devroot`, `--target`, `--verify-pr-binding`, `--no-verify-pr-binding`, `--verify-linked-issues`, `--no-verify-linked-issues`, `--output`, `--dry-run`, `--show-progress` |
| **返回值** | exit 0 = 通过, exit 1 = 失败 |
| **验证方式** | `run-lint.py` 通过；dry-run + 实执行验证 |

### 3. 修改 `git-security.json`（cs_py 根）

| 属性 | 值 |
|------|-----|
| **路径** | `git-security.json` |
| **变更类型** | 修改 |
| **修改内容** | 新增 `"owner_repo": "matt-cch/cs_py"` 字段 |
| **原因** | schema 对齐：git-security.json 必须显式声明 owner_repo，消除从 repo_url 推断的降级路径 |

### 4. 修改 `git-security.json`（jywl-settlement feat-demo）

| 属性 | 值 |
|------|-----|
| **路径** | `apps/repos/matt-cch/jywl-settlement.wt/feat-demo/git-security.json` |
| **变更类型** | 修改 |
| **修改内容** | 新增 `"owner_repo": "matt-cch/jywl-settlement"` 字段 |
| **原因** | 同上 |

### 5. 新建知识沉淀文档

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/conclusions/git-gh-source-truth-verification-design.md` |
| **变更类型** | 新建 |
| **作用** | 记录本次 session 关于 Git/GitHub 真源检测的全部讨论细节、设计决策、架构蓝图 |
| **验证方式** | `run-lint.py` md_lint + lint_encoding 通过 |


## 二、非文本操作

本次 session 无文件复制、缓存迁移、目录创建等非文本操作。

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 无 | — | — | 本次 session 纯代码/文档变更 |


## 三、环境变量速查

无新增环境变量，沿用既有 `.env`:

```
GITHUB_PAT=<PAT>
```


## 四、关键设计决策与纠偏记录

### 4.1 gh_preflight 真源认知纠偏

**误区**：认为 `gh_preflight.verify()` 从 `.git/config` 解析 owner_repo 并向 GitHub 验证是真源验证。

**实际**：`.git/config` 可被 `git remote set-url` 随时篡改；`gh repo view` 只验证"仓库存在"，不验证"本地代码属于该仓库"。

**纠正**：真源起点必须是用户意图层（`git-security.json`），`.git/config` 仅作佐证。

### 4.2 URL .git 后缀规范

**问题**：历史 create/clone 操作不规范，导致 `.git/config` 中 remote URL 可能不带 `.git`（如 `https://github.com/matt-cch/jywl-settlement`），与 GitHub 官方 clone URL（`https://github.com/matt-cch/jywl-settlement.git`）不一致。

**决策**：
- `git-security.json` 中的 `repo_url` **必须带 .git**
- 后续 gh repo create/clone **必须设置带 .git 的 remote URL**
- `.git/config` 保持现状（不修改工具内部状态）
- `canonicalize_url` 仅用于比对，原始记录保留 .git

### 4.3 L5 PR 不存在 ≠ 真源失败

**修正**：`source_truth.py` 中 L5 "分支无 open PR" 从 `errors` 降级为 `info`/`warning`，不再影响 `stx.ok`。

真源验证的硬防线是 L4（commit SHA 存在性），L5 只提供附加信息。

### 4.4 L3 交叉验证语义修正

**修正**："实测推断与用户声明一致"、".git/config 佐证通过"从 `warnings` 降级为 `infos`，warning 仅用于不一致/缺失场景。


## 五、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py` | `run-lint.py`（lint_python + lint_encoding） | Python 语法、编码/BOM/换行符 | 语法通过、无 BOM、无 CRLF |
| `.json` | `run-lint.py`（lint_json + lint_encoding） | JSON 语法、编码/BOM/换行符 | 语法通过、无 BOM、无 CRLF |
| `.md` | `run-lint.py`（md_lint + lint_encoding） | frontmatter、编码/BOM/换行符 | frontmatter 完整、无 BOM、无 CRLF |

**执行记录**:

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" `
    --devroot "${devroot}" `
    --files "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\source_truth.py" `
            "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-verify.py" `
            "${devroot}\git-security.json" `
            "${devroot}\apps\repos\matt-cch\jywl-settlement.wt\feat-demo\git-security.json" `
            "${devroot}\vaults\vault-demo\wiki\conclusions\git-gh-source-truth-verification-design.md"
# 结果: 全部通过
```


## 六、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | dry-run 模式验证 | `python atomic-gh-repo-verify.py --devroot ... --target ... --dry-run --show-progress` | 输出 L1-L5 预演信息，exit 0 |
| 2 | 实执行验证（jywl-settlement） | 同上，去掉 `--dry-run` | L1-L4 全部通过，ok=True，manifest 落盘 |
| 3 | 确认 manifest 结构 | 读取 manifest JSON | 包含 layer1-5 完整记录、owner_repo_source、physical_binding_verified |
| 4 | 确认 git-security.json 已更新 | `Test-Path` + `Get-Content` | cs_py 根和 jywl-settlement feat-demo 都有 `owner_repo` 字段 |
| 5 | 确认知识沉淀文档存在 | `Test-Path` | `vaults/vault-demo/wiki/conclusions/git-gh-source-truth-verification-design.md` 存在 |


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建插件 | `Remove-Item "references\tasks\deploy-git-isolated\scripts\py-plugins\source_truth.py"` |
| 删除新建原子脚本 | `Remove-Item "references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-repo-verify.py"` |
| 恢复 git-security.json | 手动删除 `owner_repo` 字段 |
| 删除知识沉淀文档 | `Remove-Item "vaults\vault-demo\wiki\conclusions\git-gh-source-truth-verification-design.md"` |
| 恢复 legacy 方式 | 回退到使用 `gh_preflight` 直接解析 `.git/config`（不推荐） |


## 八、Session 踩坑与纠偏记录

| # | 失误 | 根因 | 纠偏 |
|---|------|------|------|
| 1 | 初始认为 `gh_preflight` 做了真源验证 | 把 `gh repo view owner/repo` 的"仓库存在"当作"本地代码属于该仓库" | 用户指出 `.git/config` 可被篡改，真源必须是用户意图层 |
| 2 | L5 PR 不存在导致 `ok=False` | 把远程对象绑定信息（PR 存在性）与真源验证混为一谈 | 将 L5 的 `not_found` 从 errors 降级为 info/warning |
| 3 | L3 交叉验证"一致"标记为 WARN | 语义混淆：warn 应该用于异常，正常状态应该标记为 info | 新增 `infos` 字段，一致/佐证通过标记为 INFO |
| 4 | `source_truth.py` L2 未兼容旧 schema `repo_url` | 旧 git-security.json 用 `repo_url` 而非 `remote_url` | 修正 L2 读取逻辑：`data.get("repo_url", "") or data.get("remote_url", "")` |
| 5 | 文档中出现 `---` 分隔线 | 违反 `.cursor/rules/markdown-docs-format.mdc` 正文禁用 `---` 规则 | lint 检测发现后批量替换为 `***` |


## 九、产物路径

| 产物 | 路径 | 状态 |
|------|------|------|
| source_truth.py | `references/tasks/deploy-git-isolated/scripts/py-plugins/source_truth.py` | 已交付，lint 通过 |
| atomic-gh-repo-verify.py | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-repo-verify.py` | 已交付，lint 通过 |
| git-security.json（cs_py） | `git-security.json` | 已更新，lint 通过 |
| git-security.json（jywl-settlement） | `apps/repos/matt-cch/jywl-settlement.wt/feat-demo/git-security.json` | 已更新，lint 通过 |
| 知识沉淀文档 | `vaults/vault-demo/wiki/conclusions/git-gh-source-truth-verification-design.md` | 已交付，lint 通过 |
| manifest（dry-run） | `venv/tmp/atomic-gh-repo-verify-manifest-20260805-040721.json` | 已落盘 |
| manifest（实执行） | `venv/tmp/atomic-gh-repo-verify-manifest-20260805-044927.json` | 已落盘 |


## 十、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-05-133038 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户复盘昨日 env-migration 中 gh 真源检测讨论 |
| **下次修订条件** | 重构 gh_preflight.py / 重构 atomic-gh-pr-create.py / 重构 atomic-gh-pr-merge.py 时接续 |
| **跨环境迁移参考** | 直接复制 source_truth.py + atomic-gh-repo-verify.py + 按「验证清单」逐条执行 |
| **与上一份 env-migration 的关系** | 接续 `env-migration-atomic-gh-pr-merge-and-gh-source-truth-2026-08-04-173941.md`，深化真源推理链设计 |


*文档生成时间：2026-08-05*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
