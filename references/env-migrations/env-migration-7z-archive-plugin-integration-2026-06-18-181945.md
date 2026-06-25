---
title: 7z 归档插件体系集成（deploy-git-isolated task）
description: 以 project-archive 标准归档为基础，用 7z 替换 zip，将扫描/压缩功能拆分为 py-plugins 模块，调用入口放在 py-tools 下。
date: 2026-06-18
---

# env-migration-7z-archive-plugin-integration-2026-06-18-181945

> **文档性质**：环境级变更记录。本次 session 在 deploy-git-isolated task 下新增了一套基于 7z 的项目归档体系，与现有 Git 部署流程无冲突。
> **受众**：Human + Agent。后续 Agent 可直接通过 py_lib 加载 archive 插件或通过 py-tools CLI 执行归档。


## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 7z 归档插件体系集成到 deploy-git-isolated task |
| **日期** | 2026-06-18 |
| **文件名时间戳** | `2026-06-18-181945` |
| **触发原因** | 用户要求以 project-archive 标准 zip 归档为基础，用 7z 替换，功能模块集成到 py-plugins/，调用模块集成到 py-tools/ |
| **影响范围** | deploy-git-isolated/scripts/py-plugins/、scripts/py-tools/、scripts/py-sort-rules.json |
| **风险等级** | 低（纯新增模块，不影响现有 Git 部署流程） |


## 一、文本文件变更清单

### 1. 新建 `scripts/py-plugins/archive_config.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_config.py` |
| **变更类型** | `新建` |
| **作用** | 归档配置：GROUPS 定义（cs_py / venv）、7z 路径解析（从 verified-runtime-index.json 真源推导 + fallback）、输出目录 |
| **验证方式** | `python archive_config.py` 自检应输出 7z 路径和两组配置 |
| **迁移方式** | 直接复制文件即可 |

### 2. 新建 `scripts/py-plugins/archive_scanner.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_scanner.py` |
| **变更类型** | `新建` |
| **作用** | 归档扫描器：磁盘扫描、黑白名单过滤、空目录 `.emptydir` 占位、CSV + listfile 输出 |
| **验证方式** | 调用 `scan_group(cfg)` 应返回正确的 file_count / dir_count / total_size |
| **迁移方式** | 直接复制文件即可 |

### 3. 新建 `scripts/py-plugins/archive_compressor.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_compressor.py` |
| **变更类型** | `新建` |
| **作用** | 归档压缩器：7z 压缩封装（`-tzip`/`-t7z`）、心跳进度、stdout 统计解析、同时删除 `.zip` 和 `.7z` 旧包 |
| **验证方式** | 调用 `compress_group(cfg, seven_zip, fmt="7z")` 应生成压缩包并返回 size_mb |
| **迁移方式** | 直接复制文件即可 |

### 4. 修改 `scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | `追加` |
| **新增内容** | plugins 数组追加 archive_config、archive_scanner、archive_compressor 三条；profiles 追加 `"archive"` profile |
| **插入位置** | plugins 末尾（browser_session 之后）；profiles 末尾（minimal 之后） |
| **作用** | 使 py_lib.py 拓扑排序能加载 archive 插件 |
| **验证方式** | `python py_lib.py` 自检应列出 archive 插件 |
| **迁移方式** | 直接追加条目 |

### 5. 新建 `scripts/py-tools/archive_project.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive_project.py` |
| **变更类型** | `新建` |
| **作用** | 主 CLI：`--group cs_py|venv --stage scan,compress,verify --format zip|7z|auto --force` |
| **验证方式** | 执行全链条 `--group cs_py venv --stage all --format auto --force` 应 PASS |
| **迁移方式** | 直接复制文件即可 |

### 6. 新建 `scripts/py-tools/archive_cs_py.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive_cs_py.py` |
| **变更类型** | `新建` |
| **作用** | 快捷调用：`archive_project.py --group cs_py ...` |
| **迁移方式** | 直接复制文件即可 |

### 7. 新建 `scripts/py-tools/archive_venv.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive_venv.py` |
| **变更类型** | `新建` |
| **作用** | 快捷调用：`archive_project.py --group venv ...` |
| **迁移方式** | 直接复制文件即可 |


## 二、非文本操作

无。本次 session 全部为代码文件新建/修改，无文件系统迁移操作。


## 三、黑白名单精确配置

| 分组 | 白名单 | 黑名单 |
|------|--------|--------|
| cs_py | （无，全量扫描） | `venv/`、`cs_py/*.zip`、`cs_py/*.7z` |
| venv | `.opencode`、`data-opencode`、`version` | `venv/data-opencode/opencode/log/*`、`venv/data-opencode/opencode/opencode.db`、`.db-shm`、`.db-wal` |

> **来源**：venv 组的黑名单精确引用自 `debug/archive-compare/exclude-venv.txt` 真源，避免误伤其他 `.db` 文件。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `check-file-encoding.ps1` | BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.py`（全部插件/工具） | `python -m py_compile` | 语法无错误 | exit code = 0 |

**lint 执行记录**：
```
archive_config.py     -> lint exit code: 0
archive_scanner.py    -> lint exit code: 0
archive_compressor.py -> lint exit code: 0
archive_project.py    -> lint exit code: 0
archive_cs_py.py      -> lint exit code: 0
archive_venv.py       -> lint exit code: 0
py-sort-rules.json    -> json lint exit code: 0
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | archive_config 自检 | `python scripts/py-plugins/archive_config.py` | 输出 7z 路径和两组配置 |
| 2 | venv 组全链条 | `python scripts/py-tools/archive_project.py --group venv --stage all --format 7z --force` | scan+compress+verify 全部 PASS |
| 3 | cs_py 组全链条 | `python scripts/py-tools/archive_project.py --group cs_py --stage all --format 7z --force` | scan+compress+verify 全部 PASS |
| 4 | auto 格式自动选 7z | `python scripts/py-tools/archive_project.py --group venv --stage compress --format auto --force` | 输出 `[auto] 已验证 7z 更优，自动选择 7z` |
| 5 | py_lib 插件加载 | `python scripts/py_lib.py` | 已加载插件列表包含 archive_config、archive_scanner、archive_compressor |


## 六、全链条实测数据

| 分组 | 扫描文件数 | 原始大小 | 压缩格式 | 压缩大小 | 压缩耗时 | 验证 |
|------|-----------|---------|---------|---------|---------|------|
| cs_py | 40548 | 510.9 MB | 7z | 311.1 MB | 33.5s | PASS |
| venv | 7164 | 116.7 MB | 7z | 11.0 MB | 19.5s | PASS |

> **格式对比**：cs_py 组 zip 379.2 MB vs 7z 311.1 MB（7z 小 18%）；venv 组 zip 25.1 MB vs 7z 11.0 MB（7z 小 56%）。auto 默认选 7z。


## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增文件 | `Remove-Item scripts/py-plugins/archive_*.py; Remove-Item scripts/py-tools/archive_*.py` |
| 恢复 py-sort-rules.json | 删除 plugins 中的 archive_config/archive_scanner/archive_compressor 三条；删除 profiles 中的 archive profile |
| 删除输出产物 | `Remove-Item cs_py.7z, venv.7z, cs_py.zip, venv.zip` |


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-18-181945 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求集成 7z 归档功能到 deploy-git-isolated task |
| **下次修订条件** | 新增归档分组、调整黑白名单、扩展压缩格式 |
| **跨环境迁移参考** | 直接复制 7 个文件 + 更新 py-sort-rules.json，按「验证清单」逐条执行 |


*文档生成时间：2026-06-18-181945*
