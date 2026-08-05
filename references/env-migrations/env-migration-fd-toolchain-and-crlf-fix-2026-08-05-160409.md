---
title: fd 工具链集成与 CRLF 修复
description: 本次 session 完成 fd（find 替代）全链路工具链集成，并修复 update-version.py 在 Windows 下默认产出 CRLF 的编码污染问题。
date: 2026-08-05
meta:
  version: 1.0.0
---

# fd 工具链集成与 CRLF 修复

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | fd 全链路工具链集成 + update-version.py CRLF 根因修复 |
| **日期** | 2026-08-05 |
| **文件名时间戳** | `2026-08-05-160409` |
| **触发原因** | 用户要求调研 fd 与 ripgrep 的适用场景，并参照 rg 纳入版本管理和更新体系；同时排查 update-version.py 产出 CRLF 的根因 |
| **影响范围** | 工具链配置（tools_config.json、verified-runtime-index.json、verified-download-toolset.json）、Python 脚本（update-version.py、atomic-query-upstream.py）、版本记录文件、wiki 踩坑记录 |
| **风险等级** | 低（新增工具链 + 修复编码问题，不涉及业务代码） |

## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py` |
| **变更类型** | `修改` |
| **修改内容** | `write_text(..., encoding="utf-8")` → `write_text(..., encoding="utf-8", newline="\n")`（两处） |
| **插入位置** | `update_md_version()` 函数第121行、`append_history()` 函数第149行 |
| **作用** | 阻止 Python 在 Windows 上将 `\n` 自动转换为 `\r\n`，从源头消除 CRLF 污染 |
| **验证方式** | 执行 `update-version.py` 后，用 `run-lint.py` 检测输出文件，`CRLF=0, LF>0` |
| **迁移方式** | 仅需追加 `newline="\n"` 参数 |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-query-upstream.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-query-upstream.py` |
| **变更类型** | `修改` |
| **新增内容** | 在 `query()` 函数的 GitHub Release 分支中追加 `elif query_param == "fd":` 条目 |
| **作用** | 使下载脚本和真源检测能够自动查询 fd 的上游最新版本（GitHub Release sharkdp/fd） |
| **验证方式** | `wf-download-runtime.py --tool-name fd` 能正确输出上游版本号 |
| **迁移方式** | 直接追加代码块，无需调整已有逻辑 |

### 3. 修改 `references/runtime/runtime_config/tools_config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/tools_config.json` |
| **变更类型** | `修改`（追加条目） |
| **新增内容** | fd 工具配置（`name: fd`、`mode: subprocess-version`、`exe_path: venv/fd/fd.exe`） |
| **作用** | 让真源检测和版本更新脚本识别 fd 为可检测工具 |
| **验证方式** | `wf-verify-runtime.py --tool fd` 能检测到 fd 10.4.2 |
| **迁移方式** | 通过 `atomic-config-edit-json.py` 批量插入 |

### 4. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改`（追加条目） |
| **新增内容** | `toolchain.fd` 完整条目（executable、version、download_url_template、candidate_paths、upstream_sources） |
| **作用** | 运行时真源索引中登记 fd 的路径和版本信息 |
| **验证方式** | 真源检测后自动回写，索引中 fd 条目 `verified_at` 更新 |
| **迁移方式** | 通过 `atomic-config-edit-json.py` 批量插入 |

### 5. 修改 `references/runtime/verified-download-toolset.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-download-toolset.json` |
| **变更类型** | `修改`（追加条目） |
| **新增内容** | fd 条目（id、display_name、package_type: github_release_zip、trigger_keywords） |
| **作用** | 下载脚本识别 fd 为可下载工具 |
| **验证方式** | `wf-download-runtime.py --tool-name fd` 能正常执行上游查询 |
| **迁移方式** | 通过 `atomic-config-edit-json.py` 批量插入 |

### 6. 新建 `venv/version/fd.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/fd.md` |
| **变更类型** | `新建` |
| **作用** | fd 当前版本记录（frontmatter + version 表格） |
| **验证方式** | `update-version.py --tool fd` 能读取并对比版本 |

### 7. 新建 `venv/version/fd-history.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/fd-history.md` |
| **变更类型** | `新建` |
| **作用** | fd 版本变更历史（初始部署 10.4.2） |

### 8. 新建 `vaults/vault-demo/wiki/gotchas/crlf-newline-trap-2026-08-05-151450.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/gotchas/crlf-newline-trap-2026-08-05-151450.md` |
| **变更类型** | `新建` |
| **作用** | 记录 Python `write_text()` 在 Windows 下默认产出 CRLF 的根因、修复方案和反模式 |

