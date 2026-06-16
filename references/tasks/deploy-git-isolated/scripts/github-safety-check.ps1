<#
.SYNOPSIS
    综合 Git 安全检查。
.DESCRIPTION
    点源导入 github-lib.ps1 后调用 Invoke-GitSafetyCheck，输出 tracked/staged/未跟踪/敏感屏蔽状态。
    供 push 前人工确认，避免敏感文件意外上传。
.PARAMETER None
.NOTES
    Encoding: UTF-8 with BOM
#>

# 提前切换编码，确保 github-lib 加载输出也为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 引用点源（共享库）
$libPath = Join-Path $PSScriptRoot "github-lib.ps1"
. $libPath

Switch-ToUtf8
try {
    Invoke-GitSafetyCheck
} finally {
    Restore-Encoding
}
