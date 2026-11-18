<#
.SYNOPSIS
    换数据后的一键重算：数据 -> 统计 -> 插图 -> data.js -> 论文数字看板。

.DESCRIPTION
    本脚本对应 skill「ecom-viz-paper」的换数闭环。改了数据（换 seed、改天数、
    换成自己的 CSV）之后，图、HTML 与论文里的数字都必须重算，否则图文脱节。

    它按顺序跑：
      1. (可选) data_generate.py --seed N --days N --force   生成新样本
      2. analyze.py            -> analysis_stats.json
      3. figs.py               -> figures\fig*.png（缺 matplotlib 则跳过并告警）
      4. build_data_js.py      -> dashboard\data.js
      5. 打印「论文数字看板」，供人工回填到 docx

.PARAMETER Regenerate
    先重新生成数据。不带此开关时，只对现有 CSV 做重算。

.PARAMETER Seed
    生成数据用的随机种子，默认 42。换一个整数就是另一份样本。

.PARAMETER NoFigures
    跳过插图重绘（没有 matplotlib 或只想快速看数字时用）。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\resync.ps1 -Regenerate -Seed 7
#>
param(
    [string]$Project = "",
    [string]$Root = "",
    [switch]$Regenerate,
    [int]$Seed = 42,
    [int]$Days = 30,
    [switch]$NoFigures,
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = "utf-8"

function Info($m) { Write-Host "[info] $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[ ok ] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[warn] $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "[fail] $m" -ForegroundColor Red; exit 1 }
function Step($m) { Write-Host ""; Write-Host "== $m" -ForegroundColor White }

# ---------------------------------------------------------------- 定位项目
if ($Project) {
    $Proj = $Project
} elseif ($Root) {
    $Proj = Join-Path $Root "final paper\result\project"
} else {
    # 已安装：<工作区>\.dsh\skills\ecom-viz-paper\scripts\resync.ps1
    # 就地运行：<工作区>\final paper\result\project_skill\scripts\resync.ps1
    $skillDir = Split-Path -Parent $PSScriptRoot
    $rootGuess = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $skillDir))
    $Proj = Join-Path $rootGuess "final paper\result\project"
    if (-not (Test-Path (Join-Path $Proj "scripts"))) {
        # 就地运行时 project 与 project_skill 同级
        $sibling = Join-Path (Split-Path -Parent $skillDir) "project"
        if (Test-Path (Join-Path $sibling "scripts")) { $Proj = $sibling }
    }
}
if (-not (Test-Path (Join-Path $Proj "scripts"))) {
    Die "找不到 project（期望 <project>\scripts）。用 -Project 'D:\path\to\project' 指定。当前: $Proj"
}
$Proj = (Resolve-Path $Proj).Path
$rootDir = Split-Path -Parent (Split-Path -Parent $Proj)
Info "项目目录: $Proj"

$Scripts  = Join-Path $Proj "scripts"
$Data     = Join-Path $Proj "data"
$FigDir   = Join-Path $Proj "figures"
$DashDir  = Join-Path $Proj "dashboard"
$StatsFile = Join-Path $Proj "analysis_stats.json"
$Csv = Join-Path $Data "ecommerce_dashboard_data.csv"

