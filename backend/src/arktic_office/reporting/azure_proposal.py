"""Small advisory deployment contract; never authorizes or performs deployments."""
import json
from arktic_office.resources.paths import resource_path
from arktic_office.preparation.repository import AuditError, redact

TARGETS = {
    "app_service": "Azure App Service",
    "container_apps": "Azure Container Apps",
    "aks_existente": "AKS corporativo existente (por confirmar)",
    "virtual_machine": "Azure Virtual Machines",
    "por_definir": "Destino pendiente de información",
}
FIELDS = {"estado", "destino", "resumen", "justificacion", "evidencia", "supuestos", "servicios", "pasos", "pendientes"}


def instructions():
    return resource_path("profiles", "azure-v1.md").read_text(encoding="utf-8")


def validate(value, snapshot, validate_report):
    if not isinstance(value, dict) or not FIELDS <= set(value) or not set(value) <= FIELDS | {"conexiones"}:
        raise AuditError("Propuesta Azure incompleta.")
    if not isinstance(value["estado"], str) or value["estado"] not in {"propuesta_preliminar", "informacion_insuficiente"}:
        raise AuditError("Estado de propuesta Azure inválido.")
    if not isinstance(value["destino"], str) or value["destino"] not in TARGETS:
        raise AuditError("Destino Azure inválido.")
    for key in ("resumen", "justificacion"):
        if not isinstance(value[key], str) or not 1 <= len(value[key].strip()) <= 550:
            raise AuditError("Explicación de propuesta Azure inválida.")
    for key, cap in (("supuestos", 3), ("pasos", 5), ("pendientes", 4)):
        if not isinstance(value[key], list) or len(value[key]) > cap or any(not isinstance(x, str) or not 1 <= len(x.strip()) <= 300 for x in value[key]):
            raise AuditError("Lista de propuesta Azure inválida.")
    services = value["servicios"]
    if not isinstance(services, list) or len(services) > 5:
        raise AuditError("La propuesta Azure supera cinco servicios.")
    for item in services:
        if not isinstance(item, dict) or not {"servicio", "uso"} <= set(item) or not set(item) <= {"servicio", "uso", "categoria"} or any(not isinstance(x, str) or not 1 <= len(x.strip()) <= 220 for x in item.values()):
            raise AuditError("Servicio propuesto inválido.")
        if "categoria" in item:
            from arktic_office.reporting.presentation import CATEGORIES
            if item["categoria"] not in CATEGORIES:
                raise AuditError("Categoría del servicio inválida.")
    if "conexiones" in value:
        edges = value["conexiones"]
        if not isinstance(edges, list) or len(edges) > 8:
            raise AuditError("Conexiones propuestas inválidas.")
        for edge in edges:
            if not isinstance(edge, dict) or set(edge) != {"origen", "destino", "descripcion"} or any(type(edge[k]) is not int or not 1 <= edge[k] <= len(services) for k in ("origen", "destino")) or not isinstance(edge["descripcion"], str) or not 1 <= len(edge["descripcion"]) <= 220:
                raise AuditError("Conexión propuesta sin servicios válidos.")
    refs = value["evidencia"]
    if not isinstance(refs, list) or len(refs) > 3:
        raise AuditError("Fuentes de propuesta Azure inválidas.")
    if value["estado"] == "propuesta_preliminar":
        if value["destino"] == "por_definir" or not refs or not services or not value["pasos"] or not value["pendientes"]:
            raise AuditError("La propuesta necesita destino, evidencia, servicios, pasos y validaciones.")
    elif value["destino"] != "por_definir" or services or value["pasos"]:
        raise AuditError("Sin información suficiente no se publica una arquitectura como recomendada.")
    if refs:
        proof = {"confirmados": [{"observacion": "Base técnica de una recomendación, no despliegue verificado.", "evidencia": refs}], "indicios": [], "dudas": []}
        validate_report(json.dumps(proof), snapshot)
    def clean(item):
        if isinstance(item, str):
            return redact(item)
        if isinstance(item, list):
            return [clean(x) for x in item]
        if isinstance(item, dict):
            return {k: clean(v) for k, v in item.items()}
        return item
    return clean(value)
