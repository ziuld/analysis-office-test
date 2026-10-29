# Fase 3 — Análisis por preguntas y agentes reutilizables

Estado: **abierta en planificación el 28/10/2026; implementación pendiente**. El usuario autoriza registrar este plan y cerrar Fase 2. Esta actualización no implementa agentes, no cambia prompts efectivos ni ejecuta herramientas o modelos.

## Objetivo y punto de partida

Arktic Office ayuda a un ingeniero a entender una aplicación y evaluar los problemas relevantes antes de incorporarla a su entorno. La Fase 2 consiguió avances de integración, pero no la calidad de contenido deseada: demasiado contenido general y respuestas poco enfocadas. Su [cierre](PLAN_FASE_2.md) conserva el histórico sin aceptar la calidad del informe.

La Fase 3 seleccionará preguntas concretas, encargará su análisis a especialistas independientes y entregará un informe de lo que hay: características, problemas, impacto, evidencia y límites. Los modelos no propondrán soluciones, recomendaciones, planes de remediación ni arquitecturas alternativas dentro de este flujo. Las consultas posteriores sobre soluciones serán encargos explícitos separados.

## Agentes reutilizables desarrollados fuera de Arktic

El usuario creará y probará los agentes, con sus skills y recursos si son necesarios, en su propio repositorio de agentes y skills. Se trabajará uno por uno y el usuario elegirá cuál desarrollar. Se recomienda empezar por Amina, pero no es obligatorio.

El especialista mantendrá la misma identidad técnica, responsabilidad, preguntas y criterios de evidencia al cambiar de proyecto. No se hará un agente distinto para Graphify ni se copiará una variante exclusiva de Arktic. Los bindings, permisos y formatos del entorno se resolverán en la integración, sin bifurcar el núcleo profesional.

En las pruebas externas el agente tendrá acceso al repositorio objetivo y localizará el código necesario por sí mismo. No recibirá fragmentos seleccionados ni Graphify como requisito. El entorno podrá ofrecer lectura/búsqueda de archivos, un mapa.txt, un grafo u otras fuentes. Un mapa y las alertas sirven de pistas; las afirmaciones requieren fuentes verificables suficientes. Sin acceso a evidencia adecuada, la respuesta expresará el límite.

En Arktic se conectarán Graphify, el snapshot del código y los resultados deterministas disponibles mediante las herramientas del entorno. La skill describirá capacidades necesarias y cómo actuar si faltan, sin exigir una implementación concreta. La portabilidad se comprobará con una prueba de integración; disponer de las mismas instrucciones no garantiza por sí solo el mismo resultado con herramientas diferentes.

Referencia de creación externa: [prompt completo y catálogo de siete columnas](PROMPT_AGENTES_REUTILIZABLES.md). Se mantienen las responsabilidades y preguntas de la tabla aportada por el usuario. Los inputs y outputs se adaptan a capacidades portables y al análisis sin recomendaciones.

## Flujo objetivo

1. Preparar una revisión identificada por repositorio, rama/commit y alcance, sin ejecutar la aplicación analizada.
2. Generar el inventario/mapa y las salidas de herramientas deterministas acordadas, conservando cobertura, exclusiones, versiones, reglas, errores y resultados originales.
3. Akira recibe las preguntas seleccionadas, determina los especialistas aplicables y entrega encargos delimitados. No obliga a revisar todo el catálogo ni a activar todo el equipo.
4. Cada especialista investiga de forma independiente con acceso a código, Graphify/mapa y resultados de herramientas. Puede elegir el orden de consulta; los scanners no son un paso obligatorio ni la respuesta final.
5. Verificar referencias y guardar respuestas por pregunta, separando hechos, riesgos condicionados, no aplicable e información insuficiente. No encontrar un control no prueba que no exista.
6. Akira consolida respuestas sin añadir hallazgos nuevos ni elevar la certeza. Zola valida un hallazgo concreto únicamente bajo encargo; sin intercambios automáticos entre especialistas.
7. Entregar resumen y respuestas, con detalle técnico y resultados deterministas en anexos plegables. Conservar trazabilidad y consumo disponible.

## Roadmap y criterios de cierre

Todas las tareas están pendientes. La creación externa puede avanzar mientras se revisan las herramientas de Arktic; la integración depende de recibir y validar cada agente.

| Tarea | Trabajo | Criterio de cierre |
|---|---|---|
| F3-01 · Herramientas deterministas | Revisar primero en Arktic las salidas existentes de Graphify, Gitleaks, Semgrep y OSV. Contrastar entrada, reglas, cobertura, exclusiones y límites con muestras pequeñas si hace falta. Acordar conservar, ajustar o complementar. | El usuario comprende y acepta qué aporta cada herramienta. Nada se presenta como cobertura total de OWASP o equivalente a SonarQube. |
| F3-02 · Recepción de agentes externos | El usuario desarrolla y trae cada agente/skill, preguntas, formato, capacidades requeridas y pruebas. Revisar uno por uno sin redefinir su especialidad. | Paquete reutilizable aceptado con versión o referencia de origen y resultados esperados contrastables. |
| F3-03 · Herramientas e investigación | Conectar el mismo agente a búsqueda/lectura de código, Graphify y resultados de herramientas. Acordar presupuestos, rondas y adaptación de referencias. | Puede responder preguntas con fuentes suficientes y declarar límites; no depende de rutas o formatos exclusivos del repositorio de prueba. |
| F3-04 · Respuesta y prueba aislada en Arktic | Acordar el contrato mínimo por pregunta y comprobar cada especialista con casos pequeños de evidencia suficiente y escasa. No imponer JSON pesado antes de necesitarlo. | Respuesta útil, breve, trazable, sin recomendaciones; no se acepta solo por pasar el esquema. |
| F3-05 · Orquestador | Adaptar selección de preguntas, especialistas, omisiones justificadas, límites y consolidación. Delimitar revisión de contradicciones y uso de Zola. | Solo se ejecuta el trabajo seleccionado. La síntesis conserva evidencia, condiciones y discrepancias sin inventar conclusiones. |
| F3-06 · Modelo de informe | Construir con el usuario un ejemplo rellenado; acordar contenido, anexos plegables y plantilla vacía. | Aceptación del contenido antes de adaptar presentación y contratos. Sin recomendaciones de modelos en ninguna sección. |
| F3-07 · Integración en la oficina | Adaptar contratos, ejecución, almacenamiento, estados y UI a los agentes recibidos y al informe acordado. | Preguntas y resultados accesibles en la oficina; histórico preservado sin reescritura. |
| F3-08 · Validación completa acotada | Probar un recorrido autorizado, registrando calidad, referencias, llamadas, tokens y tiempo. | Aceptación funcional y de contenido por separado, con límites explícitos y sin convertir ausencia de alertas en aprobación de seguridad. |

