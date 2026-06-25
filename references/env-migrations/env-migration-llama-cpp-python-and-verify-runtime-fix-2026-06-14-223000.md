---
title: llama-cpp-python 运行时检测扩展 + verify-runtime 联动修复
description: 运行时工具链新增 llama_cpp_python（wheel 包）的检测与下载；verify-runtime 实现 candidate 命中联动修复、去噪输出、自动写回索引。
date: 2026-06-14
---

# `env-migration-llama-cpp-python-and-verify-runtime-fix-2026-06-14-223000.md`

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | llama-cpp-python 运行时检测扩展 + verify-runtime 联动修复 |
| **日期** | 2026-06-14 |
| **文件名时间戳** | `2026-06-14-223000` |
| **触发原因** | 用户需要在运行时检测系统中加入 llama-cpp-python（适配 Python 3.13 Windows x64 的预编译 wheel），并在下载后暴露问题驱动 verify-runtime 改进 |
| **影响范围** | `references/runtime/*.ps1`、`verified-runtime-index.json`、D:\download 目录 |
| **风险等级** | 低（纯工具链脚本扩展，不触及业务代码） |


## 一、文本文件变更清单

### 1. 修改 `references/runtime/verified-runtime-index.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verified-runtime-index.json` |
| **变更类型** | `追加` + `修改` |
| **新增内容** | `toolchain.llama_cpp_python` 条目（`package_type: "python_wheel"`, `python_constraint: "3.13"`, `platform: "win_amd64"`） |
| **修改内容** | `python.version` 更新为 `3.13.14`；`cursor.executable` / `cmd_wrapper` / `package_json` 联动更新；`github_connectivity` latency 更新 |
| **作用** | 将新工具纳入真源索引，供 Agent 和脚本速查引用 |
| **迁移方式** | 直接覆盖（由 verify-runtime 脚本自动写回） |

### 2. 修改 `references/runtime/upstream-queries.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/upstream-queries.ps1` |
| **变更类型** | `追加` + `修改` |
| **新增内容** | `llama_cpp_python` case：实时查询 GitHub Release assets，遍历 releases 列表，**只选 tag_name 严格匹配 `vX.Y.Z` 的纯净版本**，自动过滤 `-hip-radeon` 等特殊构建 tag |
| **修改内容** | `python` case：新增版本约束 `< 3.14.0`，指定版本和自动最新版均过滤 |
| **作用** | 上游查询能正确找到 wheel asset，不因特殊 tag 而误判版本 |
| **迁移方式** | 直接覆盖 |

### 3. 修改 `references/runtime/download-utils.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-utils.ps1` |
| **变更类型** | `追加` |
| **新增内容** | `Get-LocalToolVersion` 新增 `llama_cpp_python` 分支：从 whl 文件名正则提取版本号（`llama_cpp_python-{ver}-py3-none-win_amd64.whl`），不依赖 Python 环境 |
| **作用** | 本地版本检测与 whl 文件名解耦，不依赖 pip/conda |
| **迁移方式** | 直接覆盖 |

### 4. 修改 `references/runtime/download-runtime-tool.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/download-runtime-tool.ps1` |
| **变更类型** | `追加` + `修改` |
| **新增内容** | ① `ValidateSet` 加入 `llama_cpp_python`<br>② wheel 包下载逻辑：扩展名 `.whl`、保持 whl 形态（不解压）、整理到版本号子目录<br>③ 优先使用实时查询返回的原始 `asset_name`（含平台标记）作为文件名 |
| **修改内容** | `Write-ResultLine` 遇到本地版本 `$null` 时改为显示 `"未安装"`，避免参数绑定异常 |
| **作用** | wheel 包可被 pip/poetry 直接识别，脚本不再因文件名缺失平台标记而报错 |
| **迁移方式** | 直接覆盖 |

### 5. 修改 `references/runtime/verify-runtime.ps1`

