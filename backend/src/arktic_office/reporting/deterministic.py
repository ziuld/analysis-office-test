"""Inspectable deterministic evidence, distinct from model interpretation."""
import json
from arktic_office.preparation.repository import redact


def safe(value):
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [safe(v) for v in value]
    if isinstance(value, dict):
        return {k: "[VALOR OCULTO]" if k.lower() in {"secret", "match", "password", "token", "api_key", "lines"} else safe(v) for k, v in value.items()}
    return value


def results(snapshot, graph=None, artifact_directory=None):
    """Keep every normalized scanner result and graph output, never raw secret values."""
    records = [{"id": "D01", "name": "Adquisición e inventario del snapshot", "status": "complete" if snapshot.get("coverage", {}).get("acquisition_complete") else "partial",
        "detail": "Archivos versionados adquiridos; no equivale a revisión semántica completa ni ejecución.",
        "result": {"inventory": snapshot.get("inventory", []), "coverage": snapshot.get("coverage", {}), "excluded": snapshot.get("excluded", [])}}]
    for n, name in enumerate(("Gitleaks", "OSV-Scanner", "Semgrep"), 2):
        item = next((s for s in snapshot.get("scanners", []) if s["name"].startswith(name)), None)
        records.append({"id": f"D{n:02}", "name": item["name"] if item else name,
            "status": item["status"] if item else "no_evaluado", "detail": item.get("detail", "") if item else "Herramienta no ejecutada en esta revisión.",
            "result": item or {"findings": [], "input_files": []}})
    stored = graph or snapshot.get("preparation", {}).get("graph", {})
    records.append({"id": "D05", "name": "Graphify", "status": stored.get("status", "no_evaluado"),
        "detail": "Mapa estructural estático. Relaciones no resueltas, compatibilidad y errores se conservan; no demuestra comportamiento en ejecución.", "result": stored})
    if artifact_directory is not None:
        from pathlib import Path
        from arktic_office.storage.jsonio import read_json
        for record, folder in zip(records[1:4], ("gitleaks", "osv-scanner", "semgrep")):
            directory = Path(artifact_directory) / folder
            original = read_json(directory / "salida-original.json")
            execution = read_json(directory / "ejecucion.json")
            if original is not None:
                record["result"] = {**record["result"], "original_output_redacted": original}
            if execution is not None:
                record["result"] = {**record["result"], "execution": execution}
    return safe({"repository": snapshot["repository"], "commit": snapshot["commit"], "tools": records,
                 "preparation_cache": snapshot.get("preparation", {}).get("cache", {})})


def context(snapshot):
    """Full normalized scanner detections plus graph diagnostics; graph queries stay local."""
    saved = snapshot.get("deterministic_results")
    if not saved:
        return []
    return [{"id": t["id"], "name": t["name"], "status": t["status"], "detail": t["detail"],
             "findings": t["result"].get("findings", [])[:12],
             "findings_total": len(t["result"].get("findings", [])),
             "page_limited": len(t["result"].get("findings", [])) > 12,
             "input_count": len(t["result"].get("input_files", [])),
             "node_count": t["result"].get("node_count"), "edge_count": t["result"].get("edge_count"),
             "more": "Consultar {tool: ID, offset: 0} para páginas; grafo y código mediante queries."}
            for t in saved["tools"]]
