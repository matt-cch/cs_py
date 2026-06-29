---
title: 安全审计规范（Security Audit Spec）
description: 部署前敏感内容安全巡检的标准流程、检测规则、严重等级定义与报告格式。供 security_audit 插件与 security-audit CLI 遵循。
date: 2026-06-22
meta:
  version: 1.0.0
  schema: schema/json/security-audit-schema.json
---

# 安全审计规范（Security Audit Spec）

> **适用范围**：deploy-git-isolated task 全部推送文件（git tracked），在 commit/push 前或定期执行。
> **机器真源**：`schema/json/security-audit-schema.json`
> **插件实现**：`scripts/py-plugins/security_audit.py`
> **CLI 入口**：`scripts/py-tools/security-audit.py`

## 1. 审计目标

防止以下敏感内容被意外提交到 GitHub：

| 类别 | 示例 | 风险 |
|------|------|------|
| API Key | `sk-m9fC...`, `ghp_xxxxxxxx...` | 密钥泄露，账户被盗 |
| 环境变量值 | `.env` 中 `MOONSHOT_API_KEY=sk-...` | 配置泄露 |
| 配置文件密钥 | `config.json` 中 `"apiKey": "sk-..."` | 凭证硬编码 |
| 密钥文件 | `*-key.txt`, `*.pem` | 私钥泄露 |
| GitHub PAT | `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | 仓库被篡改 |

## 2. 审计流程（五 Phase）

```
Phase 1: 敏感模式扫描（pattern_scan）
  └─ 对全部 tracked 文件执行正则匹配
  
Phase 2: 高关注文件人工确认（high_priority_files）
  └─ 读取 provider_config.py / llm_client.py / step-09 等文件，确认无硬编码
  
Phase 3: 源码快照检查（source_snapshots）
  └─ 检查 docs/src/ 下的外部源码快照是否含密钥
  
Phase 4: Git 追踪状态验证（git_tracking）
  └─ 确认 .env / config.json / key.txt 未被 git 追踪
  
Phase 5: 汇总报告（summary）
  └─ 生成结构化报告，输出 pass / warn / fail
