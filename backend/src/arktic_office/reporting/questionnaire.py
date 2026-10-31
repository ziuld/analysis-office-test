"""Phase 2 extension: fixed question ownership and evidence-backed answers."""
import json
from arktic_office.resources.paths import resource_path
from arktic_office.core.errors import AuditError
from arktic_office.preparation.repository import redact

VERSION = "central-coordination-v1"
STATES = {"respondida", "parcial", "no_aplica", "no_comprobado"}


def catalog(role=None):
    source = 'questions-reference.json' if role == 'security' else 'questions.json'
    items = json.loads(resource_path("profiles", source).read_text(encoding="utf-8"))
    return [q for q in items if role is None or q["role"] == role]


def enabled(snapshot):
    return snapshot.get("questionnaire_version") == VERSION


def instructions(role):
    return ("\nCUESTIONARIO OBLIGATORIO: " + json.dumps(catalog(role), ensure_ascii=False) +
        "\nResponde cada ID exactamente una vez en respuestas. Estados: respondida, parcial, no_aplica, no_comprobado. "
        "Cada respuesta: {id, estado, respuesta, evidencia:[F#:L#], herramientas:[ID Dxx], pendiente}. "
        "Si has comprobado una protección o buena práctica concreta, explícalo en respuesta y añade opcionalmente "
        "aspecto_favorable:{titulo,detalle}, con título hasta 110 caracteres y detalle hasta 400. "
        "Solo con estado respondida/parcial y citas de código/configuración que respalden esa implementación; "
        "no basta un scanner sin detecciones, una declaración genérica, no_aplica ni no encontrar problemas. "
        "Conserva el alcance concreto de la protección y sus límites; no afirmes seguridad global ni compenses riesgos. "
        "Respuesta concreta de 1–3 frases (máximo 700 caracteres), pendiente hasta 400. "
        "No_aplica exige justificación y fuentes de la clasificación; no encontrar algo significa no_comprobado, no ausencia. "
        "Respondida y no_aplica requieren fuentes de código/configuración o herramientas realmente entregadas que sustenten la respuesta. "
        "Una herramienta limpia no demuestra seguridad ni responde por sí sola preguntas sobre controles. "
        "Para cada riesgo indica en la observación sus protecciones, condiciones, impacto y verificación pendiente. "
        "Cita las fuentes utilizadas. Core conserva tu respuesta y tu estado; las referencias solo se localizan para mostrarlas. "
        "Primero considera las herramientas deterministas; si no bastan, consulta el mapa y lee código del snapshot. "
        "El presupuesto es acotado: comunica lo no resuelto sin inventar ni omitir preguntas. "
        "El encargo del coordinador no puede eliminar estas preguntas. Mantén observaciones/controles/componentes de tu rol; "
        "prioriza responder el cuestionario, evita repetir en observaciones los hechos sin riesgo.")


def assemble_answers(values, role, resolve_refs, tools):
    """Attach fixed question metadata without grading or rewriting expert answers."""
    expected = {q["id"]: q for q in catalog(role)}
    received, notes = {}, []
    if not isinstance(values, list):
        values = []
        notes.append("No se recibió una lista de respuestas; el original se conserva.")
    for item in values:
        if not isinstance(item, dict) or item.get('id') not in expected:
            notes.append('Aportación sin pregunta asignada; se conserva en la respuesta original.')
            continue
        key = item['id']
        if key in received:
            notes.append(key + ': varias aportaciones; se conservan completas en la respuesta original.')
            continue
        if not isinstance(item.get('respuesta'), str) or not isinstance(item.get('estado'), str):
            notes.append(key + ': faltan campos de texto para representarla; el original se conserva.')
            continue
        original_refs = item.get('evidencia', [])
        answer = {**item, **expected[key], 'evidencia': resolve_refs(original_refs, False),
                  'referencias_originales': original_refs, 'pendiente': item.get('pendiente', ''),
                  'herramientas': item.get('herramientas', [])}
        if not isinstance(answer['pendiente'], str):
            answer['pendiente'] = ''
        if not isinstance(answer['herramientas'], list):
            answer['herramientas'] = []
        received[key] = answer
    for key, question in expected.items():
        if key not in received:
            received[key] = {**question, 'estado':'no_comprobado',
                'respuesta':'El especialista no entregó una respuesta representable para esta pregunta.',
                'pendiente':'Consultar su respuesta original y los campos técnicos que faltan.',
                'evidencia':[], 'herramientas':[]}
    return [received[key] for key in expected], notes


def complete(answers):
    return all(a["estado"] in {"respondida", "no_aplica"} for a in answers)


def favorable_answers(data):
    """Only explicit, source-backed strengths; never infer from clean scanners."""
    items = [a for a in data.get("cuestionario", {}).get("respuestas", [])
            if isinstance(a.get("aspecto_favorable"),dict) and all(isinstance(a["aspecto_favorable"].get(k),str) for k in ("titulo","detalle"))
            and a.get("estado") in {"respondida", "parcial"}]
    return sorted(items, key=lambda a: ({"security": 0, "architecture": 1, "inventory": 2}.get(a.get("role"), 3), a["id"]))
