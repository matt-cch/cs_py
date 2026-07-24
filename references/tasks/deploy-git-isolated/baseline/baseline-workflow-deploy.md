---
title: deploy-git-isolated — JS 工具链、全链条部署与三侧冲突仲裁
description: JS 三层对称架构、全链条部署 Workflow 铁律、Git 空目录保留规则、PS/PY/JS 三侧工具链的交叉引用与冲突仲裁。
date: 2026-07-03
meta:
  version: "1.0.0"
  source: task-canonical-baseline.md 拆分
---

# JS 工具链、全链条部署与三侧冲突仲裁

## 8.6 JS 工具链三层架构

> **来源**：用户与 Agent 在 2026-06-24 对话中共同确认。本节固化 JS 侧三层对称架构的设计共识，明确 `node.exe` 作为一等宿主执行环境的地位、js-plugins/ 与 js-tools/ 的职责边界、以及 dual-mode 插件的约定。

### 8.6.1 node.exe 是一等宿主执行环境

`venv/node/node.exe` 在本项目中的角色**等价于** `venv/py/python.exe` 和 `powershell.exe`：

| 维度 | python.exe | node.exe | powershell.exe |
|------|-----------|---------|---------------|
| 隔离路径 | `venv/py/python.exe` | `venv/node/node.exe` | 系统自带 |
| 脚本目录 | `py-tools/*.py` | `js-tools/*.js` | `ps-tools/*.ps1` |
| 插件目录 | `py-plugins/*.py` | `js-plugins/*.js` | `lib-plugins/*.ps1` |
| 统一入口 | `py_lib.py` | `js_lib.js` | `github-lib.ps1` |
| 注册表 | `py-sort-rules.json` | `js-sort-rules.json` | `lib-sort-rules.json` |
| 调用方式 | `python.exe script.py` | `node.exe script.js` | `powershell -File script.ps1` |

**铁律**：js-tools/ 下的 CLI 脚本受同样的三层架构约束——通过 `js_lib.js`（Entry）读取 `js-sort-rules.json`（Registry），按拓扑依赖加载 `js-plugins/`（Plugins），**禁止**直接 `require()` 插件模块绕过入口。

### 8.6.2 JS 三层对称架构

```
┌───────────────────────────────────────────────┐
│  Layer 3: js-tools/（Workflow / CLI 入口）      │
│  ────────────────────────────────────────────   │
│  url-analyze.js  ← 通过 js_lib 加载 url-utils   │
│  extract-article.js  ← 浏览器注入 workflow      │
│  readability.js · turndown.js                   │
│  （通过 js_lib --resolve <tool> 获取依赖路径）   │
└──────────────────────┬────────────────────────┘
                       ↓ require 或 add_init_script
┌───────────────────────────────────────────────┐
│  Layer 2: js_lib.js（统一入口）                 │
│  ──────────────────────────────────────────   │
│  node js_lib.js --list                        │
│  node js_lib.js --resolve <tool>              │
│  （拓扑排序 + 依赖补齐 + 路径输出）              │
└──────────────────────┬────────────────────────┘
                       ↓ 读取 JSON + 动态加载
┌───────────────────────────────────────────────┐
│  Layer 1: js-plugins/（可复用模块，dual-mode）   │
│  ──────────────────────────────────────────   │
│  url-utils.js       ← 受 readability.js 启发   │
│  markdown-rules.js  ← 受 turndown 规则系统启发  │
│  （同时支持 window.__ + module.exports）        │
└───────────────────────────────────────────────┘

┌─ Config ─────────────────────────────────────────┐
│  js-sort-rules.json  ← 资产注册表 + 依赖拓扑      │
│    type: browser | node | dual                   │
│    layer: atomic | workflow                      │
└──────────────────────────────────────────────────┘
```

### 8.6.3 js-plugins/ 与 js-tools/ 的职责边界

| 目录 | 职责 | 调用方式 | 例子 |
|------|------|---------|------|
| `js-plugins/` | 可复用的**模块**，暴露 API 给上层 | 被 js-tools 通过 `require()` 或 `add_init_script(合并)` 加载 | `url-utils.js` 提供 `toAbsoluteURI`、`isImageUrl` |
| `js-tools/` | 完整的**工具脚本**，可直接执行或浏览器注入 | `node tool.js` (CLI) 或 `add_init_script(tool.js)` (browser) | `url-analyze.js` 为 CLI + 浏览器双模式，`extract-article.js` 仅为浏览器模式 |

