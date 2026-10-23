#requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent

function Invoke-Git {
    param([string[]]$Arguments)
    & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Git falló ($LASTEXITCODE): $Arguments" }
}

# Preflight both destinations before touching either. Never reset an existing tree.
$sources = @(
    @{ Name = 'Hermes3D'; Version = 'HERMES3D_VERSION'; Url = 'https://github.com/iamlukethedev/Hermes3D.git' },
    @{ Name = 'hermes-runtime'; Version = 'HERMES_AGENT_VERSION'; Url = 'https://github.com/NousResearch/hermes-agent.git' }
)
foreach ($source in $sources) {
    $source.Commit = (Get-Content -LiteralPath (Join-Path $root $source.Version) -Raw).Trim()
    if ($source.Commit -cnotmatch '^[0-9a-f]{40}$') { throw "Commit inválido en $($source.Version)" }
    $source.Path = Join-Path $root "vendor/$($source.Name)"
    if (Test-Path -LiteralPath $source.Path) { throw "Ya existe $($source.Path). Usa un clon limpio; no se sobrescribe." }
}
foreach ($source in $sources) {
    Invoke-Git -Arguments @('init', '--quiet', $source.Path)
    Invoke-Git -Arguments @('-C', $source.Path, 'config', 'core.longpaths', 'true')
    Invoke-Git -Arguments @('-C', $source.Path, 'config', 'core.autocrlf', 'false')
    Invoke-Git -Arguments @('-C', $source.Path, 'remote', 'add', 'origin', $source.Url)
    Invoke-Git -Arguments @('-C', $source.Path, 'fetch', '--depth', '1', 'origin', $source.Commit)
    Invoke-Git -Arguments @('-C', $source.Path, 'checkout', '--detach', 'FETCH_HEAD')
    $actual = & git -C $source.Path rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $actual -cne $source.Commit) { throw 'El commit recuperado no coincide.' }
}
$office = $sources[0].Path
$patch = Join-Path $root 'docker/hermes3d-local-demo.patch'
Invoke-Git -Arguments @('-C', $office, 'apply', '--check', $patch)
Invoke-Git -Arguments @('-C', $office, 'apply', $patch)
Invoke-Git -Arguments @('-C', $office, 'apply', '--reverse', '--check', $patch)
Write-Output 'Fuentes fijadas recuperadas y parche aplicado/verificado. No se han ejecutado scripts de los originales en el host.'
