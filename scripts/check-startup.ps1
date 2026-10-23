#requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
# Unique names isolate volumes, networks and containers from daily operation.
$project = 'arktic-ci-' + [guid]::NewGuid().ToString('N').Substring(0, 12)
$compose = @('compose', '--project-name', $project, '--project-directory', $root,
    '--env-file', (Join-Path $root '.env.example'),
    '-f', (Join-Path $root 'compose.yaml'), '-f', (Join-Path $root 'compose.ci.yaml'))
function Invoke-Compose {
    param([string[]]$Arguments)
    & docker @compose @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Compose falló ($LASTEXITCODE): $Arguments" }
}
try {
    Invoke-Compose -Arguments @('config', '--quiet')
    Invoke-Compose -Arguments @('build', 'audit-api', 'office')
    Invoke-Compose -Arguments @('up', '-d', '--no-build', '--wait', '--wait-timeout', '240', 'audit-api', 'office')
    Invoke-Compose -Arguments @('ps')
    Invoke-Compose -Arguments @('exec', '-T', 'audit-api', 'python', '-c',
        'import json,os,urllib.request; from pathlib import Path; get=lambda p: json.load(urllib.request.urlopen("http://127.0.0.1:8080/"+p,timeout=5)); h=get("health"); assert h=={"ok":True,"version":os.environ["ARKTIC_BACKEND_VERSION"]},h; assert get("runs")=={"runs":[],"question_active":None}; assert not list(Path("/reports").iterdir()); assert not list(Path("/auth").iterdir()); print(h,"Sin trabajos, informes ni autenticación")')
    Invoke-Compose -Arguments @('exec', '-T', 'office', 'node', '-e',
        '(async()=>{for(const path of ["/office","/api/audit/runs"]){const r=await fetch("http://127.0.0.1:3000"+path);if(!r.ok)throw Error(path+": "+r.status);if(path.endsWith("runs")){const j=await r.json();if(j.runs.length||j.question_active)throw Error("Actividad inesperada");}console.log("GET",path,r.status);}const h=await fetch("http://audit-api:8080/health");if(!h.ok||(await h.json()).ok!==true)throw Error("API no saludable desde office");console.log("GET audit-api /health",h.status);})().catch(e=>{console.error(e);process.exit(1)})')
    Write-Output 'Arranque saludable sin revisiones, scanners ni modelos; red interna sin salida y volúmenes nuevos sin credenciales.'
}
catch {
    & docker @compose logs --no-color --tail 100
    throw
}
finally {
    # This removes only the unique, disposable CI project, never the user's volumes.
    & docker @compose down --volumes --remove-orphans
    if ($LASTEXITCODE -ne 0) { throw "No se pudo limpiar el proyecto temporal $project" }
}
