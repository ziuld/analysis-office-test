"""Three-part reading layout over saved answers; no new model conclusions."""
import base64
import re
from arktic_office.resources.paths import resource_path
from arktic_office.reporting.questionnaire_view import compact_sources, deterministic_html

GROUPS = (
    ("aplicacion", "Aplicación, tecnologías e integraciones", (4, 5, 6, 7)),
    ("estructura", "Arquitectura y organización del código", (8, 9)),
    ("datos", "Datos, persistencia y recuperación", (10, 11, 12, 13)),
    ("operacion", "Construcción, arranque y despliegue", tuple(range(15, 23))),
    ("seguridad", "Seguridad y privacidad", (14, *range(23, 38))),
    ("alcance", "Prioridades, alcance y puntos sin comprobar", (1, 2, 3, 38, 39, 40)),
)
MAX_EXECUTIVE_RISKS = 10


def authors(item):
    from arktic_office.coordination.catalog import catalog
    names = {p['id']: p['person'] + ' · ' + p['name'] for p in catalog()}
    names['security'] = 'Seguridad (histórico)'
    return ', '.join(names.get(a, a) for a in item.get('celulas', [])) or 'Autor no registrado en el resultado guardado.'


def render_markdown(data, snapshot, model=''):
    from arktic_office.reporting.brief import text, references
    from arktic_office.reporting.executive import risks
    from arktic_office.reporting.questionnaire_view import markdown
    answers = {a['id']: a for a in data['cuestionario']['respuestas']}
    title = snapshot.get('project_name') or snapshot['repository'].rstrip('/').split('/')[-1]
    lines = ['# ' + text(title), '', 'Revisión estática · ' + text(snapshot.get('branch', '')) + ' · ' + text(snapshot['commit']), '', '## Resumen ejecutivo']
    for key in ('Q07', 'Q05', 'Q01'):
        a = answers.get(key)
        if a and a['estado'] != 'no_comprobado':
            lines += ['', text(a['respuesta']), '', 'Fuentes: ' + references(a, snapshot)]
    lines += ['', '### Principales riesgos identificados']
    selected = risks(data)[:MAX_EXECUTIVE_RISKS]
    if not selected:
        lines += ['', 'No se han identificado riesgos con evidencia suficiente en el alcance revisado. Esto no descarta problemas en los puntos que quedaron sin comprobar.']
    for n, item in enumerate(selected, 1):
        lines += ['', f'#### R{n:02} · ' + text(item.get('titulo') or item['observacion']), '', text(item['observacion'])]
        if item.get('tipo'):
            lines += ['', 'Tipo de riesgo: ' + {'coste':'Coste', 'vulnerabilidad':'Vulnerabilidad', 'operacion':'Operación'}[item['tipo']]]
        lines += ['', 'Autoría: ' + text(authors(item))]
        for label, field in (('Consecuencia posible', 'importancia'), ('De qué depende', 'condiciones'), ('Qué queda por comprobar', 'pendiente')):
            if item.get(field):
                lines += ['', label + ': ' + text(item[field])]
        lines += ['', 'Fuentes: ' + references(item, snapshot)]
    from arktic_office.reporting.originals import markdown as original_markdown
    return '\n'.join(lines) + '\n' + markdown(data, snapshot) + original_markdown(data)


def unreviewed_scope(data, snapshot):
    """Only observable omissions; unknown answers do not prove missing review."""
    items = []
    inventory = snapshot.get("inventory", [])
    texts = {f["path"] for f in inventory if f.get("kind") == "text"}
    cells = data.get("celulas", [])
    if texts and cells and all("archivos" in c for c in cells):
        supplied = {p for c in cells for p in c["archivos"]}
        missing = texts - supplied
        if missing:
            items.append(f"Los especialistas no recibieron el contenido de {len(missing)} de los {len(texts)} archivos de texto del repositorio. Las lecturas realizadas pueden limitarse a fragmentos.")
    for tool in data.get("deterministic_results", {}).get("tools", []):
        result = tool.get("result", {})
        if tool["id"] == "D04" and texts and isinstance(result.get("processed_files"), list):
            processed = texts & set(result["processed_files"])
            if texts - processed:
                items.append(f"Semgrep revisó {len(processed)} de los {len(texts)} archivos de texto; los restantes no se evaluaron con sus reglas de seguridad.")
        if tool["id"] == "D02" and "sin historial" in tool.get("detail", "").lower():
            items.append("No se revisó el historial de cambios del repositorio en busca de credenciales.")
    return items


