"""Lossless text view of specialist output, separate from Akira's synthesis."""
import json
import re
from html import escape


def original_text(entry):
    raw = entry.get('texto_original', entry['respuesta'])
    return raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, indent=2)


def html(data):
    entries = data.get('aportaciones_agentes', [])
    if not entries:
        return ''
    blocks = []
    for entry in entries:
        name = escape(entry['nombre'])
        text = escape(original_text(entry), quote=False)
        blocks.append(f'<details><summary>{name}</summary>'
                      f'<pre class="original-response" tabindex="0" aria-label="Respuesta original de {name}">'
                      f'<code>{text}</code></pre></details>')
    return '<section id="respuestas-originales"><h2>Aportaciones originales de los especialistas</h2>' + ''.join(blocks) + '</section>'


def markdown(data):
    entries = data.get('aportaciones_agentes', [])
    if not entries:
        return ''
    blocks = []
    for entry in entries:
        text = original_text(entry)
        longest = max((len(match) for match in re.findall(r'`+', text)), default=0)
        fence = '`' * max(3, longest + 1)
        language = 'json' if isinstance(entry['respuesta'], (dict, list)) else 'text'
        separator = '' if text.endswith('\n') else '\n'
        blocks.append(f"\n### {entry['nombre']}\n\n{fence}{language}\n{text}{separator}{fence}\n")
    return '\n## Aportaciones originales de los especialistas\n' + ''.join(blocks)
