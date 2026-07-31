---
title: vaults/ polyvaults 工程上下文知识库架构建设 + 文章下载 workflow 固化
description: vaults/ 骨架建立、vault-demo/ 模板建设、download-article workflow 完成了从手动 8 步到自动化脚本的闭环，含 3 次实测
date: 2026-07-29
meta: {}
---

# vaults/ polyvaults 工程上下文知识库架构建设 + 文章下载 workflow 固化

## 元信息

| 字段 | 值 |
|------|-----|
| **Session 主题** | vaults/ polyvaults 知识库骨架建设 + workflow-download-article-to-vault 脚本固化 |
| **日期** | 2026-07-29 |
| **文件名时间戳** | `2026-07-29-153113` |
| **触发原因** | 用户在 cs_py 下建立 vaults/ 知识库架构，需从 vault-cloud（PascalCase）迁移设计并适配新规范 |
| **影响范围** | vaults/ 骨架、vault-demo/ 模板、download-article 工具链、workflow 编排脚本 |
| **风险等级** | 低（不涉及业务代码，纯工程上下文组织） |

## 一、文本文件变更清单

### 1. 新建 vaults/ 骨架（父级 + baseline）

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/README.md` |
| **变更类型** | 新建 |
| **作用** | vaults/ 父级总索引，说明 raw + wiki 二元结构 |

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/baseline/README.md` |
| **变更类型** | 新建 |
| **作用** | baseline 目录索引 |

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/baseline/baseline-md-format.md` |
| **变更类型** | 新建 |
| **作用** | 跨 vault Markdown 格式 baseline（YAML frontmatter、`---` 禁令、LF、UTF-8 无 BOM） |

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/baseline/baseline-naming-convention.md` |
| **变更类型** | 新建 |
| **作用** | 跨 vault 命名规范 baseline（kebab-case、category-slug 格式、短戳/长戳） |

### 2. 新建 vault-demo/ 完整模板目录

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/README.md` |
| **变更类型** | 新建 |
| **作用** | vault-demo 模板根自说明，含完整 15 子目录结构 |

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/projects/DESIGN.md` |
| **变更类型** | 新建 |
| **作用** | 项目级设计基准模板 |

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/baseline/baseline-clippings-source-tracking.md` |
| **变更类型** | 新建 |
| **作用** | 剪藏来源追踪 baseline |

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/conclusions/conclusion-preflight-as-tool-logic.md` |
| **变更类型** | 新建 |
| **作用** | preflight 应内嵌为工具代码逻辑结论 |

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/wiki/insights/insight-article-download-directory-layout.md` |
| **变更类型** | 新建 |
| **作用** | 单文章子目录模式洞见 |

**其余 10 个子目录 README.md**：
- `raw/README.md`、`raw/ingests/README.md`、`raw/clippings/README.md`、`raw/notes/README.md`
- `wiki/README.md`、`wiki/entities/README.md`、`wiki/learnings/README.md`、`wiki/researches/README.md`、`wiki/snapshots/README.md`

### 3. 新建 workflow-download-article-to-vault.py

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py` |
| **变更类型** | 新建 |
| **作用** | 编排「文章下载 → 产物验证 → Vault 目录整理 → 导航更新」完整 8 步闭环 |
| **版本** | v1.0.0 |
| **验证方式** | 3 次实测通过（6 张/16 张/11 张图片） |

### 4. 修改 vault-demo/raw/clippings/README.md

| 属性 | 值 |
|------|-----|
| **路径** | `vaults/vault-demo/raw/clippings/README.md` |
| **变更类型** | 追加导航表 |
| **新增内容** | `## 剪藏列表` 导航表（含 3 条剪藏记录） |
| **作用** | workflow 自动更新的导航索引 |

## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 目录创建 | — | `vaults/vault-demo/raw/clippings/{slug}/` | Step 5 自动创建子目录（3 次） |
| 文件移动 | `venv/tmp/article-download-{ts}/` | `vaults/vault-demo/raw/clippings/{slug}/` | Step 6 整目录移入（3 次） |

## 三、环境变量速查

本次无环境变量变更。

## 四、架构决策记录

| 决策 | 内容 |
|------|------|
| raw + wiki 二元结构 | `raw/` 收束未加工素材（ingests/clippings/notes），`wiki/` 沉淀已加工知识（projects/entities/insights/learnings/conclusions/researches/snapshots） |
| kebab-case | 全目录名 kebab-case，与 vault-cloud（PascalCase）区分 |
| 单文章子目录 | `download-article.py` 产物整目录移入 `raw/clippings/{slug}/`，不改工具自身逻辑 |
| preflight 内嵌工具 | 工具负责自检，Agent 负责调用与结果判断，不手动执行 preflight |
| workflow 自持 | 8 步流程固化为单一 Python 脚本，含 dry-run 模式 |

## 五、落盘验证

| 文件 | 验证工具 | 状态 |
|------|---------|------|
| `workflow-download-article-to-vault.py` | `run-lint.py`（lint_python + lint_encoding） | ✅ 通过 |

## 六、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | workflow 下载测试（第 1 次） | `--url "https://www.toutiao.com/article/7667463102308286991/"` | ✅ 6 张图片，全部通过 |
| 2 | workflow 下载测试（第 2 次） | `--url "https://www.toutiao.com/article/7667478307952247296/"` | ✅ 16 张图片，全部通过 |
| 3 | workflow 下载测试（第 3 次） | `--url "https://www.toutiao.com/article/7667012700145041961/"` | ✅ 11 张图片，全部通过 |
| 4 | 导航表自动追加 | 查看 `raw/clippings/README.md` | ✅ 3 条记录，格式正确 |
| 5 | 剪藏 frontmatter 合规 | 各 `.md` 文件 | ✅ title/description/date/source/tags 齐全 |

## 七、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 vaults/ 骨架 | `Remove-Item -Recurse "vaults/"` |
| 删除 workflow 脚本 | `Remove-Item "references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py"` |
| 删除剪藏产物 | `Remove-Item -Recurse "vaults/vault-demo/raw/clippings/"` |

## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-29-153113 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求建立 vaults/ 工程上下文知识库 + 文章下载自动化 |
| **下次修订条件** | 新增 vault（如 vault-v2）或 workflow 流程变更 |
| **跨环境迁移参考** | 复制 `vaults/` + `workflow-download-article-to-vault.py` 即可复用 |
