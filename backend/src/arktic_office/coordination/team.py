"""Single-pass specialists with optional, bounded AI routing and synthesis."""
import json
from arktic_office.storage.jsonio import write_json
from arktic_office.adapters.invoke import invoke_hermes
from arktic_office.config.settings import cell_config
import os
import re
from pathlib import PurePosixPath

from arktic_office.preparation.repository import AuditError, MANIFESTS, SOURCE_EXT, LOCKFILES, file_role, balanced_files
from arktic_office.reporting.reports import evidence_index, make_prompt, validate_report
from arktic_office.config.settings import settings, runtime_options

from arktic_office.resources.paths import resource_path
CELLS = tuple(json.loads(resource_path("profiles", "agents.json").read_text(encoding="utf-8")))




def relevance(cell_id, file):
    p = PurePosixPath(file["path"])
    name = p.name.lower()
    if p.name in LOCKFILES:
        return None  # Full lockfiles go to OSV, not to the language model.
    docker = name.startswith("dockerfile") or name in {"compose.yaml", "compose.yml", "docker-compose.yml", "docker-compose.yaml"}
    manifest = p.name in MANIFESTS
    readme = name.startswith("readme")
    config = p.suffix in {".yaml", ".yml", ".toml", ".xml", ".properties"} or "config" in name
    if cell_id == "inventory":
        return 0 if manifest else 1 if docker else 2 if readme else 3 if file_role(file["path"]) in {"entry", "data", "routes", "business"} else None
    if cell_id == "architecture":
        if docker or readme:
            return 0
        if p.name in {"index.js", "index.ts", "main.py", "app.py", "server.js", "server.ts", "main.go", "Program.cs", "Application.java"}:
            return 1
        return 2 if manifest or config or file_role(file["path"]) in {"entry", "data", "routes", "business", "config"} else None
    if any(word in file["path"].lower() for word in ("auth", "access", "security", "middleware", "network", "controller", "route", "service", "repository")):
        return 0
    if docker or config:
        return 1
    if manifest:
        return 2
    return 3 if p.suffix in SOURCE_EXT else None


def plan_cells(snapshot):
    """Per-cell byte/file caps are fixed MVP limits, within the global selection."""
    plan = []
    from arktic_office.config.models import request_options
    capabilities = snapshot.get("request", request_options())["capabilities"]
    for cell in CELLS:
        config = cell_config(cell)
        candidates = [(relevance(cell["id"], file), i, file) for i, file in enumerate(snapshot["files"])]
        candidates = sorted((x for x in candidates if x[0] is not None), key=lambda x: (x[0], x[1]))
        # Two manifest slots cover backend/frontend dependency declarations.
        roles = {"security": ("security", "routes", "business", "config", "manifest", "manifest", "deployment", "data", "entry", "source", "readme"),
                 "architecture": ("deployment", "entry", "data", "manifest", "manifest", "routes", "config", "business", "source", "readme"),
                 "inventory": ("manifest", "manifest", "deployment", "entry", "data", "routes", "business", "readme")}
        candidates = balanced_files([x[2] for x in candidates], roles[cell["id"]])
        selected, size = [], 0
        for file in candidates:
            length = len(file["text"].encode("utf-8"))
            if len(selected) >= config["limits"]["files"] or size + length > config["limits"]["bytes"]:
                continue
            selected.append(file)
            size += length
        plan.append({**cell, **config, "files": selected, "bytes": size, "capabilities": capabilities})
    return plan






def normalize(text):
    return re.sub(r"\W+", " ", text.casefold()).strip()


def merge_refs(target, source):
    for ref in source:
        if ref not in target:
            target.append(ref)


