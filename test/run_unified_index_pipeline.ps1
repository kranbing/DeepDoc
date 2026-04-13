param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [string]$OutputDir = "./output/pipeline_unified",

    [ValidateSet("maas", "selfhosted", "mock")]
    [string]$Mode = "maas",

    [switch]$Recurse,
    [switch]$ContinueOnError,
    [string]$BatchId = "",
    [string]$ApiKey = "",
    [string]$ConfigPath = "",
    [string]$EnvFile = "",
    [switch]$EnableMockFallback,
    [switch]$MockNoisy,
    [switch]$NoViz,
    [int]$MaxRowsPerChunk = 20,
    [int]$HeaderSearchRows = 6
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$argsList = @(
    ".\run_unified_index_pipeline.py",
    "--input", $InputPath,
    "--output-dir", $OutputDir,
    "--mode", $Mode,
    "--max-rows-per-chunk", $MaxRowsPerChunk.ToString(),
    "--header-search-rows", $HeaderSearchRows.ToString()
)

if ($Recurse) { $argsList += "--recurse" }
if ($ContinueOnError) { $argsList += "--continue-on-error" }
if ($EnableMockFallback) { $argsList += "--enable-mock-fallback" }
if ($MockNoisy) { $argsList += "--mock-noisy" }
if ($NoViz) { $argsList += "--no-viz" }
if ($BatchId) { $argsList += @("--batch-id", $BatchId) }
if ($ApiKey) { $argsList += @("--api-key", $ApiKey) }
if ($ConfigPath) { $argsList += @("--config-path", $ConfigPath) }
if ($EnvFile) { $argsList += @("--env-file", $EnvFile) }

Write-Host "Running unified batch indexing..."
Write-Host "Input:  $InputPath"
Write-Host "Output: $OutputDir"
Write-Host "Mode:   $Mode"
Write-Host ""

python @argsList
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "Batch completed successfully." -ForegroundColor Green
}
elseif ($exitCode -eq 2) {
    Write-Host "Batch completed with failed documents. Check logs/status_events.jsonl." -ForegroundColor Yellow
}
elseif ($exitCode -eq 3) {
    Write-Host "Batch aborted on first failure. Re-run with -ContinueOnError to continue." -ForegroundColor Red
}
else {
    Write-Host "Batch failed. Exit code: $exitCode" -ForegroundColor Red
}

exit $exitCode
