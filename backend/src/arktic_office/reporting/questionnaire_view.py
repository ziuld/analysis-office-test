"""Question answers and complete deterministic annexes; all text stays inert."""
import json
from html import escape


def compact_sources(answer, snapshot):
    """Display contiguous cited lines as ranges; retain all exact quotes in JSON."""
    from arktic_office.reporting.view import sources
    grouped = {}
    for ref in answer.get("evidencia", []):
        grouped.setdefault(ref["path"], {})[ref["line"]] = ref
    links = []
    for path, refs in grouped.items():
        ranges = []
        for number in sorted(refs):
            if ranges and number == ranges[-1][1] + 1:
                ranges[-1][1] = number
            else:
                ranges.append([number, number])
        for first, last in ranges:
            label = escape(f"{path}:{first}")
            target = sources({"evidencia": [refs[first]]}, snapshot)
            if last != first:
                target = target.replace(label, escape(f"{path}:{first}–{last}")).replace(f'#L{first}"', f'#L{first}-L{last}"')
            links.append(target)
    original = answer.get('referencias_originales',[])
    if original:
        links.append('Referencias del especialista: '+escape('; '.join(str(r) for r in original)))
    return "; ".join(links) or "Sin referencia indicada por el especialista."


def html(data, snapshot, summary=False):
    from arktic_office.reporting.view import detail
    answers = data.get("cuestionario", {}).get("respuestas", [])
    if not answers:
        return ""
    parts = []
    from arktic_office.coordination.catalog import catalog
    roster = {p['id']: p['name'] for p in catalog()}
    roster['security'] = 'Seguridad y privacidad (histórico)'
    for role, label in roster.items():
        if summary and role != "coordinator":
            continue
        content = ""
        for answer in answers:
            if answer["role"] != role:
                continue
            content += '<article id="' + ("resumen-" if summary else "") + answer["id"] + '"><h4>' + escape(answer["id"] + " · " + answer["pregunta"]) + '</h4>'
            content += '<p><strong>' + escape(answer["estado"].replace("_", " ")) + '</strong> · ' + escape(answer["respuesta"]) + '</p>'
            if answer.get("pendiente"):
                content += '<p><b>Pendiente:</b> ' + escape(answer["pendiente"]) + '</p>'
            proof = '<p class="source">' + compact_sources(answer, snapshot)
            proof += ' · '.join('<a href="#' + escape(t, quote=True) + '">' + escape(t) + '</a>' for t in answer.get("herramientas", [])) + '</p>'
            content += detail("fuentes-resumen-" + answer["id"], "Fuentes de " + answer["id"], "Respaldo del resumen", proof) if summary else proof
            if answer.get("aportaciones"):
                content += '<p>Respuestas de origen: ' + ' · '.join('<a href="#' + escape(q, quote=True) + '">' + escape(q) + '</a>' for q in answer["aportaciones"]) + '</p>'
            content += '</article>'
        if content:
            parts.append('<section class="panel"><h3>' + label + '</h3>' + content + '</section>' if summary else detail("cuestionario-" + role, label + " · respuestas por pregunta", "Estados, fuentes y verificaciones pendientes", content))
    if summary:
        return ''.join(parts)
    counts = {state: sum(a["estado"] == state for a in answers) for state in ("respondida", "parcial", "no_aplica", "no_comprobado")}
    return '<section id="cuestionario"><h2>Cuestionario de revisión · 40 preguntas</h2><p>' + escape(' · '.join(f'{n} {s.replace("_", " ")}' for s, n in counts.items())) + '</p>' + ''.join(parts) + '</section>'


