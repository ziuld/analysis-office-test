"""Deterministic executive report: no new findings or model calls."""
from html import escape
from brief import text, references
from security import CONTROLS, SEVERITIES

LABELS = {"critica": "🔴 Crítica", "alta": "🔴 Alta", "media": "🟡 Media", "baja": "🔵 Baja", "informativa": "🔵 Informativa"}
STATUS = {"hallazgo": "Hallazgo identificado", "evidencia_favorable_limitada": "Evidencia favorable limitada", "no_evaluado": "⚪ No evaluado", "no_aplica": "No aplica en el contexto leído"}


def risks(data):
    items = [{**x, "certeza": section} for section in ("confirmados", "indicios") for x in data.get(section, []) if x.get("severidad", "informativa") != "informativa"]
    return sorted(items, key=lambda x: (SEVERITIES.index(x["severidad"]), x["certeza"] != "confirmados"))


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
    from report_view import render_markdown as render
    return render(data, snapshot, model)


def render_html(data, snapshot, model=""):
    from report_view import render_html as render
    return render(data, snapshot, model)