def render_html(data, snapshot, model=""):
    from arktic_office.reporting.view import chapter, detail, h
    from arktic_office.reporting.executive import risks
    from arktic_office.reporting.brief import display_date
    answers = {a["id"]: a for a in data["cuestionario"]["respuestas"]}
    assets = resource_path("assets")
    css = ''.join((assets / name).read_text(encoding="utf-8") for name in ("report-v12.css", "report-v14.css", "report-reading.css"))
    logo = 'data:image/png;base64,' + base64.b64encode((assets / 'arktic-logo.png').read_bytes()).decode()
    title = snapshot.get("project_name") or snapshot["repository"].rstrip('/').split('/')[-1]
    tool_names = {t["id"]: t["name"] for t in data.get("deterministic_results", {}).get("tools", [])}

    ordered = [{**risk, "id": f"R{n:02}"} for n, risk in enumerate(risks(data), 1)]
    def name(item):
        heading = item.get("titulo") or item["observacion"]
        if heading == item["observacion"][:110] and len(item["observacion"]) > 110:
            # Old composers cut the observation mid-word; display its first complete sentence.
            heading = re.split(r'(?<=[.!?])\s+', item["observacion"], maxsplit=1)[0]
        return heading

    def marker(item):
        label = {"critica": "crítica", "alta": "alta", "media": "media", "baja": "baja"}.get(item["severidad"], item["severidad"])
        return '<span class="severity-dot severity-' + h(item["severidad"]) + '" role="img" aria-label="Gravedad ' + h(label) + '" title="Gravedad ' + h(label) + '"></span>'

    def proof(answer, key):
        body = '<p class="source">' + compact_sources(answer, snapshot) + '</p>'
        if answer.get("herramientas"):
            body += '<p>Resultados de herramientas: ' + ' · '.join(f'<a href="#{h(t)}">{h(t)} · {h(tool_names.get(t, "Resultado determinista"))}</a>' for t in answer["herramientas"]) + '</p>'
        if answer.get("aportaciones"):
            origin = [q for q in answer["aportaciones"] if isinstance(q, str) and q in answers]
            if origin:
                body += '<p>Respuestas de origen: ' + ' · '.join(f'<a href="#{h(q)}">{h(q)} · {h(answers[q]["pregunta"])}</a>' for q in origin) + '</p>'
        return detail("fuentes-" + key, "Fuentes consultadas", "Archivos y resultados que respaldan esta lectura", body)

    def paragraph(key):
        answer = answers.get(key)
        if not answer or answer["estado"] == "no_comprobado":
            return ""
        return '<p>' + h(answer["respuesta"]) + '</p>'

    about = '<section class="panel reading-panel"><div class="eyebrow">La aplicación</div><h3>Qué es y cómo funciona</h3>'
    about += paragraph("Q07") or '<p>La evidencia disponible todavía no permite describir con suficiente precisión todas las partes de la aplicación.</p>'
    about += paragraph("Q05") + proof(answers.get("Q07", {"evidencia": []}), "aplicacion-resumen") + '</section>'
    conclusion = '<section class="panel reading-panel"><h3>Hallazgos clave y riesgos</h3>'
    conclusion += paragraph("Q01") or '<p>No se recibió una síntesis respaldada. Los resultados disponibles y sus límites se conservan en el análisis detallado.</p>'
    selected = ordered[:MAX_EXECUTIVE_RISKS]
    security_roles = {'security', 'identity', 'frontend-security', 'backend-security'}
    costs = [x for x in selected if x.get('tipo') == 'coste']
    security = [x for x in selected if x not in costs and (x.get('tipo') == 'vulnerabilidad' or security_roles.intersection(x.get('celulas', [])))]
    other = [x for x in selected if x not in security and x not in costs]
    for label, values in (("Hallazgos de seguridad", security), ("Riesgos de coste", costs), ("Otros riesgos identificados", other)):
        if not values and label != "Hallazgos de seguridad":
            continue
        conclusion += '<h4>' + label + '</h4>'
        if values:
            conclusion += '<ul class="risk-overview">' + ''.join('<li>' + marker(x) + f'<a href="#{x["id"]}">{x["id"]} · {h(name(x))}</a></li>' for x in values) + '</ul>'
        else:
            conclusion += '<p>No se documentaron hallazgos de seguridad comunicados por los especialistas. Las detecciones de los escáneres pueden consultarse en los anexos.</p>'
    conclusion += proof(answers.get("Q01", {"evidencia": []}), "conclusiones-resumen") + '</section>'
    legend = '<p class="severity-legend" aria-label="Colores de gravedad">' + ' '.join(marker({"severidad": key}) + '<span>' + label + '</span>' for key, label in (("critica", "Crítica"), ("alta", "Alta"), ("media", "Media"), ("baja", "Baja"))) + '</p>'
    risk_section = '<section id="riesgos-principales" class="section"><h3>Principales riesgos identificados</h3>' + legend
    if not ordered:
        risk_section += '<div class="panel"><p>No se han identificado riesgos con evidencia suficiente en el alcance revisado. Esto no descarta problemas en los puntos que quedaron sin comprobar.</p></div>'
    for item in selected:
        certainty = "Observado en código" if item["certeza"] == "confirmados" else "Indicio pendiente de comprobar"
        certainty = h(item.get("certeza_original",certainty))
        risk_section += f'<article id="{item["id"]}" class="panel reading-risk {h(item["severidad"])}"><div class="risk-meta">' + marker(item) + '<span class="risk-certainty">' + certainty + '</span></div>'
        risk_section += '<h4>' + h(item["id"] + " · " + name(item)) + '</h4><p>' + h(item["observacion"]) + '</p>'
        risk_section += '<p class="mini">Autoría: ' + h(authors(item)) + '</p>'
        if item.get('tipo'):
            risk_section += '<p>Tipo de riesgo: ' + h({'coste':'Coste', 'vulnerabilidad':'Vulnerabilidad', 'operacion':'Operación'}.get(item['tipo'],item['tipo'])) + '</p>'
        if item.get("importancia"):
            risk_section += '<p><b>Consecuencia posible.</b> ' + h(item["importancia"]) + '</p>'
        if item.get("condiciones"):
            risk_section += '<p class="response-note"><b>De qué depende.</b> ' + h(item["condiciones"]) + '</p>'
        if item.get("pendiente"):
            risk_section += '<p><b>Qué queda por comprobar.</b> ' + h(item["pendiente"]) + '</p>'
        risk_section += proof(item, item["id"]) + '</article>'
    risk_section += '</section>'
    from arktic_office.reporting.questionnaire import favorable_answers
    original_policy = data.get("recepcion") == "sin_revision_automatica"
    favorable = '<section id="protecciones-comprobadas" class="panel reading-panel reading-strengths"><h3>Protecciones y buenas prácticas comprobadas</h3>'
    strengths = favorable_answers(data)[:5]
    if strengths:
        favorable += '<p>Implementaciones comprobadas en las fuentes revisadas. Su alcance se explica en cada pregunta.</p><ul>'
        for answer in strengths:
            good = answer["aspecto_favorable"]
            favorable += '<li><b>' + h(good["titulo"]) + '.</b> ' + h(good["detalle"]) + f' <a href="#{h(answer["id"])}">' + h(answer["id"] + " · " + answer["pregunta"]) + '</a></li>'
        favorable += '</ul>'
    else:
        favorable += '<p>Esta revisión no documentó protecciones o buenas prácticas con respaldo suficiente para destacarlas. Esto no significa que la aplicación carezca de ellas.</p>'
    if original_policy:
        favorable = favorable.replace("Protecciones y buenas prácticas comprobadas", "Protecciones descritas por los especialistas").replace("Implementaciones comprobadas en las fuentes revisadas.", "Aportaciones originales de los especialistas, sin segunda revisión automática.")
    favorable += '</section>'
    omissions = unreviewed_scope(data, snapshot)
    limits = '<section id="pendientes-validar" class="reading-limits"><h3>Pendientes de validar</h3><ul>' + ''.join('<li>' + h(x) + '</li>' for x in omissions) + '</ul></section>' if omissions else ""
    executive = chapter("resumen-ejecutivo", "01", "Una primera lectura", "Resumen ejecutivo", "La aplicación, los resultados relevantes y los límites de esta revisión.", about + conclusion + risk_section + favorable + limits)

    groups = ''
    for group, label, numbers in GROUPS:
        content = ''
        for number in numbers:
            key = f"Q{number:02}"
            answer = answers.get(key)
            if not answer:
                continue
            response = answer["respuesta"]
            if response in {"El agente no entregó una respuesta válida a esta pregunta.", "No se recibió una respuesta validada."}:
                response = "Este punto no pudo comprobarse en la revisión."
            content += f'<article id="{key}" class="reading-answer"><span class="question-id">{key}</span><h4>' + h(answer["pregunta"]) + '</h4><p>' + h(response) + '</p>'
            if answer in favorable_answers(data):
                good = answer["aspecto_favorable"]
                content += '<div class="reading-good"><b>Implementación comprobada: ' + h(good["titulo"]) + '.</b> ' + h(good["detalle"]) + '</div>'
            note = ""
            if answer.get("pendiente"):
                note = "Queda por comprobar: " + answer["pendiente"]
            if note:
                content += '<div class="response-note">' + h(note) + '</div>'
            content += proof(answer, key) + '</article>'
        groups += detail("tema-" + group, label, f"{len(numbers)} preguntas", content)
    if len(ordered) > MAX_EXECUTIVE_RISKS:
        extra = ''.join(f'<article id="{x["id"]}" class="reading-answer"><h4>' + h(x["id"] + " · " + name(x)) + '</h4><p>' + h(x["observacion"]) + '</p>' + proof(x, x["id"]) + '</article>' for x in ordered[MAX_EXECUTIVE_RISKS:])
        groups += detail("riesgos-adicionales", "Otros riesgos documentados", "Resultados fuera de los diez principales", extra)
    questions = chapter("analisis-preguntas", "02", "La evidencia, por temas", "Análisis por preguntas", "Cada respuesta conserva sus fuentes y explica qué queda por comprobar. Abre un tema para consultar sus preguntas.", groups)
    annexes = chapter("anexos-deterministas", "03", "Resultados de las herramientas", "Anexos deterministas", "Resultados explicados, cobertura y limitaciones de cada análisis automático.", deterministic_html(data))
    hero = f'<header class="hero"><div class="hero-art" aria-hidden="true"></div><div class="wrap"><div class="brand-row"><img class="corporate-logo" src="{logo}" alt="Arktic"></div><h1>{h(title)}</h1><p>Una lectura de la aplicación, sus riesgos y la evidencia disponible.</p><div class="meta"><span>{h(display_date(snapshot.get("analyzed_at")))}</span><span>Revisión estática · {h(snapshot.get("branch", ""))}@{h(snapshot["commit"][:12])}</span></div></div></header>'
    nav = '<nav class="nav" aria-label="Secciones del informe"><div class="wrap">' + ''.join(f'<a href="#{key}"><b>{n:02}</b> {label}</a>' for n, (key, label) in enumerate((("resumen-ejecutivo", "Resumen ejecutivo"), ("analisis-preguntas", "Análisis por preguntas"), ("anexos-deterministas", "Anexos deterministas")), 1)) + '</div></nav>'
    script = (assets / 'report-navigation.js').read_text(encoding='utf-8')
    banner = '<div class="demo"><div class="wrap">' + ('FUENTES FICTICIAS · ' if snapshot.get("simulation") else '') + 'Resultados vinculados al commit revisado. Las conclusiones respetan el alcance de la evidencia disponible.</div></div>'
    footer = '<footer><div class="corporate-footer"><span>ARKTIC OFFICE / TECNOLOGÍA Y CIBERSEGURIDAD</span><img class="footer-logo" src="' + logo + '" alt="Arktic"></div><p>Fuentes, respuestas originales y resultados de herramientas conservados para su revisión.</p></footer>'
    from arktic_office.reporting.originals import html as original_html
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + h(title) + ' · Informe Arktic</title><style>' + css + '</style></head><body class="reading-report">' + banner + hero + nav + '<main class="wrap">' + executive + questions + annexes + original_html(data) + footer + '</main><script id="arktic-report-navigation">' + script + '</script></body></html>'
