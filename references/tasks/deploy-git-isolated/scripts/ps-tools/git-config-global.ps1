param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Name,
    [Parameter(Mandatory=$true, Position=1)]
    [string]$Email
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
    $devroot = 'D:\pjt\cursor\cs_py'
    $gitExe = Join-Path $devroot 'venv\git\cmd\git.exe'
    $gitHome = Join-Path $devroot 'venv\data-git'

    if (-not (Test-Path $gitExe)) {
        Write-Error "隔离 Git 未找到: $gitExe。请先执行部署任务。"
        exit 1
    }

    $env:HOME = $gitHome

    & $gitExe config --global user.name "$Name"
    & $gitExe config --global user.email "$Email"

    Write-Host "[OK] 已写入隔离全局配置:"
    $configuredName = & $gitExe config --global user.name
    $configuredEmail = & $gitExe config --global user.email
    Write-Host "  user.name : $configuredName"
    Write-Host "  user.email: $configuredEmail"
} finally {
    Restore-Encoding
}