### 9. 新建 `vaults/vault-demo/wiki/gotchas/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/gotchas/README.md` |
| **变更类型** | `新建` |
| **作用** | gotchas 目录自说明与导航索引 |

### 10. 修改 `vaults/vault-demo/wiki/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/README.md` |
| **变更类型** | `修改` |
| **修改内容** | 子目录导航表中追加 `gotchas/` 条目 |

## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 下载 | GitHub Release (sharkdp/fd) | `D:\download\fd-v10.4.2-x86_64-pc-windows-msvc.zip` | 手动下载 ZIP 包（下载脚本 upstream 暂不支持 fd） |
| 解压 | `D:\download\fd-v10.4.2-x86_64-pc-windows-msvc.zip` | `venv/fd/` | 解压后平移子目录内容到根，最终路径 `venv/fd/fd.exe` |
| 目录创建 | — | `venv/fd/` | fd 工具链根目录 |
| 目录创建 | — | `vaults/vault-demo/wiki/gotchas/` | 踩坑记录目录 |

### 复现命令

```powershell
# fd 下载与解压（参照 ripgrep 模式）
$zip = "D:\download\fd-v10.4.2-x86_64-pc-windows-msvc.zip"
$dest = "D:\pjt\cursor\cs_py\venv\fd"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force

# 平移子目录（ZIP 解压后多一层目录）
$subdir = Get-ChildItem -LiteralPath $dest -Directory | Select-Object -First 1
if ($subdir) {
    Get-ChildItem -LiteralPath $subdir.FullName | Move-Item -Destination $dest -Force
    Remove-Item -LiteralPath $subdir.FullName -Recurse -Force
}

# 验证
& "$dest\fd.exe" --version
# 期望输出：fd 10.4.2
```

## 三、环境变量速查

无新增环境变量。fd 和 ripgrep 均为独立 CLI 工具，通过绝对路径调用，不依赖 PATH。

## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py` | frontmatter、CRLF/LF、BOM | `CRLF=0, LF>0, BOM=no` |
| `.json`（索引文件） | `run-lint.py` | JSON 语法 | `[OK]` 无解析错误 |
| `.py`（脚本修改） | `run-lint.py` | Python 语法 | `py_compile` 通过 |

**执行示例**：
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\<文件名>.md"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 fd 可执行 | `& "${devroot}\venv\fd\fd.exe" --version` | `fd 10.4.2` |
| 2 | 确认 fd 真源检测通过 | `wf-verify-runtime.py --tool fd` | `已是最新版` |
| 3 | 确认 fd 下载脚本识别 | `wf-download-runtime.py --tool-name fd` | `已是最新版, need_update=False` |
| 4 | 确认 update-version.py 无 CRLF | `run-lint.py --files "venv/version/*.md"` | `CRLF=0` |
| 5 | 确认 ripgrep 仍正常 | `wf-verify-runtime.py --tool ripgrep` | `已是最新版` |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 fd 索引 | 从 `tools_config.json`、`verified-runtime-index.json`、`verified-download-toolset.json` 中删除 fd 条目 |
| 删除 fd 可执行文件 | `Remove-Item -Recurse "${devroot}\venv\fd"` |
| 删除 fd 版本记录 | `Remove-Item "${devroot}\venv\version\fd.md"`、`Remove-Item "${devroot}\venv\version\fd-history.md"` |
| 恢复 update-version.py | 回退 `newline="\n"` 修改（不推荐，CRLF 是 bug） |

## 七、踩坑与纠偏记录

### 7.1 CRLF 根因（已修复）

**现象**：`update-version.py` 写入 `.md` 文件后触发 lint CRLF 违规。
**根因**：`pathlib.Path.write_text(newline=None)` 在 Windows 上自动将 `\n` 转为 `\r\n`。
**修复**：两处 `write_text()` 追加 `newline="\n"`。
**反模式**：依赖 `run-lint.py --fix` 事后修复，而非从源头消除。

### 7.2 upstream 查询脚本混淆（已澄清）

**现象**：Agent 误将 `upstream-queries.ps1`（legacy）当作当前活跃上游查询入口。
**真相**：当前活跃入口是 `atomic-query-upstream.py`（Python），已内置 ripgrep/fd 等 GitHub Release 查询。`tools_config.json` 中的 `query_tool`/`query_function` 字段对当前活跃流程无效（死字段）。
**修复**：在 `atomic-query-upstream.py` 中追加 fd 分支，无需修改 ps1。

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-05-160409 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求调研 fd 与 ripgrep 并执行 fd 全链路集成；排查 update-version.py CRLF 根因 |
| **下次修订条件** | fd 版本更新、新增类似 Rust CLI 工具链、CRLF 规则扩展 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
