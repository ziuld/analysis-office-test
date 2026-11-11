"""Single roster consumed by Core and the office; legacy roles stay out of it."""
from arktic_office.config.agents import read_profiles


def catalog():
    agents = (*read_profiles(), *read_profiles(full_stack=True))
    from arktic_office.config.models import profile
    roster = [{'id': 'coordinator', 'person': 'Akira', 'name': 'Coordinador', 'color': '#38bdf8'},
              *[{k: a[k] for k in ('id', 'person', 'name', 'color')} for a in agents]]
    return [{**a, **{k: profile(a['id'])[k] for k in ('model', 'reasoning')}} for a in roster]