# ---------------------------------------------------------------- 找解释器
$cands = @()
if ($PythonExe) { $cands += $PythonExe }
if ($env:USERPROFILE) { $cands += (Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe") }
$cands += "python"

$py = $null
foreach ($c in $cands) {
    if (-not $c) { continue }
    if ($c -ne "python" -and -not (Test-Path $c)) { continue }
    try {
        $null = & $c -c "import sys,numpy,pandas;print(sys.version.split()[0])" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $c; break }
    } catch { }
}
if (-not $py) {
    Die "找不到同时具备 numpy 与 pandas 的解释器。先跑 scripts\check_env.py，或 pip install numpy pandas"
}
$pyVer = (& $py -c "import sys;print(sys.version.split()[0])" 2>$null)
Info "解释器: $py ($pyVer)"

# matplotlib 只在 _tools 里，挂 PYTHONPATH
$toolsDir = Join-Path $rootDir "_tools"
$mplOk = $false
if (Test-Path $toolsDir) {
    $env:PYTHONPATH = $toolsDir
    try { $null = & $py -c "import matplotlib" 2>$null; if ($LASTEXITCODE -eq 0) { $mplOk = $true } } catch { }
}
if (-not $mplOk) {
    try { $null = & $py -c "import matplotlib" 2>$null; if ($LASTEXITCODE -eq 0) { $mplOk = $true } } catch { }
}
if ($mplOk) { Info "matplotlib: 可用" } else { Warn "matplotlib 不可用，插图将跳过（用 -NoFigures 显式跳过可消除此警告）" }

function Run-Py($desc, $script) {
    $path = Join-Path $Scripts $script
    if (-not (Test-Path $path)) { Die "缺少脚本: $path" }
    Info $desc
    & $py $path
    if ($LASTEXITCODE -ne 0) { Die "$script 退出码 $LASTEXITCODE" }
}

# ---------------------------------------------------------------- 1 生成数据
Step "1/4 生成数据"
if ($Regenerate) {
    $gen = Join-Path $Scripts "data_generate.py"
    Info "data_generate.py --seed $Seed --days $Days --force"
    & $py $gen --seed $Seed --days $Days --force
    if ($LASTEXITCODE -ne 0) { Die "data_generate.py 退出码 $LASTEXITCODE" }
    Ok "已写入新样本（seed=$Seed, days=$Days）"
} else {
    if (-not (Test-Path $Csv)) { Die "数据不存在: $Csv（加 -Regenerate 生成一份）" }
    Info "沿用现有 CSV（未加 -Regenerate）"
}
$rows = ((Get-Content $Csv).Count - 1)
Ok "CSV 行数: $rows"

# ---------------------------------------------------------------- 2 统计
Step "2/4 统计复算"
Run-Py "analyze.py -> analysis_stats.json" "analyze.py"
if (-not (Test-Path $StatsFile)) { Die "未生成 $StatsFile" }
Ok "analysis_stats.json 已更新: $((Get-Item $StatsFile).LastWriteTime)"

# ---------------------------------------------------------------- 3 插图
Step "3/4 重绘插图"
if ($NoFigures) {
    Warn "已按参数跳过插图重绘（图与新数据可能不一致）"
} elseif ($mplOk) {
    Run-Py "figs.py -> figures\" "figs.py"
    Ok "插图已重绘"
} else {
    Warn "跳过插图（缺 matplotlib）；数字与 data.js 已更新，但图仍是旧数据"
}

# ---------------------------------------------------------------- 4 data.js
Step "4/4 重建页面数据"
Run-Py "build_data_js.py -> dashboard\data.js" "build_data_js.py"
Ok "data.js 已重建"

# ---------------------------------------------------------------- 数字看板
Step "论文数字看板（把这些回填到 docx）"
$s = Get-Content -Raw -Encoding UTF8 $StatsFile | ConvertFrom-Json
$gmvW = [double]$s.total_gmv / 1e4
$spdW = [double]$s.total_spend / 1e4
Write-Host ("  样本      : {0} ~ {1}，{2} 天，{3} 品类，{4} 渠道" -f $s.date_range[0], $s.date_range[1], $s.n_days, $s.n_cat, $s.n_ch)
Write-Host ("  总 GMV    : {0:N2} 万      总花费: {1:N2} 万      ROAS: {2:N4}" -f $gmvW, $spdW, $s.roas)
Write-Host ("  均值转化  : {0}%        均值跳出: {1}%        日度 CV: {2:P2}" -f $s.avg_cvr, $s.avg_bounce, $s.daily_cv)
Write-Host ("  最大日    : {0}  {1:N2} 元" -f $s.daily_top.date, $s.daily_top.gmv)
Write-Host ("  最小日    : {0}  {1:N2} 元" -f $s.daily_low.date, $s.daily_low.gmv)
Write-Host ("  最差环比  : {0}  {1}%" -f $s.worst_dod.date, $s.worst_dod.chg)
Write-Host ""
Write-Host "  品类（表 4 / 4.2 节）:" -ForegroundColor White
foreach ($c in $s.category) {
    Write-Host ("    {0,-6} GMV {1,10:N2} 花费 {2,9:N2} ROAS {3,6:N3} CVR {4,5:N2}% 占比 {5,5:N2}%" -f $c.name, $c.gmv, $c.spend, $c.roas, $c.cvr, $c.share)
}
Write-Host ""
Write-Host "  渠道（表 5 / 4.3 节）:" -ForegroundColor White
foreach ($c in $s.channel) {
    Write-Host ("    {0,-6} GMV {1,10:N2} 花费 {2,9:N2} ROAS {3,6:N3} CVR {4,5:N2}% 占比 {5,5:N2}%" -f $c.name, $c.gmv, $c.spend, $c.roas, $c.cvr, $c.share)
}
if ($s.pairs_top5) {
    Write-Host ""
    Write-Host "  最佳组合（4.2 节）:" -ForegroundColor White
    foreach ($p in $s.pairs_top5) {
        Write-Host ("    {0,-14} ROAS {1,6:N3}  GMV {2,10:N2}" -f $p.name, $p.roas, $p.gmv)
    }
}

Write-Host ""
Ok "重算完成。浏览器需 Ctrl+F5 强制刷新，页面才会读到新的 data.js。"
Write-Host "  还需人工同步的论文位置：摘要与 4.1（总量/ROAS/CV）、表 4 与 4.2（品类 ROAS 与新排序）、"
Write-Host "  表 5 与 4.3（渠道）、4.5（最差环比日与机制判断）、图 6-图 9 的图注与正文数字。"
Write-Host "  确认图文一致后跑 scripts\smoke.ps1 做一次机械体检。"
exit 0
