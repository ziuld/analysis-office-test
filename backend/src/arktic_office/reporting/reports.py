from arktic_office.resources.paths import resource_path
import json

from arktic_office.preparation.repository import AuditError, redact

HERMES_COMMIT = "ce28ca328d3b85ac8663e602136eb69b027cd056"
TOPICS = {"proposito", "componentes", "arranque", "datos", "recuperacion", "estabilidad", "recursos", "servicios", "acceso", "responsabilidades"}


def evidence_index(snapshot):
    return {f"F{n}:L{i}": {"path": file["path"], "line": i, "quote": text}
            for n, file in enumerate(snapshot["files"], 1)
            for i, text in enumerate(file["text"].splitlines(), 1)}


def make_prompt(snapshot, cell=None):
    from arktic_office.reporting.editorial import instructions as editorial_instructions, contract as editorial_contract
    editorial = editorial_instructions(cell["id"] if cell else None) + editorial_contract(cell["id"] if cell else None)
    evidence = [{"id": f"F{n}", "path": f["path"], "partial": f.get("partial", False), "content": "\n".join(f"L{i} | {line}" for i, line in enumerate(f["text"].splitlines(), 1) if line.strip())} for n, f in enumerate(snapshot["files"], 1)]
    focus = (f"Célula: {cell['name']}. {cell['focus']}\n"
             "Límite de respuesta: 8 confirmados, 5 indicios y 6 dudas; prioriza riesgos relevantes, sin rellenar cupos.\n") if cell else ""
    from arktic_office.reporting.security import instructions
    profile = instructions() if cell and cell["id"] == "security" else ""
    if cell and cell["id"] == "architecture":
        if "azure" in cell.get("capabilities", []):
            from arktic_office.reporting.azure_proposal import instructions as azure_instructions
            profile = azure_instructions()
        else:
            import re
            editorial = re.sub(r"Azure:.*?(?=\n\n|$)", "", editorial, flags=re.S)
            profile = "El encargo no solicita Azure: omite propuesta_azure y recomendaciones de despliegue en Azure.\n"
    contract = resource_path("profiles", "report-contract.md").read_text(encoding="utf-8")
    request = resource_path("profiles", "review-request.md").read_text(encoding="utf-8")
    if cell:
        profile += resource_path("skills", "arktic-review", "SKILL.md").read_text(encoding="utf-8")
        if "azure" not in cell.get("capabilities", []):
            contract = "\n".join(line for line in contract.split("\n") if "Para Azure" not in line)
            request = "\n".join(line for line in request.split("\n") if not line.startswith("Solo Arquitectura añade propuesta_azure"))
    final_contract = "\nFIN DE LOS ARCHIVOS.\n" + resource_path("profiles", "cell-output-contract.md").read_text(encoding="utf-8") if cell else ""
    return editorial + "\n" + profile + "\n" + contract + focus + f"Rama revisada: {snapshot.get('branch', 'main')}.\n" + request + json.dumps(evidence, ensure_ascii=False, separators=(",", ":")) + final_contract


def validate_report(raw, snapshot, limits=None):
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        raise AuditError("Hermes no devolvió el JSON esperado; no se publica un informe válido.") from None
    if not isinstance(data, dict):
        raise AuditError("Respuesta de célula inválida.")
    if data.get("schema_version") == 3:
        from arktic_office.reporting.security import validate_v3
        return validate_v3(data, snapshot, limits, validate_report)
    version2 = "schema_version" in data
    if set(data) != ({"confirmados", "indicios", "dudas", "schema_version"} if version2 else {"confirmados", "indicios", "dudas"}) or version2 and (type(data["schema_version"]) is not int or data["schema_version"] != 2):
        raise AuditError("La respuesta de Hermes no respeta las tres secciones del informe.")
    texts = {f["path"]: f["text"].splitlines() for f in snapshot["files"]}
    for section in ("confirmados", "indicios", "dudas"):
        if not isinstance(data[section], list) or len(data[section]) > (limits or {}).get(section, 5):
            raise AuditError("El informe supera el alcance o tiene un formato inválido.")
        for item in data[section]:
            if section == "dudas":
                if not isinstance(item, str) or not item.strip() or len(item) > 1000:
                    raise AuditError("Pregunta inválida en el informe.")
                continue
            expected = {"observacion", "evidencia"} | ({"por_confirmar"} if section == "indicios" else set())
            if version2:
                expected |= {"tema", "importancia", "pendiente"}
                if isinstance(item, dict) and item.get("tema") == "componentes":
                    expected.add("componente")
            if not isinstance(item, dict) or set(item) != expected:
                raise AuditError("Hallazgo con formato inválido.")
            if version2 and (not isinstance(item["tema"], str) or item["tema"] not in TOPICS):
                raise AuditError("Tema de hallazgo no admitido.")
            for field in expected - {"evidencia", "componente"}:
                limit = 420 if version2 and field == "observacion" else 300 if version2 and field in {"importancia", "pendiente", "por_confirmar"} else 1500
                if not isinstance(item[field], str) or not item[field].strip() or len(item[field]) > limit:
                    raise AuditError("Texto de hallazgo inválido.")
            if "componente" in expected:
                component = item["componente"]
                if not isinstance(component, dict) or set(component) != {"nombre", "tecnologia", "funcion"} or any(not isinstance(v, str) or not v.strip() or len(v) > 180 for v in component.values()):
                    raise AuditError("Componente con formato inválido.")
            refs = item["evidencia"]
            if not isinstance(refs, list) or not 1 <= len(refs) <= 3:
                raise AuditError("Hallazgo sin evidencia válida.")
            for ref in refs:
                if not isinstance(ref, dict) or set(ref) != {"path", "line", "quote"}:
                    raise AuditError("Cita con formato inválido.")
                path, line, quote = ref["path"], ref["line"], ref["quote"]
                if (not isinstance(path, str) or path not in texts or type(line) is not int
                        or not 1 <= line <= len(texts[path]) or not isinstance(quote, str)
                        or not quote.strip() or quote != texts[path][line - 1]
                        or "OCULT" in quote):
                    raise AuditError("Una cita no coincide con un archivo y línea revisados; informe rechazado.")
    # Validation verifies the citation, not whether the model's interpretation is true.
    def sanitize(value):
        if isinstance(value, str):
            return redact(value)
        if isinstance(value, list):
            return [sanitize(x) for x in value]
        if isinstance(value, dict):
            return {k: sanitize(v) for k, v in value.items()}
        return value
    return sanitize(data)


