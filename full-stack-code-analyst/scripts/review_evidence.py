"""Structured review evidence and escaped HTML, interpreted by the invoking chat."""
from html import escape
from pathlib import Path
import re

from storage import atomic_text, intact, read_json, write_json


def initialize(folder, state, base=None):
    previous = {x['path']: x['sha256'] for x in (base or {}).get('source', {}).get('files', [])}
    current = {x['path']: x['sha256'] for x in state['source']['files']}
    changes = None if not base else {
        'added': sorted(current.keys() - previous.keys()),
        'removed': sorted(previous.keys() - current.keys()),
        'modified': sorted(k for k in current.keys() & previous.keys() if current[k] != previous[k])}
    write_json(folder / 'cambios-entrada.json', {'base_review': state['provenance']['base_review'], 'changes': changes})
    write_json(folder / 'cobertura.json', [dict(block=n, state='pending', entrypoints=[], controls=[],
               consumers=[], new_sources=[], reused_sources=[], pending=['Completar en el chat.']) for n in range(1, 8)])
    write_json(folder / 'hallazgos.json', [])
    rows = []
    osv = state['tools'].get('osv', {})
    if osv.get('status') == 'complete':
        payload = read_json(Path(osv['folder']) / 'resultado.json', {})
        for result in payload.get('results', []):
            for item in result.get('packages', []):
                package = item.get('package', {})
                for advisory in item.get('vulnerabilities', []):
                    fixes = sorted({event['fixed'] for affected in advisory.get('affected', [])
                                    if affected.get('package', {}).get('name') == package.get('name')
                                    for rang in affected.get('ranges', []) for event in rang.get('events', [])
                                    if 'fixed' in event})
                    rows.append(dict(package=package.get('name'), version=package.get('version'),
                        ecosystem=package.get('ecosystem'), advisory=advisory.get('id'),
                        summary=advisory.get('summary', ''), scope='unknown', consumer='Pendiente',
                        platform='Pendiente', condition='Contrastar el aviso completo en resultado.json de OSV.',
                        defense='Pendiente', decision='pending', priority='Pendiente',
                        fixed_versions=fixes, correction='Elegir corrección compatible con la rama afectada.',
                        verification='Pendiente', sources=[]))
    rows = list({(r['ecosystem'], r['package'], r['version'], r['advisory']): r for r in rows}.values())
    state['dependency_keys'] = [list(key) for key in
                               sorted((r['ecosystem'] or '', r['package'], r['version'], r['advisory']) for r in rows)]
    write_json(folder / 'dependencias.json', rows)


def load(folder, state):
    def citations(values):
        return isinstance(values, list) and all(isinstance(s, str) and re.fullmatch(r'.+:\d+(?:-\d+)?', s) for s in values)
    coverage = read_json(folder / 'cobertura.json')
    findings = read_json(folder / 'hallazgos.json')
    dependencies = read_json(folder / 'dependencias.json')
    if not isinstance(coverage, list) or [x.get('block') for x in coverage] != list(range(1, 8)):
        raise ValueError('cobertura.json debe registrar los siete bloques en orden.')
    for block in coverage:
        if block.get('state') not in {'reviewed', 'partial', 'pending'}:
            raise ValueError('Estado de cobertura inválido.')
        for field in ('entrypoints', 'controls', 'consumers', 'new_sources', 'reused_sources', 'pending'):
            if not isinstance(block.get(field), list) or any(not isinstance(s, str) for s in block[field]):
                raise ValueError('Cobertura debe contener listas de fuentes y pendientes.')
        if state['provenance']['mode'] == 'independent' and block['reused_sources']:
            raise ValueError('Una revisión independiente no admite conclusiones de revisiones anteriores.')
        if block['state'] != 'pending' and not (block['new_sources'] or block['reused_sources']):
            raise ValueError('Una cobertura revisada necesita fuentes declaradas.')
    if not isinstance(findings, list) or len({f.get('key') for f in findings}) != len(findings):
        raise ValueError('hallazgos.json requiere claves estables y únicas.')
    for f in findings:
        if not all(isinstance(f.get(k), str) and f[k].strip() for k in ('key', 'title', 'severity', 'certainty', 'verification')):
            raise ValueError('Cada hallazgo necesita clave, título, gravedad, certeza y verificación.')
        if f.get('status') not in {'open', 'pending', 'resolved'} or not citations(f.get('sources')) or not f['sources']:
            raise ValueError('Cada hallazgo necesita estado y fuentes.')
        if f['status'] == 'resolved' and not f.get('resolution_evidence'):
            raise ValueError('Un hallazgo resuelto necesita evidencia de resolución y verificación.')
    if not isinstance(dependencies, list):
        raise ValueError('dependencias.json debe ser una lista.')
    keys = sorted((r.get('ecosystem') or '', r.get('package'), r.get('version'), r.get('advisory')) for r in dependencies)
    if [list(k) for k in keys] != state.get('dependency_keys', []):
        raise ValueError('No elimines ni añadas avisos respecto al inventario de OSV; registra su decisión.')
    for row in dependencies:
        if row.get('decision') not in {'pending', 'applicable', 'not_applicable'}:
            raise ValueError('Decisión de dependencia inválida.')
        if row.get('scope') not in {'unknown', 'runtime', 'development', 'both'}:
            raise ValueError('Ámbito de dependencia inválido.')
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in
                   ('package', 'version', 'advisory', 'consumer', 'platform', 'condition', 'defense',
                    'priority', 'correction', 'verification')) or not citations(row.get('sources')):
            raise ValueError('Una dependencia necesita uso, condiciones, decisión, corrección y comprobación.')
        if row['decision'] != 'pending' and not row['sources']:
            raise ValueError('Confirmar o descartar una dependencia requiere fuentes.')
    return coverage, findings, dependencies


