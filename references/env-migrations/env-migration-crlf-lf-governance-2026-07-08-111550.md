---
title: CRLF/LF 换行符治理 — lint 检测范围扩展与 .gitattributes 分层建设
description: lint_encoding.py 的 .json CRLF 漏检事件驱动，扩展 CRLF 强制检测范围（除 .ps1/.bat/.cmd 外全部文本文件），根级与 polyrepo 分层建立 .gitattributes，更新版本目录结构。
date: 2026-07-08
meta:
  version: "1.0.0"
  category: env-migration
---

# env-migration-crlf-lf-governance-2026-07-08-111550

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | CRLF/LF 换行符治理 — lint 检测范围扩展与 .gitattributes 分层建设 |
| **日期** | 2026-07-08 |
| **文件名时间戳** | `2026-07-08-111550` |
| **触发原因** | `verified-runtime-index.json` 更新后出现 462 处 CRLF，run-lint.py 显示 ❌ 但汇总报告判定为 0 违规，暴露 lint_encoding.py 对 .json 的 CRLF 不标记为 violation 的代码缺陷 |
| **影响范围** | lint_encoding.py（检测引擎）、.gitattributes（根级 + polyrepo）、venv/version/（目录结构）、update-version.py（NAME_MAP） |
| **风险等级** | 低（纯格式治理，不涉及业务代码或运行时工具链） |


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/lint_encoding.py` |
| **变更类型** | `修改` |
| **修改内容** | CRLF 检测逻辑从 `if ext in (".md", ".mdc")` 改为 `if ext not in {".ps1", ".bat", ".cmd"}` |
| **插入位置** | `_check_encoding()` 函数，第 87-90 行附近 |
| **作用** | 除 .ps1/.bat/.cmd 外，所有文本文件的 CRLF 均被标记为 violation 并可自动修复 |
| **验证方式** | `run-lint.py --files venv/tmp/test-crlf-fix.json --fix` 三阶段闭环通过 |
| **迁移方式** | 直接覆盖 |

### 2. 新建 `D:\pjt\cursor\cs_py\.gitattributes`

| 属性 | 值 |
|------|-----|
| **路径** | `.gitattributes`（devroot 根级） |
| **变更类型** | `新建` |
| **新增内容** | `* text eol=lf` + `.ps1/.bat/.cmd -text` 豁免 + 二进制文件 binary 声明 |
| **作用** | 根级 Git 换行符强制：所有文本文件 checkout 时保持 LF，.ps1 等 Windows 原生脚本不参与转换 |
| **验证方式** | `git check-ignore -v .gitattributes` 确认被排除（预期：不跟踪，仅供本地） |
| **迁移方式** | 直接复制到目标环境根级 |

> **注意**：本文件不随仓库跟踪（被 .gitignore 的 `/*` 排除），仅供本地开发使用。

### 3. 新建 `apps/repos/jywl-team/jywl-lab/.gitattributes`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/repos/jywl-team/jywl-lab/.gitattributes` |
| **变更类型** | `新建` |
| **新增内容** | 与根级 .gitattributes 内容一致 |
| **作用** | jywl-lab 独立仓库的 LF 强制配置，与 cs_py 根级相互独立 |
| **验证方式** | `Get-ChildItem` 确认文件存在 |
| **迁移方式** | 直接复制到 jywl-lab 根级 |

> **注意**：jywl-lab 是嵌套独立仓库（有自己的 .git/），根级 .gitattributes 对它无效。必须在 jywl-lab 内部单独建立。

### 4. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `修改`（CRLF → LF） |
| **修改内容** | 462 处 CRLF 换行符替换为 LF |
| **作用** | 消除换行符污染，符合 lint 合规标准 |
| **验证方式** | `run-lint.py --files verified-runtime-index.json` → CRLF=0, LF=462 |
| **迁移方式** | 已由工具 --fix 自动修复 |

> **教训**：初始修复时 Agent 错误地用手动 PowerShell 字节操作替换，后被用户纠正。正确路径应为 `run-lint.py --fix` 让工具自治修复。

### 5. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/update-version.py` |
| **变更类型** | `修改` |
| **修改内容** | NAME_MAP 追加 `"gh": "gh_cli"` 映射 |
| **作用** | 使 `venv/version/gh.md` 能正确映射到 `tools_config.json` 中的 `gh_cli` 配置 |
| **验证方式** | `run-lint.py` Python 语法通过 |
| **迁移方式** | 直接覆盖 |

### 6. 新建 `venv/version/git.md` 与 `venv/version/git-history.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/git.md` / `venv/version/git-history.md` |
| **变更类型** | `新建` |
| **新增内容** | Git 版本记录（当前 2.55.0.windows.2）+ 变更历史基线 |
| **作用** | 补全 update-version.py 的检测驱动列表 |
| **验证方式** | `run-lint.py` md_lint + lint_encoding 通过 |
| **迁移方式** | 直接复制 |

### 7. 新建 `venv/version/gh.md` 与 `venv/version/gh-history.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/gh.md` / `venv/version/gh-history.md` |
| **变更类型** | `新建` |
| **新增内容** | GitHub CLI 版本记录（当前 2.96.0）+ 变更历史基线 |
| **作用** | 补全 update-version.py 的检测驱动列表 |
| **验证方式** | `run-lint.py` md_lint + lint_encoding 通过 |
| **迁移方式** | 直接复制 |

### 8. 新建 `venv/version/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `venv/version/README.md` |
| **变更类型** | `新建` |
| **新增内容** | 版本目录自说明：工具导航表 + 新增工具流程 + NAME_MAP 映射规则 |
| **作用** | 消除版本目录无导航的问题，指导后续新增工具时的 NAME_MAP 维护 |
| **验证方式** | `run-lint.py` md_lint + lint_encoding 通过 |
| **迁移方式** | 直接复制 |

### 9. 新建 `references/tasks/deploy-git-isolated/docs/research/crlf-lf-line-ending-governance-research-2026-07-08-111237.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/research/crlf-lf-line-ending-governance-research-2026-07-08-111237.md` |
| **变更类型** | `新建` |
| **新增内容** | 换行符治理深度研究报告：各文件类型规范、系统默认行为、.gitattributes 作用域、core.autocrlf 机制、两个独立 .git 的差异化影响 |
| **作用** | 沉淀本次深度研究的全部证据与决策路径，供后续 Agent/Human 参考 |
| **验证方式** | `run-lint.py` md_lint + lint_encoding 通过 |
| **迁移方式** | 直接复制 |

### 10. 修改 `references/tasks/deploy-git-isolated/docs/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/docs/README.md` |
| **变更类型** | `修改` |
| **修改内容** | 导航表追加 `crlf-lf-line-ending-governance-research-2026-07-08-111237.md` 条目，版本 v1.4 → v1.5 |
| **作用** | 目录导航联动 |
| **验证方式** | `run-lint.py` md_lint + lint_encoding + link_checker 通过 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作

本次 session **不涉及**文件复制、缓存迁移、目录创建等无法被 git 追踪的操作。


## 三、环境变量速查

无新增或变更的环境变量。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `run-lint.py --fix` | frontmatter、CRLF/LF、BOM、链接 | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0, frontmatter 合规 |
| `.py`（lint_encoding.py / update-version.py） | `run-lint.py` | Python 语法 + 编码 | py_compile 通过 |
| `.json`（verified-runtime-index.json） | `run-lint.py` | JSON 语法 + 编码 | JSON 解析通过, CRLF=0 |

**执行结果**：全部通过，0 违规。


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 lint_encoding.py 语法正确 | `python -m py_compile lint_encoding.py` | 无输出（通过） |
| 2 | 确认 .json CRLF 可被检测并修复 | 新建含 CRLF 的 test.json，执行 `run-lint.py --fix` | 修复后 CRLF=0, LF>0 |
| 3 | 确认 .ps1 不被强制 LF | 新建含 CRLF 的 test.ps1，执行 `run-lint.py` | 不报告 CRLF 违规 |
| 4 | 确认根级 .gitattributes 存在 | `Test-Path ".gitattributes"` | `True` |
| 5 | 确认 jywl-lab 独立 .gitattributes 存在 | `Test-Path "apps/repos/jywl-team/jywl-lab/.gitattributes"` | `True` |
| 6 | 确认 venv/version/ 新增文件完整 | `Get-ChildItem venv/version/*.md` | 包含 git.md / gh.md / README.md 及其 history |
| 7 | 确认 docs/research/ 导航已更新 | 读取 `docs/README.md` 搜索 `crlf-lf` | 存在对应条目 |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 lint_encoding.py | `git checkout -- scripts/py-plugins/lint_encoding.py` |
| 删除根级 .gitattributes | `Remove-Item ".gitattributes"` |
| 删除 jywl-lab .gitattributes | `Remove-Item "apps/repos/jywl-team/jywl-lab/.gitattributes"` |
| 删除 venv/version 新增文件 | `Remove-Item "venv/version/git.md"`、`git-history.md`、`gh.md`、`gh-history.md`、`README.md` |
| 恢复 update-version.py NAME_MAP | `git checkout -- scripts/py-tools/update-version.py` |
| 恢复 docs/README.md | `git checkout -- docs/README.md` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-08-111550 |
| **更新人** | Human + Agent Session |
| **变更触发** | verified-runtime-index.json CRLF 漏检事件 → 全面换行符治理 |
| **下次修订条件** | 新增文件类型需要调整 CRLF 豁免列表、.gitattributes 需要扩展二进制豁免 |
| **跨环境迁移参考** | 直接复制 lint_encoding.py + .gitattributes + venv/version/*.md + 按「验证清单」逐条执行 |


*文档生成时间：2026-07-08*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*