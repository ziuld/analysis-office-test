# Extensión de fase 2: revisión por preguntas

Encargo aprobado el 28/10/2026, posterior al cierre histórico de fase 2 y anterior a implementar fase 3. No implementa el diseño completo de fase 3 ni crea servicios o agentes adicionales.

## Reparto obligatorio

El catálogo canónico, incluido en el wheel y su manifiesto de hashes, es `backend/src/arktic_office/resources/profiles/questions.json`.

| Responsable | Preguntas |
|---|---|
| Coordinador | Q01–Q03: conclusiones, antes/después del despliegue, carencias y discrepancias |
| Inventario | Q04–Q07: lenguajes, tecnología/versiones, servicios externos/IA, tipo y partes de aplicación |
| Arquitectura | Q08–Q13 y Q15–Q22: estructura, datos/caché, persistencia, copias, construcción, operación, contenedores, CI/CD, entorno y recursos |
| Seguridad | Q14 y Q23–Q40: privacidad, acceso, sesiones, cookies, XSS, secretos, SQL, recursos y transferencias; respaldo, condiciones e impacto de cada problema |

Arquitectura describe la caché; Seguridad contrasta la protección de sus datos. Inventario cataloga almacenes e integraciones; Arquitectura explica su uso y migración. Todos deben contrastar protecciones, condiciones, impacto y verificación pendiente para cada problema que señalen.

## Flujo y límites

Las nuevas revisiones activan `phase2-extension-v1`. Primero se prepara el snapshot y se ejecutan las herramientas. Cada especialista recibe estados, alcance y primera página de hallazgos deterministas. Puede pedir páginas adicionales con `{"tool":"D02","offset":0}`, dentro de sus rondas existentes, y consultar símbolos/mapa o texto/rutas del snapshot completo. No hay shell, ejecución del objetivo, navegación libre ni nuevas credenciales. Se conservan los presupuestos de archivos, bytes, llamadas y modelos. El coordinador dispone de hasta 64000 bytes de prompt para recibir las 37 respuestas de los especialistas; no se aumenta su número de llamadas.

Cada respuesta contiene ID, estado, explicación, citas F#:L#, herramientas y pendiente. Estados: `respondida`, `parcial`, `no_aplica`, `no_comprobado`. No aplicable requiere justificación respaldada. No encontrar un control no acredita ausencia. Las preguntas omitidas/rechazadas o de una célula fallida quedan explícitas como no comprobadas; nunca se eliminan. Las respuestas parciales/no comprobadas mantienen parcial el resultado global. Validar citas no demuestra que la interpretación del modelo sea correcta.

El coordinador recibe todas las respuestas validadas, incluidos los límites y no aplicables, junto con los problemas respaldados. Responde Q01–Q03 enlazando IDs de respuestas de origen. No añade hechos ni resuelve discrepancias como certezas. La decisión de despliegue sigue siendo humana. Sin coordinación IA, Q01–Q03 quedan pendientes explícitas.

## Informe y resultados deterministas

Actualización visual posterior del 28/10/2026: el HTML de revisiones por preguntas se organiza en tres secciones: **Resumen ejecutivo**, **Análisis por preguntas** y **Anexos deterministas**. El resumen reutiliza las respuestas guardadas sobre aplicación/tecnologías y las conclusiones del coordinador; muestra hasta cinco riesgos respaldados, sin completar un cupo. Todas las preguntas se agrupan por tema, con respuesta natural primero, alcance y comprobaciones pendientes debajo y fuentes plegadas. No se representa la antigua sección de recomendaciones, planes de mejora ni propuestas de arquitectura alternativa. Q02 conserva la valoración de prioridades como parte del cuestionario. El visor solo muestra el documento y el botón de cierre: se retiran filtro, impresión y el título para el arquitecto; la descarga permanece fuera del visor. No se repiten agentes ni herramientas para actualizar la presentación de la prueba guardada.

El resumen Q01–Q03 aparece al inicio del HTML. Los anexos y Markdown conservan las 40 respuestas con fuentes y estados. Al final se incluye un anexo por herramienta:

- D01: adquisición, inventario y cobertura del snapshot.
- D02: Gitleaks; posibles secretos con valores ocultos.
- D03: OSV-Scanner; paquetes, detecciones, entradas y motivos de no evaluación.
- D04: Semgrep; reglas locales, detecciones y cobertura disponible.
- D05: Graphify; cobertura por archivo, diagnósticos, nodos y relaciones completos.

El HTML incluye la salida estructurada completa normalizada y, cuando existe, el JSON original de los scanners con campos sensibles ocultos y metadatos de ejecución. No incluye stdout/stderr sin filtrar. Los artefactos locales se guardan en `herramientas/`, también para repositorios GitHub; los originales pueden contener código y deben conservarse localmente. El informe nunca ejecuta contenido del repositorio. Cero detecciones y no evaluado siguen siendo estados distintos.

