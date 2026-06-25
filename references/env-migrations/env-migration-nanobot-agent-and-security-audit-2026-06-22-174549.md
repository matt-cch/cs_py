---
title: env-migration — nanobot Agent 底层能力 + 安全审计工具体系 + 命名规范固化
description: deploy-git-isolated task 引入自研 nanobot Agent 插件体系、安全审计工具、命名规范与产出文件落盘规则，记录全部新增文件与规范变更。
date: 2026-06-22
meta: {}
---

# env-migration-nanobot-agent-and-security-audit-2026-06-22-174549

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | deploy-git-isolated 引入自研 nanobot Agent 底层能力 + 安全审计工具体系 + 命名规范固化 |
| **日期** | 2026-06-22 |
| **文件名时间戳** | `2026-06-22-174549` |
| **触发原因** | 1. Issue comment 需要 AI 生成的中文语义摘要（结构层已自动化，语义层需 Agent）<br>2. 部署前需要系统化安全审计防止敏感内容泄露<br>3. tools/plugins 同名造成维护混淆，需固化命名规范 |
| **影响范围** | deploy-git-isolated task 的 scripts/py-plugins/、scripts/py-tools/、schema/、task-canonical-baseline.md |
| **风险等级** | 中（新增插件改变 py_lib 加载拓扑；命名规范变更影响未来文件创建） |

## 一、文本文件变更清单

### 1.1 新增 `scripts/py-plugins/provider_config.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/provider_config.py` |
| **变更类型** | 新增 |
| **作用** | Provider 配置真源：统一从 OpenCode config.json + .env + 环境变量读取 LLM 配置，支持 `source="auto"`/`"env"`/`"config_json"`/`"merge"` 四种策略 |
| **依赖** | 无（纯配置读取，不依赖其它插件） |
| **验证方式** | `python -c "import provider_config; print(provider_config.get_provider(source='config_json'))"` 应返回含 api_key/model/base_url 的 dict |
| **迁移方式** | 新增文件，直接复制 |

### 1.2 修改 `scripts/py-plugins/llm_client.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/llm_client.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 1. `get_config()` 改为统一调用 `provider_config.get_provider()`<br>2. `chat()` 新增 `provider_cfg` 参数，支持显式传入 provider 配置<br>3. payload 新增 `thinking` 参数传递（Moonshot kimi-k2.6 需要）<br>4. `temperature` 优先级：显式参数 > provider_cfg > None（不传） |
| **插入位置** | 替换原 `get_config()` 实现；在 `chat()` payload 构造处新增 thinking 传递 |
| **作用** | 统一配置来源，支持 config.json 分支调试，修复 Moonshot thinking 模式 400 错误 |
| **验证方式** | `run-lint.py --files llm_client.py` 通过；`generate-ai-summary.py` 成功生成摘要 |
| **迁移方式** | 直接覆盖（已保留 .env 读取作为 fallback） |

### 1.3 修改 `scripts/py-plugins/agent_core.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/agent_core.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | `AgentCore.__init__()` 新增 `provider_cfg: Optional[Dict]` 参数；`_call_llm()` 将 `provider_cfg` 透传给 `llm_client.chat()` |
| **作用** | Agent 可显式接收 config.json 来源的 provider 配置，确保 temperature=1.0 等参数正确传递 |
| **验证方式** | `run-lint.py` 通过；`generate-ai-summary.py` 调用成功 |
| **迁移方式** | 直接覆盖 |

### 1.4 修改 `scripts/py-tools/generate-ai-summary.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 1. 显式调用 `registry.provider_config.get_provider(source="config_json")`<br>2. 构造 `AgentCore` 时传入 `provider_cfg=provider_cfg`<br>3. `temperature=None`（使用 provider_cfg 中的值） |
| **作用** | 确保命中 config.json 分支，修复 Moonshot thinking 模式 temperature 冲突 |
| **验证方式** | 直接执行：`python generate-ai-summary.py --devroot ...` 成功生成中文摘要 |
| **迁移方式** | 直接覆盖 |

