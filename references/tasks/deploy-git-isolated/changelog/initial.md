---
title: deploy-git-isolated 初始变更记录
description: 任务骨架创建，设计文档定稿，待进入 Step 脚本填充阶段。
date: 2026-06-16
---

# deploy-git-isolated 变更记录

## v0.1 — 骨架创建（2026-06-16）

### 新增

- 创建 `references/tasks/deploy-git-isolated/` 目录结构。
- 编写 `DESIGN.md`：确定全路径调用 + HOME 重定向隔离机制，选定 MinGit 发行版。
- 编写 `ENTRY.json`：机器可读入口，登记 6 步骨架脚本（状态均为 pending）。
- 编写 `task-config.json`：配置路径、下载源、Git 初始配置项。
- 编写 `README.md`：任务总览、当前状态、待办清单。
- 初始化 `changelog/`、`gotchas/` 目录。

### 待办

- [ ] 填充 `skeleton/step-00-precheck.py`（预检）
- [ ] 填充 `skeleton/step-01-scan.py`（扫描下载源）
- [ ] 填充 `skeleton/step-02-process.py`（下载解压）
- [ ] 填充 `skeleton/step-03-verify.py`（验证隔离）
- [ ] 填充 `skeleton/step-04-compare.py`（多身份验证）
- [ ] 填充 `skeleton/step-05-cleanup.py`（回滚）
- [ ] 编写 `scripts/` 下的独立调用脚本
- [ ] 更新 `verified-runtime-index.json` 登记 Git 工具链
