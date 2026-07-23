---
title: env-migration — Polyrepo Git-Security 身份卡与 default_branch 机制建设
description: 本次 session 完成了 polyrepo 场景下 git-security.json 身份卡体系升级、repo_url 基准 vs 实测对碰模型落地、default_branch 动态读取机制建设，消除了所有 master/main 硬编码。
date: 2026-07-23
meta:
  version: "1.0.0"
---

# env-migration-polyrepo-git-security-identity-and-default-branch-2026-07-23-164411

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Polyrepo Git-Security 身份卡与 default_branch 机制建设 |
| **日期** | 2026-07-23 |
| **文件名时间戳** | `2026-07-23-164411` |
| **触发原因** | polyrepo workspace 架构下，各 repo 需独立 Git 配置，repo_url 不能从 devroot .env 推断，分支保护不能硬编码 master |
| **影响范围** | 3 个 git-security.json、6 个 Python 脚本、4 个 baseline 文档 |
| **风险等级** | 中（涉及部署流程核心逻辑，但 preflight 机制可在 commit 前阻断） |


## 一、文本文件变更清单

### 1. 新建/修改 `cs_py/git-security.json`

| 属性 | 值 |
|------|-----|
| **路径** | `git-security.json` |
| **变更类型** | `追加` |
| **新增内容** | `"default_branch": "master"`、`"allow_direct_push_to": []`、`"security_level": "strict"` |
| **作用** | cs_py 作为历史遗留仓库，默认分支为 master；严格模式禁止任何直接 push，必须 PR merge |
| **验证方式** | `cat git-security.json` 确认三个字段存在 |
| **迁移方式** | 直接覆盖（已有字段保留，仅追加） |

### 2. 新建/修改 `apps/repos/jywl-team/jywl-lab/git-security.json`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/repos/jywl-team/jywl-lab/git-security.json` |
| **变更类型** | `追加` |
| **新增内容** | `"default_branch": "main"`、`"allow_direct_push_to": ["main"]`、`"security_level": "normal"` |
| **作用** | jywl-lab 使用 main 作为默认分支；白名单模式允许 main 直接 push |
| **验证方式** | `cat apps/repos/jywl-team/jywl-lab/git-security.json` 确认字段 |
| **迁移方式** | 直接覆盖 |

### 3. 新建/修改 `apps/repos/matt-cch/jywl-settlement/git-security.json`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/repos/matt-cch/jywl-settlement/git-security.json` |
| **变更类型** | `追加` |
| **新增内容** | `"default_branch": "main"` |
| **作用** | 补充默认分支声明（已有 allow_direct_push_to 和 security_level） |
| **验证方式** | `cat apps/repos/matt-cch/jywl-settlement/git-security.json` 确认 default_branch 存在 |
| **迁移方式** | 直接覆盖 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/polyrepo_context.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/polyrepo_context.py` |
| **变更类型** | `重写` |
| **新增/修改内容** | `_resolve_repo_url()` 改为基准 vs 实测对碰模型；新增 `_resolve_default_branch()`、`_load_security_config()`；`PolyrepoContext` 新增 `default_branch`、`allow_direct_push_to`、`security_level` 字段 |
| **作用** | 消除 .env fallback 依赖；repo_url 以 git-security.json 为审计基准；default_branch 从 Repo 身份卡读取 |
| **验证方式** | `python -c "import polyrepo_context; print('OK')"`（路径正确时） |
| **迁移方式** | 直接替换 |

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py` |
| **变更类型** | `重写` |
| **新增/修改内容** | repo_url 解析改为对碰模型；分支保护检测从硬编码 `if current_branch == "master"` 改为读取 `git-security.json` 的 `default_branch` + `allow_direct_push_to` |
| **作用** | preflight 能正确识别任意默认分支（master/main/其他）；根据 allow_direct_push_to 白名单/严格模式给出精确阻止理由 |
| **验证方式** | 执行 `atomic-deploy-preflight.py --devroot <devroot> --target <target>` 观察输出 |
| **迁移方式** | 直接替换 |

### 6. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-git-deploy-full-poly.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | Step 7 manifest 消费时同步读取 `default_branch` 和 `allow_direct_push_to`；push reject 后根据安全策略给出三种精确提示（白名单允许但远程拒绝 / 严格模式 / 一般保护） |
| **作用** | 被动兜底机制：preflight 未拦截或远程规则比本地更严格时，给出可操作的错误提示 |
| **验证方式** | 执行 workflow --step 7 观察 reject 提示 |
| **迁移方式** | 直接替换 |

