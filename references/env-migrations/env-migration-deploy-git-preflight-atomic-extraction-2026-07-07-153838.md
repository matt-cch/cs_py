---
title: deploy-git-isolated Preflight 抽离为 Atomic 脚本体系
description: 将 workflow-deploy-full.py 内嵌的 preflight 逻辑抽离为独立 atomic 脚本，新增 Step 4.5 staged 内容安全扫描，补全文档索引与多端多 devroot 支持规则。
date: 2026-07-07
meta:
  version: "1.0.0"
  session_ts: "2026-07-07-153838"
---

# deploy-git-isolated Preflight 抽离为 Atomic 脚本体系

> **Session 主题**：将 `workflow-deploy-full.py` 内嵌的 preflight 逻辑抽离为独立 atomic 脚本体系，使编排器退化为纯流程调度器；新增 Step 4.5 强制安全门禁；补全文档索引与多端多 devroot 支持规则。
> **触发原因**：用户要求 preflight 逻辑从 workflow 中抽离，每个 atomic 可独立执行、独立测试；同时新增 staged 内容安全扫描作为 add→commit 之间的强制卡点。

## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/git_env.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_env.py` |
| **变更类型** | 新建 |
| **作用** | Git 环境基础检测插件：git exe 存在性、身份配置、当前分支、工作区状态 |
| **验证方式** | 通过 `py_lib.load_plugins(devroot=..., tags=["git"])` 加载后调用 `registry.git_env.detect()` |
| **迁移方式** | 直接复制 |

### 2. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/git_security.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_security.py` |
| **变更类型** | 新建 |
| **作用** | Git 安全扫描插件：.gitignore 生效验证、敏感文件追踪检测、staged 内容 pattern scan（调用 constants.py 唯一真源） |
| **验证方式** | `registry.git_security.scan_git_security(devroot)` |
| **迁移方式** | 直接复制 |

### 3. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/git_preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_preflight.py` |
| **变更类型** | 新建 |
| **作用** | Git Preflight 编排插件：整合 git_env + git_security，提供 `check()`/`verify()` + `GitContext`（含 `run_git`） |
| **验证方式** | `registry.git_preflight.verify(devroot)` |
| **迁移方式** | 直接复制 |

### 4. 新建 `references/tasks/deploy-git-isolated/scripts/py-plugins/git_staged_scan.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/git_staged_scan.py` |
| **变更类型** | 新建 |
| **作用** | Staged 内容扫描插件：扫描已 staged 文件中的敏感模式（API key、PAT、私钥等），调用 constants.py 唯一真源 |
| **验证方式** | `registry.git_staged_scan.scan_staged_content(devroot)` |
| **迁移方式** | 直接复制 |

### 5. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-git-preflight.py` |
| **变更类型** | 新建 |
| **作用** | 原子 CLI：通用 Git 前置验证入口。通过 `py_lib` 加载 `git_preflight` 插件执行统一验证 |
| **验证方式** | `python atomic-git-preflight.py --devroot "${devroot}"` |
| **迁移方式** | 直接复制 |

### 6. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-deploy-preflight.py` |
| **变更类型** | 新建 |
| **作用** | 原子 CLI：部署特有前置验证入口。验证 .env PAT、分支保护、agent 插件、git 空目录保留 |
| **验证方式** | `python atomic-deploy-preflight.py --devroot "${devroot}"` |
| **迁移方式** | 直接复制 |

### 7. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-check-staged-after-add.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/atomic-check-staged-after-add.py` |
| **变更类型** | 新建 |
| **作用** | 原子 CLI：Staged 内容安全扫描入口。必须在 git add 后执行，无 staged 文件时报错 |
| **验证方式** | `python atomic-check-staged-after-add.py --devroot "${devroot}"` |
| **迁移方式** | 直接复制 |

### 8. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/constants.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/constants.py` |
| **变更类型** | 修改 |
| **新增内容** | 新增 `SENSITIVE_PATTERNS` 列表 + `_is_placeholder_token()` + `scan_sensitive_content()` 函数，作为敏感内容扫描的唯一真源 |
| **作用** | 消除 `git_security.py` 和 `git_staged_scan.py` 之间的代码重复，统一敏感模式定义与占位符排除逻辑 |
| **验证方式** | `python -c "from constants import scan_sensitive_content; print(scan_sensitive_content('ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'))"` 应返回空列表 |
| **迁移方式** | 直接覆盖 |

