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
    Write-Host "多身份切换演示"
    Write-Host "========================================"

    # 项目默认身份（隔离 global）
    Write-Host "`n[1] 设置项目默认身份（--global）:"
    & $gitExe config --global user.name "Project Default"
    & $gitExe config --global user.email "default@project.local"
    Write-Host "[OK] Global 身份:"
    & $gitExe config --global user.name
    & $gitExe config --global user.email

    # 模拟一个仓库目录进行 local 覆盖
    $demoRepo = Join-Path $devroot 'venv\tmp\git-multi-identity-demo'
    if (Test-Path $demoRepo) {
        Remove-Item $demoRepo -Recurse -Force
    }
    New-Item -ItemType Directory -Path $demoRepo | Out-Null
    Set-Location $demoRepo
    & $gitExe init | Out-Null

    Write-Host "`n[2] 在 demo 仓库中覆盖 local 身份:"
    & $gitExe config --local user.name "Local Override"
    & $gitExe config --local user.email "local@repo.local"
    Write-Host "[OK] Local 身份:"
    & $gitExe config --local user.name
    & $gitExe config --local user.email

    Write-Host "`n[3] 验证优先级（local > global）:"
    $effectiveName = & $gitExe config user.name
    $effectiveEmail = & $gitExe config user.email
    Write-Host "Effective user.name : $effectiveName"
    Write-Host "Effective user.email: $effectiveEmail"

    # 清理
    Set-Location $devroot
    Remove-Item $demoRepo -Recurse -Force
    & $gitExe config --global --unset user.name 2>$null | Out-Null
    & $gitExe config --global --unset user.email 2>$null | Out-Null

    Write-Host "`n[OK] 演示完成，已清理"
} finally {
    Restore-Encoding
}
