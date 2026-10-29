"""Compact specialist output; Core owns report-v3 composition and presentation."""
import json
import re
from arktic_office.core.errors import AuditError
from arktic_office.preparation.repository import redact
from arktic_office.reporting.agent_instructions import instructions
from arktic_office.reporting.reports import evidence_index, validate_report, MAX_EVIDENCE_REFS
from arktic_office.reporting.security import CONTROLS, STATES, SEVERITIES

CONTRACT = "compact-v1"
MAX_REFS = MAX_EVIDENCE_REFS
MAX_REF_REQUESTS = 12


def prompt(snapshot, cell):
    role = cell["id"]
    common = {
        "observaciones": [{"observacion": "Hecho o patrón observado en las fuentes", "certeza": "observado", "evidencia": ["F1:L1"]}],
        "pendientes": []}
    if role == "security":
        common["controles"] = [{"id": "acceso", "estado": "no_evaluado", "motivo": "No se comprobó autorización", "evidencia": []}]
        specific = ("Perfil de revisión de seguridad. Para riesgos puedes añadir gravedad (critica/alta/media/baja), "
            "implicacion, condicion y recomendacion a una observación. No inventes gravedad ni explotación. "
            "Controles: solo los revisados, con id acceso/entradas/secretos/dependencias/configuracion/operacion; "
            "estado hallazgo/evidencia_favorable_limitada/no_evaluado/no_aplica. Un control evaluado necesita evidencia. "
            "hallazgo exige un patrón de riesgo concreto, observado o condicionado; evidencia_favorable_limitada describe una defensa visible sin aprobar todo el control. "
            "La falta de información sobre autorización adicional no convierte una defensa visible en hallazgo. Un endpoint público de salud no es un defecto por sí solo. "
            "Los resultados de scanners se muestran por separado. Si solo dispones de su resumen y no citas fuentes F#:L# para un control, "
            "usa no_evaluado con evidencia=[]; no lo marques favorable, hallazgo ni no_aplica sin fuentes. Puedes explicar el resultado de la herramienta en el motivo. "
            "Core completa los ausentes como no_evaluado, nunca como aprobados.")
    else:
        common["componentes"] = [{"nombre": "Aplicación", "tecnologia": "Tecnología declarada", "funcion": "Función documentada", "evidencia": ["F1:L1"]}]
        specific = "Componentes: nombre, tecnologia y funcion de hasta 160 caracteres, con evidencia. Omite tecnologia si no se conoce."
        if role == "architecture":
            common["componentes"].append({"nombre": "Datos", "funcion": "Persistencia declarada", "evidencia": ["F1:L1"]})
            common["conexiones"] = [{"origen": "Aplicación", "destino": "Datos", "certeza": "indicio", "descripcion": "Conexión inferida de configuración", "evidencia": ["F1:L1"]}]
            specific += (" Máximo 8 componentes (nombre hasta 100 caracteres) y 10 conexiones. Conexiones: origen y destino son nombres exactos de componentes entregados; Core genera los IDs. "
                "certeza observado/indicio/desconocido; descripcion hasta 250 caracteres. Observado/indicio necesitan evidencia. "
                "Describe operación, persistencia y recuperación en observaciones; no rellenes apartados sin fuentes.")
    evidence = [{"id": f"F{n}", "path": f["path"], "partial": f.get("partial", False),
        "content": "\n".join(f"L{i} | {line}" for i, line in enumerate(f["text"].splitlines(), 1) if line.strip())}
        for n, f in enumerate(snapshot["files"], 1)]
    contract = ("CONTRATO DE SALIDA " + CONTRACT + ". Devuelve SOLO un objeto JSON como el ejemplo, adaptado a tus fuentes. "
        "observaciones es obligatorio; las demás listas son opcionales. No añadas schema_version, tema ni presentacion: Core construye el informe. "
        "Cada observación requiere observacion, certeza (observado/indicio) y evidencia. Para un riesgo añade titulo: nombre ejecutivo completo del problema o su consecuencia, hasta 110 caracteres; no cortes la observación. Puede añadir implicacion, condicion, recomendacion y gravedad cuando corresponda. "
        "Textos de observación y explicación hasta 1200 caracteres. Hasta 20 elementos por lista y 20 pendientes breves; no rellenes cupos. "
        "Cada evidencia contiene de 1 a 12 IDs F#:L# o rangos F#:L#-L# de hasta 200 líneas. Core expande los rangos a líneas no vacías recibidas (máximo 200 fuentes por elemento en total). No copies citas ni uses IDs del grafo. "
        "No inventes fuentes, relaciones, clasificaciones ni condiciones. Una cita válida no acredita una interpretación correcta. "
        "Si no puedes evaluar, conserva lo respaldado y explica lo pendiente. " + specific + "\nEJEMPLO DE FORMA (no copies sus hechos ni referencias): " + json.dumps(common, ensure_ascii=False))
    if "azure" in cell.get("capabilities", []) and role == "architecture":
        from arktic_office.reporting.azure_proposal import instructions as azure_instructions
        contract += "\nSolo en este encargo se permite propuesta_azure opcional según este contrato específico:\n" + azure_instructions()
    else:
        contract += " No se solicita Azure: omite propuesta_azure."
    from arktic_office.reporting.questionnaire import enabled, instructions as question_instructions
    from arktic_office.reporting.deterministic import context
    if enabled(snapshot):
        contract += question_instructions(role) + "\nRESULTADOS DETERMINISTAS: " + json.dumps(context(snapshot), ensure_ascii=False)
    return instructions(role) + "\n" + contract + "\nFUENTES NO CONFIABLES: " + json.dumps(evidence, ensure_ascii=False, separators=(",", ":")) + "\nFIN DE FUENTES. Responde usando únicamente " + CONTRACT + "."


