# Diagnóstico de la regresión · 31/10/2026

Análisis de las trazas guardadas, sin nuevas llamadas a modelos ni cambios de implementación. Este documento no sustituye ni amplía el plan vigente.

## Causa comprobada: rangos que incluyen líneas ocultadas

Las once respuestas rechazadas contienen veinte referencias a líneas marcadas como ocultas dentro de sus rangos. La reconstrucción de la correspondencia de archivos del especialista no encuentra referencias con formato desconocido ni fuera del texto retenido en esas respuestas. Esto no acredita la interpretación del modelo; identifica por qué se rechazaron sus citas.

Ejemplo: Q17 fue entregada por Devops con estado `respondida` y la cita `F8:L1-L42`, correspondiente a `docker-compose.yml`. El rango contiene la línea 8, marcada como oculta. La validación rechaza el conjunto de referencias y la respuesta pasa a `no_comprobado`, aunque existan otras líneas citadas válidas. No se reproducen los valores ocultos.

Las once preguntas afectadas son Q04, Q05, Q06, Q07, Q16, Q17, Q19, Q20, Q21, Q28 y Q33. Q31 también figura como no comprobada en el informe, pero ya fue entregada con ese estado y no pertenece al grupo de rechazos por cita.

El contrato permite rangos amplios y exige que el modelo evite cualquier línea oculta. El validador rechaza toda respuesta si una de sus referencias incluye `OCULT`. La comprobación es anterior a evaluar la suficiencia del resto de las fuentes. El mensaje genérico «Una cita no coincide con un archivo y línea revisados» también se utiliza para esa situación y no permite distinguirla de una referencia inventada.

La regla de rechazo ya existía. El nuevo reparto y sus nuevas respuestas han tropezado más con ella; no se ha demostrado que el modelo inventara estas once fuentes. El fallo de integración consiste en ofrecer bloques con líneas no citables y depender de que el modelo construya correctamente sus rangos. Debe facilitarse evidencia citable desde la entrada, manteniendo la ocultación y la validación estricta, sin reparar automáticamente respuestas rechazadas.

## El indicador 12 → 4 mezcla efectos distintos

| Cambio respecto a la referencia | Preguntas | Efecto |
| --- | --- | ---: |
| Antes respondidas; ahora no comprobadas y con rangos ocultos | Q04, Q05, Q07, Q16, Q17, Q19 | −6 |
| Antes respondidas por Seguridad; ahora síntesis parcial de Akira | Q38, Q39, Q40 | −3 |
| Antes parcial; ahora respondida | Q15 | +1 |

Resultado: `12 − 6 − 3 + 1 = 4`.

Q04 y Q05 ya fueron entregadas como parciales antes de ser rechazadas. Por tanto, no toda la pérdida se explica por la validación. En la respuesta original de los especialistas nuevos había ocho preguntas marcadas como respondidas, veinticinco parciales y una no comprobada. Cuatro de las ocho respondidas y siete parciales se rechazaron por rangos con líneas ocultas. Las seis respuestas de Akira se publicaron como parciales.

Q38–Q40 cambiaron de autor y de cálculo de certeza: el coordinador aplica `parcial` si cualquiera de las respuestas de origen seleccionadas es parcial o no comprobada. La comparación conserva los textos, pero el significado operativo de «respondida» para esas tres preguntas no es idéntico. Esto impide interpretar la caída completa como ocho preguntas que dejaron de investigarse.

## Por qué aumentaron los tokens

| Grupo | Llamadas anteriores | Llamadas nuevas |
| --- | ---: | ---: |
| Inventario | 6 | 4 |
| Arquitectura, Datos y Devops | 5 | 12 |
| Seguridad, identidad, frontend y backend | 6 | 13 |
| Akira | 2 | 2 |
| Total | 19 | 31 |

Las mismas cuarenta preguntas se repartieron entre más investigadores que iniciaron sus propias búsquedas. Todos los especialistas nuevos alcanzaron sus rondas máximas. El coste medio sigue cerca de 37.000–38.000 tokens por llamada: la especialización no redujo suficientemente el contexto por petición.

