"""Bounded, non-executing scans. Raw sources/results exist only in temporary storage."""
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import time
import shutil
from arktic_office.preparation.repository import redact
from arktic_office.adapters.source_scan import scan_source

OSV_FILES = {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock",
    "Pipfile.lock", "poetry.lock", "requirements.txt", "pdm.lock", "pylock.toml", "uv.lock",
    "pom.xml", "gradle.lockfile", "buildscript-gradle.lockfile", "packages.config", "packages.lock.json",
    "deps.json", "go.mod", "Cargo.lock", "Gemfile.lock", "gems.locked", "composer.lock",
    "conan.lock", "pubspec.lock", "package_config.json", "mix.lock", "cabal.project.freeze", "stack.yaml.lock", "renv.lock"}

def osv_input(path):
    p = Path(path)
    name = p.name
    if name in {"bom.json", "bom.xml"} or name.endswith((".cdx.json", ".cdx.xml", ".spdx.json", ".spdx", ".spdx.yml", ".spdx.rdf", ".spdx.rdf.xml")):
        return "sbom"
    if name.endswith(".deps.json") or p.as_posix().endswith("gradle/verification-metadata.xml") or name in OSV_FILES:
        return "lockfile"
    if name.endswith(".txt") and (name.startswith("requirements") or "requirements" in p.parts):
        return "requirements.txt"
    return None



def run(command, output, *, capture=None):
    # No inherited tokens, credentials or repository-controlled scanner settings.
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(output.parent), "TMPDIR": str(output.parent)}
    started = time.monotonic()
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, env=env, cwd=output.parent)
    except subprocess.TimeoutExpired as exc:
        if capture is not None:
            folder = Path(capture) / command[0]
            folder.mkdir(parents=True, exist_ok=True)
            (folder/'stdout.txt').write_bytes(exc.stdout or b'')
            (folder/'stderr.txt').write_bytes(exc.stderr or b'')
            (folder/'ejecucion.json').write_text(json.dumps({'command':command,'exit_code':None,'timeout':True}),encoding='utf-8')
            if output.is_file(): shutil.copyfile(output,folder/'salida-original.json')
        raise
    if capture is not None:
        folder = Path(capture) / command[0]
        folder.mkdir(parents=True, exist_ok=True)
        (folder/'stdout.txt').write_bytes(result.stdout)
        (folder/'stderr.txt').write_bytes(result.stderr)
        (folder/'ejecucion.json').write_text(json.dumps({'command':command,'exit_code':result.returncode,
            'seconds':round(time.monotonic()-started,3),'timeout':False},ensure_ascii=False,indent=2),encoding='utf-8')
        if output.is_file(): shutil.copyfile(output,folder/'salida-original.json')
    if result.returncode not in (0, 1):
        raise ValueError("Scanner failed")
    if not output.is_file() or output.stat().st_size > 8_000_000:
        raise ValueError("Missing or oversized result")
    return json.loads(output.read_text(encoding="utf-8"))


