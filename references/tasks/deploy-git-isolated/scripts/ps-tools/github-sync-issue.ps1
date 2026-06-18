<#
.SYNOPSIS
    GitHub Issue 同步入口脚本 — 支持创建、更新、追加评论、列出评论。
.DESCRIPTION
    调用 github-lib.ps1 加载全部插件（含 github-api），读取 github-sync-issue-config.json 配置，
    根据 -Mode 参数执行对应的 GitHub Issue 操作。
    所有中文内容通过 UTF-8 encoding 发送，避免乱码。
.PARAMETER Mode
    操作模式: create / update / comment / list-comments / get-issue
.PARAMETER IssueNumber
    Issue 编号（update / comment / list-comments / get-issue 必需）
.PARAMETER Title
    Issue 标题（create / update 用）
.PARAMETER Body
    Issue 正文或评论内容（create / update / comment 用，-BodyFile 优先级更高）
.PARAMETER BodyFile
    从指定文件读取正文内容
.PARAMETER TaskName
    任务名称，用于模板替换（默认从当前分支名推断）
.PARAMETER Labels
    Labels 数组（create 用，默认从配置读取）
.PARAMETER ConfigPath
    配置文件路径（默认脚本同级目录下的 github-sync-issue-config.json）
.EXAMPLE
    # 创建追踪 Issue
    .\github-sync-issue.ps1 -Mode create -TaskName "deploy-git-isolated"

    # 更新 Issue body
    .\github-sync-issue.ps1 -Mode update -IssueNumber 1 -BodyFile "issue-body.md"

    # 追加评论（记录 commit）
    .\github-sync-issue.ps1 -Mode comment -IssueNumber 1 -Body "commit abc123: 新增 GOAL.md"

    # 列出评论
    .\github-sync-issue.ps1 -Mode list-comments -IssueNumber 1
.NOTES
    Encoding: UTF-8 with BOM
    依赖: github-lib.ps1（自动点源加载所有插件）
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('create','update','comment','list-comments','get-issue')]
    [string]$Mode,

    [int]$IssueNumber,

    [string]$Title,

    [string]$Body,

    [string]$BodyFile,

    [string]$TaskName,

    [string[]]$Labels,

    [string]$ConfigPath = ''
)

# 编码处理：保存原始编码 -> 切换到 UTF-8 -> 脚本结束时恢复
$script:originalConsoleEncoding = [Console]::OutputEncoding
$script:originalOutputEncoding  = $OutputEncoding
$script:encodingRestored = $false

function Restore-Encoding {
    if (-not $script:encodingRestored) {
        [Console]::OutputEncoding = $script:originalConsoleEncoding
        $OutputEncoding = $script:originalOutputEncoding
        $script:encodingRestored = $true
    }
}

$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Restore-Encoding }
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

