# Propuesta para estandarizar los agentes independientes

11/11/2026 · Plan aprobado · Base `947f9af`

## Punto de partida

Los siete especialistas ya tienen identidad, preguntas y fuentes iniciales en carpetas independientes. Hoy su ejecutor va acumulando los fragmentos y el historial de consultas en el prompt. Iris añade tareas con cierre propio, resultados parciales persistidos y recuperación selectiva de citas. La propuesta lleva esas capacidades a los especialistas mediante un ejecutor compartido y deja que cada perfil defina qué investiga, con qué evidencia y cuándo cierra.

En Web Corporativa 2.0, Iris gastó un 45,5 % menos de tokens que el equipo, pero reconoció cuatro de sus seis riesgos principales. Esa prueba comparó dos modalidades. Para evaluar esta migración se comparará **equipo actual frente a equipo por tareas**, con los mismos especialistas y la misma captura. [Resultados de la prueba de Iris](PLAN_COORDINACION_CENTRALIZADA.md#resultado-del-paso-9--iris-integral--11112026)

## Estándar del perfil

```text
resources/profiles/agents/<id>/
├── agent.json                 Identidad, nombre y metadatos de la oficina
├── README.md                  Alcance, uso y límites del perfil
├── AGENT.md                   Método de investigación del especialista
├── workflow.toml              Tareas, preguntas, fuentes iniciales y salidas admitidas
├── initial-sources.toml       Grupos de fuentes y límites de la selección inicial
├── tasks/
│   └── <tarea>.md             Comprobaciones y criterios de cierre
└── evals/
    └── casos.toml             Casos de prueba con proveedor simulado
```

El catálogo actual conserva la autoridad sobre el texto y la asignación de Q01–Q40. Cada tarea declara los IDs que cubre. Core incorpora el texto vigente y valida al cargar que cada pregunta del especialista tenga una sola tarea, que las dependencias sean válidas y que los recursos estén empaquetados. `models.json` conserva los límites efectivos. Los criterios de investigación se quedan en la carpeta de cada agente.

## Reparto aprobado

Una tarea puede resolver varias preguntas con la misma cadena de evidencia. Se divide cuando cambian las fuentes necesarias o cuando conviene guardar un cierre independiente.

Las diez tareas se asignan a los siete personajes actuales. Dividir la investigación de Arun en dos tareas es un cambio dentro de su perfil. Una futura división en dos especialistas con identidad propia requeriría aprobar también el alta en la interfaz, con personaje, puesto en la oficina, descripción y estados de actividad.

| Perfil | Tareas y preguntas | Primera evidencia que conviene buscar |
| --- | --- | --- |
| Inventario | Stack e integraciones · Q04–Q06 | Manifiestos de raíz y aplicaciones. Seguir un proveedor declarado hasta su cliente y consumidor. |
| Arquitectura | Componentes y conexiones · Q07–Q09 | Entradas ejecutables y dependencias entre aplicaciones. Seguir una petición o import hasta su componente de destino. |
| Datos | Persistencia y caché · Q10–Q12. Recuperación y retención · Q13–Q14. | Cliente y esquema, escrituras, montajes y políticas. Para copias, localizar la configuración o el procedimiento de restauración. |
| DevOps | Construcción, arranque y contenedores · Q15–Q17. CI/CD, persistencia operativa y despliegue · Q18–Q22. | Scripts reales, Dockerfiles y Compose. Buscar pipelines y plantillas por ruta o inventario aunque el grafo tenga poca cobertura de configuración. |
| Identidad | Autenticación, autorización y sesiones · Q23–Q27 | Entrada de login y sesión, comprobación de identidad, operación sensible y límites. |
| Seguridad frontend | Navegador, XSS, secretos y consentimiento · Q28–Q31 | Seguir datos editables hasta el renderizado. Leer la CSP aplicada, saneamiento, escape y código de consentimiento. |
| Seguridad backend | Controles de servidor · Q32–Q34. Recursos, secretos y datos salientes · Q35–Q37. | Seguir entrada, validación, operación y destino. Para CV, leer el origen del veredicto y sus consumidores de correo y OneDrive. |

Akira conserva el reparto y la síntesis Q01–Q03 y Q38–Q40. Cada especialista decide qué buscar y cuándo cerrar dentro de su encargo. Core conserva el orden de ejecución actual y permite consultar hechos ya publicados de otro perfil por ID de pregunta, con sus ubicaciones. Por ejemplo, DevOps puede recuperar las fuentes de Datos sobre volúmenes y completar sus propias comprobaciones de despliegue. Una aportación previa puede orientar una búsqueda y el especialista puede recuperar el tramo original antes de citarlo.

## Ejecutor común y respuestas acotadas

Reutilizar el bucle de Iris para cargar tareas, recibir resultados junto con consultas, resolver citas y guardar el avance. Separar de ese bucle la síntesis particular de Iris, el catálogo del perfil y la composición final. Cada tarea recibe sus preguntas, el objetivo, las fuentes iniciales pertinentes, el resultado de sus últimas consultas y los pendientes aún abiertos. Las lecturas anteriores siguen disponibles por referencia.

Una respuesta empieza por la conclusión, da el hecho comprobado y enlaza el tramo mínimo que lo respalda. Como guía inicial, usar de una a tres citas por afirmación y añadir más cuando el flujo cruce varias operaciones. Un hallazgo de seguridad explicita entrada, operación afectada, defensa observada, condición e impacto. Si faltó evidencia, especifica qué lectura o comprobación quedó abierta. Core valida IDs, estados, pertenencia de las citas a la captura y campos admitidos. Las respuestas originales siguen disponibles para trazabilidad y el informe conserva el formato actual.

Si falla una llamada o se agota el presupuesto, se conservan las aportaciones validadas y cada tarea indica su estado. El registro de ejecución distingue llamadas nuevas, intentos fallidos y respuestas recuperadas, cuando las haya. Un cierre técnico puede producir un informe parcial.

### Presupuesto aprobado para el piloto

Una ronda empieza cuando el especialista pide evidencia adicional y termina con una nueva llamada que incorpora el resultado. Puede agrupar hasta cuatro consultas. La primera llamada de cada tarea ya incluye fuentes iniciales. Contamos archivos distintos efectivamente leídos por agente, incluidos esos archivos iniciales. Leer otro tramo del mismo archivo consume contexto y puede ocupar una consulta. Las cifras de archivos son objetivos orientativos para un monorepo como Web Corporativa 2.0 y se ajustan a la estructura encontrada.

| Agente | Llamadas base | Rondas adicionales | Archivos distintos orientativos | Secuencia de lectura |
| --- | ---: | ---: | ---: | --- |
| Inventario | 1 | 2 | 6–10 | Confirmar stack con los manifiestos. Seguir el registro de proveedores hasta clientes y consumidores relevantes. |
| Arquitectura | 1 | 2 | 5–9 | Localizar entradas y fronteras de componentes. Seguir una petición o import hasta el destino. |
| Datos | 2 | 2 (1 por tarea) | 6–12 | Seguir persistencia y caché hasta configuración y escritura. Localizar respaldo, restauración o purga para el segundo bloque. |
| DevOps | 2 | 3 (1 para Q15–Q17 y 2 para Q18–Q22) | 8–14 | Contrastar scripts, Dockerfiles y Compose. Localizar etapas de CI/CD y seguir los pasos delegados o completar su configuración en la segunda ronda del bloque. |
| Identidad | 1 | 2 | 6–10 | Seguir login y sesión. Verificar la autorización en una operación y los límites en sus implementaciones. |
| Seguridad frontend | 1 | 2 | 7–12 | Identificar entradas y renderizado. Leer los consumidores y las defensas efectivas, incluidas CSP y escape, y buscar consentimiento. |
| Seguridad backend | 2 | 4 (2 por tarea) | 10–16 | Una ronda para identificar las entradas y otra para llegar a la operación y sus defensas. En datos salientes, localizar la decisión y después comprobar los consumidores y su configuración. |

El reparto suma **10 llamadas base + 17 rondas + hasta 2 llamadas de Akira + 2 rondas de reserva común = 31 llamadas**. Son máximos aprobados para empezar. La reserva queda disponible para comprobaciones concretas que puedan cerrar una conclusión, por ejemplo, localizar la CSP aplicada o seguir el veredicto de un CV hasta un segundo consumidor. Core reserva primero las llamadas base de tareas pendientes y respeta los topes globales de tiempo, salida y contexto. Cada tarea cierra en cuanto tenga evidencia suficiente.

Los siete especialistas comparten un **máximo de 300 segundos por agente**, que abarca sus tareas, llamadas y búsquedas locales. Core protege **90 segundos para cerrar** con la evidencia disponible y guarda un margen equivalente para cada tarea pendiente del mismo agente. Una llamada de exploración solo se ofrece cuando caben al menos 90 segundos de búsqueda y 90 de cierre. El margen se libera al terminar cada tarea. El siguiente especialista puede empezar en cuanto finaliza el anterior.

El adaptador de `openai-codex` aplica por defecto **90 segundos de inactividad entre eventos** y permite ajustar ese valor con `HERMES_CODEX_EVENT_STALE_TIMEOUT_SECONDS`. Hermes conserva sus límites técnicos por llamada de 180 segundos en el runtime y 240 segundos en el subproceso. Si una llamada alcanza el plazo local del especialista, Core guarda las respuestas validadas, registra el resultado y consumo remotos como desconocidos y sigue con el equipo sin reintentar esa llamada. Un fallo de proveedor conserva la interrupción global.

La oficina dispone de **45 minutos** por ejecución para incluir hasta 35 minutos de especialistas, hasta 2 de Akira y margen para preparación y publicación. Se configura con `AUDIT_JOB_TIMEOUT_SECONDS`. En la siguiente prueba completa se medirán duración por especialista, rondas aprovechadas, tokens y preguntas pendientes para decidir si conviene reducir el presupuesto de búsqueda.

Tras el piloto, revisar por agente las rondas asignadas y usadas, los archivos y tramos distintos, los tokens por llamada y qué cita, defensa o conclusión añadió cada ronda. Si sobran rondas de forma consistente, se puede reducir el máximo. Si los tokens suben por repetir fuentes, ajustar primero los fragmentos y su reenvío. Si una ronda adicional cierra una comprobación relevante, mantenerla aunque consuma el máximo previsto. Los cambios se contrastarán con la cobertura y la calidad de las citas.

**Ejemplo de Kwame.** Con manifiestos y Compose como orientación, la primera búsqueda reúne los Dockerfiles y el script de arranque delegado. La tarea de despliegue localiza el pipeline y lee qué construye, comprueba o publica. Si el pipeline delega una migración en una plantilla, la tercera ronda busca esa plantilla y el comando efectivo. El objetivo es poder explicar el recorrido, citando las piezas que lo acreditan.

## Cómo aprovechar Graphify

Graphify ya orienta las búsquedas por ruta y símbolo. Core puede mejorar el resultado de esa consulta con un índice local del grafo ya preparado. Cada tarea partiría de una ruta exacta o símbolo y recibiría un tramo del código y unas pocas relaciones pertinentes para elegir el siguiente paso. Se reutiliza la misma preparación por captura para todos los agentes.

1. Dar prioridad a la definición y a un consumidor en un archivo distinto. Presentar la ruta, la línea y el tipo de relación. Ampliar a vecinos de un salto cuando la tarea necesite seguir la operación y haya presupuesto.
2. Confirmar cada afirmación en el texto de la captura. Si el grafo aporta una relación sin ubicación útil, buscar el símbolo en texto. Usar inventario y rutas exactas para YAML, configuración y otros archivos con cobertura limitada.
3. Desduplicar por ruta y rango. Para cada nueva llamada, enviar los tramos necesarios para resolver la consulta y un índice breve de referencias disponibles. Recuperar un tramo ya citado cuando sea necesario para confirmar el resultado o para la síntesis.

**Ejemplo para Arun.** Buscar `cvScanVerdict` y traer la función y sus consumidores. Leer la rama que devuelve `clean` cuando el análisis está desactivado. Después confirmar los dos puntos que aceptan ese estado, uno en correo y otro en OneDrive, y comprobar el valor declarado en la configuración de producción. Así se puede distinguir el riesgo condicionado de una exposición efectiva.

**Ejemplo para Kwame.** Partir del comando `build` en los manifiestos, seguir el script delegado y localizar Dockerfiles y pipelines por inventario. Si el pipeline queda fuera de la captura o exige verificar un servicio externo, cerrar Q18 con ese pendiente concreto.

## Política aprobada de IA privada y credenciales

La restricción de uso es un **entorno de IA privado autorizado para código del proyecto**. La primera ejecución debe pedir una confirmación explícita al operador antes de enviar el primer prompt. Texto propuesto: «¿Estás usando un entorno de IA privado autorizado para el código de este proyecto?». Si se indica un servicio gratuito, se rechaza la confirmación o queda sin respuesta, se detiene el inicio y se explica el requisito. Core controla este paso en la entrada a la ejecución. La confirmación es una declaración del operador y permite documentar la decisión. La autorización se refiere a la cuenta y al entorno concretos.

Proteger **el valor de la credencial en la copia que sale hacia el modelo**. La captura original se usa localmente para Graphify, los escáneres y la resolución de citas. Core prepara la copia de salida y sustituye solo el tramo sensible. Por ejemplo, el especialista puede leer `DATABASE_URL = "<valor protegido>"`, seguir qué componente la consume y comprobar si se toma del entorno, está incrustada o podría llegar al navegador. El nombre, la asignación, las ramas, las llamadas y los números de línea se conservan. Las citas mostradas al usuario usan la misma protección cuando incluyen ese tramo.

1. **Detectar localmente.** Combinar ubicaciones de Gitleaks con patrones específicos para tokens, claves privadas y credenciales en URLs. Conservar ruta, línea y tipo. Revisar en local candidatos ambiguos como IDs de roles, alfabetos, hashes y valores de ejemplo. Si se confirma que un candidato es público, acotar la excepción al tramo y versión verificados.
2. **Aplicar en el punto de salida.** Ejecutar las búsquedas por ruta, texto y símbolo, la selección de fragmentos y el análisis del grafo sobre la captura original. Justo antes de enviar el prompt, proteger el valor en los fragmentos, las citas recuperadas, los resultados de herramientas y las aportaciones previas. Si el caso depende del literal protegido, registrar la propiedad comprobable localmente y marcar como pendiente la conclusión que requiera revisar ese valor. La detección puede omitir valores y se validará con ejemplos representativos.
3. **Comprobar que el análisis conserva su calidad.** Probar primero con secretos ficticios y casos no secretos. Verificar que el modelo recibe suficiente contexto para distinguir una credencial incrustada de una variable de entorno o un identificador público, que las citas conservan su línea y que el valor ficticio queda fuera del prompt y del informe. Medir falsos positivos y afirmaciones que quedaron sin respaldo por la protección.

En la ejecución del plan, **Seguridad** aporta casos de detección y excepciones, **Backend/Core** implementa la confirmación y el control de salida y **Operaciones** identifica el entorno privado para el piloto.

## Implementación y aceptación

1. **Extraer el ejecutor y validar el estándar.** Probar con proveedor simulado que Iris conserva sus resultados y que un especialista puede cerrar con evidencia, agotar rondas o publicar un parcial. Verificar rechazo de citas inventadas, recuperación de referencias y búsqueda literal cuando el grafo carezca de cobertura. Probar también que una primera ejecución sin confirmación se detiene antes de invocar al modelo y que proteger valores en la salida conserva los resultados de búsqueda y la ubicación de las citas.
2. **Pilotar DevOps y Seguridad backend.** Kwame comprueba que el flujo llega a configuración y CI/CD, donde manda el inventario. Arun comprueba que la recuperación orientada por símbolos permite seguir una cadena de llamadas. Mantener los demás perfiles en el recorrido actual durante el piloto y revisar la evidencia antes de migrarlos.
3. **Migrar los otros cinco perfiles y comparar el equipo completo.** Usar como referencia principal el equipo `2b105836-e626-42db-9742-6ff55491a2b1` y como referencia complementaria a Iris `3a29b4d5-55f3-41e3-97d7-d14d80fb3cdf`. Fijar captura, modelo, esfuerzo, herramientas, catálogo y techo global. Documentar cualquier diferencia en las fuentes que se permita enviar al proveedor. Leer la referencia de seguridad después de la corrida. [Revisiones de referencia y archivo local](PLAN_COORDINACION_CENTRALIZADA.md#cierre-antes-de-migrar-el-equipo--11112026)

Para aceptar la migración, verificar las 40 preguntas únicas y su autoría en HTML y Markdown, la conservación de parciales y la correspondencia de las citas con la captura. En los casos de referencia, revisar si las citas sostienen la afirmación y si la respuesta incluye defensas y condiciones. Comparar también estados por pregunta, llamadas, tokens, tiempo, bytes de prompt y líneas de prompt reenviadas. Instrumentar por separado los bytes de fuente repetidos y los hallazgos confirmados gracias a una pista del grafo. El ahorro de contexto cuenta como mejora cuando se conserva la evidencia de los casos principales.

El piloto empieza con tres rondas para Kwame y cuatro para Arun. Las pruebas simuladas de confirmación y protección de credenciales preceden a cualquier envío real de código.

## Activación y verificación

El ejecutor común está en `coordination/workflow.py`. La oficina mantiene sus siete especialistas y permite seguir usando Iris. En modo híbrido, `AUDIT_TASK_WORKFLOWS=pilot` activa los flujos de Kwame y Arun. `all` prepara la comparación del equipo completo una vez revisado el piloto y `legacy` permite reproducir el ejecutor anterior.

Las métricas de tareas distinguen texto de fuente enviado y repetido. El recuento de observaciones que citan líneas sugeridas por Graphify permite identificar casos para revisión manual. La coincidencia entre una cita y una ubicación del grafo permite comprobar la relación con la fuente. La utilidad de la sugerencia se evalúa leyendo el caso.

La validación local del 12/11/2026 comprobó los dos perfiles del piloto, el modo de siete especialistas con proveedor simulado, la persistencia de parciales de Iris, los IDs y citas de las 40 preguntas en HTML y Markdown y la protección de valores en el envío. La oficina se verificó con pruebas de interfaz y TypeScript. La corrida de piloto con el proveedor autorizado y la comparación completa son las siguientes comprobaciones de cobertura y consumo.

### Resultado del piloto real · 12/11/2026

La revisión `97c39807-ee5e-4c80-a19e-ae2caf00f410` ejecutó las cuatro tareas de Kwame y Arun con GPT‑6.1 Sol, esfuerzo medio y `openai-codex`. Las 11 respuestas fueron nuevas y las 14 preguntas de su alcance tienen citas. Q17 pasó a respondida y Q18 a parcial. Arun acreditó el envío de CV por correo con antimalware desactivado y el riesgo de CV huérfanos. Quedaron abiertas la cadena completa de OneDrive, la clasificación de las alertas de Gitleaks y las etapas posteriores de CI/CD.

Los dos roles consumieron 156.564 tokens, frente a 179.364 en sus aportaciones del equipo anterior. Aumentaron de 6 a 11 llamadas. La revisión conservó Q01–Q40 en los dos formatos y marcó el alcance del piloto. Se corrigieron y probaron localmente dos defectos de presentación detectados en el informe real. La comparación del equipo completo queda pendiente. [Resultado, citas y métricas del piloto](../artifacts/central-coordination/independent-pilot-comparacion.md)

### Ajustes posteriores al piloto

Kwame conserva tres rondas. La de construcción y arranque agrupa las lecturas pendientes de scripts y Dockerfiles. CI/CD y despliegue recibe dos rondas para localizar las etapas del pipeline y seguir las plantillas, scripts o tramos posteriores. La selección inicial prioriza el pipeline y sus posibles plantillas.

Arun conserva dos rondas en cada tarea. Para Q35–Q37, la selección inicial intenta entregar en el mismo bloque las líneas de la decisión antimalware y las dos ramas consumidoras. La guía pide reunirlas en una misma ronda si hace falta ampliar la evidencia y guardar sus citas antes de pasar a la configuración y al comportamiento ante fallos.

### Prueba completa del equipo por tareas · 12/11/2026

El informe final `8f98bdeb-989a-4575-8e01-a704fd059211` completó las diez tareas, el reparto y la síntesis. Se recuperaron por huella 22 respuestas de `bf2cd177-50ba-4981-9e16-1696d32ec00f` después de un límite local de tiempo y se completaron siete llamadas nuevas. Hubo 30 intentos dentro del techo de 31 y el consumo remoto de uno quedó sin confirmar. El HTML y el Markdown contienen las 40 preguntas únicas.

Se comunicaron 392.440 tokens, un 38,7 % menos que el equipo anterior. Los bytes de líneas de prompt repetidas bajaron un 31,5 %. El tiempo combinado de coordinación y análisis fue 1.183,388 s. El informe quedó parcial, con una pregunta respondida, 37 parciales y dos sin comprobar. Mejoraron Docker y CI/CD. Se acreditó la condición del antimalware para correo y OneDrive. Quedaron sin recoger el CV huérfano y la CSP específica de la web pública. La comparación recoge los pendientes de Arquitectura, la pérdida de evidencia entre observaciones y respuestas y los ajustes propuestos antes de activar los siete flujos por defecto. [Informes, comparación y métricas](../artifacts/central-coordination/independent-full-comparacion.md)

### Repetición del equipo con el plazo común · 12/11/2026

La revisión `6014f7ea-0ee2-4204-a3f7-d55d6186da16` repitió la captura de Web Corporativa 2.0 en `develop@4ae82b4` con GPT‑6.1 Sol, esfuerzo medio y `openai-codex`. Se verificó el código del workspace y el perfil efectivo de 300 segundos con margen de cierre de 90 para los siete especialistas. Cerraron las diez tareas, el reparto y la síntesis de Akira. Se completaron 28 llamadas nuevas, con cero interrupciones y cero respuestas recuperadas. Arun cerró sus dos tareas en cinco llamadas y 175,65 segundos acumulados de modelo.

Se verificaron las 40 preguntas únicas en HTML, Markdown y JSON. El informe quedó parcial, con una respondida, 37 parciales y dos sin comprobar. Registró 383.555 tokens y 905,545 segundos de coordinación y análisis. De 6.068 referencias de preguntas, 6.040 coinciden textualmente y 28 conservan ruta y línea con un valor protegido. Quedaron abiertos la atomicidad del login, la clasificación de Gitleaks y el consumidor de CV de OneDrive. La corrida valida el cierre operativo con el plazo común. El modo `all` sigue disponible para pruebas de cobertura. [Informe HTML](../reports/2026-11-12/140000-snapshot/6014f7ea-0ee2-4204-a3f7-d55d6186da16/informe.html) · [Informe Markdown](../reports/2026-11-12/140000-snapshot/6014f7ea-0ee2-4204-a3f7-d55d6186da16/informe.md) · [Comparación y métricas](../artifacts/central-coordination/equipo-300s-comparacion.json)
