<#
.SYNOPSIS
    核心工具函数模块（点源脚本）。
.DESCRIPTION
    提供 Test-IsolatedGit 和 Write-StepHeader，被后续插件模块依赖。
    因被依赖，文件名前缀为 00，确保最先加载。
.NOTES
    Encoding: UTF-8 with BOM
#>

function Test-IsolatedGit {
    <#
    .SYNOPSIS
        检查隔离 Git 是否存在并返回状态。
    .OUTPUTS
        若存在则返回 @{ exists=$true; path=$gitExe; version=$ver }，否则返回 @{ exists=$false; path=$gitExe }
    #>
    if (-not (Test-Path $gitExe)) {
        return @{ exists = $false; path = $gitExe }
    }
    $ver = & $gitExe --version 2>$null | Select-Object -First 1
    return @{ exists = $true; path = $gitExe; version = $ver }
}

function Assert-IsolatedGit {
    <#
    .SYNOPSIS
        强制断言隔离 Git 存在，不存在则报错退出。
    #>
    $status = Test-IsolatedGit
    if (-not $status.exists) {
        Write-Error "隔离 Git 未找到: $($status.path)。请先执行部署任务。"
        exit 1
    }
}

function Write-StepHeader {
    <#
    .SYNOPSIS
        输出步骤标题。
    #>
    param([string]$Title)
    Write-Host ""
    Write-Host "========================================"
    Write-Host $Title
    Write-Host "========================================"
}
