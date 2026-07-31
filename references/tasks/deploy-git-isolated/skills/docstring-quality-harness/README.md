---
title: docstring-quality-harness 目录说明
description: 本 skill 的目录结构、各子目录职责与文件导航
 date: 2026-07-31
meta:
  version: 0.1.0
---

# docstring-quality-harness 目录说明

本 skill 用于通过委派 subagent 模拟陌生 Agent 初次接触工具的场景，检验工具 docstring 的自说明质量，并渐进式积累 docstring 质量 baseline。

## 目录结构

```
docstring-quality-harness/
├── SKILL.md                          # 核心规范：触发词、测试流程、与现有体系衔接
├── README.md                         # 本文件：目录结构与导航
├── schema/
│   └── audit-manifest-schema.json    # Audit Manifest JSON Schema 定义
├── baseline/
│   └── docstring-quality-baseline.md # 渐进式积累的质量评价基准（可随测试迭代更新）
└── examples/
    └── example-audit-manifest.json   # Audit Manifest 示例（基于 workflow-git-deploy-full-poly.py 实测）
```

## 子目录职责

| 子目录 | 职责 | 更新时机 |
|--------|------|---------|
| `schema/` | 存放数据契约（JSON Schema），定义 Audit Manifest 的字段与校验规则 | schema 结构扩展时 |
| `baseline/` | 存放渐进式积累的质量基准文档，记录评价维度、评分标准、已知问题 | 每次执行 skill 发现新问题时 |
| `examples/` | 存放示例文件，供 Agent 和人类理解输出格式 | 新增典型测试场景时 |

## 使用入口

- **Agent 触发**：命中 SKILL.md 中的触发词后，按 SKILL.md 的"单次测试流程"执行
- **人类查阅**：直接阅读 `SKILL.md` 理解测试方法，阅读 `baseline/` 了解当前质量基准

## 上级导航

- [deploy-git-isolated 任务索引](../../README.md)
- [scripts 目录](../../scripts/)
