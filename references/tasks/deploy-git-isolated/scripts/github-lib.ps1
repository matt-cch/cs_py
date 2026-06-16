<#
.SYNOPSIS
    GitHub 操作共享库（插件化聚合入口，拓扑排序加载）。
.DESCRIPTION
    读取 lib-plugins/sort-rules.json 中的依赖关系，执行 Kahn 拓扑排序，
    按计算出的安全顺序循环点源导入所有插件。
    新增插件时：1) 放入 lib-plugins/ 目录；2) 在 sort-rules.json 中登记 name/file/depends；
    无需修改本文件，无需重命名已有文件。
.NOTES
    Encoding: UTF-8 with BOM
#>

$script:pluginDir = Join-Path $PSScriptRoot "lib-plugins"
$script:rulesFile = Join-Path $PSScriptRoot "lib-sort-rules.json"

# ============================================================
# 拓扑排序（Kahn 算法）
# ============================================================
function Invoke-TopologicalSort {
    param([array]$Plugins)

    # 构建 name -> plugin 映射
    $nameMap = @{}
    foreach ($p in $Plugins) { $nameMap[$p.name] = $p }

    # 验证：所有 depends 必须存在于 nameMap
    foreach ($p in $Plugins) {
        foreach ($dep in $p.depends) {
            if (-not $nameMap.ContainsKey($dep)) {
                throw "插件 '$($p.name)' 依赖 '$dep'，但 '$dep' 未在 sort-rules.json 中定义"
            }
        }
    }

    # 邻接表 + 入度表
    $inDegree = @{}
    $adj = @{}
    foreach ($p in $Plugins) {
        $inDegree[$p.name] = 0
        $adj[$p.name] = @()
    }
    foreach ($p in $Plugins) {
        foreach ($dep in $p.depends) {
            # dep 必须在 p 之前加载，所以 dep -> p 有一条边
            $adj[$dep] += $p.name
            $inDegree[$p.name]++
        }
    }

    # Kahn 算法
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

    # 环检测
    if ($sorted.Count -ne $Plugins.Count) {
        $candidates = $Plugins | Where-Object { $sorted -notcontains $_.name } | ForEach-Object { $_.name }
        throw "依赖图中存在环，无法拓扑排序。涉及插件: $($candidates -join ', ')"
    }

    # 将名字列表转换为插件对象列表
    return $sorted | ForEach-Object { $nameMap[$_] }
}

# ============================================================
# 主逻辑：读取规则 → 排序 → 循环导入
# ============================================================
if (-not (Test-Path $rulesFile)) {
    Write-Error "排序规则文件不存在: $rulesFile"
    exit 1
}

$rules = Get-Content $rulesFile -Raw -Encoding UTF8 | ConvertFrom-Json
$plugins = Invoke-TopologicalSort -Plugins $rules.plugins

Write-Host "[github-lib] 拓扑排序结果（加载顺序）："
for ($i = 0; $i -lt $plugins.Count; $i++) {
    Write-Host "  $($i + 1). $($plugins[$i].name) ($($plugins[$i].file))"
}

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
