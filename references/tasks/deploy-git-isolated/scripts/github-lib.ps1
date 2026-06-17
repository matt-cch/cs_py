<#
.SYNOPSIS
    GitHub 操作共享库（插件化聚合入口，拓扑排序 + Profile 筛选加载）。
.DESCRIPTION
    读取 lib-sort-rules.json 中的依赖关系，执行 Kahn 拓扑排序，
    支持 Profile / Include / Exclude 三层筛选，自动补齐依赖，
    按计算出的安全顺序循环点源导入插件。
    新增插件时：1) 放入 lib-plugins/ 目录；2) 在 sort-rules.json 中登记 name/file/depends；
    无需修改本文件，无需重命名已有文件。
.NOTES
    Encoding: UTF-8 with BOM
    Profile 筛选优先级：命令行 -Include/-Exclude > Profile > _default
#>

[CmdletBinding()]
param(
    [string]$Profile = "_default",
    [string[]]$Include = @(),
    [string[]]$Exclude = @()
)

$script:pluginDir = Join-Path $PSScriptRoot "lib-plugins"
$script:rulesFile = Join-Path $PSScriptRoot "lib-sort-rules.json"

# ============================================================
# 依赖自动补齐（递归）
# ============================================================
function Add-Dependencies {
    param(
        [string]$Name,
        [System.Collections.Generic.HashSet[string]]$Needed,
        [hashtable]$NameMap
    )
    if (-not $NameMap.ContainsKey($Name)) { return }
    $plugin = $NameMap[$Name]
    foreach ($dep in $plugin.depends) {
        if ($Needed.Add($dep)) {
            Add-Dependencies -Name $dep -Needed $Needed -NameMap $NameMap
        }
    }
}

# ============================================================
# 插件筛选解析
# ============================================================
function Resolve-PluginFilter {
    <#
    .SYNOPSIS
        根据 Profile / Include / Exclude 计算最终需要加载的插件集合，并自动补齐依赖。
    .PARAMETER AllPlugins
        JSON 中定义的全部插件数组
    .PARAMETER Profiles
        profiles 节转换后的 hashtable
    .PARAMETER ProfileName
        选中的 profile 名
    .PARAMETER CmdInclude
        命令行显式 include（最高优先级）
    .PARAMETER CmdExclude
        命令行显式 exclude（最高优先级）
    #>
    param(
        [array]$AllPlugins,
        [hashtable]$Profiles,
        [string]$ProfileName,
        [string[]]$CmdInclude,
        [string[]]$CmdExclude
    )

    $nameMap = @{}
    foreach ($p in $AllPlugins) { $nameMap[$p.name] = $p }

    # 1. Profile 层筛选
    $baseSet = [System.Collections.Generic.HashSet[string]]::new()

    if ($ProfileName -and $Profiles.ContainsKey($ProfileName)) {
        $prof = $Profiles[$ProfileName]
        $profInclude = @($prof.include)
        $profExclude = @($prof.exclude)

        # include 为空表示 all
        if ($profInclude.Count -gt 0) {
            foreach ($n in $profInclude) { $baseSet.Add($n) | Out-Null }
        } else {
            foreach ($p in $AllPlugins) { $baseSet.Add($p.name) | Out-Null }
        }

        # exclude 生效
        if ($profExclude.Count -gt 0) {
            foreach ($n in $profExclude) { $baseSet.Remove($n) | Out-Null }
        }
    } else {
        if ($ProfileName -and $ProfileName -ne "_default") {
            Write-Warning "Profile '$ProfileName' 未定义，回退到 _default（加载全部）"
        }
        foreach ($p in $AllPlugins) { $baseSet.Add($p.name) | Out-Null }
    }

    # 2. 命令行 Include 覆盖（最高优先级）
    if ($CmdInclude.Count -gt 0) {
        $baseSet.Clear()
        foreach ($n in $CmdInclude) { $baseSet.Add($n) | Out-Null }
    }

    # 3. 命令行 Exclude 覆盖
    if ($CmdExclude.Count -gt 0) {
        foreach ($n in $CmdExclude) { $baseSet.Remove($n) | Out-Null }
    }

    # 4. 验证：baseSet 中的名字必须在 nameMap 中存在
    foreach ($n in $baseSet) {
        if (-not $nameMap.ContainsKey($n)) {
            throw "筛选结果包含未定义的插件名: '$n'。请在 lib-sort-rules.json 中登记。"
        }
    }

    # 5. 自动补齐依赖
    $needed = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($n in $baseSet) {
        if ($needed.Add($n)) {
            Add-Dependencies -Name $n -Needed $needed -NameMap $nameMap
        }
    }

    # 6. 返回过滤后的插件列表（保持原始顺序，供后续拓扑排序）
    return $AllPlugins | Where-Object { $needed.Contains($_.name) }
}

