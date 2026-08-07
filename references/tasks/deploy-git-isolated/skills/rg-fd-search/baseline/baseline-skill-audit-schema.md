---
title: 审计基准 — Skill Execution Audit Schema（SEAS）
description: 定义 rg-fd-search skill 执行过程的可观测指标、审计日志 schema、记录时机与查询方式。将抽象的"命中次数检验"落地为可追加、可聚合、可查询的 JSON Lines 审计轨迹。
date: 2026-08-07
meta:
  version: "1.0.0"
  tags: [seas, audit, metrics, jsonl, skill, execution-log]
---

# Skill Execution Audit Schema（SEAS）

## 一、问题背景

`baseline-sed-mechanism.md` 中定义了 evolution 有效性检验标准（短期/中期/长期），但缺少**可落地的指标采集机制**：

- "evolution 被引用 >= 3 次" —— 引用次数记在哪里？
- "同一问题是否复现" —— 如何回溯历史异常？
- "Human feedback 频率是否减少" —— 基准值和当前值各是多少？

本 baseline 将上述抽象检验标准落地为**可执行、可追加、可聚合**的审计轨迹系统。

## 二、SEAS 核心设计

### 2.1 一句话定义

**每次 skill 主工作流执行完毕后，Agent 在 `versions/audit-trail.jsonl` 中追加一行结构化 JSON 记录本次执行的搜索路径、合规状态、SED 事件与异常信息。定期（收敛时）将 audit-trail.jsonl 聚合为 `versions/metrics.json` 可读视图。**

### 2.2 为什么选择 JSON Lines

| 方案 | 优劣 | 结论 |
|------|------|------|
| 扩展 manifest.json | 每次追加需读-改-写整个 JSON，易冲突 | ❌ 不适用高频追加 |
| 独立 SQLite 数据库 | 过重，引入依赖，与项目轻量原则冲突 | ❌ 不适用 |
| **JSON Lines（.jsonl）** | 追加模式（单行原子写入），无需读旧内容，天然支持并发 | ✅ **选定** |
| 纯文本日志 | 无结构，难以聚合分析 | ❌ 不适用 |

### 2.3 文件位置

```
skills/rg-fd-search/versions/
├── manifest.json          # 版本索引 + 演进历史
├── metrics.json           # 聚合视图（由 audit-trail.jsonl 定期汇总生成）
├── audit-trail.jsonl      # 原始审计轨迹（逐行追加，只增不改）
└── archive/               # 已收敛 evolution 归档
```

> **铁律**：`audit-trail.jsonl` 为**只增不改**文件。Agent 只允许在末尾追加新行，禁止修改、删除已有记录。

## 三、Audit Record Schema（单条记录结构）

每行一个 JSON 对象，字段定义如下：

```json
{
  "meta": {
    "timestamp": "2026-08-07T10:57:16+08:00",
    "session_marker": "20260807-105716",
    "agent_version": "opencode-kimi-k2.6"
  },
  "trigger": {
    "trigger_word": "查找",
    "user_intent_summary": "搜索 gh 工作进度",
    "intent_category": "progress_query"
  },
  "search_path": {
    "p0": {
      "executed": true,
      "hit": true,
      "files_accessed": ["TASK-TOOLS-INDEX.md"],
      "notes": "命中 §1.10 GitHub CLI"
    },
    "p1": {
      "executed": true,
      "hit": false,
      "files_accessed": ["ENTRY.json", "verified-task-index.json"],
      "notes": "无 gh_cli 条目"
    },
    "p2": {
      "executed": true,
      "hit": true,
      "files_accessed": ["atomic-query-upstream.py"],
      "notes": "docstring 命中"
    },
    "p3": {
      "executed": true,
      "hit": true,
      "files_accessed": ["env-migrations/*.md"],
      "notes": "兜底搜索命中 8 份文档"
    }
  },
  "compliance": {
    "audit_block_output": true,
    "search_priority_audit_completed": true,
    "shell_audit_completed": true,
    "native_fallback_used": false,
    "native_fallback_reason": null,
    "skill_loaded_before_execution": true,
    "skill_loaded_method": "read_disk"
  },
  "outcome": {
    "report_delivered": true,
    "user_satisfaction": "confirmed",
    "missing_context_found": true,
    "missing_context_note": "初始未搜索 vaults/，经用户提醒后补查"
  },
  "sed": {
    "self_check_triggered": true,
    "new_cognition_detected": true,
    "suggested_to_human": true,
    "human_decision": "accepted",
    "sed_type": "evolution",
    "sed_files_created": [
      "evolutions/evolution-2026-08-07-search-scope-extension-to-vaults.md",
      "learnings/learning-2026-08-07-vaults-env-migrations-division-pattern.md"
    ]
  },
  "exceptions": []
}
```

