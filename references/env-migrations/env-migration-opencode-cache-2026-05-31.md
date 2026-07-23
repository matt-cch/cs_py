---
title: Session Diff Manifest — 2026-05-31（OpenCode 缓存隔离修正）
description: 记录本次 session 涉及的全部文件变更、缓存迁移操作及在新开发环境复现的完整步骤。
date: 2026-05-31
---

# Session Diff Manifest — 2026-05-31

> **Session 主题**：补全 OpenCode 缓存隔离缺口（增设 `XDG_CACHE_HOME`），并建立完整决策复盘文档。  
> **适用场景**：将本次修改迁移到另一台开发机器时，按此清单逐条核对即可复现。


## 一、文本文件变更清单

### 1. 修改 `.vscode/settings.json`

| 属性 | 值 |
|------|-----|
| **路径** | `.vscode/settings.json` |
| **变更类型** | 追加一行 |
| **新增内容** | `"XDG_CACHE_HOME": "${workspaceFolder}\\venv\\data-opencode\\cache"` |
| **插入位置** | `terminal.integrated.env.windows` 对象内，位于 `XDG_DATA_HOME` 之后、`npm_config_cache` 之前 |
| **作用** | 将 OpenCode 缓存目录（models.json、rg.exe、未来 npm plugin 包）收束到项目内，避免飘在用户目录 `~/.cache/opencode/` |
| **验证方式** | 新开终端后执行 `$env:XDG_CACHE_HOME`，应输出项目内绝对路径 |

> **注意**：若目标环境 `workspaceFolder` 不同（如不同盘符），需手动调整该值。


### 2. 修改 `docs/tooling/opencode/cursor-opencode-setup-and-logs.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/cursor-opencode-setup-and-logs.md` |
| **变更类型** | 多处修正 |
| **修改点** | ① 环境变量表增加 `XDG_CACHE_HOME` 行  <br>② 核心结论段修正措辞，承认此前"缓存全隔离"为错误表述  <br>③ 关键路径总览的 tree 增加 `cache/` 子目录  <br>④ 添加历史勘误注释，链接到复盘文档 |
| **迁移方式** | 可直接覆盖（或在新环境重新执行本次 edit 的三处替换） |


### 3. 修改 `docs/tooling/opencode/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/README.md` |
| **变更类型** | 导航表追加一行 |
| **新增内容** | `[data-opencode-directory-intent-and-evolution.md]` 文档索引 |
| **迁移方式** | 直接追加即可 |


### 4. 新建 `docs/tooling/opencode/data-opencode-directory-intent-and-evolution.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/tooling/opencode/data-opencode-directory-intent-and-evolution.md` |
| **变更类型** | 新建 |
| **内容概要** | 完整记录：原始触发点（plugin npm 包隔离）→ XDG 规范职责边界 → 实测检测过程 → 缓存合并方案论证 → 实施命令 → 落地后路径布局 → 可复用检测模板 |
| **文件大小** | 约 230 行 |
| **迁移方式** | 直接复制到新环境同名路径 |

### 5. 后续关联变更（同一 Session 后半段）

以下变更是本次缓存隔离 session 的后续延伸，由文档命名规范讨论触发，但服务于同一目标：

| # | 文件/目录 | 变更类型 | 说明 |
|---|----------|---------|------|
| 5.1 | `references/env-migrations/` | 新建目录 | 一次性 env-migration 文档归档地（本文件最终落点） |
| 5.2 | `references/changelog/` | 新建目录 | Monorepo 环境变更时间线，记录本次缓存隔离 |
| 5.3 | `references/changelog/monorepo-env-changelog.md` | 新建 | 本次缓存隔离的 monorepo 级 changelog 记录 |
| 5.4 | `references/changelog/README.md` | 新建 | changelog 目录索引 |
| 5.5 | `references/README.md` | 导航联动 | 登记 `env-migrations/` 和 `changelog/` |
| 5.6 | `schema/structure/changelog-template.md` | 新建 | Monorepo 环境变更记录模板 |
| 5.7 | `schema/structure/README.md` | 导航联动 | 登记 changelog-template |

> **注意**：后半段文档命名规范建设的完整变更清单，见 `env-migration-doc-naming-standards-2026-05-31.md`。


## 二、非文本操作（缓存文件迁移）

