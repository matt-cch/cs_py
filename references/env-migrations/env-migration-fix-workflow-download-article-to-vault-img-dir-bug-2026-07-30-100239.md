---
title: 修复 workflow-download-article-to-vault 无图片场景崩溃
description: workflow-download-article-to-vault.py 在无图片时 step3_verify 返回 Path()（当前目录），导致 step6_move 中 shutil.move 误将当前目录移入目标而崩溃。
date: 2026-07-30
meta: {}
---

# env-migration-fix-workflow-download-article-to-vault-img-dir-bug-2026-07-30-100239

> **Session 主题**：修复 `workflow-download-article-to-vault.py` 无图片场景下的 `shutil.move` 崩溃 bug
> **受众**：Human + Agent。在新环境复现修复时，直接按「文本文件变更清单」执行即可。

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 修复 `workflow-download-article-to-vault.py` 无图片场景崩溃 bug |
| **日期** | 2026-07-30 |
| **文件名时间戳** | `2026-07-30-100239` |
| **触发原因** | 执行头条文章下载 workflow 时，无图片文章在 Step 6/8 报 `shutil.Error: Destination path ... already exists` |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py` 单行修复 |
| **风险等级** | 低（仅修复空图片场景的边缘 bug，不改变正常有图片流程） |

## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/workflow-download-article-to-vault.py` |
| **变更类型** | `修改` |
| **修改内容** | `return True, "", img_dir or Path(), img_count` → `return True, "", img_dir, img_count` |
| **插入位置** | `step3_verify` 函数末尾（约第 167 行） |
| **作用** | 当文章无图片时，`img_dir` 为 `None`，原代码 `img_dir or Path()` 会回退到 `Path()`（即当前目录 `.`），导致后续 `step6_move` 调用 `shutil.move(str(img_dir), str(target_dir))` 时试图移动当前目录，触发 `shutil.Error`。修复后保留 `None`，`step6_move` 中已存在 `if img_dir and img_dir.exists():` 判断，可正确跳过。 |
| **验证方式** | 执行无图片的头条文章下载 workflow，Step 6/8 应通过，不再抛出 `shutil.Error` |
| **迁移方式** | 直接按「修改内容」替换单行即可 |

## 二、非文本操作

本次 session 不涉及文件系统/缓存迁移等非文本操作。

## 三、环境变量速查

本次 session 不涉及环境变量变更。

## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `check-file-encoding.ps1` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |

执行示例：
```powershell
"${devroot}\venv\py\python.exe" "${devroot}\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "${devroot}" --files "${devroot}\references\env-migrations\env-migration-fix-workflow-download-article-to-vault-img-dir-bug-2026-07-30-100239.md"
```

## 五、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认修复已落盘 | 打开 `workflow-download-article-to-vault.py` 第 167 行 | 内容为 `return True, "", img_dir, img_count` |
| 2 | 复现无图片文章下载 | 执行 workflow 下载一篇无图片的头条文章 | Step 6/8 通过，无 `shutil.Error` |

## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 还原单行修改 | 将 `return True, "", img_dir, img_count` 改回 `return True, "", img_dir or Path(), img_count` |

## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-30-100239 |
| **更新人** | Human + Agent Session |
| **变更触发** | 头条文章下载 workflow 在无图片场景下崩溃 |
| **下次修订条件** | 若 `step3_verify` 逻辑再次调整 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
