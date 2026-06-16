<#
.SYNOPSIS
    项目常量模块（点源脚本）。
.DESCRIPTION
    定义 devroot、gitExe、gitHome、envFile 等共享常量。
    被 github-lib.ps1 聚合导入，也可独立点源使用。
.NOTES
    Encoding: UTF-8 with BOM
#>

# 动态探测 devroot：从本脚本位置向上固定层数（标准 task 目录结构）
# 路径：.../devroot/references/tasks/deploy-git-isolated/scripts/lib-plugins/constants.ps1
# 向上 5 层到达 devroot。不依赖 venv/ 是否存在，防止嵌套环境穿透。
$script:devroot = $PSScriptRoot
$levels = 0
$maxLevels = 10  # 安全上限
while ($levels -lt $maxLevels) {
    $parent = Split-Path -Parent $script:devroot
    if ([string]::IsNullOrWhiteSpace($parent) -or ($parent -eq $script:devroot)) { break }
    $script:devroot = $parent
    $levels++
    # 标准任务脚本深度：lib-plugins(1) → scripts(2) → deploy-git-isolated(3) → tasks(4) → references(5) → devroot(6)
    # 当到达 devroot 层级时，应能找到 references/ 目录（task 标志性路径）
    if (Test-Path (Join-Path $script:devroot 'references')) {
        break
    }
}
if (-not (Test-Path (Join-Path $script:devroot 'references'))) {
    throw "无法自动探测 devroot。从 $($PSScriptRoot) 向上遍历未找到包含 references/ 的目录。"
}

$script:gitExe  = Join-Path $devroot 'venv\git\cmd\git.exe'
$script:gitHome = Join-Path $devroot 'venv\data-git'
$script:envFile = Join-Path $devroot '.env'
