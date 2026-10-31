# Fase 2 — Mejora de agentes, recuperación y calidad

**Extensión posterior autorizada el 28/10/2026:** [revisión por 40 preguntas y anexos deterministas](EXTENSION_FASE_2.md). Se aplica al flujo actual antes de implementar fase 3; el cierre y las evidencias históricas siguientes se conservan.

Estado: **cerrada el 28/10/2026 por decisión del usuario, sin alcanzar la calidad de análisis esperada**. Se conservan los avances funcionales F2-01 a F2-06 y su integración comprobada el 25/10/2026. El cierre no constituye aceptación de la calidad del informe. Versión 0.3.0; no implica merge, publicación ni cambios de runtime.

**Plan vigente:** [Mejoras acordadas — Coordinación centralizada](PLAN_COORDINACION_CENTRALIZADA.md). No retomar automáticamente los experimentos ni tareas de esta fase.

## Cierre y traspaso — 28/10/2026

El flujo llegó a funcionar, pero entregaba información demasiado general y poco útil para las preguntas concretas del usuario. Se sustituye su afinado incremental por un rediseño basado en preguntas seleccionadas, especialistas independientes y un informe descriptivo sin recomendaciones generadas por modelos.

- F2-01 a F2-06: se conservan sus cierres funcionales y evidencias, sin atribuirles aceptación de calidad.
- F2-07: tuvo preparación de resultados, pero no se cerró su revisión conjunta. Su revisión se replantea en F3-01.
- F2-08 a F2-12: quedan sin completar y sustituidas por el alcance de Fase 3; no se marcan realizadas.
- Se preservan los informes, intentos fallidos y cambios técnicos existentes. No se ejecutan más análisis ni se altera código por este cierre documental.
- El usuario desarrollará los agentes y sus skills en un repositorio externo reutilizable. Arktic recibirá esos mismos agentes y adaptará las herramientas y contratos necesarios para integrarlos.

**Todo lo que sigue es histórico.** Las antiguas instrucciones de continuación, propuestas de roles, recomendaciones y estados pendientes describen esta fase; no son el encargo vigente. El único trabajo futuro está en el plan de coordinación centralizada; las referencias a fase 3 que siguen son históricas.

## Objetivo

Conseguir respuestas más útiles, precisas y propias de cada especialidad, localizando suficiente código con un coste controlado. Primero revisar qué instrucciones/configuración se aplican realmente a los agentes Hermes usados por Arktic; después cambiar una causa cada vez. No ampliar CI/CD, añadir servicios ni ejecutar suites completas sin necesidad. Mantener un perfil económico reproducible y pruebas dirigidas mínimas.

## Punto de partida histórico — anterior a F2-01

- El flujo descarga y verifica el snapshot completo antes de mapas/scanners. Los especialistas reciben fragmentos limitados: insuficiencia de contexto no implica que falten archivos descargados.
- [hermes_runtime.py](../backend/src/arktic_office/adapters/hermes_runtime.py) instancia `AIAgent` por llamada con un prompt de sistema efímero, herramientas desactivadas y `max_iterations=1`. Se usan `skip_context_files=True`, `skip_memory=True`, `skip_background_review=True`; no se solicita identidad SOUL. No asumir que una personalidad configurada en otra sesión/UI se aplica a estas llamadas.
- Los focos efectivos salen de [agents.json](../backend/src/arktic_office/resources/profiles/agents.json). Perfiles de modelos/límites: [models.json](../backend/src/arktic_office/resources/profiles/models.json) y [config/models.py](../backend/src/arktic_office/config/models.py). Investigación y coordinación: [research.py](../backend/src/arktic_office/coordination/research.py), [coordinator.py](../backend/src/arktic_office/coordination/coordinator.py). Skill y contrato de salida se añaden explícitamente; la configuración efectiva incluye también variables de entorno, sin exponer secretos.
- Las últimas consultas fueron por rutas exactas, con relaciones del grafo adjuntas. Esto no demuestra navegación eficiente por símbolos/grafo. Las ventanas de 100 líneas pueden omitir rutas/middleware posteriores; Arquitectura agotó su cap de seis archivos. El padding de líneas consume presupuesto. Aumentar archivos o modelo sin localizar el cuello de botella no garantiza mejor resultado.
- Baseline `f7043007-40a9-42a3-8b1e-a1478688c25c`: tres especialistas y síntesis, 8 llamadas gpt-6-luna/low, 52.366 tokens comunicados, 7 observaciones y 22 citas verificadas. Informe parcial: un tema inválido rechazado, cinco controles no evaluados, una formulación sobre recuperación de trabajos demasiado amplia. [Evidencia](evidence/orchestrator-research-2026-10-24.json).

## Orden y entregables históricos

F2-01 a F2-06 conservan su cierre funcional y sus evidencias. El 25/10/2026 el usuario sustituye las antiguas tareas pendientes F2-07 a F2-10 por F2-07 a F2-12, descritas en el punto 3. No se abre otra fase. Primero comprender las herramientas, después acordar la búsqueda de cada agente, integrar y finalmente definir el informe. Los diseños y pruebas anteriores son antecedentes, no aceptación del resultado deseado.

## 1. Revisar configuración efectiva de Hermes y agentes

- [x] F2-01 Trazar cómo el Hermes fijado compone el prompt: sistema base, prompt efímero, perfil, identidad, idioma, archivos de contexto, memoria y herramientas. Contrastar los flags del adaptador con el código de Hermes instalado, sin mostrar credenciales ni conversaciones privadas. Distinguir perfiles visibles en Hermes de los agentes efímeros del análisis, indicando qué configuración sí se carga, cuál se ignora y qué instrucciones heredadas permanecen. No asumir que cambiar la UI o un SOUL cambia el análisis.
- [x] F2-02 Inventariar las instrucciones realmente enviadas por rol y detectar duplicidades, contradicciones o huecos: objetivo, idioma español, qué constituye evidencia suficiente, cuándo buscar, cómo declarar límites, enums y esquema de salida. No modificar todavía varios prompts a la vez.
- [x] F2-03 Proponer focos breves y criterios claros por especialidad, con ejemplos pequeños: Seguridad evalúa controles/riesgos; Arquitectura describe estructura y operación; Inventario identifica tecnología/función. Orquestador distribuye objetivos y sintetiza sin ampliar las conclusiones. Probar el cambio mínimo que corrija el problema identificado.

**Salida de la primera tarea, realizada:** ficha siguiente y [evidencia no secreta del runtime instalado](evidence/phase2-agent-audit-2026-10-24.json). La auditoría precede al cambio de instrucciones registrado al final. Su evidencia se conserva como tal; no se convierte retrospectivamente en una ejecución real de agentes.

## 2. Comprobar cómo encuentran y reciben el código

- [x] F2-04 Seguir las trazas de fuentes necesarias, consultas, ventanas recibidas, omisiones por presupuesto y carencias finales. Clasificar cada carencia: información operativa inexistente, parser incompatible, búsqueda ineficiente, ventana incorrecta, cap agotado o interpretación del modelo.
- [x] F2-05 Verificar lectura por símbolos/relaciones y región concreta en rutas HTTP/autorización y recuperación. Corrección localizada de ubicación de definición, conservando el recuperador y los presupuestos aprobados posteriormente por el usuario. Registrar qué se entregó y sus límites.
- [x] F2-06 Ampliación aprobada: aplicar presupuestos/rondas acordados e integrar OSV multitecnología/SBOM y Semgrep local acotado. Probar casos controlados y recorrido completo, registrando entradas, carencias y límites. No atribuir causalidad o mejora general a una comparación con varios cambios. Resultado y limitaciones registrados al final.

**Salida:** explicación verificable de por qué cada rol obtuvo o no el código necesario y el menor ajuste útil al flujo existente.

## 3. Nuevo trabajo acordado: evidencia, agentes e informe

Estas tareas se realizan secuencialmente **con el usuario**. Codex prepara muestras y preguntas concretas, muestra resultados y espera el acuerdo antes de pasar al siguiente especialista o modificar criterios. No asumir preferencias sobre contenido, prioridades, búsquedas o formato. No ejecutar todo el plan de forma autónoma.

- [ ] **F2-07 · Revisar herramientas deterministas.** Mostrar por separado las salidas reales de Graphify, Gitleaks, OSV y Semgrep, antes de convertirlas en un informe de IA. Para cada una: entrada/commit, cobertura compatible, archivos omitidos y motivo, salida original relevante, interpretación y límites. Distinguir mapa estructural, secretos, dependencias vulnerables y patrones SAST; no equiparar nueve reglas locales con Sonar. Reutilizar primero los artefactos existentes. Si una capacidad no está demostrada, acordar una muestra pequeña con problemas conocidos: cero detecciones no demuestra que una herramienta no sirva. Decidir juntos conservar, ajustar o sustituir; no instalar sustitutos por iniciativa automática. **Cierre:** el usuario entiende qué aporta cada herramienta y acuerda la decisión.
- [ ] **F2-08 · Definir y probar Inventario.** Antes de cambiar instrucciones, acordar un repositorio/commit y una referencia manual pequeña de qué debería encontrar. Construir juntos una ruta por tecnología: ejemplo Java, pom y módulos → dependencias declaradas/usadas → configuración/persistencia → implementaciones/controladores/respuestas → plantillas y estáticos. Es un ejemplo pendiente de precisar con el usuario, no una receta impuesta. Mostrar entrada → consultas → fragmentos recibidos → respuesta; probar evidencia suficiente y escasa con el mínimo de llamadas. Identificar tecnologías, función, persistencia (BD/archivos/servicio, configuración local/Docker cuando exista evidencia) y forma de ejecución sin inventar. **Cierre:** el usuario valida la estrategia y los resultados frente a su referencia.
- [ ] **F2-09 · Definir y probar Seguridad.** Con Inventario validado, acordar objetivos y rutas de investigación usando código y scanners. Seguir pistas de entrada → uso sensible → defensa, distinguir riesgo concreto, indicio y no evaluado, y comprobar citas e impacto. No convertir ausencia de evidencia en vulnerabilidad ni ausencia de hallazgos en certificación. Probar aisladamente y revisar salidas con el usuario. **Cierre:** resultados útiles y estrategia aprobados, con cobertura explícita.
- [ ] **F2-10 · Definir y probar Arquitectura.** Con los dos roles anteriores revisados, acordar cómo identificar componentes, conexiones, persistencia e infraestructura declarada en Docker/Compose, CI/CD, configuración y documentación. Separar arquitectura observada, inferencias y recomendaciones; no inventar servidor/VPN ni preguntar despliegue desconocido durante el análisis automático. Probar aisladamente. **Cierre:** el usuario valida que el mapa y las recomendaciones se apoyan en fuentes.
- [ ] **F2-11 · Verificar integración.** Después de aceptar las estrategias aisladas, ejecutar un recorrido completo acotado. Comprobar encargos del coordinador, uso de evidencia, ausencia de pérdidas/contradicciones y síntesis fiel. Registrar intentos fallidos, llamadas, tiempo, tokens y presupuestos efectivos. No introducir reintentos o evaluaciones automáticas. **Cierre:** integración válida y contenido revisado con el usuario; éxito técnico y calidad se evalúan por separado.
- [ ] **F2-12 · Acordar output e informe.** Con resultados reales ya comprendidos, proponer contenido, unificarlo con la propuesta del usuario y construir juntos un modelo rellenado que él revise/complemente manualmente. Derivar una plantilla vacía coherente para que Core la rellene; adaptar contratos solo a lo acordado. Diseño/presentación al final, sin imponer el v14 actual. Hallazgos útiles al comienzo; límites detallados y próximos pasos abajo/anexos. **Cierre:** aceptación explícita del modelo y de la plantilla vacía, con trazabilidad a las salidas disponibles.

