<#
.SYNOPSIS
    Step 3: 生成顶层 README.md（空架说明）。
.DESCRIPTION
    若 devroot 下无 README.md，则生成一个最小化的空架说明。
.PARAMETER None
.NOTES
    Encoding: UTF-8 with BOM
#>

# 提前切换编码，确保 github-lib 加载输出也为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$libPath = Join-Path $PSScriptRoot "github-lib.ps1"
. $libPath

Switch-ToUtf8
try {
    Write-StepHeader -Title "Step 3: 生成 README.md"

    $readmePath = Join-Path $devroot 'README.md'
    if (Test-Path $readmePath) {
        Write-Host "[SKIP] README.md 已存在，不覆盖"
    } else {
        $cfg = Read-EnvConfig
        $content = @"
# $($cfg.RepoName)

Multi-root dev environment.

## 目录结构（渐进式填充）

| 目录 | 说明 |
|------|------|
| apps/ | 子项目入口（渐进式添加） |

## 安全注意

- 本仓库使用 ".gitignore" 严格屏蔽敏感文件
- 上传前务必检查 diff，确认无密钥/路径泄露
- "venv/" 等隔离工具链不上传
"@
        Set-Content -Path $readmePath -Value $content -Encoding UTF8
        Write-Host "[OK] README.md 已生成"
    }

} finally {
    Restore-Encoding
}
