---
title: 归档工作流 v2 增强（空目录检测 + audit + 模式语法统一）
description: archive_project.py 迁移到 py-lib 入口模式后的深度增强：空目录/0字节检测、压缩 audit、根级锚点模式语法、插件间 import 规则沉淀
date: 2026-06-21
---

# env-migration-archive-workflow-v2-enhancement-2026-06-21-143000

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | 归档工作流 v2 增强（空目录检测 + audit + 模式语法统一） |
| **日期** | 2026-06-21 |
| **文件名时间戳** | `2026-06-21-143000` |
| **触发原因** | 压缩耗时异常排查中发现 node_modules 未排除、0字节文件审计缺失、模式语法不统一 |
| **影响范围** | `deploy-git-isolated/scripts/py-plugins/`、`py-tools/`、`archive-groups.json`、baseline |
| **风险等级** | 中（修改核心扫描/压缩逻辑，但已通过 cs_py + venv 双分组验证） |


## 一、文本文件变更清单

### 1. 新建 `scripts/py-plugins/archive_empty_handler.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_empty_handler.py` |
| **变更类型** | `新建` |
| **职责** | 空目录检测、0字节文件检测、.emptydir 填充/清理、明细输出 |
| **暴露接口** | `detect_empty_dirs()`、`detect_zero_byte_files()`、`fill_emptydirs()`、`cleanup_emptydirs()`、`write_detail_list()` |
| **验证方式** | `python -m py_compile` 通过；被 archive_scanner.py import 后无循环依赖 |


### 2. 修改 `scripts/py-plugins/archive_scanner.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_scanner.py` |
| **变更类型** | `修改` |
| **关键变更** | ① scan_group 集成 empty_handler（cleanup → detect → fill → detect_zero → write）；② 新增 `verify_group()`（解压 7z 与 listfile 交叉验证）；③ 新增 `cleanup_placeholders()`（供 workflow 层调用）；④ whitelist 尾部 `/` 清理；⑤ `match_blacklist` 增强（`/*.xxx` 根级锚点、子路径匹配） |
| **验证方式** | lint 通过；cs_py scan 40734 文件、venv scan 7168 文件，两次执行 SHA256 一致 |


### 3. 修改 `scripts/py-plugins/archive_compressor.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_compressor.py` |
| **变更类型** | `修改` |
| **关键变更** | 删除旧包逻辑（不跳过，强制重建）；新增 audit 输出：`listfile - 0字节 = 7z_files_read` |
| **验证方式** | cs_py audit PASS (40734-40=40694)；venv audit PASS (7168-23=7145) |


### 4. 修改 `scripts/py-tools/archive_project.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive_project.py` |
| **变更类型** | `修改` |
| **关键变更** | ① config 独立获取（不依赖 scan 阶段）；② verify 可独立执行（只需压缩包+listfile 存在）；③ 默认 `all` 不含 verify（`DEFAULT_STAGES = ["scan", "compress"]`）；④ verify 通过后 cleanup .emptydir |
| **验证方式** | `--stage all` → scan+compress；`--stage verify` → 独立解压比对 PASS |


### 5. 修改 `scripts/py-tools/archive-groups.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive-groups.json` |
| **变更类型** | `修改` |
| **关键变更** | ① cs_py 黑名单：`"cs_py/*.zip"` → `"/*.zip"`、`"cs_py/*.7z"` → `"/*.7z"`；② venv 黑名单去掉 `"venv/"` 前缀；③ venv whitelist 加尾部 `/` |
| **验证方式** | cs_py 根级归档文件正确排除；venv db 文件正确排除 |


### 6. 修改 `task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | `修改` |
| **关键变更** | 新增 8.4.7「插件间通信规则：同层插件允许直接 import」；修正重复标题编号 |
| **验证方式** | 8.4.x 章节编号连续无重复 |


## 二、非文本操作

无（本次全部为代码/配置修改，无文件系统迁移）。


## 三、模式语法真源（archive-groups.json 与 match_blacklist 对齐）

| 模式 | 语义 | 示例 |
|------|------|------|
| `dir/` | 排除目录及其所有子孙 | `venv/` |
| `dir/*` | 同 `dir/` | `data-opencode/opencode/log/*` |
| `a/b/c` | 子路径匹配（可在任意层级命中） | `data-opencode/opencode/opencode.db` |
| `/*.xxx` | **根级锚点**：仅匹配根目录下直接文件 | `/*.zip`、`/*.7z` |
| `*.xxx` | basename 匹配（递归所有层级） | `*.tmp` |

> **迁移注意**：旧配置中的 `"cs_py/*.zip"` 已废弃，统一为 `"/*.zip"`。


## 四、验证清单

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | cs_py scan | `archive_cs_py.py --stage scan` | 40734 文件，空目录 20，0字节 40 |
| 2 | cs_py compress | `archive_cs_py.py --stage compress` | audit PASS，311.8 MB |
| 3 | cs_py verify | `archive_cs_py.py --stage verify` | 40734/40734 匹配 PASS |
| 4 | venv all | `archive_project.py --group venv --stage all` | 7168 文件，audit PASS，10.9 MB |
| 5 | venv verify | `archive_project.py --group venv --stage verify` | 7168/7168 匹配 PASS |
| 6 | 双分组并行 | `archive_project.py --group cs_py venv --stage all` | 两者均 audit PASS |
| 7 | 历史文件保留 | `ls venv/tmp/archive-cs_py/listfile-cs_py-*.txt` | 存在时间戳版本 |


## 五、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 恢复旧包跳过逻辑 | 在 `archive_compressor.py` 中恢复 `if zip_path.exists() and not force: return {...}` |
| 恢复旧模式语法 | 在 `archive-groups.json` 中恢复 `"cs_py/*.zip"`、`"cs_py/*.7z"` |
| 移除 empty_handler | 删除 `archive_empty_handler.py`；在 `archive_scanner.py` 中恢复旧 `find_empty_dirs`/`create_placeholders` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-21-143000 |
| **更新人** | Human + Agent Session |
| **变更触发** | 压缩耗时异常排查 + 用户要求细化 |
| **下次修订条件** | 新增分组、模式语法扩展、verify 纳入默认 all |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-21*  
*模板版本：v2*