**关键区分**：
- js-plugins/ 是**库代码（library）**，不自带执行入口，暴露 API 给上层 js-tools
- js-tools/ 是**入口脚本（entry script）**，自带 CLI 主逻辑或浏览器注册逻辑 `window.__xxx = fn`

### 8.6.4 js-plugins/ 是模式提取，不是重构依赖

**核心意图**：js-plugins/ 下的模块（`url-utils.js`、`markdown-rules.js`）是从 3 个 js-tools（`readability.js`、`turndown.js`、`extract-article.js`）的代码中**受启发提取**的可复用工具函数。这**不是**对 3 个 js-tools 的重构——它们保持自包含，**不**依赖 js-plugins/。

| 自包含脚本 | 对应的 js-plugins/ 提取 | 是否依赖该插件 |
|-----------|------------------------|--------------|
| `readability.js` | `url-utils.js`（toAbsoluteURI 等） | ❌ 否 |
| `turndown.js` | `markdown-rules.js`（规则预设） | ❌ 否 |
| `extract-article.js` | — | ❌ 否 |
| `url-analyze.js`（新开发） | `url-utils.js` | ✅ 是（通过 js_lib 按依赖拓扑加载） |

**铁律**：新增 js-tools 优先从 js-plugins/ 取能力；既有 js-tools（readability/turndown/extract-article）不重构引入新依赖，保持向后兼容。

### 8.6.5 Dual-mode 插件约定

所有 js-plugins/ 模块必须同时支持两种环境：

```javascript
(function (global) {
  'use strict';
  var MyModule = { someAPI: function() { ... } };

  // 浏览器：注册到 window.__命名空间
  if (typeof window !== 'undefined') global.__MY_MODULE = MyModule;

  // Node.js：通过 module.exports 暴露
  if (typeof module !== 'undefined' && module.exports) module.exports = MyModule;
})(typeof window !== 'undefined' ? window : global);
```

**原因**：同一份模块代码被两个完全不同的加载器使用——`add_init_script`（浏览器）和 `require()`（Node.js）。

### 8.6.6 Python 桥接（js_loader.py）

`js_loader.py` 是 Python 侧的 JS 资产发现桥梁，读取同一份 `js-sort-rules.json`：

| 方法 | 返回值 | 用途 |
|------|--------|------|
| `resolve_script_tags(tool_names=["extract-article"])` | `[str]` — 按拓扑排序的文件绝对路径列表 | 给 `add_init_script(合并内容)` 提供注入顺序 |
| `validate()` | `dict` — 磁盘存在性检查结果 | 注入前确认所有文件存在 |

**关键设计**：
- 纯 Python 实现，不做任何 JS 执行，不做任何网络请求
- 只读取 JSON → Kahn 拓扑排序 → 返回路径
- Python 侧通过 `js_loader.py` 发现 JS 资产，通过 `article_extractor.py` 编排注入

### 8.6.7 浏览器注入策略（CSP 处理）

| 站点 CSP | Playwright API | 条件 |
|---------|---------------|------|
| 宽松（允许 unsafe-inline） | `page.add_script_tag(path=)` | 直接可用 |
| 严格（禁止 script-src-elem inline） | `context.add_init_script(合并JS)` | **必须合并全部 JS 为单次调用**（因 `add_init_script` 每次调用创建独立 V8 作用域，`var` 声明不跨调用共享） |

**标准注入代码**：
```python
combined_js = "\n".join(Path(p).read_text(encoding="utf-8") for p in js_paths)
await context.add_init_script(combined_js)
await page.goto(url)
result = await page.evaluate("window.__extractArticle()")
```

> 详细踩坑记录见：`gotchas/browser-add-init-script-scope-isolation.md`

### 8.6.8 与 Python 侧「禁止越级」规则的对应关系

| Python 规则 | JS 等价规则 |
|------------|-----------|
| Workflow 禁止直接 `import` Plugin | js-tools 禁止直接 `require()` js-plugins/（应通过 `js_lib.js` 加载） |
| Workflow 通过 `py_lib.load_plugins()` 获取能力 | js-tools 通过 `require('js_lib.js').resolve(['tool'])` 获取依赖路径 |
| Plugin 清单通过入口 API 动态发现 | `js_lib.js --list` 动态列出全部资产 |
| 文档不暴露插件文件名 | TASK-TOOLS-INDEX.md 只说明「有哪些能力类别」 |

**例外**：`url-analyze.js` 的 fallback 路径（当 js_lib 不可用时直接 `require('../js-plugins/url-utils.js')`）与 Python 侧 `_Fallback` 类的设计意图一致——后退到能力可用，不在无入口时崩溃。但 js_lib 可用时必须走入口。


