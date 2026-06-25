---
title: env-migration — file-write-helper INI 配置支持与 schema/tool 清理
description: 记录本次 session 对 schema/tool/file-write-helper.py 的 INI 配置支持增强、.ps1 linter bug 修复，以及测试文件从 schema/tool/ 向 venv/tmp/ 的迁移清理。
date: 2026-06-01
---

# env-migration-schema-tool-write-helper-ini-support-2026-06-01

> **Session 主题**：为 `file-write-helper.py` 增加 `--config` INI 配置支持，修复 PowerShell linter 的 `KeyError` bug，并重写 `file-write-helper.ini` 模板；清理误放在 `schema/tool/` 下的测试中间产物。  
> **适用场景**：将本次 `schema/tool/` 的变更迁移到新开发环境时，按此清单逐条核对即可复现。


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | file-write-helper INI 配置支持与 schema/tool 清理 |
| **日期** | 2026-06-01 |
| **触发原因** | 用户要求用 `file-write-helper.py` 生成 .ps1/.py 测试脚本，验证生成文件的执行结果（编码、乱码、预期输出）；过程中发现 `schema/tool/` 被中间产物污染 |
| **影响范围** | `schema/tool/` 下 3 份文件修改 + 4 份测试文件迁移到 `venv/tmp/` + `schema/tool/README.md` 导航联动 |
| **风险等级** | 极低（纯工具增强与目录清理，不影响业务运行时） |


## 一、文本文件变更清单

### 1. 修改 `schema/tool/file-write-helper.py`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/file-write-helper.py` |
| **变更类型** | 功能增强 + Bug 修复 |
| **修改点** | ① 新增 `import configparser`  <br>② 新增 `--config / -c` CLI 参数，支持从 INI 文件读取 `target_path`、`content_file`、`encoding`、`verify_syntax`、`backup_existing`  <br>③ 若指定 `content_file` 且文件存在，自动读取 txt 内容覆盖脚本内 `CONTENT` 变量  <br>④ **Bug 修复**：`.ps1` linter 命令中使用 `str.replace("{path}", file_path)` 替代 `str.format(path=...)`，避免 PowerShell 命令中的 `{` `}` 被误解析为 format 占位符导致 `KeyError` |
| **作用** | 实现「内容(txt) + 配置(ini)」分离写入，避免在 `schema/tool/` 下直接修改模板来生成文件；同时修复 `.ps1` 语法检查不可用的问题 |
| **迁移方式** | 直接覆盖或在新环境重新执行本次 edit（共 3 处） |

> **备份说明**：本次修改由 `edit-helper.py` 自动备份，产生 `file-write-helper.py.20260601T143557.bak`。迁移完成后该备份可安全删除。


### 2. 修改 `schema/tool/file-write-helper.ini`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/file-write-helper.ini` |
| **变更类型** | 内容重写 |
| **修改点** | ① 移除原误导性示例路径（指向不存在的 `example-content.txt`）  <br>② 改为占位符 `<必填：...>` 形式  <br>③ 新增「重要：本文件是模板，请勿直接在 schema/tool/ 目录下修改使用」警示  <br>④ 新增路径规划建议：所有任务相关的 ini、txt、生成产物应落在工作目录（如 `venv/tmp/`），`schema/tool/` 仅存放稳定模板 |
| **作用** | 明确模板只读属性，防止用户/Agent 直接在 `schema/tool/` 下修改配置，避免架构区被中间产物污染 |
| **迁移方式** | 直接覆盖 |


### 3. 修改 `schema/tool/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/README.md` |
| **变更类型** | 导航表追加一行 |
| **新增内容** | `[file-write-helper.ini](file-write-helper.ini)` 索引条目，说明为「配套 INI 模板，定义内容文件、目标路径、编码等参数」 |
| **迁移方式** | 直接追加即可 |


### 4. 迁移测试文件（从 `schema/tool/` → `venv/tmp/`）

以下 4 份文件在本次 session 初期被错误放置在 `schema/tool/` 下，经用户指出后已迁移至 `venv/tmp/`：

| 原路径（已清理） | 新路径 | 文件作用 |
|-----------------|--------|---------|
| `schema/tool/test_ps.ini` | `venv/tmp/test_ps.ini` | PowerShell 生成任务配置 |
| `schema/tool/test_py.ini` | `venv/tmp/test_py.ini` | Python 生成任务配置 |
| `schema/tool/test_ps_content.txt` | `venv/tmp/test_ps_content.txt` | PowerShell 脚本源内容 |
| `schema/tool/test_py_content.txt` | `venv/tmp/test_py_content.txt` | Python 脚本源内容 |

| 属性 | 值 |
|------|-----|
| **变更类型** | 迁移（移动） |
| **原因** | `schema/tool/` 是稳定模板区，不应被具体任务的中间产物（ini、txt、生成产物）污染 |
| **迁移方式** | 在新环境中，这些测试文件**不应出现在 `schema/tool/` 下**；如需要复现测试，应在 `venv/tmp/` 下新建 |