### 1.5 修改 `scripts/py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 1. 新增 `_generate_ai_summary()` 函数（调用 generate-ai-summary.py）<br>2. `_generate_meta()` 中插入 AI 摘要生成步骤<br>3. meta 结构新增 `ai_summary` 字段<br>4. 修复 `_generate_ai_summary()` 缺少 `import json`<br>5. 支持 Agent 异常 fallback（默认全自动模式） |
| **作用** | Step 5 后自动生成 AI 语义摘要并注入 Issue comment meta |
| **验证方式** | 执行完整 workflow，确认 `[Mode] 🧠 AI 语义层就绪` 输出 |
| **迁移方式** | 直接覆盖 |

### 1.6 修改 `scripts/py-steps/step-09-github-sync-issue.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-09-github-sync-issue.py` |
| **变更类型** | 修改 |
| **新增/修改内容** | 评论内容构造中新增 "AI 语义摘要" 章节，读取 `meta_data.get("ai_summary", "")` |
| **作用** | Issue comment 渲染 AI 生成的中文语义摘要 |
| **验证方式** | 执行 workflow Step 9，确认评论包含 "### AI 语义摘要" |
| **迁移方式** | 直接覆盖 |

### 1.7 新增 `scripts/py-plugins/security_audit.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/security_audit.py` |
| **变更类型** | 新增 |
| **作用** | 安全审计底层插件：提供 pattern_scan、git_tracking、报告聚合能力 |
| **依赖** | 无 |
| **验证方式** | `run-lint.py` 通过；被 workflow-security-audit.py 调用成功 |
| **迁移方式** | 新增文件，直接复制 |

### 1.8 新增 `scripts/py-tools/workflow-security-audit.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-security-audit.py` |
| **变更类型** | 新增 |
| **作用** | 安全审计 Workflow 入口：组装 security_audit 插件，输出人类可读报告 + JSON 报告 |
| **验证方式** | `python workflow-security-audit.py --devroot ...` 输出 pass + 报告落盘 `venv/tmp/` |
| **迁移方式** | 新增文件，直接复制 |

### 1.9 新增 `schema/json/security-audit-schema.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/json/security-audit-schema.json` |
| **变更类型** | 新增 |
| **作用** | 安全审计报告数据结构契约：AuditReport / PhaseResult / Finding / SensitivePattern |
| **验证方式** | `run-lint.py` 通过（JSON 语法） |
| **迁移方式** | 新增文件，直接复制 |

### 1.10 新增 `schema/docs/security-audit-spec.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/docs/security-audit-spec.md` |
| **变更类型** | 新增 |
| **作用** | 安全审计规范：五 Phase 流程、敏感模式定义、严重等级、误报排除规则、Git 追踪禁止模式 |
| **验证方式** | `run-lint.py` 通过（md_lint） |
| **迁移方式** | 新增文件，直接复制 |

### 1.11 修改 `scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 修改 |
| **新增/修改内容** | 1. 注册 `provider_config` 插件（tags: core, llm）<br>2. 注册 `security_audit` 插件（tags: core, validation）<br>3. 新增 `validation` profile |
| **作用** | 让 py_lib 能正确加载新插件 |
| **验证方式** | `run-lint.py` 通过；`load_plugins(profile="validation")` 成功加载 security_audit |
| **迁移方式** | 编辑追加 |

### 1.12 修改 `task-canonical-baseline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/task-canonical-baseline.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增第 8.4.7 节（工具命名规范：workflow-/atomic- 前缀，Phase/Atomic/Workflow 边界）和第 8.4.8 节（产出文件默认落盘到 venv/tmp/） |
| **作用** | 固化命名契约，防止 tools/plugins 同名混淆；规范产出文件位置避免被 git 追踪 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 编辑追加 |

### 1.13 修改 `TASK-TOOLS-INDEX.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 新增 1.4 安全审计章节，登记 workflow-security-audit.py + security_audit.py；更新版本号到 1.2 |
| **作用** | 导航更新 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 编辑追加 |

