---
title: env-migration — Win+Cursor+OpenCode Agent Chat TLS 证书校验失败排查
description: 记录 Cursor Agent Chat 集成 OpenCode 时出现 unknown certificate verification error 的根因分析、诊断步骤与推荐环境变量修复方案。
date: 2026-06-20
---

# env-migration — Win+Cursor+OpenCode Agent Chat TLS 证书校验失败排查

> **文档性质**：环境迁移 / 故障排查指南。本次 session 以分析为主，未修改仓库内业务代码；重点沉淀 TLS 证书校验失败的可复现诊断路径与修复 env 配置。  
> **受众**：Human + Agent。在新环境或同类故障场景下，可按本文档逐步定位并修复。  
> **关联文档**：[`docs/tooling/opencode/cursor-opencode-setup-and-logs.md`](../../docs/tooling/opencode/cursor-opencode-setup-and-logs.md)


## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Win + Cursor + OpenCode 模式下 Agent Chat 任意 prompt 报 `unknown certificate verification error` |
| **日期** | 2026-06-20 |
| **文件名时间戳** | `2026-06-20-083825` |
| **触发原因** | Agent Chat 窗口对任何 prompt 均失败，重启 Agent 无效；需沉淀 TLS 根因与修复路径 |
| **影响范围** | OpenCode HTTPS 出站（LLM API / models.dev / 插件）、Cursor Agent Chat 与本地 OpenCode server 通信 |
| **风险等级** | 中（涉及 TLS 信任链；临时 bypass 方案有安全风险） |


## 一、问题摘要

### 1.1 现象

- **环境**：Windows + Cursor + OpenCode（项目配置见 `venv/.opencode/config.json`）
- **表现**：Cursor **Agent Chat** 窗口对任意 prompt 返回 `unknown certificate verification error`
- **特点**：重启 Agent / 重启 Cursor **不能**恢复；切换多个 provider/model 同样失败

### 1.2 错误本质

OpenCode（底层 Node/Bun 运行时）在 HTTPS 请求时 **TLS 证书链校验失败**。常见失败 URL：

| 目标 | 场景 |
|------|------|
| `https://api.moonshot.cn/v1` | 调用 Kimi（当前默认 `moonshot/kimi-k2.6`） |
| `https://api.minimaxi.com/v1` | 调用 MiniMax |
| `https://models.dev` | 启动时拉模型列表（GitHub opencode #12408） |
| `https://opencode.ai/...` | 配置 schema、插件等 |
| `127.0.0.1` 本地服务 | Cursor Agent Chat ↔ OpenCode 本地 server |

任意 prompt 均失败 → 问题在 **网络/TLS 环境层**，而非单条 prompt 或 session 状态。


## 二、根因分析（按概率排序）

### 2.1 代理 / 抓包 HTTPS 中间人（最高频）

- 公司网：Zscaler、深信服等 SSL inspection
- 个人环境：Clash / Surge / V2Ray **TUN + fake-ip + MITM**
- 杀毒软件：HTTPS 扫描

