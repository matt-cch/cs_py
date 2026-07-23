---
title: FTP 工具链测试与 workflow-poly staged 回滚验证
description: 测试 FTP server 连通性、生成目录 manifest、下载文件；验证 workflow-poly Step 4 git add 与 atomic-git-reset-staged 回滚能力
date: 2026-07-19
meta:
  version: 1.0.0
---

# FTP 工具链测试与 workflow-poly staged 回滚验证

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | FTP 工具链测试与 workflow-poly Step 4 + staged 回滚验证 |
| **日期** | 2026-07-19 |
| **文件名时间戳** | `2026-07-19-142559` |
| **触发原因** | 用户要求测试 FTP server 连通性、目录遍历、文件下载；并验证 deploy-git-isolated workflow 的 staged 回滚能力 |
| **影响范围** | `D:\yidongyunpan\sync\pjt\fld\te_bill\` 下新增测试脚本；`D:\BaiduNetdiskDownload\` 下新增下载文件 |
| **风险等级** | 低（纯测试操作，无环境配置变更） |


## 一、文本文件变更清单

### 1. 新建 `ftp_test_connectivity.py`

| 属性 | 值 |
|------|-----|
| **路径** | `D:\yidongyunpan\sync\pjt\fld\te_bill\test_ftp_connectivity.py` |
| **变更类型** | `新建` |
| **作用** | 从 `config.ini` base64 解码 FTP 连接信息后测试连通性 |
| **验证方式** | 执行脚本，确认输出 "连通性测试全部通过" |
| **迁移方式** | 可直接复制到目标环境，需确保 `config.ini` 路径正确 |

### 2. 新建 `ftp_gen_manifest.py`

| 属性 | 值 |
|------|-----|
| **路径** | `D:\yidongyunpan\sync\pjt\fld\te_bill\ftp_gen_manifest.py` |
| **变更类型** | `新建` |
| **作用** | 连接 FTP 后输出根目录到本地 JSON manifest |
| **验证方式** | 执行后检查 `ftp_root_manifest.json` 是否存在 |
| **迁移方式** | 可直接复制 |

### 3. 新建 `ftp_list_xm_py_data.py`

| 属性 | 值 |
|------|-----|
| **路径** | `D:\yidongyunpan\sync\pjt\fld\te_bill\ftp_list_xm_py_data.py` |
| **变更类型** | `新建` |
| **作用** | 递归列出 `xm_py_data` 子目录结构到 manifest |
| **验证方式** | 执行后检查 `ftp_xm_py_data_manifest.json`，确认路径格式为 `/xm_py_data/...` |
| **迁移方式** | 可直接复制 |

### 4. 新建 `ftp_download_file.py`

| 属性 | 值 |
|------|-----|
| **路径** | `D:\yidongyunpan\sync\pjt\fld\te_bill\ftp_download_file.py` |
| **变更类型** | `新建` |
| **作用** | 从 FTP 下载指定文件到本地路径 |
| **验证方式** | 执行后检查本地文件大小与远程一致 |
| **迁移方式** | 可直接复制 |

### 5. 新建 `ftp_search_dir.py`

| 属性 | 值 |
|------|-----|
| **路径** | `D:\yidongyunpan\sync\pjt\fld\te_bill\ftp_search_dir.py` |
| **变更类型** | `新建` |
| **作用** | 在 FTP server 上搜索指定目录名 |
| **验证方式** | 执行后查看搜索结果 |
| **迁移方式** | 可直接复制 |

### 6. 新增 manifest 文件

| 属性 | 值 |
|------|-----|
| **路径** | `D:\yidongyunpan\sync\pjt\fld\te_bill\ftp_root_manifest.json` |
| **变更类型** | `新建` |
| **作用** | FTP 根目录 26 项的结构快照 |
| **迁移方式** | 由脚本自动生成，无需手动迁移 |

| 属性 | 值 |
|------|-----|
| **路径** | `D:\yidongyunpan\sync\pjt\fld\te_bill\ftp_xm_py_data_manifest.json` |
| **变更类型** | `新建` |
| **作用** | `xm_py_data` 目录递归结构快照（285 项） |
| **迁移方式** | 由脚本自动生成 |

### 7. 下载的文件

| 属性 | 值 |
|------|-----|
| **路径** | `D:\BaiduNetdiskDownload\20221130te\20230608template\4900-TE运输账单发票模板.xlsx` |
| **变更类型** | `新建` |
| **来源** | FTP `/xm_py_data/bal/te/4900-TE运输账单发票模板.xlsx` |
| **大小** | 117,824 bytes (115.1 KB) |
| **迁移方式** | 通过 `ftp_download_file.py` 重新下载 |


## 二、非文本操作

本次 session 无环境配置变更、无缓存迁移、无目录创建（除下载时自动创建的本地目录外）。


## 三、验证清单

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | FTP 连通性 | `python test_ftp_connectivity.py` | TCP 连接成功、登录成功、目录列出成功 |
| 2 | 根目录 manifest | `python ftp_gen_manifest.py` | `ftp_root_manifest.json` 生成，26 项 |
| 3 | xm_py_data manifest | `python ftp_list_xm_py_data.py` | `ftp_xm_py_data_manifest.json` 生成，285 项，路径格式正确 |
| 4 | 文件下载 | `python ftp_download_file.py` | 本地文件大小与远程一致 (117824 bytes) |
| 5 | staged 回滚 | `git add -A` 后执行 `atomic-git-reset-staged.py` | staged 区清空，工作区修改保留 |


## 四、关键发现

### 4.1 FTP 连通性

- DNS 解析到 `198.18.x.x`（RFC 2544 测试网段），存在 DNS 污染迹象
- TCP 连接成功，TLS 握手失败（`UNEXPECTED_EOF_WHILE_READING`）
- **但 `ftplib.FTP` 可以正常连接和登录**（未走 TLS，走明文 FTP）

### 4.2 目录结构

- 根目录下无 `xm-py-data`（连字符），实际目录为 **`xm_py_data`**（下划线）
- `xm_py_data` 下主要子目录：`bak/`、`bal/`、`download/`、`install/`、`pjt/`
- `bal/` 下含业务数据：`asus/`、`te/`、`tecsv/`、`wpg/` 等

### 4.3 Git 环境

- 当前分支：`task/deploy-git-isolated`
- 远程 origin：`https://github.com/matt-cch/cs_py.git`
- `git ls-remote` 成功，说明 Git HTTPS 在当前网络下**可达**
- 工作区存在大量未提交更改（deploy-git-isolated task 建设产物）