### 3.1 字段详解

| 字段路径 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| `meta.timestamp` | string | ✅ | ISO 8601 格式，由 `get-timestamp.py --format iso` 生成 |
| `meta.session_marker` | string | ❌ | 用户提供的 session 标识，便于跨文件关联 |
| `meta.agent_version` | string | ❌ | Agent 模型标识，用于追溯模型级偏差 |
| `trigger.trigger_word` | string | ✅ | 命中 skill 的触发词 |
| `trigger.user_intent_summary` | string | ✅ | 用户意图一句话摘要 |
| `trigger.intent_category` | string | ❌ | 意图分类：`file_search` / `content_search` / `progress_query` / `docstring_search` / `combined` |
| `search_path.p0-p3` | object | ✅ | 四层搜索的执行状态 |
| `search_path.*.executed` | bool | ✅ | 该层是否实际执行 |
| `search_path.*.hit` | bool | ✅ | 该层是否命中结果 |
| `search_path.*.files_accessed` | array | ❌ | 实际访问的文件列表 |
| `compliance.audit_block_output` | bool | ✅ | 是否输出了【rg/fd 搜索优先级审计】块 |
| `compliance.native_fallback_used` | bool | ✅ | 是否 fallback 到原生 grep/glob |
| `compliance.skill_loaded_before_execution` | bool | ✅ | 执行前是否已加载配套 skill |
| `outcome.report_delivered` | bool | ✅ | 是否向用户交付了最终报告 |
| `outcome.user_satisfaction` | string | ❌ | `confirmed` / `partial` / `rejected` / `pending` |
| `outcome.missing_context_found` | bool | ❌ | 事后是否发现遗漏了关键上下文 |
| `sed.self_check_triggered` | bool | ✅ | 是否执行了 SED 自检 |
| `sed.suggested_to_human` | bool | ❌ | 是否向用户建议了 SED |
| `sed.human_decision` | string | ❌ | `accepted` / `declined` / `deferred` / null |
| `sed.sed_type` | string | ❌ | `gotcha` / `evolution` / `learning` / `baseline` |
| `sed.sed_files_created` | array | ❌ | 实际创建的 SED 文件列表 |
| `exceptions` | array | ✅ | 执行过程中的异常列表（空数组表示无异常） |

### 3.2 异常记录格式

```json
{
  "exceptions": [
    {
      "type": "ParserError",
      "layer": "p3",
      "command": "powershell -Command ...",
      "message": "Expressions are only permitted as the first element of a pipeline",
      "recovery": "改用 if/else 语法，二次验证通过",
      "recorded_gotcha": "gotcha-2026-08-06-ps51-ternary-operator-parser-error.md"
    }
  ]
}
```

## 四、记录时机与操作方式

### 4.1 记录时机

```
skill 主工作流执行完毕
    ↓
【强制】输出 SED 自检结果
    ↓
【强制】输出执行审计记录（本步骤）
    ↓
将审计记录追加到 audit-trail.jsonl
    ↓
输出"下一步建议"
```

### 4.2 操作方式（Agent 执行模板）

**Step 1：构造审计记录**

Agent 在内存中构造符合 schema 的 JSON 对象（基于本次执行的实际状态）。

**Step 2：追加到 audit-trail.jsonl**

