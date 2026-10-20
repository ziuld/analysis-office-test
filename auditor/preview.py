"""Evaluate the new format on an immutable saved snapshot, never on live main."""
import argparse
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from repository import AuditError
from settings import settings, runtime_options
from team import run_team, write_json
from reporting import markdown


def preview(source_id, root=None, invoke=None):
    root = root or Path(os.environ.get("AUDIT_REPORTS_DIR", "/reports"))
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", source_id):
        raise AuditError("Identificador de revisión inválido.")
    source = (root / source_id).resolve()
    if source.parent != root.resolve():
        raise AuditError("La revisión debe estar dentro de reports.")
    try:
        snapshot = json.loads((source / "evidencia.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise AuditError("No se encontró evidencia guardada válida.") from None
    with (root / ".audit.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AuditError("Hay una revisión o consulta activa; no se inició la prueba de formato.") from None
        hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                  for name in ("evidencia.json", "informe.json", "informe.md") if (source / name).is_file()}
        now = datetime.now(timezone.utc)
        output = root / (now.strftime("%Y%m%dT%H%M%S%fZ") + "-fase6")
        output.mkdir()
        provider, model = settings()
        snapshot.update(source_revision=source_id, source_hashes=hashes, analyzed_at=now.isoformat(),
                        evidence_origin=f"Prueba de formato sobre la evidencia guardada de {source_id}, commit {snapshot['commit']}. GitHub no se ha releído y no se comprobó el main actual. Los informes originales se conservan.",
                        runtime={"provider": provider, "model": model, "reasoning": runtime_options()["reasoning_config"]["effort"]})
        write_json(output / "evidencia.json", snapshot)
        data = run_team(snapshot, output, **({"invoke": invoke} if invoke else {}))
        write_json(output / "informe.json", data)
        (output / "informe.md").write_text(markdown(data, snapshot, provider + "/" + model), encoding="utf-8")
        if any(hashlib.sha256((source / name).read_bytes()).hexdigest() != value for name, value in hashes.items()):
            raise AuditError("La evidencia original cambió durante la prueba; revisar la trazabilidad.")
        return output, data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prueba de formato con evidencia guardada; ejecuta las tres células.")
    parser.add_argument("source_id")
    parser.add_argument("--render-only", action="store_true", help="Actualizar solo el Markdown de un ejemplo derivado; sin modelo.")
    args = parser.parse_args()
    try:
        if args.render_only:
            root = Path(os.environ.get("AUDIT_REPORTS_DIR", "/reports"))
            if not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", args.source_id):
                raise AuditError("Identificador de ejemplo inválido.")
            directory = (root / args.source_id).resolve()
            if directory.parent != root.resolve():
                raise AuditError("El ejemplo debe estar dentro de reports.")
            snapshot = json.loads((directory / "evidencia.json").read_text(encoding="utf-8-sig"))
            report = json.loads((directory / "informe.json").read_text(encoding="utf-8-sig"))
            if not snapshot.get("source_revision") or report.get("schema_version") != 2:
                raise AuditError("Solo se reformatea un ejemplo derivado de formato 2; no el informe original.")
            model = snapshot["runtime"]["provider"] + "/" + snapshot["runtime"]["model"]
            (directory / "informe.md").write_text(markdown(report, snapshot, model), encoding="utf-8")
        else:
            directory, report = preview(args.source_id)
        print(f"Informe de formato 2: {directory}/informe.md · estado: {report['estado']}")
        if report["estado"] != "completo":
            raise AuditError("Se conserva el informe parcial; no se reintenta automáticamente.")
    except AuditError as exc:
        parser.exit(1, str(exc) + "\n")
