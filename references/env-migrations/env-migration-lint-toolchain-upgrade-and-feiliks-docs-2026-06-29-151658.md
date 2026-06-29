---
title: env-migration — lint 工具链升级与 FEILIKS 发票 CSV 文档沉淀
description: 本次 session 完成了 md_lint / lint_encoding / lint_ps1 三个 lint 插件的升级修复，并补全了 FEILIKS 发票 CSV 工具链的文档资产。
date: 2026-06-29
meta:
  version: 1.0.0
---

# env-migration — lint 工具链升级与 FEILIKS 发票 CSV 文档沉淀

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | lint 工具链升级（md_lint v1.2.1 + lint_encoding v1.1.0 + lint_ps1 修复）与 FEILIKS 发票 CSV 工具链文档沉淀 |
| **日期** | 2026-06-29 |
| **文件名时间戳** | `2026-06-29-151658` |
| **触发原因** | 用户指令要求记录本次 session 产生的全部环境级与工具链级变更 |
| **影响范围** | lint 插件体系（3 个文件）、changelog（2 个文件）、FEILIKS 文档资产（3 个文件）、真源索引（1 个文件） |
| **风险等级** | 低（仅工具链增强与文档更新，不涉及业务代码或环境配置） |


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | v1.2.0 → v1.2.1：`_fix_frontmatter_fields()` 新增 `missing_keys` 参数，支持在 frontmatter 闭合 `---` 前自动插入 `meta: {}` |
| **作用** | `--fix` 模式下缺失 `meta` 字段可自动补全，无需人工干预 |
| **验证方式** | 对测试文件执行 `validate_file(path, fix=True)`，确认 `meta: {}` 已插入且重新检测 violations = 0 |
| **迁移方式** | 直接覆盖（该文件为项目内插件，无外部依赖） |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | v1.0.3 → v1.1.0：新增 UTF-8 完整性检测（`raw.decode("utf-8")`），覆盖截断/损坏场景 |
| **作用** | 填补 BOM/CRLF 检测盲区，截断字节流不再被误判为合规 |
| **验证方式** | 对截断测试文件执行 scan，确认报 `UTF8_INCOMPLETE` |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_ps1.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_ps1.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | `subprocess.run(text=True, encoding="utf-8")` → `text=False` + `decode("utf-8", errors="replace")` |
| **作用** | 消除 PowerShell GBK 中文输出在 reader thread 抛 `UnicodeDecodeError` 的崩溃 |
| **验证方式** | 对含中文的 `.ps1` 执行 lint，确认正常完成不崩溃 |
| **迁移方式** | 直接覆盖 |

### 4. 新建 `references/changelog/changelog-2026-06-29-md-lint-meta-auto-fix.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/changelog-2026-06-29-md-lint-meta-auto-fix.md` |
| **变更类型** | 新建 |
| **作用** | 记录 md_lint v1.2.1 升级详情 |
| **迁移方式** | 直接复制 |

### 5. 新建 `references/changelog/changelog-2026-06-29-lint-encoding-utf8-integrity.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/changelog-2026-06-29-lint-encoding-utf8-integrity.md` |
| **变更类型** | 新建 |
| **作用** | 记录 lint_encoding v1.1.0 升级详情 |
| **迁移方式** | 直接复制 |

### 6. 新建 `references/env-migrations/env-migration-feiliks-invoice-csv-toolchain-2026-06-29-145157.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/env-migrations/env-migration-feiliks-invoice-csv-toolchain-2026-06-29-145157.md` |
| **变更类型** | 新建 |
| **作用** | 补录 FEILIKS 发票 CSV 工具链的环境记录（工具位置、标准调用、数据特征、流水线、历史运行） |
| **迁移方式** | 直接复制 |

### 7. 修改 `docs/playbooks/csv-invoice-date-update-playbook.md`

| 属性 | 值 |
|------|-----|
| **路径** | `docs/playbooks/csv-invoice-date-update-playbook.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 追加第 8 节「xlsx → csv 转换（配套工具）」，含职责说明、标准调用、实测输出、流水线衔接 |
| **作用** | playbook 覆盖完整工具链（xlsx→csv→filter→date update） |
| **迁移方式** | 按 diff 合并或直接覆盖 |

### 8. 修改 `references/env-migrations/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/env-migrations/README.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 导航表追加 FEILIKS 发票 CSV 工具链 env-migration 条目 |
| **作用** | 保持导航索引与磁盘文件一致 |
| **迁移方式** | 追加一行 |

### 9. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | 更新 `roots.devroot.path`、`github_connectivity` latency、各工具版本号 |
| **作用** | 真源索引反映当前环境状态 |
| **迁移方式** | 执行 `verify-runtime.py` 重新生成 |

### 10. 修改 `references/changelog/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/changelog/README.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 导航表追加 md_lint 和 lint_encoding 两个 changelog 条目 |
| **作用** | 保持导航索引与磁盘文件一致 |
| **迁移方式** | 追加行 |


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
| `.md`（env-migration / playbook / changelog） | `run-lint.py`（md_lint + lint_encoding） | frontmatter、BOM、CRLF | ✅ 全部通过 |
| `.py`（lint 插件） | `python -m py_compile` | Python 语法 | ✅ 全部通过 |
| `.json`（真源索引） | `run-lint.py`（lint_json） | JSON 语法 | ✅ 通过 |
| `deploy-git-isolated` 全量 | `run-lint.py --profile lint` | 混合类型统一验证 | ✅ 0 违规 |


## 五、验证清单（新环境建议执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 lint 插件语法正确 | `python -m py_compile md_lint.py lint_encoding.py lint_ps1.py` | 无报错 |
| 2 | 确认 md_lint --fix 工作正常 | 对缺少 meta 的测试文件执行 `validate_file(path, fix=True)` | 自动插入 `meta: {}` |
| 3 | 确认 lint_encoding UTF-8 检测有效 | 对截断文件执行 scan | 报 `UTF8_INCOMPLETE` |
| 4 | 确认 lint_ps1 不崩溃 | 对含中文的 `.ps1` 执行 lint | 正常完成 |
| 5 | 确认 playbook 可访问 | 打开 `docs/playbooks/csv-invoice-date-update-playbook.md` | 第 8 节存在 |
| 6 | 确认 env-migration 导航完整 | 打开 `references/env-migrations/README.md` | FEILIKS 条目存在 |


## 六、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 还原 lint 插件 | `git checkout references/tasks/deploy-git-isolated/scripts/py-plugins/md_lint.py lint_encoding.py lint_ps1.py` |
| 还原文档 | `git checkout docs/playbooks/csv-invoice-date-update-playbook.md references/env-migrations/README.md references/changelog/README.md` |
| 删除新建文件 | `git rm references/changelog/changelog-2026-06-29-md-lint-meta-auto-fix.md references/changelog/changelog-2026-06-29-lint-encoding-utf8-integrity.md references/env-migrations/env-migration-feiliks-invoice-csv-toolchain-2026-06-29-145157.md` |
| 还原真源索引 | `git checkout references/runtime/verified-runtime-index.json`（或重新执行 verify-runtime.py） |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-29-151658 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指令「记录 env-migration」，选择记录本次 session 整体工作 |
| **下次修订条件** | lint 插件再次升级、FEILIKS 工具链新增脚本或变更数据特征 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 + 重新执行 `verify-runtime.py` 更新真源索引 |
