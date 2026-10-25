"""Remove empty presentation blocks, retaining original records and coverage on disk."""
from html import escape
from html.parser import HTMLParser


class Node:
    def __init__(self, tag="", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"img", "br", "hr", "meta", "link", "input", "source", "wbr", "area", "base", "col", "embed", "param", "track"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if len(self.stack) > 1 and self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_entityref(self, name):
        self.handle_data("&" + name + ";")

    def handle_charref(self, name):
        self.handle_data("&#" + name + ";")


def availability(v):
    known = [r for r in v["operations"] if r["estado"] != "no_evaluado"]
    azure = v["azure"] and v["azure"].get("estado") == "propuesta_preliminar"
    return {"known": known, "azure": azure, "security": bool(v["entries"] or any(c["estado"] != "no_evaluado" for c in v["data"].get("controles", [])))}


def compact_html(html, v):
    a = availability(v)
    hidden = set()
    for condition, ids in (
        (not v["observed"], {"registro"}),
        (not v["pending"], {"indicios"}),
        (not v["entries"], {"riesgos-resumen", "controles-objetivo"}),
        (not a["known"], {"datos-operacion", "continuidad"}),
        (not any(r["aspecto"] not in {"disponibilidad", "capacidad"} for r in a["known"]), {"continuidad"}),
        (not v["components"], {"inventario"}),
        (not v["summary"] and not v.get("purpose"), {"resumen-fuentes"}),
        (not v["flow"].get("componentes"), {"flujo-fuentes"}),
        (not a["security"], {"seguridad", "controles"}),
        (not a["azure"], {"azure", "entrega"}),
        (not v["decision"], {"decision", "aceptacion"}),
        (not v["decision"].get("evidencia_pendiente"), {"aceptacion"}),
        (not v["entries"] and not a["azure"] and not v["decision"], {"situacion-objetivo"}),
        (not a["security"] and not a["known"] and not v["flow"].get("componentes") and not v["data"].get("confirmados") and not v["data"].get("indicios"), {"situacion-actual"}),
        (not any(x.get("severidad") == "informativa" for s in ("confirmados", "indicios") for x in v["data"].get(s, [])), {"aportaciones"}),
    ):
        if condition:
            hidden.update(ids)
    start = html.index("<body>") + len("<body>")
    end = html.rindex("</body>")
    document = Document()
    document.feed(html[start:end])
    def prune(node):
        children = []
        for child in node.children:
            if not isinstance(child, Node):
                children.append(child)
                continue
            classes = child.attrs.get("class", "").split()
            if child.attrs.get("id") in hidden or (not v["entries"] and ("stats" in classes or "clues" in classes)) or ("operation" in classes and not v["flow"].get("componentes")) or ("operation-status" in classes and not any(r["aspecto"] in {"disponibilidad", "capacidad"} for r in a["known"])):
                continue
            prune(child)
            children.append(child)
        node.children = children
    prune(document.root)
    ids = set()
    def collect(node):
        if node.attrs.get("id"):
            ids.add(node.attrs["id"])
        for child in node.children:
            if isinstance(child, Node):
                collect(child)
    collect(document.root)
    def render(node):
        if isinstance(node, str):
            return node
        if node.tag == "a" and node.attrs.get("href", "").startswith("#") and node.attrs["href"][1:] not in ids:
            return ""
        content = "".join(render(x) for x in node.children)
        if not node.tag:
            return content
        attrs = "".join(" " + k + ('="' + escape(value, quote=True) + '"' if value is not None else "") for k, value in node.attrs.items())
        return "<" + node.tag + attrs + ">" + content + ("" if node.tag in {"img", "br", "hr", "input", "source", "wbr"} else "</" + node.tag + ">")
    return html[:start] + render(document.root) + html[end:]


def compact_markdown(markdown, v):
    a = availability(v)
    skip = set()
    for condition, titles in (
        (not v["flow"].get("componentes"), {"Flujo actual de la aplicación"}),
        (not v["entries"], {"Riesgos", "Controles y mejoras"}),
        (not a["known"], {"Base de datos y recuperación"}),
        (not a["security"], {"Qué pudo evaluar Seguridad"}),
        (not a["azure"], {"Arquitectura propuesta en Azure"}),
        (not v["decision"], {"Decisión y siguientes pasos"}),
        (not v["components"], {"Inventario"}),
    ):
        if condition:
            skip.update(titles)
    lines, dropping = [], False
    for line in markdown.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            dropping = line.startswith("### ") and line[4:] in skip
        if not dropping:
            lines.append(line)
    # Empty tables and headings should not survive the section filtering.
    cleaned, i = [], 0
    while i < len(lines):
        if lines[i].startswith('|'):
            end = i
            while end < len(lines) and lines[end].startswith('|'):
                end += 1
            if end - i > 2:
                cleaned.extend(lines[i:end])
            i = end
        else:
            cleaned.append(lines[i])
            i += 1
    lines = cleaned
    result = []
    for i, line in enumerate(lines):
        if line.startswith("## ") or line.startswith("### "):
            following = next((x for x in lines[i + 1:] if x.strip()), "")
            level = len(line) - len(line.lstrip('#'))
            following_level = len(following) - len(following.lstrip('#'))
            if not following or following_level and following_level <= level:
                continue
        result.append(line)
    return "\n".join(result) + "\n"