## 8.7 全链条部署 Workflow 铁律

> **来源**：用户与 Agent 在 2026-06-24 对话中共同确认。本节解决「Agent 按 steps 手动执行而非 workflow 整体调用」的问题。

### 8.7.1 问题背景

`workflow-deploy-full.py` 是 Step 4-9 的唯一编排入口，但 Agent 在收到"commit and push"等指令时，习惯手动逐条调用 `ps-steps/` 下的独立脚本，导致：
1. 跳过 AI 摘要生成（手动调 commit 不会触发 `generate-ai-summary.py`）
2. 跳过 meta 参数注入（手动调 Step 9 时没有 `--meta`，Issue comment 无 AI 语义摘要）
3. 跳过 Issue 同步（手动调 push 不会自动触发 issue sync）
4. `--message` 参数不一致（手动调各步骤可能传不同的 message）

### 8.7.2 铁律

凡涉及 Step 4-9（add → commit → remote → push → upstream → issue sync）的操作，**必须**使用 `workflow-deploy-full.py` 执行，禁止手动逐条调用 `py-steps/` 下的独立脚本。

**执行的正确路径**：

| 场景 | 命令 |
|------|------|
| 全自动发布（不关心 commit message） | `python workflow-deploy-full.py --devroot "${devroot}" --auto` |
| 发布并指定 commit message | `python workflow-deploy-full.py --devroot "${devroot}" --message "feat: xxx"` |
| 仅执行单步（调试用） | `python workflow-deploy-full.py --devroot "${devroot}" --step 7 --message "feat: xxx"` |

### 8.7.3 执行顺序（不可更改）

```
Step 0a: atomic-git-preflight（通用 git 环境验证）→ 失败则停止
Step 0b: atomic-deploy-preflight（部署特有验证：PAT/分支/agent）→ 失败则停止
Step 4: git add
Step 4.5: atomic-check-staged-after-add（staged 内容安全扫描）→ 失败则停止（可 git reset HEAD 回滚）
Step 4→5 之间: 生成 AI 摘要 + meta（使用 staged diff）
                 → 失败则报错停止（文件已 staged 但未 commit，可 git reset HEAD 回滚）
Step 5: git commit（使用 --message 或 --auto 自动生成）
更新 meta commit hash
Step 6: remote
Step 7: push
Step 8: upstream
Step 9: issue sync（使用 meta 中的 AI 摘要 + 分类信息）
```

### 8.7.4 关键设计决策

1. **AI 摘要失败不是静默 fallback**：AI 摘要生成失败时 workflow 直接 exit，并输出「已执行至 Step 4，请执行 git reset HEAD 回滚」。不静默跳过。
2. **前置验证全量通行后才开始**：agent 插件加载、config.json 配置、.env 变量三方验证全通过后才执行 Step 4。任一失败不执行任何 git 操作。
3. **--auto 不等于无入参**：--auto 模式自动从 staged 文件列表生成 commit message，无需用户指定 --message，但 .env 和 config.json 仍必须提前配置好。
4. **`py-steps/` 下的脚本仍保留**：作为 `--step N` 单步调试模式的底层调用，但 Agent 禁止直接调用它们来完成全链条部署。
5. **Step 4.5 必须通过 subprocess 调用原子脚本，禁止 workflow 内嵌 import 插件**：
   - `workflow-deploy-full.py`（单仓库）和 `workflow-git-deploy-full-poly.py`（polyrepo）的 Step 4.5 均通过 `subprocess.run()` 调用 `atomic-check-staged-after-add.py`
   - polyrepo 场景下必须显式传入 `--target <target>` 和 `--git-exe <git.exe>`，确保扫描在正确的仓库、使用正确的隔离 git 执行
   - 禁止 workflow 脚本直接 `from py_lib import load_plugins` 或访问 `registry.git_security` / `registry.git_staged_scan`——任何插件调用必须由原子脚本封装，workflow 只负责编排
6. **Polyrepo 全链条部署必须使用 `--target`**：`workflow-git-deploy-full-poly.py` 的 `--target` 为强制必填参数（`required=True`），不传直接报错。即使操作 devroot 自身，也必须显式传入 `--target "${devroot}"`，消除跨 session 调用时的上下文歧义。

### 8.7.5 Git 空目录保留规则

> **来源**：用户与 Agent 在 2026-06-25 对话中共同确认。本节记录 Git 空目录问题的根因、解法与架构约束。