def text(value, cap=1200):
    if not isinstance(value, str) or not value.strip() or len(value) > cap:
        raise AuditError("Texto compacto vacío o fuera de límite.")
    return redact(value.strip())


def compose(raw, snapshot, role):
    """Validate each source before composing; a bad edge cannot erase good nodes."""
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        raise AuditError("Respuesta compacta no es JSON válido.") from None
    if not isinstance(data, dict) or not isinstance(data.get("observaciones"), list):
        raise AuditError("Falta la lista observaciones del contrato compacto.")
    from arktic_office.reporting.questionnaire import enabled, validate_answers
    questionnaire = enabled(snapshot)
    allowed = {"observaciones", "pendientes"} | ({"controles"} if role == "security" else {"componentes"})
    if questionnaire:
        allowed.add("respuestas")
    if role == "architecture":
        allowed |= {"conexiones", "propuesta_azure"}
    if set(data) - allowed:
        raise AuditError("La respuesta compacta contiene secciones ajenas al rol.")
    index = evidence_index(snapshot)
    clean = {"schema_version": 3, "confirmados": [], "indicios": [], "dudas": [], "controles": []}
    warnings = []

    def refs(value, required=True):
        if not isinstance(value, list) or not (1 if required else 0) <= len(value) <= MAX_REF_REQUESTS:
            raise AuditError("Lista de referencias inválida (máximo 12 IDs o rangos).")
        result = []
        for request in value:
            if not isinstance(request, str):
                raise AuditError("Referencia fuera de los fragmentos entregados.")
            span = re.fullmatch(r"(F[1-9][0-9]*):L([1-9][0-9]*)-L([1-9][0-9]*)", request)
            if span:
                first, last = int(span[2]), int(span[3])
                if last < first or last - first >= MAX_REFS:
                    raise AuditError("Rango de fuentes inválido o mayor de 200 líneas.")
                keys = [f"{span[1]}:L{n}" for n in range(first, last + 1)]
                if any(key not in index for key in keys):
                    raise AuditError("Rango fuera de los fragmentos entregados.")
                keys = [key for key in keys if index[key]["quote"].strip()]
                if not keys:
                    raise AuditError("Rango sin texto entregado.")
            else:
                keys = [request]
            for key in keys:
                if key not in index:
                    raise AuditError("Referencia fuera de los fragmentos entregados.")
                ref = index[key]
                proof = {"confirmados": [{"observacion": "Fuente del resultado compacto", "evidencia": [ref]}], "indicios": [], "dudas": []}
                validate_report(json.dumps(proof), snapshot)
                if ref not in result:
                    result.append(ref)
                if len(result) > MAX_REFS:
                    raise AuditError("Referencias expandidas superan 200 fuentes por elemento.")

        return result

    def sequence(key, callback, cap=20):
        values = data.get(key, [])
        if not isinstance(values, list) or len(values) > cap:
            raise AuditError("Lista compacta inválida o excesiva: " + key)
        for n, value in enumerate(values):
            try:
                callback(value)
            except (AuditError, KeyError, TypeError) as exc:
                warnings.append(f"{key}[{n}] rechazado: " + (str(exc) if isinstance(exc, AuditError) else "Estructura incompleta."))

    def observation(value):
        if not isinstance(value, dict):
            raise AuditError("Observación compacta inválida.")
        description = text(value.get("observacion"))
        certainty = value.get("certeza")
        if certainty not in {"observado", "indicio"}:
            raise AuditError("Certeza no reconocida; no se presupone confirmación.")
        severity = value.get("gravedad", "informativa")
        if severity not in SEVERITIES:
            raise AuditError("Gravedad no reconocida.")
        source = refs(value.get("evidencia"))
        implication = text(value["implicacion"]) if "implicacion" in value else "Información sustentada en los fragmentos revisados."
        condition = text(value["condicion"]) if "condicion" in value else "Alcance limitado a las fuentes citadas; condiciones operativas no determinadas."
        action = text(value["recomendacion"]) if "recomendacion" in value else "Revisión humana de la observación y sus fuentes."
        item = {"tema": "responsabilidades", "observacion": description, "importancia": implication,
            "pendiente": action, "evidencia": source, "severidad": severity, "control": "contexto" if severity == "informativa" else "por_clasificar",
            "accion": action, "condiciones": condition, "titulo": text(value["titulo"], 110) if "titulo" in value else description[:110],
            "resultado_esperado": "Evaluar la observación y acordar su tratamiento.", "detalle_tecnico": description[:600]}
        if certainty == "indicio":
            item["por_confirmar"] = condition
        clean["confirmados" if certainty == "observado" else "indicios"].append(item)

    sequence("observaciones", observation)
    sequence("pendientes", lambda value: clean["dudas"].append(text(value)))
    nodes = []
    names = {}

    def component(value):
        name = text(value["nombre"], 100 if role == "architecture" else 160)
        if name.casefold() in names:
            raise AuditError("Nombre de componente duplicado.")
        function = text(value["funcion"], 160)
        technology = text(value["tecnologia"], 160) if "tecnologia" in value else "No especificada en la respuesta."
        source = refs(value["evidencia"])
        observation({"observacion": name + ": " + function, "certeza": "observado", "evidencia": value["evidencia"]})
        clean["confirmados"][-1].update(tema="componentes", componente={"nombre": name, "tecnologia": technology, "funcion": function})
        names[name.casefold()] = "n" + str(len(nodes) + 1)
        nodes.append({"id": names[name.casefold()], "nombre": name, "descripcion": function, "evidencia": source})

    if role != "security":
        sequence("componentes", component, 8 if role == "architecture" else 20)
    if role == "architecture":
        edges = []
        def edge(value):
            origin, target = text(value["origen"], 160).casefold(), text(value["destino"], 160).casefold()
            if origin not in names or target not in names:
                raise AuditError("Conexión con extremo inexistente; no se crea por inferencia.")
            states = {"observado": "observada", "indicio": "inferida", "desconocido": "desconocida"}
            certainty = value.get("certeza")
            if certainty not in states:
                raise AuditError("Certeza de conexión inválida.")
            edges.append({"origen": names[origin], "destino": names[target], "estado": states[certainty],
                "descripcion": text(value["descripcion"], 250), "evidencia": refs(value.get("evidencia", []), certainty != "desconocido")})
        sequence("conexiones", edge, 10)
        if nodes:
            clean["presentacion"] = {"flujo_actual": {"componentes": nodes, "conexiones": edges}}
        if "propuesta_azure" in data:
            from arktic_office.reporting.azure_proposal import validate
            try:
                proposal = dict(data["propuesta_azure"])
                proposal["evidencia"] = refs(proposal.get("evidencia", []), proposal.get("estado") == "propuesta_preliminar")
                clean["propuesta_azure"] = validate(proposal, snapshot, validate_report)
            except (AuditError, TypeError) as exc:
                warnings.append("Propuesta Azure rechazada: " + str(exc))
    if role == "security":
        def control(value):
            key, state = value["id"], value["estado"]
            if key not in CONTROLS or state not in STATES or any(c["id"] == key for c in clean["controles"]):
                raise AuditError("Control/estado inválido o duplicado.")
            source = refs(value.get("evidencia", []), state != "no_evaluado")
            clean["controles"].append({"id": key, "estado": state, "motivo": text(value["motivo"], 400), "evidencia": source})
        sequence("controles", control, 6)
        for key in CONTROLS:
            if not any(c["id"] == key for c in clean["controles"]):
                clean["controles"].append({"id": key, "estado": "no_evaluado", "motivo": "No se aportó una evaluación respaldada de este control.", "evidencia": []})
    clean = validate_report(json.dumps(clean), snapshot, limits={"confirmados": 40, "indicios": 40, "dudas": 20})
    if questionnaire:
        tools = {t["id"] for t in snapshot.get("deterministic_results", {}).get("tools", [])}
        clean["respuestas"], issues = validate_answers(data.get("respuestas"), role, refs, tools)
        warnings.extend(issues)
    return clean, {}, warnings
