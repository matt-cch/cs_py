---
title: deploy-git-isolated 工具索引补全与 link_checker 修复方案评估
description: 完整梳理 py-tools 工具清单、补全 scripts/ 与 py-tools/ 目录导航，评估 link_checker 断链自动修复方案后决定回滚保留检测-only。
date: 2026-07-07
meta:
  version: 1.0.0
---

# deploy-git-isolated 工具索引补全与 link_checker 修复方案评估

> **Session 主题**：完整梳理 deploy-git-isolated task 的 Python Workflow 工具，补全缺失的目录自说明与导航联动，评估断链自动修复集成方案。  
> **日期**：2026-07-07  
> **文件名时间戳**：`2026-07-07-111204`  
> **触发原因**：用户要求分析 `references/tasks/deploy-git-isolated/scripts/py-tools/` 下的可用工具，发现此前总结遗漏了 12 个脚本  
> **影响范围**：`deploy-git-isolated` task 的文档导航体系、`link_checker` 插件能力边界  
> **风险等级**：低（纯文档索引补全 + 方案评估，无环境配置变更）


## 一、文本文件变更清单

### 1. 新建 `references/tasks/deploy-git-isolated/scripts/py-tools/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/README.md` |
| **变更类型** | `新建` |
| **内容** | py-tools/ 全部脚本清单（补全遗漏的 12 个）、py-plugins/ 34 个插件清单、三层调用规则（强调禁止越级 import）、Profile 速查表 |
| **作用** | 解决 py-tools/ 长期无自说明的问题，防止后续 Agent 重复遗漏工具 |
| **验证方式** | `run-lint.py --files <path>` → ✅ 全部通过 |
| **迁移方式** | 无需迁移，纯新增 |

### 2. 新建 `references/tasks/deploy-git-isolated/scripts/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/README.md` |
| **变更类型** | `新建` |
| **内容** | scripts/ 目录总览（PS / Python / JS 三线对称结构）、各层导航表、三层架构速查、上级导航 |
| **作用** | 串接 task/ → scripts/ → py-tools/ 三级导航 |
| **验证方式** | `run-lint.py --files <path>` → ✅ 全部通过 |
| **迁移方式** | 无需迁移，纯新增 |

### 3. 修改 `references/tasks/deploy-git-isolated/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/README.md` |
| **变更类型** | `修改`（导航表追加 2 行） |
| **新增内容** | 在「文件导航」表中追加 `scripts/README.md` 和 `scripts/py-tools/README.md` 两条索引 |
| **插入位置** | `scripts/EXEC-CHEATSHEET.md` 条目之后 |
| **作用** | 修订联动：task 层总索引指向新创建的 scripts 层索引 |
| **验证方式** | `run-lint.py --files <path>` → ✅ 全部通过 |
| **迁移方式** | 直接追加行 |

### 4. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/README.md` |
| **变更类型** | `修改`（修正上级导航链接） |
| **修改内容** | 「上级导航」中 `scripts/ 目录索引` 从纯文本改为链接 `../README.md`，指向刚创建的 `scripts/README.md` |
| **作用** | 修复因先写 py-tools/README.md 后写 scripts/README.md 导致的链接断裂 |
| **验证方式** | `run-lint.py --files <path>` → ✅ 全部通过 |
| **迁移方式** | 直接替换文本 |


## 二、非文本操作

无。本次 session 不涉及文件复制、缓存迁移、目录创建、环境变量变更、工具链安装等操作。


## 三、环境变量速查

无变更。`.vscode/settings.json` 未修改。


## 四、落盘验证

所有 `.md` 文件落盘后均执行了 `run-lint.py` 验证：

```powershell
& "${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" `
    --devroot "${devroot}" `
    --files "<文件路径>"
```

验证结果：✅ 全部通过（frontmatter / encoding / md_lint / link_checker）。


## 五、关键决策记录（link_checker 断链自动修复方案）

### 5.1 需求背景

用户提出：将 `link_checker` 的断链检测能力扩展为**自动修复**，当 `.md` 文件里的相对链接断裂时，自动在父子目录层级内搜索目标文件并修正链接。

### 5.2 尝试实现

在 `link_checker.py` 中新增了：
- `_find_candidate_in_devroot()`：在 devroot 下全局搜索候选文件（按文件名 + 目录结构）
- `_compute_relative_path()`：用 `Path.parents` 计算相对路径
- `validate_file(filepath, fix=True)`：检测后自动替换文本

在 `run-lint.py` 中将 `link_checker` 加入 `FIX_CAPABLE_PLUGINS`。

### 5.3 遇到的问题

| 问题 | 说明 |
|------|------|
| **候选歧义** | `README.md` 在 devroot 下有多个实例，全局搜索返回多个候选，难以确定唯一正确目标 |
| **层级错位** | `_find_candidate_at_parent_level()`（按 `..` 数量定位父目录）在测试中发现返回 None，因为父目录层级没有对应特征文件 |
| **双向一致性** | 用户指出「父子双向有效链接」才是真正的完整导航，而自动修复只能改子文件里的链接，无法同步更新父文件的导航表 |
| **职责边界** | 用户最终澄清：实际要的是「新建 README.md 时自动在父级 README.md 里追加导航表项」，不是「检测断裂链接后自动修复链接内容」 |

### 5.4 最终决策

**回滚 fix 逻辑，只保留检测。**

- `link_checker.py`：移除 `_find_candidate_in_devroot`、`_compute_relative_path`、fix 文本替换逻辑；`validate_file()` 恢复为无 `fix` 参数
- `run-lint.py`：`FIX_CAPABLE_PLUGINS` 恢复为 `{"lint_encoding", "md_lint"}`

**理由**：
1. 自动修复链接内容涉及全局搜索歧义、层级追溯策略、跨文件一致性，短期内无法做到可靠
2. 用户真正需要的是「新建 README 时更新父级导航表」，这是一个**目录维护工具**，不是 lint 修复
3. 保持 `link_checker` 的单一职责：只检测、只报告

### 5.5 后续建议

如需实现「新建 README 自动补全父级导航」，建议独立开发一个小工具（如 `ensure-readme-nav.py`），在 `write` 落盘后调用，而非耦合到 `run-lint --fix` 中。


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除新建文件 | `Remove-Item "references\tasks\deploy-git-isolated\scripts\py-tools\README.md"` |
| 删除新建文件 | `Remove-Item "references\tasks\deploy-git-isolated\scripts\README.md"` |
| 恢复 task README 导航表 | 从 `references/tasks/deploy-git-isolated/README.md` 中删除 `scripts/README.md` 和 `scripts/py-tools/README.md` 两行 |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-07-111204 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求分析 deploy-git-isolated 工具并补全索引 |
| **下次修订条件** | 当 py-tools/ 新增/删除脚本、或目录结构变化时同步更新 |
| **跨环境迁移参考** | 直接复制本文档，无环境依赖 |


*文档生成时间：2026-07-07-111204*  
*模板版本：v2*
