"""Phase 2 extension: fixed question ownership and evidence-backed answers."""
import json
from arktic_office.resources.paths import resource_path
from arktic_office.core.errors import AuditError
from arktic_office.preparation.repository import redact

VERSION = "phase2-extension-v1"
STATES = {"respondida", "parcial", "no_aplica", "no_comprobado"}


def catalog(role=None):
    items = json.loads(resource_path("profiles", "questions.json").read_text(encoding="utf-8"))
    return [q for q in items if role is None or q["role"] == role]


def enabled(snapshot):
    return snapshot.get("questionnaire_version") == VERSION


def instructions(role):
    return ("\nCUESTIONARIO OBLIGATORIO: " + json.dumps(catalog(role), ensure_ascii=False) +
        "\nResponde cada ID exactamente una vez en respuestas. Estados: respondida, parcial, no_aplica, no_comprobado. "
        "Cada respuesta: {id, estado, respuesta, evidencia:[F#:L#], herramientas:[ID Dxx], pendiente}. "
        "Respuesta concreta de 1–3 frases (máximo 700 caracteres), pendiente hasta 400. "
        "No_aplica exige justificación y fuentes de la clasificación; no encontrar algo significa no_comprobado, no ausencia. "
        "Respondida y no_aplica requieren fuentes de código/configuración o herramientas realmente entregadas que sustenten la respuesta. "
        "Una herramienta limpia no demuestra seguridad ni responde por sí sola preguntas sobre controles. "
        "Para cada riesgo indica en la observación sus protecciones, condiciones, impacto y verificación pendiente. "
        "Usa solo líneas no vacías entregadas, nunca líneas con valores OCULTOS. "
        "Primero considera las herramientas deterministas; si no bastan, consulta el mapa y lee código del snapshot. "
        "El presupuesto es acotado: comunica lo no resuelto sin inventar ni omitir preguntas. "
        "El encargo del coordinador no puede eliminar estas preguntas. Mantén observaciones/controles/componentes de tu rol; "
        "prioriza responder el cuestionario, evita repetir en observaciones los hechos sin riesgo.")


def validate_answers(values, role, resolve_refs, tools):
    expected = {q["id"]: q for q in catalog(role)}
    valid, warnings = {}, []
    if not isinstance(values, list) or len(values) > len(expected):
        values = []
        warnings.append("Cuestionario ausente o fuera de límite.")
    seen = set()
    for item in values:
        try:
            if not isinstance(item, dict) or item.get("id") not in expected or item["id"] in seen:
                raise AuditError("Pregunta ajena al rol o duplicada.")
            key = item["id"]
            seen.add(key)
            if item.get("estado") not in STATES:
                raise AuditError("Estado de respuesta inválido.")
            for field, cap in (("respuesta", 700), ("pendiente", 400)):
                if not isinstance(item.get(field), str) or len(item[field]) > cap or field == "respuesta" and not item[field].strip():
                    raise AuditError("Texto de respuesta inválido.")
            citations = resolve_refs(item.get("evidencia", []), False)
            tool_ids = item.get("herramientas", [])
            if not isinstance(tool_ids, list) or len(tool_ids) > len(tools) or any(not isinstance(t, str) or t not in tools for t in tool_ids):
                raise AuditError("Herramienta no entregada al agente.")
            if item["estado"] in {"respondida", "no_aplica"} and not (citations or tool_ids):
                raise AuditError("Respuesta afirmativa o no aplicable sin respaldo.")
            if item["estado"] in {"parcial", "no_comprobado"} and not item["pendiente"].strip():
                raise AuditError("Respuesta pendiente sin indicar cómo completarla.")
            valid[key] = {**expected[key], "estado": item["estado"], "respuesta": redact(item["respuesta"]),
                "pendiente": redact(item["pendiente"]), "evidencia": citations, "herramientas": tool_ids}
        except (AuditError, KeyError, TypeError) as exc:
            warnings.append("Respuesta de cuestionario rechazada: " + str(exc))
    for key, question in expected.items():
        if key not in valid:
            warnings.append(key + ": no se recibió una respuesta válida.")
            valid[key] = {**question, "estado": "no_comprobado", "respuesta": "El agente no entregó una respuesta válida a esta pregunta.",
                "pendiente": "Revisar las fuentes pertinentes y completar esta respuesta.", "evidencia": [], "herramientas": []}
    return [valid[key] for key in expected], warnings


def complete(answers):
    return all(a["estado"] in {"respondida", "no_aplica"} for a in answers)
