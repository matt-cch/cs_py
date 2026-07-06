---
title: Polyrepo Workspace terminal.env 注入修复
description: Multi-root Workspace 模式下 terminal.integrated.env.windows 必须在 .code-workspace 级别定义，Folder 级别 .vscode/settings.json 对工作台级属性失效。
date: 2026-07-06
meta:
  version: 1.0.0
---

# env-migration-polyrepo-workspace-terminal-env-fix-2026-07-06-160818

> **文档性质**：环境迁移指南。聚焦单次 session 对开发环境配置的变更，供新环境复现。  
> **受众**：Human + Agent。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Polyrepo Workspace terminal.env 注入修复（.code-workspace 级别 settings 生效验证） |
| **日期** | 2026-07-06 |
| **文件名时间戳** | `2026-07-06-160818` |
| **触发原因** | Multi-root Workspace 模式下，`devroot/.vscode/settings.json` 中的 `terminal.integrated.env.windows` 被忽略，导致新窗口 Terminal PATH 不含隔离工具链，Agent Chat 找不到 `opencode`/`gh`/`node` 等命令 |
| **影响范围** | `cs-py.code-workspace` 文件、开发环境配置、polyrepo 工作流可用性 |
| **风险等级** | 低（仅影响开发环境配置，不涉及业务代码） |

## 一、文本文件变更清单

### 1. 修改 `cs-py.code-workspace`

| 属性 | 值 |
|------|-----|
| **路径** | `cs-py.code-workspace`（devroot 根目录） |
| **变更类型** | `追加` |
| **新增内容** | `settings.terminal.integrated.env.windows`、`settings.terminal.integrated.profiles.windows`、`settings.terminal.integrated.defaultProfile.windows`、`settings.workbench.colorTheme`、`settings.editor.wordWrap` |
| **插入位置** | `.code-workspace` 文件的 `settings` 对象内，原 `files.autoSave` 之后 |
| **作用** | 在 Workspace 级别注入隔离工具链 PATH 与环境变量，确保 Multi-root Workspace 模式下 Terminal 能正确加载隔离环境 |
| **验证方式** | 新开 Workspace 窗口，Terminal 中执行 `$env:PATH -split ';' \| Select-String 'cs_py\\venv'`，应输出 `venv/opencode`、`venv/node`、`venv/zig`、`venv/gh/bin` 等路径 |
| **迁移方式** | 可直接追加到目标环境的 `.code-workspace` `settings` 节；若路径不同需替换 `D:\\pjt\\cursor\\cs_py` 为实际 devroot |

#### 追加的 settings 内容（摘录）

```json
"terminal.integrated.env.windows": {
    "PATH": "D:\\pjt\\cursor\\cs_py\\venv\\opencode;D:\\pjt\\cursor\\cs_py\\venv\\node;D:\\pjt\\cursor\\cs_py\\venv\\zig;D:\\pjt\\cursor\\cs_py\\venv\\gh\\bin;${env:Path}",
    "GH_CONFIG_DIR": "D:\\pjt\\cursor\\cs_py\\venv\\data-gh",
    "OPENCODE_CONFIG": "D:\\pjt\\cursor\\cs_py\\venv\\.opencode\\config.json",
    "OPENCODE_CONFIG_DIR": "D:\\pjt\\cursor\\cs_py\\venv\\.opencode",
    "OPENCODE_TUI_CONFIG": "D:\\pjt\\cursor\\cs_py\\venv\\.opencode\\tui.json",
    "XDG_DATA_HOME": "D:\\pjt\\cursor\\cs_py\\venv\\data-opencode",
    "XDG_CACHE_HOME": "D:\\pjt\\cursor\\cs_py\\venv\\data-opencode\\cache",
    "npm_config_cache": "D:\\pjt\\cursor\\cs_py\\venv\\node\\.npm-cache",
    "TMP": "D:\\pjt\\cursor\\cs_py\\venv\\tmp",
    "TEMP": "D:\\pjt\\cursor\\cs_py\\venv\\tmp",
    "CL": "/utf-8"
},
"terminal.integrated.profiles.windows": {
    "PowerShell": {
        "source": "PowerShell",
        "args": [
            "-NoLogo",
            "-NoExit",
            "-Command",
            "$global:ProjectRoot = 'D:\\pjt\\cursor\\cs_py'; $function:prompt = { Set-Location $global:ProjectRoot; Write-Host ('PS ' + $global:ProjectRoot + '> ') -NoNewline; return ' ' }; Set-Location $global:ProjectRoot"
        ]
    }
},
"terminal.integrated.defaultProfile.windows": "PowerShell",
"workbench.colorTheme": "Default Dark Modern",
"editor.wordWrap": "on"
```

> **重要**：`D:\\pjt\\cursor\\cs_py` 必须替换为实际 devroot 绝对路径；`${env:Path}` 保持原样以继承系统 PATH。

### 2. 保留 `devroot/.vscode/settings.json`

| 属性 | 值 |
|------|-----|
| **路径** | `.vscode/settings.json` |
| **变更类型** | `无变更`（保留原状） |
| **作用** | 继续作为 **Open Folder 模式** 下的 IDE 配置 fallback。当用户选择「Open Folder」而非「Open Workspace」时，Folder 级别的 `terminal.integrated.env.windows` 仍然有效 |
| **说明** | 两个文件并存、互不冲突。Workspace 模式下 `.code-workspace` 的 settings 优先；Open Folder 模式下 `.vscode/settings.json` 生效 |

## 二、非文本操作（文件系统/缓存迁移）

