---
title: HunyuanOCR-1.5 本地 llama.cpp 验证最终结论与 GLM-OCR 对照
description: 记录本次 session 对 HunyuanOCR-1.5 本地 CPU 验证的完整过程、失败原因、GLM-OCR 对照结果及用户终止决定。
date: 2026-07-20
meta:
  version: "1.0.0"
  filename_timestamp: "2026-07-20-173843"
---

# HunyuanOCR-1.5 本地 llama.cpp 验证最终结论与 GLM-OCR 对照

> **Session 主题**：HunyuanOCR-1.5 本地 llama.cpp CPU 验证执行、失败排查、GLM-OCR 对照验证
> **日期**：2026-07-20
> **文件名时间戳**：2026-07-20-173843
> **触发原因**：承接上一次调研 session（env-migration-hunyuanocr-gguf-research-2026-07-20-151258），用户要求实际下载 llama.cpp 二进制与模型并执行验证
> **影响范围**：已下载模型文件（~1.1 GB）和 llama.cpp 二进制（~18 MB）到本地磁盘
> **风险等级**：低（纯验证性质，无生产环境变更）
> **Session 状态**：用户主动终止，下班结束


## 一、本次 Session 执行概览

| 时间 | 事件 | 结果 |
|------|------|------|
| 15:12 | 开始 session，承接上次调研 | 读取历史 env-migration |
| 15:15 | 确认 llama-bak 中已有旧 llama-cli | 发现版本 9305（较旧），但支持 `--image` |
| 15:20 | 开始下载 HunyuanOCR GGUF 模型 | Q4_K_M + mmproj-Q8_0 |
| 15:37 | Q4_K_M 下载完成（355 MB） | ✅ 完整 |
| 16:51 | mmproj-Q8_0 下载完成（733 MB） | ✅ 完整（用户手动覆盖不完整的旧文件） |
| 16:55 | 首次尝试 llama-cli（旧版本 9305） | ❌ `unknown projector type: hunyuanocr` |
| 17:00 | 下载 llama.cpp b10069（最新版） | 解压到 `venv/llama/` |
| 17:01 | b10069 测试 | ❌ 同样 `unknown projector type: hunyuanocr` |
| 17:02 | 调研 GitHub Issues | 发现 Issue #23481：b9263 后 HunyuanOCR 合并入 HunyuanVL |
| 17:08 | 下载 llama.cpp b9260 | 解压覆盖 `venv/llama/` |
| 17:10 | b9260 首次测试 | ❌ 模型加载成功，但输出乱码/无限重复 |
| 17:15 | 查阅官方 prompt 格式和参数 | 从 HuggingFace 模型卡获取 |
| 17:20 | 使用官方 prompt 重新测试 | ❌ 仍然乱码（"海洋海洋海洋..." / "roughly roughly..."） |
| 17:25 | 启动 llama-server + API 测试 | ❌ CPU 推理超时（>10 分钟），放弃 |
| 17:30 | 测试 GLM-OCR 对照 | ✅ 正常输出中文 OCR 结果 |
| 17:38 | 用户要求 GLM-OCR 完整输出 | 命令执行被用户中止 |
| 17:38 | 用户终止 session | "不试了，要下班了" |


## 二、HunyuanOCR 验证失败详情

### 2.1 b10069（最新版）— 完全不兼容

```
E clip_init: failed to load model '...mmproj-Q8_0.gguf':
  load_hparams: unknown projector type: hunyuanocr
```

- **根因**：llama.cpp PR #23329（b9263）将 HunyuanOCR 合并入 HunyuanVL 架构，projector type 从 `hunyuanocr` 改为 `hunyuanvl` 或其他
- **结论**：**b9263 及以上版本无法加载 mradermacher/HunyuanOCR-GGUF 的 mmproj**

### 2.2 b9260（Issue #23481 报告的最后可用版本）— 能加载但输出异常

- 模型加载：✅ 成功
- mmproj 加载：✅ 成功
- 图像编码：✅ 成功
- **推理输出：❌ 乱码 / 无限重复**

**典型异常输出**：
```
海洋海洋海洋海洋海洋海洋海洋r韵韵韵韵韵韵韵韵韵韵韵韵...
eralaeralaeralaeralaeralaerala...
roughly roughly roughly roughly...
sau sau sau sau sau sau sau...
```

- 无论使用简单 prompt（`Extract all text from this image.`）还是官方 prompt（`提取文档图片中正文的所有信息用markdown格式表示...`）
- 无论采样参数（temp=0, top_p=1, repeat_penalty=1.08）如何调整
- 输出均为无意义字符的无限重复

### 2.3 llama-server + OpenAI API — CPU 推理超时

- Server 启动：✅ 正常
- 模型加载：✅ 正常
- API 请求：❌ **单次请求 >10 分钟无响应**
- 原因：1B VLM 纯 CPU 推理 + 图像编码 + 长文本生成，速度极慢


## 三、GLM-OCR 对照验证

### 3.1 模型信息

