<#
.SYNOPSIS
    把本目录（result）里的 skill 安装到指定工作区的 .dsh\skills\ 下。

.DESCRIPTION
    DSH 会从 <工作区>\.dsh\skills\<name>\SKILL.md 发现项目级 skill。
    安装后，在该工作区打开的会话里即可按 name 引用本流程。

.PARAMETER Workspace
    工作区根目录。默认按位置推断：project_skill 的上三级（含 final paper\ 的那一级）。

.PARAMETER Force
    目标已存在时覆盖。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Workspace "D:\my-viz-paper" -Force
#>
param(
    [string]$Workspace = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$src = Split-Path -Parent $PSScriptRoot
if (-not $Workspace) {
    # <工作区>\final paper\result\project_skill -> 上三级 = 工作区根
    $Workspace = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $src))
}
if (-not (Test-Path $Workspace)) {
    Write-Host "[fail] 工作区不存在: $Workspace" -ForegroundColor Red
    exit 1
}

$dest = Join-Path $Workspace ".dsh\skills\ecom-viz-paper"
if ((Test-Path $dest) -and (-not $Force)) {
    Write-Host "[warn] 目标已存在: $dest（加 -Force 覆盖）" -ForegroundColor Yellow
    exit 1
}

foreach ($f in @("SKILL.md", "scripts\resync.ps1", "scripts\smoke.ps1", "scripts\install.ps1")) {
    $s = Join-Path $src $f
    if (-not (Test-Path $s)) {
        Write-Host "[fail] 源文件缺失: $s" -ForegroundColor Red
        exit 1
    }
    $d = Join-Path $dest $f
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $d) | Out-Null
    Copy-Item $s $d -Force
}

Write-Host "[ ok ] 已安装到 $dest" -ForegroundColor Green
Write-Host ""
Write-Host "验证："
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$dest\scripts\smoke.ps1`" -Root `"$Workspace`""
Write-Host "换数据重算："
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$dest\scripts\resync.ps1`" -Root `"$Workspace`" -Regenerate -Seed 7"