### 4.4 workflow-poly staged 回滚验证

- `git add -A` 后 302 个文件进入 staged
- `atomic-git-reset-staged.py` 成功取消全部 302 个文件的暂存
- 回滚后工作区状态与 add 前完全一致（修改保留、untracked 保留）
- **验证通过** ✅


## 五、回滚方案

本次 session 产物均为测试脚本和 manifest，无环境配置变更：

| 回滚步骤 | 命令 |
|---------|------|
| 删除测试脚本 | `Remove-Item "D:\yidongyunpan\sync\pjt\fld\te_bill\test_ftp_connectivity.py"` 等 |
| 删除 manifest | `Remove-Item "D:\yidongyunpan\sync\pjt\fld\te_bill\ftp_root_manifest.json"` 等 |
| 删除下载文件 | `Remove-Item "D:\BaiduNetdiskDownload\20221130te\20230608template\4900-TE运输账单发票模板.xlsx"` |


## 六、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-19-142559 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户指令：测试 FTP 连通性、生成 manifest、验证 workflow staged 回滚 |
| **下次修订条件** | 新增 FTP 相关原子脚本、workflow-poly 回滚机制增强 |
| **跨环境迁移参考** | 复制测试脚本 + 确保 `config.ini` 路径正确 + 按验证清单执行 |


*文档生成时间：2026-07-19*  
*模板版本：v2*
