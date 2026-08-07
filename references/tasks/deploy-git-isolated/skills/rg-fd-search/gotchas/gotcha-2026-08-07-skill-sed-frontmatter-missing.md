---
title: Skill SED 文件 frontmatter 易遗漏 description 和 meta
description: Agent 创建 gotcha/evolution/learning/baseline 等 SED 文件时，常遗漏 frontmatter 的 description 和 meta 字段，导致 run-lint.py 检测失败
date: 2026-08-07
type: gotcha
meta:
  version: "1.0.0"
  tags: [frontmatter, sed, gotcha]
fingerprint:
  content_sha256: gotcha-skill-sed-frontmatter-missing-20260807
  semantic_key: skill-sed-frontmatter-missing
---

# Skill SED 文件 frontmatter 易遗漏 description 和 meta

## 现象

Agent 使用 `write` 工具创建 skill SED 文件（evolution/learning/gotcha/baseline）时，frontmatter 中经常只写 `title` 和 `date`，遗漏 `description` 和 `meta` 字段。

示例：
```yaml
---
title: xxx
date: 2026-08-07
type: evolution
...  # 缺少 description 和 meta
---
```

后续执行 `run-lint.py` 时，md_lint 插件报：
```
❌ 缺少必填字段 description
❌ 缺少必填字段 meta（无内容时写 meta: {}）
```

## 根因

1. Agent 在构造 frontmatter 时，习惯性只填写与类型直接相关的字段（如 `type`、`scope`、`category`），忽略了所有 `.md` 文件通用的 frontmatter 必填项。
2. 不同文档类型（env-migration / evolution / baseline）的 frontmatter 要求不一致，Agent 容易混淆。
3. SKILL.md 的 SED 文件规范中虽然定义了 frontmatter 字段，但未强调 `description` 和 `meta` 为**所有 `.md` 文件的通用必填项**。

## 修复方式

创建 SED 文件时，frontmatter 必须包含：
```yaml
---
title: xxx
description: 一句话说明
date: 2026-08-07
type: xxx
meta:
  version: "1.0.0"
  tags: [xxx]
# 类型特有字段...
---
```

> **硬性规则**：`description` 和 `meta` 是 `.cursor/rules/markdown-docs-format.mdc` 对所有 `.md/.mdc` 文件的**通用必填项**，不因文件类型（env-migration / evolution / gotcha / learning / baseline）而豁免。

## 与现有规则的衔接

- `.cursor/rules/markdown-docs-format.mdc` §1.1 已明确规定：所有 `.md` 文件必须包含 `title` / `description` / `date` / `meta`
- `SKILL.md` §增量内容 frontmatter 规范 中已列出各类型必填字段，但未将 `description` 和 `meta` 标为跨类型通用项

## 关联

- 触发本次 gotcha 的 session：rg-fd-search SED 创建 session 2026-08-07
- 涉及文件：`evolution-2026-08-07-search-scope-extension-to-vaults.md`、`learning-2026-08-07-vaults-env-migrations-division-pattern.md` 初次写入时均触发此问题
