---
title: Plugin Result Schema 规范
description: py_lib 插件体系返回格式的统一契约（默认 dict + JSON Schema，备选 Pydantic Model），确保底层→上层的接口一致性。
date: 2026-06-20
meta:
  version: 1.0.0
---

# Plugin Result Schema 规范

> **版本**: v1.0.0
> **默认实现**: 纯 Dict（零依赖）
> **备选实现**: Pydantic Model（`schema/py/models.py`，需安装 pydantic）
> **适用范围**: `py-plugins/` 下所有插件的 `validate()` / `validate_file()` / `scan()` 方法


## 1. 为什么需要统一 Schema

当前各插件返回格式存在**字段名差异**（如 `lint_python` 用 `error`，`md_lint` 用 `context`），导致上层调用者（`run-lint.py`、`workflow-lint-amend-lint.py`）必须写分支处理：

```python
# 反模式：上层被迫分支
context = v.get("error") or v.get("context", "")
```

统一 Schema 后，上层可**无分支遍历**，逻辑简单、预期一致。


## 2. 核心返回结构（Dict 默认）

所有插件方法必须返回以下结构的 `dict`：

```python
{
    "success": bool,              # 执行是否成功（无异常）
    "schema_version": "1.0.0",    # 格式版本号
    "plugin": str,                # 插件标识名
    "files_scanned": int,         # 扫描文件总数
    "files_with_violations": int, # 含违规文件数
    "violations_found": int,      # 违规总项数
    "violations": [               # 违规详情列表
        {
            "file": str,          # 文件路径（必须）
            "line": int | None,   # 行号（可选）
            "context": str,       # 违规描述（必须）
            "severity": str,      # "error" | "warning" | "info"（默认 "error"）
            "fixable": bool       # 是否可自动修复（默认 False）
        }
    ],
    "metadata": {}                # 插件自定义扩展
}
```

### 2.1 必填字段（6 个）

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 执行是否成功（有 violations 不影响，只有抛异常时才 false） |
| `schema_version` | str | 固定 `"1.0.0"`，未来升级时上层可识别版本差异 |
| `plugin` | str | 插件标识，如 `"lint_python"`、`"md_lint"` |
| `files_scanned` | int | ≥0 |
| `files_with_violations` | int | ≥0 |
| `violations_found` | int | ≥0 |
| `violations` | list | 即使无违规也必须为空列表 `[]` |

### 2.2 violations 条目统一格式

**禁止**使用 `error` 等旧字段名，**统一使用 `context`**：

```python
# ✅ 正确
{"file": "x.py", "line": 12, "context": "语法错误", "severity": "error", "fixable": False}

# ❌ 错误（旧格式，已废弃）
{"file": "x.py", "error": "语法错误"}
```

| 字段 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `file` | ✅ | — | 文件路径 |
| `line` | ❌ | `None` | 行号 |
| `context` | ✅ | — | 违规描述（替代旧 `error`） |
| `severity` | ❌ | `"error"` | 严重程度分级 |
| `fixable` | ❌ | `False` | 是否可自动修复 |

### 2.3 metadata 扩展字段

插件可将自定义数据放入 `metadata`，上层不强制消费：

```python
# lint_encoding 的 fix 结果
"metadata": {
    "files_fixed": 1,
    "fixed_files": [
        {"file": "x.py", "actions": ["去BOM", "CRLF→LF(3)"]}
    ]
}

# md_lint 的 fix 结果
"metadata": {
    "files_fixed": 2
}
```


## 3. 机器可读真源

| 文件 | 格式 | 用途 |
|------|------|------|
| `schema/json/plugin-result-schema.json` | JSON Schema (draft-07) | 机器验证、IDE 提示、文档生成 |
| `schema/docs/plugin-result-schema.md` | Markdown（本文件） | 人类阅读、开发参考 |
| `schema/py/models.py` | Pydantic Model | 备选强类型实现 |


## 4. 备选：Pydantic Model 实现

用户已手工安装 `pydantic` / `pydantic-ai` 依赖。在需要强类型检查的场景（如复杂插件、CI 流水线），可使用 `schema/py/models.py`：

```python
from schema.models import PluginResult, Violation

result = PluginResult(
    plugin="lint_python",
    files_scanned=1,
    files_with_violations=0,
    violations_found=0,
    violations=[]
)

# 自动验证字段类型 + 默认值
dict_result = result.model_dump()
```

### 何时使用 Pydantic 备选

| 场景 | 建议 |
|------|------|
| 简单 lint 插件（5-10 个字段） | 默认 Dict，够用 |
| 复杂工作流（多层嵌套 metadata） | Pydantic Model，类型安全 |
| CI 流水线（需要严格输入校验） | Pydantic Model，运行时验证 |
| 跨团队协作（需要共享接口契约） | Pydantic Model + schema.json 双轨 |

> **原则**：默认走 Dict（零依赖、低门槛），复杂场景可选 Pydantic。二者共享同一 `plugin-result-schema.json` 真源，不分裂。


## 5. 插件改造 checklist

新增/改造插件时，逐条检查：

- [ ] `validate()` / `validate_file()` 返回 dict 包含全部 6 个必填字段
- [ ] `violations` 数组中每项使用 `context` 而非 `error`
- [ ] `violations` 为空时返回 `[]` 而非 `None`
- [ ] `metadata` 存在但无自定义数据时返回 `{}`
- [ ] `plugin` 字段值与 `py-sort-rules.json` 中的 `name` 一致
- [ ] 异常时返回 `success=False` + 空 violations + metadata 含 `error` 信息


## 6. 版本演进

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-06-20 | 初版：统一 6 必填字段 + violations 统一格式 + metadata 扩展 |

升级时同步修改：
1. `json/plugin-result-schema.json` 的 `$id` 和 `version`
2. 所有插件返回的 `schema_version` 字段
3. 上层调用者的版本兼容逻辑（如需）


## 7. 关联文件

| 文件 | 用途 |
|------|------|
| `json/plugin-result-schema.json` | JSON Schema 真源（机器可读） |
| `py/models.py` | Pydantic Model 备选实现 |
| `py-plugins/*.py` | 插件实现，需遵守本规范 |
| `py-tools/run-lint.py` | 上层调用者，消费统一格式 |
| `py-tools/workflow-lint-amend-lint.py` | 上层工作流，消费统一格式 |