```

## 3. 敏感模式定义（SensitivePattern）

### 3.1 默认检测模式

| name | regex | severity | 说明 |
|------|-------|----------|------|
| `api_key_moonshot` | `sk-[a-zA-Z0-9]{20,}` | critical | Moonshot API Key |
| `github_pat_classic` | `ghp_[a-zA-Z0-9]{36}` | critical | GitHub PAT (classic) |
| `github_pat_fine_grained` | `ghp_[a-zA-Z0-9]{68}` | critical | GitHub fine-grained PAT |
| `github_oauth_token` | `gho_[a-zA-Z0-9]{36}` | critical | GitHub OAuth token |
| `github_user_token` | `ghu_[a-zA-Z0-9]{36}` | critical | GitHub user-to-server token |
| `github_server_token` | `ghs_[a-zA-Z0-9]{36}` | critical | GitHub server-to-server token |
| `github_refresh_token` | `ghr_[a-zA-Z0-9]{36}` | critical | GitHub refresh token |
| `env_api_key_value` | `(?i)(MOONSHOT_API_KEY\|CORECODER_API_KEY\|OPENAI_API_KEY)\s*=\s*["']?sk-` | high | .env 中 API key 赋值 |
| `env_github_pat_value` | `(?i)GITHUB_PAT\s*=\s*["']?ghp_` | high | .env 中 PAT 赋值 |
| `config_hardcoded_key` | `"apiKey"\s*:\s*"[^"]{10,}"` | high | config.json 中硬编码 key |
| `authorization_bearer_with_value` | `Authorization.*Bearer\s+[a-zA-Z0-9_-]{20,}` | high | HTTP header 中 bearer token |
| `basic_auth_in_url` | `https?://[^:]+:[^@]+@` | high | URL 中嵌入用户名密码 |
| `private_key_pem` | `-----BEGIN (RSA \|EC \|DSA \|OPENSSH) PRIVATE KEY-----` | critical | PEM 私钥 |
| `aws_access_key` | `AKIA[0-9A-Z]{16}` | high | AWS Access Key ID |
| `aws_secret_key` | `(?i)aws(.{0,20})?(secret)?(.{0,20})?['"][0-9a-zA-Z/+]{40}['"]` | high | AWS Secret Key |

### 3.2 误报排除规则

以下匹配**不视为泄露**（人工复核时标记为 `false_positive`）：

| 场景 | 示例 | 排除理由 |
|------|------|---------|
| 环境变量名引用 | `os.environ.get("MOONSHOT_API_KEY", "")` | 只有变量名，无值 |
| 占位符检查 | `if pat == "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"` | 显式占位符，非真实密钥 |
| 模板字符串 | `f"Bearer {api_key}"` | 模板，运行时注入 |
| 文件路径引用 | `{file:./moonshot-key.txt}` | 路径引用，非密钥内容 |
| 文档示例 | 代码注释中的示例格式 | 明示为示例 |
| 变量/字段名 | `api_key`, `secret`, `token` 作为变量名 | 仅标识符 |

## 4. 严重等级（Severity）

| 等级 | 定义 | 处理要求 |
|------|------|---------|
| **critical** | 高度确信的真实密钥泄露 | **立即阻止 push**，必须修复后才能继续 |
| **high** | 疑似密钥或凭证赋值 | 必须人工复核，确认后才能 push |
| **medium** | 可疑模式但可能是误报 | 建议复核 |
| **low** | 低风险模式（如路径引用） | 记录即可 |
| **info** | 仅用于审计追溯的信息 | 无强制要求 |

## 5. Git 追踪状态验证规则

以下文件/模式**绝对禁止**出现在 git tracked 文件中：

| 模式 | 说明 |
|------|------|
| `\.env$` | 环境变量文件 |
| `\.env\..*` | 环境变量变体 |
| `venv/\.opencode/config\.json` | OpenCode 配置（含 apiKey） |
| `venv/\.opencode/.*-key\.txt` | 密钥文件 |
| `.*-key\.txt$` | 通用密钥文件 |
| `.*-key\.pem$` | PEM 密钥文件 |
| `.*\.key$` | 私钥文件 |
| `.*\.p12$` | PKCS#12 证书 |
| `.*\.pfx$` | PFX 证书 |

验证方式：
```bash
git ls-files | grep -E '<pattern>'
```
任何匹配 → `fail`

## 6. 报告格式

审计报告遵循 `schema/json/security-audit-schema.json`，最小 viable 输出：

```json
{
  "version": "1.0.0",
  "audit_id": "audit-20260622-090000",
  "audited_at": "2026-06-22T09:00:00+00:00",
  "devroot": "D:\\pjt\\cursor\\cs_py",
  "commit_range": "HEAD~10..HEAD",
  "files_in_scope": ["..."],
  "phases": [
    {
      "phase_name": "pattern_scan",
      "status": "pass",
      "summary": "扫描 48 个文件，发现 0 个真实泄露",
      "files_audited": 48,
      "files_with_findings": 0,
      "total_findings": 0,
      "details": [],
      "elapsed_seconds": 2.5
    }
  ],
  "overall_status": "pass",
  "overall_summary": "所有检查项通过，无敏感内容泄露",
  "recommendations": [],
  "total_elapsed_seconds": 5.0
}
```

## 7. CLI 用法

```powershell
# 完整审计（默认 HEAD~10..HEAD）
python security-audit.py --devroot "D:\pjt\cursor\cs_py"

# 审计指定 commit 范围
python security-audit.py --devroot "D:\pjt\cursor\cs_py" --commit-range "HEAD~5..HEAD"

# 仅执行特定 phase
python security-audit.py --devroot "D:\pjt\cursor\cs_py" --mode patterns
python security-audit.py --devroot "D:\pjt\cursor\cs_py" --mode git-tracking

# 输出 JSON 报告到文件
python security-audit.py --devroot "D:\pjt\cursor\cs_py" --output "audit-report.json"
```

## 8. 与 workflow 的集成

建议在 `workflow-deploy-full.py` 的 **Step 5 (commit) 之前**插入安全审计步骤：

```python
# Step 4.5: 安全审计（阻止含敏感内容的 commit）
audit_ok = run_security_audit(devroot, commit_range="HEAD~1..HEAD")
if not audit_ok:
    print("[FAIL] 安全审计未通过，终止部署")
    sys.exit(1)
```

## 9. 修订历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-22 | 初始版本，定义五 Phase 审计流程、敏感模式、严重等级、报告格式 |

*规范文档版本: 1.0.0*
*关联 schema: schema/json/security-audit-schema.json*