def legacy_markdown(data, snapshot, model):
    lines = ["# Revisión preliminar — equipo de agentes", "", f"Repositorio: {snapshot['repository']}",
             f"Rama: {snapshot.get('branch', 'main')} · Commit: `{snapshot['commit']}`", f"Runtime: Hermes Agent `{HERMES_COMMIT}` · Modelo: {model}",
             "", "Lectura estática parcial. Citas contrastadas con el contenido leído; las conclusiones del modelo requieren revisión humana.",
             "No se ejecutó la aplicación ni se verificó su despliegue. No es una autorización de migración."]
    cells = {c["id"]: c["nombre"] for c in data.get("celulas", [])}
    if snapshot.get("evidence_origin"):
        lines += ["", "Origen de la evidencia: " + snapshot["evidence_origin"]]
    if cells:
        lines += ["", "Estado del informe: **" + data["estado"] + "**", "", "| Célula | Estado | Modelo / razonamiento | Archivos |", "|---|---|---|---|"]
        for c in data["celulas"]:
            lines.append(f"| {c['nombre']} | {c['estado']} | {c['model']} / {c['reasoning']} | {len(c['archivos'])} |")
        for c in data["celulas"]:
            if c.get("error"):
                lines += ["", f"Pendiente — {c['nombre']}: {c['error']}", ""]
    for key, title in (("confirmados", "Confirmado en el repositorio"), ("indicios", "Indicios por confirmar"), ("dudas", "Dudas para el arquitecto")):
        lines += ["", "## " + title, ""]
        if not data[key]:
            lines.append("Sin elementos en esta revisión.")
        for item in data[key]:
            if key == "dudas":
                if isinstance(item, str):
                    lines.append("- " + item)
                else:
                    origin = ", ".join(cells[c] for c in item["celulas"])
                    lines.append(f"- [{origin}] {item['pregunta']}")
                continue
            origin = ", ".join(cells[c] for c in item.get("celulas", []))
            lines.append("- " + (f"[{origin}] " if origin else "") + item["observacion"])
            if key == "indicios":
                lines.append("  Por confirmar: " + item["por_confirmar"])
            for ref in item["evidencia"]:
                lines.append(f"  Evidencia: `{ref['path']}:{ref['line']}` — {ref['quote']}")
    lines += ["", "## Cobertura", "", f"{len(snapshot['files'])} archivos · {snapshot['bytes_read']} bytes antes de ocultar posibles credenciales.",
              "La ocultación es heurística y no garantiza detectar todos los secretos. Los archivos seleccionados se envían a OpenAI.", "", "Archivos revisados:"]
    lines.extend("- " + f["path"] for f in snapshot["files"])
    lines += ["", "Exclusiones:"]
    counts = {}
    for item in snapshot["excluded"]:
        counts[item["reason"]] = counts.get(item["reason"], 0) + 1
    lines.extend(f"- {reason}: {count}" for reason, count in sorted(counts.items()))
    lines += ["", "El detalle de exclusiones está en evidencia.json; los resultados y la cobertura por célula están en celulas/.",
              "La consolidación elimina repeticiones textuales y conserva sus fuentes. No resuelve contradicciones semánticas automáticamente."]
    return "\n".join(lines) + "\n"


def markdown(data, snapshot, model):
    if data.get("schema_version") == 3:
        from arktic_office.reporting.executive import render_markdown
        return render_markdown(data, snapshot, model)
    if data.get("schema_version") == 2:
        from arktic_office.reporting.brief import render_brief
        return render_brief(data, snapshot, model)
    return legacy_markdown(data, snapshot, model)
