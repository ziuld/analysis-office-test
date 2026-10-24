"""URL → bounded branch snapshot → three Hermes cells → consolidated report."""
import argparse
import fcntl
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from arktic_office.preparation.repository import AuditError, collect
from arktic_office.config.settings import settings, runtime_options

from arktic_office.reporting.reports import make_prompt, validate_report, markdown
from arktic_office.coordination.team import plan_cells, run_team
from arktic_office.config.settings import reports_root
from arktic_office.storage.runs import RunStore


def parse_job_id(value):
    import uuid
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError("Identificador de ejecución inválido.") from None
    return value


def run(url, inspect_only=False, job_id=None):
    from arktic_office.config.models import validate_configuration
    profiles = validate_configuration()
    provider, model = settings()
    options = runtime_options()
    if not inspect_only:
        if provider == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
            raise AuditError("Falta OPENAI_API_KEY en .env para el modo API. Plus utiliza openai-codex con OAuth.")
        if provider == "openai-codex" and not (Path(os.environ["HERMES_HOME"]) / "auth.json").is_file():
            raise AuditError("Falta iniciar sesión: docker compose --profile audit run --rm --entrypoint python auditor -m hermes_cli.main auth add openai-codex")
    reports = reports_root()
    reports.mkdir(parents=True, exist_ok=True)
    with (reports / ".audit.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AuditError("Ya existe una revisión activa; espera a que termine.") from None
        from arktic_office.adapters.scanners import scan
        mode = os.environ.get("AUDIT_PREPARATION_MODE", "legacy")
        if mode not in {"legacy", "hybrid"}:
            raise AuditError("AUDIT_PREPARATION_MODE debe ser legacy o hybrid.")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        import uuid
        output = RunStore(reports).create(job_id or f"{stamp}-{uuid.uuid4().hex[:8]}", exist_ok=bool(job_id), repository=url)
        if mode == "hybrid":
            from arktic_office.preparation.hybrid import prepare
            from arktic_office.adapters.invoke import invoke_hermes
            from arktic_office.storage.jsonio import write_json
            snapshot = prepare(url, scanner=None if inspect_only else scan,
                               invoke=None if inspect_only else invoke_hermes,
                               config=profiles["preparation"],
                               emit=lambda state: write_json(output / "preparacion.json", {"mode": "hybrid", "exploration": state}))
            write_json(output / "preparacion.json", snapshot["preparation"])
        else:
            snapshot = collect(url, scanner=None if inspect_only else scan)
        snapshot["analyzed_at"] = datetime.now(timezone.utc).isoformat()
        from arktic_office.config.models import request_options
        snapshot["request"] = request_options()
        snapshot["model_profiles"] = profiles
        snapshot["runtime"] = {"provider": provider, "model": model,
                               "reasoning": options["reasoning_config"]["effort"],
                               "max_output_tokens": options["max_tokens"]}
        (output / "evidencia.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        from arktic_office.storage.manifest import write_manifest
        write_manifest(output, snapshot)
        if inspect_only:
            plan = plan_cells(snapshot)
            routing = [{"id": c["id"], "modelo": c["model"], "razonamiento": c["reasoning"],
                        "archivos": [f["path"] for f in c["files"]], "bytes": c["bytes"]} for c in plan]
            (output / "distribucion.json").write_text(json.dumps(routing, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Solo lectura verificada: {len(snapshot['files'])} archivos, {snapshot['branch']}@{snapshot['commit']}. Evidencia: {output}. Sin llamada al modelo.")
            return
        print(f"Revisando {len(snapshot['files'])} archivos de {snapshot['branch']}@{snapshot['commit']} con Hermes Agent...", flush=True)
        data = run_team(snapshot, output)
        write_manifest(output, snapshot, data)
        model = provider + "/" + model
        (output / "informe.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        (output / "informe.md").write_text(markdown(data, snapshot, model), encoding="utf-8")
        if data.get("schema_version") == 3:
            from arktic_office.reporting.executive import render_html
            (output / "informe.html").write_text(render_html(data, snapshot, model), encoding="utf-8")
        print(f"Informe listo: {output}/informe.md")
        if data["estado"] != "completo" and any(c["estado"] == "error" for c in data.get("celulas", [])):
            raise AuditError("Se guardó un informe " + data["estado"] + "; revisar las células pendientes. No equivale a una revisión completa del equipo.")


def main():
    parser = argparse.ArgumentParser(description="Revisión acotada de la rama predeterminada con Hermes Agent")
    parser.add_argument("repository", help="https://github.com/propietario/repositorio")
    parser.add_argument("--inspect-only", action="store_true", help="Verificar lectura sin invocar el modelo")
    parser.add_argument("--job-id", type=parse_job_id, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        run(args.repository, args.inspect_only, args.job_id)
    except AuditError as exc:
        if args.job_id:
            try:
                destination = RunStore(reports_root()).resolve(args.job_id)
            except FileNotFoundError:
                destination = None
            if destination is not None:
                (destination / "error.json").write_text(json.dumps({"error": str(exc)}, ensure_ascii=False), encoding="utf-8")
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