### 9. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-deploy-full.py` |
| **变更类型** | 修改（重大重构） |
| **修改内容** | 1. 移除内嵌 `_preflight_check()` 函数（约 90 行）<br>2. 版本 `v1.2.0` → `v1.3.0`<br>3. `--devroot` 默认值改为 `None` → 运行时回退 `Path.cwd()`<br>4. 新增 Step 0a/0b/4.5 的 subprocess 编排调用<br>5. 执行顺序文档更新为 Step 0a→0b→4→4.5→AI→5→6→7→8→9<br>6. 所有 CLI 示例加上 `--devroot "${devroot}"` |
| **作用** | 编排器退化为纯流程调度器，所有业务逻辑下沉到 atomic 脚本 |
| **验证方式** | `python workflow-deploy-full.py --devroot "${devroot}" --step 9` |
| **迁移方式** | 直接覆盖 |

### 10. 修改 `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-sort-rules.json` |
| **变更类型** | 修改 |
| **新增内容** | 注册 `git_staged_scan` 插件条目（tags: `["git", "validation"]`，depends: `[]`） |
| **作用** | 使 `py_lib.load_plugins()` 能正确加载 `git_staged_scan` |
| **迁移方式** | 直接覆盖 |

### 11. 修改 `references/tasks/deploy-git-isolated/ENTRY.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/ENTRY.json` |
| **变更类型** | 修改 |
| **修改内容** | 版本 `0.20.0` → `0.21.0`；登记 4 个新插件 + 3 个新 atomic 工具；新增版本历史条目 |
| **作用** | 机器可读真源索引同步 |
| **迁移方式** | 直接覆盖 |

### 12. 修改多处文档

| 路径 | 变更类型 | 说明 |
|------|---------|------|
| `references/tasks/deploy-git-isolated/README.md` | 修改 | 工具索引表新增 atomic-deploy-preflight / atomic-check-staged-after-add |
| `references/tasks/deploy-git-isolated/TASK-TOOLS-INDEX.md` | 修改 | 新增 2 个 atomic 工具表格行 + 架构图更新（Step 0a/0b/4.5）+ CLI 示例加 `--devroot` |
| `references/tasks/deploy-git-isolated/scripts/EXEC-CHEATSHEET.md` | 修改 | 新增"部署特有 Preflight"和"Staged 内容安全扫描"命令示例 + workflow 示例加 `--devroot` |
| `references/tasks/deploy-git-isolated/baseline/baseline-workflow-deploy.md` | 修改 | 执行顺序更新为 Step 0a/0b/4.5；空目录保留规则改为 atomic-deploy-preflight 职责 |
| `references/tasks/deploy-git-isolated/SOP.md` | 修改 | Process 描述中的 workflow 命令加 `--devroot` |
| `references/tasks/deploy-git-isolated/gotchas/git-cwd-devroot-mismatch-trap.md` | 修改 | 推荐实践示例加 `--devroot` |
| `references/tasks/deploy-git-isolated/docs/patterns/atomic-vs-orchestration-workflow.md` | 修改 | workflow 调用示例加 `--devroot` |
| `venv/.opencode/AGENTS.md` | 修改 | 新增"Workflow 工具的多端多 devroot 支持"子节（三层约束 + 多 polyrepo + 正误示例） |
| `references/tasks/deploy-git-isolated/baseline/baseline-principles.md` | 修改 | 新增 0.7.1"多端多 devroot 多 polyrepo 架构"子节 |

### 13. 新建 `references/tasks/deploy-git-isolated/scripts/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/README.md` |
| **变更类型** | 新建 |
| **作用** | scripts/ 目录自说明索引：列出 ps-steps / ps-tools / lib-plugins / py-plugins / py-tools / py-examples 共 34 个文件 |
| **迁移方式** | 直接复制 |

### 14. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/README.md` |
| **变更类型** | 新建 |
| **作用** | py-tools/ 目录自说明索引：12 个工具分类为 Workflow / 原子 / 示例 |
| **迁移方式** | 直接复制 |

## 二、非文本操作

无（本次 session 不涉及文件复制、缓存迁移、目录创建等操作）。

## 三、环境变量速查

本次 session 未新增或修改环境变量。`.env` 中仍需配置：
- `GIT_USER_NAME`
- `GIT_USER_EMAIL`
- `GITHUB_REPO_URL`
- `GITHUB_PAT`

## 四、落盘验证

本次 session 所有新建/修改文件均通过 `run-lint.py` 验证：

```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "<文件路径>"
```

验证结果：全部通过（编码/BOM/换行符 + Python 语法 + Markdown frontmatter + JSON 语法）。

