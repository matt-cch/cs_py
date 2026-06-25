---
title: ima OpenAPI 深度探索与客户端工具链建设
description: 完成 ima OpenAPI（wiki + note）全部可用接口探测，建设完整客户端、知识库速查表、笔记同步工具及 copilot 凭证捕获脚本。
date: 2026-06-12
---

# ima OpenAPI 深度探索与客户端工具链建设

> **文档性质**：环境迁移指南。记录本次 session 对开发环境产生的变更（新增脚本、文档、配置），供新环境复现。  
> **受众**：Human + Agent。


## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | ima OpenAPI 深度探索与客户端工具链建设 |
| **日期** | 2026-06-12（frontmatter） |
| **文件名时间戳** | `2026-06-12-161828` |
| **触发原因** | 打通 Agent 与 ima copilot 的自动通讯协作；深度探索 ima OpenAPI（wiki + note）接口能力 |
| **影响范围** | `debug/ima-api/` 目录下新增 6 个文件；`.env` 追加 ima 鉴权密钥；`venv/data-chrome` 保存 ima 登录态 |
| **风险等级** | 低（仅新增调试脚本与文档，不涉及业务代码或生产环境） |


## 一、文本文件变更清单

### 1. 新建 `debug/ima-api/ima_api_client.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/ima-api/ima_api_client.py` |
| **变更类型** | `新建` |
| **作用** | 完整 IMA OpenAPI 客户端（wiki + note），封装全部已验证接口（15 个 wiki + 9 个 note），含 CLI 入口 |
| **验证方式** | `python debug/ima-api/ima_api_client.py --help` 应输出 CLI 帮助 |
| **迁移方式** | 可直接复制 |

### 2. 新建 `debug/ima-api/kb_index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/ima-api/kb_index.json` |
| **变更类型** | `新建` |
| **作用** | 14 个知识库的独立速查索引（id、name、description、type、space_id），与代码解耦，可独立更新 |
| **验证方式** | `python -c "import json; print(len(json.load(open('debug/ima-api/kb_index.json'))['knowledge_bases']))"` 应输出 `14` |
| **迁移方式** | 可直接复制 |

### 3. 新建 `debug/ima-api/KB_CHEATSHEET.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/ima-api/KB_CHEATSHEET.md` |
| **变更类型** | `新建` |
| **作用** | 人类可读的知识库速查表（14 个知识库名称 + ID + 类型），便于人工查知识库 ID |
| **验证方式** | 文件存在且内容非空 |
| **迁移方式** | 可直接复制 |

### 4. 新建 `debug/ima-api/RESEARCH-REPORT.md`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/ima-api/RESEARCH-REPORT.md` |
| **变更类型** | `新建` |
| **作用** | 7900+ 字深度调研报告，记录 ima OpenAPI 全部接口的探测过程、参数 schema、返回值、踩坑记录 |
| **验证方式** | 文件存在且行数 > 200 |
| **迁移方式** | 可直接复制 |

### 5. 新建 `debug/ima-api/sync_note_to_md.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/ima-api/sync_note_to_md.py` |
| **变更类型** | `新建` |
| **作用** | 笔记同步工具：通过 `get_doc_content` 下载笔记完整 Markdown，格式化为本地 `.md` 文件 |
| **验证方式** | `python debug/ima-api/sync_note_to_md.py --help` 应输出帮助 |
| **迁移方式** | 可直接复制 |

### 6. 新建 `debug/ima-api/ima_copilot_credential_harvester.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/ima-api/ima_copilot_credential_harvester.py` |
| **变更类型** | `新建` |
| **作用** | 凭证捕获脚本：Playwright + 持久化 Chrome 自动输入 "ping"、拦截 `/cgi-bin/assistant/qa` 请求、提取 `x-ima-cookie` + `x-ima-bkn`、保存到 `.env`、验证复用 |
| **验证方式** | 运行后检查 `.env` 中是否新增 `IMA_COPILOT_COOKIE` 和 `IMA_COPILOT_BKN` |
| **迁移方式** | 可直接复制 |