本次 session 执行了一次文件系统迁移操作，**不涉及 git 追踪的文件**，但需要在目标环境手动复现或自行决定是否执行。

### 源 → 目标映射

| 源路径（旧环境） | 目标路径（项目内） | 内容 |
|-----------------|-------------------|------|
| `C:\Users\matt_hall\.cache\opencode\` | `venv\data-opencode\cache\opencode\` | models.json (2.1 MB)、version (2 B)、bin/rg.exe (4.2 MB) |

### 迁移命令（PowerShell）

```powershell
$src = "C:\Users\<User>\.cache\opencode"
$dst = "<devroot>\venv\data-opencode\cache\opencode"

if (-not (Test-Path $dst)) {
    New-Item -ItemType Directory -Path $dst -Force | Out-Null
}

Get-ChildItem -Path $src | ForEach-Object {
    $target = Join-Path $dst $_.Name
    if ($_.PSIsContainer) {
        if (-not (Test-Path $target)) {
            Copy-Item -Path $_.FullName -Destination $target -Recurse -Force
        }
    } else {
        Copy-Item -Path $_.FullName -Destination $target -Force
    }
}
```

> **重要**：目标机器的用户名和 `devroot` 路径不同，务必替换 `<User>` 和 `<devroot>`。
> 如果目标环境从未运行过 OpenCode，旧缓存可能不存在，此步骤可跳过（新 session 会自动在新路径生成缓存）。


## 三、环境变量速查（复现核对待办）

迁移到新环境后，打开 `.vscode/settings.json` 核对以下注入项是否齐全：

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

**本次新增/修正的项**（与其他环境变量相比，这是唯一变化）：
- ✅ `XDG_CACHE_HOME`：本次新增
- ✅ `XDG_DATA_HOME`：此前已有，但文档描述被修正


## 四、验证清单（新环境必须执行）

迁移完成后，按以下步骤验证隔离是否生效：

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | 确认 `XDG_CACHE_HOME` 注入成功 | `$env:XDG_CACHE_HOME` | 输出项目内绝对路径 |
| 2 | 确认 `XDG_DATA_HOME` 注入成功 | `$env:XDG_DATA_HOME` | 输出项目内绝对路径 |
| 3 | 确认用户目录无泄漏 | `Get-ChildItem "$env:USERPROFILE\.cache\opencode" -ErrorAction SilentlyContinue` | 无输出或为空目录 |
| 4 | 确认项目目录有缓存 | `Get-ChildItem "venv\data-opencode\cache\opencode"` | 存在 models.json、version、bin/ 等 |
| 5 | 运行一次 OpenCode | `opencode debug info` | 正常输出，无异常 |
| 6 | 确认日志落点正确 | `Get-ChildItem "venv\data-opencode\opencode\log"` | 产生新日志文件 |


## 五、与其他 Session 的边界说明

本次 session **不涉及**以下文件的变更（这些属于历史 session，不在本次 diff 范围内）：

| 文件/目录 | 所属 Session | 说明 |
|-----------|-------------|------|
| `apps/api-demo/src/api_demo/utils/iso_agent_manager.py` | Handoff V12 | ISO Agent 进程管理 |
| `apps/api-demo/src/api_demo/routers/iso_agent.py` | Handoff V12 | ISO Agent 路由 |
| `apps/web-demo/html/debug/iso-agent/index.html` | Handoff V12 | ISO Agent 调试页 |
| `DESIGN.md` | Handoff V12 | 设计基准更新 |
| `apps/archive/` | V10 | 归档机制 |
| `backend/` 全部源码 | V1~V9 | 业务代码 |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-05-31 |
| **更新人** | Human + Agent Session |
| **变更触发** | 探索 OpenCode 缓存目录时发现 XDG_CACHE_HOME 缺失，缓存泄漏到用户目录 |
| **下次修订条件** | OpenCode 隔离策略有进一步调整（如增设更多 XDG 变量、发现新的泄漏点）时追加 |
| **跨环境迁移参考** | 新环境需同步 `.vscode/settings.json` 的 `XDG_CACHE_HOME` + 复制 `references/` 下的 changelog 和 env-migrations 内容 |


*文档生成时间：2026-05-31*  
*最后更新时间：2026-05-31*  
*对应 Session 主题：OpenCode 缓存隔离修正与决策复盘*