try {
    # ============================================================
    # 0. 参数默认值补偿（$PSScriptRoot 在参数块中可能为空）
    # ============================================================
    if (-not $ConfigPath) {
        $ConfigPath = Join-Path $PSScriptRoot 'github-sync-issue-config.json'
    }

    # ============================================================
    # 1. 加载插件体系
    # ============================================================
    $libPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'github-lib.ps1'
    if (-not (Test-Path $libPath)) {
        throw "github-lib.ps1 不存在: $libPath"
    }
    . $libPath -Profile "issue-sync"

    # ============================================================
    # 2. 读取配置
    # ============================================================
    if (-not (Test-Path $ConfigPath)) {
        throw "配置文件不存在: $ConfigPath"
    }
    $config = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

    # ============================================================
    # 3. 读取认证信息
    # ============================================================
    $creds = Get-GitHubCredentials
    $owner = $config.defaults.owner
    if (-not $owner) { $owner = $creds.owner }
    $repo = $config.defaults.repo
    if (-not $repo) { $repo = $creds.repo }

    # ============================================================
    # 4. 推断 TaskName（如果未提供）
    # ============================================================
    if (-not $TaskName) {
        $TaskName = & $gitExe -C $devroot rev-parse --abbrev-ref HEAD 2>$null
        # 去掉 task/ 前缀
        if ($TaskName -match '^task/(.+)$') {
            $TaskName = $Matches[1]
        }
    }

    # ============================================================
    # 5. 处理 Body 内容
    # ============================================================
    $finalBody = $Body
    if ($BodyFile -and (Test-Path $BodyFile)) {
        $finalBody = Get-Content $BodyFile -Raw -Encoding UTF8
    }

    # ============================================================
    # 6. 模式分发
    # ============================================================
    switch ($Mode) {
        'create' {
            Write-StepHeader -Title "创建 GitHub Issue"

            $tmpl = $config.issue_templates.'task-tracking'
            $issueTitle = $Title
            if (-not $issueTitle) {
                $issueTitle = $tmpl.title -replace '\{task_name\}', $TaskName
            }

            $issueBody = $finalBody
            if (-not $issueBody) {
                $commitHash = & $gitExe -C $devroot rev-parse --short HEAD 2>$null
                $commitMsg = (& $gitExe -C $devroot log -1 --pretty=format:"%s" 2>$null)
                $branch = & $gitExe -C $devroot rev-parse --abbrev-ref HEAD 2>$null
                $dateStr = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

                $issueBody = @"
$($tmpl.body_header)
| **Commit** | ``$commitHash`` |
| **Branch** | ``$branch`` |
| **Message** | $commitMsg |
| **Date** | $dateStr |
$($tmpl.body_footer -replace '\{task_name\}', $TaskName)
"@
            }

            $issueLabels = $Labels
            if (-not $issueLabels -or $issueLabels.Count -eq 0) {
                $issueLabels = $tmpl.labels
            }

            $result = New-GitHubIssue -Owner $owner -Repo $repo -Pat $creds.pat `
                -Title $issueTitle -Body $issueBody -Labels $issueLabels

            Write-Host ""
            Write-Host "Issue 创建成功!"
            Write-Host "  Number: #$($result.number)"
            Write-Host "  URL: $($result.html_url)"
            Write-Host "  State: $($result.state)"
        }

        'update' {
            if (-not $IssueNumber) { throw "-IssueNumber 是 update 模式的必需参数" }
            Write-StepHeader -Title "更新 GitHub Issue #$IssueNumber"

            $updateArgs = @{
                Owner = $owner
                Repo = $repo
                Number = $IssueNumber
                Pat = $creds.pat
            }
            if ($Title) { $updateArgs['Title'] = $Title }
            if ($finalBody) { $updateArgs['Body'] = $finalBody }
            if ($Labels -and $Labels.Count -gt 0) { $updateArgs['Labels'] = $Labels }

            $result = Update-GitHubIssue @updateArgs

            Write-Host ""
            Write-Host "Issue 更新成功!"
            Write-Host "  Number: #$($result.number)"
            Write-Host "  URL: $($result.html_url)"
        }

        'comment' {
            if (-not $IssueNumber) { throw "-IssueNumber 是 comment 模式的必需参数" }
            if (-not $finalBody) { throw "-Body 或 -BodyFile 是 comment 模式的必需参数" }
            Write-StepHeader -Title "追加评论到 Issue #$IssueNumber"

            $result = New-GitHubIssueComment -Owner $owner -Repo $repo -Number $IssueNumber -Pat $creds.pat -Body $finalBody

            Write-Host ""
            Write-Host "评论追加成功!"
            Write-Host "  Comment ID: $($result.id)"
            Write-Host "  URL: $($result.html_url)"
        }

        'list-comments' {
            if (-not $IssueNumber) { throw "-IssueNumber 是 list-comments 模式的必需参数" }
            Write-StepHeader -Title "列出 Issue #$IssueNumber 的评论"

            $comments = Get-GitHubIssueComments -Owner $owner -Repo $repo -Number $IssueNumber -Pat $creds.pat

            Write-Host ""
            Write-Host "共 $($comments.Count) 条评论:"
            foreach ($c in $comments) {
                Write-Host "  [$($c.created_at)] $($c.user.login): $($c.body.Substring(0, [Math]::Min(60, $c.body.Length)))..."
            }
        }

        'get-issue' {
            if (-not $IssueNumber) { throw "-IssueNumber 是 get-issue 模式的必需参数" }
            Write-StepHeader -Title "获取 Issue #$IssueNumber 详情"

            $uri = "https://api.github.com/repos/$owner/$repo/issues/$IssueNumber"
            $result = Invoke-GitHubApi -Method GET -Uri $uri -Pat $creds.pat

            Write-Host ""
            Write-Host "Issue #$($result.number): $($result.title)"
            Write-Host "  State: $($result.state)"
            Write-Host "  URL: $($result.html_url)"
            Write-Host "  Labels: $($result.labels.name -join ', ')"
            Write-Host "  Body 长度: $($result.body.Length) 字符"
        }
    }

} catch {
    Write-Error "执行失败: $_"
    exit 1
} finally {
    Restore-Encoding
}