### Avance F2-07 — 25/10/2026, pendiente de revisión conjunta

Se preparó la carpeta local ignorada `reports/f2-07-2026-10-25/`: `index.html` permite ver cada salida nativa, `INFORME.md` separa la valoración de Codex y `cobertura-por-archivo.csv` enumera las 567 rutas con estados y motivos. Primero se conservaron los registros históricos; después se repitieron únicamente Graphify y scanners sobre el mismo commit, verificando los SHA256 del snapshot. No se ejecutó código del repositorio ni modelos del producto. Evidencia resumida: [phase2-tools-review-2026-10-25.json](evidence/phase2-tools-review-2026-10-25.json).

Scanners coinciden con el histórico: Gitleaks sin coincidencias, OSV con 273 registros versionados sin avisos y Semgrep con un patrón deliberado en un worker de prueba. Graphify produjo 3108 nodos/5081 relaciones, 518 no resueltas; difiere en una relación del resumen histórico, cuya causa no se ha determinado. Se conservó un primer intento fallido por caché en ruta de solo lectura y su corrección de directorio de trabajo. Las recomendaciones de conservar/ajustar son propuestas: **F2-07 sigue abierta hasta el acuerdo del usuario**. No se inicia F2-08 ni se cambian herramientas/reglas/agentes.

### Forma de colaboración y límites

- Al empezar cada tarea, hacer preguntas concretas sobre el resultado esperado, la muestra y los criterios pendientes; contrastar supuestos y contradicciones con ejemplos. Preguntar cuando exista una duda material, sin volver a pedir permisos ya dados. Esperar respuestas para las decisiones dependientes; avanzar solo en lecturas/preparación independientes.
- Las pruebas aisladas permiten diálogo y corrección de estrategias; el análisis automático entrega lo encontrado y registra pendientes sin interrogar al usuario ni bloquear por datos externos ausentes.
- Las rutas guían pero permiten seguir pistas justificadas dentro del presupuesto. Separar fallos de búsqueda, cobertura, contrato y razonamiento antes de elevar modelos/archivos.
- Mantener Luna/medium y límites actuales salvo acuerdo. No modificar CI/CD, versiones/pins, instalar skills, añadir agentes ni ejecutar código del repositorio analizado. Pruebas mínimas sobre lo afectado; sin suites completas o tandas de modelos por defecto.
- Separar instrucciones profesionales reutilizables del adaptador Hermes. Portabilidad a Claude Code/OpenCode u otros entornos queda fuera de este tramo; no prometer que el agente funciona sin adaptar sus herramientas.
- Nuevos roles DevOps/Privacidad, alertas históricas de GitHub, actualizaciones de herramientas y cambios de modelos quedan **diferidos sin tarea activa**. Solo reconsiderarlos si las comprobaciones justifican la necesidad y el usuario lo acuerda.

### Retomar en otro chat — instrucciones históricas, sustituidas

**No continuar esta secuencia histórica.** Leer únicamente el [plan vigente](PLAN_COORDINACION_CENTRALIZADA.md). El antiguo encargo externo de agentes ha quedado sustituido.

1. Leer este punto 3 y la evidencia [última validación funcional](evidence/phase2-luna-validation-2026-10-25.json). El commit funcional es `af7a452`, rama de cierre `codex/fase-2-agentes`; comprobar estado de Git/PR antes de tocar nada. El usuario hace el merge.
2. No rehacer F2-01 a F2-06 ni optimizar el informe actual. El usuario no quedó satisfecho con su contenido; el cierre acepta esta base funcional, no su calidad final. La fase 2 continúa abierta.
3. Configuración de cierre: todos los roles heredan `gpt-6-luna`/`medium` en `.env.example`; comprobar overrides locales sin mostrar secretos. Presupuestos acumulados: Seguridad 20 archivos/100000 bytes/2 rondas, Arquitectura 12/60000/2, Inventario 8/32000/1. El historial contiene valores anteriores.
4. Empezar **solo F2-07**: localizar resultados originales de Graphify y scanners de la revisión `d506794d-6b23-4d84-bab8-c9438d678d7b`, repo `ziuld/beneath-the-code-page`, commit `95ede5bccc881a2230f874944299b4a73101337d`. Resumen publicable en la evidencia enlazada; artefactos completos locales bajo `reports/2026-10-25/082854-beneath-the-code-page/` y `artifacts/`. Estos directorios están ignorados: en otro equipo comprobar disponibilidad y acordar cómo regenerar lo necesario, sin fingir disponer de ellos.
5. Primera conversación: mostrar qué salidas hay y preguntar qué espera ver el usuario de una herramienta tipo Sonar y qué ejemplo quiere revisar. Presentar muestras legibles con enlaces a los originales, sin generar otro informe completo ni llamar agentes para explicarlas.
6. Antes de F2-08, pedir al usuario su ruta de lectura y hallazgos esperados de Inventario. Repetir el acuerdo por Seguridad y Arquitectura; no saltar directamente al flujo completo.

### Cierre del tramo funcional y limpieza — 25/10/2026

- [x] Mantener F2-01 a F2-06 y evidencias; sustituir el pendiente anterior por la secuencia acordada F2-07 a F2-12, sin otra fase ni plan paralelo.
- [x] Mantener informe v14 como salida provisional, demo e informes históricos sin reescribir. Conservar pruebas y contratos de compatibilidad mientras no se acuerde reemplazarlos.
- [x] Excluir de Git las tres imágenes locales de referencia de `tmp/pdf-reference/`, sin borrarlas. Mantener `.env`, OAuth, vendor, informes, cachés y artefactos fuera del commit; evidencias saneadas en `docs/evidence/` sí se conservan.
- [x] No cambiar ejecución, modelos, CI/CD ni versión 0.3.0 para este cierre documental. No repetir modelos/scanners ni una suite de código por cambios exclusivamente documentales.
- [x] Comprobación de cierre documental: `git diff --check` correcto, sin archivos locales sensibles versionados ni cambios en `.github` respecto a origin/main; audit-api, office y preparator saludables. No se repite la prueba completa: su evidencia corresponde a `af7a452`.
- Preparar PR hacia main con la base funcional acumulada; no hacer merge, tags ni releases. El PR previo de fase 1 #3 sigue siendo antecedente; comprobar solapamiento antes de fusionar.

## Registro histórico (lectura de referencia)

Lo siguiente conserva decisiones y comprobaciones de su fecha. Los modelos, presupuestos y propuestas antiguas no sustituyen el alcance vigente del punto 3. Las casillas pendientes históricas no son tareas adicionales.

## Checklist del arranque — 24/10/2026

- [x] Revisar adaptador Arktic, constructor de prompts por etapa, perfiles y estándar editorial.
- [x] Contrastar cinco archivos de Hermes instalados con las fuentes fijadas mediante SHA256.
- [x] Leer únicamente configuración no secreta con el lector nativo de Hermes: no hay config.yaml local; SOUL existe, pero el adaptador no solicita cargarlo. No leer credenciales ni conversaciones.
- [x] Identificar cobertura actual de scanners y lagunas de instrucciones/recuperación.
- [x] Incorporar el feedback como hipótesis evaluables y proponer reparto de responsabilidades.
- [x] Aplicar el cambio mínimo de instrucciones a los tres especialistas actuales y coordinador, incluida la separación de responsabilidades sobre persistencia (F2-03).
- [ ] Decidir la incorporación de DevOps y Privacidad/gobernanza IA como roles independientes; continúan como propuesta.
- [x] Comparar el resultado del ajuste sobre el mismo commit remoto y revisar persistencia/recuperación y selección de fuentes; comparación exploratoria registrada, sin atribuir mejora general.
- [ ] Implementar nuevos roles solo si se adopta esa ampliación, incluyendo contratos, informes, consultas y oficina; no basta con añadir nombres a agents.json.
- Propuesta histórica diferida (sin ID activo): valorar después un conector opcional a alertas históricas de GitHub Secret Scanning. Queda diferido; no instalar skills ni ampliar ahora el scanner al historial.

## Auditoría de agentes efectivos: qué se aplica realmente

Fuentes: [adaptador](../backend/src/arktic_office/adapters/hermes_runtime.py), [perfiles](../backend/src/arktic_office/resources/profiles/agents.json), [investigación](../backend/src/arktic_office/coordination/research.py), [constructor de análisis](../backend/src/arktic_office/reporting/reports.py), [coordinador](../backend/src/arktic_office/coordination/coordinator.py), [estándar](../backend/src/arktic_office/resources/editorial/standard.md). Hermes fijado: `agent/agent_init.py`, `agent/system_prompt.py`, `agent/codex_runtime.py`, `agent/chat_completion_helpers.py` y `run_agent.py`; las cinco fuentes instaladas coinciden con las locales verificadas.

| Capa | Efecto observado en el código/configuración |
|---|---|
| Identidad Hermes | Se conserva DEFAULT_AGENT_IDENTITY y bloques base de ayuda/metadatos; el prompt efímero de Arktic se añade, no sustituye todo el sistema |
| Identidad personal/SOUL | SOUL local existe. `skip_context_files=True` y `load_soul_identity=False` por defecto impiden cargarlo; editarlo no cambia este análisis |
| Contexto/memoria/skills automáticas | Sin contexto de proyecto y memoria por los flags actuales; sin toolset de skills. La skill existente de Arktic se incorpora explícitamente por el constructor, no por descubrimiento de Hermes |
| Herramientas | `enabled_toolsets=[]` y comprobación de herramientas vacías. El modelo solicita JSON y Core realiza las consultas locales; no tiene shell/red del repositorio |
| Otros bloques Hermes | Configuración por defaults, posibles hints de entorno/plataforma y hooks de plugins siguen existiendo. No hay directorio local de plugins; la auditoría no presume que los flags borren todos los posibles bloques de Hermes |
| Oficina | Los cuatro personajes se proyectan por IDs y estados del análisis. No equivalen a cuatro perfiles personales persistentes del gateway Hermes |
| Modelos efectivos | Coordinador y tres especialistas `openai-codex`, `gpt-6-luna`, `low`. Una ronda de investigación por especialista; topes actuales preservados |

