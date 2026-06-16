<#
.SYNOPSIS
    .env 配置读取模块（点源脚本）。
.DESCRIPTION
    提供 Read-EnvConfig 函数，从 .env 读取 GitHub 相关配置。
    依赖 github-lib-constants.ps1（须先导入）。
.NOTES
    Encoding: UTF-8 with BOM
#>

function Read-EnvConfig {
    <#.SYNOPSIS 从 .env 读取 GitHub 相关配置。.OUTPUTS PSCustomObject#>
    param([switch]$RequirePat)

    if (-not (Test-Path $envFile)) {
        Write-Error ".env 文件不存在: $envFile"
        exit 1
    }

    $cfg = [PSCustomObject]@{
        Username = $null
        RepoUrl  = $null
        RepoName = $null
        Pat      = $null
        GitName  = $null
        GitEmail = $null
    }

    Get-Content $envFile -Encoding UTF8 | ForEach-Object {
        if ($_ -match '^GITHUB_USERNAME=(.+)$')  { $cfg.Username = $Matches[1].Trim() }
        if ($_ -match '^GITHUB_REPO_URL=(.+)$')   { $cfg.RepoUrl  = $Matches[1].Trim() }
        if ($_ -match '^GITHUB_REPO_NAME=(.+)$')  { $cfg.RepoName = $Matches[1].Trim() }
        if ($_ -match '^GITHUB_PAT=(.+)$')        { $cfg.Pat      = $Matches[1].Trim() }
        if ($_ -match '^GIT_USER_NAME=(.+)$')     { $cfg.GitName  = $Matches[1].Trim() }
        if ($_ -match '^GIT_USER_EMAIL=(.+)$')    { $cfg.GitEmail = $Matches[1].Trim() }
    }

    if (-not $cfg.Username) { Write-Error "GITHUB_USERNAME 未在 .env 中配置"; exit 1 }
    if (-not $cfg.RepoUrl)  { Write-Error "GITHUB_REPO_URL 未在 .env 中配置"; exit 1 }
    if (-not $cfg.GitName)  { Write-Error "GIT_USER_NAME 未在 .env 中配置"; exit 1 }
    if (-not $cfg.GitEmail) { Write-Error "GIT_USER_EMAIL 未在 .env 中配置"; exit 1 }

    if ($RequirePat) {
        if (-not $cfg.Pat -or $cfg.Pat -eq 'ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx') {
            Write-Error "GITHUB_PAT 未配置或仍是占位符。请填入真实 PAT。"
            exit 1
        }
    }

    return $cfg
}
