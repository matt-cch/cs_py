---
title: atomic-gh-pr-merge 新建与 gh 真源认知纠偏
description: 新建 atomic-gh-pr-merge.py 原子脚本，修正越界设计，并复盘 gh_preflight 真源验证的本质误区。
date: 2026-08-04
meta:
  version: 1.0.0
  session_ts: "2026-08-04-173941"
---

# atomic-gh-pr-merge 新建与 gh 真源认知纠偏

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 新建 atomic-gh-pr-merge.py + gh 真源验证认知纠偏 |
| **日期** | 2026-08-04 |
| **文件名时间戳** | `2026-08-04-173941` |
| **触发原因** | 用户要求新建 atomic-gh-pr-merge.py，规范对齐 atomic-gh-pr-create.py v1.0.2；执行后复盘 gh 真源验证逻辑 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/` 新增 1 个原子脚本；gh_preflight 认知勘误 |
| **风险等级** | 中 |

## 一、文本文件变更清单

### 1. 新建 `atomic-gh-pr-merge.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-pr-merge.py` |
| **变更类型** | 新建 |
| **作用** | 在 polyrepo worktree 模式下，通过 GH CLI 合并 GitHub Pull Request |
| **polyrepo 契约** | `--devroot` + `--target`，所有 gh CLI 命令显式 `--repo ctx.owner_repo` |
| **版本** | v1.0.0 |
| **验证方式** | `run-lint.py` lint_python + lint_encoding 通过；dry-run + 实执行验证 |

**核心设计要点**:

- Post-Audit: `gh pr view <number> --json state` 验证 PR 状态变为 `MERGED`
- 职责边界: **绝不执行本地 git 操作**（无 checkout、无 pull）
- default_branch 从 `target/git-security.json` 读取，仅用于日志/审计

### 2. 修正越界设计

| 属性 | 值 |
|------|-----|
| **路径** | 同上（edit） |
| **修改内容** | **移除 Step 5（自动 `checkout main + pull`）**；Post-Audit 从 `git log` 改为 `gh pr view --json state` |
| **原因** | 用户指出: atomic 脚本不应做 workflow 的事，不应猜测用户意图，不应擅自修改本地工作区 |

**越界行为的恶果**（第一次执行时）:

- 自动 `git checkout main`: 把用户的 worktree 从 `feat/demo` 切到了 `main`
- 自动 `git pull origin main`: 因本地 `main` 超前 2 commit 而失败（分歧分支冲突）
- 两者均不属于 "gh pr merge" 的职责

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

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py` | `run-lint.py`（lint_python + lint_encoding） | Python 语法、编码/BOM/换行符 | 语法通过、无 BOM、无 CRLF |

**执行记录**:

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" `
    --devroot "${devroot}" `
    --files "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-merge.py"
# 结果: ✅ 全部通过
```

## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | dry-run 模式验证 | `python atomic-gh-pr-merge.py --devroot ... --target ... --dry-run` | 输出命令构造，不实际 merge |
| 2 | 实执行 merge（PR #2） | 同上，去掉 `--dry-run` | PR 状态变为 MERGED，manifest 落盘 |
| 3 | 远程 PR 状态确认 | `gh pr view 2 --repo matt-cch/jywl-settlement --json state` | `{"state":"MERGED"}` |
| 4 | 网页确认 | 浏览器打开 `github.com/matt-cch/jywl-settlement/pulls` | Open PR 数量为 0 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建脚本 | `Remove-Item "references\tasks\deploy-git-isolated\scripts\py-tools\atomic-gh-pr-merge.py"` |
| 恢复 legacy 脚本使用 | 回退到使用 `gh-pr-merge.py`（无 --target 支持，不支持 polyrepo） |

## 七、Session 踩坑与纠偏记录

> **本节为本次 session 的核心产出，记录 gh "真源"概念的认知误区与纠正。**

### 7.1 初始错误: 认为 `gh_preflight` 做了 "真源验证"

**误区表述**:

