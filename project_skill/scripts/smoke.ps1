<#
.SYNOPSIS
    机械体检：结构、数据 schema、统计/插图/页面的新鲜度与同步性。

.DESCRIPTION
    本脚本不校验「论文里写了 1422.92 万」这类具体数字——数字随数据变，写死就会
    在换 seed 后误报。它只检查**结构**与**一致性**：

      - 项目结构与必需文件
      - CSV 是否含必需列、行数是否合理
      - analysis_stats.json 是否比 CSV 新（否则统计过期）
      - dashboard\data.js 是否与 CSV 一致（调 build_data_js.py --check）
      - 9 张论文插图是否存在、是否比 CSV 新
      - app.js / data.js / server.mjs 的语法
      - 论文 docx 是否存在

    最后打印「当前数据的关键数字」，供人对照论文正文。

.PARAMETER Project
    project 目录（含 scripts、data、dashboard）。默认按 skill 位置推断。

.PARAMETER Root
    工作区根；给了就按 <root>\final paper\project 找。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\smoke.ps1
#>
param(
    [string]$Project = "",
    [string]$Root = "",
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = "utf-8"

$script:pass = 0; $script:warn = 0; $script:fail = 0
function Pass($m) { $script:pass++; Write-Host "[PASS] $m" -ForegroundColor Green }
function Warn($m) { $script:warn++; Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { $script:fail++; Write-Host "[FAIL] $m" -ForegroundColor Red }
function Head($m) { Write-Host ""; Write-Host "-- $m" -ForegroundColor White }

# ---------------------------------------------------------------- 定位
if ($Project) {
    $Proj = $Project
} elseif ($Root) {
    $Proj = Join-Path $Root "final paper\result\project"
} else {
    # 已安装：<工作区>\.dsh\skills\ecom-viz-paper\scripts\smoke.ps1
    # 就地运行：<工作区>\final paper\result\project_skill\scripts\smoke.ps1
    $skillDir = Split-Path -Parent $PSScriptRoot
    $rootGuess = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $skillDir))
    $Proj = Join-Path $rootGuess "final paper\result\project"
    if (-not (Test-Path (Join-Path $Proj "scripts"))) {
        # 就地运行时 project 与 project_skill 同级
        $sibling = Join-Path (Split-Path -Parent $skillDir) "project"
        if (Test-Path (Join-Path $sibling "scripts")) { $Proj = $sibling }
    }
}
if (-not (Test-Path $Proj)) { Fail "项目目录不存在: $Proj"; exit 1 }
$Proj = (Resolve-Path $Proj).Path
$rootDir = Split-Path -Parent (Split-Path -Parent $Proj)
Write-Host "体检目标: $Proj"

# ---------------------------------------------------------------- 结构
Head "项目结构"
$required = @(
    "scripts\analyze.py", "scripts\figs.py", "scripts\data_generate.py", "scripts\build_data_js.py",
    "data\ecommerce_dashboard_data.csv",
    "dashboard\index.html", "dashboard\app.js", "dashboard\data.js", "dashboard\server.mjs"
)
$missing = @()
foreach ($r in $required) { if (-not (Test-Path (Join-Path $Proj $r))) { $missing += $r } }
if ($missing.Count -eq 0) { Pass "必需文件齐全（$($required.Count) 项）" }
else { Fail "缺少文件: $($missing -join ', ')" }

$extras = @("scripts\check_env.py", "requirements.txt")
foreach ($e in $extras) {
    if (Test-Path (Join-Path $Proj $e)) { Pass "可选文件存在: $e" } else { Warn "缺少可选文件: $e" }
}

# ---------------------------------------------------------------- CSV
Head "数据"
$Csv = Join-Path $Proj "data\ecommerce_dashboard_data.csv"
$csvNewest = $null
if (Test-Path $Csv) {
    $head = Get-Content $Csv -TotalCount 1
    $cols = $head.TrimStart([char]0xFEFF) -split ","
    $need = @("Date", "Category", "Channel", "Ad_Spend", "GMV", "Conversion_Rate", "Bounce_Rate")
    $lack = @($need | Where-Object { $cols -notcontains $_ })
    if ($lack.Count -eq 0) { Pass "CSV 列齐全（$($cols.Count) 列）" }
    else { Fail "CSV 缺少列: $($lack -join ', ')" }
    $n = (Get-Content $Csv).Count - 1
    if ($n -ge 2) { Pass "CSV 行数: $n" } else { Fail "CSV 行数异常: $n" }
    $csvNewest = (Get-Item $Csv).LastWriteTime
} else { Fail "CSV 不存在" }

# ---------------------------------------------------------------- 统计新鲜度
Head "统计"
$Stats = Join-Path $Proj "analysis_stats.json"
if (Test-Path $Stats) {
    $stTime = (Get-Item $Stats).LastWriteTime
    if ($csvNewest -and $stTime -lt $csvNewest) {
        Warn "analysis_stats.json 比 CSV 旧（统计过期），跑 scripts\resync.ps1"
    } else { Pass "analysis_stats.json 不早于 CSV" }
} else { Fail "analysis_stats.json 不存在，跑 scripts\analyze.py" }

