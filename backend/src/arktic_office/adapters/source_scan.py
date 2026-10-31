"""Trusted local Semgrep rules. No target config, code execution or model calls."""
from pathlib import Path
import shutil
import subprocess
import time
from arktic_office.resources.paths import resource_path

EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".php", ".go"}

def scan_source(safe, root, runner):
    started = time.monotonic()
    source = root / "sast-source"
    source.mkdir()
    inputs = []
    for path, relative in safe.items():
        if Path(relative).suffix.lower() in EXTENSIONS:
            dest = source / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            inputs.append(relative)
    # Override default exclusions; never honor target .semgrepignore/config.
    (source / ".semgrepignore").write_text("", encoding="utf-8")
    item = {"name": "Semgrep 1.182.1", "status": "no_evaluado", "findings": [], "input_files": inputs,
            "detail": "Reglas locales acotadas para Python, JavaScript/TypeScript, Java, C#, PHP y Go. Sin análisis exhaustivo ni explotación probada."}
    if inputs:
        try:
            output = root / "semgrep.json"
            payload = runner(["semgrep", "scan", "--oss-only", "--config", str(resource_path("profiles", "semgrep-rules.json")),
                "--json", "--output", str(output), "--metrics=off", "--disable-version-check", "--no-git-ignore",
                "--no-rewrite-rule-ids", "--jobs=1", "--timeout=10", "--max-target-bytes=32000000", str(source)], output)
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                raise ValueError()
            for hit in payload["results"]:
                path = Path(hit.get("path", ""))
                if not path.is_absolute():
                    path = root / path
                relative = path.relative_to(source).as_posix()
                line = hit.get("start", {}).get("line")
                rule = hit.get("check_id", "")
                if relative not in inputs or type(line) is not int or line < 1 or not rule.startswith("arktic."):
                    raise ValueError()
                item["findings"].append({"path": relative, "line": line,
                    "summary": "Patrón SAST · " + rule + ". Revisar origen de datos y controles; no demuestra vulnerabilidad explotable."})
            scanned = payload.get("paths", {}).get("scanned", [])
            item["processed_files"] = [Path(p).relative_to(source).as_posix() if Path(p).is_absolute() else Path(p).relative_to(source.relative_to(root)).as_posix() for p in scanned]
            if payload.get("errors") or set(item["processed_files"]) != set(inputs):
                raise ValueError()
            item["status"] = "detecciones_por_validar" if item["findings"] else "sin_detecciones_en_seleccion"
        except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.TimeoutExpired):
            item.update(status="error", detail="Semgrep no completó todas las fuentes compatibles; no se interpreta como ausencia de problemas.")
    item["seconds"] = round(time.monotonic() - started, 3)
    return item
