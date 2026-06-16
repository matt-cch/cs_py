<#
.SYNOPSIS
    Step 5: git commit。
.DESCRIPTION
    提交 staged 文件，使用标准 init commit message。
.PARAMETER Message
    可选：自定义 commit message。默认 "init: empty scaffold with safety gitignore"。
.NOTES
    Encoding: UTF-8 with BOM
#>
param(
    [string]$Message = "init: empty scaffold with safety gitignore"
)

# 提前切换编码，确保 github-lib 加载输出也为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$libPath = Join-Path $PSScriptRoot "github-lib.ps1"
. $libPath

Switch-ToUtf8
try {
    Write-StepHeader -Title "Step 5: git commit"
    Test-IsolatedGit

    Set-Location $devroot
    & $gitExe commit -m "$Message"
    if ($LASTEXITCODE -ne 0) { throw "git commit 失败" }

    Write-Host "[OK] commit 完成: $Message"

} finally {
    Restore-Encoding
}
