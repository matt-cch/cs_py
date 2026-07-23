---
title: Zvec 与 SQLite+sqlite-vec 对比分析
description: 围绕 BM25、FTS、向量存储与搜索、Rerank 等维度，对阿里巴巴 Zvec 与 sqlite-vec 进行多源交叉验证与场景化选型分析。
date: 2026-07-20
meta:
  version: "1.0.0"
  sources:
    - "https://github.com/alibaba/zvec"
    - "https://github.com/asg017/sqlite-vec"
    - "https://zvec.org/en/docs/db/"
    - "https://alexgarcia.xyz/sqlite-vec/"
---

# Zvec 与 SQLite+sqlite-vec 对比分析

> 分析日期：2026-07-20
> 信息来源：GitHub 官方仓库、官方文档、Issue/PR 追踪

## 一、项目定位与架构差异

| 维度 | **Zvec** (alibaba/zvec) | **sqlite-vec** (asg017/sqlite-vec) |
|------|------------------------|-----------------------------------|
| **定位** | 独立进程内向量数据库 | SQLite 扩展（loadable extension） |
| **实现语言** | C++ (80.8%) | 纯 C |
| **Stars** | 15.2k | 7.9k |
| **成熟度** | v0.5.1，已生产级（阿里内部 battle-tested） | v0.1.9，pre-v1，breaking changes 预期 |
| **运行环境** | 笔记本/服务器/边缘设备 | 任何 SQLite 能运行的地方（含 WASM、浏览器、树莓派） |
| **持久化** | 独立 collection 目录 + WAL | 依赖 SQLite 的页式存储 |
| **并发模型** | 多进程读，单进程写 | 依赖 SQLite 的并发模型 |

## 二、BM25 与全文搜索（FTS）

### Zvec：原生内置 FTS

Zvec 在 **v0.5.0** 引入了原生 Full-Text Search，是**开箱即用**的完整文本检索引擎：

