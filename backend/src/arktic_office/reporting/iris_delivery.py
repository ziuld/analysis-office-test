"""Office adapter for the shared Iris contract; keeps native snapshots, calls and storage."""
import hashlib
import json
from pathlib import Path

from arktic_office.reporting import iris_core
from arktic_office.resources.paths import resource_path
from arktic_office.storage.jsonio import read_json, write_json
from arktic_office.preparation.repository import redact

VERSION = '0.2.0'
ANSWER_STATES = {'respondida':'Respondida', 'parcial':'Parcial', 'no_comprobado':'No comprobada', 'no_aplica':'No aplica'}


def citations(refs):
    return list(dict.fromkeys(f'{ref["path"]}:{ref["line"]}' for ref in refs if isinstance(ref,dict) and 'path' in ref and 'line' in ref))


def triage(item, visible, delivered):
    """Only accept source-backed decisions after the OSV output was delivered to this task."""
    from arktic_office.reporting.references import locate
    fields = ('package','version','advisory','scope','consumer','platform','condition','defense','decision','priority','correction','verification')
    if 'D03' not in delivered or any(not isinstance(item.get(k),str) or not 1 <= len(item[k]) <= 1200 for k in fields):
        return None
    if item['decision'] not in {'pending','applicable','not_applicable'} or item['scope'] not in {'unknown','runtime','development','both'}:
        return None
    refs = locate([r for r in item.get('evidencia',[]) if isinstance(r,str)], visible)
    if item['decision'] != 'pending' and not refs:
        return None
    return {**{k:redact(item[k]) for k in fields}, 'evidencia':refs}


def dependencies(snapshot, tasks):
    saved = snapshot.get('deterministic_results', {})
    tool = next((t for t in saved.get('tools',[]) if t.get('id') == 'D03'), {})
    result = tool.get('result',{})
    raw = result.get('original_output_redacted', {})
    rows = {}
    for group in raw.get('results',[]) if isinstance(raw,dict) else []:
        for item in group.get('packages',[]):
            package = item.get('package',{})
            for advisory in item.get('vulnerabilities',[]):
                row = dict(package=package.get('name','unknown'), version=package.get('version','unknown'),
                    advisory=advisory.get('id','unknown'), summary=advisory.get('summary',''), ecosystem=package.get('ecosystem',''),
                    scope='unknown',consumer='Pendiente de contrastar',platform='Pendiente',condition='Consultar las condiciones completas del aviso.',
                    defense='Pendiente',decision='pending',priority='Sin priorizar',correction='Seleccionar una corrección compatible con la rama afectada.',
                    verification='Contrastar versión desplegada y función alcanzable.',sources=[],
                    fixed_versions=sorted({event['fixed'] for affected in advisory.get('affected',[]) if affected.get('package',{}).get('name') == package.get('name')
                                           for span in affected.get('ranges',[]) for event in span.get('events',[]) if 'fixed' in event}))
                rows[(row['package'],row['version'],row['advisory'])] = row
    # Historical/native summaries may lack full OSV JSON. Preserve them as pending rows, never silently erase them.
    if not rows:
        for n, finding in enumerate(result.get('findings',[]),1):
            summary = str(finding.get('summary',''))
            rows[('unknown','unknown',f'pendiente-{n}')] = dict(package='unknown',version='unknown',advisory=f'pendiente-{n}',
                summary=summary,scope='unknown',consumer='Pendiente',platform='Pendiente',condition='Falta el resultado OSV estructurado.',
                defense='Pendiente',decision='pending',priority='Sin priorizar',correction='Recuperar el aviso original.',
                verification='Contrastar paquete, versión y función.',sources=[],fixed_versions=[])
    ignored = 0
    for task in tasks:
        for decision in task.get('result',{}).get('dependencias',[]):
            key = tuple(decision[k] for k in ('package','version','advisory'))
            if key not in rows:
                ignored += 1
                continue
            rows[key].update({k:v for k,v in decision.items() if k not in {'evidencia'}})
            rows[key]['sources'] = citations(decision['evidencia'])
    return list(rows.values()), ignored


