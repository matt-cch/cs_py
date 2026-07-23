<#
.SYNOPSIS
    Step 7: git push（使用 .env 中的 PAT）。
.DESCRIPTION
    从 .env 读取 GITHUB_PAT，构造认证 URL 后 push 到 GitHub。
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
    Write-StepHeader -Title "Step 7: git push"
    Test-IsolatedGit

    $cfg = Read-EnvConfig -RequirePat
    Set-Location $devroot

    $branch = & $gitExe branch --show-current 2>$null
    Write-Host "[OK] 当前分支: $branch"

    $repoPath = $cfg.RepoUrl -replace '^https://github.com/', ''
    $authUrl = "https://$($cfg.Username):$($cfg.Pat)@github.com/$repoPath"

    Write-Host "正在 push 到 GitHub ..."
    & $gitExe push $authUrl $branch
    if ($LASTEXITCODE -ne 0) { throw "git push 失败" }

    Write-Host "[OK] push 成功: $($cfg.RepoUrl) [$branch]"

} finally {
    Restore-Encoding
}
