---
title: 头条文章下载工具链索引补全与 docstring 增强
description: 补全 download-article.py 及其依赖插件在 ENTRY.json 的登记，重写 docstring（版本/意图/依赖/示例），并在 TASK-TOOLS-INDEX/EXEC-CHEATSHEET/README 中增加浏览器/Chrome 工具聚合导航，解决"找不着"问题。
date: 2026-07-10
meta: {}
---

# env-migration-download-article-index-docstring-2026-07-10-162824

> **文档性质**：环境迁移指南。聚焦 task 工具链的索引治理与文档完备性，确保 Agent 和人类能在新环境中快速发现浏览器/Chrome/文章下载相关工具。
> **受众**：Human + Agent。

### 文件命名（硬性）

| 部分 | 格式 | 示例 |
|------|------|------|
| 前缀 | `env-migration-` | — |
| 主题 | `download-article-index-docstring` | — |
| 时间戳 | `2026-07-10-162824` | — |
| 扩展名 | `.md` | — |

完整文件名：`env-migration-download-article-index-docstring-2026-07-10-162824.md`


## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 头条文章下载工具链索引补全与 docstring 增强 |
| **日期** | 2026-07-10 |
| **文件名时间戳** | `2026-07-10-162824` |
| **触发原因** | 用户下载头条文章时发现 `download-article.py` 在 ENTRY.json 未登记，docstring 缺少版本/意图/依赖/示例；浏览器工具散落在多处无聚合入口 |
| **影响范围** | `ENTRY.json` active_scripts、`download-article.py` docstring、`TASK-TOOLS-INDEX.md`、`EXEC-CHEATSHEET.md`、`scripts/README.md`、`py-tools/README.md` |
| **风险等级** | 低（纯索引/文档变更，不涉及业务代码） |


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | `追加` |
| **新增内容** | `active_scripts` 追加 4 条：<br>① `download-article.py`（文章下载 CLI 入口）<br>② `article_extractor.py`（提取编排插件）<br>③ `chrome_session.py`（Session 状态检测器）<br>④ `js_loader.py`（JS 资产拓扑排序） |
| **插入位置** | `active_scripts` 数组末尾，`atomic-check-chrome-session.py` 之后 |
| **作用** | 将浏览器/文章下载工具链纳入核心索引，确保 Agent 通过 ENTRY.json 即可发现可用工具 |
| **验证方式** | `grep '"name": "download-article.py"' ENTRY.json` 应命中 |
| **迁移方式** | 直接追加 |


### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/download-article.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-article.py` |
| **变更类型** | `修改`（docstring 重写） |
| **新增/修改内容** | docstring 新增：<br>- 版本号 `v1.0.0`<br>- 设计意图（标准化 URL→Markdown 流程、头条 Session 门禁）<br>- 外部依赖（Playwright、Chrome、py_lib 插件体系、JS 资产）<br>- 6 组命令行示例（基本用法/标签/输出目录/headed/跳过 preflight/显式 devroot） |
| **插入位置** | 文件顶部，替换原简短 docstring |
| **作用** | 使 Agent 和人类无需翻源码即可理解工具用途、依赖和调用方式 |
| **验证方式** | `head -30 download-article.py` 应看到版本号和命令行示例 |
| **迁移方式** | 直接覆盖 docstring 段落 |


### 3. 修改 `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | `追加` |
| **新增内容** | ① 边界矩阵新增 3 行（Chrome Session 检测 / 文章下载 / 截图验证）；② 速查命令新增 4 条（chrome session 默认检测 / --output / --user-data-dir / --domain-patterns） |
| **插入位置** | §3 边界矩阵末尾、§4.1 本地脚本调用末尾 |
| **作用** | 提供"什么时候用什么"的决策矩阵和可复制命令 |
| **验证方式** | `grep 'download-article' TASK-TOOLS-INDEX.md` 应命中多处 |
| **迁移方式** | 直接追加 |


