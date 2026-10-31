"""Lossless text view of specialist output, separate from Akira's synthesis."""
from html import escape

LABELS = {'respuestas':'Respuestas originales', 'observaciones':'Observaciones originales',
          'componentes':'Componentes', 'conexiones':'Conexiones', 'controles':'Controles',
          'pendientes':'Pendientes', 'confirmados':'Conclusiones del especialista', 'indicios':'Indicios',
          'dudas':'Dudas', 'respuesta':'Respuesta', 'estado':'Estado indicado por el especialista',
          'evidencia':'Referencias indicadas', 'observacion':'Observación'}


def human_html(value):
    if isinstance(value,dict):
        return '<dl>'+''.join('<dt>'+escape(LABELS.get(k,k))+'</dt><dd>'+human_html(v)+'</dd>' for k,v in value.items())+'</dl>'
    if isinstance(value,list):
        return '<ul>'+''.join('<li>'+human_html(v)+'</li>' for v in value)+'</ul>'
    return '<p style="white-space:pre-wrap;overflow-wrap:anywhere">'+escape(str(value) if value is not None else '')+'</p>'


def html(data):
    entries = data.get('aportaciones_agentes',[])
    if not entries:
        return ''
    return '<section id="respuestas-originales"><h2>Aportaciones originales de los especialistas</h2>'+''.join(
        '<details><summary>'+escape(e['nombre'])+'</summary>'+human_html(e['respuesta'])+'</details>' for e in entries)+'</section>'


def human_markdown(value, depth=0):
    if isinstance(value,dict):
        return '\n'.join('  '*depth+'- **'+LABELS.get(k,k)+'**\n'+human_markdown(v,depth+1) for k,v in value.items())
    if isinstance(value,list):
        return '\n'.join(human_markdown(v,depth) for v in value)
    return '  '*depth+str(value if value is not None else '')


def markdown(data):
    entries = data.get('aportaciones_agentes',[])
    if not entries:
        return ''
    return '\n## Aportaciones originales de los especialistas\n'+''.join(
        '\n### '+e['nombre']+'\n\n'+human_markdown(e['respuesta'])+'\n' for e in entries)
