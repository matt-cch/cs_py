<#
.SYNOPSIS
    编码处理模块（点源脚本）。
.DESCRIPTION
    提供 Switch-ToEncoding / Switch-ToUtf8 / Restore-Encoding / Invoke-WithEncoding。
    被 github-lib.ps1 聚合导入，也可独立点源使用。
.NOTES
    Encoding: UTF-8 with BOM
#>

$script:originalConsoleEncoding = [Console]::OutputEncoding
$script:originalOutputEncoding  = $OutputEncoding
$script:encodingRestored = $false

function Switch-ToEncoding {
    <#.SYNOPSIS 将控制台输出编码和 PowerShell 管道编码切换到指定编码。#>
    param([System.Text.Encoding]$Encoding)
    [Console]::OutputEncoding = $Encoding
    $script:OutputEncoding = $Encoding
}

function Switch-ToUtf8 {
    <#.SYNOPSIS 快捷方式：切换到 UTF-8（本项目默认编码）。#>
    Switch-ToEncoding -Encoding ([System.Text.Encoding]::UTF8)
}

function Restore-Encoding {
    <#.SYNOPSIS 恢复到脚本启动前的原始编码状态（幂等）。#>
    if (-not $script:encodingRestored) {
        if ($null -ne $script:originalConsoleEncoding) {
            [Console]::OutputEncoding = $script:originalConsoleEncoding
        }
        if ($null -ne $script:originalOutputEncoding) {
            $script:OutputEncoding = $script:originalOutputEncoding
        }
        $script:encodingRestored = $true
    }
}

function Invoke-WithEncoding {
    <#.SYNOPSIS 在指定编码环境下临时执行代码块，完毕后自动恢复。#>
    param(
        [System.Text.Encoding]$Encoding,
        [scriptblock]$Command
    )
    Switch-ToEncoding -Encoding $Encoding
    try {
        & $Command
    } finally {
        Restore-Encoding
    }
}

$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Restore-Encoding }