# ---------------------------------------------------------------- data.js 同步
Head "页面数据"
$py = $null
$cands = @()
if ($PythonExe) { $cands += $PythonExe }
if ($env:USERPROFILE) { $cands += (Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe") }
$cands += "python"
foreach ($c in $cands) {
    if (-not $c) { continue }
    if ($c -ne "python" -and -not (Test-Path $c)) { continue }
    try { $null = & $c -c "import json" 2>$null; if ($LASTEXITCODE -eq 0) { $py = $c; break } } catch { }
}
$buildJs = Join-Path $Proj "scripts\build_data_js.py"
if ($py -and (Test-Path $buildJs)) {
    & $py $buildJs --check 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Pass "data.js 与 CSV 一致" }
    else { Fail "data.js 与 CSV 不一致，跑 scripts\build_data_js.py --force" }
} else { Warn "无法比较 data.js（找不到 python 或 build_data_js.py）" }

# ---------------------------------------------------------------- 插图
Head "插图"
$figs = @("fig1_arch.png", "fig2_pipeline.png", "fig4_category.png", "fig5_trend.png",
          "fig6_scatter.png", "fig7_heatmap.png", "fig8_cvr_bounce.png", "fig9_color.png", "fig10_agent.png")
$figDir = Join-Path $Proj "figures"
$figMissing = @(); $figStale = @()
foreach ($f in $figs) {
    $p = Join-Path $figDir $f
    if (-not (Test-Path $p)) { $figMissing += $f; continue }
    if ($csvNewest -and (Get-Item $p).LastWriteTime -lt $csvNewest) { $figStale += $f }
}
if ($figMissing.Count -eq 0) { Pass "9 张论文插图齐全" } else { Fail "缺插图: $($figMissing -join ', ')" }
if ($figStale.Count -eq 0) { Pass "插图不早于 CSV" } else { Warn "以下插图早于 CSV，需重绘: $($figStale -join ', ')" }

# ---------------------------------------------------------------- JS 语法
Head "前端语法"
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) {
    foreach ($js in @("app.js", "data.js", "server.mjs")) {
        $p = Join-Path $Proj ("dashboard\" + $js)
        if (-not (Test-Path $p)) { continue }
        & node --check $p 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { Pass "node --check $js" } else { Fail "node --check $js 失败" }
    }
} else { Warn "未找到 node，跳过前端语法检查" }

# ---------------------------------------------------------------- 论文
Head "论文"
$docs = @()
foreach ($d in @($rootDir, (Split-Path -Parent $rootDir))) {
    if ($d -and (Test-Path $d)) {
        $docs += @(Get-ChildItem $d -Filter "*.docx" -ErrorAction SilentlyContinue |
                   Where-Object { $_.Name -notlike "~`$*" -and $_.Name -notlike "_new*" })
    }
}
if ($docs.Count -gt 0) {
    foreach ($d in $docs) { Pass ("论文: {0}（{1:N0} KB，{2:yyyy-MM-dd HH:mm}）" -f $d.Name, ($d.Length / 1KB), $d.LastWriteTime) }
} else { Warn "final paper 下没有 docx（若只想验数据链路可忽略）" }

# ---------------------------------------------------------------- 数字
Head "当前数据的关键数字（人工对照论文）"
if (Test-Path $Stats) {
    try {
        $s = Get-Content -Raw -Encoding UTF8 $Stats | ConvertFrom-Json
        Write-Host ("  样本: {0} ~ {1}，{2} 天" -f $s.date_range[0], $s.date_range[1], $s.n_days)
        Write-Host ("  GMV {0:N2} 万   花费 {1:N2} 万   ROAS {2:N4}" -f ([double]$s.total_gmv / 1e4), ([double]$s.total_spend / 1e4), $s.roas)
        Write-Host ("  日度 CV {0:P2}   最差环比 {1} {2}%" -f $s.daily_cv, $s.worst_dod.date, $s.worst_dod.chg)
        $catTop = $s.category | Select-Object -First 1
        $catBot = $s.category | Select-Object -Last 1
        Write-Host ("  品类 ROAS: 最高 {0} {1:N3} / 最低 {2} {3:N3}" -f $catTop.name, $catTop.roas, $catBot.name, $catBot.roas)
    } catch { Warn "analysis_stats.json 解析失败: $_" }
}
Write-Host ""
Write-Host ("汇总: PASS {0}  WARN {1}  FAIL {2}" -f $script:pass, $script:warn, $script:fail)
if ($script:fail -gt 0) { Write-Host "有 FAIL，按上面提示修；数字类 WARN 属正常（换数据后需人工回填论文）。" -ForegroundColor Red; exit 1 }
Write-Host "结构一致。若刚换过数据，记得回填论文数字并重导 docx。" -ForegroundColor Green
exit 0
