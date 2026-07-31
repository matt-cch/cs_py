---
title: atomic-config-edit-json bak 路径改造与 CLI docstring 显式化
description: 修复 atomic-config-edit-json.py 备份文件污染 JSON 同目录的问题，改为 TMP 真源落盘；同步重构 workflow-download-article-to-vault.py 参数文档，使陌生 Agent 一眼锁定默认值。
date: 2026-07-30
meta:
  version: 1.0.0
---

# env-migration-atomic-config-edit-json-bak-tmp-and-cli-docstring-2026-07-30-173057

> **文档性质**：单次 session 的环境级变更记录。聚焦脚本接口与产物落盘规范的修正，非业务功能交付。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | atomic-config-edit-json bak 路径改造与 CLI docstring 显式化 |
| **日期** | 2026-07-30（frontmatter；文件名时间戳见上表） |
| **文件名时间戳** | `2026-07-30-173057` |
| **触发原因** | ① atomic-config-edit-json.py 的 `--backup` 在原 JSON 同目录生成 `.bak`，造成工作目录污染；② workflow-download-article-to-vault.py 的 docstring 参数描述模糊，陌生 Agent 构造命令行时遗漏 `--vault-dir` 或填入凭空路径 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py`（备份逻辑 + help 文本）、`references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py`（docstring + argparse help） |
| **风险等级** | 低（纯落盘路径与文档变更，无业务逻辑改动） |

## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-config-edit-json.py` |
| **变更类型** | `修改` |
| **作用** | 将 `--backup` 生成的 bak 文件从 JSON 同目录移至 TMP 真源目录，避免污染工作区 |

#### 变更前（污染代码）

```python
# 备份
if args.backup:
    bak_path = file_path.with_suffix(file_path.suffix + ".bak")
    bak_path.write_text(original_text, encoding="utf-8", newline="\n")
    manifest["backup_path"] = str(bak_path)
    print(f"[Backup] 已备份: {bak_path}")
```

#### 变更后（TMP 真源落盘）

```python
# 备份（落盘路径由 manifest_path 插件统一决定，禁止硬编码 venv/tmp/）
if args.backup:
    _scripts_dir = Path(__file__).parent.parent.resolve()
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
    from py_lib import load_plugins
    registry = load_plugins(devroot=str(devroot), tags=["utility"])
    manifest_path = registry.manifest_path
    bak_dir = manifest_path.get_manifest_dir(devroot)
    bak_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak_path = bak_dir / f"atomic-config-edit-json-{file_path.stem}-{ts}.bak"
    bak_path.write_text(original_text, encoding="utf-8", newline="\n")
    manifest["backup_path"] = str(bak_path)
    print(f"[Backup] 已备份: {bak_path}")
```

- **落盘位置**：由 `manifest_path` 插件统一决定（TMP/TEMP 优先，fallback 到 devroot/venv/tmp/）
- **文件名**：`atomic-config-edit-json-{stem}-{ts}.bak`（含时间戳防覆盖）
- **docstring `--backup` 说明同步更新**：明确标注"bak 落盘位置由 manifest_path 插件统一决定，禁止在 JSON 同目录生成 .bak"

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py` |
| **变更类型** | `修改` |
| **作用** | 重构 docstring 参数区块，使陌生 Agent 一眼锁定 `--vault-dir` 默认值，杜绝凭记忆构造错误路径 |

#### 变更前（散文式参数列表，默认值淹没在文本中）

```
  参数
    完整参数列表及默认值请运行: python workflow-download-article-to-vault.py --help

    --devroot      devroot 路径（默认自动探测）
    --vault-dir    目标 vault 目录（必填）
    --url          文章 URL（必填）
    ...