### 7. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/gh-branch-protect.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/gh-branch-protect.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 `_get_default_branch(devroot)` 函数；`--branch` 默认值从硬编码 `"master"` 改为从 `git-security.json` 读取 |
| **作用** | 保护正确的默认分支，不再假设 master |
| **验证方式** | `python gh-branch-protect.py --dry-run` 观察默认分支 |
| **迁移方式** | 直接替换 |

### 8. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-create.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-create.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 `_get_default_branch(devroot)` 函数；`--base` 默认值从硬编码 `"master"` 改为从 `git-security.json` 读取 |
| **作用** | PR 目标分支正确指向当前仓库的默认分支 |
| **验证方式** | `python gh-pr-create.py --help` 观察默认 base 值 |
| **迁移方式** | 直接替换 |

### 9. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-merge.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/gh-pr-merge.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 提示语从 `checkout master` 改为动态读取 `default_branch` 后输出 `checkout {default_branch}` |
| **作用** | merge 后同步提示指向正确的默认分支 |
| **验证方式** | 执行 merge 后观察提示语 |
| **迁移方式** | 直接替换 |

### 10. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-gh-pr.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-gh-pr.py` |
| **变更类型** | `修改` |
| **新增/修改内容** | 新增 `_get_default_branch(devroot)` 函数；`--base` 默认值从硬编码 `"master"` 改为从 `git-security.json` 读取 |
| **作用** | PR workflow 默认目标分支与仓库实际默认分支一致 |
| **验证方式** | `python workflow-gh-pr.py --help` 观察默认 base 值 |
| **迁移方式** | 直接替换 |

### 11. 修改 baseline 文档

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/baseline/baseline-principles.md`、`baseline-workflow-deploy.md`、`baseline-structure.md`、`baseline-index.md` |
| **变更类型** | `追加` |
| **新增内容** | 语义清晰化（公共资源 vs 操作对象）、CWD 锚定实质、repo_url 基准 vs 实测对碰模型、default_branch 与分支保护策略、脚本改造清单 |
| **作用** | 将本次设计决策固化为 baseline 共识 |
| **验证方式** | lint 通过 |
| **迁移方式** | 直接追加 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 无文件复制、缓存迁移、目录创建等非文本操作。


## 三、环境变量速查

无新增环境变量。`.env` 职责收缩：
- **保留**：`GITHUB_PAT`、`GITHUB_USERNAME`（全局认证信息）
- **淘汰**：`GITHUB_REPO_URL`（仓库特定信息应写入各自 `git-security.json`）


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.json`（3 个 git-security.json） | `run-lint.py lint_json` | JSON 语法正确性 | `[OK]` 无解析错误 |
| `.py`（6 个脚本） | `run-lint.py lint_python` | Python 语法解析 | `[OK]` py_compile 通过 |
| `.md`（4 个 baseline + 本文件） | `run-lint.py md_lint + lint_encoding` | frontmatter 合规 + 编码/BOM/换行符 | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |

**验证结果**：全部 20 个文件通过，0 违规。


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 git-security.json 字段完整 | `cat <target>/git-security.json \| python -m json.tool` | 包含 repo_url、default_branch、allow_direct_push_to、security_level |
| 2 | 确认 polyrepo_context 能正确加载 | `python -c "from polyrepo_context import PolyrepoContext; ctx = PolyrepoContext.from_args(toolchain_root=Path('.'), target=Path('.')); print(ctx.default_branch, ctx.allow_direct_push_to)"` | 输出与 git-security.json 一致 |
| 3 | 确认 preflight 分支检测正确 | `python atomic-deploy-preflight.py --devroot . --target .` | 能识别当前分支是否在白名单中 |
| 4 | 确认 PR 工具默认分支正确 | `python gh-pr-create.py --help` | --base 默认值为当前仓库的 default_branch |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 git-security.json | 从 `.bak` 备份恢复（atomic-config-edit-json.py 已自动生成） |
| 恢复代码 | git checkout 到变更前 commit |
| 恢复 baseline | git checkout 到变更前 commit |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-23-164411 |
| **更新人** | Human + Agent Session |
| **变更触发** | polyrepo workspace 架构下各 repo 需独立 Git 配置，消除 master/main 硬编码 |
| **下次修订条件** | 新增 polyrepo 仓库时需补充 git-security.json；发现新的 master/main 硬编码时需修复 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-23*  
*模板版本：v2*
