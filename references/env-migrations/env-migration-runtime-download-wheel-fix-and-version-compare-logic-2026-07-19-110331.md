---
title: 运行时下载 whl 解压修复与版本比较逻辑修正
description: 修复 llama_cpp_python whl 被错误解压为 ZIP、git windows 版本号比较误判两处根因，统一 package_type 字段命名。
date: 2026-07-19
meta: {}
---

# env-migration-runtime-download-wheel-fix-and-version-compare-logic-2026-07-19-110331

> **Session 主题**：运行时下载 whl 解压修复与版本比较逻辑修正
> **日期**：2026-07-19（文件名时间戳：2026-07-19-110331）
> **触发原因**：
> 1. 强制下载 llama_cpp_python 时发现 `.whl` 被当成 ZIP 解压到 `-extracted` 目录，产生大量 Python 包文件而非保留单一 whl
> 2. 真源检测报告中 git 版本状态显示 `local_newer`，实际应为 `outdated`（上游 `.windows.3` 高于本地 `.windows.2`）
> **影响范围**：运行时下载脚本链、版本比较原子脚本、工具配置 JSON、api-demo 依赖配置
> **风险等级**：中（影响下载产物正确性和版本判断准确性）


## 一、文本文件变更清单

### 1. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-compare-version.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/runtime-common/atomic-compare-version.py` |
| **变更类型** | `修改` |
| **修改内容** | `_to_sortable` 函数正则逻辑：从 `re.sub(r'[a-zA-Z].*$', '', ver)` 改为 `re.sub(r'[a-zA-Z]+', '.', ver)` + `re.sub(r'\.+', '.', clean).strip('.')` |
| **作用** | 保留字母前后数字（如 `2.55.0.windows.2` → `2.55.0.2`），使版本号可被正确比较 |
| **验证方式** | `python atomic-compare-version.py --local-ver "2.55.0.windows.2" --upstream-ver "2.55.0.windows.3"` → 输出 `outdated` |
| **迁移方式** | 可直接覆盖 |

### 2. 修改 `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_naming.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/runtime_naming.py` |
| **变更类型** | `修改` |
| **修改内容** | `get_extract_dir` 增加 `package_type` 参数；当 `package_type == "python_wheel"` 时返回 `-wheel` 后缀 |
| **作用** | whl 类型的下载产物使用 `-wheel` 目录名，而非 `-extracted` |
| **验证方式** | `python -c "from runtime_naming import get_extract_dir; print(get_extract_dir('x', '1.0', 'python_wheel'))"` → `x-1.0-wheel` |
| **迁移方式** | 可直接覆盖 |

### 3. 修改 `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/download-runtime/wf-download-runtime.py` |
| **变更类型** | `修改` |
| **修改内容** | 两处 `tool.get("download_type", ...)` 改为 `tool.get("package_type", ...)` |
| **插入位置** | 第 322 行（`naming.get_download_paths` 调用）和第 358 行（`--config-json` 参数） |
| **作用** | 消除无意义的 "download_type → package_type" 翻译层，直接透传配置字段 |
| **验证方式** | 执行 `wf-download-runtime.py --tool-name llama_cpp_python --force`，产物目录后缀应为 `-wheel` |
| **迁移方式** | 可直接覆盖 |

### 4. 修改 `references/runtime/runtime_config/tools_config.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_config/tools_config.json` |
| **变更类型** | `修改` |
| **修改内容** | `llama_cpp_python` 条目新增 `"package_type": "python_wheel"`（之前该字段完全缺失） |
| **作用** | 使下载流程能识别 llama_cpp_python 为 whl 类型，避免被当成 ZIP 解压 |
| **验证方式** | `python -c "import json; d=json.load(open('tools_config.json')); print([t.get('package_type') for t in d['tools'] if t['name']=='llama_cpp_python'])"` → `['python_wheel']` |
| **迁移方式** | 可直接覆盖 |

### 5. 修改 `references/runtime/verified-download-toolset.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-download-toolset.json` |
| **变更类型** | `修改` |
| **修改内容** | 全部 6 处 `download_type` → `package_type` |
| **作用** | 文档级索引与运行时配置字段名统一，消除命名歧义 |
| **验证方式** | `grep -c "download_type" verified-download-toolset.json` → `0` |
| **迁移方式** | 可直接覆盖 |

### 6. 修改 `apps/api-demo/pyproject.toml`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/api-demo/pyproject.toml` |
| **变更类型** | `修改` |
| **修改内容** | `llama-cpp-python` 本地 whl 路径从 `D:/download/llama_cpp_python-0.3.22/...` 改为 `D:/download/llama_cpp_python-0.3.22-wheel/...` |
| **作用** | 与下载流程生成的 `-wheel` 目录对齐 |
| **验证方式** | `poetry check` → `All set!` |
| **迁移方式** | 可直接覆盖 |


## 二、非文本操作（文件系统清理）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 删除 | `D:\download\llama_cpp_python-0.3.22-extracted` | — | 错误解压产物（whl 被 unzip 为 Python 包文件） |
| 删除 | `D:\download\llama_cpp_python-0.3.22` | — | 旧命名目录（无 `-wheel` / `-extracted` 后缀） |

### 复现命令

```powershell
# 清理旧产物（若在新环境复现，确认这些目录存在后再删除）
$dirs = @(
    "D:\download\llama_cpp_python-0.3.22-extracted",
    "D:\download\llama_cpp_python-0.3.22"
)
foreach ($d in $dirs) {
    if (Test-Path $d) {
        Remove-Item -Recurse -Force $d
        Write-Output "Removed: $d"
    }
}
```


## 三、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 版本比较逻辑修复 | `python atomic-compare-version.py --local-ver "2.55.0.windows.2" --upstream-ver "2.55.0.windows.3"` | 输出 `outdated` |
| 2 | 版本比较相等场景 | `python atomic-compare-version.py --local-ver "2.55.0.windows.2" --upstream-ver "2.55.0.windows.2"` | 输出 `up_to_date` |
| 3 | 命名插件 whl 后缀 | `python -c "import sys; sys.path.insert(0, 'py-plugins'); from runtime_naming import get_extract_dir; print(get_extract_dir('x', '1.0', 'python_wheel'))"` | 输出 `x-1.0-wheel` |
| 4 | llama_cpp_python 强制下载 | `"N" | python wf-download-runtime.py --tool-name llama_cpp_python --force` | 产物目录为 `-wheel`，内部仅含一个 `.whl` 文件 |
| 5 | pyproject.toml 校验 | `poetry check` | `All set!` |
| 6 | lint 全量通过 | `python run-lint.py --files <修改的文件列表>` | 全部通过 |


## 四、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 还原版本比较逻辑 | 恢复 `atomic-compare-version.py` 中 `_to_sortable` 的正则为 `re.sub(r'[a-zA-Z].*$', '', ver)` |
| 还原命名插件 | 恢复 `runtime_naming.py` 中 `get_extract_dir` 为无 `package_type` 参数的旧签名 |
| 还原字段名 | 将 `tools_config.json` 和 `verified-download-toolset.json` 中的 `package_type` 改回 `download_type` |
| 还原 pyproject.toml 路径 | 将 `llama_cpp_python-0.3.22-wheel` 改回 `llama_cpp_python-0.3.22` |


## 五、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-19-110331 |
| **更新人** | Human + Agent Session |
| **变更触发** | 强制下载 llama_cpp_python 发现 whl 被错误解压；真源检测 git 版本状态误判 |
| **下次修订条件** | 新增 python_wheel 类型工具时，需在 `tools_config.json` 中同步登记 `package_type` |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |
