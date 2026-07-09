---
title: Polyrepo Workflow 改造落地（Pending 清单完结）
description: 接续 2026-07-08 的 Pending 清单，完成 atomic-deploy-preflight、generate-ai-summary、step-09-github-sync-issue、fetch_issue、workflow-git-deploy-full-poly 的 polyrepo 适配改造，以及 git-security.json 与 task-index 更新。
date: 2026-07-09
meta:
  version: 1.0.0
  author: opencode-agent
  tags: [polyrepo, deploy-git-isolated, workflow, manifest]
---

# env-migration-polyrepo-workflow-completion-2026-07-09-164950

> **文档性质**：环境级变更记录。接续 `env-migration-polyrepo-context-manifest-2026-07-08-173019.md` 的 Pending 清单，记录本次 session 全部落地内容。
> **受众**：Human + Agent。新环境复现时按「文本文件变更清单」逐条复制即可。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Polyrepo Workflow 改造落地（Pending 清单完结） |
| **日期** | 2026-07-09 |
| **文件名时间戳** | `2026-07-09-164950` |
| **触发原因** | 接续 07-08 Pending 清单，将 polyrepo 适配改造编码落地 |
| **影响范围** | deploy-git-isolated 脚本体系（py-tools/5 个、py-steps/1 个、py-plugins/1 个）、仓库根 git-security.json、jywl-lab git-security.json、verified-task-index.json |
| **风险等级** | 中（触及部署 workflow 核心链路，但采用向后兼容改造 + 新增文件，不影响既有单仓库场景） |

## 一、文本文件变更清单

### 1. 新建 `py-tools/atomic-deploy-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py` |
| **变更类型** | `新建` |
| **作用** | 部署前安全检查原子脚本。新增 `--target` 参数；`repo_url` 仅从 target 的 `git remote get-url origin` 读取（禁止 fallback 到 `.env`）；检测 `git-security.json` 与 `.gitattributes` 同级配对；支持 `security-level` 四级控制（strict/normal/loose/off） |
| **验证方式** | `python atomic-deploy-preflight.py --devroot <devroot> --target <target>` |
| **迁移方式** | 直接复制 |

### 2. 新建 `py-tools/atomic-polyrepo-context-manifest.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-polyrepo-context-manifest.py` |
| **变更类型** | `新建` |
| **作用** | Polyrepo Context Manifest 生成原子脚本。接受 `--devroot`/`--target`/`--output` 参数；调用 `PolyrepoContext.from_args()` 生成上下文并序列化到指定 `--output` 路径；workflow 通过该 manifest 向各 step 传递上下文 |
| **验证方式** | `python atomic-polyrepo-context-manifest.py --devroot <devroot> --target <target> --output venv/tmp/test-manifest.json` |
| **迁移方式** | 直接复制 |

### 3. 修改 `py-tools/generate-ai-summary.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/generate-ai-summary.py` |
| **变更类型** | `修改` |
| **修改内容** | 新增 `--target` 参数；`git diff` / `git status` / `git log` 等操作全部在 `--target` 目录执行；agent 插件体系（`py_lib`）仍从 `--devroot` 加载；修复 `capture_output=True` 导致实时输出丢失的问题，改为 `capture_output=False` + 日志落盘 |
| **验证方式** | `python generate-ai-summary.py --devroot <devroot> --target <target>` |
| **迁移方式** | 直接覆盖（向后兼容：省略 `--target` 时默认等于 `--devroot`） |

### 4. 修改 `py-steps/step-09-github-sync-issue.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-steps/step-09-github-sync-issue.py` |
| **变更类型** | `修改` |
| **修改内容** | 新增 `--target` 参数；`git add`/`commit`/`push` 等操作在 `--target` 执行；新增 `--repo-url` 参数覆盖（优先于 target 的 git remote）；Issue 同步流程复用 manifest 中的 repo_url |
| **验证方式** | `python step-09-github-sync-issue.py --devroot <devroot> --target <target>` |
| **迁移方式** | 直接覆盖（向后兼容） |

### 5. 修改 `py-tools/fetch_issue.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/fetch_issue.py` |
| **变更类型** | `修改` |
| **修改内容** | 新增 `--repo-url` 参数，允许调用方显式传入仓库 URL，不再强制依赖 `.env` 或 git remote |
| **验证方式** | `python fetch_issue.py --devroot <devroot> --repo-url "https://github.com/owner/repo"` |
| **迁移方式** | 直接覆盖（向后兼容） |

### 6. 修改 `py-tools/workflow-git-deploy-full-poly.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` |
| **变更类型** | `修改` |
| **修改内容** | **Step 0c**：调用 `atomic-polyrepo-context-manifest.py` 生成 manifest；**Step 7/9/10**：从 manifest 读取上下文，拆解为 `--target`/`--repo-url` 等参数传给子脚本；新增 `--step 0` 模式（仅执行 preflight + manifest audit，不执行 git add/commit/push）；`--message` 支持自定义 commit message，`--auto` 支持自动生成 message（调用 `generate-ai-summary.py`）；workflow 不直接 import 任何 py-plugins，全部通过 subprocess 调用 atomic 脚本 |
| **验证方式** | `python workflow-git-deploy-full-poly.py --devroot <devroot> --target <target> --step 0` |
| **迁移方式** | 直接覆盖 |