def deterministic_html(data):
    from arktic_office.reporting.view import detail
    from arktic_office.reporting.tool_narrative import narrative
    saved = data.get("deterministic_results")
    if not saved:
        return ""
    body = '<section id="resultados-deterministas"><h2>Resultados de todos los análisis deterministas</h2><p>Qué revisó cada herramienta, qué encontró y qué queda por comprobar. Las alertas automáticas se distinguen de las vulnerabilidades contrastadas por los agentes.</p>'
    body += '<p>Repositorio: ' + escape(saved["repository"]) + ' · commit ' + escape(saved["commit"]) + '</p>'
    cache = saved.get('preparation_cache', {})
    if cache.get('status') == 'reused':
        body += '<p>Preparación reutilizada para el mismo repositorio y commit. Generada el ' + escape(cache.get('prepared_at', 'fecha no disponible')) + '. Los agentes se han ejecutado de nuevo; los escáneres y Graphify conservan los resultados de esa fecha.</p>'
    for tool in saved["tools"]:
        state, paragraphs, findings = narrative(tool)
        content = ''.join('<p>' + escape(p) + '</p>' for p in paragraphs)
        if findings:
            content += '<ul>' + ''.join('<li>' + escape(f) + '</li>' for f in findings) + '</ul>'
        body += detail(tool["id"], tool["id"] + " · " + tool["name"], state, content)
    return body + '</section>'


def markdown(data, snapshot):
    from arktic_office.reporting.brief import text, references
    lines = []
    answers = data.get("cuestionario", {}).get("respuestas", [])
    if answers:
        from arktic_office.reporting.questionnaire import favorable_answers
        strengths = favorable_answers(data)[:5]
        lines += ['', '## Protecciones y buenas prácticas comprobadas', '']
        for a in strengths:
            good = a["aspecto_favorable"]
            lines += ['- **' + text(good["titulo"]) + '**: ' + text(good["detalle"]) + ' — ' + a["id"] + ' · ' + text(a["pregunta"])]
        if not strengths:
            lines += ['Esta revisión no documentó protecciones o buenas prácticas con respaldo suficiente para destacarlas. Esto no significa que la aplicación carezca de ellas.']
        lines += ['', '## Cuestionario de revisión', '']
    for a in answers:
        lines += ['### ' + a["id"] + ' · ' + text(a["pregunta"]), '', text(a["respuesta"]),
            *(['', 'Queda por comprobar: ' + text(a['pendiente'])] if a.get('pendiente') else []), '', references(a, snapshot),
            '', 'Herramientas: ' + text(', '.join(a.get("herramientas", [])) or 'Sin referencias a herramientas.')]
        if a.get("aspecto_favorable") and a.get("evidencia") and a["estado"] in {"respondida", "parcial"}:
            lines += ['', '**Implementación comprobada: ' + text(a["aspecto_favorable"]["titulo"]) + '.** ' + text(a["aspecto_favorable"]["detalle"])]
    saved = data.get("deterministic_results")
    if saved:
        lines += ['', '## Resultados de todos los análisis deterministas', '', 'Resultados explicados, alcance y comprobaciones pendientes.']
        cache = saved.get('preparation_cache', {})
        if cache.get('status') == 'reused':
            lines += ['', 'Preparación reutilizada para el mismo repositorio y commit. Generada el ' + text(cache.get('prepared_at', 'fecha no disponible')) + '. Los agentes se han ejecutado de nuevo; escáneres y Graphify conservan los resultados de esa fecha.']
        for tool in saved["tools"]:
            from arktic_office.reporting.tool_narrative import narrative
            state, paragraphs, findings = narrative(tool)
            lines += ['', '### ' + tool["id"] + ' · ' + text(tool["name"]), '', state]
            for p in paragraphs:
                lines += ['', text(p)]
            lines += ['- ' + text(f) for f in findings]
    result = '\n'.join(lines) + '\n' if lines else ""
    if data.get("recepcion") == "sin_revision_automatica":
        result = result.replace("Protecciones y buenas prácticas comprobadas", "Protecciones descritas por los especialistas").replace("Implementación comprobada:", "Implementación descrita por el especialista:")
    return result
