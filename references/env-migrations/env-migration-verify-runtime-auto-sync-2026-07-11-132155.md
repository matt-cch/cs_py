---
title: verify-runtime 自动回写机制建设 — 消除人工路径更新
description: 解决真源检测后 resolved_path 未自动回写索引/配置导致的 update-version 检测失败问题。建设 manifest 上下文传递 + 自动索引回写闭环。
date: 2026-07-11
meta:
  version: "1.0.0"
  related_files:
    - references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_version.py
    - references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-detect-local.py
    - references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py
    - references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py
    - .cursor/rules/high-frequency-verify-runtime.mdc
    - references/runtime/verified-task-index.json
---

# verify-runtime 自动回写机制建设

## 问题根因

真源检测（`wf-verify-runtime.py`）执行时，`atomic-detect-local.py` 会通过 `candidate_paths` 扫描找到实际存在的工具路径（如 cursor 实际在 `D:\tools\cursor\Cursor.exe`）。

但检测完成后：
- `resolved_path` 只进了报告 JSON，**没有回写**到 `verified-runtime-index.json` 的 `executable`
- `tools_config.json` 的 `exe_path` 仍然是过时的 `C:\Program Files\cursor\Cursor.exe`
- 后续 `update-version.py` 读的是过时路径，检测直接失败（"文件不存在"）

## 修改意图

1. **消除人工环节**：检测到的实际命中路径应自动同步到所有消费方，禁止 Agent 手工改路径
2. **唯一真源原则**：`runtime_version.detect()` 作为底层检测能力，被 `wf-verify-runtime.py` 和 `update-version.py` 共同调用，确保二者看到同一套路径解析逻辑
3. **上下文可追溯**：引入 `manifest` 机制，底层写出完整探测过程（primary_path / fallback_paths / candidate_paths 各条目的存在性状态），上层按 manifest 回写索引，而非自行重新探测

## 涉及文件变更

| # | 文件 | 变更内容 |
|---|------|---------|
| 1 | `py-plugins/runtime_version.py` | `detect()` 新增 `index_path`、`tool_name`、`manifest_path` 参数；主路径 miss 时 fallback 扫描索引 candidate_paths；检测完成后把完整上下文写入 manifest |
| 2 | `runtime-common/atomic-detect-local.py` | 新增 `--manifest-path` 参数；透传给 `runtime_version.detect()`；同步 `resolved_path` 回写 |
| 3 | `verify-runtime/wf-verify-runtime.py` | 新增 `--dry-run` / `--no-sync` 参数；Step 6 新增 `_sync_index_and_config()`：按 manifest 回写 `executable`、`version`、`verified_at`、`candidate_paths[].status` 到索引，回写 `exe_path` 到 tools_config |
| 4 | `py-tools/update-version.py` | 调用 `runtime_version.detect()` 时传入 `index_path`、`tool_name`、`manifest_path`，复用底层 candidate_paths fallback |
| 5 | `.cursor/rules/high-frequency-verify-runtime.mdc` | 补充 `--dry-run` / `--no-sync` 参数说明；更新"执行后动作"描述 |
| 6 | `references/runtime/verified-task-index.json` | 更新 `wf-verify-runtime` 条目 description + entry_command + verified_at；更新 `verify_runtime` 高频任务 description + verified_at |

## 数据流示意

```
wf-verify-runtime.py
    ↓ 调用
atomic-detect-local.py --manifest-path venv/tmp/detect-{tool}.json
    ↓ 调用
runtime_version.detect(index_path=..., tool_name=..., manifest_path=...)
    ↓ 写入
manifest: {primary_path, fallback_paths[], candidate_paths[], resolved_path, local_version}
    ↓ wf-verify-runtime.py Step 6 读取
_sync_index_and_config(manifest)
    ↓ 回写
verified-runtime-index.json: executable, version, verified_at, candidate_paths[].status
    ↓ 回写
tools_config.json: local.exe_path
```

## 验证清单

- [x] `--no-sync` 模式不改数据（索引和配置保持原状）
- [x] 正常模式自动回写 cursor：
  - `verified-runtime-index.json` `executable` → `D:\tools\cursor\Cursor.exe`
  - `candidate_paths`：`D:\tools\cursor\` → `verified_hit`，其余 → `missing`
  - `tools_config.json` `cursor.local.exe_path` → `D:\tools\cursor\Cursor.exe`
- [x] `update-version.py --tool cursor` 成功检测到 `3.11.13 @ D:\tools\cursor\Cursor.exe`
- [x] 全部修改文件通过 `run-lint.py`（Python 语法 + encoding）

## 命令速查

```powershell
# 只检测，不回写任何文件
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}" --dry-run

# 检测并生成报告，但不回写索引/配置
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}" --no-sync

# 检测并自动回写（默认行为）
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}"

# 仅检测指定工具并回写
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}" --tool cursor
```

## 反模式（禁止）

- 禁止 Agent 在真源检测后手工改 `verified-runtime-index.json` 的 `executable` 或 `tools_config.json` 的 `exe_path`
- 禁止 `update-version.py` 自行实现 candidate_paths 扫描逻辑（已有 `runtime_version.detect()` 统一处理）
- 禁止在命令行里构造 JSON 字符串传给 atomic 脚本（`--config-json` 应由 workflow 内部生成）

## 后续建议

1. `wf-download-runtime.py` 在下载替换完成后，应调用相同的 `_sync_index_and_config()` 逻辑，确保下载后的路径也自动同步
2. 考虑在 `verified-runtime-index.json` 中增加 `auto_synced` 标记，区分"人工更新"和"脚本自动回写"


*修订联动：本 env-migration 已同步更新以下导航/索引文件*
- `.cursor/rules/high-frequency-verify-runtime.mdc`（参数说明 + 执行后动作）
- `references/runtime/verified-task-index.json`（wf-verify-runtime + verify_runtime 条目）
- `references/env-migrations/README.md`（导航表追加）
