---
title: HunyuanOCR-1.5 模型调研与本地 llama.cpp CPU 验证准备
description: 记录对腾讯 HunyuanOCR-1.5 轻量级 OCR VLM 的多方调研过程，包括模型大小、GGUF 现成量化版本、llama.cpp 本地验证方案及测试图片选定。
date: 2026-07-20
meta:
  version: "1.0.0"
  filename_timestamp: "2026-07-20-151258"
---

# HunyuanOCR-1.5 模型调研与本地 llama.cpp CPU 验证准备

> **Session 主题**：HunyuanOCR-1.5 模型大小确认、GGUF 现成版本发现、本地 llama.cpp CPU 验证方案制定与测试图片选定
> **日期**：2026-07-20
> **文件名时间戳**：2026-07-20-151258
> **触发原因**：用户阅读头条文章《腾讯混元推出又快又强的轻量级文字识别大模型 HunyuanOCR-1.5》后，要求多方求证模型大小、下载可行性、llama.cpp 本地验证方式及注意事项
> **影响范围**：调研结论记录 + 实际验证执行；已下载 llama.cpp 二进制与模型文件
> **风险等级**：低（纯验证性质，无生产环境变更）

---

## 一、模型基本信息（多方交叉验证）

| 来源 | 指标 | 数值 |
|------|------|------|
| HuggingFace `tencent/HunyuanOCR` 文件列表 | `model.safetensors`（主权重） | **2.24 GB** |
| HuggingFace 仓库总大小 | 含 tokenizer、dflash 草稿模型等 | **4.62 GB** |
| arXiv:2607.04884 / 文章正文 | 参数规模 | **~1B**（十亿） |
| 文章正文 | DFlash 草稿模型 | **90.7M**（约主模型 1/10） |

**结论**：safetensors 格式下约 2.2 GB（FP16）。若转换为 GGUF 量化格式，体积大幅缩减。

---

## 二、现成 GGUF 版本发现（无需自行转换）

通过 HuggingFace 全文搜索 `HunyuanOCR gguf`，确认多个社区量化版本已开放下载：

| 仓库 | 维护者 | 说明 |
|------|--------|------|
| **mradermacher/HunyuanOCR-GGUF** | 社区量化专家 | 最完整的量化矩阵（Q2_K ~ F16）+ mmproj 视觉投影层 |
| **ggml-org/HunyuanOCR-GGUF** | llama.cpp 官方组织 | 官方背书版本 |
| **AnandSingh/hunyuanocr-GGUF** | 社区 | 提供多种量化格式 |

### 推荐：mradermacher/HunyuanOCR-GGUF

该仓库提供了完整的量化梯度 + mmproj，可直接供 llama.cpp CPU 推理：

| 文件 | 大小 | 用途 |
|------|------|------|
| `HunyuanOCR.Q4_K_M.gguf` | **355 MB** | 主模型（decoder）— **推荐，精度与速度平衡** |
| `HunyuanOCR.Q5_K_M.gguf` | **400 MB** | 主模型 — 更高精度 |
| `HunyuanOCR.Q8_0.gguf` | **578 MB** | 主模型 — 接近无损 |
| `HunyuanOCR.f16.gguf` | **1.08 GB** | 主模型 — 无损 FP16 |
| `HunyuanOCR.mmproj-Q8_0.gguf` | **733 MB** | 视觉投影层（**VLM 推理必须**） |
| `HunyuanOCR.mmproj-f16.gguf` | **953 MB** | 视觉投影层（无损） |

**CPU 验证推荐组合**：`Q4_K_M (355 MB) + mmproj-Q8_0 (733 MB)` = **约 1.1 GB 总下载**

---

## 三、llama.cpp 本地验证方案

### 3.1 官方支持依据

- GitHub `Tencent-Hunyuan/HunyuanOCR` 根目录下有 `llama_cpp/` 目录
- 官方 README 明确说明："HunyuanOCR-1.5 also supports **CPU / consumer-GPU / laptop** deployment through `llama.cpp`"
- 专门文档：`docs/llama_cpp.md`

### 3.2 llama-cli 可直接验证（非必须用 server）

从 HuggingFace 模型页官方集成说明中，两种方式并列：

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| **Server** | `llama serve -hf mradermacher/HunyuanOCR-GGUF:Q4_K_M` | 启动 OpenAI-compatible 服务 |
| **CLI** | `llama cli -hf mradermacher/HunyuanOCR-GGUF:Q4_K_M` | **终端直接对话，单次验证** |

### 3.3 llama-cli VLM 关键参数

HunyuanOCR 是**视觉语言模型（VLM）**，`llama-cli` 在新版本中已支持 `--image` 参数：

```powershell
# 预编译二进制直接运行
./llama-cli.exe `
    --model  HunyuanOCR.Q4_K_M.gguf `
    --mmproj HunyuanOCR.mmproj-Q8_0.gguf `
    --image  ./test-image.jpeg `
    --prompt "Extract all text from this image." `
    --ctx-size 10240 --n-predict 4096
