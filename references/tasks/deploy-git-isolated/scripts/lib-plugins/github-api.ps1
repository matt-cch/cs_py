<#
.SYNOPSIS
    GitHub REST API 封装插件（点源脚本）。
.DESCRIPTION
    提供 Invoke-GitHubApi / New-GitHubIssue / Update-GitHubIssue / New-GitHubIssueComment
    等通用函数，自动处理 UTF-8 encoding、认证头、错误解析。
    被 github-sync-issue.ps1 等脚本点源导入。
.NOTES
    Encoding: UTF-8 with BOM
    依赖: constants（$devroot / $envFile）, env-config（Read-EnvConfig）
#>

function Get-GitHubCredentials {
    <#
    .SYNOPSIS
        从 .env 读取 GitHub 认证信息。
    .OUTPUTS
        @{ pat; username; repoUrl; owner; repo }
    #>
    $cfg = Read-EnvConfig -RequirePat
    $pat = $cfg.Pat
    $username = $cfg.Username
    $repoUrl = $cfg.RepoUrl

    if (-not $pat) { throw "GITHUB_PAT 未在 .env 中配置" }
    if (-not $username) { throw "GITHUB_USERNAME 未在 .env 中配置" }
    if (-not $repoUrl) { throw "GITHUB_REPO_URL 未在 .env 中配置" }

    if ($repoUrl -match 'github\.com/([^/]+)/([^/]+?)(?:\.git)?$') {
        $owner = $Matches[1]
        $repo = $Matches[2]
    } else {
        throw "无法从 GITHUB_REPO_URL 提取 owner/repo: $repoUrl"
    }

    return @{
        pat = $pat
        username = $username
        repoUrl = $repoUrl
        owner = $owner
        repo = $repo
    }
}

function Build-GitHubHeaders {
    <#
    .SYNOPSIS
        构造 GitHub API 请求头。
    #>
    param([string]$Pat)
    return @{
        'Authorization' = "token $Pat"
        'Accept' = 'application/vnd.github.v3+json'
        'User-Agent' = 'deploy-git-isolated/1.0'
    }
}

function Invoke-GitHubApi {
    <#
    .SYNOPSIS
        通用 GitHub API 调用，自动处理 UTF-8 encoding。
    .PARAMETER Method
        HTTP 方法: GET / POST / PATCH / DELETE
    .PARAMETER Uri
        完整 API URL
    .PARAMETER Pat
        GitHub PAT
    .PARAMETER Body
        请求体（PSObject / Hashtable），自动转为 UTF-8 JSON
    .PARAMETER TimeoutSec
        超时秒数，默认 30
    .OUTPUTS
        API 响应对象（已解析 JSON）
    #>
    param(
        [Parameter(Mandatory)]
        [ValidateSet('GET','POST','PATCH','DELETE')]
        [string]$Method,

        [Parameter(Mandatory)]
        [string]$Uri,

        [Parameter(Mandatory)]
        [string]$Pat,

        [object]$Body,

        [int]$TimeoutSec = 30
    )

    $headers = Build-GitHubHeaders -Pat $Pat

    $invokeParams = @{
        Uri = $Uri
        Method = $Method
        Headers = $headers
        TimeoutSec = $TimeoutSec
    }

    if ($Body) {
        # 显式编码为 UTF-8 bytes，避免 PowerShell 5.1 默认用 GBK 发送导致中文乱码
        $bodyJson = $Body | ConvertTo-Json -Depth 10
        $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyJson)
        $invokeParams['Body'] = $bodyBytes
        $invokeParams['ContentType'] = 'application/json; charset=utf-8'
    }

    Write-Host "[GitHub API] $Method $Uri"

    try {
        $response = Invoke-RestMethod @invokeParams
        return $response
    } catch {
        $msg = $_.Exception.Message
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $reader.BaseStream.Position = 0
            $reader.DiscardBufferedData()
            $errorBody = $reader.ReadToEnd()
            $msg += " | Response: $errorBody"
        }
        throw $msg
    }
}

function New-GitHubIssue {
    <#
    .SYNOPSIS
        创建 GitHub Issue。
    #>
    param(
        [Parameter(Mandatory)]
        [string]$Owner,

        [Parameter(Mandatory)]
        [string]$Repo,

        [Parameter(Mandatory)]
        [string]$Pat,

        [Parameter(Mandatory)]
        [string]$Title,

        [string]$Body = "",

        [string[]]$Labels = @()
    )

    $uri = "https://api.github.com/repos/$Owner/$Repo/issues"
    $payload = @{ title = $Title; body = $Body }
    if ($Labels.Count -gt 0) { $payload['labels'] = $Labels }

    return Invoke-GitHubApi -Method POST -Uri $uri -Pat $Pat -Body $payload
}

function Update-GitHubIssue {
    <#
    .SYNOPSIS
        更新（PATCH）GitHub Issue。
    #>
    param(
        [Parameter(Mandatory)]
        [string]$Owner,

        [Parameter(Mandatory)]
        [string]$Repo,

        [Parameter(Mandatory)]
        [int]$Number,

        [Parameter(Mandatory)]
        [string]$Pat,

        [string]$Title,

        [string]$Body,

        [string[]]$Labels,

        [string]$State
    )

    $uri = "https://api.github.com/repos/$Owner/$Repo/issues/$Number"
    $payload = @{}
    if ($PSBoundParameters.ContainsKey('Title')) { $payload['title'] = $Title }
    if ($PSBoundParameters.ContainsKey('Body')) { $payload['body'] = $Body }
    if ($PSBoundParameters.ContainsKey('Labels')) { $payload['labels'] = $Labels }
    if ($PSBoundParameters.ContainsKey('State')) { $payload['state'] = $State }

    return Invoke-GitHubApi -Method PATCH -Uri $uri -Pat $Pat -Body $payload
}

function New-GitHubIssueComment {
    <#
    .SYNOPSIS
        在 Issue 下追加评论。
    #>
    param(
        [Parameter(Mandatory)]
        [string]$Owner,

        [Parameter(Mandatory)]
        [string]$Repo,

        [Parameter(Mandatory)]
        [int]$Number,

        [Parameter(Mandatory)]
        [string]$Pat,

        [Parameter(Mandatory)]
        [string]$Body
    )

    $uri = "https://api.github.com/repos/$Owner/$Repo/issues/$Number/comments"
    $payload = @{ body = $Body }

    return Invoke-GitHubApi -Method POST -Uri $uri -Pat $Pat -Body $payload
}

function Get-GitHubIssueComments {
    <#
    .SYNOPSIS
        列出 Issue 下的评论。
    #>
    param(
        [Parameter(Mandatory)]
        [string]$Owner,

        [Parameter(Mandatory)]
        [string]$Repo,

        [Parameter(Mandatory)]
        [int]$Number,

        [Parameter(Mandatory)]
        [string]$Pat
    )

    $uri = "https://api.github.com/repos/$Owner/$Repo/issues/$Number/comments"
    return Invoke-GitHubApi -Method GET -Uri $uri -Pat $Pat
}
