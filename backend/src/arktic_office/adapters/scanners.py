"""Bounded, non-executing scans. Raw sources/results exist only in temporary storage."""
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import time
from arktic_office.preparation.repository import LOCKFILES, redact


def run(command, output):
    # No inherited tokens, credentials or repository-controlled scanner settings.
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(output.parent), "TMPDIR": str(output.parent)}
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, env=env, cwd=output.parent)
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
            payload = runner(["gitleaks", "dir", str(source), "--config", str(config), "--redact=100", "--ignore-gitleaks-allow", "--no-banner", "--report-format", "json", "--report-path", str(output)], output)
            if not isinstance(payload, list):
                raise ValueError()
            for finding in payload:
                original = safe.get(finding.get("File")) or safe.get(str(source / finding.get("File", "")))
                if original and type(finding.get("StartLine")) is int:
                    rule = re.sub(r"[^a-zA-Z0-9_-]", "", str(finding.get("RuleID", "unknown")))[:80]
                    item["findings"].append({"path": original, "line": finding["StartLine"], "end_line": finding.get("EndLine", finding["StartLine"]), "summary": "Posible secreto · regla " + rule + ". Valor oculto; actividad no comprobada."})
            item["status"] = "detecciones_por_validar" if item["findings"] else "sin_detecciones_en_seleccion"
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
            item.update(status="error", detail="Gitleaks no completó la comprobación; no se interpreta como ausencia de secretos.")
        item["seconds"] = round(time.monotonic() - started, 3)
        item["input_files"] = list(safe.values())
        if source_root is not None:
            item["detail"] = "Snapshot completo ofrecido a Gitleaks; reglas y límites nativos, sin historial Git. Binarios y enlaces no equivalen a texto analizable."
        results.append(item)
        started = time.monotonic()
        locks = [path for path in safe if Path(path).name in LOCKFILES | {"requirements.txt"}]
        item = {"name": "OSV-Scanner 2.7.0", "status": "no_evaluado", "findings": [], "detail": "No hay archivos de versiones resueltas admitidos en la selección. Revisar dependencias queda pendiente."}
        if locks:
            output = root / "osv.json"
            config = root / "trusted-osv.toml"
            config.write_text("", encoding="utf-8")
            try:
                payload = runner(["osv-scanner", "scan", "source", "--no-call-analysis=all", "--no-resolve", "--all-packages", "--config=" + str(config), "--format=json", "--output-file=" + str(output)] + ["--lockfile=" + p for p in locks], output)
                packages = 0
                for result in payload.get("results", []):
                    path = safe.get(result.get("source", {}).get("path"), "archivo de dependencias seleccionado")
                    for package in result.get("packages", []):
                        pkg = package.get("package", {})
                        if not pkg.get("version"):
                            continue
                        packages += 1
                        for vuln in package.get("vulnerabilities", []):
                            identifier = str(vuln.get("id", ""))
                            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", identifier):
                                continue
                            item["findings"].append({"path": path, "summary": redact(f"{pkg.get('name', '?')} {pkg['version']} · {identifier}. Coincidencia de versión; alcance y explotación por validar.")})
                item.update(status="detecciones_por_validar" if item["findings"] else "sin_detecciones_en_seleccion" if packages else "no_evaluado",
                            detail=f"{packages} paquetes con versión en la respuesta; {len(locks)} archivos enviados. Consulta OSV en línea con metadatos de paquetes. Sin instalar dependencias ni analizar llamadas; no demuestra ausencia de vulnerabilidades.")
            except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.TimeoutExpired):
                item.update(status="error", detail="OSV no completó la comprobación (formato, acceso o tiempo). Dependencias pendientes de evaluación.")
        item["seconds"] = round(time.monotonic() - started, 3)
        item["input_files"] = [safe[p] for p in locks]
        results.append(item)
        return results