```

**关键约束**：
- llama-cli 版本必须足够新（2024 下半年后），才支持 `--image` 和 VLM 推理
- **必须带 `--mmproj`**：缺少视觉投影层会导致模型"看不见"图片，输出纯幻觉
- Prompt 格式需符合 VLM 模板（如 `<image>\nDescribe this image`），参考模型卡示例

### 3.4 跳过 cmake 的三种方式

| 方式 | 步骤 | 说明 |
|------|------|------|
| **A. llama.app 一键安装** | `winget install llama.cpp` | 最简单，自动处理 PATH |
| **B. 预编译二进制** | 从 GitHub Releases 下载 `llama-server.exe` + `llama-cli.exe` | 无需编译，解压即用 |
| **C. Docker** | `docker model run hf.co/mradermacher/HunyuanOCR-GGUF:Q4_K_M` | 容器化，无环境污染 |

**推荐方式 B**：下载预编译二进制到 `venv/llama.cpp/` 或临时目录，执行验证。

---

## 四、测试图片选定

从 `out/articles/` 目录中物色候选图片，最终用户选定：

| 属性 | 值 |
|------|-----|
| **路径** | `out\articles\opencode系统性入门-06-lsp神器加持代码重构从未如此简单_files\img-002.jpeg` |
| **来源文章** | 《OpenCode 系统性入门 06：LSP 神器加持，代码重构从未如此简单》（知乎） |
| **内容特征** | 中英文混合正文 + **标准三列表格**（功能 / 传统方式 / LSP 方式，5 行数据）+ 知乎水印 `@大熊掌门` |
| **表格内容** | 查找定义、查找引用、重命名、代码分析、类型检查 |
| **OCR 难度** | ⭐⭐⭐ 中等（清晰白底、标准字体、表格边框明确、有水印干扰） |

**验证价值**：
- ✅ 中文正文识别（段落 + 列表项）
- ✅ 英文术语识别（LSP, AST-Grep, VSCode, IDE, AI）
- ✅ 表格结构还原（3 列 × 5 行）
- ✅ 水印文字识别（右下角 `@大熊掌门`）

---

## 五、实际验证执行记录

### 5.1 环境准备

| 步骤 | 结果 | 说明 |
|------|------|------|
| llama.cpp 二进制下载 | ✅ 成功 | 先后测试 b10069（最新）和 b9260 两个版本 |
| HunyuanOCR.Q4_K_M.gguf | ✅ 完整 | 355 MB，与官方大小一致 |
| HunyuanOCR.mmproj-Q8_0.gguf | ✅ 完整 | 733 MB，hf-mirror 下载 |
| GLM-OCR 对照验证 | ✅ 通过 | 同环境下 GLM-OCR Q8_0 + mmproj 正常输出中文 OCR 结果 |

### 5.2 llama-cli 直接推理（失败）

**b10069（最新版）**：
- 错误：`load_hparams: unknown projector type: hunyuanocr`
- 原因：b9263 后 llama.cpp 将 HunyuanOCR 合并入 HunyuanVL 架构，导致旧版 GGUF 的 projector type 不被识别
- 结论：**b9263 及以上版本不兼容 mradermacher/HunyuanOCR-GGUF**

**b9260（issue #23481 报告的最后可用版本）**：
- 模型加载：✅ 成功（主模型 + mmproj 均正常加载）
- 图像编码：✅ 成功（图像被正确读入）
- 推理输出：❌ **乱码/无限重复**（如 `"海洋海洋海洋..."`、`"roughly roughly..."`、`"sau sau sau..."`）
- 官方 prompt + 官方采样参数（temp=0, top_p=1, repeat_penalty=1.08）均无法改善

### 5.3 llama-server + OpenAI API（超时放弃）

- Server 启动：✅ 正常，模型加载成功
- API 请求：❌ **超时**（600 秒仍未返回）
- 原因：CPU 推理 1B VLM + 图像编码 + 长文本生成，速度极慢，不具备实用价值
- 用户反馈：执行效率过低，不具备可用性

### 5.4 关键发现

| 发现 | 来源 | 影响 |
|------|------|------|
| llama.cpp b9263 合并 HunyuanOCR 到 HunyuanVL | GitHub PR #23329 | 新版 llama.cpp 不兼容现有 GGUF |
| b9260 虽能加载但输出异常 | 实测 | 本地 llama.cpp CPU 推理不可靠 |
| 官方推荐 server 方式而非 cli | HuggingFace 模型卡 | cli 对 VLM chat template 支持不完善 |
| CPU 推理速度极慢 | 实测 | 单次请求 >10 分钟，无实用价值 |

---

## 六、结论与建议

### 6.1 当前状态

**本地 llama.cpp CPU 验证未通过**。虽然模型文件完整、环境配置正确、GLM-OCR 对照正常，但 HunyuanOCR 在 llama.cpp 下的输出异常（乱码/超时），不具备可用性。

### 6.2 可能原因

1. **版本适配问题**：mradermacher 量化的 GGUF 可能针对特定 llama.cpp 版本生成，与 b9260 的 chat template 处理存在错位
2. **chat template 不匹配**：llama-cli/llama-server 对 HunyuanOCR 的 `<｜hy_begin▁of▁sentence｜>` 等特殊 token 处理可能不正确
3. **CPU 推理性能瓶颈**：1B VLM 在纯 CPU 下推理速度过慢，server 方式单次请求超时

### 6.3 后续可行路径

| 路径 | 可行性 | 说明 |
|------|--------|------|
| **vLLM / transformers 原生推理** | ✅ 推荐 | 官方优先支持的方式，精度有保障 |
| **llama.cpp 自行编译最新源码** | ⚠️ 不确定 | 需从源码编译，且 DFlash 适配在 fork 中，非主线 |
| **使用 GLM-OCR 替代** | ✅ 立即可用 | 同环境下 GLM-OCR 验证通过，输出正常 |
| **Ollama / LM Studio 等封装工具** | ⚠️ 待验证 | 可能内置了正确的 chat template 和参数 |

---

## 七、待执行任务

| # | 任务 | 状态 | 说明 |
|---|------|------|------|
| 1 | 下载 llama.cpp 预编译二进制 | ✅ 完成 | b9260 和 b10069 均已测试 |
| 2 | 下载 HunyuanOCR GGUF 模型 | ✅ 完成 | Q4_K_M + mmproj-Q8_0 已就位 |
| 3 | llama-cli 直接推理验证 | ❌ 失败 | 输出乱码，无法使用 |
| 4 | llama-server API 验证 | ❌ 放弃 | CPU 推理过慢，超时 |
| 5 | 记录验证结果与踩坑笔记 | 🔄 进行中 | 本文档即记录 |

---

## 八、依赖与注意事项

| 项目 | 说明 |
|------|------|
| **模型 License** | Tencent Hunyuan Community License Agreement（非标准开源协议，商用需审阅条款） |
| **llama-cli 版本** | b9260 为 issue 报告的最后可用版本，但实际输出仍异常；b9263+ 不兼容 |
| **磁盘空间** | 模型文件约 1.1 GB + llama 二进制约 18 MB |
| **内存需求** | Q4_K_M 下模型加载约需 2-4 GB RAM |
| **CPU 推理速度** | 1B VLM 纯 CPU 推理极慢，单次请求 >10 分钟，不适合交互式使用 |
| **推荐替代方案** | GLM-OCR（同环境已验证通过）或 vLLM/transformers 原生推理 |

---

## 九、验证清单（实际执行结果）

| # | 验证步骤 | 结果 | 备注 |
|---|---------|------|------|
| 1 | 确认 llama-cli 可执行 | ✅ | b9260 和 b10069 均可执行 |
| 2 | 确认 GGUF 文件完整性 | ✅ | 两个文件大小均匹配官方 |
| 3 | GLM-OCR 对照验证 | ✅ | 同环境下正常输出中文 OCR |
| 4 | HunyuanOCR 模型加载 | ✅ | b9260 下主模型 + mmproj 加载成功 |
| 5 | HunyuanOCR 图像编码 | ✅ | 图像被正确读入 |
| 6 | HunyuanOCR 推理输出质量 | ❌ | 乱码/无限重复，无法使用 |
| 7 | HunyuanOCR server 方式 | ❌ | CPU 推理超时，不具备可用性 |

---

## 十、信息来源汇总

| 来源 | 状态 | 用途 |
|------|------|------|
| arXiv:2607.04884 | ✅ 直接访问 | 确认论文、模型参数、DFlash 技术细节 |
| HuggingFace `tencent/HunyuanOCR` | ✅ 直接访问 | 确认官方 prompt 格式、采样参数、使用示例 |
| HuggingFace `mradermacher/HunyuanOCR-GGUF` | ✅ 直接访问 | 确认 GGUF 量化矩阵与文件大小 |
| GitHub `Tencent-Hunyuan/HunyuanOCR` | ✅ 直接访问 | 确认 llama.cpp 官方支持文档与转换脚本 |
| GitHub llama.cpp Issue #23481 | ✅ 直接访问 | 确认 b9263 后 HunyuanOCR 合并入 HunyuanVL，导致兼容性问题 |
| 头条文章下载（download-article.py） | ✅ 成功执行 | 触发本次调研的原始材料 |

---

## 十一、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-07-20-151258 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户阅读头条文章后要求多方求证模型与验证方案 |
| **下次修订条件** | 若后续改用 vLLM / transformers / Ollama 等方式重新验证，更新结果 |
| **跨环境迁移参考** | 本调研结论可直接复用；实际验证时需重新下载二进制与模型 |
