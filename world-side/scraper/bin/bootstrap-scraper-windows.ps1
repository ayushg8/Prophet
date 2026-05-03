param(
    [string]$InstallRoot = "C:\srv\scraper",
    [string]$AppDir = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($AppDir)) {
    $AppDir = Split-Path -Parent $PSScriptRoot
}

$OutputDir = Join-Path $InstallRoot "output"
$LogDir = Join-Path $InstallRoot "logs"
$StateDir = Join-Path $InstallRoot "state"
$TmpDir = Join-Path $InstallRoot "tmp"

New-Item -ItemType Directory -Force -Path $InstallRoot, $AppDir, $OutputDir, $LogDir, $StateDir, $TmpDir | Out-Null

$python = Get-Command python -ErrorAction Stop
Write-Output "python=$($python.Source)"
python --version

$env:PYTHONPATH = $AppDir
python -m compileall -q (Join-Path $AppDir "scraper_side")

Write-Output "scraper bootstrap complete"
Write-Output "app=$AppDir"
Write-Output "output=$OutputDir"