**问题根因**：
Git 的默认行为是**不跟踪空目录**。这意味着即使某目录被 `.gitignore` 白名单显式保留（如 `!/references/env-migrations/`），如果该目录内没有任何文件，Git 仍然不会将其纳入版本管理。这会导致目录结构在克隆/检出后丢失。

**解法**：
在 `atomic-deploy-preflight.py`（Step 0b）内部，通过 `py_lib` 统一入口调用 `git_keep_emptydir` 插件，扫描指定目录列表，为空目录自动创建 `.gitkeep` 占位文件。

**架构约束**：
- **不是独立 Step**：空目录保留是 `atomic-deploy-preflight` 的一部分，不存在独立的 "Step 0c"。禁止将其提升为与 Step 4 并列的独立阶段。
- **必须通过 py_lib 加载**：`atomic-deploy-preflight.py` 禁止直接 `import git_keep_emptydir`，必须通过 `load_plugins(devroot=..., tags=["git"])` 获取 registry 后调用。
- **失败不阻断**：`git_keep_emptydir` 执行异常时输出 `[WARN]`，不调用 `sys.exit(1)`。空目录保留是辅助性检查，不是部署的必要条件。
- **目录列表内嵌配置**：当前需要保留空目录的目录列表（如 `["references/env-migrations", "references/tasks/deploy-git-isolated"]`）内嵌在 atomic-deploy-preflight 代码中。未来若配置化，应提取到 `task-config.json` 或同类 Config 契约中，由 atomic 脚本读取后传入插件。

**执行时序**：
```
Step 0a: atomic-git-preflight.py
  ├── 检查 git.exe、身份配置、分支、working tree 状态
  └── [OK] 通过

Step 0b: atomic-deploy-preflight.py
  ├── 检查 .env（PAT、repo URL）
  ├── 验证分支保护（禁止 master 直接 push）
  ├── 验证 agent 插件体系（config.json api_key）
  ├── Git 空目录保留（load_plugins tags=["git"] → git_keep_emptydir.ensure_empty_dirs()）
  └── [OK] 通过

Step 4: git add（此时空目录已有 .gitkeep，可被正常跟踪）

Step 4.5: atomic-check-staged-after-add.py
  ├── 扫描 staged 文件内容敏感模式
  └── [OK] 无敏感内容
```


### 8.7.6 Polyrepo 部署架构设计共识

> **来源**：用户与 Agent 在 2026-07-23 对话中共同确认。本节固化 polyrepo 场景下 workflow 的上下文管理、远程 URL 解析、认证缓存与输出脱敏等设计共识。

#### 8.7.6.1 `PolyrepoContext` 与 manifest 机制

`workflow-git-deploy-full-poly.py` 在 Step 0c 调用 `atomic-polyrepo-context-manifest.py`，生成 `PolyrepoContext` 并序列化为 manifest JSON。manifest 是 polyrepo 部署的**运行时上下文真源**，下游步骤消费而非自行推导。

**核心字段**:

| 字段 | 来源 | 说明 |
|------|------|------|
| `toolchain_root` / `devroot` | 传入参数 | 工具链根 |
| `target` | 传入参数 | 操作目标 |
| `is_polyrepo` | `target.resolve() != devroot.resolve()` | 自动判定 |
| `repo_url` | **优先 target 的 git remote** | 见 8.7.6.2 |
| `branch` | target 的 `git branch --show-current` | 操作目标的真实分支 |
| `git_exe` / `python_exe` | toolchain_root + 固定子路径 | 隔离工具链 |
| `env_file` | toolchain_root / `.env` | 认证信息来源 |

**调用契约**:
```powershell
& "${devroot}\venv\py\python.exe" atomic-polyrepo-context-manifest.py --devroot "${devroot}" --target "${target}" --output "${manifest_path}"
```

**下游消费**：Step 7/8/9 从 manifest 读取 `repo_url`，注入步骤参数，避免各步骤自行推导导致不一致。

#### 8.7.6.2 `repo_url` 基准 vs 实测对碰模型

**铁律**：polyrepo 场景下，`repo_url` 不是"谁先谁后"的优先级 fallback，而是**基准值与实测值的交叉验证**。

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

**对碰规则**：

| git-security 基准 | git-remote 实测 | 结果 | 行为 |
|------------------|----------------|------|------|
| 有值 | 有值，且 **一致** | ✅ 审计通过 | 返回该值，继续部署 |
| 有值 | 有值，但 **不一致** | ❌ 审计失败 | **阻断部署**，提示检查是否操作了错误仓库 |
| 有值 | 无值 | ⚠️ 初始化场景 | 返回基准值，提示建议设置 origin remote |
| 无值 | 有值 | ⚠️ 无基准 | 返回实测值（git-security.json 未配置 repo_url） |
| 无值 | 无值 | ❌ 无来源 | fallback 到 `.env`（已淘汰的 anti-pattern，兼容旧场景） |

