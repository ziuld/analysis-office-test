# Coordinación y recuperación compartida — 0.3.0

El recorrido híbrido prepara un snapshot íntegro y mapas/scanners deterministas. El coordinador recibe contexto común acotado y da tres objetivos en una llamada; no selecciona archivos ni omite especialidades. Cada especialista elige fuentes del mismo snapshot/grafo. El índice del prompt puede ser parcial; la búsqueda local dispone del conjunto completo compatible.

```dotenv
AUDIT_SECURITY_RESEARCH_ROUNDS=1
AUDIT_ARCHITECTURE_RESEARCH_ROUNDS=1
AUDIT_INVENTORY_RESEARCH_ROUNDS=1
```

Rango 0–2: cero genera un informe sin lecturas de código y con carencias explícitas; uno exige una ronda inicial de consultas y después el informe; dos permite una segunda ronda opcional. Cada ronda admite 1–4 consultas, cada una hasta tres fragmentos de 100 líneas/6000 bytes, símbolos y relaciones. Se conservan topes acumulados de archivos/bytes por rol: Seguridad 12/64000, Arquitectura e Inventario 6/24000. El padding de posiciones originales también cuenta; un fragmento con padding no puede superar 12000 bytes. Si una lectura nueva no cabe, se registra la omisión y se conserva la evidencia anterior.

La skill compartida explica `{"queries":[{"query":"símbolo o texto","paths":["ruta exacta"],"start_line":1}]}`. Los campos son opcionales, pero hacen falta query o paths. El Core valida rutas y opera únicamente sobre evidencia ocultada de esta revisión: sin shell, red ni ejecución del objetivo. Consulta insegura/ausente y omisión por presupuesto quedan trazadas. Los antiguos `MAX_EXTRA_QUERIES` no controlan este recorrido.

Con una ronda por rol, hasta ocho llamadas: orquestación + tres investigaciones + tres análisis + síntesis. Con dos, hasta once; con cero, hasta cinco sin código para los especialistas. No hay reintentos automáticos ni subida de modelo. Los roles trabajan consecutivamente y no se pasan conclusiones entre sí. Las preguntas posteriores son independientes.

Los campos `calls`, `invocations`, `retrievals`, `execution` y `coverage` registran uso y carencias. Las citas se contrastan con lo realmente suministrado; un hallazgo inválido no elimina otros válidos. La síntesis utiliza únicamente aportaciones validadas y conserva certeza, condiciones, acciones y pendientes. Validar citas no prueba corrección semántica. Base funcional aceptada en Fase 1; mejoras propuestas en [Fase 2](PLAN_FASE_2.md).

Los apartados siguientes describen la configuración común y el reparto legacy sin evidencia compartida.

## Registro anterior (Bloques 5 y 7; contratos anteriores conservados para compatibilidad)

# Coordinador, perfiles y skills — Bloque 5

La revisión conserva las tres células de una pasada. El coordinador puede añadir un reparto inicial y una síntesis final con IA, sin búsqueda, herramientas de agente, reintentos ni ampliación de evidencia. Se activa expresamente para controlar el consumo; la configuración predeterminada continúa siendo determinista.

## Encargo y consumo

En el `.env` local, sin sustituir su contenido ni credenciales:

```dotenv
AUDIT_COORDINATION_MODE=deterministic
AUDIT_CAPABILITIES=
```

`AUDIT_COORDINATION_MODE=ai` habilita hasta **dos llamadas adicionales**, una por reparto y otra por síntesis. Un contexto sin archivos o sin aportaciones válidas omite la llamada correspondiente. No se ejecutan ambos coordinadores: el reparto y la consolidación deterministas sirven como base de conservación y recuperación ante error, sin consumir modelo.

`AUDIT_CAPABILITIES=azure` solicita la propuesta Azure a Arquitectura. Vacío la omite; esta ausencia no vuelve parcial una evaluación que no la necesita. Si se solicita y falta o resulta inválida, se conserva el núcleo válido y se registra la limitación, como antes. Solo se admite actualmente esa capacidad opcional. Los informes históricos y sus propuestas siguen disponibles independientemente del encargo actual.

Para que los servicios lean cambios de `.env`, recrearlos sin trabajos activos, utilizando los mismos archivos Compose con los que se arrancaron. El modo de preparación `legacy`/`hybrid` es independiente:

| Recorrido | Máximo de llamadas de revisión |
|---|---|
| Preparación legacy + coordinación determinista | 3 células |
| Preparación legacy + coordinación IA | 3 células + 2 del coordinador |
| Preparación híbrida + coordinación IA | Hasta 2 del explorador por defecto (1 + loops) + 3 células + 2 del coordinador |

Cada pregunta posterior sigue siendo una llamada independiente. Ninguna de estas llamadas se inicia por construir imágenes o arrancar servicios. Las comprobaciones de este bloque emplearon respuestas ficticias; no se consumió modelo del proyecto para validarlo.

