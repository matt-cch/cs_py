---
title: env-migration — 唐彪5月工作报告PPT生成 + references/scripts/ 图片工具链建设
description: 生成数据驱动可编辑PPT（v1→v4），建设 references/scripts/ 通用工具链（pptx/image/tavily），端到端验证图片下载能力。
date: 2026-06-10
---

# env-migration-tangbiao-may-report-pptx-and-image-toolchain-2026-06-10-220000

## 元信息

| 字段 | 填写示例 |
|------|---------|
| **Session 主题** | 唐彪5月工作报告PPT生成（v1→v4演进）+ references/scripts/ 图片工具链建设 |
| **日期** | 2026-06-10 |
| **文件名时间戳** | `2026-06-10-220000` |
| **触发原因** | 用户要求生成唐彪5月工作报告PPT，要求可编辑、数据驱动、含真实图片；同时建设可复用的通用工具链 |
| **影响范围** | `out/` 输出目录、`references/scripts/` 工具链目录、`debug/` 调试脚本目录 |
| **风险等级** | 低（纯新增文件，不影响既有业务代码或环境配置） |


## 一、文本文件变更清单

### 1. 新建 `out/reports/tangbiao-may-report-outline.md`

| 属性 | 值 |
|------|-----|
| **路径** | `out/reports/tangbiao-may-report-outline.md` |
| **变更类型** | `新建` |
| **内容** | 8页PPT内容大纲，含数据源分析（2026年5月应收结算单61条记录、¥1.15M总额、86.9%毛利率）、客户拜访、工作进展、总结计划 |
| **作用** | 作为PPT生成的内容真源，数据从 `应收结算单维度5月份2026.xlsx` 等文件提取 |
| **迁移方式** | 直接复制 |

### 2. 新建 `debug/pptx-generator/generate_tangbiao_may_report.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/pptx-generator/generate_tangbiao_may_report.py` |
| **变更类型** | `新建` |
| **内容** | 多模式PPT生成调度器，支持 `--mode no-image` / `--mode with-image` |
| **作用** | v1/v2 版本生成器，使用抽象几何图形作为占位图 |
| **迁移方式** | 直接复制 |

### 3. 新建 `debug/pptx-generator/generate_tangbiao_v4.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/pptx-generator/generate_tangbiao_v4.py` |
| **变更类型** | `新建` |
| **内容** | v4 物流主题具象设计生成器，使用原生 python-pptx 形状（shipping label、container door、nautical log） |
| **作用** | 替代抽象几何图形，用物流/航运意象增强视觉表达 |
| **迁移方式** | 直接复制 |

### 4. 新建 `debug/pptx-generator/image_toolkit_verify.py`

| 属性 | 值 |
|------|-----|
| **路径** | `debug/pptx-generator/image_toolkit_verify.py` |
| **变更类型** | `新建` |
| **内容** | 端到端图片工具链验证脚本：源探测 → 搜索 → 下载 → 魔数校验 |
| **作用** | 验证 image/ 工具链各模块能否协同工作 |
| **迁移方式** | 直接复制 |

### 5. 新建 `references/scripts/pptx/primitives.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/scripts/pptx/primitives.py` |
| **变更类型** | `新建` |
| **内容** | python-pptx 原子组件库：颜色管理、形状绘制、文本框、柱状图、面积图、表格、边框装饰 |
| **作用** | 供所有 PPT 生成脚本复用的底层组件库 |
| **迁移方式** | 直接复制 |
| **验证方式** | `python -m py_compile references/scripts/pptx/primitives.py` 应通过 |

### 6. 新建 `references/scripts/image/probe.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/scripts/image/probe.py` |
| **变更类型** | `新建` |
| **内容** | 图片源可用性探测：HTTP 状态码、响应延迟、HTML 陷阱检测 |
| **作用** | 探测 Unsplash/Pexels/Pollinations.ai/Pixabay 等源的实际可用性 |
| **迁移方式** | 直接复制 |

