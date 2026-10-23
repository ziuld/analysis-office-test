"""Information sufficiency is a normal terminal outcome, not a technical failure."""
from arktic_office.preparation.repository import AuditError, redact

INSUFFICIENT = "informacion_insuficiente"


def validate_evaluation(value):
    if not isinstance(value, dict) or set(value) != {"estado", "motivo", "necesita"} or not isinstance(value.get("estado"), str) or value.get("estado") not in {"con_aportaciones", INSUFFICIENT}:
        raise AuditError("Evaluación de suficiencia inválida.")
    if not isinstance(value["motivo"], str) or not 1 <= len(value["motivo"].strip()) <= 400:
        raise AuditError("Falta explicar la suficiencia de la información.")
    needs = value["necesita"]
    if not isinstance(needs, list) or len(needs) > 6 or any(not isinstance(x, str) or not 1 <= len(x.strip()) <= 300 for x in needs):
        raise AuditError("Información necesaria inválida.")
    return {"estado": value["estado"], "motivo": redact(value["motivo"]), "necesita": [redact(x) for x in needs]}


def useful(report):
    p = report.get("presentacion", {})
    return bool(report.get("confirmados") or report.get("indicios") or
                any(c.get("estado") != "no_evaluado" for c in report.get("controles", [])) or
                p.get("resumen") or p.get("flujo_actual", {}).get("componentes") or
                any(r.get("estado") != "no_evaluado" for r in p.get("estado_operativo", [])) or
                report.get("propuesta_azure", {}).get("estado") == "propuesta_preliminar")


def notice(data):
    cells = data.get("celulas", [])
    questions = [q if isinstance(q, str) else q["pregunta"] for q in data.get("dudas", [])]
    for cell in cells:
        questions.extend(cell.get("necesita", []))
    questions.extend(r["pendiente"] for r in data.get("presentacion", {}).get("estado_operativo", []) if r.get("estado") == "no_evaluado")
    if data.get("propuesta_azure", {}).get("estado") == INSUFFICIENT:
        questions.extend(data["propuesta_azure"].get("pendientes", []))
    needs = list(dict.fromkeys(questions))
    unknown = [c["id"] for c in data.get("controles", []) if c.get("estado") == "no_evaluado"]
    if not useful(data):
        message = "No hay información validada suficiente para elaborar una evaluación técnica útil. Hace falta una lectura más profunda del código y la configuración; no puede valorarse su seguridad ni su despliegue."
    elif any(c.get("estado") in {INSUFFICIENT, "sin_evidencia", "parcial", "error"} for c in cells) or unknown or data.get("estado") == "parcial":
        message = "La lectura permite describir los resultados que se muestran, pero no cerrar la evaluación. Se conservan las aportaciones válidas y se concentra aquí la información que falta."
    else:
        message = "Los resultados corresponden al código seleccionado. La evaluación y la decisión de despliegue requieren revisión humana."
    return message, needs, unknown