| 属性 | 值 |
|------|-----|
| **路径** | `references/runtime/verify-runtime.ps1` |
| **变更类型** | `追加` + `修改` |
| **新增内容** | ① `llama_cpp_python` 版本检测（whl 文件名提取）<br>② **candidate 命中联动修复**：主路径失效 + candidate 命中时，自动将 `executable` 切到命中路径，并在报告中体现 `"主路径失效，从候选 [type] 命中"`<br>③ 去噪输出：无状态变化的 missing candidate 不再逐个刷屏<br>④ **自动写回索引**：检测完成后同步更新 `verified-runtime-index.json` 的 candidate 状态和 executable 路径 |
| **作用** | 报告从"一堆 FAIL"变为精准命中 + 自动修复，减少人工更新索引成本 |
| **迁移方式** | 直接覆盖 |


## 二、非文本操作（文件系统）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 目录创建 | — | `D:\download\llama_cpp_python-0.3.29\` | 下载脚本创建的 wheel 存放目录 |
| 文件下载 | GitHub Release | `D:\download\llama_cpp_python-0.3.29\llama_cpp_python-0.3.29-py3-none-win_amd64.whl` | 6.14 MB 压缩 / 24.86 MB 解压 |

> 注：`llama_cpp_python` 当前未执行替换到 `D:\download\llama_cpp_python\`，所以 verify-runtime 仍报告 executable 不存在。若需全绿，手动移动或重新运行 download 脚本输入 `Y`。Poetry `--dry-run` 已验证该 whl 无依赖冲突。


## 三、环境变量 / 路径速查

索引中的关键路径（Agent 引用时以 `verified-runtime-index.json` 为准）：

```json
{
  "llama_cpp_python": {
    "executable": "D:\\download\\llama_cpp_python",
    "download_url_template": "https://github.com/abetlen/llama-cpp-python/releases/download/v{version}/llama_cpp_python-{version}-py3-none-win_amd64.whl"
  }
}
```

- `executable` 指向目录（wheel 包的特殊处理），非单个文件
- `download_url_template` 中的 `{version}` 替换为纯净版本号（如 `0.3.29`，不含 `-hip-radeon` 等后缀）


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 llama_cpp_python 下载 | `"N" | powershell.exe -ExecutionPolicy Bypass -File "references\runtime\download-runtime-tool.ps1" -ToolName "llama_cpp_python" -IndexPath "references\runtime\verified-runtime-index.json"` | 下载成功，whl 文件名含 `py3-none-win_amd64` |
| 2 | 确认 Poetry 识别 whl | `python.exe -m poetry --directory apps\api-demo add D:\download\llama_cpp_python-0.3.29\llama_cpp_python-0.3.29-py3-none-win_amd64.whl --dry-run` | 零依赖冲突，版本匹配 |
| 3 | 确认 Python 版本约束 | `"N" | powershell.exe -ExecutionPolicy Bypass -File "references\runtime\download-runtime-tool.ps1" -ToolName "python" -IndexPath "references\runtime\verified-runtime-index.json"` | 检测到版本 `< 3.14.0` |
| 4 | 确认 verify-runtime 联动修复 | `powershell.exe -ExecutionPolicy Bypass -File "references\runtime\verify-runtime.ps1"` | cursor.executable PASS，candidate missing 不再刷屏 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 移除 llama_cpp_python 索引条目 | 从 `verified-runtime-index.json` `toolchain` 中删除 `llama_cpp_python` 对象 |
| 恢复 verify-runtime 旧逻辑 | `git checkout references/runtime/verify-runtime.ps1`（v1.0.0 之前） |
| 删除下载的 whl | `Remove-Item -Recurse "D:\download\llama_cpp_python*"` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-14-223000 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求将 llama-cpp-python 纳入运行时检测与下载体系 |
| **下次修订条件** | llama_cpp_python 发布新版本需更新 `latest_checked`；或 Python 版本约束需调整 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-14*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
