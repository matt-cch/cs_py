---
title: devroot/vaults/ 与 references/env-migrations/ 的分工模式与搜索互补性
description: 从实测 session 中提炼 vaults/ 与 env-migrations/ 的分工模式，两者互补查询才能获取完整上下文
date: 2026-08-07
type: learning
category: pattern
confidence: high
evidence_count: 1
meta:
  version: "1.0.0"
  tags: [vaults, env-migrations, search-pattern, division-of-labor]
fingerprint:
  content_sha256: learning-vaults-env-migrations-division-pattern-20260807
  semantic_key: vaults-env-migrations-division
---

# devroot/vaults/ 与 references/env-migrations/ 的分工模式与搜索互补性

## 结论

在同一个项目中，工程变更日志（env-migrations/）与认知资产库（vaults/）是 **互补而非替代** 的关系。搜索任务中缺失任一维度都会导致上下文断裂。

## 分工对比

| 维度 | references/env-migrations/ | devroot/vaults/ |
|------|---------------------------|----------------|
| **文档类型** | env-migration（变更日志） | conclusions / learnings / progress / gotchas（认知资产） |
| **内容粒度** | "改了什么文件、第几行、验证命令" | "为什么这么设计、踩了什么坑、决策依据是什么" |
| **阅读时机** | 工程续接（Agent 执行具体任务时参考） | 认知续接（Agent 理解设计上下文时参考） |
| **更新频率** | 按 session 追加（时间线事实痕迹） | 按结论收敛更新（知识沉淀） |
| **典型场景** | 查看"下一步改什么" | 查看"架构原则是什么" |

## 实测证据

本次 session（2026-08-07）搜索 "gh 工作进度"：

- **仅搜索 env-migrations/**：命中 `env-migration-gh-work-progress-2026-08-06-111453.md`（详细改造清单：P0/P1/P2 脚本改造方案）
- **扩展搜索 vaults/**：额外命中 `vaults/vault-demo/wiki/projects/progress/gh-scene-current-progress.md`（速查看板）、`wiki/conclusions/git-gh-source-truth-verification-design.md`（L1-L5 架构设计）、`wiki/learnings/git-gh-polyrepo-pr-issue-relationship-2026-08-04-154240.md`（踩坑记录）
- **结果**：两者结合才构成 "改什么 + 为什么改 + 设计原则 + 已知陷阱" 的完整上下文

## 对搜索优先级的启示

P0 树状自说明不应仅限于 task 内部导航文件（README/INDEX/CHEATSHEET），当搜索意图涉及进度、设计、决策、踩坑时，**必须扩展至 devroot/vaults/**（若存在）。

## 多端多根注意事项

- vaultroot 路径不固定，devroot/vaults/ 只是当前仓库内的一个 vault 挂载点
- 搜索前应先探测目录存在性，不存在时 HITL 询问用户，禁止硬编码
