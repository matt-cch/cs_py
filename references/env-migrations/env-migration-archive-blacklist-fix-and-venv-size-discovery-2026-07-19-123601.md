---
title: 归档黑名单匹配修复与 venv.7z 大小发现
description: archive_scanner match_blacklist 第三项检查修复导致黑名单正确生效，进而发现旧版 venv.7z 曾错误包含 snapshot/storage/cache 等脏数据；同时 cs_py blacklist 补全与 archive_compressor 旧包删除 bug 修复。
date: 2026-07-19
meta:
  version: "1.0.0"
  related_mdc: high-frequency-verify-runtime.mdc
---

# env-migration-archive-blacklist-fix-and-venv-size-discovery-2026-07-19-123601

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 归档黑名单匹配修复与 venv.7z 大小异常发现 |
| **日期** | 2026-07-19 |
| **文件名时间戳** | `2026-07-19-123601` |
| **触发原因** | 用户发现 venv.7z 从 10.9 MB 降到 8.4 MB，担心本次改造多改了地方 |
| **影响范围** | archive_scanner.py 黑名单匹配逻辑、archive_compressor.py 旧包删除逻辑、archive-groups.json cs_py 黑名单 |
| **风险等级** | 低（修复 bug，数据更干净；旧版 10.9 MB 实为脏数据） |

## 一、文本文件变更清单

### 1. 修改 `archive_scanner.py` — match_blacklist 第三项检查

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_scanner.py` |
| **变更类型** | `修复` |
| **修复内容** | `pat.endswith("/")` 分支增加第三项检查：`("/" + dir_pat + "/") in (path + "/")` |
| **作用** | 使 `data-opencode/opencode/snapshot/` 等黑名单模式能正确命中带 `venv/` 前缀的扫描路径 |
| **验证方式** | 对比新旧 listfile，旧版错误包含 289 个黑名单文件，新版为 0 |
| **修复时间** | `2026-07-03 15:25:24`（非本次 session，本次为发现该修复的副作用） |

**修复前后对比**：

旧版（bug）仅检查 `path == dir_pat` 和 `path.startswith(dir_pat + "/")`：
```python
elif pat.endswith("/"):
    dir_pat = pat[:-1]
    if path == dir_pat or path.startswith(dir_pat + "/"):
        return True
```

对于扫描路径 `venv/data-opencode/opencode/snapshot/...`：
- `path == "data-opencode/opencode/snapshot"` → False
- `path.startswith("data-opencode/opencode/snapshot/")` → False（因为 path 以 `venv/` 开头）
- 结果：**错误放行**，snapshot 文件被扫描进 listfile

新版（修复）增加第三项：
```python
elif pat.endswith("/"):
    dir_pat = pat[:-1]
    if (
        path == dir_pat
        or path.startswith(dir_pat + "/")
        or ("/" + dir_pat + "/") in (path + "/")
    ):
        return True
```

- `("/" + "data-opencode/opencode/snapshot" + "/") in ("venv/data-opencode/opencode/snapshot/..." + "/")` → **True**
- 结果：**正确排除**

### 2. 修改 `archive-groups.json` — cs_py 黑名单补全

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-tools/archive-groups.json` |
| **变更类型** | `追加` |
| **新增内容** | `cs_py.blacklist` 追加 `.agents/`、`.opencode/`、`out/`、`__pycache__/` |
| **作用** | cs_py 归档排除 Agent skills、OpenCode 配置、构建输出、Python 缓存目录 |
| **验证方式** | 解压 cs_py.7z 检查无 `.agents/`、`.opencode/`、`out/`、`__pycache__/` 内容 |

### 3. 修改 `archive_compressor.py` — 旧包删除逻辑修复

| 属性 | 值 |
|------|-----|
| **路径** | `references/tasks/deploy-git-isolated/scripts/py-plugins/archive_compressor.py` |
| **变更类型** | `修复` |
| **修复内容** | 旧包删除不再跳过当前格式，改为遍历所有后缀（`.zip`、`.7z`、`.zst`）统一删除 |
| **作用** | 避免 `7z.exe a` 在旧包存在时进入更新模式（读取旧归档 + 合并），导致压缩极慢且体积异常 |
| **验证方式** | 压缩日志显示 `[compress] 删除旧包: ...`；输出大小从 306 MB 异常降至 15.1 MB |

### 4. 修改 `archive_config.py` / `archive_compressor.py` / `archive_project.py` — zstd 格式支持