**核心设计意图**：
- `git-security.json` 是每个 repo 的**身份卡**，`repo_url` 写在该 repo 内部，操作谁就读谁的——天然避免"拿错地址、推到别人仓库"
- `.env` 中的 `GITHUB_REPO_URL` 是 devroot（cs_py）**自身的**仓库地址，**绝不应**作为 polyrepo 的推送目标
- `.env` 只保留**全局认证信息**（`GITHUB_PAT`、`GITHUB_USERNAME`），不保留**仓库特定信息**（`repo_url`）
- 安全扫描规则（`required_ignore_patterns`、`sensitive_tracked_patterns`）同样因仓库而异，从 target 自身的 `git-security.json` 读取

#### 8.7.6.3 认证信息缓存

Step 7（push）读取 `.env` 获取 `GITHUB_PAT` 和 `GITHUB_USERNAME` 后，将三者缓存为模块变量，供 Step 8（upstream）复用：

- `auth_repo_url`：解析后的仓库路径
- `auth_pat`：PAT（全程内存变量，不输出到日志）
- `auth_username`：GitHub 用户名

**禁止**：Step 8 不复读 `.env`，避免 polyrepo 场景下认证信息错位。

#### 8.7.6.4 PAT 脱敏输出

所有含 PAT 的命令行输出必须经过 `_mask_pat()` 处理：

```python
def _mask_pat(text: str) -> str:
    return re.sub(r"(https?://[^:]+:)([^@]+)(@)", r"\1***\3", text)
```

**生效范围**：`git push` 的认证 URL、任何日志/stdout 中可能暴露 PAT 的字符串。

#### 8.7.6.5 产出文件

| 产物 | 路径模板 | 说明 |
|------|---------|------|
| PolyrepoContext manifest | `venv/tmp/polyrepo-context-wf-{timestamp}.json` | Step 0c 生成 |
| diff 审计 | `venv/tmp/diff-audit-for-ai-summary-{timestamp}.json` | Step 6a 生成 |
| Agent Preflight | `venv/tmp/agent-preflight-for-ai-summary-{timestamp}.json` | Step 6b 生成 |
| AI Summary | `venv/tmp/ai-summary-{timestamp}.json` | Step 6c 生成 |
| Workflow meta | `venv/tmp/workflow-meta-{timestamp}.json` | Step 5 前生成 |

#### 8.7.6.6 `default_branch` 与分支保护策略

**来源**：用户与 Agent 在 2026-07-23 对话中共同确认。本节固化 default_branch 的来源、allow_direct_push_to 的语义、以及各脚本消除硬编码 master/main 的改造原则。

**`default_branch` 的来源**：

| 来源 | 优先级 | 说明 |
|------|--------|------|
| `git-security.json` → `default_branch` | **唯一真源** | 每个 repo 自声明，代码全部从此读取 |
| 代码兜底 | 最后防线 | 若 `git-security.json` 缺失该字段，返回 `"main"`（符合当前潮流） |

**禁止**：任何脚本中硬编码 `"master"` 或 `"main"` 作为默认分支。

**`allow_direct_push_to` 语义**：

> **约束范围**：白名单仅对 **`default_branch`** 生效。非 `default_branch` 的分支（如 `feature/xxx`）不受白名单约束，本地 preflight 无条件放行。remote 是否接受由 GitHub 分支保护策略独立决定。
>
> **历史原因**：早期只处理 `main`/`master` 的 push 管控场景，feature 分支不在设计范围内。保持现状的原因是：① feature 分支通常无严重后果；② 若严格管控 feature 分支，每新增一个 feature 都需同步修改 `git-security.json` 和 remote 保护策略，维护成本过高。

**本地配置与 Remote 规则的端点独立性**：

```
┌─────────────────────────────────────┐     ┌─────────────────────────────┐
│ 本地端点                              │     │ Remote 端点                  │
│ git-security.json + atomic-deploy-    │     │ GitHub 分支保护策略           │
│ preflight.py                          │     │ (Settings → Branches)        │
├─────────────────────────────────────┤     ├─────────────────────────────┤
│ • 自声明规则，由 repo 维护者写入       │     │ • 由仓库 Owner/Admin 配置     │
│ • 代码读取并执行判定（exit 0/1）       │     │ • 网络请求时的实际裁决         │
│ • 只控制"走现成脚本"的路径            │     │ • 控制所有 git push 请求      │
│ • 手工直接 git push → bypass         │     │ • 无法 bypass                 │
└─────────────────────────────────────┘     └─────────────────────────────┘
         ↓                                              ↓
    【预判】本地提前拦截，避免无效请求           【终审】实际决定是否接受 push
```

