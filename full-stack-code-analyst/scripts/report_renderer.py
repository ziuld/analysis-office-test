"""Canonical Iris report: the assistant supplies data, never layout or executable HTML."""
from html import escape
import re

from storage import KIT, atomic_text, read_json, write_json
import review_evidence

STATES = {'Respondida', 'Parcial', 'No comprobada', 'No aplica'}
SEVERITIES = {'Crítica': 0, 'Alta': 1, 'Media': 2, 'Baja': 3}


def guides():
    result = []
    for number, path in enumerate(sorted((KIT / 'skills/revisar-codigo/referencias').glob('*.md')), 1):
        text = path.read_text(encoding='utf-8-sig')
        result.append((number, text.splitlines()[0].lstrip('# '), re.findall(r'^### (Q\d{2}) · (.+)$', text, re.M)))
    if len(result) != 7 or {q for _, _, questions in result for q, _ in questions} != {f'Q{i:02}' for i in range(1, 41)}:
        raise ValueError('Las guías deben definir siete bloques y Q01–Q40.')
    return result


def initialize(folder, state):
    write_json(folder / 'informe.json', dict(schema_version=1, project='Web / proyecto · Iris',
        status='Revisión estática parcial · validaciones pendientes',
        scope=f'Copia de trabajo · {state["source"].get("commit") or "sin commit"}',
        summary=dict(application='Pendiente de revisar.', connections='Pendiente de revisar.',
                     priorities='Pendiente de sintetizar.', strengths=[], limits=['Revisión aún sin completar.']),
        blocks=[dict(number=n, conclusion='Pendiente de revisar.') for n, _, _ in guides()],
        answers={q: dict(state='No comprobada', text='Pendiente de revisar.', sources=[], pending='Completar este recorrido.')
                 for _, _, questions in guides() for q, _ in questions},
        annexes=[dict(title='Método y límites', paragraphs=['Completar métodos, herramientas, modelo conocido y omisiones.'])]))


def build(folder, state):
    import iris_core
    data = read_json(folder / 'informe.json')
    if isinstance(data, dict):
        data = {**data, 'tools': state['tools']}
    coverage, findings, _ = review_evidence.load(folder, state)
    return iris_core.build(data, coverage, findings, guides(),
        (KIT / 'plantillas/informe.html').read_text(encoding='utf8'), review_evidence.render(folder, state))


def render(folder, state):
    html, fichas = build(folder, state)
    atomic_text(folder / 'informe-iris.html', html)
    for name, contents in fichas.items():
        atomic_text(folder / 'bloques' / name, contents)
    return html
