---
title: llama-cpp-python 版本固定与 Python 下载脚本建设
description: 创建 download-runtime-tool.py（Python 版）替代 PowerShell 版，解决上游查询不一致问题；通过二分法确定 llama-cpp-python 预编译 whl 兼容性分界（0.3.22 vs 0.3.23），并在下载脚本中固定安全版本。
date: 2026-06-17
---

# env-migration-llama-cpp-python-version-pin-and-download-script-2026-06-17-124500

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | llama-cpp-python 版本固定与 Python 下载脚本建设 |
| **日期** | 2026-06-17 |
| **文件名时间戳** | `2026-06-17-124500` |
| **触发原因** | 1. PowerShell 版 download-runtime-tool.ps1 上游查询返回 $null，fallback 到索引缓存导致下载旧版本；2. verify-runtime.py 实时查询到 0.3.30 但下载到 0.3.29 |
| **影响范围** | `references/runtime/download-runtime-tool.py`（新建）、`upstream_checker.py`（扩展指定版本查询）、`apps/api-demo/pyproject.toml`（依赖修正） |
| **风险等级** | 中（涉及工具链下载脚本核心逻辑，但仅新增不替换旧脚本） |


## 一、文本文件变更清单

### 1. 新建 `references/runtime/download-runtime-tool.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-runtime-tool.py` |
| **变更类型** | `新建` |
| **新增内容** | Python 版运行时工具下载脚本，复用 `upstream_checker.py` + `local_verifier.py`，解决 PS 版查询不一致问题 |
| **作用** | 替代/补充 PowerShell 版 `download-runtime-tool.ps1`，上游查询更稳定（requests 直连 GitHub API），错误信息更清晰，不再静默 fallback 到索引缓存 |
| **验证方式** | `python -m py_compile download-runtime-tool.py` 无语法错误；`--help` 正常输出；实际下载 llama_cpp_python 0.3.22 成功 |
| **迁移方式** | 直接复制文件到目标环境 |

### 2. 修改 `references/runtime/runtime_modules/upstream_checker.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/runtime_modules/upstream_checker.py` |
| **变更类型** | `修改` |
| **新增内容** | `query()` 方法新增 `target_version` 参数；`_query_opencode()` / `_query_llama_cpp_python()` 支持指定版本查询（构造 `releases/tags/v{version}` URL 而非 `releases/latest`） |
| **作用** | 让 `download-runtime-tool.py` 可以指定目标版本下载，而非只能追最新版 |
| **验证方式** | 调用 `checker.query("llama_cpp_python", "llama_cpp_python", "0.3.22")` 返回 `asset_url` 不为空 |
| **迁移方式** | 直接替换文件或按 diff 修改 |

### 3. 修改 `apps/api-demo/pyproject.toml`

| 属性 | 值 |
|------|-----|
| **路径** | `apps/api-demo/pyproject.toml` |
| **变更类型** | `修改` |
| **新增/修改内容** | llama-cpp-python 依赖从 PyPI 版本约束改为本地 whl 直接引用： `"llama-cpp-python @ D:/download/llama_cpp_python-0.3.22/llama_cpp_python-0.3.22-py3-none-win_amd64.whl"` |
| **作用** | 锁定已验证可用的 0.3.22 版本，避免 Poetry 自动升级到不兼容的 0.3.23+ |
| **验证方式** | `poetry show llama-cpp-python` 输出版本 `0.3.22`；运行翻译模型加载成功 |
| **迁移方式** | 编辑 `[project].dependencies`，确保文件名路径与实际磁盘一致 |


## 二、非文本操作（文件系统/缓存迁移）

本次 session 是否涉及文件复制、缓存迁移、目录创建等**无法被 git 追踪**的操作？

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| whl 下载 | GitHub Release | `D:\download\llama_cpp_python-0.3.22\llama_cpp_python-0.3.22-py3-none-win_amd64.whl` | Python 脚本下载的已验证安全版本 |
| whl 下载（废弃） | GitHub Release | `D:\download\llama_cpp_python-0.3.29*`, `D:\download\llama_cpp_python-0.3.30*` | 已验证不兼容，可删除 |


## 三、环境变量速查

无新增环境变量。


## 四、落盘验证（写入后必须执行）

