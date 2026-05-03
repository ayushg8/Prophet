param(
    [string]$AppDir = "C:\srv\scraper\app",
    [string]$OutputDir = "C:\srv\scraper\output",
    [string]$StateDir = "C:\srv\scraper\state",
    [string]$Source = "cisa_kev_json",
    [string]$Collector = "",
    [int]$Limit = 25,
    [switch]$Live,
    [switch]$AllEnabled,
    [string]$RunId = "",
    [string]$Out = ""
)

$ErrorActionPreference = "Stop"

if ($Limit -lt 0) {
    throw "Limit must be non-negative"
}

if (!(Test-Path $AppDir)) {
    throw "AppDir does not exist: $AppDir"
}

New-Item -ItemType Directory -Force -Path $OutputDir,$StateDir | Out-Null

$Catalog = Join-Path $AppDir "config\source_catalog.json"
if (!(Test-Path $Catalog)) {
    throw "Source catalog not found: $Catalog"
}

$env:PYTHONPATH = $AppDir

if ($AllEnabled) {
    if ([string]::IsNullOrWhiteSpace($RunId)) {
        $RunId = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    }
    $env:SCRAPER_APP_DIR = $AppDir
    $env:SCRAPER_OUTPUT_DIR = $OutputDir
    $env:SCRAPER_STATE_DIR = $StateDir
    $env:SCRAPER_CATALOG = $Catalog
    $env:SCRAPER_RUN_ID = $RunId
    $env:SCRAPER_LIMIT = "$Limit"
    $env:SCRAPER_LIVE = if ($Live) { "1" } else { "0" }

    python (Join-Path $AppDir "bin\collect-once.py")
    python (Join-Path $AppDir "bin\sanitize-once.py")
    $SanitizedOutput = Join-Path $OutputDir "sanitized-$RunId.jsonl"
    $CollectionManifest = Join-Path $StateDir "collection-manifest-$RunId.json"
    $SanitizationManifest = Join-Path $OutputDir "sanitization-manifest-$RunId.json"
    Write-Output "sanitized_output=$SanitizedOutput"
    Write-Output "collection_manifest=$CollectionManifest"
    Write-Output "sanitization_manifest=$SanitizationManifest"
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Out)) {
    $safeName = if ([string]::IsNullOrWhiteSpace($Collector)) { $Source } else { $Collector }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $Out = Join-Path $OutputDir "$safeName-$stamp.jsonl"
}

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
