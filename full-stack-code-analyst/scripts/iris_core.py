"""Shared Iris HTML contract. Pure data in, escaped HTML/Markdown blocks out; no IO."""
from html import escape
import re

CONTRACT_VERSION = "1.1"
STATES = {"Respondida", "Parcial", "No comprobada", "No aplica"}
SEVERITIES = {"Crítica": 0, "Alta": 1, "Media": 2, "Baja": 3, "Sin determinar": 4}


def h(value):
    return escape(str(value), quote=True)


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} debe contener texto.')
    return value


def citations(values):
    if not isinstance(values, list) or any(not isinstance(v, str) or not re.fullmatch(r'.+:\d+(?:-\d+)?', v) for v in values):
        raise ValueError('Las fuentes deben ser citas ruta:línea o ruta:inicio-fin.')
    return '<p class="source">' + ' · '.join('<code>' + h(v) + '</code>' for v in values) + '</p>' if values else ''


def build(data, coverage, findings, guide, template, annex_html):
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('Falta informe.json válido; no redactes el HTML a mano.')
    answers = data.get('answers', {})
    if not isinstance(answers, dict) or set(answers) != {f'Q{i:02}' for i in range(1, 41)}:
        raise ValueError('informe.json debe contener Q01–Q40 una vez cada una.')
    conclusions = data.get('blocks', [])
    if not isinstance(conclusions, list) or [b.get('number') for b in conclusions] != list(range(1, 8)):
        raise ValueError('informe.json debe contener conclusiones de los siete bloques en orden.')
    for a in answers.values():
        if a.get('state') not in STATES:
            raise ValueError('Estado de respuesta inválido.')
        text(a.get('text'), 'Respuesta')
        citations(a.get('sources'))
        if a['state'] in {'Parcial', 'No comprobada'}:
            text(a.get('pending'), 'Pendiente')
    ids = set()
    for risk in findings:
        rid = risk.get('id', '')
        if not re.fullmatch(r'R\d{2,}', rid) or rid in ids or risk.get('block') not in range(1, 8):
            raise ValueError('Cada hallazgo requiere id Rxx único y block entre 1 y 7.')
        ids.add(rid)
        if risk['severity'] not in SEVERITIES:
            raise ValueError('Gravedad inválida.')
        for field in ('title', 'certainty', 'observation', 'effect', 'conditions', 'action', 'verification'):
            text(risk.get(field), field)
        citations(risk['sources'])
    summary = data.get('summary', {})
    for key in ('application', 'connections', 'priorities'):
        text(summary.get(key), 'summary.' + key)
    if not isinstance(summary.get('strengths'), list) or not isinstance(summary.get('limits'), list):
        raise ValueError('summary requiere listas strengths y limits.')
    summary_html = ('<section class="panel reading-panel" id="resumen-aplicacion"><h3>Aplicación y conexiones</h3>'
                    f'<p>{h(summary["application"])}</p><p>{h(summary["connections"])}</p></section>'
                    '<section class="panel reading-panel" id="resumen-prioridades"><h3>Prioridades de Iris</h3>'
                    f'<p>{h(summary["priorities"])}</p><ul class="risk-overview">')
    for risk in sorted(findings, key=lambda r: SEVERITIES[r['severity']])[:10]:
        summary_html += (f'<li><div><a href="#{risk["id"]}">{risk["id"]} · {h(risk["title"])}</a>'
                         f'<p><b>Gravedad {h(risk["severity"].lower())}.</b> Certeza: {h(risk["certainty"])}.</p>'
                         f'<p><b>Acción:</b> {h(risk["action"])} <b>Condición:</b> {h(risk["conditions"])}</p></div></li>')
    summary_html += '</ul></section><section class="panel reading-panel reading-strengths" id="resumen-protecciones"><h3>Protecciones comprobadas</h3><ul>'
    for strength in summary['strengths']:
        label = h(text(strength.get('text'), 'Protección'))
        if strength.get('question'):
            if strength['question'] not in answers:
                raise ValueError('La protección apunta a una pregunta inexistente.')
            label = f'<a href="#{strength["question"]}">{label}</a>'
        summary_html += '<li>' + label + citations(strength.get('sources', [])) + '</li>'
    if not summary['strengths']:
        summary_html += '<li>No se han documentado protecciones; consulta los pendientes de cobertura.</li>'
    summary_html += '</ul></section><section class="reading-limits" id="resumen-limites"><h3>Alcance pendiente</h3>'
    for limit in summary['limits']:
        summary_html += '<p>' + h(text(limit, 'Límite')) + '</p>'
    for name, tool in data.get('tools', {}).items():
        if tool.get('status') != 'complete':
            summary_html += f'<p>{h(name)}: {h(tool.get("status"))}. Esta cobertura no está completada.</p>'
    summary_html += '</section>'
    blocks, fichas = [], {}
    for n, title, questions in guide:
        conclusion = text(conclusions[n-1].get('conclusion'), 'Conclusión')
        status = {'reviewed': 'Revisado', 'partial': 'Parcial', 'pending': 'Pendiente'}[coverage[n-1]['state']]
        body = [f'<details id="bloque-{n:02}"><summary>{n}. {h(title)}<span>{status}</span></summary>',
                '<div class="detail-body">', '<p>' + h(conclusion) + '</p>']
        ficha = [f'# {n}. {title}', f'Estado: {status}', conclusion]
        for qid, question in questions:
            a = answers[qid]
            body += [f'<article class="reading-answer" id="{qid}"><span class="question-id">{qid} · {h(a["state"])}</span>',
                     f'<h4>{h(question)}</h4><p>{h(a["text"])}</p>', citations(a['sources'])]
            if a.get('pending'):
                body.append('<p class="response-note"><b>Pendiente.</b> ' + h(a['pending']) + '</p>')
            body.append('</article>')
            ficha += ['', f'## {qid} · {question}', a['state'], a['text'], 'Fuentes: ' + ' | '.join(a['sources']), a.get('pending', '')]
        for risk in findings:
            if risk['block'] != n:
                continue
            body += [f'<article id="{risk["id"]}" class="reading-risk"><h4>{risk["id"]} · {h(risk["title"])}</h4>',
                     f'<p><b>Gravedad {h(risk["severity"].lower())}.</b> Certeza: {h(risk["certainty"])}.</p>']
            for key, label in [('observation','Observación'), ('effect','Consecuencia posible'), ('conditions','Condiciones y defensas'),
                               ('action','Mejora propuesta'), ('verification','Comprobación')]:
                body.append(f'<p><b>{label}.</b> {h(risk[key])}</p>')
            body += [citations(risk['sources']), '</article>']
            ficha += ['', f'## {risk["id"]} · {risk["title"]}'] + [f'{k}: {risk[k]}' for k in
                      ('severity','certainty','observation','effect','conditions','action','verification')] + ['Fuentes: ' + ' | '.join(risk['sources'])]
        body.append('</div></details>')
        blocks.append('\n'.join(body))
        fichas[f'{n:02}.md'] = '\n'.join(ficha) + '\n'
    annex = []
    for item in data.get('annexes', []):
        text(item.get('title'), 'Título de anexo')
        if not isinstance(item.get('paragraphs'), list):
            raise ValueError('Un anexo requiere paragraphs.')
        annex.append('<section class="panel reading-panel"><h3>' + h(item['title']) + '</h3>' +
                     ''.join('<p>' + h(text(p, 'Anexo')) + '</p>' for p in item['paragraphs']) + '</section>')
    annex.append(annex_html)
    for key, value in dict(PROYECTO=h(text(data.get('project'), 'Proyecto')), ESTADO=h(text(data.get('status'), 'Estado')),
                           ALCANCE=h(text(data.get('scope'), 'Alcance')), RESUMEN=summary_html,
                           BLOQUES='\n'.join(blocks), ANEXOS='\n'.join(annex)).items():
        template = template.replace('{{' + key + '}}', value)
    if re.search(r'{{[A-Z_]+}}', template):
        raise ValueError('Quedan marcadores sin sustituir.')
    return template, fichas
