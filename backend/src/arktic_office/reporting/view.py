"""Executive v14 layout over validated records; no semantic rewriting or model calls."""
import base64
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import quote
from arktic_office.reporting.brief import text, references, display_date
from arktic_office.preparation.repository import parse_repo, AuditError
from arktic_office.reporting.presentation import ASPECTS, CATEGORIES
from arktic_office.reporting.security import CONTROLS, SEVERITIES

from arktic_office.resources.paths import resource_path
ASSETS = resource_path("assets")
GRAVITY = {"critica": ("Crítica", "critical", "c"), "alta": ("Alta", "high", "h"), "media": ("Media", "medium", "m"), "baja": ("Baja", "low", "l"), "informativa": ("Informativa", "neutral", "i")}
CONTROL_STATES = {"hallazgo": "Hallazgo identificado", "evidencia_favorable_limitada": "Evidencia favorable limitada", "no_evaluado": "No evaluado", "no_aplica": "No aplica justificado"}
UNKNOWN = "No aportado en los resultados guardados."
NEXT = {"motor": "Confirmar motor y versión utilizados.", "ubicacion": "Identificar dónde se conservan datos y archivos.", "acceso": "Comprobar quién puede conectarse.", "cuentas": "Verificar cuentas efectivas y sus permisos.", "copias": "Localizar copias y su ubicación.", "recuperacion": "Aportar una restauración comprobada.", "disponibilidad": "Comprobar arranque, reinicios y disponibilidad.", "capacidad": "Medir volumen, concurrencia y consumo."}

def h(value):
    return escape(str(value), quote=True)

def paragraph(label, value):
    return '<p><strong>' + h(label) + '</strong> ' + h(value) + '</p>'

def link(target, label, cls=""):
    return f'<a class="{cls}" href="#{target}">{h(label)}</a>'

def sources(item, snapshot):
    values = []
    for ref in item.get("evidencia", []):
        label = f"{ref['path']}:{ref['line']}"
        if snapshot.get("simulation"):
            values.append(h(label + " (fuente ficticia)"))
            continue
        try:
            owner, repo = parse_repo(snapshot["repository"])
        except AuditError:
            values.append(h(label))
            continue
        commit = snapshot.get("commit", "")
        if re.fullmatch(r"[0-9a-fA-F]{40}", commit):
            url = f"https://github.com/{owner}/{repo}/blob/{commit}/{quote(ref['path'], safe='/')}#L{ref['line']}"
            values.append(f'<a href="{h(url)}" target="_blank" rel="noopener noreferrer">{h(label)}</a>')
        else:
            values.append(h(label))
    return "; ".join(dict.fromkeys(values)) or "Sin fuente aportada."

def table(headers, rows, row_classes=None):
    if not rows:
        return '<p class="sub">' + h(UNKNOWN) + '</p>'
    return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th scope="col">' + h(x) + '</th>' for x in headers) + '</tr></thead><tbody>' + ''.join('<tr class="' + h(row_classes[i] if row_classes else "") + '">' + ''.join('<td>' + x + '</td>' for x in row) + '</tr>' for i, row in enumerate(rows)) + '</tbody></table></div>'

def detail(key, title, subtitle, body):
    return f'<details id="{key}"><summary>{h(title)}<span>{h(subtitle)}</span></summary><div class="detail-body">{body}</div></details>'

def chapter(key, number, eyebrow, title, intro, body):
    return f'<section class="chapter" id="{key}"><header class="chapter-heading"><span class="chapter-number">{number}</span><div><div class="eyebrow">{h(eyebrow)}</div><h2>{h(title)}</h2><p>{h(intro)}</p></div></header>{body}</section>'

def view(data, snapshot):
    from arktic_office.reporting.executive import risks, components
    entries = [{**x, "id": f"R{i:02}"} for i, x in enumerate(risks(data), 1)]
    observed = [x for x in entries if x["certeza"] == "confirmados"]
    pending = [x for x in entries if x["certeza"] == "indicios"]
    info = data.get("presentacion", {})
    summary = info.get("resumen", {})
    purpose = next((x for x in data.get("confirmados", []) if x.get("tema") == "proposito" and x.get("severidad") == "informativa"), None)
    tentative = next((x for x in data.get("indicios", []) if x.get("tema") == "proposito"), None)
    description = summary.get("descripcion") or (purpose["observacion"] if purpose else "Hipótesis por confirmar: " + tentative["observacion"] + " Falta información para confirmar su alcance." if tentative else "Resultados de la revisión estática del repositorio.")
    rows = {x["aspecto"]: x for x in info.get("estado_operativo", [])}
    operations = [{"aspecto": key, "estado": "no_evaluado", "descripcion": "Sin dato estructurado para este aspecto.", "pendiente": NEXT[key], "evidencia": [], **rows.get(key, {})} for key in ASPECTS]
    return {"data": data, "snapshot": snapshot, "entries": entries, "observed": observed, "pending": pending,
            "description": description, "summary": summary, "purpose": purpose or tentative, "operations": operations, "components": components(data), "flow": info.get("flujo_actual", {}), "decision": info.get("decision", {}), "azure": data.get("propuesta_azure")}

def uses_compact_contract(data):
    return any(c.get("contrato_salida") == "compact-v1" for c in data.get("celulas", []))