### 4. 修改 `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` |
| **变更类型** | `追加` |
| **新增内容** | 新增 **Stage S6.5: Chrome / 浏览器 Session 检测**（含默认检测 / --output / --user-data-dir / --domain-patterns 4 组命令） |
| **插入位置** | Stage S6 与 Stage S7 之间 |
| **作用** | 命令速查真源，复制粘贴即用 |
| **验证方式** | `grep 'Stage S6.5' EXEC-CHEATSHEET.md` 应命中 |
| **迁移方式** | 直接追加 |


### 5. 修改 `references/tasks/deploy-git-isolated/scripts/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/README.md` |
| **变更类型** | `追加` |
| **新增内容** | 各层导航表新增 🌐 标识的 3 个浏览器工具入口（chrome-session / download-article / screenshot-verifier） |
| **插入位置** | `py-tools/` 行之后 |
| **作用** | 目录级导航，一眼定位浏览器相关工具 |
| **验证方式** | `grep '🌐' scripts/README.md` 应命中 |
| **迁移方式** | 直接追加 |


### 6. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/README.md` |
| **变更类型** | `追加` + `修改` |
| **新增/修改内容** | ① 独立工具表更新 `download-article.py` 描述（含 🌐 标识）；② 新增 **🌐 浏览器 / Chrome / Session 工具聚合** 醒目标识章节（4 个脚本 + 4 个底层插件支撑说明） |
| **插入位置** | 独立工具表 `download-article.py` 行、新增章节在"文章下载"节之前 |
| **作用** | 解决"找不着"问题——将散落在 py-plugins/ 和 py-tools/ 的浏览器工具聚合到一处 |
| **验证方式** | `grep '🌐 浏览器' py-tools/README.md` 应命中 |
| **迁移方式** | 直接追加/替换 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 不涉及文件复制、缓存迁移等无法被 git 追踪的操作。


## 三、环境变量速查

无新增环境变量。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（6 个文档文件） | `run-lint.py` | frontmatter + encoding + link | `✅ 全部通过` |
| `.json`（ENTRY.json） | `run-lint.py` | JSON 语法 + encoding | `✅ 全部通过` |
| `.py`（download-article.py） | `run-lint.py` | Python 语法 + encoding | `✅ 全部通过` |

**执行命令**：
```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "<文件路径>"
```

> 所有修改文件均已通过 run-lint 三阶段闭环验证（0 违规）。


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 ENTRY.json 已登记 | `grep '"name": "download-article.py"' references/tasks/deploy-git-isolated/ENTRY.json` | 命中且 path 正确 |
| 2 | 确认 docstring 含版本号 | `head -5 references/tasks/deploy-git-isolated/scripts/py-tools/download-article.py` | 看到 `v1.0.0` |
| 3 | 确认 docstring 含示例 | `grep '命令行示例' references/tasks/deploy-git-isolated/scripts/py-tools/download-article.py` | 命中 |
| 4 | 确认 TASK-TOOLS-INDEX 已登记 | `grep 'download-article' references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` | 命中多处 |
| 5 | 确认 EXEC-CHEATSHEET 有 Stage S6.5 | `grep 'Stage S6.5' references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` | 命中 |
| 6 | 确认 py-tools README 有聚合章节 | `grep '🌐 浏览器' references/tasks/deploy-git-isolated/scripts/py-tools/README.md` | 命中 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 ENTRY.json 登记 | `edit` 删除 active_scripts 中 download-article.py / article_extractor.py / chrome_session.py / js_loader.py 4 个条目 |
| 恢复 docstring | `edit` 将 download-article.py 顶部 docstring 替换为原简短版本 |
| 移除文档追加内容 | `edit` 删除 TASK-TOOLS-INDEX.md / EXEC-CHEATSHEET.md / scripts/README.md / py-tools/README.md 中的本次追加段落 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-10-162824 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户下载头条文章时发现工具索引不完整、docstring 缺失 |
| **下次修订条件** | 新增浏览器/Chrome/文章下载相关工具时，需同步更新本批文档 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
