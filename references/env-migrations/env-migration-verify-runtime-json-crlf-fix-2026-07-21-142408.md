---
title: 修复 verify-runtime JSON 回写 CRLF 缺陷
description: wf-verify-runtime.py 回写 verified-runtime-index.json 时产生 CRLF，导致每次真源检测后都需要 run-lint --fix 修复。通过显式传入 newline="\n" 根治。
date: 2026-07-21
meta: {}
---

# 修复 verify-runtime JSON 回写 CRLF 缺陷

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 修复 wf-verify-runtime.py JSON 落盘产生 CRLF 的缺陷 |
| **日期** | 2026-07-21 |
| **文件名时间戳** | `2026-07-21-142408` |
| **触发原因** | 用户观察到每次执行真源检测后，verified-runtime-index.json 都出现 465 处 CRLF，需事后修复 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py` |
| **风险等级** | 低（仅修改文件写模式参数，无业务逻辑变更） |


## 一、文本文件变更清单

### 1. 修改 `wf-verify-runtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/verify-runtime/wf-verify-runtime.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 两处 `open(...)` 增加 `newline="\n"` 参数 |
| **插入位置** | 第 355 行、第 372 行 |
| **作用** | 强制 JSON 回写使用 LF 换行符，避免 Windows 平台默认 CRLF |
| **验证方式** | 执行真源检测后，对 `verified-runtime-index.json` 执行 lint，CRLF 应为 0 |
| **迁移方式** | 直接覆盖 |

**具体变更（diff）**：

```python
# 第 355 行（回写 verified-runtime-index.json）
- with open(index_path, "w", encoding="utf-8") as f:
+ with open(index_path, "w", encoding="utf-8", newline="\n") as f:
      json.dump(index, f, ensure_ascii=False, indent=4)

# 第 372 行（回写 tools_config.json）
- with open(config_path, "w", encoding="utf-8") as f:
+ with open(config_path, "w", encoding="utf-8", newline="\n") as f:
      json.dump(config, f, ensure_ascii=False, indent=2)
```

> **根因说明**：Python 的 `open()` 在 Windows 上默认 `newline=None`，会自动将 `\n` 转换为 `\r\n`。`json.dump()` 继承文件对象的换行符行为，因此每次回写都产生 CRLF。


## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移或目录创建。


## 三、环境变量速查

无需变更环境变量。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文档） | `run-lint.py` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.py`（修复后脚本） | `run-lint.py` | Python 语法 + 编码 | 通过 |

**已执行验证**：

```powershell
# 脚本本身 lint
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\verify-runtime\wf-verify-runtime.py"
# 结果：✅ 全部通过

# 独立验证 newline="\n" 效果
"${devroot}\venv\py\python.exe" "${devroot}\venv\tmp\test_lf_write.py"
# 结果：CRLF: 0, LF: 5, PASS
```


## 五、验证清单（新环境/后续复测）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 执行真源检测 | `wf-verify-runtime.py --devroot "${devroot}"` | 正常完成 |
| 2 | 检查索引文件换行符 | `run-lint.py --files "verified-runtime-index.json"` | CRLF=0, LF>0 |
| 3 | 确认无需事后修复 | 检测完成后直接 lint，不应出现 CRLF 违规 | ✅ 全部通过 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 还原写模式 | 将两处 `newline="\n"` 删除，恢复为默认行为 |
| 注意 | 回滚后将重新出现 CRLF 问题，需配合 lint --fix 使用 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-21-142408 |
| **更新人** | Agent Session |
| **变更触发** | 用户指出真源检测反复制造 CRLF 后修复 |
| **下次修订条件** | 若新增 JSON 回写逻辑，需同步检查是否已加 `newline="\n"` |
| **跨环境迁移参考** | 直接复制修改后的 `.py` 文件即可 |


*文档生成时间：2026-07-21*  
*模板版本：v2*