def summary_findings(data):
    """Show existing observations first, preserving certainty and risk conditions."""
    from arktic_office.reporting.executive import risks
    ordered = risks(data) + [{**x, "certeza": "confirmados"} for x in data.get("confirmados", []) if x.get("severidad", "informativa") == "informativa"]
    selected, seen = [], set()
    for item in ordered:
        if item["observacion"] not in seen:
            selected.append(item)
            seen.add(item["observacion"])
        if len(selected) == 3:
            break
    return selected


def badges(item, snapshot):
    label, css, _ = GRAVITY[item["severidad"]]
    certainty = "Observado en fuentes ficticias" if snapshot.get("simulation") and item["certeza"] == "confirmados" else "Observado en archivos" if item["certeza"] == "confirmados" else "Indicio por confirmar"
    return f'<span class="tag {css}">Gravedad {h(label.lower())}</span><span class="tag {"neutral" if item["certeza"] == "confirmados" else "pending"}">{certainty}</span>'

def flow_html(flow, snapshot):
    nodes = flow.get("componentes", [])
    edges = flow.get("conexiones", [])
    if not nodes:
        return '<div class="callout">Conexiones no estructuradas en este resultado. No se dibuja una cadena por deducción. ' + link("inventario", "Consultar componentes y fuentes") + '</div>'
    by_id = {n["id"]: n for n in nodes}
    ordered_chain = len(edges) == len(nodes) - 1 and all(edge["origen"] == nodes[i]["id"] and edge["destino"] == nodes[i + 1]["id"] for i, edge in enumerate(edges))
    body = '<div class="flow">'
    for i, node in enumerate(nodes):
        body += '<div class="node"><b>' + h(node["nombre"]) + '</b>' + h(node["descripcion"]) + '</div>'
        if ordered_chain and i < len(edges):
            edge = edges[i]
            symbol = '→' if edge['estado'] == 'observada' else '⇢' if edge['estado'] == 'inferida' else '⋯ ? ⋯'
            body += '<span class="arrow" title="' + h(edge['descripcion']) + '">' + symbol + '<small>' + h(edge['estado']) + '</small></span>'
    body += '</div>'
    for edge in edges:
        state = edge["estado"]
        arrow = '→' if state == 'observada' else '⇢' if state == 'inferida' else '⋯ ? ⋯'
        body += f'<div class="connection {state}"><b>{h(by_id[edge["origen"]]["nombre"])}</b><span class="arrow">{arrow}</span><b>{h(by_id[edge["destino"]]["nombre"])}</b><span class="tag neutral">{h(state)}</span><p>{h(edge["descripcion"])}</p></div>'
    if not edges:
        body += '<p class="sub">No se aportaron conexiones entre estos componentes.</p>'
    return body + '<p class="flow-note">Flecha continua: observada · discontinua: inferida · puntos/interrogante: desconocida. ' + link("flujo-fuentes", "Ver respaldo del flujo") + '</p>'

