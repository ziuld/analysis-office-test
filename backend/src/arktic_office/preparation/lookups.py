"""Bounded local retrieval of published answers and deterministic outputs."""
import json
from arktic_office.core.errors import AuditError


def source_ranges(refs):
    grouped = {}
    for ref in refs:
        if isinstance(ref,dict) and isinstance(ref.get('path'),str) and type(ref.get('line')) is int:
            grouped.setdefault(ref['path'],set()).add(ref['line'])
    result = []
    for path,lines in sorted(grouped.items()):
        for line in sorted(lines):
            if result and result[-1]['path']==path and result[-1]['end_line']+1==line:
                result[-1]['end_line']=line
            else:
                result.append({'path':path,'start_line':line,'end_line':line})
    return result


def questions(evidence, request):
    from arktic_office.reporting.questionnaire import catalog
    ids = request['questions']
    offset = request.get('offset',0)
    valid = {q['id'] for q in catalog()}
    if (set(request)-{'questions','offset'} or not isinstance(ids,list) or not 1<=len(ids)<=4
        or any(not isinstance(q,str) or q not in valid for q in ids) or len(set(ids))!=len(ids)
        or type(offset) is not int or offset<0):
        raise AuditError('Consulta de respuestas inválida: usa questions:[hasta 4 IDs Q01–Q40], offset opcional para sus fuentes.')
    if not getattr(evidence,'knowledge',None):
        raise AuditError('No hay información compartida disponible para esta revisión.')
    answers,unavailable=[],[]
    for question in ids:
        try:
            answer=evidence.knowledge.answer(evidence.run_id,question)
        except AuditError:
            unavailable.append(question)
            continue
        sources=source_ranges(answer.get('evidencia',[]))
        # Full original text/state, compact source locations; full quotes stay in Core.
        answers.append({'answer':{k:v for k,v in answer.items() if k not in {'evidencia','referencias_originales'}},
                        'original_reference_labels':answer.get('referencias_originales',[]),
                        'sources':sources[offset:offset+20], 'sources_total':len(sources),
                        'next_offset':offset+20 if offset+20<len(sources) else None})
    return {'fragments':[], 'answers':answers, 'unavailable':unavailable,
            **({'error':'No hay respuesta publicada para los IDs solicitados en esta revisión; no se despierta otro modelo.'} if not answers else {}),
            'limitation':'Aportaciones originales de sus autores. Sus IDs F pertenecen a otra selección; lee las rutas con tus propias fuentes antes de citarlas. No se ha consultado ningún modelo.'}


def tool(evidence, request):
    if set(request)-{'tool','offset','limit','query','paths','index'} or not isinstance(request['tool'],str):
        raise AuditError('Consulta determinista inválida.')
    offset,limit=request.get('offset',0),request.get('limit',20)
    query,paths=request.get('query',''),request.get('paths',[])
    if (type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=20
        or not isinstance(query,str) or len(query)>120 or not isinstance(paths,list) or len(paths)>3
        or any(not isinstance(p,str) for p in paths) or type(request.get('index',False)) is not bool):
        raise AuditError('Filtros/página determinista inválidos: limit 1–20, query hasta 120 caracteres y hasta 3 paths.')
    item=next((t for t in getattr(evidence,'deterministic',{}).get('tools',[]) if t['id']==request['tool']),None)
    if item is None:
        raise AuditError('Herramienta no disponible en esta revisión.')
    key='inventory' if item['id']=='D01' else 'file_coverage' if item['id']=='D05' else 'findings'
    all_values=item['result'].get(key,[])
    values=[v for v in all_values if (not paths or v.get('path') in paths)
            and (not query or query.casefold() in json.dumps(v,ensure_ascii=False).casefold())]
    if request.get('index'):
        values=[{k:v[k] for k in ('path','line','end_line','summary','rule_id','check_id','severity','status','reason') if k in v} for v in values]
        key='entries'
    page,used=[],0
    for value in values[offset:offset+limit]:
        size=len(json.dumps(value,ensure_ascii=False).encode())
        if used+size>12000:
            if not page:
                raise AuditError('Este elemento supera 12000 bytes; consulta las fuentes por su ruta. No se repite automáticamente esta página.')
            break
        page.append(value);used+=size
    return {'fragments':[], 'relations':[], 'symbols':[], 'tool':item['id'], 'status':item['status'],
            'detail':item['detail'], key:page, 'total':len(values), 'unfiltered_total':len(all_values), 'offset':offset,
            'next_offset':offset+len(page) if offset+len(page)<len(values) else None,
            'limitation':'Consulta local paginada; alertas de herramientas, no conclusiones de un especialista. Original completo conservado en Core.'}
