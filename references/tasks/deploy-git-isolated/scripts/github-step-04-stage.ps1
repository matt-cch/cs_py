<#
.SYNOPSIS
    Step 4: 安全 add（仅 .gitignore + README.md）。
.DESCRIPTION
    只 add 两个安全文件，显示 staged 列表供人工确认，绝不 add 现有业务代码。
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
    Write-StepHeader -Title "Step 4: 安全 add"
    Test-IsolatedGit

    Set-Location $devroot
    & $gitExe add .gitignore
    & $gitExe add README.md

    Write-Host ""
    Write-Host "--- Staged 文件（确认无敏感内容）---"
    & $gitExe status --short
    Write-Host "--------------------------------------"

    $staged = & $gitExe diff --cached --name-only
    Write-Host ""
    Write-Host "本次将提交的文件:"
    foreach ($f in $staged) {
        Write-Host "  - $f"
    }

} finally {
    Restore-Encoding
}