**关键认知**：

| 维度 | 本地 `git-security.json` + code | Remote push policy |
|------|-------------------------------|-------------------|
| **性质** | 本地配置文件 + 脚本判定 | 远程服务器规则 |
| **受众** | `atomic-deploy-preflight.py` 等现成脚本 | GitHub/Git 服务 |
| **强制力** | 仅对走现成脚本的路径有效 | 对所有 push 请求有效（无法 bypass） |
| **手工 push** | ❌ 不控制（直接 bypass） | ✅ 控制（照样 reject） |
| **对齐关系** | 本地配置**反映** remote 规则的事实 | 独立配置，不受本地影响 |
| **典型场景** | `cs_py` 写 `[]` 是因为 remote 实际 reject main push | 仓库 Settings 中配置了 branch protection |

**示例对照**：

| 仓库 | 本地 `allow_direct_push_to` | Remote 实际规则 | 本地脚本行为 | Remote 实际结果 |
|------|---------------------------|----------------|------------|---------------|
| `cs_py` | `[]` | `main` 受保护，reject push | preflight 主动 `exit(1)` | push 被拒绝 |
| `jywl-settlement` | `["main"]` | `main` 允许 push | preflight 放行 | push 成功 |
| 某仓库（假设） | `["main"]` | `main` 受保护，reject push | preflight 放行 | push 被拒绝 |

> **最后一行说明**：本地配置与 remote 规则**可能不一致**。`git-security.json` 只是"本地脚本的行为预期"，不代表 remote 一定配合。当两端不一致时，以 remote 实际返回为准。

| 值 | 对 `default_branch` 的效果 | 对 `feature/*` 等非默认分支的效果 |
|----|-------------------------|--------------------------------|
| `[]`（空数组） | **禁止**直接 push，`preflight` 主动 `exit(1)` | 不受约束，`preflight` 放行 |
| `["main"]` | **允许**直接 push | 不受约束，`preflight` 放行 |
| `["main", "dev"]` | **允许**直接 push | 不受约束，`preflight` 放行 |

**分支保护检测时序**：

```
Step 0b (atomic-deploy-preflight.py):
  读取 git-security.json → default_branch + allow_direct_push_to
  若 current_branch 不在 allow_direct_push_to 中:
    → [WARN] + [FAIL] Preflight 终止（主动阻止）

Step 7 (workflow-git-deploy-full-poly.py push):
  若 push 被 remote reject:
    → 根据 allow_direct_push_to 给出精确提示（被动兜底）
    - 白名单允许但仍失败 → 提示检查远程额外保护规则
    - 严格模式 → 提示必须走 feature 分支 + PR merge
    - 一般保护 → 提示使用 PR merge 流程
```

**脚本改造清单（消除硬编码）**：

| 脚本 | 改造前 | 改造后 |
|------|--------|--------|
| `atomic-deploy-preflight.py` | 硬编码 `if current_branch == "master"` | 读取 `git-security.json` 的 `default_branch` + `allow_direct_push_to` |
| `polyrepo_context.py` | 无 `default_branch` 字段 | 新增字段，从 `git-security.json` 读取 |
| `gh-branch-protect.py` | `--branch` 默认 `"master"` | 默认从 `git-security.json` 读取 `default_branch` |
| `gh-pr-create.py` | `--base` 默认 `"master"` | 默认从 `git-security.json` 读取 `default_branch` |
| `gh-pr-merge.py` | 提示 `checkout master` | 动态读取 `default_branch` |
| `workflow-gh-pr.py` | `--base` 默认 `"master"` | 默认从 `git-security.json` 读取 `default_branch` |

**历史遗留策略**：
- `cs_py` 的默认分支为 `master`（创建时设定），**不改**
- 所有后续新仓库默认 `main`，代码通过 `git-security.json` 自识别，无需硬编码


## 8.8 三类型三层架构的交叉引用与冲突仲裁

> **来源**：用户与 Agent 在 2026-06-24 对话中共同确认。本 task 存在三套平行的三层架构（PS、PY、JS/TS），它们之间天然产生数据面交叉和路由面冲突。随着三侧工具链扩展，仲裁机制会渐进式明晰。

