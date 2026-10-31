# Prueba real de mapas y consultas — 31/10/2026

La prueba reduce el consumo del sistema centralizado un 39,64 %, pero no demuestra mantener la profundidad de lectura en Arquitectura y Devops. No se altera ninguna respuesta para mejorar los contadores.

## Alcance y presupuesto

- Una única ejecución nueva: `813716cc-477b-4a4b-9795-a231973a4b9f`.
- Misma captura local, rama `develop`, commit `4ae82b4097b3b01360bd8c6fb6d779b210f50564`, inventario y textos Q01–Q40.
- Mismo proveedor `openai-codex`, modelo `gpt-6.1-sol`, esfuerzo `medium` y salida máxima de 8.000 tokens por especialista; Akira conserva su límite de 6.000.
- Mismos límites globales que el centralizado anterior: 31 llamadas, 244.000 tokens de salida reservados, 8 MB de contexto acumulado y 7.440 segundos. No son una cuota monetaria ni un corte remoto exacto de salida.
- Se reutilizaron Graphify y la preparación compatible durante la ejecución. La preparación previa conservó 14 artefactos originales de herramientas; se verificaron identidad e integridad antes de usarlos. No se ejecutó el proyecto objetivo ni se instalaron sus dependencias.

## Resultado comparado

| Métrica | Referencia de tres especialistas | Centralizado anterior | Mapas actuales |
| --- | ---: | ---: | ---: |
| Llamadas | 19 | 31 | 30 |
| Tokens de entrada | 692,377 | 1,165,061 | 693,252 |
| Tokens de salida | 16,707 | 24,259 | 24,597 |
| Tokens totales | 709,084 | 1,189,320 | 717,849 |
| Duración de la revisión | 708.818 s | 1043.915 s | 874.675 s |
| Preguntas publicadas como respondidas | 12 | 4 | 3 |
| Parciales | 23 | 24 | 36 |
| No comprobadas | 5 | 12 | 1 |
| Archivos distintos leídos | 94 | 100 | 84 |

Frente al centralizado anterior: tokens -39,64 %, contexto enviado -40,83 % (4.213.464 → 2.493.232 bytes) y duración -16,21 % (17 min 24 s → 14 min 35 s). Las líneas exactamente repetidas bajan de 1.946.976 a 680.406 bytes; ese contador es un indicador parcial de repetición, no una medición de descuentos del proveedor.

Frente al sistema original de tres especialistas, los tokens quedan un 1,24 % por encima y las llamadas pasan de 19 a 30. Su duración antigua es aproximada, calculada con fechas de archivos; las otras dos usan el registro monotónico. Una prueba por configuración no constituye una comparación estadística.

## Qué ocurrió con las respuestas

Los números publicados anteriores incluyen el efecto del filtro ya retirado. Para comparar las mismas 34 preguntas especializadas sin ese efecto se revisaron las salidas originales guardadas:

| Estados originales de los especialistas | Centralizado anterior | Mapas actuales |
| --- | ---: | ---: |
| Respondida | 8 | 3 |
| Parcial | 25 | 30 |
| No comprobada | 1 | 1 |

Las cinco diferencias son Q07–Q09 (Arquitectura) y Q15–Q16 (Devops). Inventario, Datos y los tres perfiles de Seguridad conservan exactamente los mismos estados por pregunta. Las seis respuestas de Akira quedan parciales en ambas ejecuciones. Se ha comprobado que los 34 textos y estados nuevos coinciden exactamente con lo recibido del modelo: no hay una rebaja posterior por Core.

- Q07 reconoce que no se leyó la implementación de la web pública.
- Q08–Q09 dejan pendientes cliente/contexto tRPC, enrutador y módulos administrativos.
- Q15 deja sin leer tareas de Turborepo, el paquete de la web y el Dockerfile de migraciones.
- Q16 deja pendiente completar la lectura de inyección de variables y validaciones de inicio.

