"""Reference-v12 layout over validated records; no semantic rewriting or model calls."""
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
    description = summary.get("descripcion") or (purpose["observacion"] if purpose else "Hipótesis por confirmar: " + tentative["observacion"] + " Falta información para confirmar su alcance." if tentative else "No he podido determinar con suficiente fundamento qué hace la aplicación. Hace falta una lectura más profunda de su código y configuración.")
    rows = {x["aspecto"]: x for x in info.get("estado_operativo", [])}
    operations = [{"aspecto": key, "estado": "no_evaluado", "descripcion": "Sin dato estructurado para este aspecto.", "pendiente": NEXT[key], "evidencia": [], **rows.get(key, {})} for key in ASPECTS]
    return {"data": data, "snapshot": snapshot, "entries": entries, "observed": observed, "pending": pending,
            "description": description, "summary": summary, "purpose": purpose or tentative, "operations": operations, "components": components(data), "flow": info.get("flujo_actual", {}), "decision": info.get("decision", {}), "azure": data.get("propuesta_azure")}

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
    v = view(data, snapshot)
    css = (ASSETS / "report-v12.css").read_text(encoding="utf-8")
    logo = 'data:image/png;base64,' + base64.b64encode((ASSETS / "arktic-logo.png").read_bytes()).decode()
    simulation = bool(snapshot.get("simulation"))
    title = snapshot.get("project_name") or snapshot["repository"].rstrip('/').split('/')[-1]
    state = "Simulación" if simulation else "Información insuficiente" if data.get("estado") == "informacion_insuficiente" else "Células completadas; lectura parcial" if data.get("estado") == "completo" else "Resultado parcial: revisar alcance y resultados"
    banner = '<div class="demo"><div class="wrap"><strong>' + ('EJEMPLO FICTICIO' if simulation else 'REVISIÓN PRELIMINAR') + '</strong>' + h(snapshot.get("evidence_origin") or "Hallazgos y recomendaciones para evaluación humana; fuentes al commit revisado.") + '</div></div>'
    hero = f'<header class="hero"><div class="hero-art" aria-hidden="true"></div><div class="wrap"><div class="brand-row"><img class="corporate-logo" src="{logo}" alt="Arktic"></div><h1>{h(title)}</h1><p>Evaluación preliminar de la aplicación, sus riesgos y las condiciones para incorporarla a TI.</p><div class="meta"><span>{h(state)}</span><span>{h(display_date(snapshot.get("analyzed_at")))}</span><span>Decisión del arquitecto pendiente</span></div></div></header>'
    nav = '<nav class="nav" aria-label="Hilo conductor del informe"><div class="wrap">' + ''.join(f'<a href="#{key}"><b>{i:02}</b>{name}</a>' for i, (key, name) in enumerate((("introduccion", "Resumen del informe"), ("situacion-actual", "Diagnóstico y riesgos"), ("situacion-objetivo", "Mejoras propuestas"), ("anexos", "Anexos")), 1)) + '</div></nav>'
    about = '<div class="grid two"><div class="panel"><div class="eyebrow">Aplicación analizada</div><h3>Qué hace y con qué tecnología</h3><p class="appdesc">' + h(v["description"]) + '</p>'
    if v["summary"].get("tecnologia_principal"):
        about += paragraph("Tecnología principal:", v["summary"]["tecnologia_principal"])
    about += link("inventario", "Consultar inventario y fuentes →", "back") + ' ' + link("resumen-fuentes", "Fuentes del resumen", "back") + '</div><div class="panel"><div class="eyebrow">Contenido del informe</div><h3>Diagnóstico, mejoras y evidencia</h3><div class="report-contents">'
    for key, label, desc in (("situacion-actual", "Diagnóstico y riesgos", "Funcionamiento, seguridad y continuidad."), ("situacion-objetivo", "Mejoras propuestas", "Controles, propuesta Azure y condiciones para decidir."), ("anexos", "Anexos técnicos", "Hallazgos, fuentes y comprobaciones completas.")):
        about += f'<a href="#{key}"><b>{label}</b><span>{desc}</span></a>'
    about += '</div></div></div>'
    from arktic_office.core.outcome import notice
    message, needs, unknown = notice(data)
    conclusion = '<section id="resultado-lectura" class="panel margin-top"><h3>Resultado y siguiente paso</h3><p>' + h(message) + '</p>'
    if unknown:
        conclusion += '<p>Evaluación pendiente en: ' + h(', '.join(CONTROLS[x] for x in unknown)) + '.</p>'
    if needs:
        conclusion += '<h4>Información que falta para avanzar</h4><ul>' + ''.join('<li>' + h(x) + '</li>' for x in needs[:3]) + '</ul>' + link('preguntas', 'Consultar todas las preguntas y necesidades →')
    conclusion += '</section>'
    intro = chapter("introduccion", "01", "Contexto", "Resumen del informe", "Lo que permite concluir la evidencia seleccionada y lo que hace falta para avanzar.", about + conclusion)
    operation = '<div class="panel operation"><div class="eyebrow">Componentes y comunicación</div><h2>Flujo actual de la aplicación</h2>' + flow_html(v["flow"], snapshot) + '<div class="operation-status">'
    for key in ("disponibilidad", "capacidad"):
        row = next(x for x in v["operations"] if x["aspecto"] == key)
        operation += '<span><strong>' + ASPECTS[key] + ':</strong> ' + h(row["descripcion"]) + ' ' + link("datos-operacion", "Ver estado y pendientes") + '</span>'
    operation += '</div></div>'
    security = '<section id="seguridad" class="section"><div class="heading-row"><div><div class="eyebrow">2.1 / Ciberseguridad</div><h2>Qué podría ocurrir con la información</h2><p class="sub">' + str(len(v["observed"])) + (' riesgos representados en fuentes ficticias.' if simulation else ' riesgos observados en archivos seleccionados; su explotación no está comprobada.') + '</p></div>' + link("registro", "Ver todos los riesgos y sus evidencias →") + '</div><div class="stats">'
    for key in SEVERITIES[:-1]:
        label, _, cls = GRAVITY[key]
        security += f'<div class="stat {cls}"><strong>{sum(x["severidad"] == key for x in v["observed"])}</strong><span>{label}</span><small>Observados en el alcance leído</small></div>'
    security += '</div><div class="clues">' + h(f'{len(v["pending"])} indicios por confirmar · {sum(c["estado"] == "no_evaluado" for c in data.get("controles", []))} dominios no evaluados.') + ' ' + link("indicios", "Ver qué falta comprobar →") + '</div><div class="grid three margin-top">'
    for item in v["entries"][:3]:
        security += f'<article id="destacado-{item["id"]}" class="risk-card risk {item["severidad"]} {"confirmed" if item["certeza"] == "confirmados" else "pending"}"><div class="tags">' + badges(item, snapshot) + '</div><h3>' + h(item.get("titulo", item["observacion"])) + '</h3>' + paragraph("Qué encontramos.", item["observacion"]) + paragraph("Qué podría pasar.", item["importancia"]) + '<p class="condition"><strong>Condiciones.</strong> ' + h(item["condiciones"]) + '</p>' + link(item["id"], "Explicación completa y comprobaciones →") + '</article>'
    security += '</div>'
    security_cell = next((c for c in data.get("celulas", []) if c.get("id") == "security"), {})
    security += '<div class="panel margin-top"><h3>Qué pudo evaluar Seguridad</h3><p>Estado: ' + h(security_cell.get("estado", "No registrado")) + ' · ' + str(len(security_cell.get("archivos", []))) + ' archivos enviados a esta célula.</p>'
    security += table(["Dominio", "Resultado de la lectura", "Evidencia y pendiente"], [[h(CONTROLS[c["id"]]), h(CONTROL_STATES[c["estado"]]), h(c["motivo"]) + '<p>' + sources(c, snapshot) + '</p>'] for c in data.get("controles", []) if c["estado"] != "no_evaluado"])
    security += link("controles", "Ver cobertura completa, scanners y archivos →") + '</div>'
    risk_rows = []
    for item in v["entries"]:
        risk_rows.append([f'<span id="resumen-{item["id"]}"></span>' + link(item["id"], item.get("titulo", item["observacion"])), badges(item, snapshot), h(item["condiciones"])])
    security += '<div id="riesgos-resumen" class="panel margin-top"><h3>Registro resumido de riesgos</h3>' + table(["Qué preocupa", "Gravedad y certeza", "De qué depende"], risk_rows, [f'risk {x["severidad"]} {"confirmed" if x["certeza"] == "confirmados" else "pending"}' for x in v["entries"]]) + link("controles-objetivo", "Ver controles propuestos →", "back") + '</div></section>'
    op_rows = [[h(ASPECTS[r["aspecto"]]), '<span class="tag neutral">' + h(r["estado"]) + '</span><p>' + h(r["descripcion"]) + '</p>', h(r["pendiente"]) + ' ' + link("datos-operacion", "Ver fuentes")] for r in v["operations"] if r["aspecto"] not in {"disponibilidad", "capacidad"} and r["estado"] != "no_evaluado"]
    database = '<section id="continuidad" class="section panel"><div class="eyebrow">2.2 / Almacenamiento y recuperación</div><h2>Base de datos y recuperación</h2>' + table(["Aspecto", "Estado identificado", "Pendiente"], op_rows) + '</section>'
    current = chapter("situacion-actual", "02", "Funcionamiento y principales riesgos", "Diagnóstico y riesgos", "Lo observado, sus posibles consecuencias y lo que todavía debe confirmarse.", operation + security + database)
    control_rows = []
    for key, name in CONTROLS.items():
        items = [x for x in v["entries"] if x.get("control") == key]
        if items:
            for x in items:
                control_rows.append([h(name) + '<p>' + link(x["id"], x.get("titulo", x["observacion"])) + '</p>', h(x["accion"]), h(x.get("resultado_esperado", "Objetivo de aceptación no explicitado en el resultado; debe concretarlo el responsable técnico.")), h(x["pendiente"]) + ' ' + link(x["id"], "Ver respaldo")])
    controls = '<section id="controles-objetivo" class="section panel"><div class="eyebrow">3.1 / Seguridad propuesta</div><h2>Controles y mejoras</h2><p class="sub">Acciones organizadas por dominios OWASP del perfil Arktic. Los resultados esperados son objetivos pendientes de comprobar.</p>' + table(["Problema y dominio", "Acción propuesta", "Resultado esperado", "Cómo comprobarlo"], control_rows) + '</section>'
    azure = azure_html(v)
    decision = v["decision"]
    pending_rows = [[h(q), "Revisión humana del alcance y de la evidencia antes de decidir."] for q in decision.get("evidencia_pendiente", [])]
    acceptance = '<section id="aceptacion" class="section panel"><div class="eyebrow">3.3 / Condiciones de aceptación</div><h2>Evidencia pendiente para decidir</h2>' + table(["Qué falta aportar", "Para qué se revisa"], pending_rows) + '</section>'
    decision_block = '<section id="decision" class="decision"><div><div class="eyebrow">3.4 / Decisión propuesta al arquitecto</div><h2>' + h(decision.get("propuesta", "No se aportó una decisión propuesta en este resultado.")) + '</h2><p>La recomendación requiere evaluación y decisión humana.</p></div><div class="aside"><h3>Siguiente paso</h3><p>' + h(decision.get("siguiente_paso", "Completar las preguntas y revisar los resultados antes de acordar el siguiente paso.")) + '</p>' + link("anexos", "Consultar anexos →") + '</div></section>'
    target = chapter("situacion-objetivo", "03", "Controles y operación propuesta", "Mejoras propuestas", "Acciones respaldadas por el diagnóstico, propuesta de alojamiento y evidencia para la evaluación humana.", controls + azure + acceptance + decision_block)
    annex = annex_html(v)
    footer = f'<footer><div class="corporate-footer"><span>ARKTIC OFFICE / TECNOLOGÍA Y CIBERSEGURIDAD</span><img class="footer-logo" src="{logo}" alt="Arktic"></div><p>La evaluación y la decisión corresponden al arquitecto. {"Ejemplo completamente ficticio; sin llamadas a modelos." if simulation else "Lectura estática parcial con evidencia guardada."}</p></footer>'
    script = (ASSETS / "report-navigation.js").read_text(encoding="utf-8")
    extra = '.connection{border-left:3px solid #41c0cf;padding:12px;margin:10px 0}.connection.inferida{border-left-style:dashed}.connection.desconocida{border-left-style:dotted}.connection .arrow{padding:0 12px;display:inline-block!important}.connection p{font-size:12px;margin:5px 0 0}.proposal-lanes{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.proposal-lane{border:1px dashed #008ad8;padding:14px;border-radius:5px}.source pre{white-space:pre-wrap;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}.risk-detail{border-left:3px solid #dce5ec;padding-left:16px}#registro .risk-detail,#indicios .risk-detail{margin-top:12px}[id]{scroll-margin-top:115px}.risk-meta+h3{display:block}.hero h1{overflow-wrap:anywhere}.tag{white-space:normal}.risk-card.alta{border-top-color:var(--high)}.risk-card.media{border-top-color:var(--medium)}.risk-card.baja{border-top-color:var(--low)}.flow>.arrow{display:block!important;text-align:center}.arrow small{display:block;font-size:9px}'
    from arktic_office.reporting.compact import compact_html
    return compact_html('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + h(title) + ' · Informe Arktic</title><style>' + css + extra + '</style></head><body>' + banner + hero + nav + '<main class="wrap">' + intro + current + target + annex + footer + '</main><script id="arktic-report-navigation">' + script + '</script></body></html>', v)

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
    body = detail("registro", "Registro de riesgos observados", f'{len(v["observed"])} riesgos', ''.join(risk_detail(x) for x in v["observed"]) or '<p>No hay riesgos observados en el alcance guardado.</p>')
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
    body += detail("controles", "Resultado de la revisión por dominio", "Qué se observó; pendientes en el resumen", table(["Dominio", "Estado", "Resultado y fuentes"], [[h(CONTROLS[c["id"]]), h(CONTROL_STATES[c["estado"]]), h(c["motivo"]) + '<p>' + sources(c, snapshot) + '</p>'] for c in data.get("controles", []) if c["estado"] != "no_evaluado"]) + link("controles-objetivo", "← Volver a mejoras"))
    proposal = v["azure"]
    delivery = '<p>No se aportó una propuesta Azure.</p>'
    if proposal:
        delivery = '<h3>Supuestos por comprobar</h3><ul>' + ''.join('<li>' + h(x) + '</li>' for x in proposal["supuestos"]) + '</ul><h3>Preparación y entrega de una versión</h3><ol class="plain-steps">' + ''.join('<li>' + h(x) + '</li>' for x in proposal["pasos"]) + '</ol><h3>Antes de aceptar la propuesta</h3><ul>' + ''.join('<li>' + h(x) + '</li>' for x in proposal["pendientes"]) + '</ul><p>Base técnica que motiva la recomendación: ' + sources(proposal, snapshot) + '</p><p>Las fuentes respaldan los componentes leídos; no demuestran compatibilidad ni despliegue en Azure.</p>'
    body += detail("entrega", "Cómo preparar, instalar y recuperar en Azure", "Propuesta y vuelta atrás", delivery + link("azure", "← Volver a la arquitectura propuesta"))
    extra = []
    for section in ("confirmados", "indicios"):
        for x in data.get(section, []):
            if x.get("severidad") == "informativa":
                extra.append([h(section), h(x["observacion"]), h(x["importancia"]) + '<p>' + h(x["pendiente"]) + '</p>', sources(x, snapshot)])
    body += detail("aportaciones", "Otras aportaciones de las células", "Contexto, observaciones y pendientes originales", table(["Certeza", "Observación original", "Implicación y pendiente", "Fuentes"], extra))
    from arktic_office.core.outcome import notice
    _, questions, _ = notice(data)
    body += detail("preguntas", "Preguntas pendientes", "Información para la evaluación humana", '<ul>' + ''.join('<li>' + h(q) + '</li>' for q in questions) + '</ul>')
    coverage = '<p>Perfil acotado inspirado en OWASP ASVS 5.0.0 y Top 10:2025; los dominios son una agrupación de Arktic. No hay certificación ni porcentaje de cumplimiento.</p>'
    coverage += paragraph("Origen", snapshot.get("evidence_origin", snapshot["repository"])) + paragraph("Rama y commit", str(snapshot.get("branch", "No registrado")) + ' · ' + str(snapshot.get("commit", "No registrado")))
    coverage += paragraph("Estado del equipo", data.get("estado", "No registrado"))
    if data.get("estandar_editorial"):
        coverage += paragraph("Estándar editorial utilizado", data["estandar_editorial"]["archivo"] + ' · versión ' + str(data["estandar_editorial"]["version"]))
    coverage += table(["Célula", "Estado", "Modelo / razonamiento", "Resultado o incidencia"], [[h(c.get("nombre", c.get("id", ""))), h(c["estado"]), h(c.get("model", "")) + ' / ' + h(c.get("reasoning", "")), h(c.get("error") or c.get("mensaje", "—"))] for c in data.get("celulas", [])])
    for tool in data.get("scanners", []):
        coverage += '<h4>' + h(tool["name"]) + ' · ' + h(tool["status"]) + '</h4><p>' + h(tool["detail"]) + '</p><ul>' + ''.join('<li>' + h(f.get("summary", "")) + ' · ' + h(f.get("path", "")) + '</li>' for f in tool.get("findings", [])) + '</ul>'
    coverage += '<p>No se ejecutó la aplicación ni se comprobaron acceso real, credenciales válidas, consumo o restauración. Ausencia de hallazgos no acredita seguridad.</p><h4>Archivos seleccionados</h4><ul>' + ''.join('<li>' + h(f["path"]) + (' · extractos; líneas omitidas' if f.get("partial") else '') + '</li>' for f in snapshot.get("files", [])) + '</ul><h4>Exclusiones</h4><ul>' + ''.join('<li>' + h(f["path"]) + ' · ' + h(f["reason"]) + '</li>' for f in snapshot.get("excluded", [])) + '</ul>'
    coverage += '<p>Las citas se contrastan con la evidencia, no con la verdad de la interpretación. Las aportaciones contradictorias requieren revisión humana.</p>'
    body += detail("cobertura", "Marco de seguridad, cobertura y límites", "Origen, fallos y comprobaciones automáticas", coverage)
    return chapter("anexos", "04", "Fuentes y comprobaciones", "Anexos", "Explicaciones completas y comprensibles; terminología y resultado original en un segundo nivel.", body)

def render_markdown(data, snapshot, model=""):
    v = view(data, snapshot)
    lines = ['# Informe para evaluación humana · Arktic', '', '**EJEMPLO FICTICIO · sin agentes ni análisis reales.**' if snapshot.get("simulation") else 'Lectura estática parcial; la evaluación y la decisión corresponden al arquitecto.', '', text(snapshot.get("evidence_origin", snapshot["repository"])), '', '## 1. Resumen del informe', '', text(v["description"])]
    from arktic_office.core.outcome import notice
    message, needs, unknown = notice(data)
    lines += ['', '**Resultado y siguiente paso:** ' + text(message)]
    if unknown:
        lines += ['', 'Evaluación pendiente en: ' + text(', '.join(CONTROLS[x] for x in unknown)) + '.']
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
    lines += ['', '## 4. Anexos', '', '### Inventario', '', '| Componente | Tecnología y versión declarada | Función | Certeza / fuente |', '|---|---|---|---|']
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
    lines += ['', '### Preguntas pendientes', ''] + ['- ' + text(q) for q in needs]
    lines += ['', '### Otras aportaciones originales', '']
    for section in ("confirmados", "indicios"):
        for x in data.get(section, []):
            if x.get("severidad") == "informativa":
                lines += ['- ' + text(section + ': ' + x["observacion"]) + ' · ' + references(x, snapshot)]
    lines += ['', '### Cobertura y límites', '', 'Estado del equipo: ' + data.get("estado", "No registrado"), '', 'Perfil acotado inspirado en OWASP ASVS 5.0.0 y Top 10:2025. Sin certificación ni porcentaje de cumplimiento. La aplicación no se ejecutó; acceso real, credenciales, consumo y restauración no se comprobaron.']
    lines += ['', 'Rama: ' + text(snapshot.get("branch", "No registrada")) + ' · Commit: ' + text(snapshot.get("commit", "No registrado")), '', '| Dominio | Estado | Resultado / fuentes |', '|---|---|---|']
    for c in (c for c in data.get("controles", []) if c["estado"] != "no_evaluado"):
        lines.append(f'| {CONTROLS[c["id"]]} | {CONTROL_STATES[c["estado"]]} | {text(c["motivo"])} · {references(c, snapshot)} |')
    for c in data.get("celulas", []):
        lines.append('- ' + text(c.get("nombre", c.get("id", "")) + ': ' + c["estado"] + ' · ' + c.get("error", "")))
    for tool in data.get("scanners", []):
        lines += ['- ' + text(tool["name"] + ': ' + tool["status"] + ' · ' + tool["detail"])] + ['  - ' + text(x.get("summary", "") + ' · ' + x.get("path", "")) for x in tool.get("findings", [])]
    lines += ['- Archivo: ' + text(f["path"]) + (' · extractos; líneas omitidas' if f.get("partial") else '') for f in snapshot.get("files", [])]
    lines += ['- Excluido: ' + text(f["path"] + ' · ' + f["reason"]) for f in snapshot.get("excluded", [])]
    from arktic_office.reporting.compact import compact_markdown
    return compact_markdown('\n'.join(lines) + '\n', v)