### 7. 修改 `.env`

| 属性 | 值 |
|------|-----|
| **路径** | `.env` |
| **变更类型** | `追加` |
| **新增内容** | `IMA_OPENAPI_CLIENTID=<值>`、`IMA_OPENAPI_APIKEY=<值>`（wiki/note 鉴权）；运行凭证捕获脚本后可能追加 `IMA_COPILOT_COOKIE`、`IMA_COPILOT_BKN` |
| **插入位置** | 文件末尾 |
| **作用** | ima OpenAPI 与 copilot 的鉴权密钥 |
| **验证方式** | 检查 `.env` 中上述变量是否存在 |
| **迁移方式** | 需手动从原环境复制密钥值（**禁止**将密钥写入 git） |

> **重要**：`.env` 只存放密钥，不存放笔记链接或参考信息。


## 二、非文本操作（文件系统/缓存迁移）

本次 session 是否涉及文件复制、缓存迁移、目录创建等**无法被 git 追踪**的操作？

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 目录创建 | — | `debug/ima-api/` | 新建 ima API 探索专用目录 |
| Chrome 登录态保存 | — | `venv/data-chrome/Default/Local Storage/leveldb/` | 用户微信扫码登录 ima 后，Chrome Profile 已持久化登录态 |

> **复现说明**：新环境中需在 Chrome 中手动登录 ima（微信扫码），或从原环境复制 `venv/data-chrome` 目录。


## 三、环境变量速查

迁移到新环境后，打开 `.env` 核对以下变量是否齐全：

```
IMA_OPENAPI_CLIENTID=<wiki/note OpenAPI 的 clientid>
IMA_OPENAPI_APIKEY=<wiki/note OpenAPI 的 apikey>
IMA_COPILOT_COOKIE=<运行凭证捕获脚本后自动填充>
IMA_COPILOT_BKN=<运行凭证捕获脚本后自动填充>
```

> **注意**：ima copilot 与 wiki/note OpenAPI 是**两套独立鉴权体系**。wiki/note 使用 `ima-openapi-clientid` + `ima-openapi-apikey`（长期稳定）；copilot 使用 `x-ima-cookie` + `x-ima-bkn`（浏览器 Cookie，有效期 29~59 天）。


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认文件已复制 | `Get-ChildItem "debug/ima-api"` | 存在 6 个文件（见「一、文本文件变更清单」） |
| 2 | 确认密钥存在 | `Get-Content .env` | 包含 `IMA_OPENAPI_CLIENTID` 和 `IMA_OPENAPI_APIKEY` |
| 3 | 确认客户端可运行 | `python debug/ima-api/ima_api_client.py --help` | 输出 CLI 帮助 |
| 4 | 确认知识库索引有效 | `python -c "import json; d=json.load(open('debug/ima-api/kb_index.json')); print(len(d['knowledge_bases']))"` | 输出 `14` |
| 5 | 确认笔记同步工具可运行 | `python debug/ima-api/sync_note_to_md.py --help` | 输出帮助 |
| 6 | 确认 Chrome 登录态（如需 copilot） | 启动 Chrome 访问 ima 空间 | 无需重新扫码即可进入 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新增脚本 | `Remove-Item -Recurse "debug/ima-api"` |
| 移除 ima 密钥 | 从 `.env` 中删除 `IMA_OPENAPI_CLIENTID`、`IMA_OPENAPI_APIKEY`、`IMA_COPILOT_COOKIE`、`IMA_COPILOT_BKN` 行 |
| 清除 Chrome 登录态（可选） | `Remove-Item -Recurse "venv/data-chrome/Default/Local Storage/leveldb"` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-12-161828 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求打通 Agent ↔ ima copilot 自动通讯；深度探索 ima OpenAPI |
| **下次修订条件** | 新增 ima OpenAPI 接口、知识库数量变更、凭证捕获脚本改进 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-12-161828*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
