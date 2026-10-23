"""Optional structured presentation. Missing data stays missing in older reports."""
import json
from arktic_office.preparation.repository import AuditError, redact

ASPECTS = {"motor": "Motor", "ubicacion": "Ubicación de los datos", "acceso": "Acceso y conexiones", "cuentas": "Cuentas y permisos", "copias": "Copias de seguridad", "recuperacion": "Recuperación", "disponibilidad": "Disponibilidad", "capacidad": "Capacidad"}
CATEGORIES = {"ejecucion": "Ejecución", "datos": "Datos", "entrega": "Entrega de versiones", "monitorizacion": "Monitorización", "acceso": "Acceso"}

def string(value, limit=400):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
        raise AuditError("Texto estructurado del informe inválido.")
    return redact(value)

def refs(value, snapshot, checker, required=True):
    if not isinstance(value, list) or len(value) > 3 or required and not value:
        raise AuditError("Faltan fuentes para el contenido estructurado.")
    if value:
        checker(json.dumps({"confirmados": [{"observacion": "Base del contenido estructurado", "evidencia": value}], "indicios": [], "dudas": []}), snapshot)
    return value

def validate(value, snapshot, checker):
    if not isinstance(value, dict) or not set(value) <= {"resumen", "flujo_actual", "estado_operativo", "decision"}:
        raise AuditError("Presentación del informe inválida.")
    result = {}
    if "resumen" in value:
        x = value["resumen"]
        if not isinstance(x, dict) or set(x) != {"descripcion", "tecnologia_principal", "evidencia"}:
            raise AuditError("Resumen estructurado inválido.")
        result["resumen"] = {"descripcion": string(x["descripcion"]), "tecnologia_principal": string(x["tecnologia_principal"], 150), "evidencia": refs(x["evidencia"], snapshot, checker)}
    if "flujo_actual" in value:
        flow = value["flujo_actual"]
        if not isinstance(flow, dict) or set(flow) != {"componentes", "conexiones"} or not isinstance(flow["componentes"], list) or not isinstance(flow["conexiones"], list) or len(flow["componentes"]) > 8 or len(flow["conexiones"]) > 10:
            raise AuditError("Flujo estructurado inválido.")
        nodes, edges, seen = [], [], set()
        for node in flow["componentes"]:
            if not isinstance(node, dict) or set(node) != {"id", "nombre", "descripcion", "evidencia"}:
                raise AuditError("Componente de flujo inválido.")
            key = string(node["id"], 40)
            if not key.isascii() or not key.replace("_", "").isalnum() or key in seen:
                raise AuditError("Identificador de flujo inválido o duplicado.")
            seen.add(key)
            nodes.append({"id": key, "nombre": string(node["nombre"], 100), "descripcion": string(node["descripcion"], 180), "evidencia": refs(node["evidencia"], snapshot, checker)})
        for edge in flow["conexiones"]:
            if not isinstance(edge, dict) or set(edge) != {"origen", "destino", "estado", "descripcion", "evidencia"} or not isinstance(edge["estado"], str) or edge["estado"] not in {"observada", "inferida", "desconocida"}:
                raise AuditError("Conexión de flujo inválida.")
            if not isinstance(edge["origen"], str) or not isinstance(edge["destino"], str) or edge["origen"] not in seen or edge["destino"] not in seen:
                raise AuditError("Conexión con componentes inexistentes.")
            edges.append({**edge, "descripcion": string(edge["descripcion"], 250), "evidencia": refs(edge["evidencia"], snapshot, checker, edge["estado"] != "desconocida")})
        result["flujo_actual"] = {"componentes": nodes, "conexiones": edges}
    if "estado_operativo" in value:
        rows = value["estado_operativo"]
        if not isinstance(rows, list) or len(rows) > 8:
            raise AuditError("Estado operativo inválido.")
        seen, clean = set(), []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"aspecto", "estado", "descripcion", "pendiente", "evidencia"} or not isinstance(row["aspecto"], str) or row["aspecto"] not in ASPECTS or row["aspecto"] in seen or not isinstance(row["estado"], str) or row["estado"] not in {"observado", "indicio", "no_evaluado"}:
                raise AuditError("Fila operativa inválida o duplicada.")
            seen.add(row["aspecto"])
            clean.append({**row, "descripcion": string(row["descripcion"]), "pendiente": string(row["pendiente"], 300), "evidencia": refs(row["evidencia"], snapshot, checker, row["estado"] != "no_evaluado")})
        result["estado_operativo"] = clean
    if "decision" in value:
        x = value["decision"]
        if not isinstance(x, dict) or set(x) != {"propuesta", "evidencia_pendiente", "siguiente_paso"} or not isinstance(x["evidencia_pendiente"], list) or len(x["evidencia_pendiente"]) > 5:
            raise AuditError("Decisión propuesta inválida.")
        result["decision"] = {"propuesta": string(x["propuesta"]), "evidencia_pendiente": [string(v, 300) for v in x["evidencia_pendiente"]], "siguiente_paso": string(x["siguiente_paso"])}
    return result