> "`gh_preflight.verify(devroot, target)` 从 target 的 git remote 解析 owner/repo，并向 GitHub 验证真源。"

**实际发生的过程**:

| 步骤 | 调用 | 输出 | 验证了什么 |
|------|------|------|-----------|
| 4a | `git remote get-url origin` | `https://github.com/matt-cch/jywl-settlement.git` | **本地 `.git/config` 文件里的一个字符串** |
| 4b | 字符串解析 | `matt-cch/jywl-settlement` | 纯本地格式化转换 |
| 4c | `gh repo view matt-cch/jywl-settlement --json url` | 返回 200 + JSON | "GitHub 上**存在一个叫这个名字的仓库**" |

**问题**:

- `.git/config` 可被 `git remote set-url` **随时篡改**
- 4c 只验证了"仓库存在"，**没验证"本地代码属于这个仓库"**
- 如果 `.git/config` 被改成攻击者的仓库（且该仓库存在），4c 会通过，后续所有操作都会在**错误仓库**上执行

### 7.2 用户的纠偏

用户连续追问:

1. "既然是本地文件，你怎么知道就是真源？"
2. "你的真源的本质不就是远端 repo 的真实状态吗？"
3. "谁给你保证是真实物理连接？"

**结论**:

- `gh_preflight` 的 4a/4c **不是真源验证**
- 4a 是**本地配置读取**（可被篡改）
- 4c 是**远程可达性验证**（只证明"有个仓库叫这个名字"）
- **真源验证**必须由业务脚本的 **Post-Audit** 完成

### 7.3 真正的真源验证在哪里

| 脚本 | 真源验证方式 | 本质 |
|------|-------------|------|
| `atomic-gh-pr-create.py` | `gh pr create` → 得到 pr_number → `gh pr view <number> --json state` | **操作 → 回查**: 确认远程确实出现了刚才创建的对象 |
| `atomic-gh-pr-merge.py` | `gh pr merge <number>` → `gh pr view <number> --json state` 确认 `MERGED` | **操作 → 回查**: 确认远程状态确实变为 merged |
| `gh_preflight` | `gh repo view owner/repo` | **可达性验证**: 证明远程存在同名仓库 |

**关键区别**:

- Preflight: "我能 ping 通一个叫 `matt-cch/jywl-settlement` 的仓库"
- Post-Audit: "我刚才让你创建/merge 的 PR #2，现在还在那里，而且状态正确"

### 7.4 对后续脚本设计的约束

1. **不要把 preflight 的输出当作绝对真源**——`ctx.owner_repo` 是"经过可达性验证的候选值"，不是不可篡改的真源
2. **原子脚本的 Post-Audit 必须直接回查操作结果**——不能只验证"仓库存在"，要验证"我刚才操作的对象确实在那里"
3. **如果需要在 preflight 层做真源绑定**，应额外验证本地 HEAD commit 是否存在于远程仓库，但这会让 preflight 臃肿，建议由业务脚本按需处理

## 八、产物路径

| 产物 | 路径 | 状态 |
|------|------|------|
| atomic-gh-pr-merge.py | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-gh-pr-merge.py` | ✅ 已交付，lint 通过 |
| manifest（dry-run） | `venv/tmp/atomic-gh-pr-merge-manifest-20260804-075950.json` | ✅ 已落盘 |
| manifest（实执行） | `venv/tmp/atomic-gh-pr-merge-manifest-20260804-080628.json` | ✅ 已落盘 |
| PR #2 | `https://github.com/matt-cch/jywl-settlement/pull/2` | ✅ 已 merged |

## 九、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-04-173941 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求新建 atomic-gh-pr-merge.py + 深度复盘 gh 真源验证 |
| **下次修订条件** | atomic-gh-pr-merge.py 功能扩展；gh_preflight 真源绑定增强 |
| **跨环境迁移参考** | 直接复制 atomic-gh-pr-merge.py + 按「验证清单」逐条执行 |

*文档生成时间: 2026-08-04*  
*模板版本: env-migration-template.md v2*
