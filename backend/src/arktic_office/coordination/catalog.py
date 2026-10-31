"""Single roster consumed by Core and the office; legacy roles stay out of it."""
import json
from arktic_office.resources.paths import resource_path


def catalog():
    agents = json.loads(resource_path('profiles', 'agents.json').read_text(encoding='utf-8'))
    from arktic_office.config.models import profile
    roster = [{'id': 'coordinator', 'person': 'Akira', 'name': 'Coordinador', 'color': '#38bdf8'},
              *[{k: a[k] for k in ('id', 'person', 'name', 'color')} for a in agents]]
    return [{**a, **{k: profile(a['id'])[k] for k in ('model', 'reasoning')}} for a in roster]