### 1. 新建 Workspace 启动 Shortcut

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 新建 Shortcut | — | `C:\Users\Matt\Desktop\code\Cursor_cs_py_Workspace.lnk` | Workspace 模式启动入口 |

**Shortcut 参数**：
```
Target:     "C:\Program Files\cursor\Cursor.exe"
Arguments:  --user-data-dir "d:\pjt\cursor\cs_py\venv\data-cursor" --extensions-dir "d:\pjt\cursor\cs_py\venv\data-cursor" --new-window "d:\pjt\cursor\cs_py\cs-py.code-workspace"
WorkingDir: D:\pjt\cursor\cs_py
```

> 与旧 shortcut `Cursor_cs_py - Shortcut.lnk`（Open Folder 模式）并存。Workspace 模式用于 polyrepo 多根工作流；Open Folder 模式作为 fallback。

## 三、环境变量速查

迁移到新环境后，打开 `.code-workspace` 核对以下注入项是否齐全：

```json
"terminal.integrated.env.windows": {
    "PATH": "<devroot>\\venv\\opencode;<devroot>\\venv\\node;<devroot>\\venv\\zig;<devroot>\\venv\\gh\\bin;${env:Path}",
    "GH_CONFIG_DIR": "<devroot>\\venv\\data-gh",
    "OPENCODE_CONFIG": "<devroot>\\venv\\.opencode\\config.json",
    "OPENCODE_CONFIG_DIR": "<devroot>\\venv\\.opencode",
    "OPENCODE_TUI_CONFIG": "<devroot>\\venv\\.opencode\\tui.json",
    "XDG_DATA_HOME": "<devroot>\\venv\\data-opencode",
    "XDG_CACHE_HOME": "<devroot>\\venv\\data-opencode\\cache",
    "npm_config_cache": "<devroot>\\venv\\node\\.npm-cache",
    "TMP": "<devroot>\\venv\\tmp",
    "TEMP": "<devroot>\\venv\\tmp",
    "CL": "/utf-8"
}
```

> `<devroot>` 替换为实际绝对路径（如 `D:\\pjt\\cursor\\cs_py`）。

## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.code-workspace` | `python -c "import json; json.load(...)"` | JSON 语法正确性 | 无解析错误 |
| `.md`（本文件） | `run-lint.py` / `lint_encoding` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |

**执行示例**：
```powershell
# .code-workspace JSON 语法检查
"<devroot>\venv\py\python.exe" -c "import json; json.load(open('<devroot>\\cs-py.code-workspace', encoding='utf-8')); print('JSON OK')"

# Markdown 编码检查
"<devroot>\venv\py\python.exe" "<devroot>\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "<devroot>" --files "<devroot>\references\env-migrations\env-migration-polyrepo-workspace-terminal-env-fix-2026-07-06-160818.md"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 Workspace 加载正确 | 双击 `.code-workspace` 文件打开 | Explorer 显示 4 个 root：cs_py (devroot)、api-demo、web-demo、jywl-lab |
| 2 | 确认 PATH 注入成功 | `$env:PATH -split ';' \| Select-String 'cs_py\\venv'` | 输出包含 `venv\opencode`、`venv\node`、`venv\zig`、`venv\gh\bin` |
| 3 | 确认 opencode 可用 | `Get-Command opencode` | 解析到 `venv\opencode\opencode.exe` |
| 4 | 确认 Terminal 启动目录 | 新开 Terminal | Prompt 显示 `PS D:\pjt\cursor\cs_py>`（自动 cd 到 devroot） |
| 5 | 确认环境变量齐全 | `$env:GH_CONFIG_DIR`、`$env:OPENCODE_CONFIG` 等 | 均输出 devroot 内的绝对路径 |

## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 移除 Workspace 级 env 注入 | 从 `.code-workspace` 的 `settings` 中删除 `terminal.integrated.env.windows`、`terminal.integrated.profiles.windows`、`terminal.integrated.defaultProfile.windows` 字段 |
| 恢复纯 Open Folder 工作流 | 关闭 Workspace，使用 `File > Open Folder` 打开 devroot，依赖 `.vscode/settings.json` 的 Folder 级注入 |
| 保留 `.code-workspace` 备用 | 若需保留 Workspace 文件结构但禁用 env 注入，仅保留 `files.autoSave` 等无害设置 |

## 七、根因总结（供后续 Agent 参考）

**核心发现**：
- Multi-root Workspace 中，Folder 级别的 `.vscode/settings.json` **只加载"资源级"设置**（如 `python.defaultInterpreterPath`、`files.exclude`）。
- `terminal.integrated.env.windows` 属于**工作台级属性**，在 Folder 级别被**忽略/置灰**。
- `.code-workspace` 文件本身可以包含**全局 Workspace settings**，覆盖所有 Folder。工作台级属性必须在 `.code-workspace` 级别定义。

**参考**：VS Code 官方文档 — Multi-root Workspaces > Settings  
> "To avoid setting collisions, only resource (file, folder) settings are applied when using a multi-root workspace. Settings that affect the entire editor (for example, UI layout) are ignored."

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-06-160818 |
| **更新人** | Human + Agent Session |
| **变更触发** | Multi-root Workspace 模式下 terminal.env 注入失效排查 |
| **下次修订条件** | 新增 Folder 到 Workspace、变更 devroot 绝对路径、VS Code 行为变更 |
| **跨环境迁移参考** | 直接复制 `.code-workspace` 的 `settings` 节 + 替换 `<devroot>` 路径 + 按「验证清单」逐条执行 |

*文档生成时间：2026-07-06*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
