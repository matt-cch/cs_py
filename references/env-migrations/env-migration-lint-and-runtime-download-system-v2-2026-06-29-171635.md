---
title: env-migration — lint 工具链升级与运行时下载体系 v2.0 重构
description: 本次 session 完成了 md_lint / lint_encoding / lint_ps1 三个 lint 插件的升级修复，新建 list_upstream_versions plugin，重构 atomic-query-upstream 为 v2.0，修复 wf-download-runtime 数据源缺失，新增 version_constraint 实测版本约束机制。
date: 2026-06-29
meta:
  version: 1.0.0
---

# env-migration — lint 工具链升级与运行时下载体系 v2.0 重构

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | lint 工具链升级（md_lint v1.2.1 + lint_encoding v1.1.0 + lint_ps1 修复 + file-version 模式）与运行时下载体系 v2.0 重构（list_upstream_versions plugin + atomic-query-upstream v2.0 + wf-download-runtime 数据源修复 + version_constraint 约束机制） |
| **日期** | 2026-06-29 |
| **文件名时间戳** | `2026-06-29-171635` |
| **触发原因** | 用户指令要求修复 chromium 版本检测弹窗 bug、完善运行时下载体系、兼顾实测版本约束 |
| **影响范围** | lint 插件体系（4 个文件）、下载体系（4 个文件）、tools_config.json、py-sort-rules.json、verified-runtime-index.json |
| **风险等级** | 低（工具链增强，不涉及业务代码） |


## 一、文本文件变更清单

### 1. 修改 `schema/tool/get-runtime-version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `schema/tool/get-runtime-version.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增 `file-version` 模式：纯 `ctypes` 读取 Windows PE 文件 `ProductVersion`，零进程启动 |
| **作用** | 修复 chromium 版本检测时执行 `chrome.exe --version` 弹窗的 bug |
| **验证方式** | `get-runtime-version.py --mode file-version --target "D:\download\chrome-win64\chrome.exe"` → 返回 `151.0.7905.0`，无弹窗 |
| **迁移方式** | 直接覆盖 |

### 2. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/list_upstream_versions.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/list_upstream_versions.py` |
| **变更类型** | 新建 |
| **职责** | Plugin：接收 JSON 配置（url + parser_type + parser_config），查询上游可用版本列表，支持 `target_version` 存在性验证 |
| **解析模式** | `html_regex`（阿里云镜像目录列表）、`json_array`（Chrome for Testing JSON） |
| **迁移方式** | 直接复制 |

### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | 注册 `list_upstream_versions` 插件条目 |
| **迁移方式** | 追加条目 |

### 4. 重构 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-query-upstream.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-query-upstream.py` |
| **变更类型** | 重构（v1.0.0 → v2.0.0） |
| **新增/修改内容** | Python/Node/Chromium 的查询逻辑提取为 JSON 配置常量，调用 `list_upstream_versions` plugin；OpenCode/llama 保留 GitHub API 直接查询 |
| **作用** | 解耦上游查询逻辑，支持版本列表存在性验证 |
| **迁移方式** | 直接覆盖 |

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | ① 新增 `_load_download_template_from_index()` 函数，fallback 读取 `verified-runtime-index.json` 的 `download_url_template`；② Step 2 改为即使用户传 `--target-version` 也强制调用 atomic 验证；③ 新增 Step 3.5 `version_constraint` 强制检查（`pin` / `max`）；④ 新增语义版本比较函数 `_parse_version()` / `_version_gt()` / `_version_gte()` |
| **作用** | 修复 chromium 无下载链接问题；防止用户传入不存在版本空转；强制执行实测版本约束 |
| **迁移方式** | 直接覆盖 |

### 6. 修改 `references/runtime/runtime_config/tools_config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/tools_config.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | ① llama_cpp_python 增加 `version_constraint: {type: "pin", value: "0.3.22", reason: "CPU 模式在 0.3.23+ 实测崩溃"}`；② python 增加 `version_constraint: {type: "max", value: "3.13.99", reason: "Python 3.14+ 尚未完成兼容性测试"}` |
| **作用** | 将实测验证后的版本边界固化为配置，workflow 强制执行 |
| **迁移方式** | 按 diff 合并 |

### 7. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| **变更类型** | 修改（v1.2.0 → v1.2.1） |
| **新增/修改内容** | `--fix` 自动补全缺失的 `meta: {}` 字段；`_fix_frontmatter_fields()` 扩展 `missing_keys` 参数 |
| **作用** | 修复 `--fix` 模式下缺失 `meta` 字段未自动补全的问题 |
| **迁移方式** | 直接覆盖 |

### 8. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` |
| **变更类型** | 修改（v1.0.3 → v1.1.0） |
| **新增/修改内容** | 新增 UTF-8 完整性检测（`raw.decode("utf-8")`），覆盖截断/损坏场景 |
| **作用** | 填补 BOM/CRLF 检测盲区 |
| **迁移方式** | 直接覆盖 |

