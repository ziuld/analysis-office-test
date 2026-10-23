"""Human-facing report v2. Pure rendering: no model calls or new conclusions."""
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from urllib.parse import quote

from arktic_office.preparation.repository import parse_repo

UNKNOWN = "No determinado en esta revisión"
TOPIC_NAMES = {
    "proposito": "Propósito", "componentes": "Componentes", "arranque": "Arranque",
    "datos": "Datos y archivos persistentes", "recuperacion": "Recuperación", "estabilidad": "Estabilidad",
    "recursos": "Recursos y capacidad", "servicios": "Conexiones externas", "acceso": "Acceso y exposición",
    "responsabilidades": "Responsabilidades",
}


def text(value):
    """Render model/repository text as a single literal Markdown paragraph/cell."""
    return re.sub(r"([\\`*_{}\[\]<>|#!])", r"\\\1", " ".join(str(value).split()))


def references(item, snapshot):
    if snapshot.get("simulation"):
        return ", ".join(dict.fromkeys(text(f"{ref['path']}:{ref['line']} (fuente ficticia)") for ref in item.get("evidencia", [])))
    owner, repo = parse_repo(snapshot["repository"])
    commit = snapshot["commit"]
    labels = []
    for ref in item.get("evidencia", []):
        label = text(f"{ref['path']}:{ref['line']}")
        if re.fullmatch(r"[0-9a-fA-F]{40}", commit):
            url = f"https://github.com/{owner}/{repo}/blob/{commit}/{quote(ref['path'], safe='/')}#L{ref['line']}"
            labels.append(f"[{label}]({url})")
        else:
            labels.append(label)
    return ", ".join(dict.fromkeys(labels))


def display_date(value):
    if not value:
        return "No registrada en la evidencia original"
    try:
        moment = datetime.fromisoformat(value)
        if moment.tzinfo is None:
            return text(value)
        try:
            moment = moment.astimezone(ZoneInfo("Europe/Madrid"))
        except ZoneInfoNotFoundError:
            moment = moment.astimezone(timezone.utc)
        return moment.strftime("%d/%m/%Y %H:%M %Z")
    except (ValueError, TypeError):
        return "Fecha no válida en la evidencia guardada"