| 属性 | 值 |
|------|-----|
| 路径 | `D:\yidongyunpan\sync\install\models\glm-ocr-gguf\` |
| 主模型 | `GLM-OCR-Q8_0.gguf` |
| mmproj | `mmproj-GLM-OCR-Q8_0.gguf` |

### 3.2 成功验证（早期测试）

**命令**：
```powershell
llama-cli.exe `
  --model GLM-OCR-Q8_0.gguf `
  --mmproj mmproj-GLM-OCR-Q8_0.gguf `
  --image img-002.jpeg `
  --prompt "Extract all text from this image." `
  --ctx-size 4096 --n-predict 1024 -ngl 0 --no-display-prompt
```

**输出**（部分）：
```
不够精确
跨文件修改困难
浪费时间

今天我要介绍一下 LSP + AST-Grep，将彻底解决这个问题。

什么是 LSP?

核心概念

LSP = Language Server Protocol（语言服务器协议）
```

- ✅ 中文正文识别正常
- ✅ 英文术语识别正常
- ✅ 无乱码、无无限重复

### 3.3 完整输出测试（用户终止）

用户后续要求 GLM-OCR 用完整命令重新输出（不加 `--no-display-prompt`，不截断，不落盘），但在命令执行过程中用户中止了操作，未获得最终结果。


## 四、已下载文件清单

| 文件 | 路径 | 大小 | 状态 |
|------|------|------|------|
| llama-cli.exe (b9260) | `venv/llama/llama-cli.exe` | ~18 MB 解压目录 | ✅ 可用 |
| llama-server.exe (b9260) | `venv/llama/llama-server.exe` | 同上 | ✅ 可用 |
| HunyuanOCR.Q4_K_M.gguf | `D:\yidongyunpan\sync\install\models\` | 355 MB | ✅ 完整 |
| HunyuanOCR.mmproj-Q8_0.gguf | `D:\yidongyunpan\sync\install\models\` | 733 MB | ✅ 完整 |

### 临时文件（已清理）

| 文件 | 路径 | 状态 |
|------|------|------|
| 下载脚本 | `venv/tmp/download-hunyuanocr.py` | ✅ 保留 |
| 下载脚本 | `venv/tmp/download-llama-b10069.py` | ✅ 保留 |
| 下载脚本 | `venv/tmp/redownload-mmproj.py` | ✅ 保留 |
| 下载脚本 | `venv/tmp/download-mmproj-reliable.py` | ✅ 保留 |
| OCR 输出（HunyuanOCR） | `venv/tmp/ocr-hunyuanocr*.txt` | ❌ 已清理 |
| OCR 输出（GLM-OCR） | `venv/tmp/ocr-glm-ocr-full.txt` | ❌ 已清理 |
| Server 日志 | `venv/tmp/llama-server-*.log` | ❌ 已清理 |


## 五、结论

### 5.1 HunyuanOCR-1.5 本地 llama.cpp CPU 验证

**未通过**。原因：
1. **版本不兼容**：b9263+ 的 llama.cpp 不支持现有 GGUF 的 projector type
2. **输出异常**：b9260 虽能加载模型，但推理输出乱码/无限重复，无法使用
3. **性能瓶颈**：CPU 推理 1B VLM 极慢，不具备交互式可用性

### 5.2 GLM-OCR 对照

**验证通过**。同环境下 GLM-OCR 可正常输出中文 OCR 结果，证明 llama.cpp b9260 + VLM 推理链路本身无问题，问题出在 HunyuanOCR 的 chat template / tokenizer 适配。

### 5.3 后续可行路径

| 路径 | 可行性 | 说明 |
|------|--------|------|
| vLLM / transformers 原生推理 | ✅ 推荐 | 官方优先支持的方式 |
| Ollama / LM Studio | ⚠️ 待验证 | 可能内置正确 chat template |
| 使用 GLM-OCR 替代 | ✅ 立即可用 | 同环境已验证通过 |
| llama.cpp 源码编译最新版 + 自行转换 GGUF | ⚠️ 不确定 | 官方文档提供转换脚本，但未验证 |


## 六、踩坑记录（Agent 反思）

1. **未先调研再执行**：直接套用简单 prompt 测试 HunyuanOCR，未先查阅官方推荐的 prompt 格式和采样参数
2. **参数移植错误**：将 HunyuanOCR 的官方 prompt 和参数（`--single-turn`、`--temp 0.0` 等）直接套用到 GLM-OCR，两种模型的 chat template 不同
3. **网络下载不稳定**：urllib 默认下载多次因网络中断导致文件不完整，应优先使用 `requests` + resume 或 `huggingface_hub`
4. **用户明确要求 hf-mirror 为主**：国内下载应优先使用 `hf-mirror.com`，不应默认尝试 huggingface.co 直连
5. **执行效率低**：反复试错而非先制定方案再执行，浪费用户时间


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-20-173843 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求实际执行 HunyuanOCR 本地验证 |
| **下次修订条件** | 若后续改用 vLLM / Ollama / transformers 等方式重新验证，或成功跑通 GLM-OCR 完整输出 |
| **跨环境迁移参考** | 模型文件在 `D:\yidongyunpan\sync\install\models\`，llama.cpp 在 `venv/llama/` |
