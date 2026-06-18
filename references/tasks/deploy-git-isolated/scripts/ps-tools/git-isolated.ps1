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
    # 动态探测 devroot：从脚本位置向上查找包含 venv/git/cmd/git.exe 的目录
    $devroot = $PSScriptRoot
    $found = $false
    while ($devroot) {
        if (Test-Path (Join-Path $devroot 'venv\git\cmd\git.exe')) {
            $found = $true
            break
        }
        $parent = Split-Path -Parent $devroot
        if ([string]::IsNullOrWhiteSpace($parent) -or ($parent -eq $devroot)) { break }
        $devroot = $parent
    }

    if (-not $found) {
        Write-Error "无法自动探测 devroot。从脚本位置向上遍历未找到 venv\git\cmd\git.exe。"
        exit 1
    }

    $gitExe = Join-Path $devroot 'venv\git\cmd\git.exe'
    $gitHome = Join-Path $devroot 'venv\data-git'

    if (-not (Test-Path $gitExe)) {
        Write-Error "隔离 Git 未找到: $gitExe。请先执行部署任务。"
        exit 1
    }

    $env:HOME = $gitHome

    # 透传所有参数给 git.exe
    & $gitExe @args
} finally {
    Restore-Encoding
}
