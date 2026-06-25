---
title: env-migration — verify-runtime.ps1 真源检测脚本修复与索引更新
description: 修复 verify-runtime.ps1 的 BOM 双写、cursor candidate_paths 遍历、chromium Windows 版本检测、无期望值分支遗漏等问题，同步更新 verified-runtime-index.json。
date: 2026-06-02
---

# env-migration-verify-runtime-script-fixes-2026-06-02-224000

> **Session 主题**：verify-runtime.ps1 真源检测脚本修复与 toolchain 检测逻辑完善
> **日期**：2026-06-02
> **文件名时间戳**：`2026-06-02-224000`
> **触发原因**：运行 verify-runtime.ps1 时发现 cursor.executable 路径失效、chromium.version 跳过、BOM 首行解析错误等多项缺陷
> **影响范围**：`references/runtime/verify-runtime.ps1`、`references/runtime/verified-runtime-index.json`、`schema/tool/file-write-helper.py`
> **风险等级**：中（影响真源检测准确性，不涉及业务代码）


## 一、文本文件变更清单

### 1. 修改 `references/runtime/verify-runtime.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime.ps1` |
| **变更类型** | `修改` |
| **作用** | 修复真源检测脚本的多个逻辑缺陷 |
| **验证方式** | 执行 `powershell -ExecutionPolicy Bypass -File verify-runtime.ps1`，应通过 22/23 项 |
| **迁移方式** | 可直接覆盖（已备份多份 `.bak`） |

#### 修复内容

1. **cursor.executable 遍历 candidate_paths**（第 181~199 行）
   - 原逻辑：仅检查 JSON 登记的单一 `executable` 路径
   - 修复：对 `cursor` 特殊处理，遍历 `candidate_paths` 数组，支持 `%ENV%` 环境变量展开，同时检查运行中进程路径
   - 结果：从 `D:\tools\cursor\Cursor.exe` 正确命中实际安装的 `D:\tools\cursor\Cursor.exe`

2. **cursor.version 检测方式**（第 250~295 行）
   - 原逻辑：读取 `resources\app\package.json` 的 `version` 字段
   - 修复：优先调用 `resources\app\bin\cursor.cmd --version`，fallback 到 `package.json`
   - 原因：Electron 应用 `Cursor.exe` 不处理 `--version`，但提供了 CLI wrapper `.cmd` 脚本

3. **chromium.version Windows 检测**（第 290~303 行）
   - 原逻辑：`$actualVersion = "SKIP"`（未实现）
   - 修复：使用 `Get-ItemProperty -LiteralPath <exe>.VersionInfo.ProductVersion` 读取 PE 文件属性
   - 原因：Windows 构建的 Chromium 不支持 `--version` CLI 参数

4. **无期望值版本记录分支**（第 313~329 行）
   - 原逻辑：当 `$expectedVersion` 为 null 时，四个条件全不满足，`Add-Result` 不被调用
   - 修复：增加 `else` 分支，以 PASS 状态记录实际检测版本，message 标注 "版本已检测（无期望值）"

5. **chromium.executable 检测**（同步修复）
   - 遍历 `candidate_paths`，支持 `%ENV%` 展开


### 2. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改` |
| **作用** | 同步实测数据，新增经验教训记录 |
| **验证方式** | `python -m json.tool verified-runtime-index.json` 应无错误 |
| **迁移方式** | 直接覆盖 |

#### 新增 `lessons_learned` 区块

记录了 5 条踩坑经验，供后续 Agent 参考：

| ID | 标题 | 核心教训 |
|----|------|---------|
| `bom-double-write` | UTF-8 BOM 双写 | 已有 BOM 的文件复制为 content.txt 后，需先去 BOM 再让 helper 写入 |
| `cursor-version-cli-wrapper` | `Cursor.exe --version` 无效 | 必须用 `resources\app\bin\cursor.cmd --version` |
| `chromium-version-windows` | Windows Chromium 无 `--version` | 用 `Get-ItemProperty.VersionInfo.ProductVersion` |
| `expected-version-missing-branch` | 无期望值时逻辑遗漏 | 必须加 `else` 分支记录检测到的版本 |
| `candidate-paths-traversal` | 必须遍历 `candidate_paths` | 不能只看登记的单一 `executable` 路径 |

