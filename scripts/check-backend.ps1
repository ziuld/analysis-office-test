#requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$compose = @('compose', '--env-file', (Join-Path $root '.env.example'),
    '--project-directory', $root, '-f', (Join-Path $root 'compose.backend-tests.yaml'))
& docker @compose build backend-tests
if ($LASTEXITCODE -ne 0) { throw 'Backend test image build failed' }
& docker @compose run --rm --no-deps -T backend-tests
if ($LASTEXITCODE -ne 0) { throw 'Backend regression failed' }
