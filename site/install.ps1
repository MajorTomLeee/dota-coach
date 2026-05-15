# Dota Coach - Windows 一键安装
# Usage: irm https://dota.bowie.top/install.ps1 | iex

$ErrorActionPreference = "Stop"

function Section($t) { Write-Host ""; Write-Host "==> $t" -ForegroundColor Cyan }
function Ok($t)      { Write-Host "[OK] $t" -ForegroundColor Green }
function Warn($t)    { Write-Host "[WARN] $t" -ForegroundColor Yellow }
function Die($t)     { Write-Host "[ERR] $t" -ForegroundColor Red; exit 1 }

Section "Dota Coach 安装开始"
Write-Host "目标目录: $HOME\dota-coach"

# --- 1. Python 检查 ---
Section "检查 Python"
$pythonOk = $false
try {
    $ver = (python --version 2>&1) -replace 'Python ', ''
    if ([version]$ver -ge [version]"3.11") {
        Ok "Python $ver 已安装"
        $pythonOk = $true
    }
} catch {}

if (-not $pythonOk) {
    Warn "Python 未安装或版本 < 3.11，尝试用 winget 安装..."
    try {
        winget install --id=Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
        Ok "Python 安装完成"
        Warn "可能需要重开 PowerShell 让 PATH 生效。如果接下来失败，请关闭再重跑本脚本。"
    } catch {
        Die "winget 失败。请手动从 https://www.python.org/downloads/ 安装 Python 3.12+"
    }
}

# --- 2. uv 检查 ---
Section "检查 uv"
try {
    uv --version | Out-Null
    Ok "uv 已安装"
} catch {
    Warn "uv 未安装，自动安装..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = "$HOME\.local\bin;$env:PATH"
    try { uv --version | Out-Null; Ok "uv 安装完成" }
    catch { Die "uv 安装失败" }
}

# --- 3. 克隆/更新仓库 ---
Section "克隆 Dota Coach 仓库"
$dest = "$HOME\dota-coach"
if (Test-Path $dest) {
    Warn "$dest 已存在，跳过克隆，更新到最新"
    Push-Location $dest
    git pull --ff-only
    Pop-Location
} else {
    git clone https://github.com/MajorTomLeee/dota-coach.git $dest
}
Ok "源码就绪：$dest"

# --- 4. 装依赖 ---
Section "安装 Python 依赖（一两分钟）"
Push-Location $dest
uv venv
uv pip install -e ".[dev]"
Ok "依赖安装完成"

# --- 5. 交互式配置 ---
Section "配置 Steam ID 和 API key"
uv run dotacoach init

# --- 6. GSI 配置 ---
Section "部署 Valve GSI 配置"
uv run dotacoach install-gsi

Pop-Location

# --- 7. 收尾提示 ---
Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "  ✅ 安装完成！还差最后一步（Steam 没有开 API，必须手动）" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "在 Steam 库 → Dota 2 → 右键 → 属性 → 启动选项 中，加入：" -ForegroundColor White
Write-Host ""
Write-Host "    -gamestateintegration -condebug" -ForegroundColor Yellow
Write-Host ""
Write-Host "然后运行实时层（建议放进任务计划程序设为开机启动）：" -ForegroundColor White
Write-Host ""
Write-Host "    cd $dest" -ForegroundColor Yellow
Write-Host "    uv run dotacoach run" -ForegroundColor Yellow
Write-Host ""
Write-Host "F8 = 全局静音切换。详细说明：https://dota.bowie.top" -ForegroundColor White
Write-Host ""
