<#
.SYNOPSIS
    Step 1: git init + 配置隔离 Git 身份。
.DESCRIPTION
    在 devroot 下执行 git init（若尚未 init），并从 .env 读取 GIT_USER_NAME / GIT_USER_EMAIL 写入隔离配置。
.PARAMETER None
.NOTES
    Encoding: UTF-8 with BOM
#>

# 提前切换编码，确保 github-lib 加载输出也为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 点源导入共享库
$libPath = Join-Path $PSScriptRoot "github-lib.ps1"
. $libPath

Switch-ToUtf8
try {
    Write-StepHeader -Title "Step 1: git init + 身份配置"
    Test-IsolatedGit

    # 1. git init
    $gitDir = Join-Path $devroot '.git'
    if (Test-Path $gitDir) {
        Write-Host "[SKIP] .git 已存在"
    } else {
        Set-Location $devroot
        & $gitExe init
        if ($LASTEXITCODE -ne 0) { throw "git init 失败" }
        Write-Host "[OK] git init 完成"
    }

    # 2. 读取 .env 身份并配置
    $cfg = Read-EnvConfig
    & $gitExe config --global user.name "$($cfg.GitName)"
    & $gitExe config --global user.email "$($cfg.GitEmail)"
    Write-Host "[OK] 身份已配置: $($cfg.GitName) / $($cfg.GitEmail)"

    # 验证
    $confirmedName = & $gitExe config --global user.name
    $confirmedEmail = & $gitExe config --global user.email
    Write-Host "[OK] 验证: $confirmedName / $confirmedEmail"

} finally {
    Restore-Encoding
}
