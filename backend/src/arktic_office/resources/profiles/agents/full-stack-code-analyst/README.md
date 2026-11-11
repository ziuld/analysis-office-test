# Iris · Full Stack

Iris realiza una revisión estática individual del repositorio y responde las 40 preguntas de Arktic Office. En la oficina, activa **Usar Full Stack** al iniciar la revisión. La API acepta `full_stack: true` y la CLI ofrece `--full-stack`. La modalidad queda registrada con la revisión. El equipo sigue siendo la modalidad predeterminada.

## Cómo trabaja

Core divide la revisión en siete tareas. Cada tarea recibe sus preguntas, fuentes iniciales y resultados de búsqueda. Iris registra lo comprobado, cita rutas y líneas, y anota lo que queda pendiente. La síntesis usa las respuestas y citas guardadas de los seis bloques anteriores.

| Tarea | Preguntas |
| --- | --- |
| Aplicación | Q04–Q07 |
| Estructura | Q08–Q09 |
| Datos | Q10–Q13 |
| Operación | Q15–Q22 |
| Seguridad de identidad y navegador | Q23–Q31 |
| Seguridad de servidor y datos | Q14 y Q32–Q37 |
| Síntesis y alcance | Q01–Q03 y Q38–Q40 |

El perfil reserva siete llamadas de tarea y hasta once rondas de búsqueda, con un máximo de 18 llamadas al modelo y 1.080 segundos para Iris. Cada bloque de seguridad tiene dos rondas reservadas dentro de ese presupuesto. Las fuentes iniciales se limitan a ocho archivos y 7.200 bytes. El perfil admite hasta 200 archivos y 600.000 bytes de fragmentos durante la investigación. El presupuesto global también se aplica. Para `openai-codex`, el adaptador establece 90 segundos de inactividad entre eventos de forma predeterminada.

Core guarda el avance por tarea en `agents/full-stack-code-analyst/workflow.json` y las llamadas y su consumo en `metrics.json`, dentro de la carpeta de la revisión. Publica HTML y Markdown con las 40 preguntas, las citas y la autoría de Iris. Un informe parcial identifica qué se comprobó y qué sigue pendiente. La revisión estática puede acreditar un patrón de código y dejar abierta su explotación o configuración efectiva.

## Archivos del perfil

- [AGENT.md](AGENT.md) define el método común de revisión y el contrato de salida.
- [workflow.toml](workflow.toml) ordena las tareas y declara sus dependencias, grupos de fuentes y campos de salida.
- [tasks/](tasks/) contiene las preguntas completas, los criterios de evidencia y el cierre de cada tarea. El encabezado de cada pregunta usa la forma `### QNN · Pregunta`.
- [initial-sources.toml](initial-sources.toml) configura la selección de fuentes antes de la primera llamada.
- [evals/casos.toml](evals/casos.toml) contiene casos de la suite de backend con un proveedor simulado.

## Validación de esta fase

La corrida integral de Web Corporativa 2.0 en `develop@4ae82b4` completó las siete tareas con GPT‑6.1 Sol, esfuerzo medio y `openai-codex`. Publicó Q01–Q40 una vez en cada formato con 18 llamadas nuevas. El informe quedó parcial por cobertura. En esa captura, Iris reconoció cuatro de los seis riesgos de referencia. Quedaron pendientes la política de scripts en línea, el flujo de CV con antimalware desactivado y la clasificación de dos alertas de Gitleaks. Los resultados y la comparación con el equipo están en el [plan de coordinación centralizada](../../../../../../../docs/PLAN_COORDINACION_CENTRALIZADA.md#resultado-del-paso-9--iris-integral--11112026).

Para esa corrida, el lanzador de evaluación protegió 57 líneas antes de enviarlas al proveedor. El flujo habitual conserva el texto de los fragmentos seleccionados, incluidas las líneas que marquen los escáneres.