### 9. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_ps1.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_ps1.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | `subprocess.run(text=True, encoding="utf-8")` → `text=False` + `decode("utf-8", errors="replace")` |
| **作用** | 消除 PowerShell GBK 中文输出在 reader thread 抛 `UnicodeDecodeError` 的崩溃 |
| **迁移方式** | 直接覆盖 |

### 10. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | 更新 `roots.devroot.path`、`github_connectivity` latency、各工具版本号、chromium candidate_paths 状态 |
| **作用** | 真源索引反映当前环境状态 |
| **迁移方式** | 执行 `verify-runtime.py` 重新生成 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session **不涉及**文件复制、缓存迁移、目录创建等非 git 追踪操作。


## 三、环境变量速查

本次 session **未修改** `.vscode/settings.json` 中的环境变量注入项。现有注入项保持如下：

```json
"terminal.integrated.env.windows": {
    "PATH": "${workspaceFolder}\\venv\\opencode;${workspaceFolder}\\venv\\node;${workspaceFolder}\\venv\\zig;${env:Path}",
    "OPENCODE_CONFIG": "${workspaceFolder}\\venv\\.opencode\\config.json",
    "OPENCODE_CONFIG_DIR": "${workspaceFolder}\\venv\\.opencode",
    "OPENCODE_TUI_CONFIG": "${workspaceFolder}\\venv\\.opencode\\tui.json",
    "XDG_DATA_HOME": "${workspaceFolder}\\venv\\data-opencode",
    "XDG_CACHE_HOME": "${workspaceFolder}\\venv\\data-opencode\\cache",
    "npm_config_cache": "${workspaceFolder}\\venv\\node\\.npm-cache",
    "TMP": "${workspaceFolder}\\venv\\tmp",
    "TEMP": "${workspaceFolder}\\venv\\tmp",
    "CL": "/utf-8"
}
```


## 四、落盘验证（写入后已执行）

| 文件类型 | 验证工具 | 验证内容 | 结果 |
|---------|---------|---------|------|
| `.md`（env-migration） | `run-lint.py`（md_lint + lint_encoding） | frontmatter、BOM、CRLF | ✅ 通过 |
| `.py`（lint 插件 / atomic / workflow） | `python -m py_compile` | Python 语法 | ✅ 全部通过 |
| `.json`（tools_config / py-sort-rules / index） | `run-lint.py`（lint_json） | JSON 语法 | ✅ 通过 |
| `deploy-git-isolated` 全量 | `run-lint.py --profile lint` | 混合类型统一验证 | ✅ 0 违规 |
| **workflow 端到端** | `wf-download-runtime.py` | opencode / node / chromium / llama / python | ✅ 全部通过 |


## 五、验证清单（新环境建议执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 lint 插件语法正确 | `python -m py_compile md_lint.py lint_encoding.py lint_ps1.py get-runtime-version.py` | 无报错 |
| 2 | 确认 md_lint --fix 自动补全 meta | 对缺少 meta 的测试文件执行 `validate_file(path, fix=True)` | 自动插入 `meta: {}` |
| 3 | 确认 lint_encoding UTF-8 检测有效 | 对截断文件执行 scan | 报 `UTF8_INCOMPLETE` |
| 4 | 确认 lint_ps1 不崩溃 | 对含中文的 `.ps1` 执行 lint | 正常完成 |
| 5 | 确认 chromium 版本检测无弹窗 | `get-runtime-version.py --mode file-version --target "...chrome.exe"` | 返回版本号，无弹窗 |
| 6 | 确认 plugin 版本列表查询有效 | `list_upstream_versions.py --config-json '{...}' --target-version 99.99.99` | 返回 `target_exists: false` |
| 7 | 确认 llama pin 约束生效 | `wf-download-runtime.py --tool-name llama_cpp_python --target-version 0.3.23` | `[FAIL] 版本约束违反` |
| 8 | 确认 python max 约束生效 | `wf-download-runtime.py --tool-name python --target-version 3.14.0` | `[FAIL] 版本约束违反` |
| 9 | 确认无约束工具正常通过 | `wf-download-runtime.py --tool-name node --target-version 26.3.1` | 正常通过或 `无需更新` |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 还原 lint 插件 | `git checkout schema/tool/get-runtime-version.py references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py lint_encoding.py lint_ps1.py` |
| 还原下载体系 | `git checkout references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-query-upstream.py references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` |
| 删除新建 plugin | `git rm references/tasks/deploy-git-isolated/scripts/py-plugins/list_upstream_versions.py` |
| 还原配置 | `git checkout references/runtime/runtime_config/tools_config.json references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| 还原真源索引 | `git checkout references/runtime/verified-runtime-index.json`（或重新执行 verify-runtime.py） |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-29-171635 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指令「记录 env-migration」，选择记录本次 session 整体工作 |
| **下次修订条件** | lint 插件再次升级、运行时下载体系新增工具或约束类型扩展（如 `channel: stable/beta/dev`） |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 + 重新执行 `verify-runtime.py` 更新真源索引 |
