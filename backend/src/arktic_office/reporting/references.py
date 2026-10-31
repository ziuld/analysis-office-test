"""Locate labels for presentation, without accepting/rejecting expert conclusions."""
from copy import deepcopy
import re
from arktic_office.core.errors import AuditError


def receive_proposal(value):
    """Only types/indexes needed by the renderer, never suitability or evidence grading."""
    if any(not isinstance(value.get(k),str) for k in ('estado','destino','resumen','justificacion')):
        raise AuditError('Faltan campos de texto en la propuesta; original conservado.')
    if any(not isinstance(value.get(k),list) for k in ('supuestos','servicios','pasos','pendientes','evidencia')):
        raise AuditError('Faltan listas en la propuesta; original conservado.')
    if any(not isinstance(x,str) for k in ('supuestos','pasos','pendientes') for x in value[k]):
        raise AuditError('Lista de texto no representable; original conservado.')
    if any(not isinstance(s,dict) or any(not isinstance(s.get(k),str) for k in ('servicio','uso')) for s in value['servicios']):
        raise AuditError('Servicio no representable; original conservado.')
    for edge in value.get('conexiones',[]):
        if (not isinstance(edge,dict) or not isinstance(edge.get('descripcion'),str)
            or any(type(edge.get(k)) is not int or not 1 <= edge[k] <= len(value['servicios']) for k in ('origen','destino'))):
            raise AuditError('Conexión sin extremos representables; original conservado.')
    return value


def locate(values, index):
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        if isinstance(value, dict):
            if isinstance(value.get('path'), str) and type(value.get('line')) is int:
                ref = {**value, 'quote':value.get('quote', '')}
                if not isinstance(ref['quote'], str):
                    ref['quote'] = ''
                if ref not in result:
                    result.append(ref)
            continue
        if not isinstance(value, str):
            continue
        match = re.fullmatch(r'(F[1-9][0-9]*):L([1-9][0-9]*)(?:-L([1-9][0-9]*))?',value)
        if not match:
            continue
        first, last = int(match[2]),int(match[3] or match[2])
        # An unrepresentable range stays in referencias_originales, never changes an answer.
        if last < first or last-first >= 200:
            continue
        for line in range(first,last+1):
            ref = index.get(f'{match[1]}:L{line}')
            if ref and ref not in result and ref['quote'].strip():
                result.append(dict(ref))
    return result


def receive_legacy(data, snapshot, role):
    from arktic_office.reporting.reports import evidence_index
    from arktic_office.reporting.questionnaire import enabled, assemble_answers
    if any(not isinstance(data.get(s,[]),list) for s in ('confirmados','indicios','dudas','controles')):
        raise AuditError('Formato técnico de listas inválido; se conserva la respuesta original.')
    def format_refs(value):
        if isinstance(value,list):
            return [format_refs(v) for v in value]
        if isinstance(value,dict):
            output = {k:format_refs(v) for k,v in value.items() if k != 'evidencia'}
            if 'evidencia' in value:
                output.update(evidencia=locate(value['evidencia'],index), referencias_originales=deepcopy(value['evidencia']))
            return output
        return value
    index = evidence_index(snapshot)
    result = format_refs(data)
    result.update(schema_version=3, respuesta_original=deepcopy(data), recepcion='sin_revision_automatica')
    index = evidence_index(snapshot)
    for section in ('confirmados','indicios','controles'):
        result.setdefault(section,[])
        for item in result[section]:
            if not isinstance(item,dict):
                raise AuditError('Elemento no representable; se conserva la respuesta original.')
            if section != 'controles':
                if not isinstance(item.get('observacion'),str):
                    raise AuditError('Falta texto de la aportación; se conserva la respuesta original.')
                defaults = {'tema':'responsabilidades','importancia':'','pendiente':'', 'accion':'',
                            'condiciones':'','severidad':'informativa','control':'contexto'}
                for key,value in defaults.items():
                    item.setdefault(key,value)
    result.setdefault('dudas',[])
    notes = []
    if enabled(snapshot):
        tools = {t['id'] for t in snapshot.get('deterministic_results',{}).get('tools',[])}
        result['respuestas'],notes = assemble_answers(data.get('respuestas'),role,lambda refs,required=False:locate(refs,index),tools)
    return result,{},notes
