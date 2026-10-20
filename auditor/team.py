"""Fixed, sequential three-cell workflow. Coordination never calls a model."""
import json
import os
import re
import subprocess
import sys
from pathlib import PurePosixPath

from repository import AuditError, MANIFESTS, SOURCE_EXT
from reporting import evidence_index, make_prompt, validate_report
from settings import settings, runtime_options

CELLS = (
    {"id": "security", "name": "Seguridad", "focus": "Prioriza acceso a datos, autenticación, exposición y configuraciones inseguras evidentes. Gobernanza y responsables desconocidos quedan como dudas. No afirmes CVE sin prueba ni reproduzcas secretos."},
    {"id": "architecture", "name": "Arquitectura y migración", "focus": "Prioriza arranque, persistencia/recuperación de datos, estabilidad y conexiones. Configuración de recursos no demuestra consumo real. Explica implicaciones para operar o migrar, sin elegir destino ni suponer infraestructura."},
    {"id": "inventory", "name": "Inventario tecnológico", "focus": "Identifica componentes principales con tecnología, versiones declaradas y función evidenciada. No enumeres todos los paquetes. Incluye propósito solo si está documentado. Distingue declaración de uso real; no evalúes seguridad ni elijas infraestructura."},
)


def cell_config(cell):
    provider, model = settings()
    options = runtime_options()
    prefix = "AUDIT_" + cell["id"].upper()
    model = os.environ.get(prefix + "_MODEL", "").strip() or model
    effort = os.environ.get(prefix + "_REASONING", "").strip() or options["reasoning_config"]["effort"]
    if effort not in {"low", "medium", "high"}:
        raise AuditError(prefix + "_REASONING debe ser low, medium o high.")
    return {"provider": provider, "model": model, "reasoning": effort}


def relevance(cell_id, file):
    p = PurePosixPath(file["path"])
    name = p.name.lower()
    docker = name.startswith("dockerfile") or "compose" in name
    manifest = p.name in MANIFESTS
    readme = name.startswith("readme")
    config = p.suffix in {".yaml", ".yml", ".toml", ".xml", ".properties"} or "config" in name
    if cell_id == "inventory":
        return 0 if manifest else 1 if docker else 2 if readme else None
    if cell_id == "architecture":
        if docker or readme:
            return 0
        if p.name in {"index.js", "index.ts", "main.py", "app.py", "server.js", "server.ts", "main.go", "Program.cs", "Application.java"}:
            return 1
        return 2 if manifest or config else None
    if any(word in name for word in ("auth", "access", "security", "middleware", "network")):
        return 0
    if docker or config:
        return 1
    if manifest:
        return 2
    return 3 if p.suffix in SOURCE_EXT else None


def plan_cells(snapshot):
    """Per-cell byte/file caps are fixed MVP limits, within the global selection."""
    plan = []
    for cell in CELLS:
        candidates = [(relevance(cell["id"], file), i, file) for i, file in enumerate(snapshot["files"])]
        candidates = sorted((x for x in candidates if x[0] is not None), key=lambda x: (x[0], x[1]))
        selected, size = [], 0
        for _, _, file in candidates:
            length = len(file["text"].encode("utf-8"))
            if len(selected) >= 6 or size + length > 24000:
                continue
            selected.append(file)
            size += length
        plan.append({**cell, **cell_config(cell), "files": selected, "bytes": size})
    return plan


