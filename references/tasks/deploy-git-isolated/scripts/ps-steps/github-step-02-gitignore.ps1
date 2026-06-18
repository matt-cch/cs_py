<#
.SYNOPSIS
    Step 2: 生成安全 .gitignore。
.DESCRIPTION
    在 devroot 下生成 .gitignore，屏蔽敏感文件与隔离环境。若已存在则保留现有内容并追加缺失规则。
.PARAMETER None
.NOTES
    Encoding: UTF-8 with BOM
#>

# 提前切换编码，确保 github-lib 加载输出也为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$libPath = Join-Path (Split-Path -Parent $PSScriptRoot) "github-lib.ps1"
. $libPath

Switch-ToUtf8
try {
    Write-StepHeader -Title "Step 2: 生成安全 .gitignore"

    $gitignorePath = Join-Path $devroot '.gitignore'
    $rules = @(
        "# ========================================"
        "# 安全屏蔽：禁止上传敏感文件与隔离环境"
        "# ========================================"
        ""
        "# 环境变量与密钥（最高优先级）"
        ".env"
        ".env.*"
        "*.key"
        "*.pem"
        "*-key.txt"
        "*-key.pem"
        "*secret*"
        "*token*"
        "*password*"
        "credentials*"
        ""
        "# 隔离工具链（不应上传）"
        "venv/"
        ""
        "# 编辑器本地配置（含绝对路径）"
        ".vscode/settings.json"
        ".cursor/settings.json"
        ".idea/"
        ""
        "# 调试与临时产物"
        "debug/"
        "out/"
        "logs/"
        "*.log"
        "venv/tmp/"
        ""
        "# 运行时数据（含状态、缓存）"
        "venv/data-*/"
        "venv/cache-*/"
        "venv/state-*/"
        ""
        "# 构建输出与依赖锁定（按需开放）"
        "__pycache__/"
        "*.pyc"
        "node_modules/"
        ""
        "# 真源检测报告（可能含本地路径）"
        "references/runtime/verify-runtime-report-*.json"
        ""
        "# 其他"
        "*.zip"
        "*.7z"
        "*.tar.gz"
    )

    if (Test-Path $gitignorePath) {
        $existing = Get-Content $gitignorePath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        $missing = @()
        foreach ($rule in $rules) {
            if ($rule -match '^#' -or [string]::IsNullOrWhiteSpace($rule)) { continue }
            if ($existing -notmatch [regex]::Escape($rule)) {
                $missing += $rule
            }
        }
        if ($missing.Count -gt 0) {
            Add-Content -Path $gitignorePath -Value ("`n" + ($missing -join "`n")) -Encoding UTF8
            Write-Host "[OK] 已追加 $($missing.Count) 条缺失规则"
        } else {
            Write-Host "[SKIP] .gitignore 已存在且规则完整"
        }
    } else {
        Set-Content -Path $gitignorePath -Value ($rules -join "`n") -Encoding UTF8
        Write-Host "[OK] .gitignore 已生成"
    }

    Write-Host "[OK] Step 2 完成"

} finally {
    Restore-Encoding
}