## Perfiles y validación

La fuente de perfiles y límites locales es [models.json](../backend/src/arktic_office/resources/profiles/models.json). El adaptador de configuración la aplica a preparación, coordinador, especialistas y consultas. El perfil de pruebas usa el modelo mínimo ya configurado de cada proveedor (`gpt-6-luna` en Codex OAuth, `gpt-5.4-mini` en API) y razonamiento `low`, sin elevaciones por célula en `.env.example`. Los overrides explícitos siguen disponibles. No hay cambios automáticos de modelo o proveedor.

| Rol | Límites predeterminados relevantes |
|---|---|
| Seguridad | 12 archivos, 64000 bytes, una llamada, 240 s, salida solicitada hasta 4500 tokens |
| Arquitectura / Inventario | 6 archivos, 24000 bytes, una llamada cada uno, 240 s, salida solicitada hasta 4500 tokens |
| Coordinador | Dos llamadas como máximo; cada una hasta 32000 bytes de prompt, 16000 bytes de respuesta, 60 s, salida solicitada hasta 2000 tokens |
| Preparación | 1 pasada inicial + `AUDIT_PREPARATION_MAX_LOOPS` adicionales (1 por defecto), 180 s, 60000 bytes acumulados; 60 s por llamada, salida solicitada hasta 1500 tokens |
| Consulta al coordinador | Una llamada, 240 s; hereda el modelo común, salida solicitada hasta 4500 tokens |

`AUDIT_MODEL`, `AUDIT_REASONING` y `AUDIT_MAX_OUTPUT_TOKENS` siguen siendo la base. Los prefijos `AUDIT_SECURITY_`, `AUDIT_ARCHITECTURE_`, `AUDIT_INVENTORY_`, `AUDIT_COORDINATOR_`, `AUDIT_PREPARATION_` y `AUDIT_QUESTION_` permiten ajustar `MODEL`, `REASONING` y `MAX_OUTPUT_TOKENS`. Los límites locales de archivos, tiempo y contexto están en el registro. La consulta a un especialista mantiene su perfil propio; `QUESTION` corresponde a la consulta al coordinador. Los ajustes explícitos de salida admiten 1000–8000 tokens; el valor predeterminado de cada rol limita el valor común heredado.

Se valida toda la configuración antes de la adquisición/exploración o de la primera llamada del equipo: proveedor, sintaxis del modelo, razonamiento, salida, modo y capacidades. Esta validación es local: no demuestra disponibilidad del modelo, cuota, soporte de razonamiento ni compatibilidad del proveedor. El runtime recibe el proveedor, modelo, razonamiento y salida efectivos del perfil. El backend Codex OAuth fijado sigue sin garantizar un techo duro de tokens de salida; llamadas, bytes y tiempo tampoco equivalen a un presupuesto monetario exacto. El límite global de 1500 segundos de la ejecución API continúa prevaleciendo sobre las fases.

## Reparto, síntesis y conservación

El reparto recibe inventario, roles de archivo, tamaños, focos, capacidades y presupuestos; no todo el código. Solo puede asignar rutas ya presentes en el contexto preparado, sin lockfiles, duplicados ni exceso de archivos/bytes por célula. Una respuesta inválida deja registrado el fallo y utiliza el reparto determinista. Nunca relanza la preparación ni pide más archivos a un especialista.

Cada especialista recibe sus fragmentos una vez. Sus citas se contrastan con el texto seleccionado y se conserva su resultado original en `celulas/`. La consolidación estructural anterior continúa conservando procedencia y discrepancias.

La síntesis recibe exclusivamente aportaciones validadas y sus fuentes. Devuelve hasta cinco textos con identificadores de esas aportaciones. El Core rechaza identificadores inventados y vuelve a comprobar las citas; hereda las fuentes y mantiene la etiqueta de indicio si participa alguna aportación incierta. No crea hallazgos ni sustituye los originales. El texto es una interpretación del modelo: validar citas no demuestra fidelidad semántica ni resuelve contradicciones. La síntesis aparece identificada en los anexos HTML y Markdown y queda disponible para la consulta al coordinador.

`coordinacion.json` guarda perfiles, etapas, llamadas intentadas, bytes de entrada, consumo comunicado, resultados y fallos. La información de síntesis y coordinación también queda en `informe.json`; el encargo y los perfiles efectivos quedan en `evidencia.json`. Un consumo no comunicado permanece `null`. Un error del coordinador conserva la base y las aportaciones válidas, deja parcial un equipo que de otro modo fuese completo y no dispara reintentos.

## Instrucciones reutilizables