### 7. 新建 `references/scripts/image/search.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/scripts/image/search.py` |
| **变更类型** | `新建` |
| **内容** | 多源图片搜索聚合：Tavily AI 搜索 + 正则提取直链 + fallback 固定 URL |
| **作用** | 将 Tavily 搜索结果转换为可下载的图片 URL |
| **迁移方式** | 直接复制 |
| **已知局限** | Tavily 返回的是页面链接而非直链，正则提取模块对 `images.unsplash.com` 直链提取不够鲁棒，当前依赖 fallback URL |

### 8. 新建 `references/scripts/image/download.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/scripts/image/download.py` |
| **变更类型** | `新建` |
| **内容** | 图片下载器：HTTP Range 请求、JPEG/PNG 魔数校验（拒绝 HTML 陷阱）、文件头检测 |
| **作用** | 安全下载图片，确保文件是真实图像而非代理广告页 |
| **迁移方式** | 直接复制 |

### 9. 新建 `references/scripts/tavily/search.py`

| 属性 | 值 |
|------|-----|
| **路径** | `references/scripts/tavily/search.py` |
| **变更类型** | `新建` |
| **内容** | Tavily AI Search 封装：自动读取 `.env` 中的 `TAVILY_API_KEY`，支持 `search` / `context` 模式 |
| **作用** | 为 image/search.py 和 future 工具提供统一的 Tavily 调用接口 |
| **迁移方式** | 直接复制 |
| **环境依赖** | 需要 `TAVILY_API_KEY` 环境变量（`.env` 中已配置） |

### 10. 新建 `references/scripts/README.md`

| 属性 | 值 |
|------|-----|
| **路径** | `references/scripts/README.md` |
| **变更类型** | `新建` |
| **内容** | 目录自说明：子目录导航（pptx/ image/ tavily/）、设计原则（按领域拆分、不堆根目录） |
| **作用** | 人类/Agent 快速理解 references/scripts/ 的组织结构 |
| **迁移方式** | 直接复制 |

### 11. 新建 `references/scripts/manifest.json`

| 属性 | 值 |
|------|-----|
| **路径** | `references/scripts/manifest.json` |
| **变更类型** | `新建` |
| **内容** | 机器可读脚本索引：目录列表、脚本元信息（status/verified_at/dependencies/entrypoint/test_cmd） |
| **作用** | Agent 执行时可快速查询有哪些现成工具可用，避免重复造轮子 |
| **迁移方式** | 直接复制 |
| **状态更新** | image/ 下 3 个脚本已从 `planned` 更新为 `verified` |


## 二、非文本操作（文件系统/缓存迁移）

| 操作类型 | 源路径 | 目标路径 | 说明 |
|---------|--------|---------|------|
| 文件生成 | — | `out/ppt-master-projects/tangbiao-may-report/唐彪5月份工作汇报v1.pptx` | v1：无图版，柱状图+面积图+表格 |
| 文件生成 | — | `out/ppt-master-projects/tangbiao-may-report/唐彪5月份工作汇报v2.pptx` | v2：带占位图版，抽象几何图形 |
| 文件生成 | — | `out/ppt-master-projects/tangbiao-may-report/唐彪5月份工作汇报v3.pptx` | v3：去除遮罩版 |
| 文件生成 | — | `out/ppt-master-projects/tangbiao-may-report/唐彪5月份工作汇报v4.pptx` | v4：物流主题具象版（shipping label/container door/nautical log） |
| 图片下载 | `images.unsplash.com` | `out/ppt-master-projects/tangbiao-may-report/images/verified_1.jpg` | 物流仓库实景图，184KB，JPEG 魔数通过 |
| 图片下载 | `images.pexels.com` | `out/ppt-master-projects/tangbiao-may-report/images/verified_2.jpg` | 商务团队握手图，50KB，JPEG 魔数通过 |


## 三、环境变量速查

本次 session **不涉及**新的环境变量变更。依赖既有配置：

```bash
# .env 中已配置
TAVILY_API_KEY=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
```


## 四、验证清单（新环境必须执行）

