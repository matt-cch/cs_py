---
title: Polyrepo 结构理解加深与 git-security 语义对齐全记录
description: 本次 session 围绕 cs-py.code-workspace polyrepo 结构、deploy-git-isolated baseline 深度阅读、git-security.json 语义澄清、人机协同边界 baseline 建设、git worktree 开发规划等主题展开，用户逐条纠正 Agent 认知偏差，最终固化多项 baseline 与认知共识。
date: 2026-07-24
meta:
  version: "1.0.0"
---

# Polyrepo 结构理解加深与 git-security 语义对齐全记录

> **Session 主题**：cs-py.code-workspace polyrepo 结构理解 → deploy-git-isolated baseline 深度阅读 → git-security.json 语义澄清 → 人机协同边界 baseline 建设 → git worktree 渐进式开发规划
> **文件名时间戳**：`2026-07-24-171616`
> **触发原因**：用户要求"说说 polyrepo 项目结构的理解"，Agent 初始理解存在多处偏差，用户逐条纠正
> **影响范围**：`baseline/`（3 个文件）、认知对齐（多个概念）、未来 atomic 脚本规划（1 个待开发）
> **风险等级**：低（认知文档 + 规划讨论，无代码执行风险）


## 一、文本文件变更清单

### 1. 新建 `baseline-human-ai-boundary.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-human-ai-boundary.md` |
| **变更类型** | 新建 |
| **作用** | 定义人机协同边界：确定性事务由配置/schema/rule/workflow 按规范执行，概率性事务才由 Agent 临场判断 |
| **核心条款** | §9.1 确定性 vs 概率性事务区分；§9.2 git-security.json 反例；§9.3 Agent 行为决策树 |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |
| **迁移方式** | 直接复制，无需调整路径 |

### 2. 修改 `baseline-workflow-deploy.md` §8.7.6.6

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-workflow-deploy.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | ① `allow_direct_push_to` 语义修正：明确仅约束 `default_branch`，非默认分支不受约束；② 补充"本地配置与 Remote 规则的端点独立性"段落（两端点模型 + 示例对照表） |
| **作用** | 消除"白名单 = 穷举"的误解；明确本地预判 vs remote 终审的关系 |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |
| **迁移方式** | 全文替换对应章节 |

### 3. 修改 `baseline-index.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-index.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | ① 导航表追加 `baseline-human-ai-boundary.md`；② 顶层原则速查追加第 18 条；③ 版本历史追加 v2.5.0/v2.5.1/v2.5.2 |
| **作用** | 保持导航索引与新增 baseline 同步 |
| **验证方式** | `run-lint.py --profile lint-md` 通过 |
| **迁移方式** | 全文替换对应章节 |


## 二、认知对齐记录（用户纠正项）

### 纠正 1：`--devroot` ≠ 操作对象

**Agent 错误**：认为 `--devroot` 可以指向不同 polyrepo 切换目标仓库。

**用户纠正**：`--devroot` 固定传 `cs_py`（公共资源根），操作对象由 `--target` 指定。

| 参数 | 语义 | 类比 |
|------|------|------|
| `--devroot` | 公共资源根：`venv/`、`scripts/`、`.env` | 手术室器械台 |
| `--target` | 操作对象：`git add/commit/push` 实际作用的仓库 | 手术台上的病人 |

### 纠正 2：Agent 主观判断 ≠ 权限真源

**Agent 错误**：凭"cs_py 是 personal repo"的主观推断判断权限，未读取 `git-security.json`。

**用户纠正**：`git-security.json` 是自声明的 Repo 身份卡，Agent 的判断权在确定性规范面前为零。

**反例**：`cs_py` 的 `security_level="strict"`、`allow_direct_push_to=[]`，实际上比某些 Team repo 更严格。

### 纠正 3：本地配置与 Remote 规则的端点独立性

**Agent 错误**：把 `allow_direct_push_to` 当作有强制力的权限声明。

