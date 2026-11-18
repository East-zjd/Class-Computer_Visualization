<#
.SYNOPSIS
    校验本目录文件的完整性（与 CHECKSUMS.txt 比对）。

.DESCRIPTION
    Git 在推送时可能把 CRLF 换成 LF（本仓库的 analysis_stats.json、
    visualization_business_data.csv、CHECKSUMS.txt 就发生过），
    直接对字节做 SHA256 会出现“内容一样但哈希不同”的假失败。

    因此 CHECKSUMS.txt 记录的是**文本规范化后**的哈希：
    文本类文件先统一换行（CRLF/CR → LF）再算 SHA256，二进制文件（PNG 等）按原始字节算。
    这样本地 CRLF 副本与 GitHub 上 LF 副本都能通过。

.PARAMETER Root
    校验目录，默认本脚本所在目录。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File verify.ps1
#>
param([string]$Root = $PSScriptRoot)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$sumFile = Join-Path $Root "CHECKSUMS.txt"
if (-not (Test-Path $sumFile)) { Write-Host "[fail] 找不到 $sumFile" -ForegroundColor Red; exit 1 }

$textExt = @(".md", ".txt", ".json", ".csv", ".js", ".mjs", ".py", ".html", ".ps1", ".gitattributes", ".yml", ".yaml")

function Get-NormHash([string]$path) {
    $ext = [System.IO.Path]::GetExtension($path).ToLower()
    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($textExt -contains $ext) {
        $text = [System.Text.Encoding]::UTF8.GetString($bytes)
        $text = $text.Replace("`r`n", "`n").Replace("`r", "`n")
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ([System.BitConverter]::ToString($sha.ComputeHash($bytes)) -replace "-", "").ToLower() }
    finally { $sha.Dispose() }
}

$ok = 0; $bad = @(); $missing = @()
foreach ($line in Get-Content $sumFile -Encoding UTF8) {
    if ($line -notmatch '^\s*([0-9a-fA-F]{64})\s{2,}(.+?)\s{2,}(\d+)\s*$') { continue }
    $want = $Matches[1].ToLower()
    $rel = $Matches[2]
    $path = Join-Path $Root $rel
    if (-not (Test-Path $path)) { $missing += $rel; continue }
    $got = Get-NormHash $path
    if ($got -eq $want) { $ok++ } else { $bad += ("{0}`n      期望 {1}`n      实际 {2}" -f $rel, $want, $got) }
}

Write-Host ""
Write-Host "校验目录: $Root"
Write-Host ("一致: {0}   不一致: {1}   缺失: {2}" -f $ok, $bad.Count, $missing.Count)
if ($bad.Count) { Write-Host ""; Write-Host "内容与清单不符:" -ForegroundColor Red; $bad | ForEach-Object { Write-Host ("  - " + $_) -ForegroundColor Red } }
if ($missing.Count) { Write-Host ""; Write-Host "清单里有、目录里没有:" -ForegroundColor Yellow; $missing | ForEach-Object { Write-Host ("  - " + $_) -ForegroundColor Yellow } }

if ($bad.Count -or $missing.Count) { exit 1 }
Write-Host "全部通过。" -ForegroundColor Green
exit 0
