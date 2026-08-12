---
title: wf-download-runtime.py --force 替换闭环修复
description: 修改 wf-download-runtime.py 使 --force 参数真正完成下载→替换闭环，修复 Chromium 替换时路径构造错误，补录 cs-py.code-workspace 的 python.defaultInterpreterPath。
date: 2026-08-10
meta: {}
---

# env-migration-download-runtime-force-closure-2026-08-10-110139

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | wf-download-runtime.py `--force` 替换闭环修复 + Chromium 下载替换路径纠偏 + cs-py.code-workspace Python 解释器配置补全 |
| **日期** | 2026-08-10 |
| **文件名时间戳** | `2026-08-10-110139` |
| **触发原因** | 1. 用户执行真源检测发现 Chromium 可更新；2. 下载替换过程中 Agent 自行构造路径导致错误目录被写入；3. `wf-download-runtime.py` 的 `--force` 参数名不副实，只跳过版本对比不触发替换闭环；4. cs-py.code-workspace 缺少 `python.defaultInterpreterPath` 导致右下角解释器 fallback 到系统路径 |
| **影响范围** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py`、`.vscode/settings.json`、`cs-py.code-workspace`、`D:\download\chrome-win64` |
| **风险等级** | 中（修改核心 workflow 脚本的行为契约，需验证向后兼容） |


## 一、文本文件变更清单

### 1. 修改 `cs-py.code-workspace`

| 属性 | 值 |
|------|-----|
| **路径** | `cs-py.code-workspace` |
| **变更类型** | `追加` |
| **新增内容** | `"python.defaultInterpreterPath": "${workspaceFolder}\\venv\\py\\python.exe"` |
| **插入位置** | `settings` 对象内首行 |
| **作用** | 修复工作区模式下右下角 Python 解释器 fallback 到系统路径的问题 |
| **验证方式** | 重载窗口后 `Ctrl+Shift+P` → `Python: Select Interpreter`，确认显示 `venv/py/python.exe` |
| **迁移方式** | 多端迁移时 `${workspaceFolder}` 自动解析，无需调整 |

### 2. 修改 `wf-download-runtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` |
| **变更类型** | `修改` |
| **修改内容** | Step 7（原"默认不替换"）改为：当 `args.force` 为 True 时，读取 `verified-runtime-index.json` → 获取 `toolchain.<tool>.executable` → 推导 `tool_dir` 和 `exe_path` → 调用 `atomic-04-backup-replace.py` 完成替换 |
| **插入位置** | 原第 368-376 行 |
| **作用** | 使 `--force` 参数名副其实，完成下载→替换闭环，避免调用者（Agent/用户）二次调用 atomic-04 时自行构造路径出错 |
| **验证方式** | `wf-download-runtime.py --tool-name chromium --force --show-progress` → 观察 Step 7 输出"替换成功" |
| **迁移方式** | 直接覆盖文件即可，无额外依赖 |

> **向后兼容说明**：不传 `--force` 时行为不变（"默认不替换"），仅当显式传 `--force` 时才触发替换闭环。


## 二、非文本操作（文件系统/缓存迁移）

本次 session 涉及以下非文本操作：

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 下载+解压 | — | `D:\download\chromium-153.0.7998.0-extracted\chrome-win64` | Chrome for Testing 新版本下载 |
| 错误复制（已纠偏） | `chromium-153.0.7998.0-extracted\chrome-win64` | `D:\download\chrome-win`（错误位置） | Agent 自行构造路径 `--tool-dir` 时遗漏 `-64` 后缀，后续已删除 |
| 正确替换 | `chromium-153.0.7998.0-extracted\chrome-win64` | `D:\download\chrome-win64` | 从真源 `executable` 推导路径后，由 atomic-04 完成替换 |
| 下载（不替换） | — | `D:\download\opencode_cli-1.18.15-extracted` | OpenCode CLI 1.18.15 下载，默认不替换，产物保留 |
| 清理 | 上述中间产物/旧备份 | — | 解压目录、ZIP 包、旧备份已删除 |


## 三、环境变量速查

无新增环境变量。本次 session 未修改 `terminal.integrated.env.windows`。


## 四、落盘验证

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.py`（wf-download-runtime.py） | `run-lint.py --profile lint-python` | Python 语法 | py_compile 通过 |

**执行记录**：
```powershell
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "D:\pjt\cursor\cs_py" --files "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\download-runtime\wf-download-runtime.py"
# 结果: ✅ 全部通过
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 `--force` 替换闭环 | `python wf-download-runtime.py --tool-name chromium --force --show-progress` | Step 7 输出"替换成功"，无需二次调用 atomic-04 |
| 2 | 确认解释器路径生效 | 重载窗口后检查右下角 Python 解释器 | 显示 `venv/py/python.exe`（非系统路径） |
| 3 | 确认真源索引同步 | 执行 `wf-verify-runtime.py --tool chromium` | `executable` 指向 `D:\download\chrome-win64\chrome.exe` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 wf-download-runtime.py | 从 Git 回滚到修改前版本（`git checkout HEAD -- .../wf-download-runtime.py`） |
| 恢复 cs-py.code-workspace | 删除 `"python.defaultInterpreterPath"` 行 |
| 恢复 Chromium 旧版本 | 若备份目录存在，将 `chrome-win64-backup-<timestamp>` 重命名为 `chrome-win64` |


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-08-10-110139 |
| **更新人** | Human + Agent Session |
| **变更触发** | 真源检测发现 Chromium 可更新 + Agent 路径构造错误纠偏 + cs-py.code-workspace 解释器配置缺失 |
| **下次修订条件** | `wf-download-runtime.py` 的 `--force` 行为再次变更；或新增工具需要替换闭环 |
| **跨环境迁移参考** | 直接覆盖 `wf-download-runtime.py` + 按「验证清单」逐条执行 |


*文档生成时间：2026-08-10*  
*模板版本：v2*