### Hallazgos de instrucciones

1. **Los focos de agents.json son breves, pero no son todas las instrucciones.** El análisis añade perfil de Seguridad, estándar editorial, skill existente, contratos y fuentes; faltaba distinguir estas capas antes de editar supuestas personalidades.
2. **Investigación y análisis reciben criterios distintos.** La primera llamada usa contexto común, foco corto y contrato de consultas; no incorpora los seis controles detallados de Seguridad ni las reglas editoriales. Es una hipótesis plausible de selección incompleta, no una causa demostrada por una comparación controlada.
3. **El coordinador no usa el mismo estándar editorial del análisis.** Recibe skill y encargo de la etapa; el idioma y límites semánticos deberían estar expresados de forma breve y consistente, también al investigar y sintetizar.
4. **Hay varios contratos/examples en el prompt de análisis.** Los temas/control/estados deben proceder de una referencia coherente; el piloto ya mostró un tema inválido. Revisar duplicidad y ejemplos antes de relajar validadores o añadir reintentos.
5. **XSS, privacidad/consentimiento y gobernanza LLM no tienen un checklist específico actual.** Seguridad contempla entradas, consultas parametrizadas, destinos de red y secretos de forma general; esto no acredita una revisión dedicada de todos esos temas.
6. **El grafo aporta relaciones, pero las consultas del último piloto fueron por rutas.** Ventanas iniciales y caps dejaron fuera código posterior. No atribuir toda insuficiencia al modelo o a la falta de descarga: el snapshot ya está completo.

**Límite de la auditoría:** lectura de código y configuración del runtime, sin inferencia ni captura de una petición real. No se ejecutaron modelos, scanners, el proyecto objetivo ni alertas GitHub. No se cambian perfiles, versiones, CI/CD, pins, autenticación ni skills en este paso.

## Propuesta de F2-03: equipo y responsabilidades

Se propone un equipo objetivo de **cinco especialistas y un coordinador**, ampliando los tres especialistas actuales con DevOps y Privacidad/gobernanza IA. La decisión es propuesta, no una ampliación implementada. Empezar por alinear las instrucciones de investigación/análisis; comparar antes de activar nuevos roles. El frontend se reparte según la responsabilidad; un especialista frontend adicional se valoraría solo si esa división deja lagunas demostradas.

| Rol propuesto | Responsabilidad principal | Fuentes/resultado esperado |
|---|---|---|
| Coordinador | Objetivos, alcance, registro de cobertura y síntesis fiel; no elegir archivos ni hacer de experto de todo | Encargos por rol; conservar desacuerdos, carencias y condiciones; cero hallazgos nuevos en síntesis |
| Seguridad de aplicación | Autenticación/autorización, aislamiento por usuario, XSS, SQL/command injection, SSRF, secretos, dependencias y límites de herramientas LLM | Trazar entrada → uso sensible → defensa. Diferenciar patrón, posible impacto condicionado y explotación demostrada; no inventar CVE ni pruebas |
| Arquitectura e integraciones | Componentes, límites de confianza, flujos de datos, servicios externos y SDK/proveedores LLM | Mapa origen → datos → destino → finalidad → autenticación/transporte → fuentes y tramos desconocidos; descubrir dependencias VPN/red sin asumir despliegue real |
| DevOps y operación (nuevo) | Despliegue, configuración de red/VPN/egress, secretos operativos, permisos, registros, límites, backups/restauración y recuperación | Contrastar configuración declarada y evidencia operativa; volumen no equivale a backup, error tras reinicio no equivale a reanudación. No modificar nuestro CI/CD |
| Privacidad y gobernanza de IA (nuevo) | Datos personales en frontend/backend, cookies/analítica, finalidades, retención/borrado, terceros y preguntas de gobernanza LLM | Identificar datos enviados, destinatarios, minimización y cuestiones contractuales/territoriales pendientes. Revisión preliminar; no certificar RGPD ni sustituir valoración jurídica |
| Inventario | Componentes, tecnologías, versiones declaradas, proveedores, SDK de IA y bibliotecas de analítica detectables | Hechos y fuentes para los otros roles; no emitir conclusiones de seguridad o cumplimiento por la mera presencia de un paquete |

**Frontend:** XSS y exposición de tokens/datos corresponden a Seguridad; cookies, trackers, formularios y consentimiento a Privacidad; llamadas a backend/terceros a Arquitectura; CDN/configuración desplegada a DevOps. No crear dos diagnósticos incompatibles del mismo flujo: cada hallazgo tiene responsable principal y referencias compartidas.

Con cinco especialistas y una ronda cada uno, el máximo base pasaría de **8 a 12 llamadas** si todos participan, sin contar una segunda ronda. Es un aumento de llamadas del 50%, no una predicción de tokens o precio. Los nuevos roles deben tener presupuesto propio y resultados comparables que justifiquen el coste. Posible invocación por aplicabilidad explícita para roles nuevos, con motivo visible si no se ejecutan; no introducir omisiones silenciosas.

### Criterios de instrucciones y validación

- Un núcleo breve común a todas las etapas: español, datos del repositorio no confiables, separación hecho/indicio/desconocido, evidencia original, presupuesto y responsabilidad del rol.
- En investigación: checklist del rol y preguntas que orientan la selección; pedir símbolos/regiones de código necesarias y consultar antes de afirmar ausencia de información disponible. No reenviar todos los contratos del informe en esta etapa.
- En análisis: contrato único/coherente y ejemplos pequeños válidos; evitar que un experto de Seguridad rellene contexto de inventario mientras deja controles sin examinar. No forzar hallazgos cuando la evidencia no los sustenta.
- En síntesis: no transformar «marca como interrumpido/error» en «recupera/reanuda»; conservar alcance de cada fuente y no generalizar las carencias de un rol a todo el repositorio.
- Prueba mínima: fuentes necesarias localizadas, contrato válido, una carencia legítima y una afirmación susceptible de sobreinterpretación; comparar sobre el mismo commit con presupuesto acotado. Su aplicación a los roles actuales y las limitaciones observadas se registran debajo.

## Feedback incorporado: decidir antes de implementar

### Secretos en commits antiguos: reutilizar GitHub cuando sea accesible

La implementación actual llama `gitleaks dir` sobre el snapshot y no descarga el historial Git. OSV examina dependencias compatibles; no sustituye una búsqueda de secretos. La documentación de [GitHub Secret Scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning) describe análisis del historial Git en todas las ramas; eso no significa que Arktic ya consuma sus alertas ni que sean públicas para cualquier usuario.