## 五、验证清单

| # | 验证步骤 | 命令 | 期望结果 |
|---|---------|------|---------|
| 1 | atomic-git-preflight 独立执行 | `python atomic-git-preflight.py --devroot "${devroot}"` | 输出 `[Git Preflight] 全部通过` |
| 2 | atomic-deploy-preflight 独立执行 | `python atomic-deploy-preflight.py --devroot "${devroot}"` | 输出 `[Deploy Preflight] 全部通过` |
| 3 | atomic-check-staged-after-add 独立执行（无 staged） | `python atomic-check-staged-after-add.py --devroot "${devroot}"` | `[FAIL] 无 staged 文件`，exit 1 |
| 4 | workflow 编排调用 | `python workflow-deploy-full.py --devroot "${devroot}" --step 9` | Step 0a/0b 正常执行，Step 9 成功 |
| 5 | 占位符排除验证 | `python -c "from constants import scan_sensitive_content; print(scan_sensitive_content('ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'))"` | 输出 `[]` |

### Step 10 评论内容验证逻辑（新增）

**验证目标**：确认 Step 9 发送到 GitHub 的评论内容与本地预期一致。

**三层验证架构**：

| 层级 | 真源 | 落盘路径 | 说明 |
|------|------|---------|------|
| 本地发送端 | `summary_text`（Step 9 构造的 "### 变更摘要" 节纯文本） | `venv/tmp/sent-summary-{ts}.txt` | 稳定锚点：不含时间戳、commit hash 等动态内容 |
| Remote 接收端 | GitHub API 返回的最新 comment body | `venv/tmp/remote-latest-comment-{ts}.txt` | 完整 comment：含时间戳、hash、文件清单等动态内容 |

**比对逻辑**：
```
验证通过条件 = remote 最新 comment body 包含 sent-summary 的全部内容（子字符串匹配）
```

**特征规律**（实测确认）：
1. sent-summary 是 remote comment 的精确子集（逐字一致）
2. sent-summary 稳定：不受时间、commit hash、文件数量影响
3. remote comment 含噪声：时间戳、hash、统计数字每次 push 都会变化

**失败处理**：
- 比对失败 → 输出 `[FAIL] Step 10: 评论内容不一致` → 部署标记为 FAILURE
- 网络/API 异常 → 输出 `[FAIL] Step 10: 获取 remote 评论失败` → 部署标记为 FAILURE

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 workflow 内嵌 preflight | 从 git history 恢复 `workflow-deploy-full.py` v1.2.0 版本 |
| 移除 atomic 脚本 | 删除 `atomic-*.py` 三个文件 |
| 移除 py-plugins | 删除 `git_env.py`、`git_security.py`、`git_preflight.py`、`git_staged_scan.py` |
| 恢复 constants.py | 从 git history 恢复 constants.py 旧版本（移除 SENSITIVE_PATTERNS 和 scan_sensitive_content） |
| 恢复 py-sort-rules.json | 移除 `git_staged_scan` 条目 |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-07-153838 |
| **更新人** | Agent Session |
| **变更触发** | 用户要求将 workflow 内嵌 preflight 抽离为 atomic 脚本体系 |
| **下次修订条件** | 新增 atomic 工具或修改 preflight 逻辑时 |
| **跨环境迁移参考** | 直接复制新增文件 + 修改文件覆盖 + 按「验证清单」逐条执行 |

## 八、实测验证记录（2026-07-07）

**测试命令**：
```powershell
python workflow-deploy-full.py --devroot "${devroot}" --step 10 --message "test: verify step 10.5 content comparison"
```

**测试结果**：

| 步骤 | 状态 | 说明 |
|------|------|------|
| Step 0a: atomic-git-preflight | ✅ 通过 | git 环境、身份、分支验证正常 |
| Step 0b: atomic-deploy-preflight | ✅ 通过 | .env、PAT、agent 插件验证正常 |
| Step 9: issue sync | ✅ 通过 | 评论追加成功，sent-summary 落盘（186 字符） |
| Step 10: fetch latest comment | ✅ 通过 | Remote 最新评论落盘（3032 字符） |
| **Step 10.5: 内容比对验证** | **✅ 通过** | **sent-summary（186 字符）完整出现在 remote comment（3032 字符）中** |

**比对特征**：
- 本地摘要稳定锚点：186 字符，纯文本，不含动态内容
- Remote 评论完整内容：3032 字符，含时间戳、commit hash、文件清单等动态内容
- 子字符串匹配：本地摘要作为精确子集完整出现在 Remote 评论中
