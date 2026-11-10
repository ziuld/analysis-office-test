"""Resolve the ordered roster and independently packaged specialist profiles."""
import json
import re

from arktic_office.core.errors import AuditError
from arktic_office.resources.paths import resource_path


def read_profiles():
    from arktic_office.reporting.questionnaire import catalog

    profiles = resource_path('profiles')
    registered = json.loads((profiles / 'agents.json').read_text(encoding='utf-8'))
    active = []
    seen = set()
    for entry in registered:
        role = entry['id']
        if not re.fullmatch(r'[a-z][a-z0-9-]*', role) or role in seen:
            raise AuditError('Identificador de agente inválido o duplicado: ' + role)
        seen.add(role)
        if set(entry) == {'id'}:
            folder = profiles / 'agents' / role
            if not folder.is_dir():
                continue
            entry = json.loads((folder / 'agent.json').read_text(encoding='utf-8'))
            expected = [question['id'] for question in catalog(role)]
            if entry.get('id') != role or entry.get('questions') != expected:
                raise AuditError('La identidad o las preguntas del agente no coinciden con el catálogo: ' + role)
        active.append(entry)
    return tuple(active)