def render_html(data, snapshot, model=""):
    """Executive v14 layout over saved evidence; no extra model calls."""
    if data.get("cuestionario"):
        from arktic_office.reporting.reading import render_html as reading_html
        return reading_html(data, snapshot, model)
    v = view(data, snapshot)
    css = (ASSETS / "report-v12.css").read_text(encoding="utf-8") + (ASSETS / "report-v14.css").read_text(encoding="utf-8")
    logo = 'data:image/png;base64,' + base64.b64encode((ASSETS / "arktic-logo.png").read_bytes()).decode()
    simulation = bool(snapshot.get("simulation"))
    title = snapshot.get("project_name") or snapshot["repository"].rstrip('/').split('/')[-1]
    banner = '<div class="demo"><div class="wrap"><strong>' + ('FUENTES FICTICIAS' if simulation else 'REVISIÓN PRELIMINAR') + '</strong>' + h(snapshot.get("evidence_origin") or "Resultados estáticos para evaluación humana; fuentes al commit revisado.") + '</div></div>'
    hero = f'<header class="hero"><div class="hero-art" aria-hidden="true"></div><div class="wrap"><div class="brand-row"><img class="corporate-logo" src="{logo}" alt="Arktic"></div><h1>{h(title)}</h1><p>Evaluación preliminar de la aplicación, sus riesgos y las condiciones para incorporarla a TI.</p><div class="meta"><span>{h(display_date(snapshot.get("analyzed_at")))}</span><span>Decisión del arquitecto pendiente</span></div></div></header>'
    nav = '<nav class="nav" aria-label="Hilo conductor del informe"><div class="wrap">' + ''.join(f'<a href="#{key}"><b>{i:02}</b>{name}</a>' for i, (key, name) in enumerate((("introduccion", "Resumen y prioridades"), ("situacion-actual", "Aplicación y datos"), ("situacion-objetivo", "Recomendaciones"), ("anexos", "Anexos completos")), 1)) + '</div></nav>'
    about = '<p class="appdesc">' + h(v["description"]) + '</p>'
    if v["summary"].get("tecnologia_principal"):
        about += paragraph("Tecnología principal:", v["summary"]["tecnologia_principal"])
    about += '<p class="mini">' + link("inventario", "Componentes y fuentes") + ' · ' + link("cobertura", "Repositorio, revisión y cobertura") + '</p>'
    counts = {state: sum(c["estado"] == state for c in data.get("controles", [])) for state in CONTROL_STATES}
    cards = '<section id="resumen-revisiones" class="review-grid">'
    for target, label, value, description in (
        ("controles", "Seguridad", str(counts["hallazgo"]) + (" control con riesgos" if counts["hallazgo"] == 1 else " controles con riesgos") if data.get("controles") else "Sin estados registrados", str(counts["evidencia_favorable_limitada"]) + " con defensas observadas · " + str(counts["no_evaluado"]) + " no evaluados · " + str(counts["no_aplica"]) + " no aplicables. Estados de los controles registrados; no es una puntuación."),
        ("flujo-actual", "Arquitectura", str(len(v["flow"].get("componentes", []))) + " componentes" if v["flow"].get("componentes") else "Flujo no estructurado", str(len(v["flow"].get("conexiones", []))) + " conexiones documentadas. Configuración y relaciones descritas; ejecución no comprobada."),
        ("cobertura", "Mapas y herramientas", str(len(data.get("scanners", []))) + " resultados registrados" if data.get("scanners") else "Sin resultados guardados", "Estado y alcance de cada herramienta en anexos. Una herramienta sin evaluar no equivale a un resultado limpio.")):
        cards += '<a class="review-card" href="#' + target + '"><span class="review-label">' + label + '</span><strong class="review-text">' + value + '</strong><p>' + h(description) + '</p></a>'
    cards += '</section>'
    findings = '<section id="hallazgos-resumen" class="panel margin-top"><h3>Hallazgos y prioridades</h3>'
    if v["entries"]:
        selected = v["entries"][:7]
        rows = []
        for item in selected:
            rows.append(['<span id="resumen-' + item["id"] + '"></span>' + link(item["id"], item["id"]), h(item["observacion"]), h(item["importancia"]) + paragraph("Condiciones:", item["condiciones"]), badges(item, snapshot)])
        findings += table(["ID", "Qué encontramos", "Consecuencia posible", "Gravedad / estado"], rows)
        rest = v["entries"][7:]
        if rest:
            findings += '<p class="mini">Más resultados: ' + ' · '.join('<span id="resumen-' + x["id"] + '"></span>' + link(x["id"], x["id"]) for x in rest) + '</p>'
        findings += '<p class="mini">Selección por gravedad declarada, conservando certeza y condiciones; no demuestra explotación. ' + link("registro", "Detalle completo y fuentes") + '</p>'
    else:
        facts = summary_findings(data)
        for item in facts:
            findings += paragraph("Observado:", item["observacion"]) + '<p class="source">' + sources({**item, "evidencia": item.get("evidencia", [])[:3]}, snapshot) + '</p>'
        if not facts:
            findings += '<p>No se obtuvieron observaciones respaldadas en esta revisión.</p>'
    findings += '</section>'
    from arktic_office.reporting.questionnaire_view import html as questionnaire_html
    intro = chapter("introduccion", "01", "Lectura inicial", "Resumen ejecutivo y prioridades", "Lo encontrado y sus implicaciones; verificaciones pendientes en anexos.", about + questionnaire_html(data, snapshot, summary=True) + cards + findings)
    operation = '<div id="flujo-actual" class="panel operation"><div class="eyebrow">Componentes y comunicación</div><h2>Flujo actual de la aplicación</h2>' + flow_html(v["flow"], snapshot) + '</div>'
    known = [r for r in v["operations"] if r["estado"] != "no_evaluado"]
    database = ''
    if known:
        database = '<section id="continuidad" class="section panel"><h2>Almacenamiento y operación declarados</h2>' + table(["Aspecto", "Identificado", "Pendiente de verificar"], [[h(ASPECTS[r["aspecto"]]), h(r["descripcion"]), h(r["pendiente"])] for r in known]) + '<p class="mini">' + link("datos-operacion", "Ver fuentes") + '</p></section>'
    # Compact results deliberately keep these as observations, not a second required schema.
    facts = [{**x, "certeza": section} for section in ("confirmados", "indicios") for x in data.get(section, []) if x.get("severidad", "informativa") == "informativa" and not x.get("componente")]
    if facts:
        database += '<section id="contexto-aplicacion" class="panel section"><h2>Información identificada en las fuentes</h2>'
        for item in facts[:4]:
            database += paragraph("Observado:" if item["certeza"] == "confirmados" else "Indicio:", item["observacion"]) + '<p class="source">' + sources({**item, "evidencia": item.get("evidencia", [])[:3]}, snapshot) + '</p>'
        database += link("aportaciones", "Observaciones completas y fuentes →") + '</section>'
    current = chapter("situacion-actual", "02", "Situación identificada", "Aplicación y datos", "Componentes, conexiones y hechos respaldados por código, configuración o documentación.", operation + database)
    target_body = '<div class="panel"><h3>Acciones respaldadas por los hallazgos</h3><p>Las recomendaciones y sus condiciones se conservan junto a cada resultado.</p>' + link("controles-objetivo", "Consultar acciones propuestas →") + '</div>'
    if v["azure"] and v["azure"].get("estado") == "propuesta_preliminar":
        target_body += azure_html(v)
    if v["decision"]:
        target_body += '<section id="decision" class="panel section"><h3>Propuesta para revisión humana</h3>' + paragraph("", v["decision"].get("propuesta", "")) + paragraph("Siguiente paso:", v["decision"].get("siguiente_paso", "")) + '</section>'
    target = chapter("situacion-objetivo", "03", "Recomendación preliminar", "Mejoras propuestas", "Acciones derivadas del análisis. Alojamiento solo cuando existe una propuesta explícita.", target_body)
    footer = f'<footer><div class="corporate-footer"><span>ARKTIC OFFICE / TECNOLOGÍA Y CIBERSEGURIDAD</span><img class="footer-logo" src="{logo}" alt="Arktic"></div><p>La evaluación y la decisión corresponden al arquitecto. Las fuentes y los resultados originales se conservan.</p></footer>'
    script = (ASSETS / "report-navigation.js").read_text(encoding="utf-8")
    from arktic_office.reporting.compact import compact_html
    return compact_html('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + h(title) + ' · Informe Arktic</title><style>' + css + '</style></head><body>' + banner + hero + nav + '<main class="wrap">' + intro + current + target + annex_html(v) + footer + '</main><script id="arktic-report-navigation">' + script + '</script></body></html>', v)

def azure_html(v):
    p = v["azure"]
    body = '<section id="azure" class="section panel azure"><div class="eyebrow">3.2 / Alojamiento y entrega</div><h2>Arquitectura propuesta en Azure</h2>'
    if not p:
        return body + '<p>No disponible en esta revisión. Los informes anteriores conservan su alcance; revisar el estado de Arquitectura.</p></section>'
    from arktic_office.reporting.azure_proposal import TARGETS
    body += paragraph("Objetivo propuesto:", p["resumen"]) + paragraph("Opción principal:", TARGETS[p["destino"]]) + paragraph("Por qué encaja:", p["justificacion"])
    services = p.get("servicios", [])
    body += '<figure class="infra-diagram"><div class="infra-boundary-label">Esquema lógico propuesto · no representa infraestructura desplegada</div><div class="proposal-lanes">'
    for category, label in {**CATEGORIES, "sin_categoria": "Función no estructurada"}.items():
        group = [s for s in services if s.get("categoria", "sin_categoria") == category]
        if group:
            body += '<div class="proposal-lane"><span class="infra-kicker">' + label + '</span>' + ''.join('<div class="infra-node"><strong>' + h(s["servicio"]) + '</strong><span>' + h(s["uso"]) + '</span></div>' for s in group) + '</div>'
    body += '</div>'
    for edge in p.get("conexiones", []):
        body += '<div class="connection"><b>' + h(services[edge["origen"] - 1]["servicio"]) + '</b><span class="arrow">→</span><b>' + h(services[edge["destino"] - 1]["servicio"]) + '</b><p>' + h(edge["descripcion"]) + '</p></div>'
    if not p.get("conexiones"):
        body += '<p class="sub">No se aportaron conexiones estructuradas entre los servicios. No se deducen flechas a partir de sus nombres.</p>'
    body += '<figcaption>Servicios, conectividad, identidad y permisos propuestos deben diseñarse y probarse.</figcaption></figure>'
    body += detail("funcion-servicios", "Función de cada servicio propuesto", "Servicios y supuestos", table(["Servicio", "Función propuesta"], [[h(s["servicio"]), h(s["uso"])] for s in services]) + '<h3>Supuestos pendientes</h3><ul>' + ''.join('<li>' + h(x) + '</li>' for x in p["supuestos"]) + '</ul>')
    return body + link("entrega", "Preparación, pruebas y vuelta atrás →", "back") + '<p class="mini">Criterios de servicio: <a href="https://learn.microsoft.com/en-us/azure/container-apps/compare-options" target="_blank" rel="noopener noreferrer">Comparación oficial de Azure</a>. Verificar disponibilidad y política corporativa antes de implementar.</p></section>'

def annex_html(v):
    data, snapshot = v["data"], v["snapshot"]
    def risk_detail(item):
        key = item["id"]
        body = f'<article id="{key}" class="risk-detail"><h3>{key} · {h(item.get("titulo", item["observacion"]))}</h3><div class="risk-meta">' + badges(item, snapshot) + '</div>'
        for label, field in (("Qué encontramos", "observacion"), ("Qué podría pasar", "importancia"), ("De qué depende", "condiciones"), ("Qué cambiar", "accion"), ("Cómo comprobarlo o cerrar la duda", "pendiente")):
            body += paragraph(label, item[field])
        if item.get("por_confirmar"):
            body += paragraph("Por confirmar", item["por_confirmar"])
        body += '<p class="source">Fuentes: ' + sources(item, snapshot) + '</p>'
        technical = paragraph("Terminología y mecanismo", item.get("detalle_tecnico", "No se aportó un detalle técnico adicional; se conserva la observación original debajo."))
        for ref in item.get("evidencia", []):
            technical += '<p class="source">' + h(f'{ref["path"]}:{ref["line"]}') + '</p><pre>' + h(ref["quote"]) + '</pre>'
        originals = item.get("aportaciones", [{"celula": ", ".join(item.get("celulas", [])), "resultado": {k: val for k, val in item.items() if k not in {"id", "certeza"}}}])
        technical += '<h4>Aportaciones originales</h4><pre>' + h(json.dumps(originals, ensure_ascii=False, indent=2)) + '</pre>'
        body += detail("tecnico-" + key, "Terminología y respaldo técnico", "Fuentes y resultado original", technical)
        return body + link("resumen-" + key, "← Volver al contexto del riesgo", "return-link") + '</article>'
    body = ""
    body += detail("registro", "Registro de riesgos observados", f'{len(v["observed"])} riesgos', ''.join(risk_detail(x) for x in v["observed"]) or '<p>No hay riesgos observados en el alcance guardado.</p>')
    body += detail("indicios", "Indicios pendientes de confirmación", f'{len(v["pending"])} posibles riesgos', ''.join(risk_detail(x) for x in v["pending"]) or '<p>No se aportaron indicios.</p>')
    op = table(["Aspecto", "Estado identificado", "Pendiente", "Fuente"], [[h(ASPECTS[r["aspecto"]]), h(r["estado"]) + '<p>' + h(r["descripcion"]) + '</p>', h(r["pendiente"]), sources(r, snapshot)] for r in v["operations"] if r["estado"] != "no_evaluado"])
    body += detail("datos-operacion", "Datos, disponibilidad y capacidad", "Estado identificado y comprobaciones pendientes", op + '<p>Persistencia no demuestra copia recuperable. La configuración no acredita funcionamiento ni capacidad medida.</p>' + link("continuidad", "← Volver a base de datos y recuperación"))
    inventory = table(["Componente", "Tecnología y versión declarada", "Función", "Certeza / fuente"], [[h(x["componente"]["nombre"]), h(x["componente"]["tecnologia"]), h(x["componente"]["funcion"]), h(x["certeza"]) + '<p>' + sources(x, snapshot) + '</p>'] for x in v["components"]])
    inventory += '<p>Se conservan las variantes aportadas por las células; no se resuelven diferencias de versiones o descripciones automáticamente. Las versiones declaradas no se verificaron en ejecución.</p>'
    body += detail("inventario", "Inventario de componentes y tecnologías", "Función y fuentes; variantes conservadas", inventory + link("introduccion", "← Volver al resumen"))
    summary_sources = sources(v["summary"], snapshot) if v["summary"] else "Resumen no estructurado en el resultado original; se conserva únicamente el propósito observado si se aportó."
    if not v["summary"]:
        purpose = v.get("purpose")
        if purpose:
            summary_sources += '<p>' + sources(purpose, snapshot) + '</p>'
    body += detail("resumen-fuentes", "Fuentes del resumen", "Descripción y tecnología principal", '<p>' + h(v["description"]) + '</p><p>' + summary_sources + '</p>' + link("introduccion", "← Volver al resumen"))
    flow_sources = ''.join('<p><b>' + h(x["nombre"]) + '</b> · ' + sources(x, snapshot) + '</p>' for x in v["flow"].get("componentes", []))
    flow_sources += ''.join('<p>' + h(x["descripcion"]) + ' · ' + h(x["estado"]) + ' · ' + sources(x, snapshot) + '</p>' for x in v["flow"].get("conexiones", []))
    body += detail("flujo-fuentes", "Fuentes del flujo actual", "Componentes, conexiones y certeza", (flow_sources or '<p>No se aportó flujo estructurado.</p>') + link("situacion-actual", "← Volver al flujo"))
    body += detail("controles", "Resultado de la revisión por dominio", "Riesgos, defensas observadas y controles no evaluados", table(["Dominio", "Estado", "Resultado y fuentes"], [[h(CONTROLS[c["id"]]), h(CONTROL_STATES[c["estado"]]), h(c["motivo"]) + '<p>' + sources(c, snapshot) + '</p>'] for c in data.get("controles", [])]) + link("controles-objetivo", "← Volver a mejoras"))
    proposal = v["azure"]
    delivery = '<p>No se aportó una propuesta Azure.</p>'
    if proposal:
        delivery = '<h3>Supuestos por comprobar</h3><ul>' + ''.join('<li>' + h(x) + '</li>' for x in proposal["supuestos"]) + '</ul><h3>Preparación y entrega de una versión</h3><ol class="plain-steps">' + ''.join('<li>' + h(x) + '</li>' for x in proposal["pasos"]) + '</ol><h3>Antes de aceptar la propuesta</h3><ul>' + ''.join('<li>' + h(x) + '</li>' for x in proposal["pendientes"]) + '</ul><p>Base técnica que motiva la recomendación: ' + sources(proposal, snapshot) + '</p><p>Las fuentes respaldan los componentes leídos; no demuestran compatibilidad ni despliegue en Azure.</p>'
    body += detail("entrega", "Cómo preparar, instalar y recuperar en Azure", "Propuesta y vuelta atrás", delivery + link("azure", "← Volver a la arquitectura propuesta"))
    actions = [[h(CONTROLS.get(x.get("control"), "Sin dominio asignado")) + ' · ' + link(x["id"], x["id"]), h(x["accion"]), h(x["pendiente"])] for x in v["entries"]]
    body += detail("controles-objetivo", "Controles y mejoras", "Acciones aportadas, sin completar dominios por deducción", table(["Dominio / riesgo", "Acción propuesta", "Cómo comprobarlo"], actions))
    extra = [[h(section), h(x["observacion"]), h(x["importancia"]) + '<p>' + h(x["pendiente"]) + '</p>', sources(x, snapshot)] for section in ("confirmados", "indicios") for x in data.get(section, []) if x.get("severidad", "informativa") == "informativa" and not x.get("componente")]
    body += '<section id="resultados-core">' + detail("aportaciones", "Observaciones y fuentes completas", "Contexto y pendientes originales", table(["Certeza", "Observación original", "Implicación y pendiente", "Fuentes"], extra)) + '</section>'
    if data.get("sintesis"):
        content = ''.join('<p>' + h(item["certeza"]) + ' · ' + h(item["texto"]) + ' · ' + references(item, snapshot) + '</p>' for item in data["sintesis"])
        body += detail("sintesis", "Síntesis del coordinador", "Interpretación con IA sobre aportaciones validadas; originales conservados", content)
    from arktic_office.core.outcome import notice
    message, questions, unknown = notice(data)
    closing = '<p>' + h(message) + '</p>'
    if unknown:
        closing += paragraph("Dominios pendientes:", ', '.join(CONTROLS[x] for x in unknown))
    body += detail("resultado-lectura", "Resultado y siguiente paso", "Alcance y próximas verificaciones", closing)
    body += detail("preguntas", "Verificaciones pendientes", "Información para la evaluación humana", '<ul>' + ''.join('<li>' + h(q) + '</li>' for q in questions) + '</ul>')
    coverage = '<p>Perfil acotado inspirado en OWASP ASVS 5.0.0 y Top 10:2025; los dominios son una agrupación de Arktic. No hay certificación ni porcentaje de cumplimiento.</p>'
    coverage += paragraph("Origen", snapshot.get("evidence_origin", snapshot["repository"])) + paragraph("Rama y commit", str(snapshot.get("branch", "No registrado")) + ' · ' + str(snapshot.get("commit", "No registrado")))
    coverage += paragraph("Estado del equipo", "Resultado parcial" if data.get("estado") == "parcial" else data.get("estado", "No registrado"))
    if data.get("coordination"):
        coverage += paragraph("Coordinación con IA", ' · '.join(name + ': ' + stage["status"] for name, stage in data["coordination"]["stages"].items()) + '. Consumo y fallos en coordinacion.json; sin reintentos.')
    from arktic_office.preparation.coverage import notes
    coverage += ''.join('<p>' + h(note) + '</p>' for note in notes(snapshot))
    if data.get("estandar_editorial"):
        coverage += paragraph("Estándar editorial utilizado", data["estandar_editorial"]["archivo"] + ' · versión ' + str(data["estandar_editorial"]["version"]))
    coverage += table(["Célula", "Estado", "Modelo / razonamiento", "Resultado o incidencia"], [[h(c.get("nombre", c.get("id", ""))), h(c["estado"]), h(c.get("model", "")) + ' / ' + h(c.get("reasoning", "")), h(c.get("error") or c.get("mensaje", "—"))] for c in data.get("celulas", [])])
    if data.get("coverage"):
        coverage += table(["Célula", "Ejecución", "Cobertura", "Motivo / carencias"], [[h(c.get("nombre", c["id"])), h(c.get("execution", c["estado"])), h(c.get("coverage", "insufficient")), h(c.get("reason", c.get("mensaje", ""))) + " · " + h("; ".join(c.get("missing", c.get("necesita", []))))] for c in data.get("celulas", [])])
    for tool in data.get("scanners", []):
        coverage += '<h4>' + h(tool["name"]) + ' · ' + h(tool["status"]) + '</h4><p>' + h(tool["detail"]) + '</p><ul>' + ''.join('<li>' + h(f.get("summary", "")) + ' · ' + h(f.get("path", "")) + '</li>' for f in tool.get("findings", [])) + '</ul>'
    coverage += '<p>No se ejecutó la aplicación ni se comprobaron acceso real, credenciales válidas, consumo o restauración. Ausencia de hallazgos no acredita seguridad.</p><h4>Archivos seleccionados</h4><ul>' + ''.join('<li>' + h(f["path"]) + (' · extractos; líneas omitidas' if f.get("partial") else '') + '</li>' for f in snapshot.get("files", [])) + '</ul><h4>Exclusiones</h4><ul>' + ''.join('<li>' + h(f["path"]) + ' · ' + h(f["reason"]) + '</li>' for f in snapshot.get("excluded", [])) + '</ul>'
    coverage += '<p>Las citas se contrastan con la evidencia, no con la verdad de la interpretación. Las aportaciones contradictorias requieren revisión humana.</p>'
    body += detail("cobertura", "Marco de seguridad, cobertura y límites", "Origen, fallos y comprobaciones automáticas", coverage)
    from arktic_office.reporting.questionnaire_view import html as questionnaire_html, deterministic_html
    body += questionnaire_html(data, snapshot) + deterministic_html(data)
    return chapter("anexos", "04", "Fuentes y comprobaciones", "Anexos", "Explicaciones completas y comprensibles; terminología y resultado original en un segundo nivel.", body)

def render_markdown(data, snapshot, model=""):
    if data.get('cuestionario'):
        from arktic_office.reporting.reading import render_markdown as reading_markdown
        return reading_markdown(data, snapshot, model)
    v = view(data, snapshot)
    lines = ['# Informe para evaluación humana · Arktic', '', '**FUENTES FICTICIAS · consultar origen de los resultados.**' if snapshot.get("simulation") else 'Lectura estática; la evaluación y la decisión corresponden al arquitecto.', '', text(snapshot.get("evidence_origin", snapshot["repository"])), '', '## 1. Resumen del informe', '', text(v["description"])]
    from arktic_office.core.outcome import notice
    message, needs, unknown = notice(data)
    for item in summary_findings(data):
        lines += ['', '**' + ('Indicio' if item["certeza"] == "indicios" else 'Observado') + ':** ' + text(item["observacion"])]
        if item.get("severidad", "informativa") != "informativa":
            lines += ['Implicación: ' + text(item["importancia"]), 'Condiciones: ' + text(item["condiciones"])]
        lines += ['Fuentes: ' + references({**item, 'evidencia': item.get('evidencia', [])[:3]} if uses_compact_contract(data) else item, snapshot)]
    if v["summary"].get("tecnologia_principal"):
        lines += ['', 'Tecnología principal: ' + text(v["summary"]["tecnologia_principal"])]
    if v["summary"]:
        lines += ['', 'Fuentes del resumen: ' + references(v["summary"], snapshot)]
    lines += ['', '## 2. Diagnóstico y riesgos', '', '### Flujo actual de la aplicación', '']
    flow = v["flow"]
    for node in flow.get("componentes", []):
        lines.append('- ' + text(node["nombre"] + ': ' + node["descripcion"]) + ' · ' + references(node, snapshot))
    for edge in flow.get("conexiones", []):
        lines.append('- ' + text(f'{edge["origen"]} → {edge["destino"]} · {edge["estado"]}: {edge["descripcion"]}') + ' · ' + references(edge, snapshot))
    if not flow.get("componentes"):
        lines.append('Conexiones no estructuradas en este resultado; no se completa el flujo por deducción.')
    lines += ['', '### Riesgos', '', '| Riesgo | Gravedad | Certeza |', '|---|---|---|']
    for x in v["entries"]:
        lines.append(f'| [{x["id"]} · {text(x.get("titulo", x["observacion"]))}](#{x["id"].lower()}) | {GRAVITY[x["severidad"]][0]} | {"Observado" if x["certeza"] == "confirmados" else "Indicio por confirmar"} |')
    if not v["entries"]:
        lines += ['', 'No se aportaron riesgos clasificables; esto no acredita seguridad.']
    lines += ['', 'Recuento de observados: ' + ' · '.join(f'{GRAVITY[s][0]}: **{sum(x["severidad"] == s for x in v["observed"])}**' for s in SEVERITIES[:-1]), '', f'{len(v["pending"])} indicios de riesgo por confirmar.']
    lines += ['', '### Qué pudo evaluar Seguridad', '', '| Dominio | Resultado de la lectura | Evidencia y pendiente |', '|---|---|---|']
    for c in (c for c in data.get("controles", []) if c["estado"] != "no_evaluado"):
        lines.append(f'| {CONTROLS[c["id"]]} | {CONTROL_STATES[c["estado"]]} | {text(c["motivo"])} · {references(c, snapshot)} |')
    lines += ['', '### Base de datos y recuperación', '', '| Aspecto | Estado identificado | Pendiente | Fuente |', '|---|---|---|---|']
    for row in (r for r in v["operations"] if r["estado"] != "no_evaluado"):
        lines.append(f'| {ASPECTS[row["aspecto"]]} | {text(row["estado"] + ": " + row["descripcion"])} | {text(row["pendiente"])} | {references(row, snapshot)} |')
    if uses_compact_contract(data):
        lines += ['', '### Información identificada en las fuentes', '']
        for section in ('confirmados', 'indicios'):
            for item in data.get(section, []):
                if item.get('severidad') == 'informativa' and not item.get('componente'):
                    lines += ['- ' + text(section + ': ' + item['observacion']) + ' · ' + references(item, snapshot)]
    lines += ['', '## 3. Mejoras propuestas', '', '### Controles y mejoras', '', '| Dominio / riesgo | Acción propuesta | Resultado esperado (por verificar) | Cómo comprobarlo |', '|---|---|---|---|']
    for x in v["entries"]:
        lines.append(f'| {CONTROLS.get(x["control"], x["control"])} · {x["id"]} | {text(x["accion"])} | {text(x.get("resultado_esperado", "Objetivo no explicitado en el resultado."))} | {text(x["pendiente"])} |')
    lines += ['', '### Arquitectura propuesta en Azure', '']
    p = v["azure"]
    if p:
        from arktic_office.reporting.azure_proposal import TARGETS
        lines += ['Recomendación preliminar; compatibilidad y despliegue no validados.', '', '**Opción principal:** ' + TARGETS[p["destino"]], '', text(p["resumen"]), '', '**Justificación:** ' + text(p["justificacion"]), '', 'Base técnica: ' + references(p, snapshot), '', '| Servicio | Función propuesta | Categoría |', '|---|---|---|']
        for s in p["servicios"]:
            lines.append(f'| {text(s["servicio"])} | {text(s["uso"])} | {CATEGORIES.get(s.get("categoria"), "Sin categoría estructurada")} |')
        for edge in p.get("conexiones", []):
            lines += ['', text(f'{p["servicios"][edge["origen"] - 1]["servicio"]} → {p["servicios"][edge["destino"] - 1]["servicio"]}: {edge["descripcion"]}')]
        for field, label in (("supuestos", "Supuestos"), ("pasos", "Preparación y entrega"), ("pendientes", "Validaciones pendientes")):
            lines += ['', '**' + label + '**', ''] + ['- ' + text(x) for x in p[field]]
    else:
        lines.append('No disponible en esta revisión; no se añade una recomendación a informes anteriores.')
    lines += ['', '### Decisión y siguientes pasos', '', text(v["decision"].get("propuesta", "No se aportó una decisión propuesta.")), '', text(v["decision"].get("siguiente_paso", "Completar la información pendiente y revisar los resultados."))] + ['- ' + text(x) for x in v["decision"].get("evidencia_pendiente", [])]
    if uses_compact_contract(data):
        lines += ['', '## 4. Anexos', '', '### Observaciones y fuentes completas', '']
        for section in ('confirmados', 'indicios'):
            for item in data.get(section, []):
                lines += ['- ' + text(section + ': ' + item['observacion']), '  Fuentes: ' + references(item, snapshot)]
    lines += ['', 'Inventario y detalle' if uses_compact_contract(data) else '## 4. Anexos', '', '### Inventario', '', '| Componente | Tecnología y versión declarada | Función | Certeza / fuente |', '|---|---|---|---|']
    for x in v["components"]:
        c = x["componente"]
        lines.append(f'| {text(c["nombre"])} | {text(c["tecnologia"])} | {text(c["funcion"])} | {x["certeza"]} · {references(x, snapshot)} |')
    for x in v["entries"]:
        lines += ['', '### ' + x["id"], '', '**' + text(x.get("titulo", x["observacion"])) + '**', '', f'Gravedad: {GRAVITY[x["severidad"]][0]} · Certeza: {x["certeza"]}']
        for label, field in (("Qué encontramos", "observacion"), ("Qué podría pasar", "importancia"), ("De qué depende", "condiciones"), ("Qué cambiar", "accion"), ("Cómo comprobarlo", "pendiente")):
            lines += ['', '**' + label + ':** ' + text(x[field])]
        if x.get("por_confirmar"):
            lines += ['', '**Por confirmar:** ' + text(x["por_confirmar"])]
        lines += ['', 'Fuentes: ' + references(x, snapshot), '', '**Terminología técnica:** ' + text(x.get("detalle_tecnico", "Sin detalle adicional; se conserva la observación original."))]
        lines += ['', 'Aportaciones originales:', '']
        for original in x.get("aportaciones", [{"celula": ", ".join(x.get("celulas", [])), "resultado": x}]):
            lines.append('- ' + text(original["celula"] + ': ' + original["resultado"]["observacion"]))
            for ref in original["resultado"].get("evidencia", []):
                lines.append('  - ' + text(f'{ref["path"]}:{ref["line"]} · {ref["quote"]}'))
        lines += ['', '[Volver al diagnóstico](#riesgos)']
    lines += ['', '### Resultado y siguiente paso', '', text(message)]
    if unknown:
        lines += ['', 'Evaluación pendiente en: ' + text(', '.join(CONTROLS[x] for x in unknown)) + '.']
    lines += ['', '### Verificaciones pendientes', ''] + ['- ' + text(q) for q in needs]
    lines += ['', '### Otras aportaciones originales', '']
    for section in ("confirmados", "indicios"):
        for x in data.get(section, []):
            if x.get("severidad") == "informativa":
                lines += ['- ' + text(section + ': ' + x["observacion"]) + ' · ' + references(x, snapshot)]
    lines += ['', '### Cobertura y límites', '', 'Estado del equipo: ' + data.get("estado", "No registrado"), '', 'Perfil acotado inspirado en OWASP ASVS 5.0.0 y Top 10:2025. Sin certificación ni porcentaje de cumplimiento. La aplicación no se ejecutó; acceso real, credenciales, consumo y restauración no se comprobaron.']
    from arktic_office.preparation.coverage import notes
    lines += ['- ' + text(note) for note in notes(snapshot)]
    if data.get("coordination"):
        lines += ['- Coordinación con IA: ' + text(' · '.join(name + ': ' + stage["status"] for name, stage in data["coordination"]["stages"].items())) + '. Consumo y fallos en coordinacion.json.']
    for item in data.get("sintesis", []):
        lines += ['- Síntesis del coordinador (' + text(item["certeza"]) + '): ' + text(item["texto"]) + ' · ' + references(item, snapshot)]
    lines += ['', 'Rama: ' + text(snapshot.get("branch", "No registrada")) + ' · Commit: ' + text(snapshot.get("commit", "No registrado")), '', '| Dominio | Estado | Resultado / fuentes |', '|---|---|---|']
    for c in data.get("controles", []):
        lines.append(f'| {CONTROLS[c["id"]]} | {CONTROL_STATES[c["estado"]]} | {text(c["motivo"])} · {references(c, snapshot)} |')
    for c in data.get("celulas", []):
        lines.append('- ' + text(c.get("nombre", c.get("id", "")) + ': ' + c["estado"] + ' · ' + c.get("error", "")))
    if data.get("coverage"):
        for c in data.get("celulas", []):
            lines.append("- " + text(c["id"] + ": ejecución=" + c.get("execution", c["estado"]) + "; cobertura=" + c.get("coverage", "insufficient") + "; " + c.get("reason", c.get("mensaje", "")) + "; falta: " + "; ".join(c.get("missing", c.get("necesita", [])))))
    for tool in data.get("scanners", []):
        lines += ['- ' + text(tool["name"] + ': ' + tool["status"] + ' · ' + tool["detail"])] + ['  - ' + text(x.get("summary", "") + ' · ' + x.get("path", "")) for x in tool.get("findings", [])]
    lines += ['- Archivo: ' + text(f["path"]) + (' · extractos; líneas omitidas' if f.get("partial") else '') for f in snapshot.get("files", [])]
    lines += ['- Excluido: ' + text(f["path"] + ' · ' + f["reason"]) for f in snapshot.get("excluded", [])]
    from arktic_office.reporting.compact import compact_markdown
    from arktic_office.reporting.questionnaire_view import markdown as questionnaire_markdown
    return compact_markdown('\n'.join(lines) + '\n', v) + questionnaire_markdown(data, snapshot)
