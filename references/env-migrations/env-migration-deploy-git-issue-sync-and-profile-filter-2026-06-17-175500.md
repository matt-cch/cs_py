---
title: deploy-git-isolated 扩展 — Issue 同步体系与 Profile 筛选机制
description: 记录 deploy-git-isolated task 从 "仅支持 Git 部署" 扩展到 "Issue 同步闭环 + Profile 插件筛选" 的完整环境变更。date: 2026-06-17
---

# env-migration-deploy-git-issue-sync-and-profile-filter-2026-06-17-175500

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | deploy-git-isolated 扩展 — Issue 同步体系与 Profile 筛选机制 |
| **日期** | 2026-06-17 |
| **文件名时间戳** | `2026-06-17-175500` |
| **触发原因** | 1) push 后 Issue 未自动反映变更历史，发现缺少 Issue 更新能力；2) 插件目录膨胀后全量加载造成冗余，需引入 Profile 筛选机制 |
| **影响范围** | deploy-git-isolated task 全部脚本、插件架构、文档体系 |
| **风险等级** | 低（task 自包含，不影响仓库其他目录） |

---

## 一、文本文件变更清单

### 1. 新增 `references/tasks/deploy-git-isolated/scripts/lib-plugins/github-api.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/lib-plugins/github-api.ps1` |
| **变更类型** | `新建` |
| **作用** | GitHub REST API 封装插件：Invoke-GitHubApi / New-GitHubIssue / Update-GitHubIssue / New-GitHubIssueComment / Get-GitHubIssueComments，自动处理 UTF-8 encoding |
| **依赖** | constants.ps1, env-config.ps1 |
| **验证方式** | 执行 `github-sync-issue.ps1 -Mode get-issue -IssueNumber 1` |
| **迁移方式** | 直接复制文件 + 在 `lib-sort-rules.json` 中登记 |

### 2. 新增 `references/tasks/deploy-git-isolated/scripts/github-sync-issue.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-sync-issue.ps1` |
| **变更类型** | `新建` |
| **作用** | Issue 同步统一入口：create / update / comment / list-comments / get-issue 五种模式，从 `.env` 读取 PAT，调用 github-api.ps1 |
| **验证方式** | 执行 `-Mode comment -IssueNumber 1 -Body "测试"` |
| **迁移方式** | 直接复制文件 |

### 3. 新增 `references/tasks/deploy-git-isolated/scripts/github-sync-issue-config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-sync-issue-config.json` |
| **变更类型** | `新建` |
| **作用** | 配置真源：Issue 模板、labels、API endpoint 映射、Profile 定义，高频变动内容独立于此文件 |
| **验证方式** | `ConvertFrom-Json` 解析无错误 |
| **迁移方式** | 直接复制文件 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/lib-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/lib-sort-rules.json` |
| **变更类型** | `修改` |
| **新增内容** | `profiles` 节：`_default`（向后兼容）、`deploy`（Git 部署，排除 github-api）、`issue-sync`（全功能）、`minimal`（最小集） |
| **插入位置** | `plugins` 数组之后 |
| **作用** | 为 github-lib.ps1 提供 Profile 筛选的配置真源 |
| **验证方式** | 执行 `. github-lib.ps1 -Profile "deploy"` 确认只加载 5 个插件 |
| **迁移方式** | 追加 profiles 节 |

### 5. 重写 `references/tasks/deploy-git-isolated/scripts/github-lib.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-lib.ps1` |
| **变更类型** | `重写` |
| **新增内容** | `Resolve-PluginFilter`（Profile/Include/Exclude 三层筛选）、`Add-Dependencies`（递归依赖自动补齐）、生效验证日志 |
| **作用** | 解决插件冗余加载问题，保持入口脚本稳定，通过 JSON 配置驱动行为变化 |
| **验证方式** | 四场景验证：issue-sync(6/6), deploy(5/6), _default(6/6), exclude-override(5/6) |
| **迁移方式** | 直接覆盖（向后兼容，无参数时等价于 _default） |

### 6. 修改 `references/tasks/deploy-git-isolated/scripts/github-sync-issue.ps1`（追加 Profile 参数）

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/github-sync-issue.ps1` |
| **变更类型** | `修改` |
| **修改内容** | 点源 `github-lib.ps1` 时传入 `-Profile "issue-sync"` |
| **作用** | 明确声明本脚本需要哪些插件，避免冗余加载 |
| **迁移方式** | `. $libPath` → `. $libPath -Profile "issue-sync"` |

### 7. 文档联动更新（7 份文件）