### 5. 清理自动备份文件（可选）

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/file-write-helper.py.20260601T143557.bak` |
| **变更类型** | 产生 → 建议清理 |
| **原因** | 由 `edit-helper.py` / `file-write-helper.py` 的 `BACKUP_EXISTING=True` 自动生成 |
| **迁移方式** | 迁移完成后确认主文件无误，可删除该备份：`Remove-Item "schema/tool/file-write-helper.py.20260601T143557.bak"` |


## 二、非文本操作

本次 session 不涉及缓存迁移、注册表修改、环境变量变更等系统级操作。唯一的文件系统操作是上述 4 份测试文件从 `schema/tool/` 移动到 `venv/tmp/`。


## 三、环境变量速查

本次 session **未新增或修改**任何环境变量，无需核对。


## 四、验证清单（新环境必须执行）

迁移完成后，按此表逐项验证：

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 write-helper 存在且含 config 参数 | `Select-String "--config" "schema/tool/file-write-helper.py"` | 有匹配行 |
| 2 | 确认 configparser 已导入 | `Select-String "import configparser" "schema/tool/file-write-helper.py"` | 有匹配行 |
| 3 | 确认 .ps1 linter 使用 replace 而非 format | `Select-String 'replace\("\{path\}"' "schema/tool/file-write-helper.py"` | 有匹配行 |
| 4 | 确认 ini 模板已更新 | `Select-String "请勿直接在 schema/tool" "schema/tool/file-write-helper.ini"` | 有匹配行 |
| 5 | 确认 schema/tool/README.md 已登记 ini | `Select-String "file-write-helper.ini" "schema/tool/README.md"` | 有匹配行 |
| 6 | 确认 schema/tool/ 下无测试产物 | `Get-ChildItem "schema/tool/test_*" -ErrorAction SilentlyContinue` | **无输出** |
| 7 | 端到端测试：生成 PowerShell 脚本 | 在 `venv/tmp/` 下准备 `test_ps.ini` + `test_ps_content.txt`，执行 `python schema/tool/file-write-helper.py --config venv/tmp/test_ps.ini` | `success: true`，生成 `test_output.ps1` |
| 8 | 端到端测试：生成 Python 脚本 | 同上，使用 `test_py.ini` | `success: true`，生成 `test_output.py` |
| 9 | 执行生成的 PS1，验证中文无乱码 | `powershell -ExecutionPolicy Bypass -Command "& 'venv/tmp/test_output.ps1'"` | 输出「PowerShell 测试：中文输出正常」「结果验证：符合预期」 |
| 10 | 执行生成的 PY，验证中文无乱码 | `python venv/tmp/test_output.py` | 输出「Python 测试：中文输出正常」「结果验证：符合预期」 |
| 11 | 验证 PS1 编码为 UTF-8 BOM | 检查 `venv/tmp/test_output.ps1` 前 3 字节 | `0xEF 0xBB 0xBF` |
| 12 | 验证 PY 编码为 UTF-8 无 BOM | 检查 `venv/tmp/test_output.py` 前 3 字节 | `0x23 0x21 0x2F`（即 `#!/`） |


## 五、与其他 Session 的边界说明

本次 session **不包含**以下变更（这些已在其他文档中记录或属于历史 session）：

| 文件/目录 | 所属文档/Session | 说明 |
|-----------|----------------|------|
| `venv/tmp/` 下其他临时文件 | 历史各 session | `venv/tmp/` 为公共临时区，本次仅迁移 4 份测试文件至此 |
| `.vscode/settings.json` | `env-migration-opencode-cache-2026-05-31.md` | 环境变量注入 |
| `apps/`、`backend/` 全部业务代码 | Handoff V1~V12 | 项目功能交付 |
| `docs/tooling/opencode/` 下文档 | `env-migration-opencode-cache-2026-05-31.md` | OpenCode 缓存隔离修正 |
| `schema/structure/doc-naming-conventions.md` | `env-migration-doc-naming-standards-2026-05-31.md` | 文档命名规范建设 |


## 六、回滚方案

若迁移后发现问题，按以下步骤回退：

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 write-helper 到修改前 | 如有备份 `.bak`，执行 `Move-Item "schema/tool/file-write-helper.py.20260601T143557.bak" "schema/tool/file-write-helper.py" -Force`；如无备份，从版本控制回退 |
| 恢复 ini 到旧版 | 从版本控制回退 `schema/tool/file-write-helper.ini` |
| 恢复 README.md | 从版本控制回退 `schema/tool/README.md` |
| 清理 venv/tmp/ 测试文件（如需） | `Remove-Item "venv/tmp/test_ps.ini"`, `Remove-Item "venv/tmp/test_py.ini"`, `Remove-Item "venv/tmp/test_ps_content.txt"`, `Remove-Item "venv/tmp/test_py_content.txt"` |
| 清理生成产物（如需） | `Remove-Item "venv/tmp/test_output.ps1"`, `Remove-Item "venv/tmp/test_output.py"` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-01 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求用 write-helper 生成测试脚本并验证执行结果；过程中发现 schema/tool/ 被中间产物污染，需纠正 |
| **下次修订条件** | file-write-helper.py 功能有进一步调整（如新增文件类型支持、新增 linter）时追加 |
| **跨环境迁移参考** | 新环境需同步 `schema/tool/file-write-helper.py` + `schema/tool/file-write-helper.ini` + `schema/tool/README.md` 导航更新 |


*文档生成时间：2026-06-01*  
*最后更新时间：2026-06-01*  
*对应 Session 主题：file-write-helper INI 配置支持与 schema/tool 清理*
