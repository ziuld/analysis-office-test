"""Explain deterministic results without publishing raw data or source code."""
import json
import re
from collections import Counter
from arktic_office.resources.paths import resource_path

STATES = {'complete': 'Completado', 'ready': 'Completado', 'partial': 'Completado con limitaciones',
    'error': 'No se pudo completar', 'no_evaluado': 'No evaluado',
    'detecciones_por_validar': 'Con alertas pendientes de comprobar',
    'sin_detecciones_en_seleccion': 'Sin alertas en los archivos revisados'}


def narrative(tool):
    result, key = tool['result'], tool['id']
    paragraphs, findings = [], []
    state = STATES.get(tool['status'], 'Revisar el alcance de esta comprobación')
    alerts = result.get('findings', [])
    inputs = result.get('input_files', [])
    if key == 'D01':
        inventory = result.get('inventory', [])
        texts = sum(f.get('kind') == 'text' for f in inventory)
        paragraphs += [f'Se capturaron {len(inventory)} archivos del commit revisado: {texts} de texto y {len(inventory) - texts} de otros tipos.',
            'El inventario permite identificar las partes de la aplicación. Tener un archivo capturado no significa que un agente haya revisado todo su contenido.']
        excluded = result.get('excluded', [])
        if excluded:
            paragraphs.append(f'Quedaron fuera de la captura {len(excluded)} archivos; esta revisión no cubre su contenido.')
    elif key == 'D02':
        paragraphs += [f'La búsqueda de posibles credenciales recibió {len(inputs)} archivos y registró {len(alerts)} alertas.',
            'Los valores detectados no se muestran. Una coincidencia no demuestra que la credencial esté activa ni que permita acceder a un servicio.']
        if 'sin historial' in tool.get('detail', '').lower():
            paragraphs.append('Se revisaron los archivos del commit, sin analizar el historial de cambios de Git.')
        for alert in alerts:
            findings.append('Se detectó un posible secreto que requiere comprobar si es una credencial real, un valor de ejemplo o un falso positivo.' + location(alert))
    elif key == 'D03':
        paragraphs += [f'Se enviaron {len(inputs)} archivos de dependencias y se encontraron {len(alerts)} coincidencias entre versiones de paquetes y avisos públicos de vulnerabilidad.',
            'Estas coincidencias no equivalen a vulnerabilidades explotables confirmadas en la aplicación. Hay que comprobar si el paquete y la función afectados se utilizan en un flujo expuesto. No se asigna una gravedad que no esté respaldada.']
        if result.get('unevaluated_files'):
            paragraphs.append(f'No se pudieron evaluar las versiones de {len(result["unevaluated_files"])} archivos de dependencias.')
        for alert in alerts:
            package, separator, rest = str(alert.get('summary', '')).partition(' · ')
            advisory = rest.split('. ', 1)[0] if separator else ''
            if package and re.fullmatch(r'(?:CVE-|GHSA-|[A-Z][A-Z0-9]+-)[A-Za-z0-9., _-]+', advisory):
                findings.append(f'El paquete {package} coincide con el aviso {advisory}. Su efecto en la aplicación está pendiente de comprobar.' + location(alert))
            else:
                findings.append('Se registró una coincidencia de versión con un aviso público; falta comprobar su efecto en la aplicación.' + location(alert))
    elif key == 'D04':
        processed = result.get('processed_files')
        coverage = str(len(processed)) if isinstance(processed, list) else 'un número no registrado de'
        paragraphs += [f'El análisis estático revisó {coverage} archivos con las reglas disponibles y registró {len(alerts)} patrones que requieren revisión.',
            'Las reglas cubren determinados patrones y lenguajes. Una alerta necesita contrastarse con el origen de los datos y las protecciones del flujo; no demuestra por sí sola una vulnerabilidad.']
        rules = json.loads(resource_path('profiles', 'semgrep-rules.json').read_text())['rules']
        messages = {r['id']: r['message'] for r in rules}
        for alert in alerts:
            rule = re.search(r'arktic\.[\w-]+', str(alert.get('summary', '')))
            message = messages.get(rule[0], 'Patrón de código pendiente de comprobar.') if rule else 'Patrón de código pendiente de comprobar.'
            findings.append(message + location(alert))
    elif key == 'D05':
        coverage = result.get('file_coverage', [])
        counts = Counter(f.get('status') for f in coverage)
        paragraphs += [f'El mapa estructural procesó {counts["processed"]} archivos y no pudo indexar {counts["unsupported"]}; {counts["error"]} terminaron con error.',
            f'Se registraron {result.get("node_count", len(result.get("nodes", [])))} elementos y {result.get("edge_count", len(result.get("edges", [])))} relaciones entre ellos.',
            'El mapa ayuda a los agentes a localizar componentes y conexiones. No acredita su funcionamiento ni demuestra que una aplicación sea segura. Los archivos de texto no indexados siguen disponibles para consulta directa.']
        unresolved = result.get('unresolved_relations', 0)
        if unresolved:
            paragraphs.append(f'{unresolved} relaciones no pudieron vincularse completamente con los elementos registrados.')
        for f in coverage:
            if f.get('status') != 'processed':
                reason = {'no_static_parser': 'su formato no tiene un analizador compatible',
                    'unsupported_json_data_schema': 'el indexador no reconoce este esquema de datos',
                    'unsupported_yaml_dialect_or_data_schema': 'el indexador no reconoce este formato de configuración',
                    'yaml_structure_unavailable_after_secret_redaction': 'ocultar posibles secretos impide interpretar su estructura'}.get(f.get('reason'), 'el analizador no completó su interpretación')
                findings.append(f'No se indexó {f["path"]}: {reason}.')
    if tool['status'] in {'no_evaluado', 'error'}:
        paragraphs.insert(0, 'Esta herramienta no completó la evaluación. La ausencia de alertas en su salida no puede interpretarse como un resultado favorable.')
    elif key in {'D02', 'D03', 'D04'} and not alerts:
        paragraphs.append('No se registraron alertas en el alcance indicado. Esto no descarta problemas fuera de las reglas o archivos evaluados.')
    return state, paragraphs, findings


def location(alert):
    path = alert.get('path')
    if not path:
        return ''
    line = alert.get('line')
    return ' Localización: ' + str(path) + (f', línea {line}.' if isinstance(line, int) else '.')
