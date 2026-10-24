"""Small polling projection of persisted events/states; never invents dialogue."""
from arktic_office.storage.jsonio import read_json
from arktic_office.core.contracts import ACTIVE_STATES

LABELS = {"no_ejecutado": "Omitido con justificación","preparando": "Preparando evidencia", "analizando": "Revisando evidencia", "completo": "Revisión completada",
          "completada": "Aportación completada", "parcial": "Resultado parcial", "error": "Trabajo interrumpido o con error",
          "informacion_insuficiente": "Información insuficiente", "pendiente": "Esperando evidencia"}


def project(directory, job, cells):
    active = job["estado"] in ACTIVE_STATES
    preparation = read_json(directory / "preparacion.json", {})
    coordination = read_json(directory / "coordinacion.json", {})
    result = {}
    for agent in ("coordinator", "security", "architecture", "inventory"):
        state = job["estado"] if agent == "coordinator" else next((c["estado"] for c in cells if c["id"] == agent), "pendiente")
        if not active and state in {"analizando", "preparando", "pendiente"}:
            state = "error" if job["estado"] == "error" else job["estado"]
        text, meeting = LABELS.get(state, state), False
        if active and agent == "coordinator":
            stages = coordination.get("stages", {})
            if stages.get("routing", {}).get("status") == "running":
                text = "Distribuyendo el contexto preparado"
            elif stages.get("synthesis", {}).get("status") == "running":
                text, meeting = "Sintetizando aportaciones del equipo", True
            elif preparation.get("exploration", {}).get("status") == "running":
                text = "Explorando evidencia con límites"
            elif any(c["estado"] == "analizando" for c in cells):
                state, text = "pendiente", "Contexto entregado a los especialistas"
        cell = next((c for c in cells if c["id"] == agent), {})
        if cell.get("coverage"):
            coverage = {"partial": "cobertura parcial", "insufficient": "evidencia insuficiente", "incomplete": "cobertura incompleta", "available_evidence": "evidencia disponible evaluada"}
            text += " · " + coverage.get(cell["coverage"], cell["coverage"])
        result[agent] = {"state": state, "text": text, "meeting": meeting,
                         "working": active and state in ACTIVE_STATES}
    return result