def render_brief(data, snapshot, model):
    cells = {c["id"]: c.get("nombre", c["id"]) for c in data.get("celulas", [])}
    facts = data.get("confirmados", [])
    clues = data.get("indicios", [])
    entries = [(x, "Confirmado en repositorio") for x in facts] + [(x, "Indicio por confirmar") for x in clues]
    attention = [(item, certainty) for item, certainty in entries if item.get("tema") not in {"componentes", "proposito"}]
    ids = {id(item): f"H{n}" for n, (item, _) in enumerate(attention, 1)}
    purpose = next((x for x in facts if x.get("tema") == "proposito"), None)
    status = "Células completadas; lectura parcial del repositorio" if data.get("estado") == "completo" else "Revisión parcial: hay células sin resultado válido"
    lines = ["# Evaluación preliminar de iniciativa", "", "## Contexto", "",
             f"- **Proyecto:** {text(snapshot['repository'].rstrip('/').split('/')[-1])}.",
             f"- **Propósito documentado:** {text(purpose['observacion']) + ' · ' + references(purpose, snapshot) if purpose else UNKNOWN}.",
             f"- **Repositorio:** {snapshot['repository']} · rama **{text(snapshot.get('branch', 'main'))}** · commit `{snapshot['commit']}`.",
             f"- **Fecha de generación:** {display_date(snapshot.get('analyzed_at'))}.",
             f"- **Estado:** {status}."]
    if snapshot.get("evidence_origin"):
        lines += ["", "**Origen de la evidencia:** " + text(snapshot["evidence_origin"])]
    lines += ["", "## 1. Resumen para el responsable técnico", ""]
    highlights = []
    for role in ("security", "architecture"):
        found = next((x for x in facts if role in x.get("celulas", [])), None)
        if found and found not in highlights:
            highlights.append(found)
    for item in highlights:
        lines.append("- **Confirmado:** " + text(item["observacion"]) + f" (fuentes: {ids.get(id(item), 'sección 2')}).")
    if not highlights:
        lines.append("No hay hechos operativos suficientes para resumir seguridad y arranque; revisar cobertura y pendientes.")
    lines += ["", "Los indicios y la información pendiente se separan abajo. La revisión no determina por sí sola si puede desplegarse con seguridad.",
              "", "## 2. Cómo está construida", "", "| Componente | Tecnología declarada | Función identificada | Evidencia |", "|---|---|---|---|"]
    components = [x for x in facts if x.get("componente")]
    for item in components:
        c = item["componente"]
        lines.append(f"| {text(c['nombre'])} | {text(c['tecnologia'])} | {text(c['funcion'])} | {references(item, snapshot)} |")
    if not components:
        lines.append(f"| {UNKNOWN} | {UNKNOWN} | {UNKNOWN} | — |")
    for item in clues:
        if item.get("tema") in {"componentes", "proposito"}:
            lines += ["", "**Indicio por confirmar:** " + text(item["observacion"]) + " · " + references(item, snapshot),
                      "Por verificar: " + text(item.get("por_confirmar", item.get("pendiente", UNKNOWN)))]
    inventory_pending = list(dict.fromkeys(item["pendiente"] for item in components if item.get("pendiente")))
    if inventory_pending:
        lines += ["", "**Por verificar en el inventario:** " + text(" ".join(inventory_pending))]
    for topic in ("arranque", "datos", "servicios"):
        found = next(((item, certainty) for item, certainty in entries if item.get("tema") == topic), None)
        lines += ["", f"**{TOPIC_NAMES[topic]}:** " + (f"{found[1]} — {text(found[0]['observacion'])} (fuentes: {ids.get(id(found[0]), 'sección 3')})" if found else UNKNOWN) + "."]
    lines += ["", "## 3. Puntos que requieren atención", ""]
    for item, certainty in attention:
        area = "seguridad" if "security" in item.get("celulas", []) else "continuidad" if item.get("tema") in {"datos", "recuperacion", "estabilidad"} else "operación"
        origin = ", ".join(cells.get(c, c) for c in item.get("celulas", [])) or "No registrado"
        pending = item.get("pendiente", UNKNOWN)
        if certainty == "Indicio por confirmar" and item.get("por_confirmar") and item["por_confirmar"] != pending:
            pending += " " + item["por_confirmar"]
        lines += [f"### {ids[id(item)]} · {TOPIC_NAMES.get(item.get('tema'), 'Observación')} — {certainty}", "",
                  f"- **Encontrado:** {text(item['observacion'])}",
                  f"- **Por qué importa:** {text(item.get('importancia', UNKNOWN))}",
                  f"- **Por verificar:** {text(pending)}",
                  f"- **Fuente:** {references(item, snapshot)} · {text(origin)} · área: {area}.", ""]
    if not attention:
        lines += ["No se obtuvieron observaciones operativas con evidencia suficiente; esto no acredita ausencia de riesgos.", ""]
    lines += ["## 4. Estabilidad, recursos y gobernanza", "", "| Aspecto | Evidencia disponible | Validación pendiente |", "|---|---|---|"]
    aspects = (
        ("datos", "Persistencia identificada", "Confirmar ubicación real y persistencia de los datos."),
        ("recuperacion", "Recuperación", "Aportar evidencia de copias y restauración comprobada."),
        ("estabilidad", "Estabilidad", "Comprobar arranque, reinicios y disponibilidad en un entorno controlado."),
        ("recursos", "Recursos y capacidad", "Aportar mediciones de CPU/RAM y volumen de uso; la configuración no demuestra consumo real."),
        ("servicios", "Servicios externos", "Confirmar destinos, cuentas y conectividad utilizados realmente."),
        ("acceso", "Acceso a datos", "Contrastar permisos declarados con el acceso del entorno real."),
        ("responsabilidades", "Responsables y gobernanza", "Identificar responsable de negocio, de operación y autorización de uso de los datos."),
    )
    for topic, label, gap in aspects:
        found = next(((item, certainty) for item, certainty in entries if item.get("tema") == topic), None)
        if found:
            item, certainty = found
            available = f"{certainty} · {ids.get(id(item), 'sección 2')}"
            pending = f"Véase «Por verificar» de {ids.get(id(item), 'sección 2')}."
        else:
            available, pending = UNKNOWN, gap
        lines.append(f"| {label} | {available} | {pending} |")
    lines += ["", "La persistencia identificada puede referirse a archivos de configuración; no acredita cubrir todos los datos de negocio. Los datos desconocidos no demuestran ausencia de controles. Las validaciones de esta tabla son preguntas de cobertura, no hallazgos nuevos.",
              "", "## 5. Implicaciones para la migración", ""]
    base = [ids[id(item)] for item, certainty in attention if certainty == "Confirmado en repositorio" and "architecture" in item.get("celulas", [])]
    lines.append("**Punto de partida declarado:** " + (", ".join(base) + "; sus fuentes y condiciones están en la sección 3." if base else UNKNOWN + "."))
    conditions = [ids[id(item)] for item, _ in attention if "architecture" in item.get("celulas", [])]
    lines.append("**Condiciones por aclarar:** " + (", ".join(conditions) + " (apartados «Por verificar»)." if conditions else UNKNOWN + "."))
    for item, _ in attention:
        if "architecture" in item.get("celulas", []):
            lines.append(f"- {text(item.get('pendiente', UNKNOWN))} ({ids[id(item)]})")
    lines += ["", "**Preguntas pendientes para el responsable técnico:**", ""]
    questions = data.get("dudas", [])
    for q in questions:
        if isinstance(q, str):
            lines.append("- " + text(q))
        else:
            origin = ", ".join(cells.get(c, c) for c in q.get("celulas", []))
            lines.append(f"- {text(q['pregunta'])} ({text(origin)})")
    if not questions:
        lines.append("No se formularon preguntas adicionales; permanecen las carencias de cobertura de la sección 4.")
    lines += ["", "Destino y esfuerzo de migración: no estimados. La decisión corresponde al arquitecto.",
              "", "## 6. Alcance y límites", "",
              f"- **Lectura:** {len(snapshot['files'])} archivos · {snapshot.get('bytes_read', 0)} bytes antes de ocultar posibles credenciales."]
    if data.get("celulas"):
        labels = {"completada": "completada", "error": "falló", "sin_evidencia": "sin evidencia", "pendiente": "pendiente"}
        lines.append("- **Células:** " + "; ".join(f"{text(c.get('nombre', c['id']))}: {labels.get(c['estado'], text(c['estado']))}" for c in data["celulas"]) + ".")
        for c in data["celulas"]:
            if c.get("error"):
                lines.append(f"  - {text(c.get('nombre', c['id']))}: {text(c['error'])}")
    counts = {}
    for item in snapshot.get("excluded", []):
        counts[item["reason"]] = counts.get(item["reason"], 0) + 1
    lines.append("- **Exclusiones:** " + ("; ".join(f"{text(k)}: {v}" for k, v in sorted(counts.items())) if counts else "ninguna registrada") + ".")
    lines += ["- **Detalle:** archivos y citas completas en `evidencia.json`; resultados y cobertura por célula en `celulas/`.",
              "- **Límites:** no se ejecutó la aplicación, no se midió rendimiento ni se verificaron despliegue, exposición o restauración. Las referencias coinciden con el texto leído; las interpretaciones requieren revisión humana. La ocultación de credenciales es heurística.",
              f"- **Generación:** formato 2 · {text(model)} · consolidación mediante código."]
    return "\n".join(lines) + "\n"
