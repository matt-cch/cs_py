<#
.SYNOPSIS
    项目常量模块（点源脚本）。
.DESCRIPTION
    定义 devroot、gitExe、gitHome、envFile 等共享常量。
    被 github-lib.ps1 聚合导入，也可独立点源使用。
.NOTES
    Encoding: UTF-8 with BOM
#>

# 动态探测 devroot：从本脚本位置向上遍历，找到包含 venv\git\cmd\git.exe 的目录
$script:devroot = $PSScriptRoot
while ($devroot) {
    if (Test-Path (Join-Path $devroot 'venv\git\cmd\git.exe')) { break }
    $parent = Split-Path -Parent $devroot
    if ([string]::IsNullOrWhiteSpace($parent) -or ($parent -eq $devroot)) { break }
    $devroot = $parent
}
if (-not (Test-Path (Join-Path $devroot 'venv\git\cmd\git.exe'))) {
    throw "无法自动探测 devroot。从 $($PSScriptRoot) 向上遍历未找到 venv\git\cmd\git.exe。"
}

$script:gitExe  = Join-Path $devroot 'venv\git\cmd\git.exe'
$script:gitHome = Join-Path $devroot 'venv\data-git'
$script:envFile = Join-Path $devroot '.env'
