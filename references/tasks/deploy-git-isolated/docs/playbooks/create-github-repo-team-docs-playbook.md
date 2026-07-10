---
title: 新建 GitHub 仓库 team-docs 实施方案（polyrepo 模式）
description: 在 matt-cch 账号下新建 team-docs 仓库并首次推送本地 apps/repos/team-docs/ 独立仓库的完整操作手册，含 remote 对应陷阱、先私后转策略与执行前核查项。
date: 2026-07-10
meta: {}
---

# 新建 GitHub 仓库 team-docs 实施方案（polyrepo 模式）

> **适用范围**：在 `matt-cch` GitHub 账号下新建 `team-docs` 仓库，并将其与本地 `apps/repos/team-docs/`（独立 `.git`）对应、首次推送。  
> **阅读对象**：需要本机创建 GitHub 仓库并落盘 polyrepo 的 Agent / Human。  
> **关联文档**：[README.md](../../README.md)（场景 J）、[EXEC-CHEATSHEET.md](../../scripts/EXEC-CHEATSHEET.md)（Stage S7.2）、[TASK-TOOLS-INDEX.md](../../TASK-TOOLS-INDEX.md)（§1.10）、[github-publish-playbook.md](github-publish-playbook.md)

## 一、背景（Background）

1. 用户需要在 GitHub 上新建一个文档协作仓库 `team-docs`，对应本地 `devroot` 下的 `apps/repos/team-docs/`，采用**独立 `.git` 的 polyrepo 模式**（与已有的 `apps/repos/jywl-team/jywl-lab` 平级，物理上位于 cs_py 子目录内、逻辑上独立）。
2. `deploy-git-isolated` task 的主部署流水线（`workflow-deploy-full.py` / `workflow-git-deploy-full-poly.py`）只覆盖 `init → commit → push → issue sync`，**不封装 `repo create`（新建仓库）**。新建仓库这一步必须用已隔离部署的 `gh` CLI（`venv/gh/bin/gh.exe`）在本机补齐，保持全链路无网页。
3. `cs_py` 的 `.env` 中 `GITHUB_REPO_URL` 指向 cs_py 自身仓库。team-docs 作为独立仓库**不能直接复用**该变量，否则 poly workflow 的 remote 绑定会错绑到 cs_py 的 URL。

## 二、意图（Intent）

- **全程本机操作，不打开 GitHub 网页**：建仓库用 `gh`、push 用隔离 `git`、可见性切换用 `gh repo edit`。
- **建立正确对应**：把远端 `github.com/matt-cch/team-docs` 与本地 `apps/repos/team-docs/` 通过 `git remote add origin <URL>` 显式绑定。
- **先私后转策略**：先建 private 仓，推完内容自查无误后再转 public，避免半成品 / 临时文件提前暴露。
- **对齐已有 polyrepo 模式**：参照 `jywl-lab` 的实际配置（remote 写法、是否独立 `.env`、被 poly workflow 调用的参数形态），形成可复用操作手册，不凭空推断。

## 三、关键认知澄清

### 3.1 账号 public ≠ 仓库 public

`matt-cch` 是个人账号，其"公开性"指个人主页 / 资料对外可见；该账号下**每个仓库单独**有自己的可见性开关（private / public），互不影响。账号公开不强制 `team-docs` 必须公开。

### 3.2 可见性可随时转换

`gh repo create` 的 `--private` / `--public` 只是创建时的初始值，创建后用一行命令即可互转（免费账户也支持）：

```powershell
& "D:\pjt\cursor\cs_py\venv\gh\bin\gh.exe" repo edit matt-cch/team-docs --visibility public
& "D:\pjt\cursor\cs_py\venv\gh\bin\gh.exe" repo edit matt-cch/team-docs --visibility private
```

### 3.3 remote 与本地目录的对应

- 本地目录名 `apps/repos/team-docs/` 与 GitHub 仓库名 `team-docs` **没有自动绑定**；对应关系完全靠 `git remote add origin <URL>` 建立。
- URL 里的 `<owner>/team-docs` 才是"对应"本身。
- team-docs 自带独立 `.git`，与 cs_py 主仓库**平级而非从属**——物理上位于 cs_py 子目录下，逻辑上是独立 git 仓库（nested repo，父仓库默认不跟踪子仓库内容）。

## 四、详细实施方案

> 以下为实施方案，**未执行**。执行时按 Step 0→4 顺序操作，且执行前先完成第五节两项核查。

### Step 0 — 建本地目录 + 初始 README

执行时先用 Agent 工具创建目录并写一份最小 `README.md`，保证首次 commit 有内容（空目录无法提交）：

```
D:\pjt\cursor\cs_py\apps\repos\team-docs\   # 新建，独立 .git
```

### Step 1 — 建远程私仓（gh headless）

```powershell
$env:GH_TOKEN = $env:GITHUB_PAT
$env:GH_CONFIG_DIR = "D:\pjt\cursor\cs_py\venv\data-gh"
& "D:\pjt\cursor\cs_py\venv\gh\bin\gh.exe" repo create team-docs --private
# GH_TOKEN 属 matt-cch，仓库自动落在 github.com/matt-cch/team-docs
```

### Step 2 — 本地 init + 独立绑定 remote

```powershell
# init（隔离 git，需 .env 有 GIT_USER_NAME / GIT_USER_EMAIL）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\ps-steps\github-step-01-init.ps1"

# 关键：team-docs 专属 remote，手动绑定，不读 cs_py 的 GITHUB_REPO_URL
& "D:\pjt\cursor\cs_py\venv\git\cmd\git.exe" -C "D:\pjt\cursor\cs_py\apps\repos\team-docs" remote add origin https://github.com/matt-cch/team-docs.git
```

### Step 3 — 安全扫描 + push（poly workflow）

```powershell
# push 前安全检查（敏感文件屏蔽验证）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\ps-tools\github-safety-check.ps1"

# 全链条部署（--target 强制指向 team-docs 本地仓库）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\workflow-git-deploy-full-poly.py" --devroot "D:\pjt\cursor\cs_py" --target "D:\pjt\cursor\cs_py\apps\repos\team-docs"
```

> 注意：Step 2 已手动 `remote add origin`。若 poly workflow 的 Step 6（remote）在检测到 remote 已存在时报错而非跳过，则改用 `--step` 跳过 Step 6（仅跑 add / commit / push / upstream）。具体行为以执行前核查第二项为准。

### Step 4 — 私转公

```powershell
& "D:\pjt\cursor\cs_py\venv\gh\bin\gh.exe" repo edit matt-cch/team-docs --visibility public
```

## 五、执行前核查项（降低风险）

1. **读 `apps/repos/jywl-team/jywl-lab` 的现有 git 配置**：确认其 remote 写法、是否有独立 `.env`、被 poly workflow 调用时传的 `--target` / `--devroot` 形态，让 team-docs 完全对齐已有 polyrepo 模式。
2. **核对 poly workflow 的 Step 6（remote）行为**：确认 workflow 在 remote 已存在时是跳过还是报错，决定是否用 `--step` 跳过 Step 6，避免重复 `remote add` 冲突。

## 六、前置条件清单

- `.env` 已配置 `GITHUB_PAT`（gh headless 认证复用）、`GIT_USER_NAME`、`GIT_USER_EMAIL`
- 隔离工具已部署：`venv/gh/bin/gh.exe`、`venv/git/cmd/git.exe`
- 本地目录 `apps/repos/team-docs/` 在执行 Step 0 时创建（当前不存在）
