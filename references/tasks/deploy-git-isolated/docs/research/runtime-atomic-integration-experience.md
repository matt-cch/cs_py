---
title: 运行时域原子脚本集成经验
description: 将 references/runtime/ 下的 verify-runtime 与 download-runtime-tool 重构为 task 插件体系原子脚本的完整踩坑、决策与修复路径。
date: 2026-06-26
meta:
  version: 1.0.0
---

# 运行时域原子脚本集成经验

> **范围**：`references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/`、`verify-runtime/`、`download-runtime/`
> **目标**：替代 `references/runtime/verify-runtime.py` 和 `download-runtime-tool.py`，走原子脚本体系
> **时间**：2026-06-26


## 1. 背景与目标

原 `references/runtime/` 下的 `verify-runtime.py` 和 `download-runtime-tool.py` 是单体脚本，职责混杂、步骤黑盒、不可独立测试。本次任务将其拆分为 task 插件体系下的原子脚本 + workflow 编排器，实现：

- 每个步骤独立可测（CLI 原子）
- 检测与下载职责分离（verify-runtime/ vs download-runtime/）
- 公共能力复用（runtime-common/）
- 进度条、时间戳、路由探测全部可见


## 2. 架构决策

### 2.1 目录隔离

| 目录 | 职责 | 典型文件 |
|------|------|---------|
| `runtime-common/` | 公共原子，跨 workflow 复用 | `atomic-detect-local.py`、`atomic-query-upstream.py`、`atomic-compare-version.py`、`atomic-generate-report.py` |
| `verify-runtime/` | 真源检测编排 | `wf-verify-runtime.py` |
| `download-runtime/` | 下载编排 + 独有原子 | `wf-download-runtime.py`、`atomic-01-route-probe.py` ~ `atomic-05-cleanup-temp.py` |

### 2.2 命名规范

- `wf-` 前缀：workflow 编排器，不负责具体业务逻辑，只负责步骤串联
- `atomic-` 前缀：单职责 CLI 原子，接受参数、输出 JSON、可被 workflow 或人工直接调用

### 2.3 编码与输出约定

- 所有 `.py` 脚本开头 `sys.stdout.reconfigure(encoding="utf-8")`
- `process_runner.py` 增加 `sys.stderr.reconfigure(encoding="utf-8")` + `atexit.register(_restore_encoding)`，确保子进程编码切换后必恢复
- 进度条走 `sys.stderr.write()`，避免被 `capture_output=True` 吞掉
- workflow 调用下载原子时，`stderr=None` 透传，而非 `capture_output=True`


## 3. 踩坑与修复

### 3.1 进度条被吞（最严重的设计缺陷）

**现象**：`wf-download-runtime.py` 调用 `atomic-02-download-file.py` 时，下载进度完全看不到，命令返回空。

**根因**：workflow 使用统一的 `run_atomic()` 封装，内部是 `subprocess.run(capture_output=True, ...)`，把子进程的 stdout 和 stderr 全部捕获进 buffer。下载原子的进度条（`print(..., flush=True)`）被吞进 stdout buffer，长时间无输出导致 bash 超时截断。

**修复**：workflow 中下载步骤单独处理——`stdout=subprocess.PIPE` 捕获最终 JSON，`stderr=None` 透传进度条到终端。

```python
# 错误：进度条被吞
result = subprocess.run(cmd, capture_output=True, ...)

# 正确：stdout 捕获 JSON，stderr 透传进度条
result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=None, ...)
```

**教训**：凡是需要人眼看到实时进度的子进程，必须 `stderr=None` 或 `stdout=None` 透传，不能用 `capture_output=True` 一刀切。

### 3.2 路由探测串行太慢

**现象**：opencode release 下载前，路由探测花了 **68 秒**。

**根因**：`atomic-01-route-probe.py` 对 7 个代理串行 `for` 循环 HEAD 探测，每个超时 10 秒，部分代理连接超时后累计耗时极高。

**修复**：引入 `concurrent.futures.ThreadPoolExecutor`，7 个代理并发探测，超时缩至 5 秒。最坏情况从 70 秒降到 5 秒。

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=len(GITHUB_PROXIES)) as executor:
    futures = {executor.submit(_probe_one, proxy, url, timeout): proxy for proxy in GITHUB_PROXIES}
    ...
```

### 3.3 GitHub Release 直连可达但极慢

**现象**：`atomic-01-route-probe.py` 对 GitHub HEAD 探测返回 200（延迟 2198ms），判定"直连可用"，但实际下载时 TCP 吞吐量极差，速度仅几十 KB/s。

**根因**：HEAD 探测只验证了 HTTP 可达性，没验证实际下载带宽。GitHub 直连在部分网络环境下能通但极慢。

**修复**：增加 `is_release_download = "/releases/download/" in url` 判断，GitHub Release 文件下载直接跳过直连，强制走代理探测。

```python
if not is_release_download:
    # 探测直连（API、页面等）