| 文件类型 | 验证工具 | 验证内容 | 合规标准 |
|---------|---------|---------|---------|
| `.md`（env-migration 正文） | `check-file-encoding.ps1` | BOM、双 BOM、CRLF、LF | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 |
| `.py`（download-runtime-tool.py） | `python -m py_compile` | Python 语法正确性 | 无 SyntaxError |

**执行示例**：
```powershell
# Python 语法检查
"${devroot}\venv\py\python.exe" -m py_compile "${devroot}\references\runtime\download-runtime-tool.py"

# Markdown 文件编码检查
powershell.exe -ExecutionPolicy Bypass -File "${devroot}\schema\tool\check-file-encoding.ps1" -Path "${devroot}\references\env-migrations\env-migration-llama-cpp-python-version-pin-and-download-script-2026-06-17-124500.md"
```


## 五、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 download-runtime-tool.py 语法正确 | `python -m py_compile references/runtime/download-runtime-tool.py` | 无输出（通过） |
| 2 | 确认 llama-cpp-python 0.3.22 可用 | `python -c "from llama_cpp import Llama; print('import ok')"` | 输出 `import ok` |
| 3 | 确认模型加载不崩溃 | 运行 `debug/test-llama-params.py` | `[OK] 模型加载成功` |
| 4 | 确认 Poetry 依赖解析正确 | `poetry show llama-cpp-python` | 版本 `0.3.22` |
| 5 | 确认下载脚本固定版本行为 | `echo "N" | python download-runtime-tool.py --tool-name llama_cpp_python --index-path ...` | Step 3 显示 `使用固定版本（不查询上游）: 0.3.22` |


## 六、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 恢复 PyPI 依赖方式 | 编辑 `pyproject.toml`，将 `@ D:/download/...` 改回 `(">=0.3.20,<0.3.30")` |
| 删除 Python 下载脚本 | `Remove-Item "references/runtime/download-runtime-tool.py"` |
| 恢复 upstream_checker.py | 从 git 历史恢复 `runtime_modules/upstream_checker.py` 的旧版本 |
| 清理下载的 whl | `Remove-Item -Recurse "D:\download\llama_cpp_python-0.3.22"` |


## 七、关键发现（必须记录）

### llama-cpp-python 预编译 whl 兼容性分界

| 版本 | 状态 | 根因 |
|------|------|------|
| 0.3.20 | ✅ | py3139_cs26 项目验证可用 |
| 0.3.21 | ✅ | 本次验证可用 |
| **0.3.22** | ✅ **推荐** | **0.3.20 之后最新可用版本** |
| 0.3.23 | ❌ | `q4_K_8x8` repack 阶段触发 `0xc000001d`（非法指令） |
| 0.3.25 | ❌ | 同上 |
| 0.3.29 | ❌ | 同上 |
| 0.3.30 | ❌ | 同上 |

> **CPU 信息**：AMD Ryzen 7 5800H with Radeon Graphics
> **崩溃位置**：`llama_model_load_from_file` → `load_tensors` 完成后，`repack tensor blk.0.attn_q.weight with q4_K_8x8` 阶段
> **结论**：0.3.23 起的预编译 whl 启用了当前 CPU 不支持的 SIMD 指令（可能是 AVX-512 或 AMX），与 `py3-none-win_amd64` 标记的"通用 x64"承诺不符。

### 下载脚本设计决策

- **不删除 PS 版**：`download-runtime-tool.ps1` 仍保留，Python 版作为补充/优选方案
- **llama_cpp_python 固定版本**：在脚本内建 `FIXED_VERSIONS = {"llama_cpp_python": "0.3.22"}`，默认不再追新，避免下载到不兼容版本
- 其他工具（python/node/chromium/opencode_cli）仍正常查询上游最新版


## 八、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-17-124500 |
| **更新人** | Human + Agent Session |
| **变更触发** | llama-cpp-python 预编译 whl 版本兼容性问题 + PowerShell 上游查询不可靠 |
| **下次修订条件** | 1. AMD Ryzen 7 5800H 升级 BIOS/微码后支持新指令集；2. llama-cpp-python 官方修复 whl 兼容性；3. 发现 0.3.22 之后的可用版本 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-17*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
