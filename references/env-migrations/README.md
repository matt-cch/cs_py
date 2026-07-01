---
title: references/env-migrations — 环境配置变更记录（一次性交接单）
description: 存放单次 session 的环境级变更清单，供新开发环境复现后归档。与 changelog/（跨 session 时间线）区分。
date: 2026-06-02
meta: {}
---

# `references/env-migrations/` — 环境配置变更记录

本目录存放 **单次 session 的环境级变更清单**（env-migration），格式统一为 `env-migration-<主题>-YYYY-MM-DD-HHmmss.md`（秒级时间戳，便于同日多场 session 区分）。模板见 [`schema/structure/env-migration-template.md`](../../schema/structure/env-migration-template.md)。

## 与其他文档类型的区分

| 类型 | 存放位置 | 内容 | 生命周期 |
|------|---------|------|---------|
| **env-migration** | `references/env-migrations/` | 单次 session 的全部环境变更（文件 + 非文本操作 + 验证清单） | 一次性，迁移完成后归档 |
| **changelog** | `references/changelog/` | 跨 session 的 Monorepo 环境变更时间线 | 持续追加 |
| **handoff** | `docs/` 或项目笔记 | 跨 session 的业务功能交付上下文 | 持续追加 |

> 命名规范详见 `schema/structure/doc-naming-conventions.md`。

## 文件导航