```

#### 变更后（表格 + 强制规则区块）

```
  参数
    完整参数列表及默认值请运行: python workflow-download-article-to-vault.py --help

    | 参数            | 必填 | 默认值/说明                                              |
    |-----------------|------|----------------------------------------------------------|
    | --devroot       | 是   | 无。polyrepo 场景下必须显式传入，禁止自动推导。          |
    | --vault-dir     | 是   | {devroot}/vaults/vault-demo。未指定时命令行必须带入此值。 |
    | --url           | 是   | 无。                                                     |
    ...

    --vault-dir 强制规则
      命令行中必须出现 --vault-dir。
      若任务未提供明确 vault 路径，其值必须固定为：
        {devroot}/vaults/vault-demo
      禁止根据记忆、经验或猜测填写其他路径。
```

- **命令行示例**：硬编码绝对路径改为 `{devroot}` 占位符，支持多端多根
- **argparse help 文本**：`--devroot` 标注 "polyrepo 场景下必须显式传入"；`--vault-dir` 标注 "默认值: {devroot}/vaults/vault-demo"；所有可选参数标注 "（可选）"
- **代码逻辑**：`vault_dir = Path(args.vault_dir).resolve() if args.vault_dir else devroot / "vaults" / "vault-demo"`

### 3. 实测验证 `apps/repos/matt-cch/jywl-settlement/git-security.json`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/repos/matt-cch/jywl-settlement/git-security.json` |
| **变更类型** | `测试验证`（无持久修改） |
| **作用** | 验证改造后的 `--backup` 不再在 JSON 同目录生成 bak |

- 执行 `atomic-config-edit-json.py --backup` 修改 `security_level`：`"normal"` → `"test"` → `"normal"`
- 结果：bak 文件生成于 `venv/tmp/atomic-config-edit-json-git-security-*.bak`，JSON 同目录无新增 bak
- 清理了旧残留 bak：`git-security.json.bak`（由旧版本脚本遗留）

## 二、非文本操作

本次 session 涉及一次旧残留 bak 清理：

| 操作类型 | 源路径 | 说明 |
|---------|--------|------|
| 删除旧残留 | `apps/repos/matt-cch/jywl-settlement/git-security.json.bak` | 旧版本 atomic-config-edit-json.py 遗留，已清理 |

## 三、环境变量速查

本次 session 未新增或修改环境变量注入项。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py`（atomic-config-edit-json.py） | `run-lint.py --profile lint-python` | Python 语法解析 | 通过 |
| `.py`（workflow-download-article-to-vault.py） | `run-lint.py --profile lint-python` | Python 语法解析 | 通过 |
| `.md`（本 env-migration） | `run-lint.py --profile lint-md` | frontmatter、编码、换行符 | 通过 |

## 五、验证清单（新环境可执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---|---------|---------|
| 1 | 确认 bak 落盘路径正确 | 执行 `--backup` 修改任意 JSON，观察输出 | `[Backup] 已备份: ...venv/tmp/...` |
| 2 | 确认 JSON 同目录无 bak | `Get-ChildItem <json_dir> -Filter "*.bak"` | 无输出 |
| 3 | 确认 docstring 含参数表格 | `python -c "import ast; print(ast.get_docstring(...))"` | 输出含 `\| 参数 \| 必填 \| 默认值/说明 \|` |
| 4 | 陌生 Agent 命令行构造测试 | 将脚本交给无上下文 Agent，观察构造的命令行 | `--vault-dir` 出现且值为 `{devroot}/vaults/vault-demo` |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 还原 atomic-config-edit-json.py | 从 git 历史恢复 bak 路径为 `file_path.with_suffix(file_path.suffix + ".bak")` 的版本 |
| 还原 workflow-download-article-to-vault.py | 从 git 历史恢复 docstring 为散文式参数列表的版本 |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-30-173057 |
| **更新人** | Human + Agent Session |
| **变更触发** | ① bak 污染工作目录；② CLI docstring 导致陌生 Agent 构造错误命令行 |
| **下次修订条件** | 当 manifest_path 插件的落盘策略变更，或脚本新增必填参数时 |
| **跨环境迁移参考** | 直接阅读本文档 + 执行「验证清单」 |

*文档生成时间：2026-07-30-173057*
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
