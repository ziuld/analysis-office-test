"""Evaluate the new format on an immutable saved snapshot, never on live main."""
import argparse
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from arktic_office.preparation.repository import AuditError
from arktic_office.config.settings import settings, runtime_options
from arktic_office.coordination.team import run_team, write_json
from arktic_office.reporting.reports import markdown
from arktic_office.config.settings import reports_root
from arktic_office.storage.runs import RunStore


def preview(source_id, root=None, invoke=None):
    root = root or reports_root()
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", source_id):
        raise AuditError("Identificador de revisión inválido.")
    try:
        source = RunStore(root).resolve(source_id)
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
        output = RunStore(root).create(now.strftime("%Y%m%dT%H%M%S%fZ") + "-fase6")
        provider, model = settings()
        snapshot.update(source_revision=source_id, source_hashes=hashes, analyzed_at=now.isoformat(),
                        evidence_origin=f"Prueba de formato sobre la evidencia guardada de {source_id}, commit {snapshot['commit']}. GitHub no se ha releído y no se comprobó el main actual. Los informes originales se conservan.",
                        runtime={"provider": provider, "model": model, "reasoning": runtime_options()["reasoning_config"]["effort"]})
        write_json(output / "evidencia.json", snapshot)
        data = run_team(snapshot, output, **({"invoke": invoke} if invoke else {}))
        write_json(output / "informe.json", data)
        (output / "informe.md").write_text(markdown(data, snapshot, provider + "/" + model), encoding="utf-8")
        if data.get("schema_version") == 3:
            from arktic_office.reporting.executive import render_html
            (output / "informe.html").write_text(render_html(data, snapshot), encoding="utf-8")
        if any(hashlib.sha256((source / name).read_bytes()).hexdigest() != value for name, value in hashes.items()):
            raise AuditError("La evidencia original cambió durante la prueba; revisar la trazabilidad.")
        return output, data


def main():
    parser = argparse.ArgumentParser(description="Prueba de formato con evidencia guardada; ejecuta las tres células.")
    parser.add_argument("source_id")
    parser.add_argument("--render-only", action="store_true", help="Actualizar solo el Markdown de un ejemplo derivado; sin modelo.")
    args = parser.parse_args()
    try:
        if args.render_only:
            root = reports_root()
            if not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", args.source_id):
                raise AuditError("Identificador de ejemplo inválido.")
            try:
                directory = RunStore(root).resolve(args.source_id)
            except FileNotFoundError:
                raise AuditError("No se encontró el ejemplo guardado.") from None
            snapshot = json.loads((directory / "evidencia.json").read_text(encoding="utf-8-sig"))
            report = json.loads((directory / "informe.json").read_text(encoding="utf-8-sig"))
            if not snapshot.get("source_revision") or report.get("schema_version") not in (2, 3):
                raise AuditError("Solo se reformatea un ejemplo derivado; no el informe original.")
            model = snapshot["runtime"]["provider"] + "/" + snapshot["runtime"]["model"]
            (directory / "informe.md").write_text(markdown(report, snapshot, model), encoding="utf-8")
            if report.get("schema_version") == 3:
                from arktic_office.reporting.executive import render_html
                (directory / "informe.html").write_text(render_html(report, snapshot), encoding="utf-8")
        else:
            directory, report = preview(args.source_id)
        print(f"Informe de formato {report.get('schema_version', 1)}: {directory}/informe.md · estado: {report['estado']}")
        if report["estado"] != "completo":
            raise AuditError("Se conserva el informe parcial; no se reintenta automáticamente.")
    except AuditError as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
