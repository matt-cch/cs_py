---
title: env-migration — Polyrepo Git-Security 身份卡、default_branch 机制与 manifest_path 反复踩坑全记录
description: 完整记录 polyrepo workspace 下 git-security.json 身份卡体系建设、repo_url 对碰模型、default_branch 动态读取改造，以及 workflow 中 manifest_path 被覆盖导致 .env fallback 的反复踩坑过程。
date: 2026-07-23
meta:
  version: "1.0.0"
---

# env-migration-polyrepo-git-security-manifest-bug-2026-07-23-174127

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | Polyrepo Git-Security 身份卡、default_branch 机制与 manifest_path 反复踩坑 |
| **日期** | 2026-07-23 |
| **文件名时间戳** | `2026-07-23-174127` |
| **触发原因** | 用户要求理解 polyrepo workspace 架构，发现 git-security.json 未作为 Repo 身份卡被消费，且代码中大量硬编码 master/main |
| **影响范围** | 3 个 git-security.json、6 个 Python 脚本、4 个 baseline 文档、1 个 workflow 核心 bug |
| **风险等级** | **高** — 涉及部署流程核心逻辑，manifest_path 被覆盖会导致 repo_url 从 .env 推断，polyrepo 场景下可能推到错误仓库 |


## 一、架构背景：polyrepo workspace 与公共资源/操作对象分离

### 1.1 .code-workspace 结构

```json
{
  "folders": [
    {"name": "cs_py (devroot)", "path": "."},
    {"name": "api-demo", "path": "apps/api-demo"},
    {"name": "web-demo", "path": "apps/web-demo"},
    {"name": "jywl-lab", "path": "apps/repos/jywl-team/jywl-lab"},
    {"name": "jywl-settlement", "path": "apps/repos/matt-cch/jywl-settlement"}
  ]
}
```

每个 `folder` 都是独立 Git 仓库，各自拥有 `.git/`、`.gitignore`、`.gitattributes`、`git-security.json`。

### 1.2 --devroot 与 --target 的语义

| 参数 | 本质语义 | 类比 |
|------|---------|------|
| `--devroot` | **可用公共资源根**：工具链（`venv/`）、脚本（`scripts/`）、配置（`.env`）的来源 | 手术室里的器械台——无菌器械固定取用，位置不漂移 |
| `--target` | **操作对象**：`git add/commit/push` 实际作用的仓库 | 手术台上的病人——每次只能有一个主操作对象，必须明确指定 |

**CWD 锚定的实质**：workflow 执行路径（CWD）必须锚定在 devroot，这不是形式主义，而是公共资源可用性保障。`venv/`、`.env` 均通过 `Path.cwd()` 或 `--devroot` 定位，CWD 漂移会导致调用到系统全局工具。操作对象（`--target`）通过 `git -C <absolute_path>` 与 CWD 解耦，确保 polyrepo 场景下多个仓库的操作天然隔离、互不污染。


## 二、Git-Security.json 身份卡体系建设

### 2.1 核心设计意图

`git-security.json` 不是"安全附件"，而是每个仓库的**自描述元数据文件**（Repo 身份卡）。其 `repo_url` 字段是 workflow 识别"这个仓库应该推送到哪里"的首要依据。

**为什么不用 .env 的 GITHUB_REPO_URL？**
- `.env` 中的 `GITHUB_REPO_URL` 是 devroot（cs_py）**自身的**仓库地址
- polyrepo 部署时若直接使用 `.env` 的 URL，会导致 push 到错误仓库
- `.env` 只保留**全局认证信息**（`GITHUB_PAT`、`GITHUB_USERNAME`），不保留仓库特定信息

### 2.2 三个仓库的配置对照

| 仓库 | default_branch | allow_direct_push_to | security_level |
|------|---------------|---------------------|----------------|
| `cs_py` | `master`（历史遗留，不改） | `[]`（严格模式，必须 PR） | `strict` |
| `jywl-lab` | `main` | `["main"]`（白名单模式） | `normal` |
| `jywl-settlement` | `main` | `["main"]`（白名单模式） | `normal` |

### 2.3 新增字段说明

| 字段 | 职责 |
|------|------|
| `default_branch` | 仓库默认分支，代码从此读取，消除 master/main 硬编码 |
| `allow_direct_push_to` | 允许直接 push 的分支白名单。`[]` = 严格模式（禁止任何直接 push） |
| `security_level` | `strict` / `normal`，用于提示语分级 |


## 三、Repo URL 基准 vs 实测对碰模型

### 3.1 设计意图

不是"谁先谁后"的优先级 fallback，而是**基准值与实测值的交叉验证**：

```
┌─────────────────┐     对碰      ┌─────────────────┐
│  git-security   │  ←──────→   │  git remote     │
│  .repo_url      │   一致/不一致 │  get-url origin │
│  (基准/审计真源) │              │  (实测值)       │
└─────────────────┘              └─────────────────┘
        ↓ origin 未设置
   以基准指导操作
   （自动设置 remote）
```

### 3.2 对碰规则