def consolidate(results, cells):
    findings, questions = {}, {}
    for cell_id, report in results:
        for section in ("confirmados", "indicios"):
            for item in report[section]:
                key = normalize(item["observacion"])
                if key not in findings:
                    findings[key] = {**item, "evidencia": list(item["evidencia"]), "celulas": [cell_id], "section": section, "aportaciones": [{"celula": cell_id, "resultado": item}]}
                    continue
                existing = findings[key]
                existing["aportaciones"].append({"celula": cell_id, "resultado": item})
                if cell_id not in existing["celulas"]:
                    existing["celulas"].append(cell_id)
                merge_refs(existing["evidencia"], item["evidencia"])
                for field in ("importancia", "pendiente", "accion", "condiciones"):
                    if item.get(field) and item[field] != existing.get(field):
                        existing[field] = (existing.get(field, "") + " " + item[field]).strip()
                if item.get("severidad") and existing.get("severidad"):
                    from arktic_office.reporting.security import SEVERITIES
                    existing["severidad"] = min((existing["severidad"], item["severidad"]), key=SEVERITIES.index)
                if existing["section"] != section:
                    existing["section"] = "indicios"
                    existing["por_confirmar"] = "Las células discrepan sobre la certeza de esta observación; debe revisarla el arquitecto."
                elif section == "indicios" and item["por_confirmar"] != existing["por_confirmar"]:
                    existing["por_confirmar"] += " " + item["por_confirmar"]
        for question in report["dudas"]:
            key = normalize(question)
            if key not in questions:
                questions[key] = {"pregunta": question, "celulas": []}
            if cell_id not in questions[key]["celulas"]:
                questions[key]["celulas"].append(cell_id)
    output = {"confirmados": [], "indicios": [], "dudas": list(questions.values()), "celulas": cells}
    presentation = {}
    allowed = {"inventory": {"resumen"}, "architecture": {"flujo_actual", "estado_operativo", "decision"}, "security": set()}
    for cell_id, report in results:
        for key, value in report.get("presentacion", {}).items():
            if key in allowed.get(cell_id, set()):
                presentation[key] = value
    if presentation:
        output["presentacion"] = presentation
    from arktic_office.reporting.editorial import metadata
    output["estandar_editorial"] = metadata()
    for cell_id, report in results:
        if cell_id == "architecture" and "propuesta_azure" in report:
            output["propuesta_azure"] = report["propuesta_azure"]
    if any(report.get("schema_version") == 3 for _, report in results):
        from arktic_office.reporting.security import CONTROLS
        controls = next((report.get("controles", []) for cell_id, report in results if cell_id == "security"), [])
        found = {c["id"]: c for c in controls}
        output.update(schema_version=3, controles=[found.get(key, {"id": key, "estado": "no_evaluado", "motivo": "La célula no aportó una evaluación válida de este control.", "evidencia": []}) for key in CONTROLS])
    if "schema_version" not in output and any(report.get("schema_version") == 2 for _, report in results):
        output["schema_version"] = 2
    for item in findings.values():
        section = item.pop("section")
        output[section].append(item)
    from arktic_office.core.outcome import INSUFFICIENT, useful
    output["estado"] = (INSUFFICIENT if not useful(output) and cells and all(c["estado"] in {INSUFFICIENT, "sin_evidencia"} for c in cells)
                        else "completo" if all(c["estado"] == "completada" for c in cells) else "parcial" if results else "sin_resultados")
    return output