| 属性 | 值 |
|------|-----|
| **路径** | `archive_config.py`、`archive_compressor.py`、`archive_project.py` |
| **变更类型** | `追加` |
| **新增内容** | `--format zstd` 选项、`.zst` 后缀、7-Zip-ZS `variant="zs"` 探测 |
| **作用** | 扩展归档格式支持，zstd 压缩比通常优于 zip |
| **注意事项** | 7-Zip-ZS 的 `-tzstd` 仅支持单文件；多文件归档需用 `.tar.zst` 两步（先 `-ttar` 再 `-tzstd`） |

## 二、非文本操作

本次 session 无文件系统/缓存迁移操作，全部为代码修改与归档验证。

## 三、核心发现：venv.7z 为何从 10.9 MB 降到 8.4 MB

### 旧版（2026-06-21）——脏数据

| 指标 | 数值 |
|------|------|
| 文件数 | 7,168 |
| 压缩大小 | 10.9 MB |
| 错误包含的黑名单文件 | **289 个** |

**被错误包含的黑名单文件分布**：

| 目录 | 文件数 | 说明 |
|------|--------|------|
| `data-opencode/opencode/snapshot/` | 175 | Git 仓库快照，体积大 |
| `data-opencode/opencode/storage/` | 64 | session diff 等存储 |
| `data-opencode/opentui/` | 12 | tree-sitter wasm 等 |
| `data-opencode/cache/` | 35 | OpenCode 缓存 |
| `data-opencode/cache-test/` | 3 | 缓存测试目录 |

### 新版（2026-07-19）——干净数据

| 指标 | 数值 |
|------|------|
| 文件数 | 6,949 |
| 压缩大小 | **8.4 MB** |
| 错误包含的黑名单文件 | **0** |

### 根因时间线

| 时间 | 事件 | 影响 |
|------|------|------|
| 2026-06-21 | 旧版归档（7168 文件，10.9 MB） | snapshot 等 289 个黑名单文件被错误包含 |
| 2026-07-03 15:25:24 | `archive_scanner.py` 修复 `match_blacklist` | 增加 `("/" + dir_pat + "/") in (path + "/")` 检查 |
| 2026-07-19 | 本次归档（6949 文件，8.4 MB） | 黑名单正确生效，体积回归正常 |

**结论**：8.4 MB 是正确值，10.9 MB 是 bug 产物。修复后的归档更干净、更准确。

## 四、落盘验证

### 验证命令

```powershell
# Markdown 编码检查
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\run-lint.py" --devroot "D:\pjt\cursor\cs_py" --files "D:\pjt\cursor\cs_py\references\env-migrations\env-migration-archive-blacklist-fix-and-venv-size-discovery-2026-07-19-123601.md"

# archive 审计（cs_py）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\archive_project.py" --group cs_py --stage scan --devroot "D:\pjt\cursor\cs_py"

# archive 审计（venv）
& "D:\pjt\cursor\cs_py\venv\py\python.exe" "D:\pjt\cursor\cs_py\references\tasks\deploy-git-isolated\scripts\py-tools\archive_project.py" --group venv --stage scan --devroot "D:\pjt\cursor\cs_py"
```

### 合规标准

| 检查项 | 标准 | 结果 |
|--------|------|------|
| Markdown 编码 | BOM=no, DOUBLE_BOM=no, CRLF=0, LF>0 | 待 lint 验证 |
| cs_py 黑名单 | 无 `.agents/`、`.opencode/`、`out/`、`__pycache__/` | PASS |
| venv 黑名单 | 无 snapshot/storage/opentui/cache/cache-test | PASS |
| 旧包删除 | 压缩前删除旧包，非更新模式 | PASS |

## 五、回滚方案

| 回滚步骤 | 命令/操作 |
|---------|----------|
| 恢复旧 blacklist | 从 `archive-groups.json` 移除 `.agents/`、`.opencode/`、`out/`、`__pycache__/` |
| 恢复旧 match_blacklist | 移除 `("/" + dir_pat + "/") in (path + "/")` 检查（**不推荐**，会导致脏数据回归） |
| 重新归档 | 执行 `archive_project.py --group cs_py venv --stage all --force` |

> **警告**：回滚 match_blacklist 修复会导致 snapshot 等黑名单文件重新被错误包含，强烈不建议。

## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-19-123601 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户发现 venv.7z 体积异常变小，排查后发现是旧版 match_blacklist bug 修复的副作用 |
| **下次修订条件** | archive_scanner 黑名单模式语法再次变更；archive-groups 黑名单条目增减 |
| **跨环境迁移参考** | 直接复用 `archive_scanner.py` 的 `match_blacklist` 逻辑；黑名单模式语法见文档内「模式语法」节 |
