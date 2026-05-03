param(
    [string]$AppDir = "C:\srv\scraper\app",
    [string]$OutputDir = "C:\srv\scraper\output",
    [string]$Source = "cisa_kev_json",
    [string]$Collector = "",
    [int]$Limit = 25,
    [switch]$Live,
    [string]$Out = ""
)

$ErrorActionPreference = "Stop"

if ($Limit -lt 0) {
    throw "Limit must be non-negative"
}

if (!(Test-Path $AppDir)) {
    throw "AppDir does not exist: $AppDir"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$Catalog = Join-Path $AppDir "config\source_catalog.json"
if (!(Test-Path $Catalog)) {
    throw "Source catalog not found: $Catalog"
}

if ([string]::IsNullOrWhiteSpace($Out)) {
    $safeName = if ([string]::IsNullOrWhiteSpace($Collector)) { $Source } else { $Collector }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Out = Join-Path $OutputDir "$safeName-$stamp.jsonl"
}

$env:PYTHONPATH = $AppDir

$argsList = @("-m", "scraper_side.cli", "--limit", "$Limit", "--out", $Out)
if ($Live) {
    $argsList += "--live"
}

if (![string]::IsNullOrWhiteSpace($Collector)) {
    $argsList += @("--collector", $Collector)
} else {
    $argsList += @("--catalog", $Catalog, "--source", $Source)
}

python @argsList
Write-Output "sanitized_output=$Out"