| # | 验证步骤 | 命令/操作 | 期望结果 |
|---|---------|----------|---------|
| 1 | 确认 pptx primitives 语法正确 | `python -m py_compile references/scripts/pptx/primitives.py` | 无输出（通过） |
| 2 | 确认 Tavily 搜索可用 | `python references/scripts/tavily/search.py` | 返回搜索结果 JSON |
| 3 | 确认图片工具链端到端可用 | `python debug/pptx-generator/image_toolkit_verify.py` | 下载 2 张图片，魔数校验通过 |
| 4 | 确认 image/ 各模块可独立导入 | `python -c "from references.scripts.image.probe import probe_all; from references.scripts.image.search import search_images; from references.scripts.image.download import download_image"` | 无报错 |
| 5 | 确认 v4 PPT 可生成 | `python debug/pptx-generator/generate_tangbiao_v4.py` | 生成 `.pptx` 文件 |


## 五、回滚方案

| 回滚步骤 | 命令 |
|---------|------|
| 删除 PPT 输出 | `Remove-Item -Recurse "out/ppt-master-projects/tangbiao-may-report"` |
| 删除 references/scripts/ 新增 | `Remove-Item -Recurse "references/scripts/pptx"`, `Remove-Item -Recurse "references/scripts/image"`, `Remove-Item -Recurse "references/scripts/tavily"`, `Remove-Item "references/scripts/README.md"`, `Remove-Item "references/scripts/manifest.json"` |
| 删除 debug 脚本 | `Remove-Item -Recurse "debug/pptx-generator"` |
| 删除报告大纲 | `Remove-Item "out/reports/tangbiao-may-report-outline.md"` |


## 六、关键决策与踩坑记录

### 决策 1：PPT 版本保留策略
- **结论**：v1/v2/v3/v4 全部保留，不覆盖，供用户对比选择
- **原因**：用户明确要求"每个版本都要保留"，以便评估不同设计方向

### 决策 2：references/scripts/ 按领域拆分
- **结论**：按 `pptx/`、`image/`、`tavily/` 三个子目录拆分，不堆在根目录
- **原因**：AGENTS.md 要求`references/scripts/`下新建路径需说明用途；按领域拆分最清晰

### 决策 3：从抽象几何图形转向物流主题具象设计
- **结论**：v4 放弃 v2 的抽象 Pillow 生成图，改用原生 python-pptx 形状构建物流意象
- **原因**：用户要求"不要用AI生成的抽象图"；Pillow 生成的渐变几何图形属于"AI生成图"范畴

### 踩坑 1：Tavily 搜索结果不含图片直链
- **现象**：`search.py` 正则提取未命中，只能依赖 fallback 固定 URL
- **根因**：Tavily API 返回的是网页链接和内容摘要，不含 `images.unsplash.com` 等直链
- **修复方向**：后续改进正则逻辑，或增加对返回页面 HTML 的二次抓取

### 踩坑 2：Pollinations.ai 免费匿名调用关闭
- **现象**：返回 `402 Payment Required`
- **根因**：服务方关闭了免费匿名 tier
- **修复方向**： probe.py 已标记为 `unavailable`，后续如需使用需配置 API Key

### 踩坑 3：Pexels 直接页面抓取被 403 拦截
- **现象**：`HEAD` 请求返回 403
- **根因**：Pexels 对非浏览器 UA 的请求进行拦截
- **修复方向**：使用 `images.pexels.com` 直链（已通过验证），避免抓取页面 HTML


## 七、文档元信息

| 属性 | 值 |
|------|-----|
| **最后更新** | 2026-06-10-220000 |
| **更新人** | Human + Agent Session |
| **变更触发** | 用户要求生成唐彪5月工作报告PPT + 建设通用工具链 |
| **下次修订条件** | image/search.py 直链提取逻辑改进时、新增 PPT 版本时、图片工具链扩展时 |
| **跨环境迁移参考** | 直接复制本文档 + 按「验证清单」逐条执行 |


*文档生成时间：2026-06-10*  
*模板版本：v2（文件名时间戳：`YYYY-MM-DD-HHmmss`）*
