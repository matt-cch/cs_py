<#
.SYNOPSIS
    Step 8: 设置 upstream。
.DESCRIPTION
    设置本地分支跟踪 origin，简化后续 push（无需再指定 remote）。
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
    Write-StepHeader -Title "Step 8: 设置 upstream"
    Test-IsolatedGit

    Set-Location $devroot
    $branch = & $gitExe branch --show-current 2>$null

    & $gitExe push -u origin $branch
    if ($LASTEXITCODE -ne 0) { throw "upstream 设置失败" }

    Write-Host "[OK] upstream 设置完成: origin/$branch"

} finally {
    Restore-Encoding
}
