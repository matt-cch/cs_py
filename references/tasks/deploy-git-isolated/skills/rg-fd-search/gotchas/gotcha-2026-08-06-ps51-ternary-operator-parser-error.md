---
title: PowerShell 5.1 不支持三元运算符 ? : 导致 ParserError
description: 按 rg-fd-search skill 中的 PowerShell 示例执行文件存在性验证时，使用 $($exists ? 'OK' : 'MISSING') 语法在 Windows PowerShell 5.1 下触发 ParserError
date: 2026-08-06
type: gotcha
meta:
  version: "1.1.0"
fingerprint:
  content_sha256: "gotcha-ps51-ternary-operator-parser-error-20260806"
  semantic_key: "powershell-5.1-ternary-operator"
---

# PowerShell 5.1 不支持三元运算符 ? : 导致 ParserError

## 现象

按 rg-fd-search skill 工作流执行 Step 4（磁盘存在性验证）时，使用以下 PowerShell 脚本：

```powershell
foreach ($f in $files) {
    $p = Join-Path 'D:\pjt\cursor\cs_py' $f;
    $mark = "$($exists ? 'OK' : 'MISSING')"   # ❌ 错误写法
    Write-Output "$mark  $f"
}
```

执行后触发 ParserError：

```
表达式或语句中包含意外的标记 "?"
+ CategoryInfo          : ParserError
+ FullyQualifiedErrorId : UnexpectedToken
```

## 根因

- **Windows PowerShell 5.1**（`powershell.exe`）**不支持**三元运算符 `? :`
- 该语法是 **PowerShell 7+**（`pwsh.exe`）才引入的特性
- 项目硬性规定默认执行环境为 Windows PowerShell 5.1，脚本中不得使用 PS 7+ 独占语法

## 修复方式

改用传统的 `if/else`：

```powershell
foreach ($f in $files) {
    $p = Join-Path 'D:\pjt\cursor\cs_py' $f;
    if (Test-Path -LiteralPath $p) { $mark = 'OK' } else { $mark = 'MISSING' }   # ✅ 正确写法
    Write-Output "$mark  $f"
}
```

## 涉及命令

```powershell
# 错误（PS 5.1 不支持）
"$($exists ? 'OK' : 'MISSING')"

# 正确（PS 5.1 兼容）
if ($exists) { $mark = 'OK' } else { $mark = 'MISSING' }
```

## 反模式

- 从 PowerShell 7 / VS Code 终端（可能默认 pwsh）复制脚本到项目执行环境
- 使用 `?:`、`.ForEach()`、`.Where()` 等 PS 7+ 语法
- 使用 `ForEach-Object -Parallel` 等 PS 7+ cmdlet

## 验证方式

执行前确认 PowerShell 版本：

```powershell
$PSVersionTable.PSVersion  # Major 应为 5
```

或显式使用兼容语法，不依赖版本推断。

## 关联规则

- `.cursor/rules/high-frequency-shell-guard-content.mdc` — Shell 安全执行
- `AGENTS.md` — PowerShell 脚本编码与运行时环境约束

## 来源

2026-08-06 执行 rg-fd-search skill Step 4（磁盘存在性验证）时触发。