### 1.14 修改 `schema/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/schema/README.md` |
| **变更类型** | 修改 |
| **新增/修改内容** | 文件清单中追加 security-audit-spec.md 和 security-audit-schema.json |
| **作用** | 导航更新 |
| **验证方式** | `run-lint.py` 通过 |
| **迁移方式** | 编辑追加 |

### 1.15 新增研究文档与源码快照

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/research/cli-agent-integration-research.md`<br>`references/tasks/deploy-git-isolated/docs/research/nanobot-minimal-agent-research.md`<br>`references/tasks/deploy-git-isolated/docs/src/opencode_agent_go.go`<br>`references/tasks/deploy-git-isolated/docs/src/aider_base_coder_methods_extracted.txt`<br>`references/tasks/deploy-git-isolated/docs/src/subzeroclaw.c` |
| **变更类型** | 新增 |
| **作用** | CLI Agent 集成深度研究文档与源码快照（OpenCode agent.go、Aider base_coder、SubZeroClaw） |
| **验证方式** | `run-lint.py` 通过（markdown + python lint） |
| **迁移方式** | 新增文件，直接复制 |

## 二、非文本操作

无。本次 session 全部为代码/文档新增与修改，无文件系统迁移或缓存操作。

## 三、环境变量速查

无变更。本次 session 未修改 `.vscode/settings.json` 或 `.env`。新增工具读取的变量与既有 `.env` 一致：
- `MOONSHOT_API_KEY` / `CORECODER_API_KEY`（provider_config.py 消费）
- `GITHUB_PAT` / `GITHUB_REPO_URL`（step-09 消费，已有）

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py` → `md_lint` | frontmatter 合规性 | title/description/date/meta 齐全 |
| `.py`（全部新增/修改） | `run-lint.py` → `lint_python` | Python 语法 | 全部通过 |
| `.json`（sort-rules + schema） | `run-lint.py` → `lint_json` | JSON 语法 | 全部通过 |

**执行命令**：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "<全部变更文件列表>"
```

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 加载 validation profile | `python -c "from py_lib import load_plugins; r=load_plugins(devroot='...', profile='validation'); print(r.security_audit)"` | 不报错，打印模块对象 |
| 2 | 运行安全审计 | `python workflow-security-audit.py --devroot "..."` | 输出 `总体结论: PASS`，报告落盘 `venv/tmp/` |
| 3 | 运行 AI 摘要生成 | `python generate-ai-summary.py --devroot "..."` | 输出中文语义摘要，落盘 `venv/tmp/ai-summary-*.json` |
| 4 | 运行完整 deploy workflow | `python workflow-deploy-full.py --devroot "..." --step all` | Step 4-9 全部通过，Issue comment 含 AI 语义摘要 |
| 5 | 检查 git 追踪状态 | `git ls-files \| grep -E '\.env$\|config\.json$\|.*-key\.txt$'` | 无输出（敏感文件未被追踪） |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 Agent 插件 | 从 `py-sort-rules.json` 中删除 `provider_config`、`security_audit` 条目 |
| 恢复 llm_client | 回滚到依赖 `env_config` 的版本（保留 .env 读取逻辑） |
| 移除安全审计工具 | 删除 `py-plugins/security_audit.py` + `py-tools/workflow-security-audit.py` + schema 文件 |
| 恢复命名规范 | 从 `task-canonical-baseline.md` 中删除 8.4.7/8.4.8 节 |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-22-174549 |
| **更新人** | Human + Agent Session |
| **变更触发** | Issue comment AI 语义摘要需求 + 部署前安全审计需求 + 命名规范澄清 |
| **下次修订条件** | 1. 新增 Atomic 脚本需确认是否符合 8.4.7 命名规范<br>2. 新增产出文件需确认是否默认落盘 `venv/tmp/`<br>3. 安全审计模式扩展（新增检测规则） |
| **跨环境迁移参考** | 直接复制新增文件 + 编辑 `py-sort-rules.json` + 按「验证清单」逐条执行 |

***
*文档生成时间：2026-06-22*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
