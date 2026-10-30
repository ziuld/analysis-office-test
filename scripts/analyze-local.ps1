param(
    [Parameter(Mandatory=$true)][string]$Repository,
    [switch]$InspectOnly,
    [switch]$PrepareOnly,
    [ValidateRange(1000000,256000000)][long]$MaxSnapshotBytes = 32000000
)
$ErrorActionPreference = 'Stop'
if ($InspectOnly -and $PrepareOnly) { throw 'Usar -InspectOnly o -PrepareOnly, no ambas.' }
$officeRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = (Resolve-Path -LiteralPath $Repository).Path
if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw 'Indicar una carpeta de repositorio Git.' }
$hostAutocrlf = (& git -C $repoRoot config --get core.autocrlf)
if ($LASTEXITCODE -eq 1) { $hostAutocrlf = 'false' } elseif ($LASTEXITCODE -ne 0) { throw 'No se pudo leer la configuración Git local.' }
$hostFilemode = (& git -C $repoRoot config --get core.filemode)
if ($LASTEXITCODE -eq 1) { $hostFilemode = 'false' } elseif ($LASTEXITCODE -ne 0) { throw 'No se pudo leer la configuración Git local.' }
$bundleRoot = Join-Path $officeRoot ('artifacts/local-inputs/' + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $bundleRoot -Force | Out-Null
Push-Location $officeRoot
try {
    # Only the explicitly supplied checkout is mounted. No host drive or Git credentials.
    & docker run --rm --read-only --network none --cap-drop ALL --security-opt no-new-privileges `
        --tmpfs /tmp:rw,noexec,nosuid,size=128m `
        --mount "type=bind,source=$repoRoot,target=/repository,readonly" `
        --mount "type=bind,source=$PSScriptRoot,target=/scripts,readonly" `
        --mount "type=bind,source=$bundleRoot,target=/bundle" `
        --entrypoint python arktic-indexer:graphify-0.9.97 `
        /scripts/export-local.py /repository /bundle --origin $repoRoot --autocrlf $hostAutocrlf --filemode $hostFilemode --max-bytes $MaxSnapshotBytes
    if ($LASTEXITCODE -ne 0) { throw 'No se capturó el repositorio; no se inicia el equipo.' }
    Write-Output "Snapshot conservado: $bundleRoot"
    if ($PrepareOnly) {
        Write-Output 'Captura lista. Abrir http://localhost:3000/office, elegir Repositorio local e iniciar la revisión.'
        return
    }
    & docker compose -f compose.yaml -f compose.hybrid.yaml up -d --wait preparator
    if ($LASTEXITCODE -ne 0) { throw 'El preparador no está disponible.' }
    $runArgs = @('compose','-f','compose.yaml','-f','compose.hybrid.yaml','--profile','audit',
        'run','--rm','-T','--volume',"${bundleRoot}:/local-input:ro",'auditor','--local-snapshot','/local-input')
    if ($InspectOnly) { $runArgs += '--inspect-only' }
    & docker @runArgs
    if ($LASTEXITCODE -ne 0) { throw 'El equipo devolvió un error o resultado parcial; revisar el informe y las respuestas conservadas.' }
} finally { Pop-Location }