def prepare_response(raw, snapshot):
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        raise AuditError("La célula no devolvió JSON válido.") from None
    base = {"schema_version", "confirmados", "indicios", "dudas", "controles"}
    new_shape = isinstance(data, dict) and data.get("schema_version") == 3 and base <= set(data) <= base | {"propuesta_azure", "presentacion", "evaluacion"}
    if not isinstance(data, dict) or not new_shape and set(data) not in ({"confirmados", "indicios", "dudas"}, {"schema_version", "confirmados", "indicios", "dudas"}):
        raise AuditError("La célula no devolvió las tres secciones esperadas.")
    index = evidence_index(snapshot)
    omitted = {}
    v3 = data.get("schema_version") == 3
    limits = {"confirmados": 12, "indicios": 8, "dudas": 8} if v3 else {"confirmados": 2, "indicios": 1, "dudas": 2}
    for section, limit in limits.items():
        if not isinstance(data[section], list):
            raise AuditError("Sección de célula inválida.")
        omitted[section] = max(0, len(data[section]) - limit)
        if v3 and len(data[section]) > limit:
            raise AuditError("Respuesta excesiva; no se recortan silenciosamente los riesgos.")
        data[section] = data[section][:limit]
        if section == "dudas":
            continue
        for item in data[section]:
            if not isinstance(item, dict) or not isinstance(item.get("evidencia"), list):
                raise AuditError("Hallazgo sin referencias válidas.")
            refs = []
            if not item["evidencia"]:
                raise AuditError("La célula devolvió un hallazgo sin ninguna referencia; no se publica como hecho.")
            omitted["referencias"] = omitted.get("referencias", 0) + max(0, len(item["evidencia"]) - 3)
            for ref in item["evidencia"][:3]:
                if isinstance(ref, str):
                    if ref not in index:
                        raise AuditError("La célula citó un identificador de evidencia inexistente.")
                    refs.append(index[ref])
                else:
                    # Previously validated reports can be rechecked against the same snapshot.
                    refs.append(ref)
            item["evidencia"] = refs
    if v3:
        def resolve_presentation(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "evidencia" and isinstance(child, list):
                        refs = []
                        for ref in child:
                            if isinstance(ref, str):
                                if ref not in index:
                                    raise AuditError("Contenido editorial con fuente inexistente.")
                                ref = index[ref]
                            refs.append(ref)
                        value[key] = refs
                    else:
                        resolve_presentation(child)
            elif isinstance(value, list):
                for child in value:
                    resolve_presentation(child)
        if "presentacion" in data:
            resolve_presentation(data["presentacion"])
        if not isinstance(data.get("controles"), list):
            raise AuditError("Controles inválidos.")
        for control in data["controles"]:
            if not isinstance(control, dict) or not isinstance(control.get("evidencia"), list):
                raise AuditError("Control sin evidencia estructurada.")
            refs = []
            for ref in control["evidencia"]:
                if isinstance(ref, str):
                    if ref not in index:
                        raise AuditError("Control con fuente inexistente.")
                    ref = index[ref]
                refs.append(ref)
            control["evidencia"] = refs
        if "propuesta_azure" in data:
            proposal = data["propuesta_azure"]
            if not isinstance(proposal, dict) or not isinstance(proposal.get("evidencia"), list):
                raise AuditError("Fuentes de propuesta Azure inválidas.")
            refs = []
            for ref in proposal["evidencia"]:
                if isinstance(ref, str):
                    if ref not in index:
                        raise AuditError("La propuesta Azure citó una fuente inexistente.")
                    ref = index[ref]
                refs.append(ref)
            proposal["evidencia"] = refs
    return validate_report(json.dumps(data), snapshot, limits=limits), omitted


def prepare_cell_response(raw, snapshot, cell_id):
    """Optional presentation errors cannot discard an independently valid core."""
    if cell_id != "architecture":
        report, omitted = prepare_response(raw, snapshot)
        return report, omitted, []
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return (*prepare_response(raw, snapshot), [])
    if not isinstance(data, dict):
        return (*prepare_response(raw, snapshot), [])
    proposal = data.pop("propuesta_azure", None)
    presentation = data.pop("presentacion", None)
    report, omitted = prepare_response(json.dumps(data), snapshot)
    warnings = []
    parts = [("propuesta_azure", proposal)] if proposal is not None else []
    if presentation is not None:
        if not isinstance(presentation, dict):
            warnings.append("Presentación rechazada: estructura inválida.")
        else:
            parts.extend(("presentacion", {key: value}) for key, value in presentation.items())
    for field, value in parts:
        try:
            checked, _ = prepare_response(json.dumps({**data, field: value}), snapshot)
            if field == "presentacion":
                report.setdefault(field, {}).update(checked[field])
            else:
                report[field] = checked[field]
        except AuditError as exc:
            warnings.append(("Propuesta Azure" if field == "propuesta_azure" else "Bloque de presentación") + " rechazado: " + str(exc))
    return report, omitted, warnings


def run_team(snapshot, output, invoke=invoke_hermes, emit=print):
    from arktic_office.config.models import validate_configuration, request_options
    validate_configuration()
    snapshot = {**snapshot, "request": snapshot.get("request", request_options())}
    plan = plan_cells(snapshot)
    coordinator = None
    if snapshot["request"]["mode"] == "ai":
        from arktic_office.coordination.coordinator import Coordinator
        coordinator = Coordinator(snapshot, output, invoke)
        plan = coordinator.route(plan)
    cells = [{"id": c["id"], "nombre": c["name"], "estado": "pendiente", "provider": c["provider"],
              "model": c["model"], "reasoning": c["reasoning"], "archivos": [f["path"] for f in c["files"]],
              "bytes": c["bytes"]} for c in plan]
    results = []
    (output / "celulas").mkdir()
    for config, state in zip(plan, cells):
        state["estado"] = "analizando" if config["files"] else "informacion_insuficiente"
        write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
        if not config["files"]:
            state["mensaje"] = "La selección no incluye código suficiente para esta especialidad. Hace falta ampliar la lectura."
            state["necesita"] = ["Archivos de código y configuración relevantes para " + config["name"] + "."]
            write_json(output / "celulas" / (config["id"] + ".json"), state)
            continue
        emit(f"Célula {config['name']}: {len(config['files'])} archivos, {config['bytes']} bytes, {config['model']}/{config['reasoning']}...", flush=True)
        subset = {**snapshot, "files": config["files"]}
        prompt = make_prompt(subset, config)
        raw = None
        try:
            envelope = invoke(prompt, config)
            state["usage"] = envelope.get("usage")
            raw = envelope["report"]
            if config["id"] == "architecture" and "azure" not in config["capabilities"]:
                try:
                    payload = json.loads(raw)
                    if isinstance(payload, dict):
                        payload.pop("propuesta_azure", None)
                        raw = json.dumps(payload)
                except (ValueError, TypeError):
                    pass  # Existing response validator produces the technical error.
            report, omitted, warnings = prepare_cell_response(raw, subset, config["id"])
            proposal_error = "Algunos apartados no superaron la validación; se conservan las aportaciones válidas. No se reintentó." if warnings else None
            if warnings:
                state["advertencias"] = warnings
            for item in report["confirmados"] + report["indicios"]:
                if item.get("severidad") != "informativa" and not {"titulo", "resultado_esperado", "detalle_tecnico"} <= set(item):
                    raise AuditError("La célula no aportó título comprensible, objetivo y detalle técnico para un riesgo nuevo.")
            owned = {"inventory": {"resumen"}, "architecture": {"flujo_actual", "estado_operativo", "decision"}, "security": set()}
            if not set(report.get("presentacion", {})) <= owned[config["id"]]:
                raise AuditError("La célula devolvió bloques editoriales de otra especialidad.")
            if report.get("schema_version") != 3:
                raise AuditError("La célula no devolvió el formato 3 con severidad y cobertura; no se completó esta célula.")
            if config["id"] == "architecture" and "azure" in config["capabilities"] and "propuesta_azure" not in report:
                proposal_error = proposal_error or "Arquitectura no aportó una propuesta Azure; se conservan sus resultados válidos."
            if config["id"] != "architecture" and "propuesta_azure" in report:
                raise AuditError("Solo Arquitectura puede generar la propuesta Azure.")
            if config["id"] == "security":
                from arktic_office.reporting.security import CONTROLS
                if not report["controles"] and report.get("evaluacion", {}).get("estado") == "informacion_insuficiente":
                    report["controles"] = [{"id": key, "estado": "no_evaluado", "motivo": report["evaluacion"]["motivo"], "evidencia": []} for key in CONTROLS]
                if {c["id"] for c in report["controles"]} != set(CONTROLS):
                    raise AuditError("Seguridad no informó los seis controles.")
            from arktic_office.core.outcome import INSUFFICIENT, useful
            insufficient = report.get("evaluacion", {}).get("estado") == INSUFFICIENT or not useful(report)
            state["estado"] = INSUFFICIENT if not useful(report) else "parcial" if proposal_error or insufficient else "completada"
            if insufficient:
                state["mensaje"] = report.get("evaluacion", {}).get("motivo", "La información recibida no permite elaborar una evaluación útil de esta especialidad.")
                state["necesita"] = report.get("evaluacion", {}).get("necesita", report["dudas"])
            if proposal_error and useful(report):
                state["mensaje"] = (state.get("mensaje", "") + " " + proposal_error).strip()
            state["omitidos_por_limite"] = omitted
            if envelope.get("reused_from"):
                state["reutilizado_de"] = envelope["reused_from"]
            results.append((config["id"], report))
            write_json(output / "celulas" / (config["id"] + ".json"), {**state, "resultado": report})
        except AuditError as exc:
            if isinstance(raw, str):
                # Diagnostic only: never rendered or reused as a validated contribution.
                from arktic_office.preparation.repository import redact
                (output / "celulas" / (config["id"] + ".respuesta-rechazada.txt")).write_text(redact(raw)[:120000], encoding="utf-8")
            state["estado"] = "error"
            state["error"] = str(exc)
            emit(f"Célula {config['name']}: error; el informe indicará cobertura parcial.", flush=True)
            write_json(output / "celulas" / (config["id"] + ".json"), state)
        write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
    data = consolidate(results, cells)
    if coordinator:
        data["sintesis"] = coordinator.synthesize(results)
        data["coordination"] = coordinator.state
        if data["estado"] == "completo" and any(s["status"] == "error" for s in coordinator.state["stages"].values()):
            data["estado"] = "parcial"
    from arktic_office.reporting.security import CONTROLS
    data["schema_version"] = 3
    data.setdefault("controles", [{"id": key, "estado": "no_evaluado", "motivo": "Seguridad no completó su evaluación.", "evidencia": []} for key in CONTROLS])
    data["scanners"] = snapshot.get("scanners", [])
    preparation = snapshot.get("preparation")
    if preparation:
        data["preparation"] = preparation
        if data["estado"] == "completo" and preparation["exploration"]["closure"] != "sufficient":
            data["estado"] = "parcial"
    from arktic_office.core.outcome import notice
    data["mensaje"], data["necesita"], _ = notice(data)
    write_json(output / "estado.json", {"estado": data["estado"], "celulas": cells})
    return data