El paquete incluye [arktic-review/SKILL.md](../backend/src/arktic_office/resources/skills/arktic-review/SKILL.md), instrucciones por rol en [agents.json](../backend/src/arktic_office/resources/profiles/agents.json), el [contrato de informe](../backend/src/arktic_office/resources/profiles/report-contract.md) y la [petición común](../backend/src/arktic_office/resources/profiles/review-request.md). Se reutilizan los perfiles de Seguridad/Azure y el estándar editorial canónico sin duplicarlo ni modificarlo. El prompt omite el párrafo editorial de Azure cuando no corresponde al encargo; no reescribe el estándar ni los informes guardados.

La skill declara entradas, salida, herramientas y restricciones. Se carga explícitamente desde los recursos instalados; no habilita herramientas o descubrimiento implícito de Hermes. Para portarla hay que conservar sus referencias, aportar el estándar/esquema vigente y adaptar el anfitrión para imponer permisos, presupuestos y validación. El formato `SKILL.md` no garantiza por sí solo compatibilidad con Codex, Hermes u otros productos. No se instala en la configuración personal del usuario ni se añade un gestor de skills.

## Comprobaciones y límites

Se reutiliza la suite manual y se añaden solo tres casos necesarios: configuración inválida sin llamadas; reparto y síntesis válidos con conservación de originales y Azure omitido; fallos de coordinador/especialista sin reintentos ni pérdida de aportaciones válidas. Los fixtures previos que necesitan Azure lo solicitan expresamente. El runner bloquea procesos externos y conexiones no locales; el contenedor no tiene red ni credenciales. Resultado: 116 ejecutadas, 115 correctas y 1 referencia visual opcional omitida en 6,582 segundos. La skill pasó el validador de formato local.

Se construyeron imágenes y se reutilizó el comprobador de arranque existente: API 0.2.0 y oficina saludables, oficina/proxy HTTP 200, sin trabajos, autenticación ni revisiones. El proyecto y sus volúmenes temporales se retiraron. Logs locales: `artifacts/block5-tests-final.log` y `artifacts/block5-startup.log`.

No se ejecutaron análisis de repositorios reales, scanners ni modelos del proyecto. No se evaluaron calidad semántica del reparto/síntesis reales, consumo del proveedor, disponibilidad de modelos, carga concurrente ni recuperación de una llamada interrumpida. La prueba valida contratos y conservación con respuestas deterministas, no esas propiedades. CI/CD conserva su base sin ampliaciones; frontend/backend permanecen en 0.2.0, sin cierre de entrega.

El límite de loops corresponde a la exploración híbrida; véase [PREPARACION.md](PREPARACION.md). No multiplica especialistas ni reparto/síntesis. El Bloque 9 separa la calibración posterior de modelos de estas pruebas funcionales.

## Verificación funcional real posterior — 24/10/2026

El reparto recibe ahora la selección base de cada célula y no puede vaciar una célula con evidencia disponible. Un reparto vacío inválido conserva la base determinista, deja constancia del fallo y permite que el especialista evalúe su propia suficiencia. Cada célula registra `calls` para distinguir una invocación real de una etapa sin entrada.

La prueba final real de bookingApi ejecutó siete llamadas de `gpt-6-luna`/`low`: dos de exploración, reparto, tres especialistas y síntesis. Especialistas y coordinación válidos, cero etapas de modelos omitidas; 40020 tokens comunicados y unos 105 s. El informe es parcial por el límite de preparación, no por errores de especialistas. Gitleaks activo sin detecciones; OSV sin entrada compatible, dependencias no evaluadas. Resultados, intentos anteriores y límites en el [plan](PLAN_FASE_1.md) y la [evidencia final](evidence/full-pilot-final-2026-10-24.json). Esto valida el recorrido funcional de esta muestra, sin cerrar la calibración del Bloque 9.

## Instrucciones por especialidad — Fase 2

El foco y checklist de cada uno de los tres especialistas actuales se definen en `resources/profiles/agents.json`; `resources/profiles/agent-common.md` fija las reglas comunes. El constructor compartido `reporting/agent_instructions.py` entrega ese mismo brief antes de elegir fuentes y durante el análisis. No es una skill nueva ni depende de cargar SOUL o personalidades del gateway Hermes. El coordinador recibe las reglas comunes y sus propios límites de orquestación/síntesis. Los esquemas JSON siguen dependiendo de cada etapa.

Inventario identifica motores o archivos y perfiles declarados; Arquitectura explica uso, conexiones y ubicación configurable; Seguridad revisa acceso y exposición. Una dependencia de base de datos no prueba uso, una ruta/URL no prueba el despliegue efectivo y un volumen no acredita backup. La investigación dirige `query` al símbolo/texto y `paths` al archivo, agrupa fuentes y reserva configuración relevante sin cambiar caps. Nuevos roles DevOps/Privacidad siguen como propuesta en el plan de Fase 2.