| 文件 | 变更内容 |
|------|---------|
| `ENTRY.json` | v0.7.0，新增 lib-sort-rules.json 登记，更新 github-lib role |
| `README.md` | 状态表新增 Profile 筛选机制，文件导航表新增 docs/ 子分类 |
| `TASK-TOOLS-INDEX.md` | 新增 Issue 同步节、Profile 用法速查、边界矩阵 |
| `SOP-CHEATSHEET.md` | 新增 Issue 同步命令、Profile 筛选命令 |
| `PLUGIN-ARCHITECTURE.md` | v1.1，新增 3.3 Profile 筛选层设计、依赖自动补齐说明 |
| `docs/patterns/profile-filter-pattern.md` | 新建：Profile 筛选模式沉淀 |
| `docs/patterns/manifest-plugin-pattern.md` | 新建：Manifest+Plugins 扩展模式沉淀 |
| `docs/harness/delivery-checklist.md` | 新建：四步交付流程检查清单 |
| `docs/README.md` | 新建：docs/ 子分类导航 |
| `docs/playbooks/github-publish-playbook.md` | 从 `docs/` 根级迁入 `docs/playbooks/` |

---

## 二、非文本操作（文件系统/缓存迁移）

本次 session **无**非文本操作。所有变更均为代码和文档文件。

---

## 三、环境变量速查

本次 session **无新增**环境变量。`.env` 中已有的 `GITHUB_PAT`、`GITHUB_USERNAME`、`GITHUB_REPO_URL` 是前置条件。

---

## 四、落盘验证（写入后必须执行）

### 4.1 代码文件验证

| 文件 | 验证工具 | 结果 |
|------|---------|------|
| `github-lib.ps1` | `[PSParser]::Tokenize` | ✅ 语法通过 |
| `github-sync-issue.ps1` | `[PSParser]::Tokenize` | ✅ 语法通过 |
| `github-api.ps1` | `[PSParser]::Tokenize` | ✅ 语法通过（修复 BOM 后） |
| `lib-sort-rules.json` | `ConvertFrom-Json` | ✅ 解析通过 |
| `github-sync-issue-config.json` | `ConvertFrom-Json` | ✅ 解析通过 |

### 4.2 编码验证

| 文件 | 验证工具 | 标准 | 结果 |
|------|---------|------|------|
| `github-api.ps1` | `check-file-encoding.ps1` | UTF-8 BOM | ✅ BOM 头 `EF BB BF` |
| `github-lib.ps1` | `check-file-encoding.ps1` | UTF-8 BOM | ✅ BOM 头 `EF BB BF` |
| `github-sync-issue.ps1` | `check-file-encoding.ps1` | UTF-8 BOM | ✅ BOM 头 `EF BB BF` |

---

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | Profile 筛选生效（deploy） | `. github-lib.ps1 -Profile "deploy"` | 加载 5 个插件，不含 github-api |
| 2 | Profile 筛选生效（issue-sync） | `. github-lib.ps1 -Profile "issue-sync"` | 加载全部 6 个插件 |
| 3 | 向后兼容 | `. github-lib.ps1`（无参数） | 加载全部 6 个插件（等价 _default） |
| 4 | Issue 同步（get-issue） | `github-sync-issue.ps1 -Mode get-issue -IssueNumber 1` | 输出 Issue 标题、状态、URL |
| 5 | Issue 同步（comment） | `github-sync-issue.ps1 -Mode comment -IssueNumber 1 -Body "测试"` | 评论追加成功，返回 Comment ID |
| 6 | 依赖自动补齐 | `. github-lib.ps1 -Include @("env-config")` | 自动拉入 constants（env-config 的依赖） |

---

## 六、回滚方案

| 回滚步骤 | 操作 |
|---------|------|
| 移除新增文件 | 删除 `github-sync-issue.ps1`、`github-api.ps1`、`github-sync-issue-config.json` |
| 恢复旧版 github-lib | 回退到无 Profile 参数的旧版 `github-lib.ps1` |
| 恢复旧版 lib-sort-rules | 回退到无 `profiles` 节的旧版 `lib-sort-rules.json` |
| 移除新增文档 | 删除 `docs/patterns/`、`docs/harness/`、`docs/playbooks/` 下新增文件 |
| 恢复 README 导航 | 从 git 历史恢复 `README.md`、`TASK-TOOLS-INDEX.md` 等 |

---

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-17-175500 |
| **更新人** | Agent Session |
| **变更触发** | 用户 push 后 Issue 未更新；用户提出插件冗余加载问题 |
| **下次修订条件** | 新增 profile 类型、新增插件需登记到 profile、筛选逻辑变更 |
| **跨环境迁移参考** | 直接复制新增文件 + 按「验证清单」逐条执行 |

---

*文档生成时间：2026-06-17*  
*模板版本：v2*  
*对应 commit：`4a39e37` 及之前系列*
