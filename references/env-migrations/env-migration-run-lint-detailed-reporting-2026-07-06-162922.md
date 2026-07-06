---
title: run-lint 插件逐项展示增强
description: 扩展 run-lint 输出格式，支持 md/py/ps1/json/encoding 全类型逐项检测结果展示，消除"通过"二字的模糊性。
date: 2026-07-06
meta:
  version: 1.0.0
---

# env-migration-run-lint-detailed-reporting-2026-07-06-162922

> **文档性质**：环境迁移指南。聚焦单次 session 对开发工具链的增强变更。  
> **受众**：Human + Agent。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | run-lint 插件逐项展示增强（md/py/ps1/json/encoding 全覆盖） |
| **日期** | 2026-07-06 |
| **文件名时间戳** | `2026-07-06-162922` |
| **触发原因** | lint 汇总输出过于简略（仅显示"通过"或"X处违规"），无法确认各检测细项是否真正执行，容易掩盖遗漏 |
| **影响范围** | `run-lint.py` 展示逻辑、`lint_encoding.py` 返回数据结构、`md_lint.py` 返回数据结构、`.code-workspace` 文件类型路由 |
| **风险等级** | 低（仅影响 lint 输出格式，不修改检测逻辑本身） |

## 一、文本文件变更清单

### 1. 修改 `run-lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | `修改` |
| **作用** | Phase 1 / Phase 3 输出逻辑重写，按 `(文件, 插件)` 分组，每个插件的检测细项逐条列出 |
| **新增覆盖** | `lint_json` → JSON 语法解析；`lint_encoding` → BOM/双BOM/CRLF/LF/UTF-8；`lint_python` → py_compile 语法；`lint_ps1` → PSParser::Tokenize 语法；`md_lint` → frontmatter 8 项 + --- 污染 |
| **迁移方式** | 直接替换文件；无需手动调整 |

### 2. 修改 `lint_encoding.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` |
| **变更类型** | `修改` |
| **作用** | `validate_file` 返回结果中新增 `metadata.check_details`，包含 BOM/双BOM/CRLF/LF/UTF-8 原始检测数据 |
| **迁移方式** | 直接替换文件 |

### 3. 修改 `md_lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| **变更类型** | `修改` |
| **作用** | `validate_file` 返回结果中新增 `metadata.check_details`，包含 frontmatter 8 项检测的布尔结果 |
| **迁移方式** | 直接替换文件 |

### 4. 修改 `run-lint.py` EXT_TO_PLUGIN 路由表

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/run-lint.py` |
| **变更类型** | `追加` |
| **新增内容** | `".code-workspace": ["lint_json"]` |
| **作用** | `.code-workspace` 文件类型等同于 `.json` / `.jsonc` 处理，走 JSON 语法检查 |

### 5. 版本号变更

| 文件 | 旧版本 | 新版本 | 变更说明 |
|------|--------|--------|---------|
| `run-lint.py` | v1.3.0 | **v1.4.0** | 新增逐项展示逻辑、`.code-workspace` 路由 |
| `lint_encoding.py` | v1.1.0 | **v1.2.0** | `validate_file` 返回 `metadata.check_details` |
| `md_lint.py` | v1.2.1 | **v1.3.0** | `validate_file` 返回 `metadata.check_details` |

## 二、非文本操作（文件系统/缓存迁移）

本次 session 无文件复制、缓存迁移或目录创建操作。

## 三、lint 输出格式对比

### 变更前（模糊）
```
  ✅ D:\pjt\cursor\cs_py\cs-py.code-workspace
  ✅ D:\pjt\cursor\cs_py\cs-py.code-workspace
```
→ 仅显示"通过"，无法确认具体检查了哪些细项。

### 变更后（逐项）
```
  📄 D:\pjt\cursor\cs_py\cs-py.code-workspace
    └─ [lint_encoding]
       ✅ 无 UTF-8 BOM 头检测
       ✅ 无 双 BOM 检测
       ✅ CRLF 行尾符 — 0 处
       ✅ LF 行尾符 — 50 处
       ✅ UTF-8 完整性检测
    └─ [lint_json]
       ✅ JSON 语法解析 — 通过
```

### `.md` 文件逐项示例
```
  📄 xxx.md
    └─ [md_lint]
       ✅ frontmatter 存在性检测
       ✅ frontmatter 必须从第 1 行开始
       ✅ 必填字段 title
       ✅ 必填字段 description
       ✅ 必填字段 date
       ✅ 必填字段 meta
       ✅ date 格式 YYYY-MM-DD
       ✅ description 与 date 未拼接
       ✅ 正文无 --- 污染
```

### `.py` 文件逐项示例
```
  📄 xxx.py
    └─ [lint_python]
       ✅ Python 语法解析（py_compile）— 通过
```

### `.ps1` 文件逐项示例
```
  📄 xxx.ps1
    └─ [lint_ps1]
       ✅ PowerShell 语法解析（PSParser::Tokenize）— 通过
```

## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py`（run-lint / 插件） | `run-lint.py` 自身 | Python 语法 | `py_compile` 通过 |
| `.md`（本文件） | `run-lint.py` | 编码 + md_lint | BOM=no, CRLF=0, frontmatter 合规 |

**执行示例**：
```powershell
"<devroot>\venv\py\python.exe" "<devroot>\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "<devroot>" --files "<devroot>\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" "<devroot>\references\env-migrations\env-migration-run-lint-detailed-reporting-2026-07-06-162922.md"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 `.code-workspace` 被识别 | `run-lint.py --files cs-py.code-workspace` | 不跳过，走 lint_json + lint_encoding |
| 2 | 确认 `.md` 逐项展示 | `run-lint.py --files xxx.md` | 输出 frontmatter 8 项 + --- 污染检测 |
| 3 | 确认 `.py` 逐项展示 | `run-lint.py --files xxx.py` | 输出 py_compile 语法检测 |
| 4 | 确认 `.ps1` 逐项展示 | `run-lint.py --files xxx.ps1` | 输出 PSParser::Tokenize 语法检测 |
| 5 | 确认 `.json` 逐项展示 | `run-lint.py --files xxx.json` | 输出 JSON 语法解析检测 |

## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复旧版输出格式 | 从 git 恢复 `run-lint.py`、`lint_encoding.py`、`md_lint.py` 的旧版本 |
| 移除 `.code-workspace` 路由 | 从 `EXT_TO_PLUGIN` 中删除 `".code-workspace": ["lint_json"]` 行 |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-06-162922 |
| **更新人** | Human + Agent Session |
| **变更触发** | lint 输出过于简略，用户要求展示逐项检测结果 |
| **下次修订条件** | 新增文件类型支持、新增检测细项、输出格式进一步调整 |
| **跨环境迁移参考** | 直接 git pull 最新代码即可，无需手动配置 |

*文档生成时间：2026-07-06*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