Los informes anteriores conservan sus datos y formato; no se inventan respuestas retrospectivas. Los fallos que detienen la preparación antes de los modelos conservan sus artefactos y error; no generan una evaluación IA válida.

## Validación

Pruebas dirigidas de cuestionario, especialistas, coordinación, suficiencia y recuperación. Incluyen 40 preguntas conservadas ante errores, citas inválidas, no aplicables sin fuentes, paginación de herramientas y HTML con contenido malicioso escapado. La prueba real se documenta en `artifacts/` y la ejecución correspondiente de `reports/`; sus resultados no garantizan exhaustividad ni calidad general para otros repositorios.

### Resultado de la primera prueba real — 28/10/2026

Revisión iniciada desde el formulario del frontend: `a66b57a9-a012-46f0-b850-3d071ca69821`, `ziuld/bookingApi`, rama `master`, commit `c0d247e3226d77a83471c7a1b32afdb0981eb7f1`. Los tres especialistas y la síntesis finalizaron con 9 llamadas y 112987 tokens comunicados por Hermes, con el perfil existente `gpt-6-luna/medium`. El HTML contiene las 40 preguntas: 5 respondidas, 13 parciales y 22 no comprobadas; ninguna se clasificó como no aplicable en esta ejecución. Entre los límites observados hay preguntas que el agente no pudo cerrar con las fuentes leídas y respuestas rechazadas por citar regiones con valores ocultos. Este resultado demuestra integración, no una mejora de calidad ya aceptada ni cobertura completa.

La adquisición conserva 44 archivos. Graphify registra 38 textos procesados y 5 sin parser compatible; el binario permanece en el inventario. Gitleaks y Semgrep no detectaron coincidencias; OSV no evaluó dependencias por falta de versiones resueltas compatibles. Se comprobó que los cinco bloques JSON de herramientas incluidos en el HTML son iguales a sus resultados guardados, sin perder nodos, relaciones ni diagnósticos. La descarga desde el frontend coincide por hash con el Markdown completo.

Pruebas finales en Docker sin red y con bloqueo de procesos externos: 69 ejecutadas, 68 correctas y una referencia visual opcional omitida. Las citas del resumen se agruparon por rangos y su respaldo se plegó después de la prueba, regenerando solo HTML/Markdown desde resultados guardados, sin llamadas adicionales; los originales y la procedencia del render se conservaron. Evidencia local: `artifacts/phase2-extension-2026-10-28/validacion.json`, capturas y scripts de comprobación. En la oficina: seleccionar la revisión, **Leer informe → Anexos completos → Cuestionario de revisión / Resultados de todos los análisis deterministas**.

### Ajuste de presentación — 29/10/2026

El resumen pasa a un máximo de diez riesgos respaldados, sin completar un cupo. La gravedad se representa con círculos de color y una leyenda común. Resumen y detalle muestran código y nombre del riesgo. Se elimina el bloque de impacto y deuda técnica. Pendientes de validar enumera únicamente omisiones de revisión observables y se omite cuando no existen; una respuesta desconocida no demuestra por sí sola falta de revisión. Las reglas de redacción ejecutiva y comprensible se incorporan a las instrucciones comunes de los agentes. La plantilla Markdown recoge estas decisiones. Validación dirigida: 45 pruebas correctas y una referencia visual opcional omitida; HTML guardado con las 40 preguntas y los cinco resultados deterministas completos, sin nuevas llamadas a modelos.


### Investigación ampliada — 29/10/2026

Se configura gpt-6.1-sol/medium para Seguridad, Arquitectura, Inventario y Coordinador. Cada especialista dispone de hasta 200 archivos y 600000 bytes acumulados; Seguridad tiene 12 rondas, Arquitectura 8 e Inventario 6. Cada ronda mantiene cuatro consultas y fragmentos de hasta 200 líneas/6000 bytes. El inventario completo de textos puede recorrerse por páginas mediante list_paths/offset, independientemente de la compatibilidad de Graphify. La selección de fuentes sigue siendo autónoma sobre la captura de solo lectura, sin shell, ejecución del objetivo ni lectura fuera del repositorio.

En cuestionarios con investigación habilitada y textos disponibles, Core rechaza el cierre sin haber leído fuentes; si queda presupuesto devuelve al especialista una indicación para investigar. Esto garantiza lectura, no exhaustividad ni contraste correcto de cada respuesta. Se distingue código no leído, backend externo, presupuesto y citas rechazadas. Salidas: hasta 8000 tokens por especialista y 6000 en coordinación; se amplía el contexto del coordinador.

