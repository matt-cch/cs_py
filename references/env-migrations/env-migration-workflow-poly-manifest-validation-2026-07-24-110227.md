---
title: env-migration — workflow-poly Step 0c manifest 内容完整性校验增强
description: 将 Step 0c PolyrepoContext manifest 验证从「文件存在」提升到「内容完整性验证」，解决 yesterday env-migration 记录的遗留缺口。
date: 2026-07-24
meta:
  version: "1.0.0"
---

# env-migration-workflow-poly-manifest-validation-2026-07-24-110227

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | workflow-poly Step 0c manifest 内容完整性校验增强 |
| **日期** | 2026-07-24 |
| **文件名时间戳** | `2026-07-24-110227` |
| **触发原因** | 昨天 env-migration `polyrepo-git-security-manifest-bug-2026-07-23-174127` 记录的遗留缺口：Step 0c 产物仅验证文件存在性，缺少 JSON 语法及关键字段校验 |
| **影响范围** | 1 个脚本：`references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` |
| **风险等级** | **低** — 纯验证增强，无功能变更；旧场景字段完整时行为不变 |


## 一、文本文件变更清单

### 1. 修改 `workflow-git-deploy-full-poly.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | Step 0c manifest 验证逻辑增强（第 456-474 行） |
| **插入位置** | 替换原有 try/except 块 |
| **作用** | 从「文件存在即通过」升级为「关键字段完整性 + JSON 语法校验」 |
| **验证方式** | ① `py_compile` 语法通过；② 实际 workflow 部署验证通过 |
| **迁移方式** | 仅需替换对应代码段 |

**变更前后对比**：

| 维度 | 变更前 | 变更后 |
|------|--------|--------|
| 字段校验 | 无 | `repo_url` / `default_branch` / `target` / `toolchain_root` 必填 |
| 异常级别 | `[WARN]`（继续执行） | `[FAIL]` + `sys.exit(1)`（终止部署） |
| 异常分类 | 笼统 `Exception` | 区分 `JSONDecodeError` 与一般异常 |
| 日志输出 | 无 `default_branch` | 新增 `default_branch` 打印 |


## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。


## 三、环境变量速查

无新增环境变量。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py` lint-encoding | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.py`（修改的脚本） | `run-lint.py` lint_python | Python 语法（py_compile） | 通过 |

**执行命令**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py"
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认脚本语法正确 | `python -m py_compile workflow-git-deploy-full-poly.py` | 无输出（exit 0） |
| 2 | 确认 lint 通过 | `run-lint.py` 验证 | ✅ 全部通过 |
| 3 | 确认 workflow 正常执行 | 执行 `workflow-git-deploy-full-poly.py --devroot . --target . --step 0` | Step 0c 输出包含 `default_branch` 且无 `[FAIL]` |
| 4 | 确认关键字段缺失时阻断 | 手动构造缺少字段的 manifest，观察是否 exit 1 | `[FAIL] Step 0c: manifest 缺少关键字段: ...` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复代码 | `git checkout <变更前 commit>` 或手动恢复第 456-474 行为原始 try/except |
| 验证回滚 | `run-lint.py` 验证语法 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-24-110227 |
| **更新人** | Human + Agent Session |
| **变更触发** | 昨天 env-migration 记录的遗留缺口：Step 0c manifest 内容完整性校验 |
| **下次修订条件** | 新增/删减 manifest 必填字段时；变更异常处理策略时 |
| **跨环境迁移参考** | 直接替换对应代码段 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-24*  
*模板版本：v2*