Arquitectura cerró en tres llamadas, teniendo permitido un máximo de cuatro. En conjunto se realizaron 64 consultas de código frente a 79, y se leyeron 84 archivos distintos frente a 100. Hubo 11 consultas de herramientas y cinco consultas agrupadas de preguntas, frente a una consulta explícita de herramienta y respuestas antes precargadas. Esto es consistente con destinar parte de las consultas locales a recuperar contexto antes disponible automáticamente; no prueba por sí solo la causa de cada respuesta parcial. No debe inferirse mejora o empeoramiento global únicamente de la etiqueta, pero hay límites de lectura concretos reconocidos por los autores.

Q31 sigue no comprobada: falta completar el inventario de cookies, almacenamiento e integraciones del navegador y la gestión de consentimiento. No se ejecutó el objetivo ni se hicieron comprobaciones activas del sitio.

## Seguridad y Arun

Los tres perfiles de seguridad consumieron 599,400 → 327,860 tokens (-45.30 %), manteniendo las mismas 13 llamadas y los mismos estados originales de sus 15 preguntas.

Arun: 274.622 → 155.990 tokens (-43,20 %), con cinco llamadas en ambos casos. Su primera petición pasó de 114.381 a 30.361 bytes. Su duración individual fue 173,516 → 176,868 segundos: menor consumo no implicó menor tiempo en ese perfil.

Los agentes comunicaron dos riesgos como confirmados y dos como indicios, frente a uno confirmado antes. Son conclusiones de los especialistas, no una validación independiente. Tampoco se atribuye el cambio exclusivamente al mapa: se retiraron la ocultación y el filtro, y OSV actualizó sus datos (89 alertas normalizadas frente a 87; mismas versiones de herramientas, Gitleaks con dos alertas y Semgrep con una).

## Uso real de las herramientas

- Arquitectura pidió Q05 y Q06; Seguridad de identidad, Q08/Q10/Q11; Mei, Q11/Q25; Arun, Q06/Q11/Q29/Q30.
- Se registraron 50 consultas con símbolos o relaciones del grafo, además de búsquedas y lecturas directas. Graphify sigue utilizándose para localizar código.
- SQLite y escáneres se consultan localmente dentro de las rondas existentes. No se despertó al modelo de otro especialista para recuperar una respuesta.

## Comprobaciones y pendientes reales

- Las 40 preguntas conservan IDs y textos; 40 anclas únicas en HTML.
- Las 34 respuestas especializadas conservan exactamente el texto y estado originales. Siete especialistas y ambas etapas de Akira terminaron sin errores; no hubo parada global ni se superó el presupuesto.
- SQLite íntegro, con ocho tareas y 105 hechos de esta revisión.
- Las seis descargas HTML/Markdown de las tres revisiones coinciden byte a byte con sus archivos. Los 103 archivos históricos comprobados no cambiaron.
- El informe está guardado y la reunión aparece cerrada. Chromium continúa aplazado; no se afirma una comprobación visual de esta ejecución.
- No se relanzó el análisis, no se modificaron respuestas, modelos ni límites para obtener un resultado favorable, y no se hicieron commits ni publicaciones.

El mapa resuelve una parte importante del sobrecoste de contexto. Queda pendiente recuperar la profundidad reconocida como incompleta en Arquitectura y Devops antes de dar por cumplida la mejora de cobertura. Esta prueba no autoriza ni inicia otra ejecución.

## Archivos

- [Informe HTML](evidence/agent-comparison-2026-10-31/seven-lookup-maps/informe.html).
- [Informe Markdown](evidence/agent-comparison-2026-10-31/seven-lookup-maps/informe.md).
- [Métricas y comparación](evidence/agent-comparison-2026-10-31/comparison.json).
- [Matriz Q01–Q40](evidence/agent-comparison-2026-10-31/question-matrix.md).
- [Verificación de almacenamiento, originales y descargas](evidence/agent-comparison-2026-10-31/verification.json).

Archivado posteriormente por autorización del usuario en el [cierre estable](CIERRE_COORDINACION_2026-10-31.md). Las frases sobre ausencia de commits/publicaciones describen el momento de la prueba; este cierre posterior autoriza commit y push.
