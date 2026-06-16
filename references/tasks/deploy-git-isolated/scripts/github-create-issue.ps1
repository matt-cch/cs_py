<#
.SYNOPSIS
    自动创建 GitHub Issue，用于 Task 变更追踪。
.DESCRIPTION
    调用 GitHub REST API 创建 Issue，支持从 .env 读取 PAT 认证。
    被 github-lib.ps1 聚合导入，也可独立执行。
.NOTES
    Encoding: UTF-8 with BOM
#>

# 动态探测 devroot（与 constants.ps1 保持一致）
$devroot = $PSScriptRoot
while ($devroot) {
    if (Test-Path (Join-Path $devroot 'venv\git\cmd\git.exe')) { break }
    $parent = Split-Path -Parent $devroot
    if ([string]::IsNullOrWhiteSpace($parent) -or ($parent -eq $devroot)) { break }
    $devroot = $parent
}
if (-not (Test-Path (Join-Path $devroot 'venv\git\cmd\git.exe'))) {
    throw "无法自动探测 devroot。从 $($PSScriptRoot) 向上遍历未找到 venv\git\cmd\git.exe。"
}

$envFile = Join-Path $devroot '.env'

# 读取 .env
function Read-DotEnv {
    param([string]$Path)
    $cfg = @{}
    if (-not (Test-Path $Path)) {
        throw ".env 文件不存在: $Path"
    }
    Get-Content $Path -Encoding UTF8 | ForEach-Object {
        if ($_ -match '^([A-Za-z0-9_]+)=(.*)$') {
            $cfg[$Matches[1]] = $Matches[2].Trim()
        }
    }
    return $cfg
}

$cfg = Read-DotEnv -Path $envFile
$pat = $cfg['GITHUB_PAT']
$username = $cfg['GITHUB_USERNAME']
$repoUrl = $cfg['GITHUB_REPO_URL']

if (-not $pat) { throw "GITHUB_PAT 未在 .env 中配置" }
if (-not $username) { throw "GITHUB_USERNAME 未在 .env 中配置" }
if (-not $repoUrl) { throw "GITHUB_REPO_URL 未在 .env 中配置" }

# 从 GITHUB_REPO_URL 提取 owner/repo
# 支持 https://github.com/owner/repo.git 格式
if ($repoUrl -match 'github\.com/([^/]+)/([^/]+?)(?:\.git)?$') {
    $owner = $Matches[1]
    $repo = $Matches[2]
} else {
    throw "无法从 GITHUB_REPO_URL 提取 owner/repo: $repoUrl"
}

# 获取当前分支最新的 commit 信息
$gitExe = Join-Path $devroot 'venv\git\cmd\git.exe'
$branch = & $gitExe -C $devroot rev-parse --abbrev-ref HEAD 2>$null
$commitHash = & $gitExe -C $devroot rev-parse --short HEAD 2>$null
$commitMsg = (& $gitExe -C $devroot log -1 --pretty=format:"%s" 2>$null)
$commitBody = (& $gitExe -C $devroot log -1 --pretty=format:"%b" 2>$null)

# Issue 标题和正文
$issueTitle = "[Task Tracking] deploy-git-isolated 变更历史"

$issueBody = @"
## 初始提交

| 属性 | 值 |
|------|-----|
| **Commit** | ``$commitHash`` |
| **Branch** | ``$branch`` |
| **Message** | $commitMsg |
| **Date** | $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') |

### 变更摘要

$commitBody

---

> 本 Issue 用于追踪 ``deploy-git-isolated`` 任务的后续变更。
> 每次新的 commit/PR 关联到本任务时，请在下方追加评论记录。
> 任务完成时，添加 label ``task-completed`` 并关闭本 Issue。
"@

# 构造 API 请求
$apiUrl = "https://api.github.com/repos/$owner/$repo/issues"
$headers = @{
    'Authorization' = "token $pat"
    'Accept' = 'application/vnd.github.v3+json'
    'User-Agent' = 'deploy-git-isolated/1.0'
}

$body = @{
    title = $issueTitle
    body = $issueBody
    labels = @('task-active')
} | ConvertTo-Json -Depth 10

# 发送请求
Write-Host "[GitHub API] 创建 Issue..."
Write-Host "  URL: $apiUrl"
Write-Host "  Title: $issueTitle"

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Headers $headers -Body $body -ContentType 'application/json' -TimeoutSec 30
    Write-Host ""
    Write-Host "Issue 创建成功!"
    Write-Host "  Number: #$($response.number)"
    Write-Host "  URL: $($response.html_url)"
    Write-Host "  State: $($response.state)"

    # 输出 JSON 结果供下游消费
    $result = @{
        success = $true
        number = $response.number
        url = $response.html_url
        title = $response.title
        state = $response.state
    } | ConvertTo-Json

    Write-Host ""
    Write-Host $result
} catch {
    Write-Error "Issue 创建失败: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $errorBody = $reader.ReadToEnd()
        Write-Error "响应: $errorBody"
    }
    exit 1
}
