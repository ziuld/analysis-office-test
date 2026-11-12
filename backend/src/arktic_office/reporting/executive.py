"""Deterministic executive report: no new findings or model calls."""
from html import escape
from arktic_office.reporting.brief import text, references
from arktic_office.reporting.security import CONTROLS, SEVERITIES

LABELS = {"critica": "🔴 Crítica", "alta": "🔴 Alta", "media": "🟡 Media", "baja": "🔵 Baja", "informativa": "🔵 Informativa"}
STATUS = {"hallazgo": "Hallazgo identificado", "evidencia_favorable_limitada": "Evidencia favorable limitada", "no_evaluado": "⚪ No evaluado", "no_aplica": "No aplica en el contexto leído"}


def risks(data):
    items = []
    ungraded_types = {"vulnerabilidad"} if data.get("full_stack") else set()
    if data.get("task_workflows") in {"pilot", "all"}:
        ungraded_types = {"vulnerabilidad", "operacion", "coste"}
    for section in ("confirmados", "indicios"):
        for item in data.get(section, []):
            severity = item.get("severidad", "informativa")
            if severity != "informativa":
                items.append({**item, "certeza": section})
            elif item.get("tipo") in ungraded_types and item.get("evidencia"):
                items.append({**item, "certeza": section, "severidad": severity})
    return sorted(items, key=lambda x: ((SEVERITIES.index(x["severidad"]) if x["severidad"] in SEVERITIES else len(SEVERITIES)), x["certeza"] != "confirmados"))


def components(data):
    result, seen = [], set()
    for section in ("confirmados", "indicios"):
        for x in data.get(section, []):
            c = x.get("componente")
            if c:
                key = (c["nombre"].strip().casefold(), c["tecnologia"].strip().casefold(), section)
                if key not in seen:
                    result.append({**x, "certeza": section})
                    seen.add(key)
    return result


def primary_components(data):
    groups = {}
    for item in sorted(components(data), key=lambda x: "inventory" not in x.get("celulas", [])):
        key = (item["componente"]["nombre"].strip().casefold(), item["certeza"])
        groups.setdefault(key, item)
    return list(groups.values())


def render_markdown(data, snapshot, model=""):
    from arktic_office.reporting.view import render_markdown as render
    return render(data, snapshot, model)


def render_html(data, snapshot, model=""):
    from arktic_office.reporting.view import render_html as render
    return render(data, snapshot, model)