else:
    # GitHub Release 下载：跳过直连，直接探测代理
```

### 3.4 workflow 中存在 input() 阻塞

**现象**：`wf-download-runtime.py` 下载完后弹出 `input("请输入: ")` 等用户确认是否替换，自动化调用时直接挂起。

**根因**：脚本设计时保留了交互式确认环节，但未考虑 CI/CD 和 Agent 自动化场景。

**修复**：删除 `input()`，默认行为改为"下载完成，不替换"。如需替换，单独调用 `atomic-04-backup-replace.py`。

### 3.5 备份替换原子先 rename 再检查源目录

**现象**：误跑 `atomic-04-backup-replace.py` 后，`venv/node/` 被重命名为 `venv/node-backup-...`，但脚本随后报错"源目录不存在"，原目录已消失。

**根因**：`backup_and_replace()` 函数的执行顺序是：先 `shutil.move(tool_dir, backup_name)` 备份，再检查 `os.path.exists(source_dir)`。如果 source_dir 本来就不存在，备份已经完成，原目录已经没了。

**修复**：调整顺序，先检查源目录是否存在，不存在立即返回错误，不做任何备份操作。

```python
# 错误顺序
shutil.move(tool_dir, backup_name)  # 这里已经毁了原目录
if not os.path.exists(source_dir):
    return error

# 正确顺序
if not os.path.exists(source_dir):
    return {"error": "源目录不存在"}
# 再执行备份和替换
```

**教训**：任何会修改文件系统的操作，必须先做全部前置条件检查，条件不满足时必须是**无副作用**的。

### 3.6 JSON 语法错误（反斜杠未转义）

**现象**：`verified-task-index.json` 更新后，`run-lint.py` 报 `JSONDecodeError: Invalid escape`。

**根因**：新增条目中的 `entry_command` 包含 Windows 路径反斜杠，其中 `\r`、`	`、`
` 等字符在 JSON 字符串中未转义，导致解析失败。

**修复**：将反斜杠统一替换为双反斜杠 `\\`。

```json
// 错误
"entry_command": "read '${devroot}\references\runtime\verified-trigger-index.json'"

// 正确
"entry_command": "read '${devroot}\\\\references\\\\runtime\\\\verified-trigger-index.json'"
```

### 3.7 一体化 workflow 缺少 --force 透传

**现象**：`wf-runtime-full.py` 只能按版本对比结果决定是否下载，无法强制下载。

**修复**：增加 `--force` 参数，版本对比后 `if need or args.force:` 进入下载流程。


## 4. 最终验证

### 4.1 检测链路

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py" --devroot "${devroot}" --tool node
```

输出：
```
[detect] exe_exists=True, version=26.4.0
[query] upstream=26.4.0, source=阿里云 nodejs-release
[compare] 已是最新版
```

### 4.2 下载链路（带进度条）

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py" --devroot "${devroot}" --tool-name opencode_cli --show-progress
```

输出：实时百分比进度条 + 最终 JSON。

### 4.3 一体化 workflow（检测+下载）

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\runtime-common\wf-runtime-full.py" --devroot "${devroot}" --tools node,opencode_cli --force
```

全程带 `HH:MM:SS.mmm` 时间戳，检测->下载->解压验证，无需人工干预。


## 5. 可复用经验

| 经验 | 适用场景 |
|------|---------|
| `stderr=None` 透传进度条 | 任何需要实时进度的子进程调用 |
| ThreadPoolExecutor 并发探测 | 多候选路由/代理/端点的可用性扫描 |
| 先检查后行动（无副作用失败） | 任何会修改文件系统的原子操作 |
| `sys.stdout.reconfigure(encoding="utf-8")` + `atexit` 恢复 | 所有在 Windows PowerShell 5.1 下输出中文的 Python 脚本 |
| `capture_output=True` 一刀切是陷阱 | workflow 封装子进程调用时必须按步骤区分 stdout/stderr 策略 |
| GitHub Release 直连不可信 | 国内网络环境下，GitHub Release 文件下载应默认走代理 |


## 6. 修订联动记录

| 文件 | 修改内容 |
|------|---------|
| `verified-task-index.json` | 新增 `wf-verify-runtime`、`wf-download-runtime`、6 个 atomic、1 个 `wf-runtime-full` |
| `TASK-TOOLS-INDEX.md` | 追加运行时域工具表格 + CLI 用法 |
| `EXEC-CHEATSHEET.md` | Stage S8 追加 `wf-runtime-full` 推荐命令 |
| `docs/research/runtime-atomic-integration-experience.md` | 本文档 |


*文档版本: 1.0.0*  
*创建时间: 2026-06-26*
