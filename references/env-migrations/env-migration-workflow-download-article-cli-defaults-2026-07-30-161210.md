---
title: workflow-download-article CLI 默认值显式化与多端兼容改造
description: 对 workflow-download-article-to-vault.py 的 docstring、argparse help 及命令行示例进行重构，使陌生 Agent 能一眼锁定 --vault-dir 默认值，避免构造错误命令行。
date: 2026-07-30
meta:
  version: 1.0.0
---

# env-migration-workflow-download-article-cli-defaults-2026-07-30-161210

> **文档性质**：单次 session 的环境级变更记录。聚焦脚本接口文档本身的可读性与多端兼容性改进，非业务功能交付。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | workflow-download-article CLI 默认值显式化与多端兼容改造 |
| **日期** | 2026-07-30（frontmatter；文件名时间戳见上表） |
| **文件名时间戳** | `2026-07-30-161210` |
| **触发原因** | 陌生 Agent 构造命令行时遗漏 `--vault-dir` 或填入凭空路径（如 `D:\bak\vault`），与脚本设计意图不符 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py` 的 docstring 与 argparse help 文本 |
| **风险等级** | 极低（纯文档/接口声明变更，无代码逻辑改动） |

## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py` |
| **变更类型** | `修改` |
| **插入位置** | 文件头部 docstring（第 1–45 行附近）及 `main()` 内 argparse 定义（第 374–383 行附近） |
| **作用** | 让陌生 Agent 在参数列表中一眼锁定 `--vault-dir` 默认值，杜绝凭记忆构造错误路径 |

#### 具体变更内容

**A. docstring 参数区块重构**

原格式（行内散文式描述，默认值淹没在文本中）：

```
  参数
    完整参数列表及默认值请运行: python workflow-download-article-to-vault.py --help

    --devroot      devroot 路径（默认自动探测）
    --vault-dir    目标 vault 目录（必填）
    ...
```

新格式（三列表格 + 独立强制规则区块）：

```
  参数
    完整参数列表及默认值请运行: python workflow-download-article-to-vault.py --help

    | 参数            | 必填 | 默认值/说明                                              |
    |-----------------|------|----------------------------------------------------------|
    | --devroot       | 是   | 无。polyrepo 场景下必须显式传入，禁止自动推导。          |
    | --vault-dir     | 是   | {devroot}/vaults/vault-demo。未指定时命令行必须带入此值。 |
    | --url           | 是   | 无。                                                     |
    | --tags          | 否   | 无。                                                     |
    | --headed        | 否   | 无。（调试用）                                           |
    | --slug          | 否   | 无。默认从文章文件名提取。                               |
    | --dry-run       | 否   | 无。                                                     |
    | --show-progress | 否   | 无。                                                     |

    --vault-dir 强制规则
      命令行中必须出现 --vault-dir。
      若任务未提供明确 vault 路径，其值必须固定为：
        {devroot}/vaults/vault-demo
      禁止根据记忆、经验或猜测填写其他路径。
```

**B. 命令行示例改为占位符格式**

原示例（硬编码绝对路径，多端不兼容）：

```
  python workflow-download-article-to-vault.py \
      --devroot "D:\pjt\cursor\cs_py" \
      --vault-dir "D:\pjt\cursor\cs_py\vaults\vault-demo" \
```

新示例（`{devroot}` 占位符，支持多端多根）：

```
  python workflow-download-article-to-vault.py \
      --devroot "{devroot}" \
      --vault-dir "{devroot}\vaults\vault-demo" \
```

**C. argparse help 文本同步改进**

- `--devroot`：`help` 追加 "polyrepo 场景下必须显式传入，禁止依赖脚本位置的自动推导"
- `--vault-dir`：`help` 追加 "默认值: {devroot}/vaults/vault-demo。未从外部获得明确路径时，必须使用此默认值，禁止自行推断其他路径"
- 所有可选参数：`help` 追加 "（可选）" 标注

| **验证方式** | 执行 `python workflow-download-article-to-vault.py --help`，确认 usage 行中 `--vault-dir` 不带 `[ ]`（表示必填），且 help 文本包含默认值说明 |
| **迁移方式** | 无需迁移；本变更是对既有脚本文档的自修正，不涉及外部配置或环境变量 |

## 二、非文本操作

本次 session 不涉及文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。

## 三、环境变量速查

本次 session 未新增或修改环境变量注入项。请保持 `.vscode/settings.json` 中现有 `terminal.integrated.env.windows` 配置不变。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py --profile lint-encoding` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.py`（被修改脚本） | `run-lint.py --profile lint-python` | Python 语法解析 | 通过 |

执行示例：

```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-download-article-to-vault.py"
```

## 五、验证清单（新环境可执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---|---------|---------|
| 1 | 确认脚本 docstring 包含参数表格 | `python -c "import ast; print(ast.get_docstring(ast.parse(open('workflow-download-article-to-vault.py').read())))"` | 输出中包含 `| 参数 | 必填 | 默认值/说明 |` 表格 |
| 2 | 确认 `--vault-dir` help 含默认值 | `python workflow-download-article-to-vault.py --help` | `--vault-dir` 的 help 行包含 `{devroot}/vaults/vault-demo` |
| 3 | 陌生 Agent 命令行构造测试 | 将脚本路径与 URL 交给无上下文 Agent，观察其构造的命令行 | `--vault-dir` 出现在命令行中，且值为默认值，非凭空路径 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 还原 docstring | 从 git 历史恢复 `workflow-download-article-to-vault.py` 的前一版本 |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-30-161210 |
| **更新人** | Human + Agent Session |
| **变更触发** | 陌生 Agent 构造命令行时遗漏 `--vault-dir` 或填入与脚本默认值不符的路径 |
| **下次修订条件** | 当脚本新增 CLI 参数或目录结构变更导致默认值需要调整时 |
| **跨环境迁移参考** | 直接阅读本文档 + 执行「验证清单」Step 2 |

*文档生成时间：2026-07-30-161210*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