| git-security 基准 | git-remote 实测 | 结果 | 行为 |
|------------------|----------------|------|------|
| 有值 | 有值，且一致 | 审计通过 | 返回该值，继续部署 |
| 有值 | 有值，但不一致 | 审计失败 | **阻断部署**，提示检查是否操作错误仓库 |
| 有值 | 无值 | 初始化场景 | 返回基准值，提示建议设置 origin remote |
| 无值 | 有值 | 无基准 | 返回实测值（git-security.json 未配置 repo_url） |
| 无值 | 无值 | 无来源 | fallback 到 .env（已淘汰的 anti-pattern） |

### 3.3 代码实现位置

- `polyrepo_context.py`：`_resolve_repo_url()` 函数
- `atomic-deploy-preflight.py`：Step 2 对碰逻辑


## 四、代码改造清单

### 4.1 改造的 6 个脚本

| 脚本 | 改造内容 |
|------|---------|
| `polyrepo_context.py` | `_resolve_repo_url()` 改为对碰模型；新增 `_resolve_default_branch()`、`_load_security_config()`；`PolyrepoContext` 新增 `default_branch`、`allow_direct_push_to`、`security_level` |
| `atomic-deploy-preflight.py` | repo_url 解析改为对碰模型；分支保护检测从硬编码 `if current_branch == "master"` 改为读取 `git-security.json` |
| `workflow-git-deploy-full-poly.py` | Step 7 manifest 消费时同步读取 `default_branch` 和 `allow_direct_push_to`；push reject 后分层提示 |
| `gh-branch-protect.py` | `--branch` 默认从 `git-security.json` 读取 |
| `gh-pr-create.py` | `--base` 默认从 `git-security.json` 读取 |
| `gh-pr-merge.py` | 提示语 `checkout {default_branch}` 动态化 |
| `workflow-gh-pr.py` | `--base` 默认从 `git-security.json` 读取 |

### 4.2 baseline 增补

| 文件 | 新增章节 |
|------|---------|
| `baseline-principles.md` 0.7.3 | 语义清晰化（公共资源 vs 操作对象）、CWD 锚定实质 |
| `baseline-structure.md` §2.3 | Polyrepo Git 配置四件套、Repo 身份卡设计意图 |
| `baseline-workflow-deploy.md` §8.7.6 | Polyrepo 部署架构设计共识（Context/manifest、repo_url 对碰、认证缓存、PAT 脱敏、default_branch 机制） |
| `baseline-index.md` | 顶层原则速查追加第 16、17 条 |


## 五、核心踩坑：manifest_path 反复横跳

### 5.1 现象

第一轮部署（`475b1ca`）：
```
[WARN] repo_url 来自 .env（已淘汰）: https://github.com/matt-cch/cs_py.git
```

本应读取 manifest 中的 `repo_url`，却 fallback 到了 `.env`。

### 5.2 根因分析

查看 `workflow-git-deploy-full-poly.py` 代码结构：

```python
# 第 441 行：Step 0c 执行前，workflow 自己构造路径
manifest_path = toolchain_root / "venv" / "tmp" / f"polyrepo-context-wf-{int(time.time())}.json"

# 第 445-448 行：调用 0c，传入 --output
cmd_0c = [..., "--output", str(manifest_path)]
result = subprocess.run(cmd_0c, ...)

# ... 0c 执行完毕，manifest_path 指向已生成的文件 ...

# 第 490-495 行：循环开始前，"统一初始化"
all_ok = True
meta_path = None
manifest_path = None   # ← BUG！覆盖了第 441 行的赋值！
commit_executed = False
```

**代码演进遗留问题**：早期版本 Step 0c 可能在循环内部执行，所以循环开头统一初始化所有变量。后来重构把 0c 提到循环外，但忘了删除循环内的 `manifest_path = None`。

### 5.3 反复横跳过程

| 轮次 | Commit | 我的操作 | 结果 | 问题 |
|------|--------|---------|------|------|
| 1 | `475b1ca` | 原始代码 | `[WARN] 来自 .env` | ❌ manifest_path = None 覆盖了 0c 的赋值 |
| 2 | `5402aaf` | 删除 `manifest_path = None` | `[OK] 来自 manifest` | ✅ 但 AI 摘要提示"潜在风险" |
| 3 | `03b968f` | 被"潜在风险"吓到，又加回去，改成注释说明 | `[WARN] 来自 .env` | ❌ 画蛇添足，问题复现 |
| 4 | `c8127e4` | 又删除 | `[OK] 来自 manifest` | ✅ 但显得草率 |
| 5 | 当前 | 最终确认：删除是正确的 | `[OK] 来自 manifest` | ✅ |

### 5.4 为什么 AI 摘要的"潜在风险"是虚惊

AI 摘要提示：
> "若 Step 0c 未正常执行，manifest_path 将无默认值保护"

**实际代码路径保证**：

