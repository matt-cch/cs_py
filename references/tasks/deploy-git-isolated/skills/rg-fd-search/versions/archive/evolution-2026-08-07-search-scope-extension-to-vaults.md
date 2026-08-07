---
title: P0 树状自说明搜索范围扩展 — 覆盖 devroot/vaults/ 认知资产
description: 将 rg-fd-search 的 P0 树状自说明搜索范围从 task 内部文档扩展至 devroot/vaults/，建立探测+HITL机制，对齐多端多根原则
date: 2026-08-07
type: evolution
scope: add
category: workflow
target_section: "#### P0 — 树状自说明文档"
meta:
  version: "1.0.0"
  tags: [search-scope, vaults, p0, hitl, polyrepo]
fingerprint:
  content_sha256: evolution-search-scope-extension-to-vaults-20260807
  semantic_key: search-scope-vaults
---

# P0 树状自说明搜索范围扩展 — 覆盖 devroot/vaults/ 认知资产

## 问题

原 P0 树状自说明仅覆盖 task 内部文档（README.md / TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md / SOP.md 等）。

实际 session 中，用户搜索 "gh 工作进度" 时：
- env-migrations/ 命中了改造清单（"改了什么文件、第几行"）
- 但 **缺失** devroot/vaults/ 下的进度看板、架构设计、踩坑记录等认知资产
- 导致搜索结果不完整，丢失 "为什么这么设计" 的上下文

## 修正：P0 扩展规则

### 扩展范围

当搜索意图涉及以下语义时，P0 树状自说明 **必须** 扩展至 devroot/vaults/：

| 搜索意图 | vaults/ 下典型对应目录 |
|---------|----------------------|
| 工作进度、项目进度 | `vaults/*/wiki/projects/progress/` |
| 架构设计、技术决策 | `vaults/*/wiki/conclusions/` |
| 踩坑记录、陷阱复盘 | `vaults/*/wiki/gotchas/` |
| 模式沉淀、认知积累 | `vaults/*/wiki/learnings/` |
| 基线规则、行为约束 | `vaults/*/baseline/` |

### 不硬编码原则（多端多根对齐）

1. **默认探测**：先检测 `devroot/vaults/` 是否存在（`Test-Path` / `os.path.exists`）
2. **若存在**：直接纳入 P0 搜索范围
3. **若不存在**：**暂停搜索，HITL 询问用户** — "devroot 下未找到 vaults/ 目录，请确认当前 vault 挂载路径"
4. **禁止假设**：不得将 vault 路径硬编码为 `devroot/vaults/` 或任何固定路径写入代码/配置

> 原因：vaultroot 为多端不固定根目录，devroot/vaults/ 只是当前仓库内的一个 vault 挂载点，非全局默认值。

### 搜索执行模板

```powershell
# Step 0: 探测 vaults 目录
$vaultsDir = Join-Path $devroot "vaults"
if (Test-Path $vaultsDir) {
    # 纳入 P0 搜索
    & "${devroot}\venv\ripgrep\rg.exe" -n -C 3 "关键词" "$vaultsDir"
} else {
    # HITL: 询问用户 vault 实际路径
    Write-Host "[HITL] devroot/vaults/ 不存在，请确认 vault 挂载路径"
}
```

## vaults/ 与 env-migrations/ 的互补关系

| 维度 | env-migrations/ | vaults/ |
|------|----------------|---------|
| 内容性质 | 工程变更记录 | 认知资产沉淀 |
| 回答的问题 | "改了什么" | "为什么这么设计" |
| 典型内容 | 文件变更、行号、验证命令 | 架构设计、决策依据、踩坑记录、进度看板 |
| 阅读对象 | Agent 执行时参考 | Agent 理解上下文时参考 |
| 更新频率 | 按 session 追加 | 按结论收敛更新 |

两者 **必须互补查询**，缺失任一都会导致上下文断裂。

## 关联

- 触发本次演进的 session：`env-migration-gh-work-progress-2026-08-06-111453.md`
- 对应的 learning：`learning-2026-08-07-vaults-env-migrations-division-pattern.md`