Validación: 57 pruebas dirigidas correctas y una llamada real mínima a Sol (615 tokens comunicados). La suite general inicial ejecutó 168 pruebas y detectó tres fallos: uno era un límite antiguo fijado en el test de reparto (actualizado para validar el perfil vigente); los otros dos corresponden a compatibilidad del prompt editorial y un texto esperado del HTML antiguo, fuera de este ajuste. No se ha repetido el análisis completo del repositorio ni demostrado todavía una mejora de calidad. Artefactos: artifacts/research-freedom-2026-10-29/.


### Protecciones y buenas prácticas comprobadas — 29/10/2026

Las respuestas admiten aspecto_favorable opcional (titulo y detalle), únicamente con estado respondida/parcial y citas válidas de código/configuración. Una valoración favorable inválida se omite sin descartar la respuesta. Los escáneres limpios, no_aplica y la ausencia de hallazgos no generan fortalezas. HTML y Markdown muestran hasta cinco en el resumen, priorizando Seguridad y después Arquitectura e Inventario, y conservan todas en sus preguntas con fuentes y límites. El coordinador recibe estas aportaciones para equilibrar Q01 sin compensar riesgos ni garantizar seguridad global. Si no hay ninguna se explica que no se documentaron protecciones con respaldo suficiente. La plantilla editable refleja el apartado.

La prueba de Web Corporativa 2.0 - IA utiliza develop@4ae82b4097b3b01360bd8c6fb6d779b210f50564: 682 archivos, 58969662 bytes. Se añade MaxSnapshotBytes/--max-bytes configurable (1–256 MB, predeterminado 32 MB) al exportador local. Para esta ejecución el exportador y el core usan 64 MB sin excluir archivos.


### Preparación persistente e instalación oficial de Graphify — 29/10/2026

Graphify 0.9.97 se instala desde PyPI con uv tool install graphifyy[sql]==0.9.97 y registra la skill de Hermes dentro de la imagen mediante graphify install --platform hermes --project. No se instala en Windows. Registrar la skill no inicia un análisis semántico por IA; el adaptador actual sigue usando extracción estática. Los modelos consultan el grafo y los textos del snapshot. SQL incorpora el extra oficial; los YAML cuya estructura deja de ser interpretable al ocultar posibles secretos quedan unsupported con motivo específico, nunca processed. Errores reales de extracción/capacidad siguen bloqueando.

La preparación verificada se guarda en reports/.preparation-cache/ y persiste al recrear contenedores. Su identidad incluye repositorio, commit, ruta local, inventario verificado, ejecutables de scanners, reglas, implementación y huella de la instalación de Graphify. Excluye modelos, razonamiento, instrucciones y respuestas. Se conserva el texto ocultado disponible para consultas, los resultados de scanners, el grafo y los artefactos originales; cada nueva ejecución mantiene sus anexos y procedencia. Antes de reutilizar se verifican hashes; errores o cachés alteradas se regeneran. La copia del snapshot sigue verificándose. Solo se guardan preparaciones que finalizaron correctamente.

AUDIT_PREPARATION_REFRESH=1 fuerza regenerar, útil para renovar los avisos OSV aun sin cambiar el código. El informe indica la fecha original cuando reutiliza resultados. Las valoraciones de agentes y sus respuestas nunca se reutilizan automáticamente. No es una aprobación de seguridad ni una actualización continua de vulnerabilidades.


### Anexos en lenguaje natural — 29/10/2026

HTML y descarga Markdown presentan únicamente explicaciones de resultados, alertas y cobertura, sin bloques de código ni volcados JSON. Se mantienen los cinco análisis y todas las alertas normalizadas, con paquete/versión/aviso cuando consta y localización sin reproducir código. Los nodos y relaciones se resumen por su alcance; los archivos no indexados conservan su explicación. La descarga por cuestionario utiliza la estructura de lectura y no añade las citas literales de código del formato anterior. Los originales permanecen en los artefactos internos, disponibles para Core y agentes. Las instrucciones comunes piden describir el comportamiento en lugar de copiar expresiones de implementación. Estos cambios de presentación no invalidan la preparación persistente.


### Descarga HTML y Markdown — 30/10/2026

La oficina ofrece Leer informe, Descargar Markdown y Descargar HTML. La descarga HTML utiliza el archivo guardado de la revisión seleccionada, con tipo text/html y cabecera de archivo adjunto; no vuelve a generar el informe ni ejecuta agentes. La API conserva la ruta histórica /download para Markdown y añade /download-html. La opción HTML solo aparece cuando existe informe.html, mediante has_html_report. El proxy del frontend admite explícitamente la nueva ruta. Validación dirigida: 18 pruebas correctas de API y almacenamiento.