def comparisons(state, findings):
    base_path = state['provenance'].get('base_review')
    if not base_path:
        return [{'key': f['key'], 'change': 'sin base de comparación', 'title': f['title']} for f in findings]
    base = Path(base_path)
    old = read_json(base / 'estado.json', {})
    from storage import file_hash
    if file_hash(base / 'estado.json') != state['provenance'].get('base_state_hash') or not intact(base, old):
        raise ValueError('La revisión base cambió o perdió integridad.')
    previous = read_json(base / 'hallazgos.json')
    if previous is None:
        return [{'key': f['key'], 'change': 'comparación manual pendiente: base sin hallazgos estructurados',
                 'title': f['title']} for f in findings]
    prior = {f['key']: f for f in previous}
    current = {f['key']: f for f in findings}
    result = []
    for key in sorted(prior.keys() | current.keys()):
        f = current.get(key)
        change = 'pendiente: no reevaluado' if not f else (
            'resuelto' if f['status'] == 'resolved' else 'pendiente' if f['status'] == 'pending'
            else 'mantenido' if key in prior else 'nuevo')
        result.append({'key': key, 'change': change, 'title': (f or prior[key])['title']})
    return result


def render(folder, state):
    coverage, findings, dependencies = load(folder, state)
    comparison = comparisons(state, findings)
    h = lambda value: escape(str(value), quote=True)
    def sources(values):
        return ' · '.join('<code>' + h(s) + '</code>' for s in values) or 'Pendiente'
    p = state['provenance']
    labels = {'new': 'Nueva revisión; independencia no acreditada', 'extend': 'Ampliación de una revisión previa',
              'independent': 'Independiente: chat sin antecedentes declarado por el ejecutor'}
    text = [f'<section id="procedencia-revision"><h3>Procedencia</h3><p>Iris {h(state["agent_version"])} · {h(labels[p["mode"]])}</p>',
            f'<p>Base: {h(p.get("base_review") or "Sin base vinculada")}. Perfil: {h(state["source"]["profile"])}</p>',
            '<p>Exclusiones explícitas: ' + h(', '.join(state['source'].get('exclusions', [])) or 'Ninguna') + '.</p>',
            '<p>La declaración de contexto es del ejecutor; el script no puede inspeccionar ni borrar el historial del chat.</p>',
            '<ul>' + ''.join(f'<li>{h(name)}: {h(t.get("status"))}; motor {h(t.get("engine", "local"))}; caché {h(t.get("cache"))}</li>'
                            for name, t in state['tools'].items()) + '</ul></section>',
            '<section id="cobertura-revision"><h3>Cobertura por recorridos</h3>']
    changes = read_json(folder / 'cambios-entrada.json', {}).get('changes')
    if changes is not None:
        text.insert(3, '<p>Archivos respecto a la base: ' + ', '.join(
            h(label) + ': ' + str(len(changes.get(key, []))) for key, label in
            [('added', 'añadidos'), ('modified', 'modificados'), ('removed', 'eliminados')]) + '.</p>')
    for block in coverage:
        text.append(f'<details><summary>Bloque {block["block"]}: {h(block["state"])}</summary>')
        for field, title in [('entrypoints','Entradas'),('controls','Controles'),('consumers','Consumidores'),
                             ('new_sources','Fuentes contrastadas en esta revisión'),
                             ('reused_sources','Fuentes heredadas de revisiones previas'),('pending','Pendientes')]:
            text.append(f'<p><b>{title}:</b> {sources(block[field])}</p>')
        text.append('</details>')
    text += ['</section><section id="dependencias-revision"><h3>Aplicabilidad de dependencias</h3>',
             '<p>Las coincidencias de versión no demuestran explotación. Las versiones corregidas pueden corresponder a ramas distintas; no constituyen una actualización universal.</p>']
    if not dependencies:
        text.append('<p>Sin filas de avisos en esta preparación. Consultar el estado y alcance de OSV; no equivale a ausencia global de vulnerabilidades.</p>')
    for row in dependencies:
        text.append(f'<details><summary>{h(row["package"])} {h(row["version"])} · {h(row["advisory"])} · {h(row["decision"])}</summary>')
        for field, title in [('summary','Aviso'),('scope','Uso'),('consumer','Consumidor'),('platform','Plataforma'),
                             ('condition','Condición'),('defense','Protección'),('priority','Prioridad'),
                             ('correction','Corrección'),('verification','Comprobación')]:
            text.append(f'<p><b>{title}:</b> {h(row.get(field, "Pendiente"))}</p>')
        text += [f'<p>Versiones corregidas declaradas: {h(", ".join(row.get("fixed_versions", [])) or "Consultar aviso")}</p>',
                 '<p class="source">' + sources(row['sources']) + '</p></details>']
    text.append('</section><section id="cambios-revision"><h3>Cambios respecto a la base</h3>')
    if not comparison:
        text.append('<p>No se han registrado hallazgos estructurados; consultar cobertura y limitaciones.</p>')
    text += [f'<p>{h(row["key"])} · {h(row["change"])} · {h(row["title"])}</p>' for row in comparison]
    for f in findings:
        text.append(f'<p><b>{h(f["key"])}</b> · {h(f["severity"])} · {h(f["certainty"])}. Verificación: {h(f["verification"])}. '
                    + sources(f['sources']) + '</p>')
        if f.get('resolution_evidence'):
            text.append('<p>Evidencia de resolución: ' + h(f['resolution_evidence']) + '</p>')
    text.append('</section>')
    fragment = '\n'.join(text)
    write_json(folder / 'comparacion.json', comparison)
    atomic_text(folder / 'evidencia.html', fragment)
    return fragment
