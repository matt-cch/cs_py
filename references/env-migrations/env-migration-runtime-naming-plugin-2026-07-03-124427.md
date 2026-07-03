---
title: 运行时下载工具链命名真源改造
description: 新建 runtime_naming 插件，统一运行时工具下载产物命名规则，消除各脚本内嵌命名逻辑的差异
meta:
  version: "1.0.0"
date: 2026-07-03
---

# env-migration-runtime-naming-plugin-2026-07-03-124427.md

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 运行时下载工具链命名真源改造（新建 runtime_naming 插件） |
| **日期** | 2026-07-03 |
| **文件名时间戳** | `2026-07-03-124427` |
| **触发原因** | wf-download-runtime.py 内嵌 `_format_asset_name()` 函数，命名逻辑分散；atomic-03-extract-verify.py 自行拼接 extract_dir，命名不一致 |
| **影响范围** | `py-plugins/`、`py-sort-rules.json`、`wf-download-runtime.py`、`atomic-03-extract-verify.py` |
| **风险等级** | 低（纯重构，无业务逻辑变更） |

## 一、文本文件变更清单

### 1. 新建 `py-plugins/runtime_naming.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_naming.py` |
| **变更类型** | `新建` |
| **新增内容** | 命名唯一真源插件，提供 `get_asset_name()` / `get_extract_dir()` / `get_download_paths()` |
| **作用** | 集中管理 ZIP 文件名、解压目录名、完整路径生成；下游消费，不各自拼接 |
| **验证方式** | `python -m py_compile` 语法通过；py_lib.load_plugins(devroot=..., tags=["naming"]) 加载成功 |
| **迁移方式** | 直接追加文件 |

### 2. 修改 `py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | `追加` |
| **新增内容** | 插件条目 `runtime_naming`，tags `["runtime", "naming", "core"]`，depends `[]` |
| **作用** | 注册命名真源插件，供 py_lib.load_plugins() 按拓扑排序加载 |
| **验证方式** | run-lint.py 验证 JSON 语法通过 |
| **迁移方式** | 在 plugins 数组末尾追加 |

### 3. 修改 `py-tools/download-runtime/wf-download-runtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` |
| **变更类型** | `修改` |
| **修改内容** | ① 删除内嵌 `_format_asset_name()` 函数；② 通过 `py_lib.load_plugins(devroot=..., tags=["naming"])` 加载命名真源；③ Step 5 统一调用 `runtime_naming.get_download_paths()` 生成路径 |
| **作用** | 消除命名逻辑分散，统一由插件生成产物文件名与解压目录路径 |
| **验证方式** | run-lint.py 验证通过；端到端测试 git / gh_cli 下载成功 |
| **迁移方式** | 直接替换对应函数与调用块 |

### 4. 修改 `py-tools/download-runtime/atomic-03-extract-verify.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/atomic-03-extract-verify.py` |
| **变更类型** | `修改` |
| **修改内容** | ① 新增 `--extract-dir` CLI 参数；② `extract_and_verify()` 新增 `extract_dir` 参数；③ 内部生成逻辑改为 fallback：优先使用传入值，否则自行计算 |
| **作用** | 支持调用方统一传入 extract_dir，确保命名一致性 |
| **验证方式** | run-lint.py 验证通过；端到端测试 git / gh_cli 解压目录名正确 |
| **迁移方式** | 直接替换函数签名与参数解析块 |

## 二、非文本操作

本次 session 无文件系统/缓存迁移操作。

## 三、环境变量速查

无新增环境变量。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（本文档） | run-lint.py (lint-encoding + md_lint) | BOM、双 BOM、CRLF、frontmatter | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, frontmatter 合规 |
| `.py`（runtime_naming.py） | run-lint.py (lint-python + lint-encoding) | Python 语法、编码 | 语法通过、UTF-8 无 BOM |
| `.json`（py-sort-rules.json） | run-lint.py (lint-json) | JSON 语法 | `[OK]` 无解析错误 |
| `.py`（wf-download-runtime.py） | run-lint.py (lint-python) | Python 语法 | 语法通过 |
| `.py`（atomic-03-extract-verify.py） | run-lint.py (lint-python) | Python 语法 | 语法通过 |

**执行命令**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-runtime-naming-plugin-2026-07-03-124427.md" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\runtime_naming.py" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-sort-rules.json" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\atomic-03-extract-verify.py"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认插件加载成功 | `py_lib.load_plugins(devroot="...", tags=["naming"])` | registry.runtime_naming 存在 |
| 2 | 确认命名一致性 | git 下载测试 | ZIP 文件名为 `MinGit-2.x.x.x-64-bit.zip`，解压目录为 `git-2.x.x.windows.x-extracted` |
| 3 | 确认 gh_cli 命名 | gh_cli 下载测试 | ZIP 文件名为 `gh_x.x.x_windows_amd64.zip`，解压目录为 `gh_cli-x.x.x-extracted` |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除插件 | `Remove-Item "${devroot}\references\tasks\deploy-git-isolated\scripts\py-plugins\runtime_naming.py"` |
| 恢复 py-sort-rules.json | 从 Git 恢复 `py-sort-rules.json` 删除 runtime_naming 条目 |
| 恢复 wf-download-runtime.py | 从 Git 恢复 `wf-download-runtime.py` 的 `_format_asset_name()` 函数与旧调用 |
| 恢复 atomic-03-extract-verify.py | 从 Git 恢复旧版本（无 `--extract-dir` 参数） |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-03-124427 |
| **更新人** | Human + Agent Session |
| **变更触发** | 运行时下载工具链命名逻辑分散，需统一真源 |
| **下次修订条件** | 新增工具类型需要扩展 naming 规则时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