**用户纠正**：`git-security.json` + code 只控制本地现成脚本路径，remote push policy 是独立终审端点。两端可能不一致，以 remote 实际返回为准。

```
本地端点（git-security.json + code）          Remote 端点（GitHub 分支保护）
    • 预判：本地提前拦截                      • 终审：实际决定是否接受 push
    • 只控制"走现成脚本"的路径                 • 控制所有 git push 请求
    • 手工直接 git push → bypass              • 无法 bypass
```

### 纠正 4：`allow_direct_push_to` 仅约束 `default_branch`

**Agent 错误**：认为白名单是穷举列表，不在就拒绝。

**用户纠正**：白名单仅对 `default_branch` 生效，非默认分支（如 `feature/xxx`）不受约束。feature 分支维护成本过高，保持现状。

### 纠正 5：git worktree 的文件包含问题

**Agent 错误**：想当然认为 `.gitignore`、`.gitattributes`、`git-security.json` 会被 worktree 自动包含。

**用户纠正**：实测 `git ls-files` 无输出，这三个文件**未被追踪**，worktree 不会自动带出。

**解决方案**：每次 `git worktree add` 后，需手工 `mklink` 或复制这三个文件。用户计划开发 `atomic-git-worktree-link-config.py` 自动化此步骤。

### 纠正 6：git config local 身份无需重复设置

**Agent 错误**：步骤中默认包含 `git config --local user.name/email`。

**用户纠正**：实测 `jywl-settlement` 和 `jywl-lab` 的 local config 已存在且正确，无需重复执行。


## 三、非文本操作

本次 session 无文件系统/缓存迁移等非文本操作。


## 四、环境变量速查

本次 session 未修改 `.vscode/settings.json`、`.env` 或任何环境变量。无需核对。


## 五、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md` | `run-lint.py --profile lint-md` | frontmatter、BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |

**执行记录**：

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-human-ai-boundary.md" "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-workflow-deploy.md" "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-index.md" --fix
```

结果：3 个文件全部通过，0 违规。


## 六、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认新增 baseline 可访问 | `read "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-human-ai-boundary.md"` | 文件存在，内容完整 |
| 2 | 确认导航索引已登记 | `read "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-index.md"` | 导航表包含新增条目，版本为 v2.5.2 |
| 3 | 确认 `allow_direct_push_to` 语义已修正 | `read "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-workflow-deploy.md"` §8.7.6.6 | 明确"仅约束 default_branch" + "端点独立性" |
| 4 | 确认 jywl-settlement git-security 存在 | `read "${devroot}\apps\repos\matt-cch\jywl-settlement\git-security.json"` | 文件存在，`allow_direct_push_to: ["main"]` |
| 5 | 确认 jywl-lab git config 已存在 | `git config --list --local` | `user.name` 和 `user.email` 已配置 |


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增 baseline | `Remove-Item "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-human-ai-boundary.md"` |
| 恢复 baseline-index.md | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-index.md"` |
| 恢复 baseline-workflow-deploy.md | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-workflow-deploy.md"` |


## 八、待办与下次接续

| # | 待办项 | 状态 | 备注 |
|---|--------|------|------|
| 1 | 开发 `atomic-git-worktree-link-config.py` | ⏳ 待开发 | 自动化：worktree add 后 mklink `.gitignore`、`.gitattributes`、`git-security.json` |
| 2 | jywl-settlement 渐进式开发启动 | ⏳ 待启动 | 先创建 feature worktree，再启动开发 |
| 3 | 验证 worktree + workflow-poly 端到端流程 | ⏳ 待验证 | `--target` 指向 worktree 物理目录 |


## 九、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-24-171616 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求"说说 polyrepo 结构理解"，Agent 初始理解偏差，用户逐条纠正后固化 |
| **下次修订条件** | ① atomic-git-worktree-link-config.py 开发完成；② jywl-settlement 实际 worktree 开发中发现新问题 |
| **跨环境迁移参考** | 直接复制本文档涉及的 3 个 baseline 文件 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-24*  
*模板版本：v2*
