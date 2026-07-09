---
title: Polyrepo Context Manifest 体系建设
description: 建立 polyrepo-context-manifest 运行时上下文真源，解决 workflow 多步骤间上下文不一致、repo_url 推导错误、事后不可审计问题。
date: 2026-07-08
meta:
  version: "1.0.0"
---

# env-migration-polyrepo-context-manifest-2026-07-08-173019

> **文档性质**：环境级变更记录。聚焦 deploy-git-isolated 脚本体系的 polyrepo 架构改造。
> **受众**：Human + Agent。下次 session 接续时直接阅读 Pending 章节即可恢复上下文。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | Polyrepo Context Manifest 体系建设 |
| **日期** | 2026-07-08（frontmatter；文件名时间戳 2026-07-08-173019） |
| **触发原因** | workflow 多步骤各自推导上下文，导致 Step 7 push 使用工具链根 `.env` 的 repo_url 推错仓库；Step 9 issue sync 同理；事后无法审计本次部署到底操作了哪个仓库 |
| **影响范围** | deploy-git-isolated 脚本体系（py-plugins/4 个、py-tools/3 个、py-steps/1 个） |
| **风险等级** | 中（触及部署 workflow 核心链路，但采用新增文件 + 向后兼容改造，不影响既有单仓库场景） |


## 一、文本文件变更清单

### 1. 新建 `py-plugins/session_id.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/session_id.py` |
| **变更类型** | 新建 |
| **作用** | 从 OpenCode 日志文件名提取当前 session-id（`YYYY-MM-DDTHHMMSS`），作为 polyrepo-context-manifest 的命名组成部分 |
| **验证方式** | `python session_id.py --devroot <devroot>` 应输出时间戳字符串（如 `2026-06-10T032649`） |
| **迁移方式** | 直接复制 |

### 2. 新建 `py-plugins/polyrepo_context.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/polyrepo_context.py` |
| **变更类型** | 新建 |
| **作用** | PolyrepoContext dataclass：统一推导工具链根 + 操作目标的运行时上下文，含 `persist()`（落盘 manifest）和 `load()`（反序列化） |
| **关键设计** | manifest 文件名格式：`polyrepo-context-{session-id}-{timestamp}.json`；repo_url 优先从 target 的 `git remote get-url origin` 读取，fallback 到 `.env` |
| **验证方式** | `python -c "from polyrepo_context import PolyrepoContext; ctx = PolyrepoContext.from_args(Path('.')); print(ctx.repo_url, ctx.branch)"` |
| **迁移方式** | 直接复制 |

### 3. 修改 `py-plugins/env_config.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/env_config.py` |
| **变更类型** | 追加 |
| **新增内容** | `resolve_repo_url(toolchain_root, target, git_exe)` 函数：三层 fallback（git remote → .env GITHUB_REPO_URL → 空字符串） |
| **验证方式** | `python -c "from env_config import resolve_repo_url; print(resolve_repo_url(Path('.')))"` |
| **迁移方式** | 追加函数，不影响既有接口 |

### 4. 修改 `py-plugins/git_env.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_env.py` |
| **变更类型** | 修改 |
| **修改内容** | `detect_git_env(devroot: Path, target: Path = None)`：新增可选 `target` 参数，省略时向后兼容（target=devroot）；git 操作全部在 target 执行，git.exe 仍从 devroot 推导 |
| **验证方式** | `python -c "from git_env import detect_git_env; r = detect_git_env(Path('.'), Path('.')); print(r.ok, r.current_branch)"` |
| **迁移方式** | 直接覆盖（向后兼容） |


## 二、非文本操作

无。


## 三、环境变量速查

无新增环境变量。


## 四、落盘验证

| 文件 | 验证工具 | 结果 |
|------|---------|------|
| `session_id.py` | `run-lint.py` | ✅ 通过 |
| `polyrepo_context.py` | `run-lint.py` | ✅ 通过 |
| `env_config.py` | `run-lint.py` | ✅ 通过 |
| `git_env.py` | `run-lint.py` | ✅ 通过 |


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | session_id 检测 | `python session_id.py --devroot <devroot>` | 输出时间戳（非 `opencode`） |
| 2 | polyrepo_context 构建 | `python -c "from polyrepo_context import PolyrepoContext; ctx = PolyrepoContext.from_args(Path('.')); print(ctx.is_polyrepo, ctx.repo_url)"` | `is_polyrepo=False`，`repo_url` 为当前仓库 remote |
| 3 | git_env 双参数 | `python -c "from git_env import detect_git_env; r = detect_git_env(Path('.'), Path('.')); print(r.ok)"` | `True` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建文件 | `Remove-Item scripts/py-plugins/session_id.py, scripts/py-plugins/polyrepo_context.py` |
| 恢复 env_config.py | `git checkout scripts/py-plugins/env_config.py` |
| 恢复 git_env.py | `git checkout scripts/py-plugins/git_env.py` |


## 七、Pending（下次 Session 接续）

以下任务已完成方案确认，尚未编码落地，下次 session 按此清单接续：

| # | 任务 | 文件 | 改造要点 |
|---|------|------|---------|
| 1 | atomic-deploy-preflight 支持 target | `scripts/py-tools/atomic-deploy-preflight.py` | 新增 `--target` 参数；分支保护检测在 target 执行；`.env` 仍从 toolchain_root 读取 |
| 2 | generate-ai-summary 支持 target | `scripts/py-tools/generate-ai-summary.py` | 新增 `--target` 参数；`git diff` 在 target 执行；agent 插件体系仍从 toolchain_root 加载 |
| 3 | workflow 接入 PolyrepoContext | `scripts/py-tools/workflow-git-deploy-full-poly.py` | `main()` 中 `PolyrepoContext.from_args()` → `persist()`；各 step 调用时拆解 `--target`/`--repo-url` 等参数；不再让子脚本自行推导 |
| 4 | 验证所有脚本语法合规 | 全部上述文件 | `run-lint.py` 逐文件验证 |
| 5 | 实测 polyrepo 链路 | workflow | `--devroot <cs_py> --target <jywl-lab>` 跑一次完整部署，确认 Step 7/9 的 repo_url 正确 |

**关键决策已确认（无需下次重新讨论）**：
- Context manifest 传递方案：**Workflow 拆解参数**（子脚本不感知 manifest，只收 `--target`/`--repo-url` 等具体值）
- Session-id 来源：OpenCode 日志文件名时间戳（`venv/data-opencode/opencode/log/YYYY-MM-DDTHHMMSS.log`）
- `git-security.json` 与 `.gitattributes` 同级配对，每个 polyrepo 独立配置
- Team repo（jywl-lab）写操作默认禁止，必须用户亲口确认


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-08-173019 |
| **更新人** | Human + Agent Session |
| **变更触发** | Polyrepo 部署 workflow 上下文不一致问题 |
| **下次修订条件** | Pending 清单全部完成后，更新本条目状态并追加实测记录 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