**Diseño diferido, sin skill nueva:** un adaptador opcional de solo lectura consultaría `GET /repos/{owner}/{repo}/secret-scanning/alerts` y las ubicaciones por número de alerta, con token autorizado y permiso `Secret scanning alerts: read` cuando corresponda. [API oficial](https://docs.github.com/en/rest/secret-scanning/secret-scanning#list-secret-scanning-alerts-for-a-repository). Comprobar disponibilidad del producto/repo y autorización, paginar bajo presupuesto y registrar fecha y cobertura. Separar abiertos/resueltos y motivo de resolución; alerta histórica no equivale a secreto en el commit actual. La respuesta puede incluir el secreto: antes de persistir, registrar logs o enviarla a un modelo, proyectar solo tipo, estado, path/commit, fechas y URL autorizada; nunca el valor. No probar credenciales.

403/404, feature no disponible, error o paginación incompleta → **no evaluado/no accesible**, nunca «sin secretos». Respuesta vacía → «sin alertas devueltas en el alcance consultado», no garantía de historial limpio. No activar protección ni ampliar permisos automáticamente. La API de historial de escaneos es distinta de las alertas y tiene requisitos propios: su posible uso se validará después. Por ahora se conserva la cobertura del snapshot y se difiere todo acceso histórico (F2-11).

### VPN, terceros y posible salida de información

La conexión a una VPN o a un proveedor externo no es por sí sola un fallo. Proponer trazas de configuración/código: quién llama, destino configurable, finalidad, datos enviados, controles observados y qué queda por confirmar. No conectar a la VPN, terceros ni endpoints descubiertos para probarlos en esta fase de revisión estática.

Esto se aplica **al proyecto analizado y a Arktic**. Arktic envía índices, fragmentos ocultados y contexto al proveedor del modelo; la ocultación heurística no garantiza anonimización. Registrar categorías de datos, mínimo necesario, logs/retención y condiciones del proveedor por confirmar. Una URL en código no demuestra tráfico real ni que hubiera fuga; falta de contrato en el repo no demuestra que la empresa no lo tenga. [EDPB: principios de protección de datos](https://www.edpb.europa.eu/sme/learn-the-basics/data-protection-basics_en) y [transferencias internacionales](https://www.edpb.europa.eu/sme/be-compliant/international-data-transfers_en).

### Uso de LLM y gobernanza

Identificar proveedor/modelo declarado y caso de uso, qué entra/sale, datos sensibles, retención/logs, separación entre clientes, revisión humana, presupuesto y qué herramientas puede activar. Seguridad examina prompt injection y acciones indebidas; Arquitectura el flujo; DevOps permisos/operación; Privacidad coordina las preguntas sobre datos, finalidad, contratos y aplicabilidad normativa. No confundir prompt injection con XSS ni asumir que todo LLM pertenece a una categoría jurídica concreta. [EDPB: dictamen sobre datos personales y modelos de IA](https://www.edpb.europa.eu/documents/opinion-of-the-board-art-64/opinion-282024-on-certain-data-protection-aspects-related-to_en).

### Frontend, RGPD y cookies/analítica

La mera presencia de Google Analytics, un banner o una política no prueba ni incumplimiento ni cumplimiento. Seguir inicialización de trackers/SDK, almacenamiento del navegador, datos en URLs/eventos, consentimiento/revocación cuando resulte aplicable y tratamiento en servidor. RGPD abarca el tratamiento, no solo el frontend; cookies requieren considerar además el marco ePrivacy y su aplicación nacional. Señalar qué falta verificar en ejecución y con responsables de privacidad, sin emitir un certificado. [EDPB: Cookie Banner Taskforce](https://www.edpb.europa.eu/documents/task-force-report/report-of-the-work-undertaken-by-the-cookie-banner-taskforce_en).

### XSS e inyección: prioridad explícita de Seguridad

Buscar origen de datos no confiables, propagación y destino HTML/atributo/URL/JavaScript/DOM; revisar escape por contexto, sanitización cuando se permite HTML, usos de innerHTML/dangerouslySetInnerHTML y defensas existentes. CSP es defensa adicional, no prueba suficiente por sí sola. Cubrir XSS reflejado, almacenado y DOM según evidencia. SQL y comandos son mecanismos distintos y se revisan en sus destinos. Gitleaks/OSV no aportan esa comprobación; actualmente hay revisión LLM genérica de entradas, no validación dedicada exhaustiva ni explotación probada. [OWASP: prevención XSS](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) y [DOM XSS](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html).

## Aplicación inicial de F2-03 — 24/10/2026

Alcance acordado: mejorar los **tres especialistas actuales y el coordinador**, antes de decidir nuevas incorporaciones. No se añaden agentes DevOps/Privacidad, skills, herramientas, servicios, dependencias ni pipelines. Versiones y pins conservados durante el desarrollo de Fase 2. No se cambian modelos, razonamiento, caps ni rondas.

- Un núcleo común de instrucciones confiables define español, contrato de etapa, separación hecho/indicio/desconocido, no ejecución del objetivo y límites de la evidencia.
- `agents.json` reúne foco y checklist profesional por rol. El mismo brief se carga al **investigar y analizar**, antes de elegir fuentes. La investigación mantiene su contrato de consultas; el esquema detallado del informe se añade solo al analizar. El coordinador recibe las mismas reglas comunes y conserva sus encargos/síntesis propios.
- Seguridad prioriza los seis controles, XSS e inyecciones, secretos, dependencias y flujos externos/LLM. No se presume explotación, fuga ni incumplimiento.
- Inventario identifica motor o persistencia en archivos, uso configurado, versión declarada y perfiles de pruebas/desarrollo/producción. Arquitectura explica conexiones, datos, ubicación configurable, memoria/disco/local/externo y operación; Seguridad revisa acceso y exposición. Una librería no demuestra uso; un volumen no es backup; marcar interrumpido/error no es reanudar.
- Investigación favorece consultas por símbolo exacto o región pertinente, evitando quedarse siempre en las primeras líneas. Sin aumentar el presupuesto ni introducir reintentos.

Regresión mínima: **17 pruebas dirigidas correctas en 0,162 s** (`test_complete_flow`, `test_coordinator`, `test_compatibility`, `test_office_storage`). El caso existente del flujo ahora comprueba que las instrucciones de seguridad/persistencia y español llegan tanto a investigación como a análisis, incluidas rondas 0/1/2 y fallo posterior. Imagen del backend reconstruida; servicios saludables. Pilotos sobre `ziuld/analysis-office-test` con gpt-6-luna/low y una ronda por especialista; resultados siguientes. Después del ajuste observado se repitieron las mismas 17 pruebas, correctas en 0,203 s.

### Validación real de F2-03 y criterio del commit

[Evidencia de ambos intentos](evidence/phase2-agent-pilot-2026-10-24.json). Primer piloto `ef90bd9c-aabe-4fad-b82e-f54fade15952`: flujo terminado sin errores de formato, 8 llamadas, 65382 tokens comunicados y 122,150 s. Seguridad sin información suficiente: cuatro consultas repitieron rutas como query y dejaron fuera configuración disponible. Arquitectura e Inventario aportaron siete observaciones en total. Se conserva este resultado, sin presentarlo como mejora suficiente.

Se ajustaron únicamente las instrucciones: explicar diferencia paths/query, agrupar rutas, reservar configuración para Seguridad y priorizar la lectura de persistencia en Inventario. Sin cambios del buscador, presupuestos, modelos, rondas ni reintentos automáticos. Repetición manual única tras ese cambio.

Piloto final `e853155b-c96d-4e61-b994-6bb9e5fe3596`: **ejecución completa**, tres especialistas y síntesis terminados; **8 llamadas, 59879 tokens comunicados, 111,357 s, 6 observaciones, 5 conclusiones y 21 citas originales contrastadas**. Dos aportaciones por especialista, sin errores técnicos ni elementos rechazados por formato/fuentes. Seguridad localizó `do_POST` mediante query y combinó configuración/código; Inventario identificó persistencia JSON para las revisiones de la API en el directorio configurable de informes. Arquitectura describió que los trabajos interrumpidos pasan a error, sin afirmar reanudación automática.

El estado `completo` acredita que terminó el equipo, **no cobertura exhaustiva**: seis controles de Seguridad permanecen `no_evaluado`, con condiciones y preguntas pendientes. No se demuestra ausencia de otras bases/almacenes, seguridad efectiva ni explotación. Arquitectura llegó al cap de seis archivos; mejorar esa recuperación sigue dentro de F2-04 a F2-06. El número de hallazgos no es una métrica de calidad por sí solo. Comparado con el piloto de Fase 1 (52366 tokens), el último usa más contexto; no se afirma ahorro ni mejora general con estas muestras.

Ambas ejecuciones verificaron 69/69 archivos del mismo main remoto `b6b8adec2a36a43248ed5194bdc86b38bfeaccb6`; no evaluaron los cambios locales de Fase 2 como objetivo. Graphify 50 archivos procesados/19 incompatibles; Gitleaks sin detecciones en el snapshot y OSV sin entrada compatible. No se ejecutó el proyecto analizado. Dos intentos: **16 llamadas y 125261 tokens comunicados**, sin consumo desconocido.

Comprobaciones finales: API/preparador/oficina saludables, oficina/descarga HTTP 200, informe HTML disponible, cero trabajos/consultas activas, personajes con working=false y meeting=false, cero temporales propios de snapshot/índice. Sin inspección visual adicional. Se cumple el criterio para el commit de este paso: regresión dirigida correcta, todos los especialistas aportan, síntesis válida, sin bloqueos ni errores técnicos; la cobertura parcial queda registrada, no corregida mediante afirmaciones inventadas. Fase 2 continúa abierta y los roles nuevos siguen sin implementar.

## Parte 2: ensayo de recuperación e informe útil — 24/10/2026

**Ensayo retirado tras el feedback del usuario.** El registro siguiente conserva lo ejecutado, no describe el recuperador actual. Se restauraron evidence.py, research.py, team.py y su prueba añadida al commit c31041a; la ronda local de Seguridad volvió a 1. Se conserva únicamente el ajuste de instrucciones sobre infraestructura y la presentación de hallazgos/carencias. F2-05/F2-06 no se consideran adoptados ni cerrados por este ensayo.

Feedback adoptado: el informe abre con lo que se encontró y sus implicaciones. Docker/Compose, CI/CD, IaC y documentación cuentan como **infraestructura declarada**; no hay que exigir conocer el servidor o una VPN externa para describirla. No inventar la infraestructura efectiva ni tratar su ausencia documental como fallo. Una API externa identificada aporta información útil aunque su destino no se haya comprobado. Las condiciones específicas de un riesgo permanecen; las carencias generales y preguntas se reservan para próximas verificaciones/anexos.

### F2-04: diagnóstico sobre el mismo snapshot

Se descargó de nuevo, sin ejecutar el proyecto, el snapshot completo del mismo commit remoto `b6b8adec2a36a43248ed5194bdc86b38bfeaccb6` (69 archivos) y se reconstruyó el grafo determinista, sin modelos ni scanners. Se reprodujeron las consultas del piloto `e853155b-c96d-4e61-b994-6bb9e5fe3596`, antes y después del ajuste:

- Pedir `do_GET` en `auditor/server.py` entregaba también `auditor/repository.py`, no solicitado. Las primeras doce pistas de símbolos omitían el propio `do_GET` pese a existir en el grafo. Eso consume contexto y dificulta elegir el siguiente tramo.
- Arquitectura pidió nueve rutas pero su cap permite seis: quedaron fuera README, operación y Compose CI. No faltaban en el snapshot. La recuperación no debe etiquetar como cobertura completa todas las fuentes disponibles si parte de lo solicitado se omitió.
- Seguridad había leído POST y configuración, pero no la cadena completa de GET/proxy/permisos. Otras carencias sí requieren evidencia operativa que el repositorio no proporciona; esas no se convierten en preguntas genéricas al inicio del informe.

### F2-05: precisión de lectura, sin aumentar caps

- Las rutas explícitas limitan las lecturas a esos archivos. Vecinos del grafo se devuelven como `related_paths`, no como archivos implícitamente leídos que consuman puestos/bytes. Una ruta no disponible no activa una búsqueda fuera del alcance pedido.
- Una consulta de símbolo prioriza su localización en el grafo para leer la definición, en lugar de quedarse en una llamada anterior del mismo nombre. El símbolo pedido encabeza las pistas; se conservan las relaciones auxiliares.
- `query_not_found` y `window_omissions` hacen visibles búsquedas sin coincidencia y ventanas que no caben o están fuera de rango. No equivalen a ausencia del control. Las omisiones por presupuesto, rutas no disponibles o ventanas no entregadas dejan cobertura parcial en el resultado de la célula.
- Reproducción de `do_GET`: antes dos archivos; después solo `auditor/server.py`, ventana original 195–257 y símbolo correcto en L203 como primera pista. Mismas consultas de Seguridad: 19795 → 18657 bytes entregados. No se atribuye ahorro general de tokens de modelos a esta medida local.

### Presentación solicitada

HTML y Markdown abren con observaciones existentes, fuentes y condiciones concretas de riesgos. La descripción neutral sustituye al párrafo genérico de «no puedo determinar» cuando no existe propósito documentado. «Resultado y siguiente paso», los dominios pendientes y la lista de verificaciones pasan a anexos; no se eliminan de datos o trazas. Los informes históricos guardados no se reescriben. Las referencias de presentación de los fixtures se actualizan por este cambio deliberado; no se cambian sus resultados, contratos ni validadores para hacer pasar la prueba.

Regresión dirigida de recuperación, coordinación, formatos, enlaces y estados: **40 pruebas ejecutadas, 39 correctas y una referencia visual opcional omitida, en 0,723 s**. No es la suite completa. Se añadieron dos casos: alcance explícito/definición de símbolo, y hallazgos al inicio con carencias conservadas en anexos. La primera pasada detectó los hashes de presentación esperados del layout anterior; se actualizaron exclusivamente esas referencias tras comprobar el cambio solicitado.

### F2-06: experimento acotado y resultado

Se conservan modelos económicos, límites de archivos/bytes y una ronda de Arquitectura/Inventario. Solo la configuración local de prueba de Seguridad pasa a `AUDIT_SECURITY_RESEARCH_ROUNDS=2`: segunda ronda opcional para completar una cadena tras ver la primera respuesta. Predeterminado del producto continúa en 1; máximo del piloto nueve llamadas, sin reintentos automáticos. El piloto utilizó ocho llamadas: Seguridad terminó después de investigar y analizar, sin solicitar la segunda ronda opcional. No se demuestra beneficio de elevar ese límite. No se añaden agentes ni skills, ni se modifican CI/CD, dependencias o versiones.


[Evidencia de reproducción y piloto](evidence/phase2-retrieval-2026-10-24.json). Piloto `703a709a-0a0c-4a76-861c-cab6ceb4e38e`: **terminado, estado parcial; 8 llamadas, 63901 tokens comunicados y 113,974 s**. Snapshot 69/69 del mismo main `b6b8adec2a36a43248ed5194bdc86b38bfeaccb6`, Graphify 50 procesados/19 incompatibles. Gitleaks sin detecciones en snapshot, sin historial; OSV sin entrada compatible. No se ejecutó el código objetivo.

Seguridad aportó dos observaciones e Inventario cinco; síntesis con cinco conclusiones y veinte citas originales contrastadas, ninguna inválida entre las publicadas. El resumen abre con publicación local de la oficina, aislamiento/límites declarados y persistencia de informes JSON/Markdown. Las carencias generales aparecen en anexos. Seguridad pasó de seis controles no evaluados a cuatro no evaluados y dos con evidencia favorable limitada; una sola muestra no demuestra mejora general.

**Fallo del piloto:** Arquitectura entregó tres observaciones y dos bloques de presentación con identificadores de evidencia inexistentes, rechazados por el validador. Quedó `informacion_insuficiente` pese a recibir los seis archivos solicitados. No es ausencia de infraestructura en el repositorio ni bloqueo del flujo: las otras células y síntesis terminaron. Las trazas conservan el motivo del rechazo, pero las respuestas crudas de rechazos parciales no se guardan, de modo que no se puede reconstruir aquí qué identificador inventó el modelo. Resolver esa trazabilidad/contrato sigue pendiente antes de considerar estabilizado el equipo; no se relaja la validación ni se repite automáticamente para ocultar el fallo.

Las carencias quedan separadas: fuentes pedidas fuera del cap (replay de Arquitectura), ventanas parciales/símbolos no consultados (lectura), formatos incompatibles (mapa/scanners), evidencia operativa externa no aportada (fuera del repositorio) y referencias inválidas generadas (contrato de respuesta). Ninguna equivale automáticamente a ausencia de un control. La comparación modifica recuperación y presentación/instrucciones; no aísla causalidad ni acredita ahorro general.

Comprobaciones finales: tres servicios saludables; oficina, informe y descarga HTTP 200; cero trabajos/consultas activas y cero temporales propios de snapshot/índice. Sin inspección visual del navegador. Sin cambios de CI/CD, versiones, dependencias ni nuevos agentes/skills. F2-06 se marca realizado por completar el experimento y registrar también su fallo, no por tener una evaluación completa de Arquitectura. Fase 2 permanece abierta.


### Corrección de alcance solicitada

El usuario pidió ampliar la descripción y el dibujo de infraestructura actual con Docker/Compose, CI/CD, documentación y código, conservando el flujo previo. Se reconoce que el ensayo anterior mezcló ese pedido con cambios adicionales de recuperación y una ronda local de Seguridad; no permite atribuir causalmente el fallo de Arquitectura. Se retiraron esos cambios adicionales, sin relajar validadores ni aumentar modelos/caps. Se mantiene el cambio editorial ya solicitado: hallazgos al inicio y carencias generales en anexos.

Arquitectura sigue usando el contrato existente presentacion.flujo_actual para componentes y conexiones respaldados. Se aclara distinguir declaración/ejecución y usar referencias F#:L# de fuentes entregadas, nunca IDs del grafo como citas. No se crea otro agente ni se cambia su responsabilidad. Regresión mínima: 24 pruebas dirigidas, 23 correctas y una referencia visual opcional omitida (0,278 s). Piloto de comprobación `b92264e6-6879-415a-aaa5-0dd781c601ad` terminado con resultado parcial, detallado abajo. No hay cambios de CI/CD, versiones ni dependencias.


[Evidencia de corrección de alcance](evidence/phase2-scope-correction-2026-10-24.json): ocho llamadas gpt-6-luna/low, 65269 tokens comunicados, 130,795 s. Mismo snapshot remoto de 69 archivos; no se ejecutó el proyecto objetivo. Arquitectura entregó ocho observaciones válidas y el flujo Oficina web → API de auditoría → API de GitHub con tres componentes y dos conexiones. El HTML contiene los tres componentes; se verificó su estructura, sin inspección visual del navegador. Describe publicación local, volumen, salud/arranque, directorios JSON y tratamiento de interrupciones. Inventario aporta tres observaciones; informe con once observaciones, cinco conclusiones y treinta citas contrastadas.

El resultado sigue parcial: un bloque editorial adicional de Arquitectura se rechazó por falta de fuentes; Seguridad generó dos observaciones con formato inválido y un control sin evidencia válida. El flujo terminó sin bloqueo, conservando únicamente contenido válido; esto no es una ejecución sin errores ni estabilidad demostrada. No se puede atribuir causalidad al cambio de recuperación ni afirmar que repetir un modelo producirá idéntica salida. La corrección atiende el alcance pedido; la fiabilidad del contrato de respuesta sigue pendiente y no se oculta con reintentos o relajando validadores. No se hace commit de cierre de este paso.


### Ampliación de presupuestos aprobada por el usuario — 24/10/2026

Tras revisar límites, se aprueban Seguridad 20 archivos/100000 bytes/hasta dos rondas, Arquitectura 12/60000/hasta dos y Inventario 8/32000/una. Acumulados entre rondas; relectura de ruta no suma archivo distinto. Ventanas hasta 200 líneas, manteniendo 6000 bytes de contenido y 12000 con padding. Las segundas rondas son opcionales y dirigidas a evidencia faltante. Se actualizan registro, valores de entorno de ejemplo/locales, texto del prompt y prueba acumulada; no se modifica navegación del grafo, modelos, coordinador, CI/CD, dependencias ni versiones.

Validación mínima: 23 pruebas dirigidas correctas en 0,165 s (test_complete_flow, test_team, test_compatibility), incluyendo rondas 0/1/2, incorporación de archivos nuevos entre rondas, relectura/mezcla de ventanas de la misma ruta, rechazo del archivo que supera el cap y respeto del presupuesto de bytes. No se ejecuta otro piloto LLM en este incremento: estas comprobaciones acreditan los límites y su aplicación, no mejora semántica ni corrección de errores de formato/citas. F2-05/F2-06 continúan pendientes de comprobación de pertinencia real del código entregado.

Se aclara la lista de tres herramientas deterministas: Graphify, Gitleaks y OSV-Scanner. Semgrep, que podría ser la herramienta recordada como similar a Sonar, estaba diferido en PLAN_MVP.md y docs/SEGURIDAD.md; no se instala ni se presenta como existente. En el último piloto Gitleaks terminó sin detecciones, Graphify procesó 50 entradas/19 incompatibles y OSV no tuvo versiones resueltas compatibles.


### Punto 2: scanners multitecnología y lectura pertinente — ampliación aprobada

El usuario amplía F2-06 para corregir OSV, añadir Semgrep y validar al final. Se mantiene la historia de los ensayos anteriores; sus checklists y afirmaciones corresponden a esas fechas, no a la configuración vigente. No se pide tecnología principal: se detectan todos los formatos reconocidos presentes, incluidos monorepos. Detalle, familias, datos enviados y límites en [SEGURIDAD.md](SEGURIDAD.md).

- [x] OSV: ampliar selección Python/Java/JavaScript/.NET/Go y formatos comunes, más CycloneDX/SPDX; conservar Gitleaks y OSV fijados. Detectar requirements con nombre alternativo; habilitar resolución Maven de metadatos; registrar archivos con/sin paquetes versionados.
- [x] Semgrep: entorno aislado, versión 1.182.1 y dependencias nuevas fijadas por hashes, nueve reglas locales para cuatro familias de lenguajes. No cambios de Hermes, CI/CD ni dependencias existentes. Avisos de licencia conservados.
- [x] Lectura: corrección puntual de centro de ventana por definición del grafo, sin rediseñar alcance de consultas. Prueba de HTTP/autorización y recuperación con primera aparición como llamada anterior; citas conservan líneas.
- [x] Regresión mínima: 31 pruebas dirigidas correctas en 0,248 s (`test_scanner_inputs`, `test_security`, `test_complete_flow`, `test_research_targets`, `test_compatibility`). Se actualiza una expectativa antigua del resumen, incompatible con el pedido de mostrar hallazgos al inicio; no se relaja validación de citas.
- [x] Scanners reales con fixture controlado: siete entradas OSV, todas con paquetes extraídos (nueve paquetes y 51 coincidencias); incluye Python, npm, Maven, .NET, Go, CycloneDX y SPDX. Semgrep procesa siete archivos y detecta seis casos preparados, incluido oculto/tests y control limpio. Sin modelos ni ejecución del código fixture. Primer intento npm incompleto por omitir resolved; se corrige el fixture y se conserva el intento fallido, no se presenta como fallo de OSV solucionado cambiando el validador.
- [x] Recorrido real final con main remoto `analysis-office-test`, nuevos scanners y presupuestos, sin ejecutar el objetivo. Piloto `be8757a9-243f-4a10-9da4-b796c351d451` terminado sin bloqueos ni rechazos de formato/citas; detalle siguiente.

Los casos controlados prueban funcionamiento representativo, no todos los formatos admitidos ni cobertura de seguridad exhaustiva. El recorrido real usa el main remoto, no las fuentes locales con cambios. Sin actualización de versiones del producto ni commit/push automático de cierre; conservar hasta revisión del resultado.


### Resultado final del punto 2

[Evidencia de scanners, lecturas y recorrido](evidence/phase2-scanners-2026-10-24.json). Piloto `be8757a9-243f-4a10-9da4-b796c351d451` sobre main remoto `b6b8adec2a36a43248ed5194bdc86b38bfeaccb6`, snapshot verificado 69/69. Flujo **completo, sin bloqueos ni rechazos de formato/citas**: tres especialistas completados, siete observaciones (Seguridad 2, Arquitectura 2, Inventario 3), cuatro conclusiones y 39 citas originales contrastadas. Diagrama con seis componentes y cuatro conexiones: interfaz, API, proceso auditor, GitHub, proveedor de modelos y almacenamiento de informes; configuración declarada no prueba despliegue efectivo. Verificada estructura HTML, sin inspección visual del navegador.

Ocho llamadas Luna/low, 76451 tokens comunicados, 140,294 s. Seguridad leyó siete archivos/18514 bytes; Arquitectura doce/43664; Inventario ocho/28848. Todos dentro de presupuestos. Seguridad consultó do_POST y recibió ventana original 220–257; se conserva la relación auxiliar con repository.py, sin el rediseño de alcance retirado. Arquitectura e Inventario eligieron rutas; esto no acredita navegación por grafo óptima. Ninguno pidió segunda ronda: no se afirma beneficio real de esa opción, cuya acumulación/respeto de caps sí se prueba de forma dirigida.

Graphify procesó 50 entradas y dejó 19 incompatibles, contabilizadas. Gitleaks recibió el snapshot íntegro sin detecciones. Semgrep procesó sus 33 entradas compatibles, sin coincidencias de las nueve reglas locales. OSV no encontró formatos compatibles en ese main y quedó no_evaluado: la prueba controlada separada acredita su funcionamiento multitecnología/SBOM. No se transforma ese estado en un aprobado de dependencias. Cinco controles de Seguridad siguen no evaluados y uno tiene evidencia favorable limitada; este resultado no certifica seguridad ni exhaustividad.

Comprobación final: tres servicios saludables, oficina/informe/descarga HTTP 200, cero trabajos/consultas activas, cero temporales propios de snapshot/índice y licencia de Semgrep incluida en imagen. CI/CD, pins existentes y versión 0.3.0 conservados; Semgrep es la única herramienta nueva con sus dependencias aisladas y fijadas. F2-05/F2-06 se cierran por implementar y comprobar el alcance aprobado; comparación semántica, consumo y estabilidad de respuestas continúan en el punto 3. No se atribuye la diferencia respecto de pilotos anteriores a una sola causa. Sin commit/push de cierre en este paso.


### Repetición solicitada antes del commit

Primer intento `8da57b97-e413-4bb3-af28-409703b9cd5a`: terminó parcial, sin bloqueo global, ocho llamadas, 82167 tokens comunicados y 139,848 s. Seguridad agrupó cinco rutas de despliegue en una consulta cuyo máximo es tres; esa consulta se rechazó y terminó sin observaciones útiles. Arquitectura conservó observaciones pero perdió el diagrama por fuentes ausentes en un bloque; Inventario completó. Se conservan ocho observaciones, cinco conclusiones y veintiséis citas válidas. No se presenta como pasada correcta ni se oculta al repetir.

Corrección acotada: dividir agrupaciones excesivas en Core solo si caben dentro de las cuatro consultas totales, conservando trazabilidad, validación de rutas y caps de archivos/bytes. Si no caben, error explícito como antes, sin truncar ni ejecutar de más. Sin llamadas extra por normalizar. Se aclaran paths y fuentes del diagrama/estados en el contrato; no se relajan validadores. Once pruebas de lectura/flujo correctas tras el cambio de agrupación (0,052 s); después de aclarar el contrato, veinticuatro ejecutadas, veintitrés correctas y una referencia visual opcional omitida (0,237 s). No se amplía la suite ni CI/CD.

Segundo intento manual tras esa corrección: `33683fc9-ca9d-4ac4-a571-051d23a8d093`, terminó parcial en 148,154 s. Seguridad e Inventario completaron; Arquitectura perdió el flujo por una conexión que no cumplía el esquema. No hay reintentos automáticos ni modificación de modelos/versiones para conseguir una pasada favorable. El resultado completo y decisión de commit se registran al terminar.


Se detecta una carencia verificable del contrato: el ejemplo de Arquitectura incluía conexiones=[] sin mostrar las claves de una conexión completa. Se añade ejemplo con dos extremos, origen/destino/estado/descripcion/evidencia y estado inferida; una prueba lo contrasta contra el validador real. El contrato final explicita claves exactas y enum permitido, sin aceptar nuevos estados ni inventar fuentes. Los rechazos parciales guardan ahora respuesta oculta/limitada a 120 KB solo para diagnóstico local, nunca como aportación válida ni en el informe. Antes no se conservaba ese detalle y no se puede reconstruir la clave exacta incorrecta de los dos intentos previos.

Regresión de esta corrección: 25 pruebas ejecutadas, 24 correctas y una referencia visual opcional omitida (0,224 s). Nueva repetición manual tras el cambio de contrato, sin aumentar modelos ni límites; se registrará su resultado y se hará commit únicamente si cumple la comprobación acordada. Los intentos anteriores se conservan y no se presentan como éxitos.


### Resultado de la repetición previa al commit: NO aprobada

[Evidencia de los tres intentos](evidence/phase2-precommit-2026-10-24.json). Se añade al registro del segundo intento que la síntesis del coordinador también fue rechazada (`Respuesta o llamada inválida; sin reintento`), conservando los originales. El resumen anterior de ese intento no era un listado exhaustivo de errores.

Último intento `ddcf96bb-bad4-4bae-a779-5b0aa89dd586`: terminado parcial; ocho llamadas y 68382 tokens comunicados. Seguridad generó tema=entradas/configuracion fuera del enum de temas, y cuatro citas en un control cuyo máximo es tres. Arquitectura conservó observaciones, pero sus bloques de diagrama/operación fueron rechazados por listas de referencias inválidas: hay nodos y una conexión con cuatro citas cuando el máximo es tres. El mensaje genérico «Faltan fuentes» también cubre exceso de referencias; no demuestra ausencia de código. Inventario clasificó cuatro observaciones como componentes sin incluir el objeto componente obligatorio y quedó informacion_insuficiente. Los nuevos diagnósticos parciales permiten conservar la forma exacta de esos rechazos, en vez de atribuirlos sin evidencia a falta de código o al grafo.

El informe conserva seis confirmados, un indicio, cinco conclusiones y veintiuna citas contrastadas, sin citas inválidas entre las publicadas. No equivale a un recorrido aprobado. Adquisición y scanners terminaron; sin bloqueo global. Tres servicios saludables, oficina/informe/descarga HTTP 200, cero trabajos/consultas activos y cero temporales propios de snapshot/índice. Sin inspección visual adicional.

Tres intentos en esta comprobación: 24 llamadas y 221021 tokens comunicados. Ninguno cumplió la condición de ausencia de rechazos. Se interrumpe la tanda de pruebas, sin buscar una pasada favorable por repetición aleatoria ni elevar modelos. **No se hace commit**, porque el usuario lo condicionó a comprobar que no falla. F2-06 queda reabierta; el siguiente trabajo debe estabilizar/simplificar el contrato efectivo de salida y verificarlo antes de otro piloto, manteniendo validación de evidencia. Los cambios quedan locales y las versiones/CI/CD no cambian.


### Simplificación aprobada: agentes analizan y Core construye el informe

El usuario aprueba reducir la estructura exigida a los subagentes, conservando evidencia y resultados útiles. No se presume que todos los rechazos anteriores fueran conclusiones correctas. Se implementa `compact-v1`: tres campos obligatorios por observación; listas específicas para componentes, conexiones y controles. Se eliminan del prompt activo los esquemas repetidos/condicionales del informe v3. Brief profesional, lenguaje, límites y capacidad de consultar permanecen. Core compone títulos, metadatos y formato v3, genera IDs y verifica nombres de extremos, sin inventar infraestructura, conclusiones o gravedad. Los controles ausentes se marcan no_evaluado; dominio desconocido de un riesgo queda por_clasificar. Se conservan certeza y condiciones expresas.

Fuentes: hasta doce IDs o rangos por elemento (cuarenta líneas por rango, ochenta fuentes expandidas únicas como máximo) se contrastan contra las líneas realmente entregadas; una fuente falsa/ocultada/vacía sigue rechazándose. El resumen muestra tres y anexos conserva el detalle completo; no se pierde una observación por aportar cuatro citas válidas. Texto de observación de hasta 1200 caracteres, títulos derivados limitados para presentación. No se aumentan modelos, archivos, rondas o tokens máximos; CI/CD y versiones permanecen iguales. Compatibilidad histórica de lectura/formato y capacidad Azure comprobadas de forma dirigida.

[Evidencia del replay](evidence/phase2-compact-replay-2026-10-24.json): remapeo explícito de las respuestas anteriores al nuevo contrato, sin modelos ni scanners y con ventanas originales por rol. Conserva las tres observaciones de Seguridad (dos hechos y un indicio), seis de Arquitectura y cuatro de Inventario; diagrama con seis nodos y cinco conexiones, sin advertencias. Los seis nodos producen también registros internos para inventario; no se cuentan como seis descubrimientos nuevos. El replay no demuestra que el modelo genere correctamente el contrato compacto ni que su interpretación sea verdadera; tampoco reconstruye objetos de componentes que Inventario no entregó.

Pruebas mínimas afectadas: sesenta ejecutadas, cincuenta y nueve correctas y una referencia visual opcional omitida (1,387 s). Ocho casos del adaptador correctos después de ajustar el límite de nombre de nodo (0,338 s). Cubren fuentes inventadas/vacías, conservación de cuatro referencias en hecho/control/diagrama, certeza/gravedad, componentes sin metadatos del informe, extremos inexistentes, conservación de nodos válidos, recorrido compacto y fuentes completas en anexos. Se actualiza la expectativa del prompt para verificar un solo contrato activo en lugar de exigir que se concatenen los anteriores. El primer test del camino legacy detectó que faltaba aplicar el adaptador sin Evidence; se corrigió. La primera comprobación del resumen usó un ancla eliminada legítimamente por compactación y se dirigió al resumen real; no se cambió producto para hacerla pasar.

Piloto de generación directa `950e11ea-1d1f-4851-a025-d6a423c2a360` terminado parcial sobre el mismo main remoto: Arquitectura completó compact-v1 sin avisos; Seguridad recibió incomplete_response del proveedor durante investigación; Inventario citó rangos de líneas que el adaptador todavía no admitía y sus observaciones fueron rechazadas. La síntesis del coordinador también fue rechazada. Siete llamadas intentadas y 42889 tokens comunicados; una llamada fallida no comunicó uso, que no se cuenta como cero. Sin bloqueo global. No se repite el recorrido: el usuario solicita aislar primero especialistas. Se incorpora normalización acotada de rangos con validación de cada línea; veintisiete pruebas dirigidas correctas (0,190 s). El fallo del proveedor y la síntesis no se consideran resueltos por este cambio.


### Especialistas aislados: entradas controladas — 24/10/2026

El usuario solicita revisar las salidas por separado antes de repetir el recorrido. [Entradas, respuestas originales y revisión](evidence/phase2-isolated-2026-10-24.json). Son fuentes sintéticas inertes, no un análisis del repositorio real. Mismo adaptador Hermes y perfiles Luna/low; fuentes entregadas directamente, sin investigación, coordinador, descarga ni scanners.

- [x] Inventario con README escaso: limita la respuesta a lo documentado, sin inventar tecnología o persistencia. Con cinco archivos suficientes: identifica FastAPI/Uvicorn, versiones declaradas, Python, SQLite, DB_FILE, ruta y volumen; conserva la ausencia de inicialización/escrituras como pendiente.
- [x] Arquitectura con información escasa: no inventa componentes ni conexiones. Con fuentes suficientes: tres componentes y dos conexiones, diferencia loopback del host y bind del contenedor, configuración y ejecución efectiva, volumen y copias.
- [x] Seguridad con información escasa: cero hallazgos y seis controles no evaluados. Con fuentes suficientes: reconoce autenticación, SQL parametrizado, HTML sin escape y XSS condicionado, entorno y loopback; no inventa CVEs.
- [x] Conservar hallazgo de calidad: Seguridad marcó acceso como hallazgo sin demostrar defecto. Se aclaran los estados y se repite solo ese caso con las mismas fuentes. Devuelve evidencia_favorable_limitada para acceso y mantiene el riesgo de entradas con sus condiciones.
- [x] Conservar fallo de la séptima respuesta: JSON completo seguido de </final>. El adaptador elimina únicamente ese sufijo cuando lo precede un objeto JSON válido; no repara contenido arbitrario. Replay de las siete respuestas sin rechazos ni advertencias; sin octava llamada.
- [x] Regresión mínima en Linux: 31 pruebas correctas, 1,053 s, sin red. El intento host encontró imports fcntl incompatibles con Windows; se verifica en el entorno Linux previsto, sin modificar producto para ese error.

Siete llamadas reales, 19851 tokens comunicados, 93,438 s sumados de invocación; sin reintentos automáticos. Se conserva el estado inicial fallido, sin convertirlo retrospectivamente en éxito del proveedor. La primera tanda de seis pasó formato/citas; eso no impidió detectar el matiz semántico de acceso. Arquitectura también exagera ligeramente la garantía de proporcionar API_KEY fuera de Git: Compose requiere una variable y contiene ese mensaje, pero no demuestra que nunca se versionó. No se oculta ese límite ni se fuerza otra llamada para obtener una respuesta ideal.

**Resultado:** especialistas útiles en los casos controlados y correcciones de formato comprobadas. Esto no prueba recuperación por grafo, estabilidad en otros repositorios ni coordinación/síntesis. F2-06 sigue abierta hasta verificar esa integración pendiente; no se ejecuta ahora otro flujo completo ni se hace commit/push. CI/CD, modelos, presupuestos y versión 0.3.0 conservados.

Imagen local reconstruida y API actualizada con las correcciones verificadas: audit-api, office y preparator saludables, oficina HTTP 200 y cero trabajos/consultas activos. Sin inspección visual del navegador.


### Template ejecutivo v14 y Seguridad medium — 24/10/2026

Propuesta v14 del usuario adaptada al renderer real; [registro de verificación](evidence/phase2-template-2026-10-24.json). El HTML original del demo y los informes guardados no se modifican.

- [x] Resumen y prioridades, aplicación/datos, recomendaciones y anexos. Un único detalle completo por riesgo; contador de controles distingue riesgos, defensas limitadas, no evaluado y no aplica, sin puntuación.
- [x] Mostrar observaciones compactas de persistencia y funcionamiento sin exigir otra estructura a los agentes. Mantener fuentes/certeza y acciones de riesgos por_clasificar; no inventar infraestructura ni convertir ausencia de copias documentadas en un riesgo nuevo.
- [x] Azure condicionado a propuesta explícita válida; sin servicios/pipelines fijos ni tablas obligatorias vacías. Detalles de scanners/mapas y cobertura completa en anexos.
- [x] Detalle HTML estático, enlaces entre prioridades y anexos, impresión con anexos abiertos y restauración posterior. Revisada captura de escritorio; comprobados layout móvil sin desbordamiento y PDF con anexos.
- [x] 28 pruebas dirigidas correctas, 1,463 s. Referencias de render HTML/Markdown actualizadas por el cambio aprobado; datos JSON históricos y prompt standalone intactos. Sin ampliar CI/CD.
- [x] Configurar solamente Seguridad en gpt-6-luna/medium mediante .env y .env.example. Se interpreta «a medio» como razonamiento medium; no se cambia a Sol ni se atribuye una mejora de resultados todavía.
- [ ] Revisar y aceptar la nueva vista previa. Probar coordinador/síntesis antes del siguiente recorrido completo; F2-06 continúa abierta.

Vista previa artifacts/informe-v14-vista-previa.html generada a partir de las tres respuestas guardadas sobre fuentes sintéticas. Conserva el perfil low realmente utilizado por esas respuestas y señala el cambio a medium para futuras ejecuciones. Cero llamadas nuevas, scanners o descarga; no se inicia el flujo completo. Sin commit/push en este paso; versión 0.3.0 conservada.


### Recorrido completo solicitado con v14 y Seguridad medium — 24/10/2026

[Evidencia y diagnóstico](evidence/phase2-v14-full-flow-2026-10-24.json). Trabajo `9755814d-b669-4ba2-b2d2-ca86107ad71b`, main remoto `b6b8adec2a36a43248ed5194bdc86b38bfeaccb6`; no analiza las modificaciones locales. Termina **parcial**, sin quedarse bloqueado, en 166,873 s. Nueve llamadas reales, 90827 tokens comunicados. Seguridad Luna/medium; resto Luna/low. No se inicia otra tanda ni se hace commit/push.

- [x] Descarga íntegra verificada: 69/69 archivos, 68 de texto y uno binario. Graphify procesa 50 y contabiliza 19 sin parser compatible. Gitleaks recibe 69 sin detecciones; Semgrep procesa 33 compatibles sin coincidencias de las nueve reglas. OSV no encuentra formatos compatibles y queda no_evaluado; no se presenta como aprobado.
- [x] Encargos iniciales del coordinador válidos. Los tres especialistas investigan y entregan resultados: Seguridad 11 archivos/33617 bytes/3 llamadas, Arquitectura 8/36372/3, Inventario 5/13524/2. Dentro de sus presupuestos; no hay fallo de proveedor.
- [x] Informe HTML v14/Markdown generado y servido HTTP 200. Se conservan 24 observaciones/registros de componentes, un riesgo medio condicionado, cinco nodos y una conexión. Las 299 citas únicas publicadas coinciden con las fuentes originales retenidas. Cero IDs duplicados o enlaces internos rotos. Sin propuesta cloud inventada.
- [ ] Citas de Seguridad/Arquitectura/Inventario: rangos incluyen líneas ocultadas por el filtro de posibles credenciales en auditor/runtime.py (32, 34 o 36). Se rechazan sus elementos, no se pierden todos los resultados. La ocultación heurística no demuestra que existan secretos reales. Se mantiene la protección: esas líneas no se publican como evidencia.
- [ ] Arquitectura: F6:L27-L67 abarca 41 líneas, supera el máximo de 40. Se descarta el componente Proceso de auditoría; tres conexiones quedan sin extremo válido y también se descartan. No es ausencia del código ni fallo de descarga/grafo.
- [ ] Síntesis: prompt de 80010 bytes frente al máximo de 32000; se corta antes de llamar al modelo (cero llamadas de síntesis). Mensaje público genérico Respuesta o llamada inválida; la medida y el límite permiten diagnosticar el motivo exacto. Los resultados originales permanecen en el informe.
- [x] Cierre operativo: tres servicios saludables, cero trabajos o consultas activos. No se ejecutó el objetivo, no se modifican CI/CD ni versiones. F2-06 continúa abierta; esta ejecución no cumple la condición de ausencia de rechazos.

Resultado útil: identifica configuración Docker, persistencia de informes JSON/Markdown bajo /reports y estado en volúmenes, recuperación de trabajos interrumpidos como error y controles defensivos visibles. El riesgo de acceso descrito se refiere al manejador del main remoto y depende de exposición/controles externos; no demuestra explotación ni describe automáticamente el servicio local actualizado.

Siguiente ajuste acotado a valorar: evitar que las referencias incluyan líneas ocultadas/rangos excesivos, conservando solo fuentes realmente válidas sin inventarlas; y compactar las aportaciones enviadas al orquestador, que no necesita recibir de nuevo todas las citas completas para redactar una síntesis. Mantener evidencia íntegra en Core. No elevar modelos, presupuesto ni relajar la protección de fuentes para ocultar estos fallos.


### Perfil de capacidad para el próximo repositorio — 24/10/2026

El usuario solicita subir modelo y razonamiento de todos los agentes antes de aportar otro repositorio. Catálogo vivo de Hermes/Codex consultado sin generación: gpt-6.1-sol disponible para esta sesión. Se configura AUDIT_MODEL=gpt-6.1-sol y AUDIT_REASONING=medium en .env y .env.example; overrides vacíos heredan ese perfil para Coordinador, Seguridad, Arquitectura, Inventario y consultas. El helper legacy de preparación también lo hereda si se invocara; la preparación completa actual sigue siendo determinista.

Elección inicial equilibrada según https://developers.openai.com/api/docs/models y https://developers.openai.com/api/docs/guides/reasoning, no un óptimo demostrado sobre nuestras muestras. Se conserva el proveedor openai-codex y suscripción, sin cambios de claves, versiones, CI/CD, rondas, archivos, bytes o salida máxima. Los defaults económicos del registro de proveedor se conservan como fallback para configuraciones sin estos overrides explícitos.

- [x] Verificar disponibilidad mediante catálogo de cuenta; sin llamadas de análisis.
- [x] Ajustar configuración local y ejemplo para todos los roles, sin overrides antiguos de Luna/low.
- [ ] Probar calidad y consumo sobre el nuevo repositorio que aportará el usuario. No se inicia análisis ni generación de modelos en este paso.

Cambiar a Sol/medium no resuelve por sí mismo los rechazos de rangos con líneas ocultadas, el rango de 41 líneas ni la síntesis de 80010 bytes frente al cap de 32000. Esas correcciones de integración continúan pendientes; no se presentan como resueltas ni se aumentan límites para esconderlas.


### Nuevo repositorio y correcciones de preparación — 24/10/2026

El usuario aporta beneath-the-code-page para comprobar Sol/medium. [Evidencia de los fallos y correcciones](evidence/phase2-frontend-preparation-2026-10-24.json). Commit 95ede5bccc881a2230f874944299b4a73101337d, con Java/Maven además de frontend TypeScript; no se limita artificialmente al frontend.

- [x] Primer intento 6fcd5f7a-35a6-49e1-8fc0-9da6921984f6: detenido en integridad del snapshot, cero modelos. .gitattributes solicita CRLF en *.cmd; el tar de GitHub transforma mvnw.cmd (8481 bytes frente a 8292 del blob). Recuperación acotada por SHA del blob original, conservando verificación, capacidad y tiempo; nunca aceptar el contenido divergente sin verificar. Dos pruebas de adquisición correctas, 0,022 s.
- [x] Segundo intento f1bc20ad-6df9-4f2a-9119-9df68f1ac709: detenido en extracción antes de modelos. Graphify declara algunos JSON de datos como incompatibles; nuestro adaptador lo trataba como error. Se reconocen solo dos motivos nativos de exclusión JSON y se conservan en cobertura; errores reales siguen bloqueando. Dos pruebas con Graphify instalado correctas, 3,269 s. Primeros intentos de esas pruebas necesitaron PYTHONPATH explícito por PYTHONSAFEPATH y cwd temporal escribible para caché; se corrigió el entorno de test, sin modificar producto por esos errores.
- [x] Tercer intento 147509c2-56ea-45c5-96c5-ee2aefc92329 supera preparación: 567/567, 557 textos y 10 binarios, 10200922 bytes. Graphify 439 procesados/128 incompatibles contabilizados; Gitleaks sin detecciones, OSV 273 paquetes sin avisos comunicados y Semgrep un patrón por contrastar.
- [x] Ejecución terminada parcial; continuación y diagnóstico final registrados a continuación. No se repite el recorrido. Los dos fallos de preparación no gastaron modelos; la ejecución de agentes sí consumió cuota.

Sin ejecución del objetivo, cambios de CI/CD ni versiones. Las correcciones pertenecen a adaptadores de adquisición/cobertura; subir modelos no resuelve esos supuestos. No se atribuye al repositorio ni a falta de inteligencia un fallo previo a los agentes.


### Resultado Sol/medium sobre beneath-the-code-page y síntesis compacta — revisión 25/10/2026

[Evidencia final](evidence/phase2-frontend-sol-2026-10-25.json). Trabajo 147509c2-56ea-45c5-96c5-ee2aefc92329 terminado parcial en 283,411 s. Ocho llamadas intentadas, 84338 tokens comunicados; una llamada sin medida no se cuenta como consumo cero. No se compara causalmente Sol y Luna sobre repositorios distintos.

- [x] Seguridad completada, tres llamadas, doce archivos, cinco observaciones sin rechazos de formato/citas. Contrasta el patrón Semgrep de proof.worker.ts: new Function recibe el literal return 7, no la entrada del usuario; no confirma una vulnerabilidad. Identifica escape/saneamiento HTML/URL, presupuesto UTF-8 de entrada y configuración de contenedor/workflows. Cuatro controles con evidencia favorable limitada y dos no evaluados; no certifica seguridad.
- [x] Arquitectura completada, tres llamadas, doce archivos, diecisiete observaciones/registros de componentes sin rechazos. Describe Spring Boot/JAR, Thymeleaf, TypeScript/workers, Docker y entrega declarada. Predomina documentación; declara que no contrastó toda la cadena Java productiva. Las afirmaciones sobre privacidad, pruebas previas y recuperación se mantienen como documentación/evidencia histórica, no ejecución actual.
- [ ] Inventario falló en su primera investigación: Hermes clasificó cuota o límite de peticiones; no fue falta de código ni JSON inválido. Sin reintento automático y sin inventar aportación. No se relanza por la preocupación del usuario sobre consumo.
- [x] Informe v14 conserva 22 observaciones/registros y 301 citas únicas contrastadas; sin citas inválidas, IDs duplicados o enlaces internos rotos. No hay hallazgos de vulnerabilidad confirmados en lo revisado; esto no implica cobertura total.
- [ ] Síntesis real no ejecutada: 92535 bytes frente al cap de 32000. Repetía citas completas que el orquestador no necesita para sintetizar aportaciones ya validadas.
- [x] Corrección mínima de síntesis: enviar observaciones, certeza, gravedad, condiciones y acciones por ID; Core conserva las citas completas y las contrasta al resolver los IDs de salida. No se recortan observaciones ni se eleva el presupuesto. Replay offline de ambos informes: 80010 → 22083 bytes (24 aportaciones) y 92535 → 23560 (22). Respuesta de contrato simulada, cero proveedor; no equivale a síntesis semántica real ni se sobrescriben informes anteriores. Cinco pruebas de coordinador correctas, 0,490 s, incluida conservación de sesenta fuentes y condiciones. Primer replay host falló por permisos del temporal de Windows; se ejecutó en temporal dentro de artifacts, sin cambio de producto por ese error.
- [ ] Confirmar la corrección en una síntesis real cuando se autorice gasto y haya cuota disponible; F2-06 sigue abierta. Las correcciones de citas ocultadas/rangos excesivos del piloto anterior continúan pendientes; en este repositorio Seguridad y Arquitectura no tuvieron esos rechazos.

No se gastan nuevas llamadas a modelos durante la continuación del 25/10. Sin CI/CD, actualización de pins/versiones ni commit/push de cierre. Se conserva el informe parcial original como evidencia, sin convertirlo en una pasada completa por edición.


### Vuelta a Luna y comprobación previa al commit — 25/10/2026

El usuario solicita volver a Luna, comprobar funcionamiento sin errores y hacer commit antes de nuevas mejoras de calidad. Se configura gpt-6-luna/medium para todos los roles mediante .env y .env.example; modelos/versiones de herramientas, presupuestos y CI/CD permanecen sin cambios.

Primer intento 5e077251-624b-4abd-a311-361b381470bd: preparación completa, Arquitectura e Inventario completados sin rechazos y síntesis real completada con prompt de 19574 bytes. Nueve llamadas, 72046 tokens comunicados, 168,112 s. Seguridad conserva sus observaciones, pero informa dependencias como evidencia_favorable_limitada solo a partir del resumen OSV, sin referencias F#:L#. El validador rechaza ese control y lo deja no_evaluado; el informe resulta parcial. Se conserva el intento y no se presenta como pasada correcta.

Se aclara únicamente el prompt de Seguridad: los resultados de scanners ya aparecen aparte; sin fuentes F#:L# un control queda no_evaluado, aunque pueda explicar el estado de OSV en su motivo. No se añaden referencias inventadas ni se admiten controles favorables sin respaldo. Se mantiene la validación estricta. Segunda ejecución completa tras esa corrección, sin cambiar modelos, límites ni selección de fuentes para buscar una pasada favorable. Su resultado y la decisión de commit se registran al terminar.


Segundo intento Luna e70468fd-d96d-4973-9066-bc5aeab676fa: llegó al final con Arquitectura y síntesis completas, pero rangos de 41 y 46 líneas se rechazaron en Inventario y en un control no_evaluado de Seguridad. La regla de dependencias quedó corregida: no reaparece el control favorable sin fuentes. Se conserva esta segunda pasada como parcial, sin llamarla éxito.

El replay de esas respuestas mostró una segunda restricción redundante: el control válido de Seguridad suma 82 fuentes, por encima de 80. La comprobación de unificación a 80 también falló y se conserva como diagnóstico; no se hizo una llamada al modelo para ese replay. Se alinea el formato con la ventana de investigación ya existente de 200 líneas: una constante MAX_EVIDENCE_REFS=200 gobierna informe, contenido estructurado y contrato compacto; hasta doce IDs/rangos por elemento. Archivos, bytes, ventanas, rondas y límites de modelos no cambian. Cada fuente sigue contrastada contra texto recibido y se siguen rechazando líneas ocultadas, falsas, vacías o fuera del fragmento. No se acepta una fuente por el mero hecho de estar dentro del límite.

Las dos respuestas reales se revalidan offline sin advertencias, manteniendo 82 fuentes del control y 56 de la observación de Inventario. Cuarenta y seis pruebas dirigidas correctas, 1,223 s; incluye exceso de 200 fuentes, fuentes inventadas/ocultadas, formato, coordinador y presentación. El cambio no certifica la interpretación de las observaciones. Tercer recorrido funcional con Luna/medium tras esa corrección; no se modifican instrucciones de calidad, herramientas/versiones ni CI/CD. Su resultado decide el commit.


### Comprobación funcional de cierre antes del commit: aprobada — 25/10/2026

[Evidencia completa y dos intentos previos conservados](evidence/phase2-luna-validation-2026-10-25.json). Trabajo d506794d-6b23-4d84-bab8-c9438d678d7b sobre beneath-the-code-page, commit remoto 95ede5bccc881a2230f874944299b4a73101337d. **Flujo completo, sin errores ni advertencias**: preparación, encargos, tres especialistas, síntesis y generación/entrega del informe v14. No se reetiquetan los dos intentos anteriores.

- [x] Snapshot completo 567/567; mapas y scanners terminan con sus coberturas explícitas. OSV evalúa versiones; las incompatibilidades del mapa siguen contabilizadas y no se presentan como AST procesado.
- [x] Coordinador: routing y synthesis complete, una llamada cada etapa; síntesis de 24169 bytes, dentro del cap de 32000. Cinco conclusiones conservando originales y referencias.
- [x] Seguridad, Arquitectura e Inventario completados en Luna/medium, dos llamadas cada uno, sin rechazos o errores. Veintiséis observaciones/registros de componentes; no se cuentan como veintiséis vulnerabilidades. Seguridad conserva cuatro controles no_evaluado y dos defensas limitadas, sin convertir falta de información en aprobado.
- [x] 352 citas únicas contrastadas, cero citas inválidas; HTML sin IDs duplicados ni enlaces internos rotos, cuatro nodos y tres conexiones. Informe HTTP 200, tres servicios saludables y cero trabajos/consultas activos.
- [x] Ocho llamadas, 66017 tokens comunicados, 143,411 s. En esta comprobación previa al commit hubo tres intentos: 25 llamadas y 198316 tokens comunicados en total. Las dos pasadas parciales se conservan con sus causas; cada repetición siguió una corrección concreta, sin elevar modelos para conseguir un aprobado.
- [x] Regresión dirigida: 46 pruebas correctas, más caso explícito de línea ocultada correcto. Las dos respuestas problemáticas se revalidaron offline antes de la tercera ejecución. Sin suite completa añadida ni cambios de CI/CD.
- [x] Se cumple la condición funcional solicitada para hacer commit local. F2-06 se cierra por integración; En ese momento F2-07 a F2-10 seguían pendientes; su alcance fue sustituido posteriormente por F2-07 a F2-12 en el punto 3 vigente.

Se conserva versión 0.3.0, pins existentes, informes anteriores y demo del usuario. No se hace push ni se actualiza el PR en este paso. La comprobación no certifica seguridad, calidad óptima, exhaustividad semántica ni estabilidad estadística; acredita que el recorrido de este commit terminó sin errores de integración. Las correcciones de líneas ocultadas del piloto anterior continúan como asunto acotado pendiente: esta pasada no tuvo ese rechazo, y la protección sigue verificada por prueba.
