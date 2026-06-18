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

    Write-Host "========================================"
    Write-Host "隔离 Git 验证"
    Write-Host "========================================"

    Write-Host "`n[1] 版本信息:"
    & $gitExe --version

    Write-Host "`n[2] 全局配置来源（应指向 venv/data-git）:"
    & $gitExe config --global --list --show-origin

    Write-Host "`n[3] 测试写入隔离配置:"
    & $gitExe config --global deploy.verify.test "ok"
    $configPath = Join-Path $gitHome '.gitconfig'
    if (Test-Path $configPath) {
        $content = Get-Content $configPath -Raw -ErrorAction SilentlyContinue
        if ($content -and $content.Contains('deploy')) {
            Write-Host "[OK] --global 写入确实落到隔离目录"
        } else {
            Write-Warning "未在 .gitconfig 中检测到测试键"
        }
    } else {
        Write-Warning ".gitconfig 不存在"
    }
    & $gitExe config --global --unset deploy.verify.test 2>$null | Out-Null

    Write-Host "`n[4] 系统 Git 对比（信息性）:"
    try {
        $sysGit = git --version 2>$null
        if ($sysGit) {
            Write-Host "系统 Git: $sysGit"
        } else {
            Write-Host "系统 Git: 不可用"
        }
    } catch {
        Write-Host "系统 Git: 检测失败"
    }
    Write-Host "隔离 Git: $gitExe"
    Write-Host "隔离 HOME: $gitHome"

    Write-Host "`n结论: 隔离验证完成"
} finally {
    Restore-Encoding
}