### 7. 修改 `git-security.json`（cs_py 根 + jywl-lab 根）

| 属性 | 值 |
|------|-----|
| **路径** | `D:\pjt\cursor\cs_py\git-security.json` 和 `D:\pjt\cursor\cs_py\jywl-lab\git-security.json` |
| **变更类型** | `修改` |
| **修改内容** | 新增 `"repo_url"` 字段，值为各仓库的 `git remote get-url origin`，用于 audit 时快速确认操作目标 |
| **验证方式** | `git -C <target> remote get-url origin` 与 `git-security.json` 中的 `repo_url` 一致 |
| **迁移方式** | 直接覆盖 |

### 8. 修改 `verified-task-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-task-index.json` |
| **变更类型** | `修改` |
| **修改内容** | 追加 atomic-deploy-preflight、atomic-polyrepo-context-manifest、workflow-git-deploy-full-poly 等新脚本的条目；更新 `last_updated` 时间戳 |
| **验证方式** | `python schema/tool/lint-json.py -v references/runtime/verified-task-index.json` |
| **迁移方式** | 直接覆盖 |

## 二、非文本操作

无。

## 三、环境变量速查

无需新增或修改环境变量。

## 四、落盘验证

| 文件 | 验证工具 | 结果 |
|------|---------|------|
| `atomic-deploy-preflight.py` | `run-lint.py` | ✅ 通过 |
| `atomic-polyrepo-context-manifest.py` | `run-lint.py` | ✅ 通过 |
| `generate-ai-summary.py` | `run-lint.py` | ✅ 通过 |
| `step-09-github-sync-issue.py` | `run-lint.py` | ✅ 通过 |
| `fetch_issue.py` | `run-lint.py` | ✅ 通过 |
| `workflow-git-deploy-full-poly.py` | `run-lint.py` | ✅ 通过 |
| `git-security.json`（cs_py） | `lint-json.py` | ✅ 通过 |
| `git-security.json`（jywl-lab） | `lint-json.py` | ✅ 通过 |
| `verified-task-index.json` | `lint-json.py` | ✅ 通过 |

## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | Preflight 支持 target | `python atomic-deploy-preflight.py --devroot <cs_py> --target <jywl-lab>` | 通过安全检查，repo_url 为 jywl-lab 的 remote |
| 2 | Manifest 生成 | `python atomic-polyrepo-context-manifest.py --devroot <cs_py> --target <jywl-lab> --output venv/tmp/test.json` | `venv/tmp/test.json` 存在，含 `repo_url`/`branch`/`target` 字段 |
| 3 | AI Summary 支持 target | `python generate-ai-summary.py --devroot <cs_py> --target <jywl-lab>` | 正常生成摘要，git diff 在 jywl-lab 执行 |
| 4 | Workflow Step 0 | `python workflow-git-deploy-full-poly.py --devroot <cs_py> --target <jywl-lab> --step 0` | 仅执行 preflight + manifest audit，不执行 git add/commit/push |
| 5 | Task Index 合法 | `python schema/tool/lint-json.py -v references/runtime/verified-task-index.json` | `[OK]` |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建文件 | `Remove-Item scripts/py-tools/atomic-deploy-preflight.py, scripts/py-tools/atomic-polyrepo-context-manifest.py` |
| 恢复修改文件 | `git checkout scripts/py-tools/generate-ai-summary.py scripts/py-steps/step-09-github-sync-issue.py scripts/py-tools/fetch_issue.py scripts/py-tools/workflow-git-deploy-full-poly.py git-security.json references/runtime/verified-task-index.json` |

## 七、关联文档

| 文档 | 说明 |
|------|------|
| `references/env-migrations/env-migration-polyrepo-context-manifest-2026-07-08-173019.md` | 上期 Pending 清单（本次全部完成） |
| `references/tasks/deploy-git-isolated/docs/research/opencode-plugin-pre-tool-use-research-2026-07-09-163543.md` | 本次 session 衍生的 OpenCode Plugin 可行性研究 |
| `references/env-migrations/env-migration-opencode-bash-timeout-guard-2026-07-09-164437.md` | 本次 session 衍生的 bash-timeout-guard Plugin 新增 |

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-09-164950 |
| **更新人** | OpenCode Agent Session |
| **变更触发** | 接续 07-08 Pending 清单，完成 polyrepo workflow 改造编码落地 |
| **下次修订条件** | 实测 polyrepo 全链路部署（`--target jywl-lab`）发现问题时；新增 polyrepo 适配脚本时 |
| **跨环境迁移参考** | 直接复制本文档「文本文件变更清单」中的全部文件到新环境对应路径 |