def attach(data, snapshot, output):
    from arktic_office.config.agents import FULL_STACK
    from arktic_office.coordination.workflow import checkpoint_path, load_tasks
    from arktic_office.reporting.questionnaire import catalog, favorable_answers
    from arktic_office.reporting.executive import risks
    data.setdefault('deterministic_results',snapshot.get('deterministic_results',{}))
    progress = read_json(checkpoint_path(output), {})
    tasks = progress.get('tasks',[])
    specifications = load_tasks()
    questions = {q['id']:q for q in catalog()}
    answers = {a['id']:a for a in data.get('cuestionario',{}).get('respuestas',[])}
    guide = [(n, spec['instructions'].splitlines()[0].lstrip('# '),[(key,questions[key]['pregunta']) for key in spec['questions']])
             for n,spec in enumerate(specifications,1)]
    mapped = {}
    for key in questions:
        a = answers.get(key,{})
        mapped[key] = dict(state=ANSWER_STATES.get(a.get('estado'),'No comprobada'),
            text=a.get('respuesta') or 'No se recibió una respuesta.',sources=citations(a.get('evidencia',[])),
            pending=a.get('pendiente') or ('Falta completar este recorrido.' if a.get('estado') in {None,'parcial','no_comprobado'} else ''))
    coverage, conclusions = [], []
    risk_blocks = {}
    for n,spec in enumerate(specifications,1):
        task = next((t for t in tasks if t['id'] == spec['id']), {})
        refs = list(dict.fromkeys(r for key in spec['questions'] for r in mapped[key]['sources']))
        for finding in task.get('result',{}).get('observaciones',[]):
            risk_blocks[finding.get('observacion')] = n
        closure = task.get('closure_note') or 'No se conservó un cierre de este bloque.'
        conclusions.append(dict(number=n,conclusion=closure))
        coverage.append(dict(block=n,state='reviewed' if task.get('status') == 'completa' else 'partial' if task else 'pending',
            entrypoints=sorted({r.rsplit(':',1)[0] for r in refs}),controls=task.get('checks',[]),consumers=[],
            new_sources=refs,reused_sources=[],pending=list(task.get('pending',{}).values()),
            origin='Fuentes entregadas y citas de esta corrida; comprobaciones declaradas por el agente.'))
    findings = []
    for n,risk in enumerate(risks(data),1):
        key = hashlib.sha256(json.dumps([risk.get('tipo'),risk.get('control'),risk['observacion'],sorted({r['path'] for r in risk.get('evidencia',[])})],ensure_ascii=False).encode()).hexdigest()[:20]
        findings.append(dict(key=key,id=f'R{n:02}',block=risk_blocks.get(risk['observacion'],5 if risk.get('control') == 'acceso' else 6),
            title=risk.get('titulo') or risk['observacion'],severity={'critica':'Crítica','alta':'Alta','media':'Media','baja':'Baja'}.get(risk['severidad'],'Sin determinar'),
            certainty=risk.get('certeza_original') or risk['certeza'],status='open',observation=risk['observacion'],
            effect=risk.get('importancia') or 'Impacto no determinado en este resultado.',
            conditions=risk.get('condiciones') or risk.get('por_confirmar') or 'Condiciones operativas pendientes.',
            action=risk.get('accion') or risk.get('pendiente') or 'Contrastar este recorrido.',
            verification=risk.get('pendiente') or 'Validar la condición con el responsable.',sources=citations(risk.get('evidencia',[]))))
    native = read_json(output / 'herramientas' / 'resultados-deterministas.json')
    if native and (native.get('repository'),native.get('commit')) != (snapshot['repository'],snapshot['commit']):
        from arktic_office.core.errors import AuditError
        raise AuditError('Los resultados deterministas no pertenecen a esta captura.')
    rows, ignored = dependencies({**snapshot,'deterministic_results':native or snapshot.get('deterministic_results',{})},tasks)
    cache = snapshot.get('deterministic_results',{}).get('preparation_cache',snapshot.get('preparation',{}).get('cache',{}))
    provenance = dict(mode='new',basis='snapshot_and_same_run_tasks',independence='not_certified',base_run=None,
                      preparation_cache=cache, semantic_history_reused=False)
    tools = {t['id']:dict(status=t['status']) for t in snapshot.get('deterministic_results',{}).get('tools',[])}
    document = dict(schema_version=1,project=snapshot.get('project_name') or snapshot['repository'].rstrip('/').split('/')[-1],
        status='Iris · Full Stack · revisión estática · ' + data.get('estado','parcial'),
        scope=f'{snapshot.get("branch", "")} · {snapshot["commit"]} · Iris interno {VERSION}',
        tools=tools,summary=dict(application=mapped['Q07']['text'],connections=mapped['Q08']['text'],priorities=mapped['Q01']['text'],
            strengths=[dict(text=a['aspecto_favorable']['titulo'] + '. ' + a['aspecto_favorable']['detalle'],question=a['id'],sources=citations(a['evidencia'])) for a in favorable_answers(data)],
            limits=list(dict.fromkeys([a['pending'] for a in mapped.values() if a['pending']] +
                [d if isinstance(d,str) else d['pregunta'] for d in data.get('dudas',[])] +
                ['La aplicación no se ejecutó; no se acredita configuración desplegada ni exhaustividad semántica.']))),
        blocks=conclusions,answers=mapped,annexes=[dict(title='Ejecución en Arktic Office',paragraphs=[
            'El modelo configurado de la oficina investiga mediante Core; el generador compartido solo presenta resultados y no llama a modelos.',
            'Almacenamiento y escáneres nativos de la oficina. No se usa la .local ni la instalación de herramientas del portable.',
            'Las claves de hallazgo son huellas de observación y fuentes; un cambio de redacción requiere correlación humana, no implica resolución.'])])
    payload = dict(contract=iris_core.CONTRACT_VERSION,agent_version=VERSION,document=document,guide=guide,
                   coverage=coverage,findings=findings,dependencies=rows,ignored_dependency_decisions=ignored,provenance=provenance)
    data['iris_delivery'] = payload
    directory = output / 'agents' / FULL_STACK
    directory.mkdir(parents=True,exist_ok=True)
    write_json(directory / 'iris-contract.json',payload)
    for name,value in [('cobertura',coverage),('dependencias',rows),('hallazgos',findings),('procedencia',provenance)]:
        write_json(directory / (name + '.json'),value)
    _, fichas = build(data,snapshot)
    for name,contents in fichas.items():
        target = directory / 'bloques' / name
        target.parent.mkdir(exist_ok=True)
        target.write_text(contents,encoding='utf8')


