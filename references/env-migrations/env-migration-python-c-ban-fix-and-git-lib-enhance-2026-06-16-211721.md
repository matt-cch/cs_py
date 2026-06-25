---
title: python-backend-loc.mdc python-c 禁令修正 + git-lib 检测增强
description: 修正框架层规则文档中的 python-c 违规示例，增强 deploy-git-isolated 插件库的检测函数返回值
date: 2026-06-16
---

# `env-migration-python-c-ban-fix-and-git-lib-enhance-2026-06-16-211721.md`

> **文档性质**：环境迁移记录。聚焦开发环境规则文档与共享库函数修正，非业务功能交付。

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | `python-backend-loc.mdc` python-c 禁令修正 + `git-lib` 检测增强 |
| **日期** | 2026-06-16 |
| **文件名时间戳** | `2026-06-16-211721` |
| **触发原因** | 巡检发现 `.cursor/rules/python-backend-loc.mdc` 中将 `python -c "..."` 作为正确命令示例写入规则；同时 `git-lib` 的 `Test-IsolatedGit` 仅报错退出、无返回值，无法被调用方复用状态 |
| **影响范围** | `.cursor/rules/python-backend-loc.mdc`、`references/tasks/deploy-git-isolated/scripts/lib-plugins/core.ps1`、调用点更新 |
| **风险等级** | 低（规则文档修正 + 插件函数增强） |


## 一、文本文件变更清单

### 1. 修改 `.cursor/rules/python-backend-loc.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/python-backend-loc.mdc` |
| **变更类型** | 修改 |
| **作用** | 将规则文档中的 `python -c` 示例替换为标准化脚本调用，消除与 `strictly-forbid-command-str-content.mdc` 的冲突 |

**具体修改（2 处）**：

**① line 21-26 — 解释器路径验证命令**

- **旧**：
  ```
  ${project_root}/venv/py/python.exe -c "import sys; print(sys.executable)"
  ```
- **新**：
  ```
  "${project_root}/venv/py/python.exe" "${project_root}/schema/tool/get-runtime-version.py" --mode python-self --interpreter "${project_root}/venv/py/python.exe"
  ```
- **验证方式**：检查输出 JSON 中的 `success` 为 `true` 且 `interpreter` 字段等于传入路径

**② line 32-36 — pyproject.toml 明文验证命令**

- **旧**：`poetry run python -c "from pathlib import Path; print(Path('pyproject.toml').resolve())"`
- **新**：删除内嵌命令，改为三种 `poetry check/show/version` 辅助验证，并标注 **禁止** `poetry run python -c`


### 2. 修改 `references/tasks/deploy-git-isolated/scripts/lib-plugins/core.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/lib-plugins/core.ps1` |
| **变更类型** | 修改（函数重构）+ 新增 |
| **作用** | `Test-IsolatedGit` 改为返回状态对象，新增 `Assert-IsolatedGit` 供强制断言场景使用 |

**具体修改**：

- **`Test-IsolatedGit`**：
  - 旧：检查 `$gitExe` 存在性，不存在则 `Write-Error` + `exit 1`
  - 新：返回 `@{ exists=$true/false; path=$gitExe; version=$ver }`，调用方可复用状态

- **新增 `Assert-IsolatedGit`**：
  - 调用 `Test-IsolatedGit`，若 `exists=$false` 则 `Write-Error` + `exit 1`
  - 供原有强制断言场景无缝替换


### 3. 修改调用点

| 路径 | 变更 |
|------|------|
| `scripts/lib-plugins/git-checks.ps1` | `Invoke-GitSafetyCheck` 中 `Test-IsolatedGit` → `Assert-IsolatedGit` |
| `scripts/github-lib.ps1` | 自检流程中 `Test-IsolatedGit` → `Assert-IsolatedGit` |


## 二、非文本操作

无。本次不涉及文件复制、缓存迁移或目录创建。


## 三、环境变量/配置速查

无需变更 `.vscode/settings.json` 或 `.env`。本次为规则文档与共享库函数修正。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `check-file-encoding.ps1` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.mdc`（规则文档） | `check-file-encoding.ps1` | 同上 | 同上 |
| `.ps1`（插件脚本） | `lint-ps1.ps1` | 语法无错误 | `[OK] 语法检查通过` |

**执行命令**（使用现成脚本，禁止现写）：

```powershell
# Markdown 编码检查
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" -Path "${devroot}\references\env-migrations\env-migration-python-c-ban-fix-and-git-lib-enhance-2026-06-16-211721.md"

# PS1 语法检查
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\lib-plugins\core.ps1"
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\lib-plugins\git-checks.ps1"
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\lint-ps1.ps1" -Path "${devroot}\references\tasks\deploy-git-isolated\scripts\github-lib.ps1"
```


## 五、验证清单（新环境/复现时）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 python-backend-loc.mdc 无 python-c | `grep 'python -c' .cursor/rules/python-backend-loc.mdc` | 无匹配（除禁令引用外） |
| 2 | 确认 Test-IsolatedGit 返回对象 | `. scripts/lib-plugins/core.ps1; $s = Test-IsolatedGit; $s.GetType().Name` | `Hashtable` 或 `PSCustomObject` |
| 3 | 确认 Assert-IsolatedGit 存在 | `Get-Command Assert-IsolatedGit` | `Function` |
| 4 | 确认 github-lib 自检通过 | `. scripts/github-lib.ps1` | `[OK] 隔离 Git: ...` |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复 python-backend-loc.mdc | 从 git 历史或备份恢复旧版 |
| 恢复 core.ps1 | 从 git 历史或备份恢复旧版 `Test-IsolatedGit` |
| 恢复调用点 | 将 `Assert-IsolatedGit` 改回 `Test-IsolatedGit`（注意：旧版 `Test-IsolatedGit` 会直接 exit，调用方无需额外处理） |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-16-211721 |
| **更新人** | Agent Session |
| **变更触发** | 用户要求修正 python-backend-loc.mdc 中的 python-c 示例，并增强 git-lib 检测函数 |
| **下次修订条件** | 若 `Test-IsolatedGit` 需扩展更多字段（如配置读取状态） |
| **跨环境迁移参考** | 直接复制受影响的 `.mdc` 和 `.ps1` 文件 |


*文档生成时间：2026-06-16-211721*  
*模板版本：v2*  
*时间戳来源：schema/tool/get-timestamp.ps1*
