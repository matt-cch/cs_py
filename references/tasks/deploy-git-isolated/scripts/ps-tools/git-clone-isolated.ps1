param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Url,
    [string]$TargetDir = ""
)

# 编码处理
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

    if ($TargetDir) {
        & $gitExe clone "$Url" "$TargetDir"
    } else {
        & $gitExe clone "$Url"
    }
} finally {
    Restore-Encoding
}
