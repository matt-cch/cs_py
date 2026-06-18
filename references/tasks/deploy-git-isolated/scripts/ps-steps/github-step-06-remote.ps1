<#
.SYNOPSIS
    Step 6: 添加 GitHub remote。
.DESCRIPTION
    从 .env 读取 GITHUB_REPO_URL，添加为 origin remote。
.PARAMETER None
.NOTES
    Encoding: UTF-8 with BOM
#>

# 提前切换编码，确保 github-lib 加载输出也为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$libPath = Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"
. $libPath

Switch-ToUtf8
try {
    Write-StepHeader -Title "Step 6: 添加 remote"
    Test-IsolatedGit

    $cfg = Read-EnvConfig
    Set-Location $devroot

    $remotes = & $gitExe remote -v 2>$null
    if ($remotes) {
        Write-Host "[SKIP] remote 已存在:"
        Write-Host $remotes
    } else {
        & $gitExe remote add origin "$($cfg.RepoUrl)"
        if ($LASTEXITCODE -ne 0) { throw "remote add 失败" }
        Write-Host "[OK] remote add origin $($cfg.RepoUrl)"
    }

} finally {
    Restore-Encoding
}