### 8.8.1 已知的三侧对称结构

| 维度 | PS 侧 | PY 侧 | JS 侧 |
|------|-------|-------|-------|
| Layer 3（入口脚本） | `ps-tools/*.ps1` | `py-tools/*.py` | `js-tools/*.js` |
| Layer 2（统一入口） | `github-lib.ps1` | `py_lib.py` | `js_lib.js` |
| Layer 1（可复用模块） | `lib-plugins/*.ps1` | `py-plugins/*.py` | `js-plugins/*.js` |
| 注册表（依赖拓扑） | `lib-sort-rules.json` | `py-sort-rules.json` | `js-sort-rules.json` |
| Profile 筛选 | `-Profile` 参数 | `load_plugins(profile=)` | `--profile`（计划中） |

### 8.8.2 交叉引用类型

#### 数据面交叉（同一数据源多种消费）

| 数据源 | 消费者 1 | 消费者 2 | 消费者 3 |
|--------|---------|---------|---------|
| `js-sort-rules.json` | `js_lib.js`（JS 入口） | `js_loader.py`（PY 桥接） | PS 侧（未出现，理论上可消费） |
| `py-sort-rules.json` | `py_lib.py` | — | — |
| `verified-task-index.json` | Agent 全局决策 | 各 task 的 TASK-TOOLS-INDEX | — |

**规则**：同一份 JSON 被多侧消费时，JSON schema 由最先定义的侧维护，后加入的消费者必须兼容已有 schema。例如 `js-sort-rules.json` 的 `type` 字段（browser/node/dual）是 JS 侧定义的，`js_loader.py` 必须读取但不需要理解该字段。

#### 路由面交叉（同一需求多条路径）

| 需求 | PS 路径 | PY 路径 | JS 路径 | 仲裁规则 |
|------|---------|---------|---------|---------|
| 获取工具版本 | `get-*-version.ps1`（遗留） | `update-version.py`（推荐） | — | `TASK-TOOLS-INDEX.md` 边界矩阵声明「首选」 |
| GitHub API 调用 | `github-api.ps1`（PS 插件） | `github_api.py`（PY 插件） | — | 同一 task 内选已激活侧，不混用；跨 task 按入口 task 所在侧定 |
| URL 分析 | — | — | `url-analyze.js`（唯一） | 无争议，只有 JS 侧提供 |
| 文章下载 | — | `download-article.py`（PY 入口） | `extract-article.js`（被 PY 调用） | 入口在 py-tools/，核心在 js-tools/ + Chrome，不构成冲突 |

### 8.8.3 冲突仲裁原则（渐进式）

以下为当前已知原则，随冲突案例增多而补充：

| 原则 | 说明 | 案例 |
|------|------|------|
| **入口优先** | 入口在哪侧，路由就定在哪侧。另一侧不能声称同等入口。 | 文章下载入口在 py-tools/，即使核心逻辑在 JS。不创建 `js-tools/download-article.js` |
| **唯一职责** | 某个细分能力只能由一侧提供，无 parallel 实现。 | URL 分析由 `url-analyze.js` 唯一提供，不造 PS/PY 版 |
| **生态主流** | 该能力的语言生态更适合哪侧，就定在哪侧。 | Chrome 操作 → PY（Playwright API 最成熟）；字符串处理 → JS（正则、URL API 原生） |
| **已存不拆** | 已存在的 parallel 实现（如 PS+PY 的 GitHub API）不合并、不废弃，通过边界矩阵声明首选。 | `TASK-TOOLS-INDEX.md` 矩阵行 |
| **新需求优先选生态主流** | 新工具落地时，按能力天然归属选侧，不强求与既有工具同侧。 | 文章提取：PY 做编排/Chrome 管理（Playwright），JS 做 DOM 提取（Readability） |

### 8.8.4 仲裁文档化要求

当一个需求可被 ≥2 侧的工具覆盖时，必须在 `TASK-TOOLS-INDEX.md` 的边界矩阵中完成以下登记：

1. **首选路径**：当前推荐使用的工具/命令
2. **次选/备选**：其他侧的等价工具（可能为遗留）
3. **禁止行为**：什么情况下该路径不可用（如「禁止手动逐条调用 ps-steps」「禁止直接 import plugin」）
4. **仲裁理由**：一句或多句解释，说明为何首选此侧而非另一侧

> 本条是 §8.8 的**最低可接受标准（Minimum Viable Standard）**。新增冲突场景但未完成上述登记的，视为架构欠债，须在下一次触及该工具时补登。