| 能力 | 实现细节 |
|------|---------|
| **索引结构** | 倒排索引（Inverted Index） |
| **评分算法** | **BM25**（Okapi BM25），含 TF、IDF、文档长度归一化 |
| **查询优化** | **WAND (Weak AND)** + Block-Max 策略，128 文档块级快速跳过 |
| **查询类型** | 自然语言查询、精确短语匹配 `"vector database"`、布尔表达式 `+machine -neural` |
| **Tokenizer** | `standard` (Unicode UAX #29，类 ES)、`whitespace`、`jieba`（中文） |
| **Token Filters** | `lowercase`、`stemmer`、`ascii_folding` |
| **混合检索** | 单查询中可同时融合 FTS + 稠密向量 + 稀疏向量 + scalar filter |

**用法示例**（Python）：
```python
results = collection.query(
    zvec.Query(field_name="content", fts="machine learning"),
    topk=10
)
```

### sqlite-vec：不内置 FTS，需外挂 FTS5

sqlite-vec **本身不提供 FTS 能力**。它是纯粹的向量搜索扩展，文本搜索必须依赖 SQLite 原生的 **FTS5** 虚拟表：

| 能力 | 实现细节 |
|------|---------|
| **BM25** | 由 FTS5 的 `bm25()` 函数提供，非 sqlite-vec 内置 |
| **集成方式** | 应用层手动维护 FTS5 表与 vec0 表，通过 `rowid` 交叉引用（Issue #48 讨论） |
| **混合检索** | **无原生支持**。需分别查 FTS5 和 vec0，再在应用层合并结果 |
| **方案复杂度** | 需要自行处理外部内容表、ID 对齐、分数归一化 |

**用法示例**（需手动建两张表）：
```sql
-- FTS5 表负责文本
CREATE VIRTUAL TABLE docs_fts USING fts5(
  title, content, content='docs', content_rowid='id'
);

-- vec0 表负责向量
CREATE VIRTUAL TABLE docs_vec USING vec0(embedding float[768]);

-- 混合查询需在应用层合并两个结果集
```

## 三、向量存储与搜索

### 向量索引对比

| 索引类型 | **Zvec** | **sqlite-vec** |
|---------|---------|---------------|
| **Flat (暴力)** | ✅ | ✅（当前唯一方式） |
| **HNSW** | ✅ | ❌（规划中，Issue #25） |
| **HNSW-RaBitQ** | ✅（量化加速） | ❌ |
| **DiskANN** | ✅（v0.5.0 新增，磁盘索引省内存） | ❌ |
| **IVF** | ✅ | ❌（规划中） |

> **关键差异**：sqlite-vec 当前（v0.1.9）**只有 brute-force 暴力搜索**，作者明确表示在 v1 前会引入 ANN 索引（IVF/HNSW/DiskANN 候选），但目前超过 1M 向量的大型数据集会显著变慢。

### 向量类型支持

| 类型 | **Zvec** | **sqlite-vec** |
|------|---------|---------------|
| Dense FP32 | ✅ | ✅ |
| Dense FP16 | ✅ | ❌ |
| Dense INT8 | ✅ | ✅ |
| Binary / Bit | ❌ | ✅ |
| Sparse FP32 | ✅ | ❌ |
| Sparse FP16 | ✅ | ❌ |

## 四、Rerank（重排序）

### Zvec：内置 Hybrid Reranking

Zvec 的 **Hybrid Retrieval**（v0.5.0）在**单次查询调用**中即包含 reranking：

- 支持将 **全文检索、稠密向量、稀疏向量** 的结果在内部融合
- 配合 scalar filtering 做前置过滤
- 文档明确提到 `reranking` 作为 hybrid search 的一环

### sqlite-vec：MMR 多样性重排（PR 阶段）

sqlite-vec 对 rerank 的理解是**结果多样性优化**，而非 hybrid fusion：

- **PR #267**（尚未合并）引入了 **MMR (Maximal Marginal Relevance)** 重排
- 用途：解决 KNN 结果过于集中（cluster monopoly）的问题，平衡相关性 vs 多样性
- API：通过隐藏列 `mmr_lambda` 在 SQL 查询中指定

```sql
-- 标准 KNN：返回 1, 2, 3（集中在 [1,0,0,0] 附近）
SELECT rowid, distance FROM vec_items
WHERE embedding MATCH '[1,0,0,0]' AND k = 3;

-- MMR 重排：λ=0.5 时返回 1, 5, 4（打散聚类）
SELECT rowid, distance FROM vec_items
WHERE embedding MATCH '[1,0,0,0]' AND k = 3 AND mmr_lambda = 0.5;
```

> **注意**：MMR 解决的是**多样性**，不是 FTS+向量 的混合分数融合。sqlite-vec 目前没有内置的 cross-encoder 或 hybrid score fusion 机制。

## 五、应用场景与选型建议

### 选 Zvec，如果你需要：

- **开箱即用的 RAG**：需要 BM25 + 向量 + sparse vector + rerank 一站式解决
- **中文场景**：内置 jieba 分词，中文 FTS 无需额外配置
- **大规模数据**：HNSW/DiskANN 支持亿级向量毫秒级查询
- **生产级可靠性**：WAL + 阿里内部 battle-tested
- **混合检索一体化**：单次 API 调用完成多路召回与融合

### 选 SQLite + sqlite-vec，如果你需要：

- **极简部署**：单文件数据库，WASM 可在浏览器运行
- **已有 SQLite 生态**：不想引入新的数据库，只给现有 SQLite 加向量能力
- **小型数据集**：暴力搜索在 <100k 向量时完全够用，且精确度 100%
- **边缘/嵌入式**：树莓派、移动端等受限环境
- **SQL 原生体验**：所有操作都是 `CREATE VIRTUAL TABLE` / `SELECT`，无额外抽象层

## 六、能力矩阵速查

| 能力 | Zvec | SQLite + sqlite-vec |
|------|------|---------------------|
| **BM25 评分** | ✅ 原生内置 | ⚠️ 依赖 FTS5 外挂 |
| **FTS 全文索引** | ✅ 原生倒排索引 + WAND | ⚠️ 需自建 FTS5 表 |
| **向量暴力搜索** | ✅ | ✅ |
| **ANN 近似搜索** | ✅ HNSW/DiskANN/IVF | ❌ 仅 brute-force（规划中） |
| **Sparse Vector** | ✅ | ❌ |
| **Hybrid Search（原生）** | ✅ 单查询融合 | ❌ 应用层手动合并 |
| **Rerank（混合分数）** | ✅ 内置 | ❌ |
| **Rerank（多样性 MMR）** | ❌ | ⚠️ PR #267 未合并 |
| **中文分词** | ✅ jieba tokenizer | ⚠️ 依赖 FTS5 配置 |
| **WASM/浏览器** | ❌ | ✅ |
| **多语言 SDK** | Python/Node/Go/Rust/Dart | Python/Node/Ruby/Go/Rust |

## 七、信息来源汇总

| 来源 | 状态 |
|------|------|
| alibaba/zvec GitHub README + Docs | ✅ 直接访问 |
| zvec.org 官方文档（FTS / Vector Index / Data Modeling） | ✅ 直接访问 |
| asg017/sqlite-vec GitHub README | ✅ 直接访问 |
| sqlite-vec 官方文档站点 | ✅ 直接访问 |
| sqlite-vec Issue #25（ANN 索引追踪） | ✅ 直接访问 |
| sqlite-vec Issue #48（FTS5 集成讨论） | ✅ 直接访问 |
| sqlite-vec PR #267（MMR reranking） | ✅ 直接访问 |
