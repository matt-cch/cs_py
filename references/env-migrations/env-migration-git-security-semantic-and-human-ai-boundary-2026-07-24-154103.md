---
title: git-security 语义澄清与人机协同边界认知对齐
description: 本次 session 通过 cs_py / jywl-settlement 的 git-security.json 对比，澄清 allow_direct_push_to 仅约束 default_branch 的语义，明确本地配置与 remote 规则的端点独立性，新增人机协同边界 baseline（确定性 vs 概率性事务分工），修正 Agent 越权推断行为。
date: 2026-07-24
meta:
  version: "1.0.0"
---

# git-security 语义澄清与人机协同边界认知对齐

> **Session 主题**：`git-security.json` `allow_direct_push_to` 语义澄清 + 人机协同边界 baseline 建设 + 本地配置与 remote 规则的端点独立性认知对齐
> **文件名时间戳**：`2026-07-24-154103`
> **触发原因**：Agent 在分析 polyrepo 结构时，多次越权推断（① 把 `--devroot` 当操作对象；② 把 Agent 主观判断当权限真源；③ 把本地白名单当远程强制力），需要把纠正后的认知固化为 baseline
> **影响范围**：`references/tasks/deploy-git-isolated/baseline/` 目录下 3 个文件
> **风险等级**：低（纯认知文档变更，无代码执行风险）


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
| **新增/修改内容** | ① `allow_direct_push_to` 语义修正：明确仅约束 `default_branch`，非默认分支不受约束；② 补充"本地配置与 Remote 规则的端点独立性"段落（两段点模型 + 示例对照表） |
| **插入位置** | §8.7.6.6 `allow_direct_push_to` 语义 之后 |
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


## 二、非文本操作

本次 session 无文件系统/缓存迁移等非文本操作。


## 三、环境变量速查

本次 session 未修改 `.vscode/settings.json`、`.env` 或任何环境变量。无需核对。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md` | `run-lint.py --profile lint-md` | frontmatter、BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |

**执行记录**：

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-human-ai-boundary.md" "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-workflow-deploy.md" "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-index.md" --fix
```

结果：3 个文件全部通过，0 违规。


## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认新增 baseline 可访问 | `read "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-human-ai-boundary.md"` | 文件存在，内容完整 |
| 2 | 确认导航索引已登记 | `read "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-index.md"` | 导航表包含新增条目，版本为 v2.5.2 |
| 3 | 确认 `allow_direct_push_to` 语义已修正 | `read "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-workflow-deploy.md"` §8.7.6.6 | 明确"仅约束 default_branch" + "端点独立性" |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增文件 | `Remove-Item "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-human-ai-boundary.md"` |
| 恢复 baseline-index.md | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-index.md"` |
| 恢复 baseline-workflow-deploy.md | `git checkout -- "${devroot}\references\tasks\deploy-git-isolated\baseline\baseline-workflow-deploy.md"` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-24-154103 |
| **更新人** | Human + Agent Session |
| **变更触发** | Agent 多次越权推断（把主观判断当权限真源），用户逐条纠正后固化 |
| **下次修订条件** | ① 发现新的 Agent 越权推断模式；② 人机协同边界需要扩展（如多 Agent 协作场景） |
| **跨环境迁移参考** | 直接复制本文档涉及的 3 个 baseline 文件 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-24*  
*模板版本：v2*