| 文件 | 主题 | 日期 |
|------|------|------|
| [env-migration-opencode-cache-2026-05-31.md](env-migration-opencode-cache-2026-05-31.md) | OpenCode 缓存隔离修正（`XDG_CACHE_HOME`） | 2026-05-31 |
| [env-migration-doc-naming-standards-2026-05-31.md](env-migration-doc-naming-standards-2026-05-31.md) | 文档命名规范与 env-migration 模板建设 | 2026-05-31 |
| [env-migration-schema-tool-write-helper-ini-support-2026-06-01.md](env-migration-schema-tool-write-helper-ini-support-2026-06-01.md) | file-write-helper INI 配置支持与 schema/tool 清理 | 2026-06-01 |
| [env-migration-agent-long-content-two-hop-2026-06-02-164241.md](env-migration-agent-long-content-two-hop-2026-06-02-164241.md) | Agent 长内容分步写入（先 content.txt 再 helper）、Shell/`python -c` 边界、UTF-8 BOM | 2026-06-02-164241 |
| [env-migration-slides-skill-and-file-write-helper-2026-06-02-173559.md](env-migration-slides-skill-and-file-write-helper-2026-06-02-173559.md) | Slides Skill（PptxGenJS）评估、`module.paths.unshift()` 依赖注入发现、file-write-helper 工作流集中化 + AGENTS.md 触发链路 | 2026-06-02-173559 |
| [env-migration-runtime-download-modularization-2026-06-03-175439.md](env-migration-runtime-download-modularization-2026-06-03-175439.md) | runtime 下载脚本模块化重构（单文件 696 行 → 4 模块）+ Python 指定版本下载支持 | 2026-06-03-175439 |
| [env-migration-runtime-download-proxy-routing-2026-06-04-111336.md](env-migration-runtime-download-proxy-routing-2026-06-04-111336.md) | runtime 下载脚本代理支持 + 智能路由探测 + 脚本精简（422 行 → 246 行） | 2026-06-04-111336 |
| [env-migration-runtime-verification-agents-alignment-2026-06-04-155721.md](env-migration-runtime-verification-agents-alignment-2026-06-04-155721.md) | 真源检测 + AGENTS.md 与 PROJECT-STRUCTURE 对齐 + 新增 schema | 2026-06-04-155721 |
| [env-migration-tree-sitter-article-pipeline-2026-06-04-175042.md](env-migration-tree-sitter-article-pipeline-2026-06-04-175042.md) | Tree-sitter 知识体系梳理 + 网页文章提取工具链建设 | 2026-06-04-175042 |
| [env-migration-verify-runtime-trigger-migration-2026-06-05-094059.md](env-migration-verify-runtime-trigger-migration-2026-06-05-094059.md) | 真源检测触发链路从 AGENTS.md 迁移到 .mdc 规则文件 | 2026-06-05-094059 |
| [env-migration-md-format-plugin-and-shell-ban-2026-06-05-141555.md](env-migration-md-format-plugin-and-shell-ban-2026-06-05-141555.md) | Markdown 格式规则强化 + OpenCode Plugin 实验 + Shell 长内容禁令 | 2026-06-05-141555 |
| [env-migration-opencode-cli-upgrade-2026-06-05-142431.md](env-migration-opencode-cli-upgrade-2026-06-05-142431.md) | OpenCode CLI 1.15.13 → 1.16.0 升级准备 + Agent 行为失误复盘 | 2026-06-05-142431 |
| [env-migration-verify-runtime-plugin-exploration-2026-06-05-151500.md](env-migration-verify-runtime-plugin-exploration-2026-06-05-151500.md) | 真源实测更新 + OpenCode Plugin Hook 机制深度验证与功能探索 | 2026-06-05-151500 |
| [env-migration-runtime-index-update-and-upstream-check-2026-06-05-215108.md](env-migration-runtime-index-update-and-upstream-check-2026-06-05-215108.md) | 真源索引更新 + Node.js / Chromium 上游检测下载 + Cursor 路径修正 | 2026-06-05-215108 |
| [env-migration-shell-ban-rulesystem-and-gotcha-infra-2026-06-06-084200.md](env-migration-shell-ban-rulesystem-and-gotcha-infra-2026-06-06-084200.md) | Shell 禁令规则体系重构 + 高频任务 .mdc 拆分 + gotcha 基础设施 | 2026-06-06-084200 |
| [env-migration-sentinel-verification-rulesystem-2026-06-06-110325.md](env-migration-sentinel-verification-rulesystem-2026-06-06-110325.md) | 哨兵验证规则体系建设（Playbook + 模板）与 sentinel-test 测试实例退役准备 | 2026-06-06-110325 |
| [env-migration-playwright-chrome-session-extension-2026-06-08-080427.md](env-migration-playwright-chrome-session-extension-2026-06-08-080427.md) | Playwright + Chrome 持久化 Session + 扩展自动化工具链（异步事件驱动、7 个踩坑记录） | 2026-06-08-080427 |
| [env-migration-tavily-cli-toolchain-2026-06-08-164500.md](env-migration-tavily-cli-toolchain-2026-06-08-164500.md) | tavily-cli 工具链接入、.env 环境变量配置、真源检测结构扩展 | 2026-06-08-164500 |
| [env-migration-tongxin-power-dynamic-reading-report-2026-06-09-162535.md](env-migration-tongxin-power-dynamic-reading-report-2026-06-09-162535.md) | tongxin-power 动态读数报表与模块化脚本建设（v1→v6 演进、渐进式读数、差异检测） | 2026-06-09-162535 |
| [env-migration-cursor-version-verification-workflow-2026-06-10-122635.md](env-migration-cursor-version-verification-workflow-2026-06-10-122635.md) | Cursor 版本检测流程标准化（cursor.cmd --version 两步验证）+ 工具版本记录更新 | 2026-06-10-122635 |
| [env-migration-tool-shell-audit-and-schema-index-2026-06-10-142912.md](env-migration-tool-shell-audit-and-schema-index-2026-06-10-142912.md) | Tool/Shell 调用规则层审计机制 + 渐进式真源索引体系（task-index + schema-index）建设 | 2026-06-10-142912 |
| [env-migration-trigger-index-governance-2026-06-10-155422.md](env-migration-trigger-index-governance-2026-06-10-155422.md) | 触发条件索引治理体系建设（governance_rules + 来源文件引用说明 + AGENTS.md 治理规则章节） | 2026-06-10-155422 |
| [env-migration-tangbiao-may-report-pptx-and-image-toolchain-2026-06-10-220000.md](env-migration-tangbiao-may-report-pptx-and-image-toolchain-2026-06-10-220000.md) | 唐彪5月工作报告PPT生成（v1→v4）+ references/scripts/ 图片工具链建设 | 2026-06-10-220000 |
| [env-migration-encoding-boilerplate-and-mdc-linkage-2026-06-10-234043.md](env-migration-encoding-boilerplate-and-mdc-linkage-2026-06-10-234043.md) | 编码样板补齐与 mdc→ps1 联动链路建立：3 个 .ps1 追加编码样板，4 个 .mdc 追加引用 | 2026-06-10-234043 |
| [env-migration-verify-runtime-cursor-cmd-fix-2026-06-11-105830.md](env-migration-verify-runtime-cursor-cmd-fix-2026-06-11-105830.md) | verify-runtime.ps1 cursor.cmd 联动检测修复 + 头部注释规范化 | 2026-06-11-105830 |
| [env-migration-version-scripts-2026-06-11-121009.md](env-migration-version-scripts-2026-06-11-121009.md) | 版本获取脚本体系建立（5 个 .ps1）+ 编码修复 + mdc 引用更新 | 2026-06-11-121009 |
| [env-migration-version-scripts-and-encoding-2026-06-11-173900.md](env-migration-version-scripts-and-encoding-2026-06-11-173900.md) | 版本获取脚本体系扩展 + PS1模板建设 + 编码恢复修复 | 2026-06-11-173900 |
| [env-migration-reliable-backup-2026-06-13-151421.md](env-migration-reliable-backup-2026-06-13-151421.md) | 7z Zip 可靠备份方案验证（scan-for-backup.py + 修复 2 个 bug + 验证通过） | 2026-06-13-151421 |
| [env-migration-llama-cpp-python-and-verify-runtime-fix-2026-06-14-223000.md](env-migration-llama-cpp-python-and-verify-runtime-fix-2026-06-14-223000.md) | llama-cpp-python 运行时检测扩展 + verify-runtime candidate 联动修复 | 2026-06-14-223000 |
| [env-migration-verify-runtime-python-modularization-2026-06-15-132000.md](env-migration-verify-runtime-python-modularization-2026-06-15-132000.md) | verify-runtime 重构为模块化 Python 架构 + Chromium 上游源修正 + Python <3.14 约束 | 2026-06-15-132000 |
| [env-migration-task-template-system-2026-06-15-173500.md](env-migration-task-template-system-2026-06-15-173500.md) | task-template 任务模板体系建设（7 个骨架 + 6 个调用脚本 + 文档/配置模板） | 2026-06-15-173500 |
| [env-migration-chrome-upstream-refactor-and-changelog-audit-2026-06-16-151000.md](env-migration-chrome-upstream-refactor-and-changelog-audit-2026-06-16-151000.md) | Chromium 上游查询逻辑重构 + Changelog 规则修正 + Audit 自检机制建立 | 2026-06-16-151000 |
| [env-migration-deploy-git-isolated-complete-2026-06-16-173853.md](env-migration-deploy-git-isolated-complete-2026-06-16-173853.md) | deploy-git-isolated 隔离 Git 部署任务完整建设与文档体系完善（MinGit + HOME 重定向 + GitHub push + Subagent 自包含验证） | 2026-06-16-173853 |
| [env-migration-python-c-ban-fix-and-git-lib-enhance-2026-06-16-211721.md](env-migration-python-c-ban-fix-and-git-lib-enhance-2026-06-16-211721.md) | python-backend-loc.mdc python-c 禁令修正 + git-lib 检测增强（Test-IsolatedGit 返回状态对象） | 2026-06-16-211721 |
| [env-migration-deploy-git-encoding-fix-and-bom-2026-06-16-231008.md](env-migration-deploy-git-encoding-fix-and-bom-2026-06-16-231008.md) | deploy-git-isolated 脚本中文乱码修复与 BOM 补齐 | 2026-06-16-231008 |
| [env-migration-playwright-toutiao-articles-and-git-ops-2026-06-16-143500.md](env-migration-playwright-toutiao-articles-and-git-ops-2026-06-16-143500.md) | Playwright 头条文章批量提取 + 三篇技术文章阅读分析 + Git 持久化模式梳理 | 2026-06-16-143500 |
| [env-migration-deploy-git-isolated-github-publish-2026-06-17-013059.md](env-migration-deploy-git-isolated-github-publish-2026-06-17-013059.md) | deploy-git-isolated task 发布到 GitHub（白名单 .gitignore + LF 强制 + 动态探测 + Issue 自动化） | 2026-06-17-013059 |
| [env-migration-llama-cpp-python-version-pin-and-download-script-2026-06-17-124500.md](env-migration-llama-cpp-python-version-pin-and-download-script-2026-06-17-124500.md) | llama-cpp-python 版本固定与 Python 下载脚本建设（0.3.22 兼容性分界 + download-runtime-tool.py 新建） | 2026-06-17-124500 |
| [env-migration-deploy-git-issue-sync-and-profile-filter-2026-06-17-175500.md](env-migration-deploy-git-issue-sync-and-profile-filter-2026-06-17-175500.md) | deploy-git-isolated 扩展 — Issue 同步体系（github-api 插件 + 同步入口）与 Profile 筛选机制（三层筛选 + 依赖自动补齐） | 2026-06-17-175500 |
| [env-migration-deploy-git-py-steps-and-workflow-validation-2026-06-20-060000.md](env-migration-deploy-git-py-steps-and-workflow-validation-2026-06-20-060000.md) | deploy-git-isolated Python 步骤脚本化（Step 5-9）+ workflow 全链路编排验证 | 2026-06-20-060000 |
| [env-migration-runtime-verify-download-fix-and-workflow-arch-clarity-2026-06-21-103444.md](env-migration-runtime-verify-download-fix-and-workflow-arch-clarity-2026-06-21-103444.md) | runtime 检测下载修复 + workflow 架构明晰（candidate_paths 兜底、download 切 py、三层+配置契约、archive 迁入 py-lib） | 2026-06-21-103444 |
| [env-migration-archive-workflow-v2-enhancement-2026-06-21-143000.md](env-migration-archive-workflow-v2-enhancement-2026-06-21-143000.md) | 归档工作流 v2 增强（空目录检测 + audit + 模式语法统一 + 插件间 import 规则） | 2026-06-21-143000 |
| [env-migration-verify-runtime-lint-unified-and-timestamp-plugin-2026-06-21-144609.md](env-migration-verify-runtime-lint-unified-and-timestamp-plugin-2026-06-21-144609.md) | 真源检测验证统一化 + timestamp 插件体系 + py-tools 原子型/编排型分层 | 2026-06-21-144609 |
| [env-migration-version-update-python-migration-2026-06-22-112000.md](env-migration-version-update-python-migration-2026-06-22-112000.md) | 版本记录更新 Python 化迁移（runtime_version 插件 + update-version Workflow + 4 文档修订联动） | 2026-06-22-112000 |
| [env-migration-nanobot-agent-and-security-audit-2026-06-22-174549.md](env-migration-nanobot-agent-and-security-audit-2026-06-22-174549.md) | nanobot Agent 底层能力 + 安全审计工具体系 + 命名规范固化（workflow-/atomic- 前缀 + Phase/Atomic/Workflow 边界 + 产出文件默认落盘 venv/tmp/） | 2026-06-22-174549 |
| [env-migration-run-lint-routing-fix-and-archive-timeout-analysis-2026-06-23-180826.md](env-migration-run-lint-routing-fix-and-archive-timeout-analysis-2026-06-23-180826.md) | run-lint.py 路由修复（.md 双重检查）+ docs/ CRLF 批量修复 + archive 超时根因分析 + Agent 目录阅读模式文档 | 2026-06-23-180826 |
| [env-migration-lint-system-upgrade-2026-06-24-112406.md](env-migration-lint-system-upgrade-2026-06-24-112406.md) | lint 体系升级：link_checker/py-sort-rules/py_lib/run-lint 版本升级、新增 lint-rules-manifest.json、AGENTS.md 思考语言锚定、入口文件修订联动 | 2026-06-24-112406 |
| [env-migration-deploy-git-auto-deploy-and-auth-fix-2026-06-24-054242.md](env-migration-deploy-git-auto-deploy-and-auth-fix-2026-06-24-054242.md) | deploy-git-isolated 自动部署完善与 GitHub 认证弹窗修复（--auto / GCM 阻断 / Cursor 扩展 / Popen 死锁 / upstream 超时） | 2026-06-24-054242 |
| [env-migration-archive-cs-py-venv-zip-2026-06-24-175445.md](env-migration-archive-cs-py-venv-zip-2026-06-24-175445.md) | cs_py + venv 归档验证（zip 格式，40635文件381MB + 7252文件25MB 全部通过） | 2026-06-24-175445 |
| [env-migration-archive-toolchain-enhance-and-7z-revert-2026-06-25-121658.md](env-migration-archive-toolchain-enhance-and-7z-revert-2026-06-25-121658.md) | 归档工具链增强与默认值勘误（7z 回退 + 实时进度 + TOP20 卡点） | 2026-06-25-121658 |
| [env-migration-workflow-self-contained-execution-2026-06-25-142208.md](env-migration-workflow-self-contained-execution-2026-06-25-142208.md) | Workflow 自闭环执行铁律固化与部署脚本文档增强 | 2026-06-25-142208 |
| [env-migration-git-emptydir-preflight-2026-06-25-162358.md](env-migration-git-emptydir-preflight-2026-06-25-162358.md) | Git 空目录保留归并 preflight + get-timestamp 参数勘误 | 2026-06-25-162358 |
| [env-migration-download-article-preflight-2026-06-25-172700.md](env-migration-download-article-preflight-2026-06-25-172700.md) | download-article.py 增加 Preflight 检查与头条 URL 验证 | 2026-06-25-172700 |
| [env-migration-runtime-atomic-refactor-2026-06-26-231301.md](env-migration-runtime-atomic-refactor-2026-06-26-231301.md) | 运行时域原子脚本重构（verify-runtime / download-runtime-tool → task 插件体系） | 2026-06-26-231301 |
| [env-migration-lint-and-runtime-download-system-v2-2026-06-29-171635.md](env-migration-lint-and-runtime-download-system-v2-2026-06-29-171635.md) | lint 工具链升级与运行时下载体系 v2.0 重构（list_upstream_versions plugin + version_constraint 约束机制） | 2026-06-29-171635 |
| [env-migration-lint-toolchain-upgrade-and-feiliks-docs-2026-06-29-151658.md](env-migration-lint-toolchain-upgrade-and-feiliks-docs-2026-06-29-151658.md) | lint 工具链升级（md_lint v1.2.1 + lint_encoding v1.1.0 + lint_ps1 修复）与 FEILIKS 文档沉淀 | 2026-06-29-151658 |
| [env-migration-feiliks-invoice-csv-toolchain-2026-06-29-145157.md](env-migration-feiliks-invoice-csv-toolchain-2026-06-29-145157.md) | FEILIKS FAPINV 发票 CSV 工具链建设补录（xlsx→csv + 白名单过滤 + 日期更新） | 2026-06-29-145157 |
| [env-migration-gh-cli-runtime-toolchain-generalization-2026-06-30-113721.md](env-migration-gh-cli-runtime-toolchain-generalization-2026-06-30-113721.md) | gh_cli 集成与运行时工具链泛化重构（GitHub Release 通用查询 + choices 动态化） | 2026-06-30-113721 |
| [env-migration-gh-cli-pr-merge-automation-2026-06-30-173228.md](env-migration-gh-cli-pr-merge-automation-2026-06-30-173228.md) | gh CLI 隔离部署与 PR merge 自动化闭环建设（分支保护 + .gitignore 收紧 + autocrlf 修正） | 2026-06-30-173228 |


## 上级导航
- [references 总索引](../README.md)
- [devroot 目录结构](../../docs/architecture/engineering-metadata-and-docs-practices.md)