| 执行模式 | Step 0c 是否执行 | Step 7 是否执行 | manifest_path 状态 |
|---------|-----------------|----------------|-------------------|
| `--step 0` | 执行 | 不执行 | `sys.exit(0)` 直接退出 |
| `--step 4` | 执行 | 不执行 | Step 4 不消费 manifest |
| `--step 5` | 执行 | 不执行 | Step 5 不消费 manifest |
| `--step 7` | 执行 | 执行 | 0c 已赋值，直接可用 |
| `--step all`（默认） | 执行 | 执行 | 0c 已赋值，直接可用 |

不存在「Step 0c 跳过但 Step 7 执行」的路径。只要走到 Step 7，Step 0c 一定已经执行过了。

### 5.5 为什么直接删除是最小正确修复

- 不需要添加复杂的默认值保护（`manifest_path = None if 0c else ...`）
- 不需要改成带条件判断的初始化
- 只需要删除覆盖性赋值，让 0c 的赋值生效

### 5.6 遗留的验证缺口

当前代码对 0c 产物的验证仅到「文件存在」级别：

```python
if not manifest_path.exists():
    sys.exit(1)
# 没有验证 JSON 语法、关键字段是否存在
```

**建议后续增强**：
```python
try:
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "repo_url" in manifest_data
    assert "default_branch" in manifest_data
except Exception as e:
    print(f"[FAIL] manifest 内容无效: {e}")
    sys.exit(1)
```


## 六、部署验证记录

### 6.1 第一轮部署（验证改造整体）

- Commit: `475b1ca`
- 文件数: 14 个（2 新增 + 12 修改）
- 问题: Step 7 出现 `[WARN] repo_url 来自 .env（已淘汰）`
- 原因: manifest_path 被循环开头的 `manifest_path = None` 覆盖

### 6.2 第二轮部署（验证 bug 修复）

- Commit: `5402aaf`
- 文件数: 1 个
- 结果: `[OK] repo_url 来自 manifest` ✅
- 但 AI 摘要提示"潜在风险"

### 6.3 第三轮部署（错误回退）

- Commit: `03b968f`
- 操作: 被 AI 摘要吓到，又把 `manifest_path = None` 加回去
- 结果: `[WARN] 来自 .env` ❌ 问题复现

### 6.4 第四轮部署（最终确认）

- Commit: `c8127e4`
- 操作: 删除 `manifest_path = None`
- 结果: `[OK] 来自 manifest` ✅
- Step 9: `[Step 9] repo_url 来自 manifest` ✅
- Step 10: `[Step 10] repo_url 来自 manifest` ✅


## 七、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 git-security.json 字段完整 | `cat <target>/git-security.json \| python -m json.tool` | 包含 repo_url、default_branch、allow_direct_push_to、security_level |
| 2 | 确认 polyrepo_context 能正确加载 | `python -c "from polyrepo_context import PolyrepoContext; ctx = PolyrepoContext.from_args(toolchain_root=Path('.'), target=Path('.')); print(ctx.default_branch, ctx.allow_direct_push_to)"` | 输出与 git-security.json 一致 |
| 3 | 确认 preflight 分支检测正确 | `python atomic-deploy-preflight.py --devroot . --target .` | 能识别当前分支是否在白名单中 |
| 4 | 确认 PR 工具默认分支正确 | `python gh-pr-create.py --help` | --base 默认值为当前仓库的 default_branch |
| 5 | 确认 workflow manifest 消费正确 | 执行 `workflow-git-deploy-full-poly.py --devroot . --target .` | Step 7 输出 `[OK] repo_url 来自 manifest`，无 `.env` fallback |


## 八、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 git-security.json | 从 `.bak` 备份恢复（atomic-config-edit-json.py 已自动生成） |
| 恢复代码 | `git checkout <变更前 commit>` |
| 恢复 baseline | `git checkout <变更前 commit>` |


## 九、教训与反思

### 9.1 Agent 犯的错误

1. **没有认真做执行路径分析**：看到 AI 摘要的"潜在风险"就慌乱回退，没有区分"通用风险"和"实际代码路径保证"
2. **反复横跳浪费 token**：同一行代码改了 4 次，每次部署都重新跑 AI 摘要（200+s），浪费大量时间
3. **对"防御性编程"理解错误**：把循环开头的统一初始化当成必要措施，没意识到它是代码演进遗留的冗余

### 9.2 正确的调试方法

1. **先画执行路径图**：确认哪些 step 执行、哪些不执行、变量在何时赋值
2. **区分"通用风险提示"和"实际 bug"**：AI 摘要的"潜在风险"是模板化输出，不代表代码真的有问题
3. **最小修改原则**：找到根因后，只做最小必要修改，不要因恐慌而过度工程化


## 十、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-23-174127 |
| **更新人** | Human + Agent Session |
| **变更触发** | polyrepo workspace 架构下各 repo 需独立 Git 配置，消除 master/main 硬编码，修复 manifest_path 被覆盖 bug |
| **下次修订条件** | 新增 polyrepo 仓库时需补充 git-security.json；发现新的 master/main 硬编码时需修复；需补充 0c 产物内容验证 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-23*  
*模板版本：v2*
