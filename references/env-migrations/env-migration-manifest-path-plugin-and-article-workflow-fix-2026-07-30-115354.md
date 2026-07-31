---
title: manifest_path 插件体系建设与 workflow-download-article-to-vault 修复
description: 建设产物落盘路径唯一真源（manifest_path 插件 + atomic-get-manifest-path CLI），修复 article workflow 无图片崩溃与错误落盘路径 bug，同步 baseline 与审计双保险。
date: 2026-07-30
meta: {}
---

# env-migration-manifest-path-plugin-and-article-workflow-fix-2026-07-30-115354

> **Session 主题**：建设产物落盘路径唯一真源插件体系，修复 workflow-download-article-to-vault.py 边缘 bug
> **受众**：Human + Agent。在新环境复现时，直接按「文本文件变更清单」执行即可。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | manifest_path 插件体系建设 + workflow-download-article-to-vault 修复 |
| **日期** | 2026-07-30 |
| **文件名时间戳** | `2026-07-30-115354` |
| **触发原因** | 头条文章下载 workflow 在无图片场景崩溃；manifest 错误写到 vault 目录；各脚本自行推算落盘路径导致不一致 |
| **影响范围** | py-plugins/、py-tools/、baseline/、.cursor/rules/、AGENTS.md、verified-trigger-index.json |
| **风险等级** | 中（新增插件体系，但零副作用设计，不影响既有流程） |

## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/manifest_path.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/manifest_path.py` |
| **变更类型** | `新建` |
| **作用** | 产物落盘路径唯一真源插件：TMP/TEMP 优先，fallback 到 devroot/venv/tmp/，提供 `get_manifest_dir()` 和 `build_manifest_path()` 两层 API |
| **验证方式** | `python manifest_path.py --devroot "${devroot}" --tool-name "test"` 应输出 `venv/tmp/test-manifest-*.json` |
| **迁移方式** | 直接复制文件到目标路径即可 |

### 2. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-get-manifest-path.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-get-manifest-path.py` |
| **变更类型** | `新建` |
| **作用** | 原子 CLI：查询产物落盘路径。类似 `get-timestamp.py` 模式，支持 `--devroot`/`--tool-name`/`--suffix`/`--ext`/`--json` |
| **验证方式** | `python atomic-get-manifest-path.py --devroot "${devroot}" --tool-name "test" --json` 应输出含 `dir`/`path`/`filename` 的 JSON |
| **迁移方式** | 直接复制文件到目标路径即可 |

### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py` |
| **变更类型** | `修改` |
| **修改内容 1** | `step3_verify` 返回值由 `img_dir or Path()` 改为 `img_dir`（保留 None，不 fallback 到当前目录） |
| **修改内容 2** | `step8_cleanup` 改为通过 `py_lib.load_plugins(devroot=..., tags=["utility"])` 加载 `manifest_path` 插件获取落盘路径，删除内嵌 `os.environ.get("TMP")` 推算逻辑 |
| **作用** | 修复无图片崩溃 bug；根治 manifest 错误写到 vault 目录的问题；统一走唯一真源 |
| **验证方式** | 执行无图片的头条文章下载 workflow，Step 6/8 和 Step 8/8 均应通过，manifest 写到 `devroot/venv/tmp/` |
| **迁移方式** | 直接按修改内容替换对应函数即可 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | `追加` |
| **新增内容** | `manifest_path` 插件注册条目（tags: `["core", "utility"]`，depends: `[]`） |
| **作用** | 使 py_lib 能够发现和加载 manifest_path 插件 |
| **验证方式** | `python -c "from py_lib import load_plugins; r = load_plugins(devroot='...', tags=['utility']); print(r.manifest_path)"` 应成功 |
| **迁移方式** | 直接追加条目到 plugins 数组末尾 |

### 5. 修改 `references/tasks/deploy-git-isolated/ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | `追加` |
| **新增内容** | `active_scripts` 追加 `manifest_path.py`（插件）和 `atomic-get-manifest-path.py`（原子 CLI） |
| **作用** | 工具索引登记，供 Agent/人速查 |
| **迁移方式** | 直接追加条目 |

### 6. 修改 `references/tasks/deploy-git-isolated/baseline/baseline-plugin-architecture.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-plugin-architecture.md` |
| **变更类型** | `修改` |
| **修改内容** | §8.4.8：规则由「固定 devroot/venv/tmp/」改为「TMP/TEMP 优先，未配置则 fallback」；实现要求表格新增「系统配置了 TMP/TEMP」场景；追加「实现真源」条款引用 manifest_path |
| **作用** | 框架层与代码实现对齐 |
| **迁移方式** | 直接替换 §8.4.8 内容 |