代理替换证书后，**Node.js 默认不完全信任 Windows 系统证书库**，触发 `unknown certificate verification error`。  
OpenCode 上游 issue 参考：[anomalyco/opencode#8601](https://github.com/anomalyco/opencode/issues/8601)

### 2.2 系统时间不准

证书「尚未生效」或「已过期」也会触发同类错误（issue #8601 有 Windows 实测案例）。

### 2.3 环境变量只注入终端，未注入 Agent Chat

`.vscode/settings.json` 的 `terminal.integrated.env.windows` **仅影响集成终端**，Cursor Agent Chat 调用的 OpenCode 进程**不一定继承**这些变量。

典型分裂现象：

| 终端 `opencode` | Agent Chat |
|-----------------|------------|
| 正常 | 报 certificate error |

说明扩展进程缺少 `OPENCODE_*` 或 CA 相关 env。

### 2.4 代理配置不完整

- 设置了 `HTTPS_PROXY`，但未设 `NO_PROXY=localhost,127.0.0.1`
- 本地 OpenCode server 被错误走代理 → 证书/路由异常

### 2.5 启动链失败（models.dev）

即使 LLM provider 可用，启动时访问 `models.dev` 失败也会导致 Chat 不可用（#12408）。


## 三、文本文件变更清单

> **本次 session 未修改仓库内配置文件**。以下为**推荐**变更（按需在新环境或故障修复时执行）。

### 1. 可选修改 `.vscode/settings.json`（终端 + 统一文档化）

| 属性 | 值 |
|------|-----|
| **路径** | `.vscode/settings.json` |
| **变更类型** | 追加（按需） |
| **推荐追加项** | 见「四、环境变量速查 → 3.2 终端注入扩展项」 |
| **作用** | 终端内 opencode 与文档化 CA/代理配置保持一致 |
| **验证方式** | 新开终端：`$env:NODE_EXTRA_CA_CERTS`、`$env:NO_PROXY` |
| **迁移方式** | 手动追加；`<devroot>` 按实际 workspace 替换 |

### 2. 可选修改 `venv/.opencode/config.json`（models.dev 相关 workaround）

| 属性 | 值 |
|------|-----|
| **路径** | `venv/.opencode/config.json` |
| **变更类型** | 修改（仅当日志指向 models.dev 且无法访问时） |
| **说明** | 尝试关闭 title-agent / small model 相关配置，避免启动循环访问 models.dev（#12408 用户反馈） |
| **验证方式** | 重启 OpenCode，日志不再出现 `Failed to fetch models.dev` |
| **迁移方式** | 手动调整；改前备份 config.json |


## 四、非文本操作（Windows 用户级环境变量）

本次推荐的**主修复路径**是设置 **Windows 用户级**环境变量（Agent Chat 进程可继承），而非仅终端注入。

### 4.1 推荐：导入代理/企业根证书（首选）

```powershell
# 将 <ca-path> 替换为实际 PEM 路径（公司 IT 或 Clash/Surge 导出）
[System.Environment]::SetEnvironmentVariable(
    "NODE_EXTRA_CA_CERTS",
    "C:\path\to\your-corporate-or-proxy-ca.pem",
    "User"
)
```

**完全退出 Cursor 后重新打开**，再在 Agent Chat 发 prompt 验证。

### 4.2 推荐：代理 + 本地 bypass

```powershell
[System.Environment]::SetEnvironmentVariable("HTTPS_PROXY", "http://127.0.0.1:7890", "User")
[System.Environment]::SetEnvironmentVariable("NO_PROXY", "localhost,127.0.0.1,::1", "User")
```

端口 `7890` 按实际代理修改。

### 4.3 推荐：OpenCode 配置路径（用户级，解决终端 OK / Chat 不 OK）

```powershell
$devroot = "D:\pjt\cursor\cs_py"   # 按实际 devroot 替换

[System.Environment]::SetEnvironmentVariable("OPENCODE_CONFIG", "$devroot\venv\.opencode\config.json", "User")
[System.Environment]::SetEnvironmentVariable("OPENCODE_CONFIG_DIR", "$devroot\venv\.opencode", "User")
[System.Environment]::SetEnvironmentVariable("XDG_DATA_HOME", "$devroot\venv\data-opencode", "User")
[System.Environment]::SetEnvironmentVariable("XDG_CACHE_HOME", "$devroot\venv\data-opencode\cache", "User")
```

PATH 用户级追加：`%devroot%\venv\opencode`（通过系统「环境变量」UI 或 `[Environment]::SetEnvironmentVariable` 合并现有 PATH）。

### 4.4 临时验证用（不安全，确认根因后应回滚）

```powershell
[System.Environment]::SetEnvironmentVariable("NODE_TLS_REJECT_UNAUTHORIZED", "0", "User")
```

**禁止**作为长期生产配置。确认是 TLS 问题后，改回 `1` 或删除该变量，并采用 4.1 的 CA 方案。


## 五、环境变量速查

### 5.1 当前项目终端注入（已有，见 `.vscode/settings.json`）

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

### 5.2 终端注入扩展项（TLS 修复，按需追加）

| 变量 | 示例值 | 作用 |
|------|--------|------|
| `NODE_EXTRA_CA_CERTS` | `C:\certs\proxy-root.pem` | 让 Node 信任代理/企业根 CA |
| `NO_PROXY` | `localhost,127.0.0.1,::1` | 本地 OpenCode server 不走代理 |
| `HTTPS_PROXY` | `http://127.0.0.1:7890` | 出站走本地代理（若需要） |

### 5.3 当前 OpenCode provider 摘要（`venv/.opencode/config.json`）

| 项 | 值 |
|----|-----|
| 默认 model | `moonshot/kimi-k2.6` |
| Moonshot baseURL | `https://api.moonshot.cn/v1` |
| MiniMax baseURL | `https://api.minimaxi.com/v1` |
| autoupdate | `false`（不能避免 models.dev 等启动 HTTPS 请求） |


## 六、诊断步骤（新环境 / 故障时执行）

| # | 步骤 | 命令 / 操作 | 期望 / 解读 |
|---|------|------------|-------------|
| 1 | 读 OpenCode 日志 | 打开 `venv\data-opencode\opencode\log\` 最新 `.log`，搜索 `certificate`、`models.dev` | 定位失败 URL |
| 2 | PowerShell 测 Moonshot TLS | `Invoke-WebRequest -Uri "https://api.moonshot.cn/v1/models" -Method Head -UseBasicParsing` | 失败 → 系统/代理/证书问题 |
| 3 | 测 models.dev | `Invoke-WebRequest -Uri "https://models.dev" -Method Head -UseBasicParsing` | 失败 → 启动链可能卡住 |
| 4 | 查系统时间与代理 | `Get-Date`；`netsh winhttp show proxy`；`echo $env:HTTPS_PROXY` | 时间正确；NO_PROXY 含 localhost |
| 5 | 对比终端 vs Chat | 终端跑 `opencode` 发 prompt vs Agent Chat | 分裂 → 用户级 env 未齐 |

### 6.1 快速决策树

```
任意 prompt → certificate error
    │
    ├─ 系统时间不对？ → 修正时间
    │
    ├─ 有公司代理 / Clash TUN / 杀毒 HTTPS 扫描？
    │       → 导出 CA → NODE_EXTRA_CA_CERTS（用户级）→ 重启 Cursor
    │
    ├─ 终端 opencode OK，Agent Chat 不 OK？
    │       → OPENCODE_* / NODE_EXTRA_CA_CERTS 设为用户级 env
    │
    ├─ 日志指向 models.dev？
    │       → 检查该域名 TLS；或 config 关闭 title/small model
    │
    └─ 仍不行 → 临时 NODE_TLS_REJECT_UNAUTHORIZED=0 验证 → 回退并修 CA
```


## 七、验证清单（修复后必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 用户级 CA 已设置 | `[Environment]::GetEnvironmentVariable("NODE_EXTRA_CA_CERTS","User")` | 输出 PEM 绝对路径 |
| 2 | NO_PROXY 含本地 | `[Environment]::GetEnvironmentVariable("NO_PROXY","User")` | 含 `localhost` 或 `127.0.0.1` |
| 3 | Moonshot TLS | `Invoke-WebRequest https://api.moonshot.cn/v1/models -Method Head -UseBasicParsing` | StatusCode 200 或 401（非证书错误） |
| 4 | Agent Chat | Cursor Agent Chat 发任意短 prompt | 无 certificate error |
| 5 | 日志无证书错误 | 最新 `venv\data-opencode\opencode\log\*.log` | 无 `UNKNOWN_CERTIFICATE_VERIFICATION_ERROR` |


## 八、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 移除临时 TLS bypass | 删除用户级 `NODE_TLS_REJECT_UNAUTHORIZED` |
| 移除 CA 配置 | 删除用户级 `NODE_EXTRA_CA_CERTS` |
| 移除代理 env | 删除用户级 `HTTPS_PROXY` / `NO_PROXY`（若仅为排查添加） |
| 恢复 config | 若改过 `config.json` 的 title/small model，从备份还原 |

回滚后**完全退出 Cursor** 再验证。


## 九、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-20-083825 |
| **更新人** | Human + Agent Session |
| **变更触发** | Agent Chat 全 prompt certificate error 排查对话 |
| **下次修订条件** | OpenCode 版本升级后 TLS 行为变化；项目切换 provider；确认并应用具体 CA 路径后补充实测路径 |
| **跨环境迁移参考** | 复制本文档 + 按「验证清单」执行；`<devroot>` 与 CA PEM 路径按目标机器替换 |
| **外部参考** | [opencode#8601](https://github.com/anomalyco/opencode/issues/8601)、[#12408](https://github.com/anomalyco/opencode/issues/12408)、[#21206](https://github.com/anomalyco/opencode/issues/21206) |


*文档生成时间：2026-06-20*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
