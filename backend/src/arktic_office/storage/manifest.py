"""Reproducibility metadata for new results; no historical rewrites or release claim."""
import hashlib
from pathlib import Path
from importlib.metadata import version
from arktic_office.resources.paths import resource_path
from arktic_office.storage.jsonio import write_json
from arktic_office.reporting.reports import HERMES_COMMIT


def write_manifest(directory, snapshot, report=None):
    resources = {}
    root = resource_path()
    for folder in ("profiles", "skills", "editorial"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file():
                resources[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    usage = {"specialists": [{"id": c["id"], "usage": c.get("usage")} for c in (report or {}).get("celulas", [])],
             "preparation": snapshot.get("preparation", {}).get("exploration", {}).get("usage", []),
             "coordination": {k: v.get("usage") for k, v in (report or {}).get("coordination", {}).get("stages", {}).items()}}
    package = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in sorted(package.rglob("*.py")):
        digest.update(path.relative_to(package).as_posix().encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    write_json(directory / "manifest.json", {"schema_version": 1, "delivery": "closed", "backend_version": version("arktic-office-backend"),
        "backend_source_sha256": digest.hexdigest(),
        "hermes_agent": HERMES_COMMIT, "repository": snapshot["repository"], "branch": snapshot.get("branch"),
        "commit": snapshot["commit"], "source_type": snapshot.get('source_type','github'),
        "local_source": snapshot.get('local_source'), "analyzed_at": snapshot.get("analyzed_at"), "profiles": snapshot.get("model_profiles", {}),
        "request": snapshot.get("request", {}), "resource_sha256": resources, "coverage": snapshot.get("coverage", {}),
        "usage": usage, "status": (report or {}).get("estado", "inspection"),
        "limitations": ["Sin consumo comunicado no se asume cero.", "Fase 1 aceptada; no equivale a una publicación ni demuestra exhaustividad semántica."]})
