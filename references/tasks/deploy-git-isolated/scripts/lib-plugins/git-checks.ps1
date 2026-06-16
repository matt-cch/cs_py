<#
.SYNOPSIS
    高频 Git 检查函数模块（点源脚本）。
.DESCRIPTION
    提供 Get-GitTrackedFiles / Get-GitStatus / Test-GitFileIgnored / Get-GitStagedFiles / Get-GitStagedStats / Invoke-GitSafetyCheck。
    依赖 github-lib-constants.ps1（须先导入）。
.NOTES
    Encoding: UTF-8 with BOM
#>

function Get-GitTrackedFiles {
    <#.SYNOPSIS 返回当前已跟踪的文件列表（git ls-files）。#>
    Set-Location $devroot
    return & $gitExe ls-files 2>$null
}

function Get-GitStatus {
    <#.SYNOPSIS 返回工作区状态（git status --short）。#>
    Set-Location $devroot
    return & $gitExe status --short 2>$null
}

function Test-GitFileIgnored {
    <#.SYNOPSIS 验证指定文件是否被 .gitignore 屏蔽。#>
    param([string]$Path)
    Set-Location $devroot
    & $gitExe check-ignore -q $Path 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Get-GitStagedFiles {
    <#.SYNOPSIS 返回已 staged 的文件列表（git diff --cached --name-only）。#>
    Set-Location $devroot
    return & $gitExe diff --cached --name-only 2>$null
}

function Get-GitStagedStats {
    <#.SYNOPSIS 返回 staged 文件的统计摘要（git diff --cached --stat）。#>
    Set-Location $devroot
    return & $gitExe diff --cached --stat 2>$null
}

function Invoke-GitSafetyCheck {
    <#.SYNOPSIS 综合安全检查：输出 tracked/staged/未跟踪/敏感屏蔽状态，供 push 前人工确认。#>
    Write-StepHeader -Title "Git 安全检查"
    Assert-IsolatedGit

    # 1. 已跟踪
    Write-Host ""
    Write-Host "[1] 已跟踪文件（会随 push 上传）："
    $tracked = Get-GitTrackedFiles
    if ($tracked) {
        foreach ($f in $tracked) { Write-Host "  - $f" }
    } else {
        Write-Host "  (无)"
    }

    # 2. 已 staged
    Write-Host ""
    Write-Host "[2] 已 staged 文件（即将 commit）："
    $staged = Get-GitStagedFiles
    if ($staged) {
        foreach ($f in $staged) { Write-Host "  - $f" }
    } else {
        Write-Host "  (无)"
    }

    # 3. 未跟踪文件
    Write-Host ""
    Write-Host "[3] 未跟踪文件（需警惕敏感内容）："
    $status = Get-GitStatus
    $untracked = $status | Where-Object { $_ -match '^\?\?\s+(.+)$' } | ForEach-Object { $_ -replace '^\?\?\s+', '' }
    if ($untracked) {
        foreach ($f in $untracked) { Write-Host "  ? $f" }
        Write-Host "  (注意：以上文件尚未 add，暂不上传)"
    } else {
        Write-Host "  (无)"
    }

    # 4. 敏感文件屏蔽验证
    Write-Host ""
    Write-Host "[4] 敏感文件屏蔽验证："
    $sensitiveTests = @('.env', '.vscode/settings.json', 'venv/py/python.exe')
    foreach ($f in $sensitiveTests) {
        if (Test-Path (Join-Path $devroot $f)) {
            $ignored = Test-GitFileIgnored -Path $f
            if ($ignored) {
                Write-Host "  [OK] $f -> 被 .gitignore 屏蔽"
            } else {
                Write-Host "  [WARN] $f -> 未被屏蔽，可能泄露！"
            }
        }
    }

    Write-Host ""
    Write-Host "========================================"
    Write-Host "安全检查完成"
    Write-Host "========================================"
}