def build(data,snapshot):
    from arktic_office.reporting.questionnaire_view import deterministic_html
    from arktic_office.reporting.originals import html as originals
    p = data['iris_delivery']
    h = iris_core.h
    annex = '<section id="procedencia-revision"><h3>Procedencia</h3><p>Iris interno ' + h(p['agent_version']) + ' · contrato compartido ' + h(p['contract']) + '</p>'
    annex += ('<p>Recomposición de una corrida histórica, sin llamadas nuevas al modelo.</p>' if p['provenance']['mode'] == 'historical_replay' else
              '<p>Revisión nueva sobre snapshot; usa los bloques anteriores de la misma corrida. Independencia semántica no certificada. No se compara con una corrida anterior ni se declaran hallazgos resueltos.</p>')
    annex += '<p>Preparación: ' + h(json.dumps(p['provenance']['preparation_cache'],ensure_ascii=False)) + '</p></section>'
    annex += '<section id="cobertura-revision"><h3>Cobertura por bloque</h3>'
    for block in p['coverage']:
        annex += '<details><summary>Bloque ' + str(block['block']) + ': ' + h(block['state']) + '</summary><p>' + h(block['origin']) + '</p>'
        annex += iris_core.citations(block['new_sources']) + '<p>' + h('; '.join(block['pending']) or 'Consultar el alcance de las respuestas.') + '</p></details>'
    annex += '</section><section id="dependencias-revision"><h3>Aplicabilidad de dependencias</h3><p>Coincidencia de versión no implica explotación. Versiones corregidas pueden pertenecer a ramas distintas.</p>'
    if not p['dependencies']:
        annex += '<p>Sin filas de avisos disponibles. Consultar estado y alcance de OSV; no acredita ausencia de vulnerabilidades.</p>'
    for row in p['dependencies']:
        annex += '<details><summary>' + h(row['package'] + ' ' + row['version'] + ' · ' + row['advisory'] + ' · ' + row['decision']) + '</summary>'
        for field in ('summary','scope','consumer','platform','condition','defense','priority','correction','verification'):
            annex += '<p><b>' + h(field) + ':</b> ' + h(row.get(field,'')) + '</p>'
        annex += '<p>Versiones corregidas: ' + h(', '.join(row.get('fixed_versions',[]))) + '</p>' + iris_core.citations(row['sources']) + '</details>'
    annex += '</section>' + deterministic_html(data) + originals(data)
    template = resource_path('assets','iris-template.html').read_text(encoding='utf8')
    return iris_core.build(p['document'],p['coverage'],p['findings'],p['guide'],template,annex)


def render_html(data,snapshot,model=''):
    return build(data,snapshot)[0]
