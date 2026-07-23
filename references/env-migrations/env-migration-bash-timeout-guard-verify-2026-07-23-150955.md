---
title: bash-timeout-guard Hook 生效实测验证
description: 通过 130 秒完全静默脚本实测，验证 bash-timeout-guard.ts hook 已将 bash 默认 timeout 从 120s 提升到 600s。
date: 2026-07-23
meta:
  version: 1.0
---

# env-migration-bash-timeout-guard-verify-2026-07-23-150955

> **Session 主题**：验证 OpenCode bash-timeout-guard Plugin 是否真实生效
> **触发原因**：之前已部署 `bash-timeout-guard.ts`，但需用控制变量法实证 hook 是否确实将 bash 默认 timeout 从 120s 提升到 600s
> **风险等级**：低（仅验证，不改任何配置）


## 一、文本文件变更清单

本次 session 不涉及文本文件变更。


## 二、非文本操作

### 2.1 编写验证脚本

| 操作类型 | 路径 | 说明 |
|---------|------|------|
| 新建临时脚本 | `venv/tmp/test-silent.py` | 开始/结束各打印一次时间戳，中间 130 秒完全静默，零 stdout 输出 |

脚本内容：
```python
import time
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

start = datetime.now()
print(f"[test] start at {start.isoformat()}")
print(f"[test] will sleep 130 seconds with NO output...")
sys.stdout.flush()

time.sleep(130)  # 完全静默 130 秒

end = datetime.now()
elapsed = (end - start).total_seconds()
print(f"[test] end at {end.isoformat()}")
print(f"[test] elapsed: {elapsed:.1f}s")
print(f"[test] completed successfully — process was NOT killed by timeout")
```

### 2.2 执行验证

| 操作 | 命令 | 说明 |
|------|------|------|
| bash 调用 | `python.exe venv/tmp/test-silent.py` | **未传 timeout 参数**，依赖文档默认值 120s |

**关键控制变量**：
- 脚本中间 **130 秒无任何 stdout 输出**
- 若 hook 未生效 → 120s 时因"无输出静默超时"被 kill
- 若 hook 生效 → timeout 被提升到 600s，130s 正常完成


## 三、验证结果

```
[test] start at 2026-07-23T14:58:47.203285
[test] will sleep 130 seconds with NO output...
[test] end at 2026-07-23T15:00:57.203769
[test] elapsed: 130.0s
[test] completed successfully — process was NOT killed by timeout
```

| 指标 | 值 | 结论 |
|------|-----|------|
| 文档默认 timeout | 120000ms (120s) | 未变 |
| 实测执行时长 | 130.0s | 超过 120s |
| 中间 stdout 输出 | 0 行 | 完全静默 |
| 是否被 kill | 否 | ✅ 正常完成 |
| hook 是否生效 | **是** | timeout 被提升到 600s |


## 四、hook 生效的辅助证据

`venv/.opencode/plugin/hook-log.jsonl` 中的 `timeout_adjusted` 记录：

```json
{"action":"timeout_adjusted","oldTimeout":0,"newTimeout":600000}
{"action":"timeout_adjusted","oldTimeout":120000,"newTimeout":600000}
```

- `oldTimeout: 0` → 未传 timeout 的 bash 调用被提升到 600s
- `oldTimeout: 120000` → 显式传了 120s 的调用也被提升到 600s


## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 | 实际结果 |
|---|---------|----------|---------|---------|
| 1 | 确认 plugin 文件存在 | `Test-Path venv/.opencode/plugin/bash-timeout-guard.ts` | `True` | ✅ |
| 2 | 130s 静默脚本执行 | `bash` 调用 `test-silent.py`，不传 timeout | 不被 kill，正常完成 | ✅ |
| 3 | 检查 hook 日志 | `Select-String hook-log.jsonl -Pattern timeout_adjusted` | 存在记录 | ✅ |


## 六、回滚方案

无需回滚（本次仅验证，未改配置）。

若需移除 hook：
```powershell
Remove-Item "venv/.opencode/plugin/bash-timeout-guard.ts"
```
（需重启 session 生效）


## 七、踩坑记录

### 踩坑 1：最初用 show-progress（每秒输出）验证，无法排除"stdout 活跃免杀"假说

- **现象**：第一次测试脚本每秒输出一行，130s 跑完
- **问题**：无法区分是 hook 生效，还是 bash 的"无输出静默超时"机制因持续 stdout 而未触发
- **修复**：改为**完全静默 130 秒**的脚本，消除 stdout 干扰变量

### 踩坑 2：测试过程中用户中断了两次

- **现象**：前两次执行被用户手动 abort
- **原因**：用户想确认我理解验证逻辑，而非真的想中断
- **结果**：第三次执行完整跑完 130s，验证成功


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-23-150955 |
| **更新人** | Human + Agent Session |
| **变更触发** | bash-timeout-guard hook 生效性需实证 |
| **下次修订条件** | hook 逻辑变更 / timeout 阈值调整 / plugin 架构升级 |
| **跨环境迁移参考** | 复制 `bash-timeout-guard.ts` 到新环境 `venv/.opencode/plugin/` + 重启 session + 按「验证清单」执行 |