# ============================================================
# 拓扑排序（Kahn 算法）
# ============================================================
function Invoke-TopologicalSort {
    param([array]$Plugins)

    $nameMap = @{}
    foreach ($p in $Plugins) { $nameMap[$p.name] = $p }

    foreach ($p in $Plugins) {
        foreach ($dep in $p.depends) {
            if (-not $nameMap.ContainsKey($dep)) {
                throw "插件 '$($p.name)' 依赖 '$dep'，但 '$dep' 未在 sort-rules.json 中定义"
            }
        }
    }

    $inDegree = @{}
    $adj = @{}
    foreach ($p in $Plugins) {
        $inDegree[$p.name] = 0
        $adj[$p.name] = @()
    }
    foreach ($p in $Plugins) {
        foreach ($dep in $p.depends) {
            $adj[$dep] += $p.name
            $inDegree[$p.name]++
        }
    }

    $queue = [System.Collections.Generic.Queue[string]]::new()
    foreach ($name in $inDegree.Keys) {
        if ($inDegree[$name] -eq 0) {
            $queue.Enqueue($name)
        }
    }

    $sorted = @()
    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        $sorted += $current
        foreach ($neighbor in $adj[$current]) {
            $inDegree[$neighbor]--
            if ($inDegree[$neighbor] -eq 0) {
                $queue.Enqueue($neighbor)
            }
        }
    }

    if ($sorted.Count -ne $Plugins.Count) {
        $candidates = $Plugins | Where-Object { $sorted -notcontains $_.name } | ForEach-Object { $_.name }
        throw "依赖图中存在环，无法拓扑排序。涉及插件: $($candidates -join ', ')"
    }

    return $sorted | ForEach-Object { $nameMap[$_] }
}

# ============================================================
# 主逻辑：读取规则 → 筛选 → 排序 → 循环导入
# ============================================================
if (-not (Test-Path $rulesFile)) {
    Write-Error "排序规则文件不存在: $rulesFile"
    exit 1
}

$rules = Get-Content $rulesFile -Raw -Encoding UTF8 | ConvertFrom-Json

# 将 profiles PSCustomObject 转换为 hashtable
$profiles = @{}
if ($rules.profiles) {
    $rules.profiles.PSObject.Properties | ForEach-Object {
        $profiles[$_.Name] = $_.Value
    }
}

$allPlugins = $rules.plugins

# 筛选
$filteredPlugins = Resolve-PluginFilter `
    -AllPlugins $allPlugins `
    -Profiles $profiles `
    -ProfileName $Profile `
    -CmdInclude $Include `
    -CmdExclude $Exclude

# 拓扑排序（在筛选后的子图上）
$plugins = Invoke-TopologicalSort -Plugins $filteredPlugins

# 生效验证日志
Write-Host "[github-lib] Profile: $Profile"
Write-Host "[github-lib] 全图插件: $($allPlugins.Count) 个"
if ($Include.Count -gt 0) { Write-Host "[github-lib] 命令行 Include: $($Include -join ', ')" }
if ($Exclude.Count -gt 0) { Write-Host "[github-lib] 命令行 Exclude: $($Exclude -join ', ')" }
Write-Host "[github-lib] 筛选后加载顺序:"
for ($i = 0; $i -lt $plugins.Count; $i++) {
    $autoFlag = if ($plugins[$i].name -in $filteredPlugins.name -and $plugins[$i].name -notin ($profiles[$Profile].include + $Include)) { " [auto-dep]" } else { "" }
    Write-Host "  $($i + 1). $($plugins[$i].name) ($($plugins[$i].file))$autoFlag"
}
Write-Host "[github-lib] 实际加载: $($plugins.Count) 个（过滤前 $($allPlugins.Count) 个）"

# 循环导入
foreach ($p in $plugins) {
    $filePath = Join-Path $pluginDir $p.file
    if ([System.IO.Path]::GetExtension($filePath) -ne '.ps1') {
        Write-Error "插件文件必须是 .ps1: $filePath"
        exit 1
    }
    if (-not (Test-Path $filePath)) {
        Write-Error "插件文件不存在: $filePath"
        exit 1
    }
    . $filePath
}

Write-Host "[github-lib] 所有插件加载完成 ($($plugins.Count) 个)"

# ============================================================
# 独立执行时自检
# ============================================================
if ($MyInvocation.InvocationName -ne '.') {
    Switch-ToUtf8
    try {
        Write-StepHeader -Title "GitHub Lib 自检"
        Assert-IsolatedGit
        $cfg = Read-EnvConfig
        Write-Host "[OK] 隔离 Git: $gitExe"
        Write-Host "[OK] 配置读取: $($cfg.Username) / $($cfg.RepoUrl)"
    } finally {
        Restore-Encoding
    }
}