```powershell
# 追加单行 JSON 到 audit-trail.jsonl（追加模式，不读取旧内容）
$auditRecord = '{"meta":{"timestamp":"2026-08-07T10:57:16+08:00"},...}'
Add-Content -Path "${devroot}\references\tasks\deploy-git-isolated\skills\rg-fd-search\versions\audit-trail.jsonl" -Value $auditRecord -Encoding UTF8
```

**禁止行为**：
- ❌ 读取整个 audit-trail.jsonl 后再写回（破坏追加模式优势）
- ❌ 修改或删除已有行
- ❌ 将审计记录写入其他位置（如 env-migration 或临时文件）

**Step 3：输出审计确认**

```
【Skill 执行审计记录】
- 记录时间: 2026-08-07T10:57:16+08:00
- 审计轨迹: versions/audit-trail.jsonl（已追加）
- 本次执行: P0命中=是, P1命中=否, P2命中=是, P3命中=是
- 合规状态: audit_block=✓, skill_loaded=✓, native_fallback=✗
- SED 事件: self_check=✓, suggested=✓, human_decision=accepted
- 异常: 0 个
```

## 五、聚合查询方式

### 5.1 实时聚合：metrics.json

收敛时（evolutions>=5 / gotchas>=10 / >=30天），由 `scripts/` 下的聚合脚本读取 `audit-trail.jsonl` 生成 `metrics.json`：

```json
{
  "generated_at": "2026-08-07T10:57:16+08:00",
  "period": {
    "from": "2026-08-05",
    "to": "2026-08-07"
  },
  "summary": {
    "total_executions": 12,
    "p0_hit_rate": 0.92,
    "p1_hit_rate": 0.58,
    "p2_hit_rate": 0.33,
    "p3_fallback_rate": 0.25,
    "native_fallback_count": 0,
    "audit_block_compliance_rate": 1.0,
    "skill_loaded_rate": 0.83,
    "sed_suggested_rate": 0.42,
    "sed_accepted_rate": 0.80,
    "exception_rate": 0.08
  },
  "evolution_effectiveness": {
    "evolution-2026-08-07-search-scope-extension-to-vaults": {
      "executions_since_applied": 3,
      "p0_vaults_hit": 1,
      "missing_context_after": 0
    }
  }
}
```

### 5.2 临时查询：rg/fd 直接查 audit-trail

```powershell
# 查询最近 10 次执行
& "${devroot}\venv\ripgrep\rg.exe" -n "" "${devroot}\references\tasks\deploy-git-isolated\skills\rg-fd-search\versions\audit-trail.jsonl" | Select-Object -Last 10

# 查询包含异常记录的行
& "${devroot}\venv\ripgrep\rg.exe" -n '"exceptions":\s*\[' "${devroot}\references\tasks\deploy-git-isolated\skills\rg-fd-search\versions\audit-trail.jsonl"
```

## 六、与 SED 机制的联动

| SED 阶段 | audit-trail 作用 |
|---------|-----------------|
| **自检触发** | 基于本次执行实时构造记录，为自检提供结构化输入 |
| **Human 决策** | `sed.human_decision` 字段记录用户选择，作为后续分析的决策依据 |
| **evolution 有效性检验** | 通过查询 `audit-trail.jsonl` 中 `sed.sed_files_created` 被引用次数，验证">=3 次"标准 |
| **收敛分析** | `metrics.json` 中的命中率、合规率、异常率，为 SKILL.md 收敛提供数据支撑 |
| **反面教材追溯** | `exceptions` 数组中的 `recorded_gotcha` 字段，可反向关联到 gotcha 文档 |

## 七、Human 偏好声明

> **用户明确确认（2026-08-07）**：
> 1. 抽象的"命中次数检验"必须有可落地的实现，不能停留在理论设计。
> 2. 审计日志应轻量、可追加、不破坏现有 SED 架构。
> 3. Agent 每次 skill 执行后应在"下一步建议"之前输出审计记录并追加到 audit-trail.jsonl。
> 4. Human 保留查看、查询、分析审计轨迹的权利，但不强制要求 Human 每次审阅原始日志。

## 八、版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-08-07 | 初始创建：SEAS schema 定义、JSON Lines 载体、记录时机、聚合方式、与 SED 联动 |