Se reenviaron 4.213.464 bytes, con 1.946.976 bytes repetidos por líneas idénticas, aproximadamente un 46 %. Las instrucciones, contexto común y evidencia acumulada vuelven a enviarse en las rondas. SQLite conserva aportaciones, pero esa persistencia no proporciona ahorro por sí sola. Las respuestas iniciales de Inventario que quedaron no comprobadas tampoco sirven como una base factual suficiente para evitar investigar otra vez.

## Interpretación y prioridad técnica

La evidencia apunta a una combinación de fragilidad de citas, reutilización insuficiente del contexto y una métrica de cobertura parcialmente distinta. No hubo cambio de modelo ni fallo global del proveedor que explique la regresión. Una única comparación histórica no determina que siete especialistas o la coordinación centralizada sean intrínsecamente peores.

La primera corrección debería dirigirse a cómo Core presenta las referencias citables. Después debe verificarse que las aportaciones anteriores realmente evitan investigación repetida y reducen contexto sin perder preguntas. La comparación debe separar respuestas generadas, respuestas que superan la validación de citas, alcance de investigación y certeza de la síntesis. La suite actual verifica contratos y mecánica; no demuestra calidad semántica ni eficiencia del análisis.

Evidencia reproducible: `artifacts/central-coordination/regression-diagnosis.json`, `question-matrix.md`, las respuestas originales parciales de cada especialista y el código de validación. El diagnóstico no modifica los informes publicados ni convierte respuestas rechazadas en hechos.


## Decisión aplicada: originales sin ocultación ni validador

El usuario decidió retirar ambas capas. Se ha eliminado la transformación del contenido de fuentes y resultados, incluido `--redact` de Gitleaks. La recepción de los especialistas conserva sus textos, estados y referencias originales, sin descartar una respuesta por una cita, longitud, justificación o clasificación editorial. Los controles de JSON, tipos necesarios para representar el informe, rutas, integridad, presupuestos y HTML inerte siguen siendo técnicos. Akira conserva su papel de encargo y síntesis; no hay un perfil validador ni otra llamada de revisión.

Cada respuesta completa se guarda antes de procesarse, también ante JSON incorrecto. HTML/Markdown añaden las aportaciones originales de cada autor; una referencia no localizable permanece visible y no rebaja el estado declarado. Las consultas posteriores siguen la misma política y no reenvían una segunda copia del original completo. Las funciones antiguas de comprobación se conservan como compatibilidad con formatos y pruebas históricas; la ejecución actual de especialistas y síntesis no las utiliza para revisar contenido.

La reproducción offline de las siete respuestas archivadas conserva exactamente las 34 respuestas especializadas: 8 respondidas, 25 parciales y 1 no comprobada. Genera dos artefactos separados con las aportaciones originales y 40 anclas de pregunta, sin llamadas a modelos. No se ha repetido la investigación ni se han reescrito informes o capturas históricos; tampoco se puede recuperar a partir de esos archivos el código que ya quedó ocultado en la captura anterior.

## Arun frente al antiguo Seguridad: qué cambió realmente

| Métrica | Seguridad anterior | Arun actual |
| --- | ---: | ---: |
| Preguntas asignadas | 19 | 6 |
| Llamadas | 6 | 5 |
| Tokens de entrada | 267.451 | 270.832 |
| Tokens de salida | 6.328 | 3.790 |
| Tokens totales | 273.779 | 274.622 |
| Archivos leídos | 44 | 27 |
| Contexto de la primera petición | 52.376 bytes | 114.381 bytes |

Arun no hizo más llamadas: hizo una menos. Su total solo subió 843 tokens (0,31 %). La entrada por llamada pasó de una media de 44.575 a 54.166 tokens (+21,5 %); eso compensó la reducción de llamadas. En Arun, la entrada constituye el 98,6 % del total. La salida sí bajó un 40,1 %, coherente con menos preguntas; el coste dominante estuvo en lo recibido.

La implementación reenvía contexto común, instrucciones, herramientas, aportaciones previas seleccionadas, fuentes acumuladas e historial de consultas. Menos preguntas no eliminan esas partes del prompt. Los bytes de la primera petición y los contadores de uso prueban que hubo más contexto por llamada; no permiten atribuir con exactitud cada token a una de esas secciones porque no se archivó cada prompt completo. Las métricas por llamada constan en `artifacts/central-coordination/arun-comparison.json`.

