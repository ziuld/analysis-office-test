# Contrato del informe Iris

El informe se genera exclusivamente con `scripts/iris.py render --review "<revisión>"` desde los JSON de la revisión. No copies ni rellenes HTML a mano. `report_renderer.py` usa la plantilla Arktic, mantiene CSS, logotipo y navegación, escapa los textos y genera la estructura fija. `finish` compara el HTML y las siete fichas con ese resultado; cambiar clases, tarjetas o encabezados impide cerrar.

El destino obligatorio es `<agente instalado en el proyecto>/.local/revisiones/<fecha-id>/informe-iris.html`. Se crea automáticamente el almacenamiento al iniciar. Ante falta de permisos, pide acceso para esa ruta y reintenta; sin autorización no hay destino alternativo.

## Datos que completa la IA

`prepare` crea `informe.json` con `schema_version: 1`, los 40 IDs y las siete conclusiones inicializadas como pendientes. Edita ese archivo por bloques, sin cambiar sus claves de estructura:

- `project`, `status`, `scope`: textos del encabezado que describen proyecto, cobertura y captura.
- `summary.application`, `summary.connections`, `summary.priorities`: descripción, relaciones y prioridades basadas en evidencia.
- `summary.strengths`: lista de objetos con `text`, `sources` (citas) y opcionalmente `question` (Qxx a la que enlazar).
- `summary.limits`: lista de textos con omisiones y comprobaciones pendientes.
- `blocks`: siete objetos ordenados con `number` y `conclusion`. El título y orden de preguntas se toman de las guías; el estado de cada bloque se toma de `cobertura.json`.
- `answers`: objeto Q01–Q40. Cada respuesta contiene `state`, `text`, `sources` y `pending`. Usa texto plano; no introduzcas etiquetas HTML. Una respuesta parcial o no comprobada necesita un pendiente concreto.
- `annexes`: lista de objetos `title` y `paragraphs` (lista de textos). Registra fuente/captura, métodos, modelo/esfuerzo conocidos u «modelo de la sesión actual», detalle de Graphify, escáneres y límites. El generador agrega automáticamente procedencia, cobertura, aplicabilidad y comparación desde la evidencia estructurada.

Estados de respuesta: **Respondida**, **Parcial**, **No comprobada**, **No aplica**. Una afirmación técnica o hallazgo lleva fuentes verificadas `ruta/relativa:línea` o `ruta/relativa:inicio-fin`. Conserva condiciones, defensas y contradicciones. La lectura estática no demuestra configuración desplegada o explotación. Si no hay evidencia, conserva la pregunta y explica qué falta.

## Hallazgos y evidencia

Completa [la evidencia estructurada](evidencia-revisiones.md). `hallazgos.json` es la única fuente de riesgos del informe y comparación; no los dupliques en otro HTML. Cada objeto requiere:

~~~json
{
  "key": "causa:recorrido-estable",
  "id": "R01",
  "block": 6,
  "title": "Consecuencia posible",
  "severity": "Media",
  "certainty": "Indicio con defensa pendiente",
  "status": "pending",
  "observation": "Qué se observó",
  "effect": "Impacto posible",
  "conditions": "Condiciones y protecciones existentes",
  "action": "Cambio propuesto",
  "verification": "Cómo confirmarlo o descartarlo",
  "sources": ["ruta/relativa.ts:10-20"]
}
~~~

Gravedades: Crítica, Alta, Media o Baja, justificadas por impacto y condiciones; usa «Sin determinar» si falta evidencia para graduar. La certeza es independiente. Los estados `open`, `pending`, `resolved` sirven para comparación; resolved exige además `resolution_evidence` y verificación real. Una omisión no implica resolución.

## Tres secciones con diseño estable

1. **Resumen ejecutivo:** cuatro grupos fijos: Aplicación y conexiones, Prioridades de Iris (hasta diez riesgos ordenados por gravedad, con acción y condición), Protecciones comprobadas y Alcance pendiente. Conserva paneles blancos, espacios y enlaces al detalle. Herramientas no completadas aparecen como límite automáticamente.
2. **Análisis por preguntas:** exactamente siete desplegables ordenados y Q01–Q40 una vez cada una. Cada respuesta usa etiqueta `question-id`, encabezado h4, texto, citas y pendiente. Cada riesgo se coloca en su bloque de origen y conserva observación, efecto, condiciones/defensas, acción y verificación.
3. **Anexos deterministas:** notas del método y evidencia generada de los JSON. Registra versión y perfil reales. Revisiones antiguas sin versión se identifican como «versión no registrada»; no se las reetiqueta retrospectivamente.

## Cierre

Al cerrar cada bloque actualiza sus respuestas, conclusión y cobertura y ejecuta render. Este comando guarda las siete fichas; las aún abiertas mantienen Pendiente. Al finalizar los siete bloques ejecuta render y finish. El cierre verifica ubicación, vigencia del código/perfil, estructura, recursos embebidos, citas y correspondencia exacta de HTML/fichas/JSON. Sus comprobaciones no sustituyen investigar el contenido. Usa cobertura parcial si faltan herramientas, aplicabilidad o comprobaciones necesarias.
