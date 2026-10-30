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


def run(url, inspect_only=False, job_id=None, *, local_snapshot=None):
    from arktic_office.config.models import validate_configuration, scanners_enabled
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
    from contextlib import ExitStack
    with ExitStack() as lifetime, (reports / ".audit.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AuditError("Ya existe una revisión activa; espera a que termine.") from None
        from arktic_office.preparation.snapshot import snapshot_workspace
        workspace = lifetime.enter_context(snapshot_workspace())
        from arktic_office.adapters.scanners import scan
        scanner = scan if not inspect_only and scanners_enabled() else None
        mode = os.environ.get("AUDIT_PREPARATION_MODE", "hybrid")
        if local_snapshot is not None:
            if url:
                raise AuditError('Usar una URL o --local-snapshot, no ambas.')
            mode = 'hybrid'
            url = 'local:///snapshot'
        if mode not in {"legacy", "hybrid"}:
            raise AuditError("AUDIT_PREPARATION_MODE debe ser legacy o hybrid.")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        import uuid
        output = RunStore(reports).create(job_id or f"{stamp}-{uuid.uuid4().hex[:8]}", exist_ok=bool(job_id), repository=url)
        if scanner is not None:
            from functools import partial
            from arktic_office.adapters.scanners import run as scanner_run
            scanner = partial(scan, runner=partial(scanner_run, capture=output/'herramientas'))
        evidence = None
        if mode == "hybrid":
            from arktic_office.preparation.evidence import prepare_complete
            from arktic_office.storage.jsonio import write_json
            write_json(output / "preparacion.json", {"mode": "complete", "status": "running"})
            from arktic_office.preparation.hybrid import indexer_signature
            snapshot, evidence = prepare_complete(url, Path(workspace), scanner=scanner, local_snapshot=local_snapshot,
                artifact_directory=output/'herramientas', cache_root=reports/'.preparation-cache',
                indexer_signature=indexer_signature(), refresh=os.environ.get('AUDIT_PREPARATION_REFRESH') == '1')
            write_json(output / "preparacion.json", snapshot["preparation"])
        else:
            snapshot = collect(url, scanner=scanner)
        snapshot["analyzed_at"] = datetime.now(timezone.utc).isoformat()
        from arktic_office.config.models import request_options
        snapshot["request"] = request_options()
        from arktic_office.reporting.questionnaire import VERSION
        from arktic_office.reporting.deterministic import results
        snapshot["questionnaire_version"] = VERSION
        deterministic = results(snapshot, evidence.graph if evidence else None, output / "herramientas")
        # Full outputs are persisted separately; the polling snapshot stays small.
        from arktic_office.storage.jsonio import write_json
        (output / "herramientas").mkdir(exist_ok=True)
        write_json(output / "herramientas" / "resultados-deterministas.json", deterministic)
        snapshot["deterministic_results"] = {**deterministic, "tools": [
            {**t, "result": {k: v for k, v in t["result"].items() if k not in {"nodes", "edges", "original_output_redacted"}}} for t in deterministic["tools"]]}
        if evidence:
            evidence.deterministic = deterministic
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
        data = run_team(snapshot, output, evidence=evidence)
        data["deterministic_results"] = deterministic
        if evidence:
            snapshot["coverage"]["retained_paths"] = [f["path"] for f in snapshot["files"]]
            snapshot["coverage"]["retained_bytes"] = sum(len(f["text"].encode()) for f in snapshot["files"])
        (output / "evidencia.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
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
    parser = argparse.ArgumentParser(description="Revisión de GitHub o de un snapshot de la rama local activa")
    parser.add_argument("repository", nargs='?', help="https://github.com/propietario/repositorio")
    parser.add_argument('--local-snapshot', help='Bundle local generado por scripts/analyze-local.ps1')
    parser.add_argument("--inspect-only", action="store_true", help="Verificar lectura sin invocar el modelo")
    parser.add_argument("--job-id", type=parse_job_id, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if bool(args.repository) == bool(args.local_snapshot):
        parser.error('Indicar una URL o --local-snapshot.')
    try:
        run(args.repository, args.inspect_only, args.job_id, local_snapshot=args.local_snapshot)
    except AuditError as exc:
        if args.job_id:
            try:
                destination = RunStore(reports_root()).resolve(args.job_id)
            except FileNotFoundError:
                destination = None
            if destination is not None:
                from arktic_office.storage.jsonio import read_json, write_json
                preparation = read_json(destination / "preparacion.json", {})
                if preparation.get("status") == "running":
                    write_json(destination / "preparacion.json", {**preparation, "status": "error", "reason": str(exc)})
                (destination / "error.json").write_text(json.dumps({"error": str(exc)}, ensure_ascii=False), encoding="utf-8")
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
