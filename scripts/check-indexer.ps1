#requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$config = Get-Content (Join-Path $root 'preparation/indexer.json') -Raw | ConvertFrom-Json
$runId = 'indexer-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 6)
$output = Join-Path $root "artifacts/$runId"
New-Item -ItemType Directory -Path $output | Out-Null
$previous = $env:INDEXER_WORK_DIR
$env:INDEXER_WORK_DIR = $output
$compose = @('compose', '--project-name', $runId, '--env-file', (Join-Path $root '.env.example'), '--project-directory', $root,
    '-f', (Join-Path $root 'compose.indexer.yaml'))
function Invoke-Indexer {
    param([string[]]$Arguments)
    & docker @compose @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Indexer Compose failed ($LASTEXITCODE): $Arguments. Results: $output" }
}
try {
    Invoke-Indexer -Arguments @('config', '--quiet')
    Invoke-Indexer -Arguments @('build', 'fetch')
    Invoke-Indexer -Arguments @('run', '--rm', '--no-deps', '-T', '--entrypoint', 'python', 'index', '-m', 'unittest', '-v', 'test_runner')
    Invoke-Indexer -Arguments @('run', '--rm', '--no-deps', '-T', 'fetch', 'fetch')
    $failures = @()
    foreach ($sample in $config.samples) {
        try { Invoke-Indexer -Arguments @('run', '--rm', '--no-deps', '-T', 'index', 'index', $sample.id) }
        catch { $failures += $sample.id; Write-Warning $_ }
    }
    if ($failures.Count) { throw "Incomplete extractions/queries: $failures. Evidence retained: $output" }
    Write-Output "Extraction complete. Review coverage, relations and query errors before deciding: $output"
}
finally {
    & docker @compose down --remove-orphans
    $cleanupCode = $LASTEXITCODE
    $env:INDEXER_WORK_DIR = $previous
    if ($cleanupCode -ne 0) { throw "Could not clean up temporary project $runId" }
}
