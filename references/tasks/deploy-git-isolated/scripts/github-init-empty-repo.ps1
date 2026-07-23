param(
    [Parameter(Mandatory=$false)]
    [string]$RemoteUrl = "https://github.com/matt-cch/cs_py.git",
    [Parameter(Mandatory=$false)]
    [string]$Name = "",
    [Parameter(Mandatory=$false)]
    [string]$Email = ""
)

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
    Write-Host "GitHub 空仓库初始化（安全模式）"
    Write-Host "========================================"
    Write-Host "devroot : $devroot"
    Write-Host "remote  : $RemoteUrl"
    Write-Host ""

    # 1. 检测是否已有 .git
    $gitDir = Join-Path $devroot '.git'
    if (Test-Path $gitDir) {
        Write-Warning ".git 已存在，跳过 init"
    } else {
        Write-Host "[1/6] git init ..."
        Set-Location $devroot
        & $gitExe init
        if ($LASTEXITCODE -ne 0) { throw "git init 失败" }
        Write-Host "[OK] git init 完成"
    }

    # 2. 配置身份（如果未设置）
    Write-Host ""
    Write-Host "[2/6] 检查 Git 身份配置 ..."
    $currentName = & $gitExe config --global user.name 2>$null
    $currentEmail = & $gitExe config --global user.email 2>$null
    if (-not $currentName -or -not $currentEmail) {
        Write-Warning "身份未配置，请先执行:"
        Write-Host "  git-config-global.ps1 -Name 'Your Name' -Email 'your@email.com'"
        exit 1
    }
    Write-Host "[OK] user.name : $currentName"
    Write-Host "[OK] user.email: $currentEmail"

    # 3. 写 .gitignore（安全核心）
    Write-Host ""
    Write-Host "[3/6] 生成安全 .gitignore ..."
    $gitignorePath = Join-Path $devroot '.gitignore'
    $gitignoreContent = @"
# ========================================
# 安全屏蔽：禁止上传敏感文件与隔离环境
# ========================================

# 环境变量与密钥（最高优先级）
.env
.env.*
*.key
*.pem
*-key.txt
*-key.pem
*secret*
*token*
*password*
credentials*

# 隔离工具链（不应上传）
venv/

# 编辑器本地配置（含绝对路径）
.vscode/settings.json
.cursor/settings.json
.idea/

# 调试与临时产物
debug/
out/
logs/
*.log
venv/tmp/

# 运行时数据（含状态、缓存）
venv/data-*/
venv/cache-*/
venv/state-*/

# 构建输出与依赖锁定（按需开放）
__pycache__/
*.pyc
node_modules/

# 真源检测报告（可能含本地路径）
references/runtime/verify-runtime-report-*.json

# 其他
*.zip
*.7z
*.tar.gz
"@
    Set-Content -Path $gitignorePath -Value $gitignoreContent -Encoding UTF8 -NoNewline
    Write-Host "[OK] .gitignore 已写入，以下类型被屏蔽："
    Write-Host "  - .env / *.key / *-key.txt / *secret* / *token*"
    Write-Host "  - venv/ (隔离工具链)"
    Write-Host "  - .vscode/settings.json (本地路径)"
    Write-Host "  - debug/ / out/ / logs/ (临时产物)"
    Write-Host "  - venv/data-*/ (运行时数据)"

    # 4. 写顶层 README（空架说明）
    Write-Host ""
    Write-Host "[4/6] 生成顶层 README ..."
    $readmePath = Join-Path $devroot 'README.md'
    if (-not (Test-Path $readmePath)) {
        $readmeContent = @"
# cs_py

Multi-root dev environment.

## 目录结构（渐进式填充）

| 目录 | 说明 |
|------|------|
| apps/ | 子项目入口（渐进式添加） |

## 安全注意

- 本仓库使用 .gitignore 严格屏蔽敏感文件
- 上传前务必检查 diff，确认无密钥/路径泄露
- venv/ 等隔离工具链不上传
"@
        Set-Content -Path $readmePath -Value $readmeContent -Encoding UTF8 -NoNewline
        Write-Host "[OK] README.md 已创建"
    } else {
        Write-Host "[SKIP] README.md 已存在，不覆盖"
    }

    # 5. 只 add 安全文件（绝不 add 现有业务代码）
    Write-Host ""
    Write-Host "[5/6] 安全 add（仅 .gitignore + README）..."
    Set-Location $devroot
    & $gitExe add .gitignore
    & $gitExe add README.md

    # 显示 staged 内容供确认
    Write-Host ""
    Write-Host "--- Staged 文件（确认无敏感内容）---"
    & $gitExe status --short
    Write-Host "--------------------------------------"

    # 6. commit + remote + push
    Write-Host ""
    Write-Host "[6/6] commit + remote + push ..."
    & $gitExe commit -m "init: empty scaffold with safety gitignore"
    if ($LASTEXITCODE -ne 0) { throw "git commit 失败" }

    # 检查 remote
    $remotes = & $gitExe remote -v 2>$null
    if (-not $remotes) {
        & $gitExe remote add origin $RemoteUrl
        Write-Host "[OK] remote add origin $RemoteUrl"
    } else {
        Write-Host "[SKIP] remote 已存在"
    }

    # push master
    Write-Host ""
    Write-Host "正在 push 到 GitHub（首次需输入用户名/个人访问令牌）..."
    & $gitExe push -u origin master
    if ($LASTEXITCODE -ne 0) { throw "git push 失败" }

    Write-Host ""
    Write-Host "========================================"
    Write-Host "[OK] 空仓库架子已推送到 GitHub"
    Write-Host "仓库地址: $RemoteUrl"
    Write-Host "分支    : master"
    Write-Host "========================================"

} finally {
    Restore-Encoding
}