### 7. 修改 `references/tasks/deploy-git-isolated/baseline/baseline-workflow-deploy.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-workflow-deploy.md` |
| **变更类型** | `修改` |
| **修改内容** | §8.9.2 表格追加「实现真源」行；§8.9.4 默认回退示例分两层展示（TMP/TEMP 优先 + fallback） |
| **作用** | `--output` 回退路径规范与 manifest_path 插件对齐 |
| **迁移方式** | 直接替换对应段落 |

### 8. 修改 `references/tasks/deploy-git-isolated/baseline/baseline-index.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-index.md` |
| **变更类型** | `追加` |
| **新增内容** | 版本历史追加 v2.6.0（2026-07-30）变更记录 |
| **作用** | 索引导航同步 |
| **迁移方式** | 直接追加到版本历史表格 |

### 9. 修改 `.cursor/rules/high-frequency-tool-shell-audit.mdc`

| 属性 | 值 |
|------|-----|
| **路径** | `.cursor/rules/high-frequency-tool-shell-audit.mdc` |
| **变更类型** | `修改` |
| **修改内容** | 自检清单追加第 5 项：「是否涉及 --output / manifest 产物路径确定？」；流程图插入 `--output` 路径判断节点 |
| **作用** | Tool 调用前审计层自动提醒 Agent 调用 atomic-get-manifest-path |
| **迁移方式** | 直接追加/替换对应段落 |

### 10. 修改 `venv/.opencode/AGENTS.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/AGENTS.md` |
| **变更类型** | `追加` |
| **新增内容** | 「根目录与文件系统」节追加「产物落盘路径（--output / manifest）」铁律：必须调用 atomic-get-manifest-path.py |
| **作用** | 项目级硬性约束双保险 |
| **迁移方式** | 直接追加到「临时与中间产物」条款之后 |

### 11. 修改 `references/runtime/verified-trigger-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-trigger-index.json` |
| **变更类型** | `追加` |
| **新增内容** | 注册 `atomic-manifest` source_prefix；追加 2 条触发条件（T001: manifest路径查询 high；T002: 隐式路径确定 medium） |
| **作用** | 触发条件索引治理，语义触发兜底 |
| **迁移方式** | 通过 atomic-config-edit-json.py --batch 安全追加 |

## 二、非文本操作

本次 session 不涉及文件系统/缓存迁移等非文本操作。

## 三、环境变量速查

本次 session 不涉及环境变量变更（TMP/TEMP 由外部 `.code-workspace` 统一控制，脚本只读取不修改）。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py --profile lint-encoding` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.json`（ENTRY.json / py-sort-rules.json / verified-trigger-index.json） | `run-lint.py --profile lint-json` | JSON 语法 | `[OK]` 无解析错误 |
| `.py`（新增脚本） | `run-lint.py --profile lint-python` | py_compile 语法 | 通过 |

执行示例：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-manifest-path-plugin-and-article-workflow-fix-2026-07-30-115354.md"
```

## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 manifest_path 插件可加载 | `python -c "from py_lib import load_plugins; r = load_plugins(devroot='...', tags=['utility']); print(r.manifest_path.get_manifest_dir(Path('...')))"` | 输出 `D:\...\venv\tmp` |
| 2 | 确认 atomic CLI 正常 | `python atomic-get-manifest-path.py --devroot "${devroot}" --tool-name "test"` | 输出完整路径到 `venv/tmp/test-manifest-*.json` |
| 3 | 确认 article workflow 修复 | 执行无图片头条文章下载 | Step 6/8 和 8/8 通过，无 `shutil.Error`，manifest 写到 `venv/tmp/` |
| 4 | 确认 audit.mdc 自检项存在 | 打开 `.cursor/rules/high-frequency-tool-shell-audit.mdc` | 自检清单含「--output / manifest 产物路径确定」项 |
| 5 | 确认 AGENTS.md 铁律存在 | 打开 `venv/.opencode/AGENTS.md` | 「根目录与文件系统」节含「产物落盘路径」铁律 |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 manifest_path 插件 | 删除 `py-plugins/manifest_path.py`，从 `py-sort-rules.json` 移除对应条目 |
| 移除 atomic CLI | 删除 `py-tools/atomic-get-manifest-path.py`，从 `ENTRY.json` 移除对应条目 |
| 恢复 workflow 旧逻辑 | 将 `workflow-download-article-to-vault.py` 的 `step8_cleanup` 改回内嵌 `os.environ.get("TMP")` 推算 |
| 恢复 baseline 旧版 | 从 git 历史检出 2026-07-30 之前的 `baseline-plugin-architecture.md` 和 `baseline-workflow-deploy.md` |
| 恢复 audit.mdc 旧版 | 删除自检清单中的「--output / manifest」项 |
| 恢复 AGENTS.md 旧版 | 删除「产物落盘路径」铁律条款 |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-30-115354 |
| **更新人** | Human + Agent Session |
| **变更触发** | workflow-download-article-to-vault 崩溃 + 落盘路径不一致 |
| **下次修订条件** | 新增其他需要统一落盘路径的脚本；manifest_path API 扩展 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