## 8.9 Pipeline Phase 产物统筹与 `--output` 统一参数规范

> **来源**：用户与 Agent 在 2026-07-23 对话中共同确认。本节固化 polyrepo / 全链条部署 pipeline 中"跨 phase 产物统筹"的设计意图。

### 8.9.1 核心意图

Pipeline 编排层（workflow）需要对各 phase 产生的**所有关键产物**进行统一掌控：追踪、读取、字段传递、事后清理、日志归档。这些产物不限于 JSON manifest，还包括截图、diff 文本、扫描报告等。

为实现这一意图，所有产生可落盘产物的 atomic / workflow-phase 脚本，其产物路径**必须由上级调用者显式指定**，禁止由脚本内部封闭生成。

### 8.9.2 `--output` 统一参数铁律

**CLI 参数统一名**：`--output`

| 规则 | 说明 |
|------|------|
| 参数语义 | 本 phase 的核心产物文件路径（不限定格式） |
| 必填性 | workflow 调用时**必须显式传入**；独立运行时未传入可回退到默认路径 |
| 禁止别名 | 禁止同时使用 `--manifest` / `--output` / `--outfile` 等多个参数名。已存在的 `--manifest` 等历史参数须迁移为 `--output` |
| 回退路径 | `--output` 未传入时，默认落盘到 `venv/tmp/{tool-name}-manifest-{timestamp}.json`。`tool-name` 取脚本文件名（不含扩展名），不做额外转换 |

### 8.9.3 代码内命名规范

CLI 统一为 `--output`，代码内部仍保留 `manifest` 术语描述结构化审计数据：

| 层级 | 变量名 | 类型 |
|------|--------|------|
| CLI 参数 | `args.output` | `str` |
| 路径对象 | `output_path` | `Path` |
| 产物数据字典 | `manifest` | `dict` |
| 写入函数 | `save_manifest(devroot, manifest, output_path)` | 函数 |

### 8.9.4 文件名命名规则

**默认回退**（独立运行，无 `--output` 时）：
```
{devroot}/venv/tmp/{tool-name}-manifest-{timestamp}.json
```
> `tool-name` = 脚本文件名（不含 `.py` 扩展名），例如 `atomic-gh-repo-create`、`workflow-phase-git-local-diff-add-commit`。

**编排层指定**（workflow 调用，推荐格式）：
```
{pipeline-id}-step{step-number}-{phase-name}-{timestamp}.{ext}
```

**示例**：
- `polyrepo-wf-step0c-context-20260722-143000.json`
- `polyrepo-wf-step4-diff-audit-20260722-143105.json`
- `polyrepo-wf-step6b-preflight-20260722-143200.json`

### 8.9.5 已存在脚本的迁移义务

以下脚本须按本节规范整改：

| 脚本 | 当前参数 | 整改动作 |
|------|---------|---------|
| `atomic-agent-preflight.py` | `--manifest` | 改为 `--output`；`generate-ai-summary.py` 调用处联动 |
| `atomic-polyrepo-context-manifest.py` | `--output` | 已符合，无需改动 |
| `atomic-check-chrome-session.py` | `--output` / `-o` | 已符合，移除 `-o` 短别名避免歧义 |
| `workflow-security-audit.py` | `--output` | 已符合 |
| `fetch_issue.py` | `--output` | 已符合 |
| `atomic-gh-repo-create.py` | 无 | 新增 `--output` |
| `atomic-git-repo-clone.py` | 无 | 新增 `--output` |
| `atomic-git-push-smoke.py` | 无 | 新增 `--output` |
| `workflow-phase-git-local-diff-add-commit.py` | 无 | 新增 `--output` |
| `atomic-config-edit-json.py` | 无 | 新增 `--output` |

### 8.9.6 上下游契约示例

**workflow 生成侧**（指定路径）：
```python
output_path = toolchain_root / "venv" / "tmp" / f"polyrepo-wf-step0c-context-{ts}.json"
cmd = [..., str(script), "--devroot", str(toolchain_root), "--output", str(output_path)]
```

**workflow 消费侧**（读取上一 phase 产物）：
```python
if output_path.exists():
    manifest_data = json.loads(output_path.read_text())
    repo_url = manifest_data.get("repo_url", "")
    next_cmd = [..., "--repo-url", repo_url]
```

**注意**：消费侧内部变量仍可用 `manifest_data` / `manifest_path`，仅 CLI 参数统一为 `--output`。


***
> **导航**：返回 [baseline-index.md](baseline-index.md)