#### 更新的实测数据

| 项 | 旧值 | 新值 |
|----|------|------|
| `cursor.executable` | `C:\Program Files\cursor\Cursor.exe` | `D:\tools\cursor\Cursor.exe` |
| `cursor.version_cli_wrapper` | — | 新增 `D:\tools\cursor\resources\app\bin\cursor.cmd` |
| `chromium.version` | — | 新增 `144.0.7507.0` |
| `node.version` | `v26.1.0` | `v26.2.0` |
| GitHub 连通性延迟 | 785ms/796ms | 895ms/1006ms（API） |


### 3. 修改 `schema/tool/file-write-helper.py`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/file-write-helper.py` |
| **变更类型** | `修改` |
| **作用** | 修复 `.json`/`.yaml`/`.yml` linter 命令的 Windows 路径转义 bug |
| **验证方式** | 用 helper 写 `.json` 文件，linter 应通过 |
| **迁移方式** | 直接覆盖 |

#### 修复内容

**问题**：`_LINTER_MAP` 中 `.json` 的 linter 命令为：
```python
"python", "-c", "import json; json.load(open('{path}', encoding='utf-8'))"
```

当 `{path}` 被替换为 Windows 路径 `D:ilterilterilter_py
eferences
untimeilter-runtime-package.json` 时，`` 和 `
` 被 Python 解析为转义字符（`` = form feed, `
` = carriage return），导致 `OSError: [Errno 22] Invalid argument`。

**修复**：在 `_run_linter` 中，对 `.json`/`.yaml`/`.yml` 类型的路径提前将 `\` 替换为 `\\`：

```python
if ext in (".json", ".yaml", ".yml"):
    escaped_path = file_path.replace("\\", "\\\\")
    cmd = [part.replace("{path}", escaped_path) for part in cmd_template]
else:
    cmd = [part.replace("{path}", file_path) for part in cmd_template]
```


## 二、非文本操作

本次 session 无文件复制/缓存迁移/目录创建等操作，全部变更均可被 git 追踪。


## 三、环境变量速查

无新增环境变量。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 运行真源检测脚本 | `powershell -ExecutionPolicy Bypass -File references/runtime/verify-runtime.ps1` | 总计 23 项，通过 >=22 项，跳过 0 项 |
| 2 | 验证 cursor.executable 命中 | 检查报告 `cursor.executable` | `new_value` 应为实际存在的路径（如 `D:\tools\cursor\Cursor.exe`） |
| 3 | 验证 cursor.version 检测 | 检查报告 `cursor.version` | 版本号应与期望值一致 |
| 4 | 验证 chromium.version 检测 | 检查报告 `chromium.version` | 应为 `144.0.7507.0` 或实际版本，非 SKIP |
| 5 | 验证 JSON 无 BOM | `python -c "import codecs; print(open('references/runtime/verified-runtime-index.json', 'rb').read(3).startswith(codecs.BOM_UTF8))"` | `False` |
| 6 | 验证 helper 写 JSON 正常 | 用 file-write-helper 写任意 `.json` | linter 通过，exit 0 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 verify-runtime.ps1 | 复制备份文件 `verify-runtime.ps1.*.bak` 覆盖 |
| 恢复 verified-runtime-index.json | 复制备份文件 `verified-runtime-index.json.*.bak` 覆盖 |
| 恢复 file-write-helper.py | 从 git checkout 或 schema/tool 备份恢复 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-02-224000 |
| **更新人** | Human + Agent Session |
| **变更触发** | verify-runtime.ps1 运行时检测到 cursor 路径失效、chromium 版本跳过、BOM 解析错误 |
| **下次修订条件** | 新增工具链（如 zig、go）、工具链版本升级、candidate_paths 变更 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-02*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