def write_json(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def invoke_hermes(prompt, config):
    env = dict(os.environ, AUDIT_MODEL=config["model"], AUDIT_REASONING=config["reasoning"])
    try:
        result = subprocess.run([sys.executable, "/app/runtime.py"], input=prompt, text=True,
                                capture_output=True, timeout=240, check=False, env=env)
    except subprocess.TimeoutExpired:
        raise AuditError("La célula superó 240 segundos; no se reintentó.") from None
    if result.returncode:
        raise AuditError("Hermes no completó la célula. Revisar sesión, acceso al modelo, límites y conectividad. Sin reintento automático.")
    try:
        envelope = json.loads(result.stdout)
        if not isinstance(envelope, dict) or not isinstance(envelope.get("report"), str):
            raise ValueError()
    except (ValueError, TypeError):
        raise AuditError("El runtime no devolvió una respuesta estructurada válida.") from None
    return envelope


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
                    findings[key] = {**item, "evidencia": list(item["evidencia"]), "celulas": [cell_id], "section": section}
                    continue
                existing = findings[key]
                if cell_id not in existing["celulas"]:
                    existing["celulas"].append(cell_id)
                merge_refs(existing["evidencia"], item["evidencia"])
                for field in ("importancia", "pendiente"):
                    if item.get(field) and item[field] != existing.get(field):
                        existing[field] = (existing.get(field, "") + " " + item[field]).strip()
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
    if any(report.get("schema_version") == 2 for _, report in results):
        output["schema_version"] = 2
    for item in findings.values():
        section = item.pop("section")
        output[section].append(item)
    output["estado"] = "completo" if all(c["estado"] == "completada" for c in cells) else "parcial" if results else "sin_resultados"
    return output


def prepare_response(raw, snapshot):
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        raise AuditError("La célula no devolvió JSON válido.") from None
    if not isinstance(data, dict) or set(data) not in ({"confirmados", "indicios", "dudas"}, {"schema_version", "confirmados", "indicios", "dudas"}):
        raise AuditError("La célula no devolvió las tres secciones esperadas.")
    index = evidence_index(snapshot)
    omitted = {}
    for section, limit in (("confirmados", 2), ("indicios", 1), ("dudas", 2)):
        if not isinstance(data[section], list):
            raise AuditError("Sección de célula inválida.")
        omitted[section] = max(0, len(data[section]) - limit)
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
    return validate_report(json.dumps(data), snapshot, limits={"confirmados": 2, "indicios": 1, "dudas": 2}), omitted


def run_team(snapshot, output, invoke=invoke_hermes, emit=print):
    plan = plan_cells(snapshot)
    cells = [{"id": c["id"], "nombre": c["name"], "estado": "pendiente", "provider": c["provider"],
              "model": c["model"], "reasoning": c["reasoning"], "archivos": [f["path"] for f in c["files"]],
              "bytes": c["bytes"]} for c in plan]
    results = []
    (output / "celulas").mkdir()
    for config, state in zip(plan, cells):
        state["estado"] = "analizando" if config["files"] else "sin_evidencia"
        write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
        if not config["files"]:
            state["error"] = "No hay archivos relevantes seleccionados para esta célula. Ampliar o revisar la selección."
            write_json(output / "celulas" / (config["id"] + ".json"), state)
            continue
        emit(f"Célula {config['name']}: {len(config['files'])} archivos, {config['bytes']} bytes, {config['model']}/{config['reasoning']}...", flush=True)
        subset = {**snapshot, "files": config["files"]}
        prompt = make_prompt(subset, config)
        try:
            envelope = invoke(prompt, config)
            state["usage"] = envelope.get("usage")
            report, omitted = prepare_response(envelope["report"], subset)
            if report.get("schema_version") != 2:
                raise AuditError("La célula no devolvió el formato 2 con implicaciones y pendientes; no se completó esta célula.")
            state["estado"] = "completada"
            state["omitidos_por_limite"] = omitted
            if envelope.get("reused_from"):
                state["reutilizado_de"] = envelope["reused_from"]
            results.append((config["id"], report))
            write_json(output / "celulas" / (config["id"] + ".json"), {**state, "resultado": report})
        except AuditError as exc:
            state["estado"] = "error"
            state["error"] = str(exc)
            emit(f"Célula {config['name']}: error; el informe indicará cobertura parcial.", flush=True)
            write_json(output / "celulas" / (config["id"] + ".json"), state)
        write_json(output / "estado.json", {"estado": "analizando", "celulas": cells})
    data = consolidate(results, cells)
    data["schema_version"] = 2
    write_json(output / "estado.json", {"estado": data["estado"], "celulas": cells})
    return data
