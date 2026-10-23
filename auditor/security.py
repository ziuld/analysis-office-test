"""Versioned security contract. Local rules are trusted; repository text is not."""
import copy
import json
from pathlib import Path
from repository import AuditError

SEVERITIES = ("critica", "alta", "media", "baja", "informativa")
CONTROLS = {
    "acceso": "Autenticación y autorización",
    "entradas": "Entradas, inyección, archivos y llamadas externas",
    "secretos": "Secretos y protección de datos",
    "dependencias": "Dependencias y cadena de suministro",
    "configuracion": "Configuración y exposición",
    "operacion": "Errores, registros y continuidad",
}
STATES = {"hallazgo", "evidencia_favorable_limitada", "no_evaluado", "no_aplica"}


def instructions():
    return (Path(__file__).parent / "profiles" / "security-v1.md").read_text(encoding="utf-8")


def validate_v3(data, snapshot, limits, validate_legacy):
    if type(data.get("schema_version")) is not int:
        raise AuditError("Versión de informe inválida.")
    required = {"schema_version", "confirmados", "indicios", "dudas", "controles"}
    if not required <= set(data) or not set(data) <= required | {"propuesta_azure", "presentacion", "evaluacion"}:
        raise AuditError("Formato 3 incompleto.")
    legacy = copy.deepcopy(data)
    evaluation = legacy.pop("evaluacion", None)
    proposal = legacy.pop("propuesta_azure", None)
    presentation = legacy.pop("presentacion", None)
    controls = legacy.pop("controles")
    legacy["schema_version"] = 2
    extras = []
    for section in ("confirmados", "indicios"):
        if not isinstance(legacy[section], list):
            raise AuditError("Lista de hallazgos inválida.")
        for item in legacy[section]:
            if not isinstance(item, dict):
                raise AuditError("Hallazgo inválido.")
            extra = {key: item.pop(key, None) for key in ("severidad", "control", "accion", "condiciones")}
            for key, cap in (("titulo", 110), ("resultado_esperado", 300), ("detalle_tecnico", 600)):
                if key in item:
                    from presentation import string
                    extra[key] = string(item.pop(key), cap)
            if not isinstance(extra["severidad"], str) or not isinstance(extra["control"], str) or extra["severidad"] not in SEVERITIES or extra["control"] not in {*CONTROLS, "contexto"}:
                raise AuditError("Severidad o control inválido.")
            if any(not isinstance(extra[k], str) or not extra[k].strip() or len(extra[k]) > 400 for k in ("accion", "condiciones")):
                raise AuditError("Falta acción o condición del riesgo.")
            if extra["control"] == "contexto" and extra["severidad"] != "informativa":
                raise AuditError("El contexto no se cuenta como riesgo.")
            extras.append(extra)
    valid = validate_legacy(json.dumps(legacy), snapshot, limits or {"confirmados": 12, "indicios": 8, "dudas": 8})
    for item, extra in zip(valid["confirmados"] + valid["indicios"], extras):
        from repository import redact
        item.update({k: redact(v) for k, v in extra.items()})
    if not isinstance(controls, list) or len(controls) > len(CONTROLS):
        raise AuditError("Cobertura inválida.")
    seen = set()
    clean_controls = []
    for control in controls:
        if not isinstance(control, dict) or set(control) != {"id", "estado", "motivo", "evidencia"}:
            raise AuditError("Control inválido.")
        if not isinstance(control["id"], str) or not isinstance(control["estado"], str) or control["id"] not in CONTROLS or control["id"] in seen or control["estado"] not in STATES:
            raise AuditError("Control duplicado o estado inválido.")
        seen.add(control["id"])
        if not isinstance(control["motivo"], str) or not 1 <= len(control["motivo"]) <= 400 or not isinstance(control["evidencia"], list):
            raise AuditError("Control sin explicación.")
        refs = control["evidencia"]
        if control["estado"] != "no_evaluado" and not refs:
            raise AuditError("Control evaluado sin evidencia.")
        if refs:
            proof = {"confirmados": [{"observacion": control["motivo"], "evidencia": refs}], "indicios": [], "dudas": []}
            checked = validate_legacy(json.dumps(proof), snapshot)
            refs = checked["confirmados"][0]["evidencia"]
        from repository import redact
        clean_controls.append({**control, "motivo": redact(control["motivo"]), "evidencia": refs})
    valid.update(schema_version=3, controles=clean_controls)
    if "propuesta_azure" in data:
        from azure_proposal import validate
        valid["propuesta_azure"] = validate(proposal, snapshot, validate_legacy)
    if "presentacion" in data:
        from presentation import validate
        valid["presentacion"] = validate(presentation, snapshot, validate_legacy)
    if "evaluacion" in data:
        from outcome import validate_evaluation
        valid["evaluacion"] = validate_evaluation(evaluation)
    return valid