El aumento grande del área de seguridad es el conjunto: Noor + Mei + Arun sumaron 13 llamadas y 599.400 tokens, frente a las 6 llamadas y 273.779 tokens del especialista anterior. Esto mide coste adicional; por sí solo no demuestra ni descarta una mejora de calidad.

Verificación final de esta decisión: 196 pruebas de backend, 195 correctas y una omisión preexistente. Se conservaron los logs de los intentos previos. Las expectativas antiguas de ocultar o rechazar contenido se sustituyeron explícitamente por pruebas de conservación; no se regeneraron referencias doradas. Chromium sigue aplazado y no se ejecutaron modelos. Los modelos y presupuestos configurados no se cambiaron.

Servicio actualizado y saludable. Comprobación posterior: ocho perfiles disponibles, sin revisiones activas ni reunión abierta y sin incremento de las 31 llamadas históricas. Las cuatro descargas HTML/Markdown de las dos revisiones coinciden con los archivos guardados. Los 103 archivos históricos comprobados permanecen idénticos y SQLite devuelve `integrity_check=ok`. Evidencias: `api-original-policy.json`, `download-original-policy.json`, `original-policy-persistence.json` y `backend-original-policy-release.log`, en `artifacts/central-coordination`. No se hicieron commits ni publicaciones.


## Cambio aplicado: mapas consultables de preguntas y herramientas

Por indicación del usuario se elimina la precarga de respuestas compartidas y detecciones de escáneres en las peticiones de investigación. Core genera mapas locales sin modelos: preguntas ya publicadas con ID, texto, autor y estado; herramientas con identidad, finalidad, estado y cantidades. El especialista solicita preguntas concretas o páginas de escáneres mediante la misma lista `queries` que usa para Graphify y código. No recibe SQL libre ni puede elegir otra revisión.

SQLite devuelve respuestas originales y sus estados, con ubicaciones de fuente agrupadas; no resume ni juzga el contenido. La autoría procede del registro de Core. Si una pregunta no está disponible, se indica sin despertar a otro agente; las demás respuestas disponibles de la misma petición se conservan. Los resultados de Gitleaks/OSV/Semgrep admiten índice, filtros por texto/ruta y paginación con límites. Un elemento excesivo devuelve un error explícito, sin páginas que repitan indefinidamente el mismo desplazamiento. El acceso mediante Graphify y la lectura/búsqueda directa siguen operativos, también para lenguajes sin parser.

Medición reconstruida con los datos archivados de Arun: bloque compartido 67.153 → mapa 3.850 bytes (-94,27 %), con 20 preguntas descubribles frente a siete respuestas antes precargadas; primera petición 114.381 → 30.449 bytes (-73,38 %). Los datos corresponden a bytes de contexto, no a tokens nuevos ni a una comparación nueva de calidad. Se han realizado cero llamadas reales a modelos.

Suite: 202 pruebas de backend, 201 correctas y una omisión previa. Incluye una integración de siete especialistas que recuperan Q04 desde SQLite únicamente tras solicitarla, sin recibir su respuesta en la primera petición, y una ronda que agrupa consulta SQL, escáner y símbolo/código. Modelos, límites de llamadas/rondas, ejecución secuencial y presupuestos se conservan. No se requiere un cambio de interfaz ni se reanuda Chromium.

Evidencias en `artifacts/central-coordination`: `lookup-maps-measurement.json`, `measure-lookup-maps.py`, `backend-lookup-maps-verified.log` y `build-lookup-maps.log`.

Cierre de mapas comprobado: backend actualizado y saludable; 202 pruebas (201 correctas y una omisión previa), API con ocho perfiles y sin tareas activas, cuatro descargas HTML/Markdown idénticas a las guardadas, 103 archivos históricos intactos e integridad SQLite correcta. Sin llamadas reales a modelos, cambios de modelos/presupuestos, commits ni publicaciones. Chromium continúa aplazado. Evidencias finales: `backend-lookup-maps-verified.log`, `recreate-lookup-maps.log`, `lookup-maps-verification.json` y `download-lookup-maps.json`, en `artifacts/central-coordination`.
