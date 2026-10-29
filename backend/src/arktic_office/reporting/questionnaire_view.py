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
    return "; ".join(links) or "Sin fuente de código aportada; consultar herramientas y límites."


def html(data, snapshot, summary=False):
    from arktic_office.reporting.view import detail
    answers = data.get("cuestionario", {}).get("respuestas", [])
    if not answers:
        return ""
    parts = []
    for role, label in (("coordinator", "Resumen del coordinador"), ("inventory", "Inventario"), ("architecture", "Arquitectura y operación"), ("security", "Seguridad y privacidad")):
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
        parts.append('<section class="panel"><h3>' + label + '</h3>' + content + '</section>' if summary else detail("cuestionario-" + role, label + " · respuestas por pregunta", "Estados, fuentes y verificaciones pendientes", content))
    if summary:
        return ''.join(parts)
    counts = {state: sum(a["estado"] == state for a in answers) for state in ("respondida", "parcial", "no_aplica", "no_comprobado")}
    return '<section id="cuestionario"><h2>Cuestionario de revisión · 40 preguntas</h2><p>' + escape(' · '.join(f'{n} {s.replace("_", " ")}' for s, n in counts.items())) + '</p>' + ''.join(parts) + '</section>'


def deterministic_html(data):
    from arktic_office.reporting.view import detail
    saved = data.get("deterministic_results")
    if not saved:
        return ""
    body = '<section id="resultados-deterministas"><h2>Resultados de todos los análisis deterministas</h2><p>Salidas estructuradas conservadas para este commit. Los posibles secretos se ocultan. No son conclusiones del modelo; una herramienta no evaluada no equivale a una comprobación limpia.</p>'
    body += '<p>Repositorio: ' + escape(saved["repository"]) + ' · commit ' + escape(saved["commit"]) + '</p>'
    for tool in saved["tools"]:
        result = tool["result"]
        content = '<p><b>Estado:</b> ' + escape(tool["status"]) + '</p><p>' + escape(tool["detail"]) + '</p>'
        content += '<p>Hallazgos normalizados: ' + str(len(result.get("findings", []))) + ' · archivos de entrada registrados: ' + str(len(result.get("input_files", result.get("inventory", [])))) + '</p>'
        content += '<p>Se conserva el resultado completo estructurado: entradas, hallazgos, cobertura, omisiones y diagnósticos disponibles. Graphify incluye nodos y relaciones; su mapa es una ayuda estática.</p>'
        content += '<pre>' + escape(json.dumps(result, ensure_ascii=False, indent=2)) + '</pre>'
        body += detail(tool["id"], tool["id"] + " · " + tool["name"], tool["status"], content)
    return body + '</section>'


def markdown(data, snapshot):
    from arktic_office.reporting.brief import text, references
    lines = []
    answers = data.get("cuestionario", {}).get("respuestas", [])
    if answers:
        lines += ['', '## Cuestionario de revisión', '']
    for a in answers:
        lines += ['### ' + a["id"] + ' · ' + text(a["pregunta"]), '', text(a["estado"] + ': ' + a["respuesta"]),
            '', 'Pendiente: ' + text(a.get("pendiente") or 'No se añadió un pendiente específico.'), '', references(a, snapshot),
            '', 'Herramientas: ' + text(', '.join(a.get("herramientas", [])) or 'Sin referencias a herramientas.')]
    saved = data.get("deterministic_results")
    if saved:
        lines += ['', '## Resultados de todos los análisis deterministas', '', 'Salidas estructuradas con posibles secretos ocultos.']
        for tool in saved["tools"]:
            lines += ['', '### ' + tool["id"] + ' · ' + text(tool["name"]), '', text(tool["status"] + ': ' + tool["detail"]), '',
                # Indented code cannot be closed by repository-controlled backticks.
                '\n'.join('    ' + line for line in json.dumps(tool["result"], ensure_ascii=False, indent=2).splitlines())]
    return '\n'.join(lines) + '\n' if lines else ""