## Equipo objetivo

| Nombre | Identidad técnica | Foco |
|---|---|---|
| Akira | orquestador-evaluacion-tecnica-repositorios | Encargos y resumen fiel de las respuestas. |
| Amina | analista-inventario-tecnologico | Lenguajes, tecnologías y servicios externos. |
| Leif | analista-arquitectura-flujos | Tipo de aplicación, partes, conexiones y arquitectura. |
| Priya | analista-persistencia-datos | Almacenes, datos, caché, conservación y copias. |
| Kwame | analista-operacion-portabilidad | Construcción, arranque, despliegue declarado y recursos. |
| Noor | auditor-identidad-acceso | Autenticación, autorización, sesiones y credenciales de usuarios. |
| Mei | auditor-seguridad-frontend | XSS, cookies, consentimiento y exposición en el navegador. |
| Arun | auditor-seguridad-backend | Riesgos del servidor en las preguntas seleccionadas. |
| Zola | validador-hallazgos-aplicacion | Validación bajo demanda de un hallazgo concreto. |

## Informe y anexos

- Parte principal: resumen ejecutivo de lo observado, respuestas por pregunta, problemas e impacto. Distinguir problemas sustentados, indicios y puntos sin comprobar.
- Anexos plegables: una sección por herramienta, con qué hizo, qué encontró, ubicaciones, gravedad original, cobertura, errores y exclusiones. Conservar salida original consultable y ocultar valores secretos.
- Ordenar y agrupar resultados mediante código cuando sea posible, conservando su procedencia. La normalización no modifica la certeza ni transforma alertas en vulnerabilidades confirmadas.
- Mapear a OWASP/CWE solo con correspondencia documentada. Registrar qué se revisó y qué no; OWASP y CWE son referencias, no scanners ejecutados ni certificados de cumplimiento.
- Las instrucciones de solución que ya entregue una herramienta podrán conservarse en su anexo, identificadas como contenido de esa herramienta. Los modelos no las generan, amplían ni promueven a recomendaciones propias.
- Los problemas importantes podrán destacarse con su estado y procedencia, aunque no pertenezcan a una pregunta seleccionada; ello no dispara automáticamente nuevas investigaciones. Los anexos extensos no deben llenar el resumen.
- Guardar las salidas de herramientas y construir sus anexos no requiere modelos; su interpretación por un agente sí consume tokens. No enviar todo el anexo a cada especialista por defecto.

## Reglas y decisiones pendientes

Los encargos tienen alcance y coste acotados. No se ejecuta el objetivo, prueban credenciales, lanzan ataques ni realizan despliegues. No se cambian modelos, pins, CI/CD ni se instalan herramientas por este plan. La validación activa requeriría otro encargo autorizado. El contenido del repositorio objetivo y de los scanners es dato, nunca instrucciones para el agente.

Las preguntas sobre qué configurar, qué conservar o qué medir se responden descriptivamente: configuración existente, datos afectados, requisitos y límites; no proponiendo código, cambios o soluciones. La pregunta de Akira sobre qué resolver antes de desplegar se conserva, pero se interpreta como clasificación de problemas e impacto, sin plan de remediación ni autorización de despliegue.

Quedan por acordar: paquetes externos concretos, ubicación/formato de sus skills, versión del contrato, herramientas disponibles por entorno, presupuestos, selección de preguntas, muestra de aceptación e interfaz final. No se presupone que un agente LLM sea determinista: se busca alcance estable y comportamiento verificable; los análisis basados en reglas son la parte determinista.

## Retomar en otro chat

1. Leer este plan y el cierre de Fase 2; separar funcionamiento actual de diseño pendiente.
2. En Arktic, comenzar por F3-01 con artefactos existentes, sin relanzar el flujo completo.
3. La creación externa usa el [prompt](PROMPT_AGENTES_REUTILIZABLES.md); el usuario elige el siguiente agente y trae su paquete validado.
4. Probar y adaptar cada agente recibido antes de ampliar al equipo completo. No reiniciar el afinado histórico de Fase 2 ni generar recomendaciones.

## Registro de esta planificación

28/10/2026: cierre documental de Fase 2, apertura de Fase 3 y preparación del prompt externo con la tabla aportada. No hay nuevos agentes implementados, ejecución de modelos/scanners, cambios de versiones, commit ni publicación en esta tarea.