def scan(files, runner=run, *, source_root=None):
    results = []
    with tempfile.TemporaryDirectory(prefix="arktic-scan-") as temp:
        root = Path(temp)
        source = Path(source_root) if source_root is not None else root / "source"
        if source_root is None:
            source.mkdir()
        safe = {}
        for f in files:
            relative = PurePosixPath(f["path"])
            if relative.is_absolute() or ".." in relative.parts or "\\" in f["path"] or ":" in f["path"]:
                continue
            path = source.joinpath(*relative.parts)
            if source_root is None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f["text"], encoding="utf-8")
            safe[str(path)] = f["path"]
        started = time.monotonic()
        output = root / "gitleaks.json"
        config = root / "trusted-gitleaks.toml"
        config.write_text("[extend]\nuseDefault = true\n", encoding="utf-8")
        item = {"name": "Gitleaks 8.30.1", "status": "no_evaluado", "findings": [], "detail": "Solo archivos seleccionados; no historial, .env ni archivos excluidos. Posibles secretos requieren validación y rotación si son reales."}
        try:
            payload = runner(["gitleaks", "dir", str(source), "--config", str(config), "--ignore-gitleaks-allow", "--no-banner", "--report-format", "json", "--report-path", str(output)], output)
            if not isinstance(payload, list):
                raise ValueError()
            item["original_output"] = payload
            for finding in payload:
                original = safe.get(finding.get("File")) or safe.get(str(source / finding.get("File", "")))
                if original and type(finding.get("StartLine")) is int:
                    rule = re.sub(r"[^a-zA-Z0-9_-]", "", str(finding.get("RuleID", "unknown")))[:80]
                    item["findings"].append({"path": original, "line": finding["StartLine"], "end_line": finding.get("EndLine", finding["StartLine"]), "summary": "Posible secreto · regla " + rule + ". Actividad no comprobada."})
            item["status"] = "detecciones_por_validar" if item["findings"] else "sin_detecciones_en_seleccion"
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
            item.update(status="error", detail="Gitleaks no completó la comprobación; no se interpreta como ausencia de secretos.")
        item["seconds"] = round(time.monotonic() - started, 3)
        item["input_files"] = list(safe.values())
        if source_root is not None:
            item["detail"] = "Snapshot completo ofrecido a Gitleaks; reglas y límites nativos, sin historial Git. Binarios y enlaces no equivalen a texto analizable."
        results.append(item)
        started = time.monotonic()
        locks = [path for path in safe if osv_input(path)]
        item = {"name": "OSV-Scanner 2.7.0", "status": "no_evaluado", "findings": [], "detail": "No hay archivos de versiones resueltas admitidos en la selección. Revisar dependencias queda pendiente."}
        if locks:
            output = root / "osv.json"
            config = root / "trusted-osv.toml"
            config.write_text("", encoding="utf-8")
            try:
                payload = runner(["osv-scanner", "scan", "source", "--no-call-analysis=all", "--all-packages", "--config=" + str(config), "--format=json", "--output-file=" + str(output)] + [("--sbom=" + p) if osv_input(p) == "sbom" else "--lockfile=" + (("requirements.txt:" + p) if osv_input(p) == "requirements.txt" else p) for p in locks], output)
                packages = 0
                evaluated = set()
                for result in payload.get("results", []):
                    path = safe.get(result.get("source", {}).get("path"), "archivo de dependencias seleccionado")
                    for package in result.get("packages", []):
                        pkg = package.get("package", {})
                        if not pkg.get("version"):
                            continue
                        packages += 1
                        if path in safe.values():
                            evaluated.add(path)
                        for vuln in package.get("vulnerabilities", []):
                            identifier = str(vuln.get("id", ""))
                            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", identifier):
                                continue
                            item["findings"].append({"path": path, "summary": redact(f"{pkg.get('name', '?')} {pkg['version']} · {identifier}. Coincidencia de versión; alcance y explotación por validar.")})
                item["evaluated_files"] = sorted(evaluated)
                item["unevaluated_files"] = [safe[p] for p in locks if safe[p] not in evaluated]
                item.update(status="detecciones_por_validar" if item["findings"] else "sin_detecciones_en_seleccion" if packages else "no_evaluado",
                            detail=f"{packages} paquetes con versión en la respuesta; {len(locks)} archivos enviados, {len(evaluated)} con paquetes versionados y {len(item["unevaluated_files"])} sin paquetes versionados. Consulta OSV en línea con metadatos de paquetes. Resolución Maven habilitada por metadatos (deps.dev); sin instalar dependencias ni ejecutar builds/código, sin analizar llamadas. No prueba versiones instaladas ni ausencia de vulnerabilidades.")
            except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.TimeoutExpired):
                item.update(status="error", detail="OSV no completó la comprobación (formato, acceso o tiempo). Dependencias pendientes de evaluación.")
        item["seconds"] = round(time.monotonic() - started, 3)
        item["input_files"] = [safe[p] for p in locks]
        item["input_kinds"] = {safe[p]: osv_input(p) for p in locks}
        results.append(item)
        results.append(scan_source(safe, root, runner))
        return results
