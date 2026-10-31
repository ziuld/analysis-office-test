"""Bounded specialists with shared retrieval, validated routing and synthesis."""
import json
from arktic_office.storage.jsonio import write_json
from arktic_office.adapters.invoke import invoke_hermes
from arktic_office.config.settings import cell_config
import os
import re
import time
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
        candidates = balanced_files([x[2] for x in candidates], roles.get(cell["id"], roles["security"]))
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
    output["recepcion"] = "sin_revision_automatica"
    names = {c['id']:c.get('nombre',c['id']) for c in cells}
    output['aportaciones_agentes'] = [{'id':role,'nombre':names.get(role,role),'respuesta':report['respuesta_original']}
                                    for role,report in results if 'respuesta_original' in report]
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
        controls = [c for _, report in results for c in report.get("controles", [])]
        # Preserve every specialist's contribution and disagreement, never overwrite a finding
        # with a later placeholder from another security profile.
        found = {}
        for control in controls:
            previous = found.get(control['id'])
            if previous is None or previous['estado'] == 'no_evaluado':
                found[control['id']] = {**control, 'evidencia': list(control['evidencia'])}
            elif control['estado'] != 'no_evaluado':
                previous['motivo'] = (previous['motivo'] + ' / ' + control['motivo'])[:1200]
                merge_refs(previous['evidencia'], control['evidencia'])
                if control['estado'] != previous['estado']:
                    previous['estado'] = 'hallazgo' if 'hallazgo' in {previous['estado'], control['estado']} else 'no_evaluado'
        output.update(schema_version=3, controles=[found.get(key, {"id": key, "estado": "no_evaluado", "motivo": "La célula no aportó una evaluación válida de este control.", "evidencia": []}) for key in CONTROLS])
    if "schema_version" not in output and any(report.get("schema_version") == 2 for _, report in results):
        output["schema_version"] = 2
    for item in findings.values():
        section = item.pop("section")
        output[section].append(item)
    from arktic_office.core.outcome import INSUFFICIENT, useful
    output["estado"] = (INSUFFICIENT if not useful(output) and cells and all(c["estado"] in {INSUFFICIENT, "sin_evidencia", "no_ejecutado"} for c in cells)
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
    try:
        compact = json.loads(raw)
    except (ValueError, TypeError):
        compact = None
    if isinstance(compact, dict) and "observaciones" in compact:
        from arktic_office.reporting.specialist import compose
        return compose(raw, snapshot, cell_id)
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


def prepare_partial_response(raw, snapshot, cell_id):
    """Retain independently valid findings; malformed envelopes still fail closed."""
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return prepare_cell_response(raw, snapshot, cell_id)
    if isinstance(data, dict) and "observaciones" in data:
        from arktic_office.reporting.specialist import compose
        return compose(raw, snapshot, cell_id)
    if not isinstance(data, dict) or data.get("schema_version") != 3:
        return prepare_cell_response(raw, snapshot, cell_id)
    if any(not isinstance(data.get(k), list) for k in ("confirmados", "indicios", "dudas", "controles")):
        return prepare_cell_response(raw, snapshot, cell_id)
    from copy import deepcopy
    from arktic_office.reporting.security import CONTROLS
    base = deepcopy(data)
    base.update(confirmados=[], indicios=[], controles=[])
    # Validate envelope, editorial ownership and optional content independently first.
    clean, omitted, warnings = prepare_cell_response(json.dumps(base), snapshot, cell_id)
    # Presentation is already validated independently; do not reject it again for every item.
    for field in ("presentacion", "propuesta_azure"):
        base.pop(field, None)
    for section in ("confirmados", "indicios"):
        limit = 12 if section == "confirmados" else 8
        for i, item in enumerate(data[section]):
            if i >= limit:
                warnings.append(f"{section}[{i}] rechazado: límite de hallazgos.")
                continue
            try:
                if not isinstance(item, dict) or not isinstance(item.get("evidencia"), list):
                    raise AuditError("Hallazgo sin referencias estructuradas.")
                for ref in item["evidencia"]:
                    prepare_response(json.dumps({"schema_version": 3, "confirmados": [], "indicios": [], "dudas": [], "controles": [], section: [{**item, "evidencia": [ref]}]}), snapshot)
                candidate = {**base, section: [item]}
                report, _, extra = prepare_cell_response(json.dumps(candidate), snapshot, cell_id)
                accepted = report[section][0]
                if accepted.get("severidad") != "informativa" and not {"titulo", "resultado_esperado", "detalle_tecnico"} <= set(accepted):
                    raise AuditError("Riesgo sin detalle editorial obligatorio.")
                clean[section].append(accepted)
                warnings.extend(extra)
            except AuditError as exc:
                warnings.append(f"{section}[{i}] rechazado: {exc}")
    for i, control in enumerate(data["controles"]):
        try:
            report, _, _ = prepare_cell_response(json.dumps({**base, "controles": [control]}), snapshot, cell_id)
            if any(c["id"] == report["controles"][0]["id"] for c in clean["controles"]):
                raise AuditError("Control duplicado.")
            clean["controles"].extend(report["controles"])
        except AuditError as exc:
            warnings.append(f"control[{i}] rechazado: {exc}")
    if cell_id == "security":
        for key in CONTROLS:
            if not any(c["id"] == key for c in clean["controles"]):
                clean["controles"].append({"id": key, "estado": "no_evaluado", "motivo": "Control ausente o rechazado; no demuestra ausencia de riesgo.", "evidencia": []})
                warnings.append("Control no evaluado: " + key)
    return clean, omitted, warnings


def run_team(snapshot, output, invoke=invoke_hermes, emit=print, evidence=None):
    from arktic_office.config.models import validate_configuration, request_options
    validate_configuration()
    snapshot = {**snapshot, "request": snapshot.get("request", request_options())}
    from arktic_office.execution.budget import Budget
    from arktic_office.storage.knowledge import Knowledge
    from arktic_office.config.settings import reports_root
    budget = Budget(invoke, output)
    invoke = budget
    root = reports_root()
    knowledge = Knowledge(root if output.resolve().is_relative_to(root.resolve()) else output.parent)
    knowledge.begin(output.name, snapshot)
    if evidence:
        evidence.knowledge = knowledge
        evidence.run_id = output.name
    plan = plan_cells(snapshot)
    coordinator = None
    if snapshot["request"]["mode"] == "ai":
        from arktic_office.coordination.coordinator import Coordinator
        coordinator = Coordinator(snapshot, output, invoke, evidence=evidence)
        coordinator.knowledge = knowledge
        plan = coordinator.route(plan)
    if evidence:
        plan = [{**c, "files": [], "bytes": 0} for c in plan]
    cells = [{"id": c["id"], "nombre": c["name"], "estado": "pendiente", "provider": c["provider"],
              "model": c["model"], "reasoning": c["reasoning"], "archivos": [f["path"] for f in c["files"]],
              "bytes": c["bytes"], "calls": 0} for c in plan]
    results = []
    (output / "celulas").mkdir()
    for config, state in zip(plan, cells):
        from arktic_office.reporting.questionnaire import catalog
        knowledge.export(output, config, state)
        if budget.stop_reason:
            state.update(estado='bloqueado', execution='blocked', error=budget.stop_reason,
                         necesita=['Comprobar proveedor, acceso y presupuesto; no se reanuda automáticamente.'])
            knowledge.export(output, config, state)
            write_json(output / 'celulas' / (config['id'] + '.json'), state)
            continue
        missing_dependencies = [dep for dep in config.get('dependencies', []) if not any(r == dep for r, _ in results)]
        if missing_dependencies:
            state.update(estado='bloqueado', execution='blocked', error='Faltan aportaciones necesarias: ' + ', '.join(missing_dependencies))
            knowledge.export(output, config, state)
            continue
        # Discovery only: full contributions are retrieved explicitly through Core.
        config['knowledge_index'] = knowledge.index(output.name)
        started = time.monotonic()
        state["estado"] = "analizando" if config["files"] or evidence else "informacion_insuficiente"
        write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
        if not config["files"] and not evidence:
            state["mensaje"] = "La selección no incluye código suficiente para esta especialidad. Hace falta ampliar la lectura."
            state["necesita"] = ["Archivos de código y configuración relevantes para " + config["name"] + "."]
            write_json(output / "celulas" / (config["id"] + ".json"), state)
            continue
        emit(f"Célula {config['name']}: {len(config['files'])} archivos, {config['bytes']} bytes, {config['model']}/{config['reasoning']}...", flush=True)
        if evidence:
            state.update(execution="running", coverage="partial", decision=config.get("decision", "execute"),
                         reason=config.get("task", config["focus"]), missing=config.get("missing", []), considered=config.get("considered", []), retrievals=[])
        subset = {**snapshot, "files": config["files"]}
        knowledge.export(output, config, state)
        raw = None
        try:
            if evidence:
                from arktic_office.coordination.research import research
                envelope = research(snapshot, config, state, evidence, invoke, output, cells)
                subset["files"] = config["files"]
            else:
                state["calls"] = 1
                write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
                envelope = invoke(make_prompt(subset, config), config)
                state["usage"] = envelope.get("usage")
            raw = envelope["report"]
            original_raw = raw
            (output / "celulas" / (config["id"] + ".respuesta-original.txt")).write_text(raw, encoding="utf-8")
            if isinstance(raw, str) and "\"observaciones\"" in raw:
                state["contrato_salida"] = "compact-v1"
            if config["id"] == "architecture" and "azure" not in config["capabilities"]:
                try:
                    payload = json.loads(raw)
                    if isinstance(payload, dict):
                        payload.pop("propuesta_azure", None)
                        raw = json.dumps(payload)
                except (ValueError, TypeError):
                    pass  # Existing response validator produces the technical error.
            from arktic_office.reporting.specialist import compose
            report, omitted, warnings = compose(raw, subset, config["id"])
            report["respuesta_original"] = json.loads(original_raw)
            from arktic_office.reporting.questionnaire import enabled, complete
            if enabled(snapshot) and (not report.get("respuestas") or not complete(report.get("respuestas", []))):
                warnings.append("Hay preguntas pendientes o respondidas parcialmente; revisar el cuestionario.")
            if evidence:
                warnings.extend("Consulta no completada: " + q["result"]["error"] for q in state["retrievals"] if q["result"].get("error"))
            proposal_error = None
            if warnings:
                from arktic_office.preparation.repository import redact
                # Diagnostics only, never rendered or reused as validated evidence.
                (output / "celulas" / (config["id"] + ".respuesta-parcial.txt")).write_text(redact(raw), encoding="utf-8")
                state["advertencias"] = warnings
            from arktic_office.core.outcome import INSUFFICIENT, useful
            insufficient = report.get("evaluacion", {}).get("estado") == INSUFFICIENT or not useful(report)
            state["estado"] = INSUFFICIENT if not useful(report) else "parcial" if proposal_error or insufficient else "completada"
            if insufficient:
                state["mensaje"] = report.get("evaluacion", {}).get("motivo", "La información recibida no permite elaborar una evaluación útil de esta especialidad.")
                state["necesita"] = report.get("evaluacion", {}).get("necesita", report["dudas"])
            if proposal_error and useful(report):
                state["mensaje"] = (state.get("mensaje", "") + " " + proposal_error).strip()
            if evidence:
                state["execution"] = "completed"
                state["coverage"] = "insufficient" if insufficient else "partial" if warnings or config.get("missing") or any(c["estado"] == "no_evaluado" for c in report.get("controles", [])) else "available_evidence"
            state["omitidos_por_limite"] = omitted
            if envelope.get("reused_from"):
                state["reutilizado_de"] = envelope["reused_from"]
            results.append((config["id"], report))
            state['summary'] = next((a['respuesta'] for a in report.get('respuestas', []) if a['estado'] in {'respondida', 'parcial'}), 'Aportación guardada; consultar cobertura.')[:240]
            knowledge.export(output, config, state, report)
            write_json(output / "celulas" / (config["id"] + ".json"), {**state, "resultado": report})
        except AuditError as exc:
            if isinstance(raw, str):
                # Diagnostic only: never rendered or reused as a validated contribution.
                from arktic_office.preparation.repository import redact
                (output / "celulas" / (config["id"] + ".respuesta-rechazada.txt")).write_text(redact(raw), encoding="utf-8")
            state["estado"] = "error"
            if evidence:
                state.update(execution="error", coverage="incomplete")
            state["error"] = str(exc)
            emit(f"Célula {config['name']}: error; el informe indicará cobertura parcial.", flush=True)
            write_json(output / "celulas" / (config["id"] + ".json"), state)
        state['duration_seconds'] = round(time.monotonic() - started, 3)
        state['tokens_available'] = max(0, budget.limits['output_tokens'] - budget.charged_output_tokens())
        knowledge.export(output, config, state, next((r for a, r in results if a == config['id']), None))
        saved_result = next((r for a, r in results if a == config['id']), None)
        write_json(output / 'celulas' / (config['id'] + '.json'), {**state, **({'resultado': saved_result} if saved_result is not None else {})})
        write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
    data = consolidate(results, cells)
    if coordinator and not budget.stop_reason:
        write_json(output / 'meeting.json', {'active': True, 'run_id': output.name, 'participants': ['coordinator', *[a for a, _ in results]], 'phase': 'synthesis'})
        data["sintesis"] = coordinator.synthesize(results)
        data["coordination"] = coordinator.state
        if data["estado"] == "completo" and (coordinator.state.get("routing_fallback") or any(s["status"] == "error" for s in coordinator.state["stages"].values())):
            data["estado"] = "parcial"
    from arktic_office.reporting.questionnaire import enabled, catalog, VERSION, complete
    if enabled(snapshot):
        received = {a["id"]: a for _, report in results for a in report.get("respuestas", [])}
        if coordinator:
            received.update({a["id"]: a for a in coordinator.state.get("question_answers", [])})
        answers = [received.get(q["id"], {**q, "estado": "no_comprobado", "respuesta": "El responsable no entregó una respuesta para esta pregunta.",
            "evidencia": [], "herramientas": [], "pendiente": "Completar la revisión de esta pregunta; consultar el estado del agente responsable."}) for q in catalog()]
        data["cuestionario"] = {"version": VERSION, "respuestas": answers}
        if not complete(answers):
            data["estado"] = "parcial"
    from arktic_office.reporting.security import CONTROLS
    data["schema_version"] = 3
    data.setdefault("controles", [{"id": key, "estado": "no_evaluado", "motivo": "Seguridad no completó su evaluación.", "evidencia": []} for key in CONTROLS])
    data["scanners"] = snapshot.get("scanners", [])
    preparation = snapshot.get("preparation")
    if preparation:
        data["preparation"] = preparation
        if data["estado"] == "completo" and preparation.get("mode") != "complete" and preparation["exploration"]["closure"] != "sufficient":
            data["estado"] = "parcial"
    if evidence:
        data["coverage"] = {"snapshot": "complete", "semantic": "partial", "cells": {c["id"]: c.get("coverage", "insufficient") for c in cells}, "limitation": "Ejecución terminada no demuestra exhaustividad semántica; consultar inventario y controles no evaluados."}
    from arktic_office.core.outcome import notice
    data["mensaje"], data["necesita"], _ = notice(data)
    budget.save()
    data['metrics'] = __import__('json').loads((output / 'metrics.json').read_text(encoding='utf-8'))
    data['stop_reason'] = budget.stop_reason
    write_json(output / "estado.json", {"estado": data["estado"], "celulas": cells})
    return data

