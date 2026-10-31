# Coordinación y recuperación compartida — 0.3.0

## Funcionamiento actual · coordinación centralizada

La implementación vigente sigue exclusivamente [PLAN_COORDINACION_CENTRALIZADA.md](PLAN_COORDINACION_CENTRALIZADA.md). Akira reparte y sintetiza; Inventario, Arquitectura, Datos, Seguridad, Seguridad frontend, Seguridad backend y Devops ejecutan en ese orden. Core publica aportaciones validadas en SQLite y archivos y entrega contexto anterior selectivo, sin conversación adicional entre modelos. Las consultas se encolan; no hay dos tareas de modelo simultáneas.

Se mantienen Q01–Q40 y sus textos. La configuración efectiva aplica hasta tres rondas de consultas por especialista, salvo cuatro para Seguridad backend, más la respuesta final de cada uno. El límite global es de 31 llamadas contando las dos de Akira. La salida reservada máxima conserva el techo anterior; contexto y tiempo también tienen límites globales. No se cambian modelos ni se amplían presupuestos automáticamente. Credenciales, conexión de resultado remoto desconocido o presupuesto agotado detienen nuevas llamadas; un fallo local bloquea solo dependencias necesarias y conserva resultados válidos.

La base vive en `/reports/.knowledge/office.sqlite`, junto al montaje persistente de informes y caché. No se añade Redis. Los resultados comprobados, incluidos los pendientes solicitados, figuran en [RESULTADOS_COORDINACION_2026-10-30.md](RESULTADOS_COORDINACION_2026-10-30.md).

## Histórico de los recorridos anteriores

Las notas siguientes documentan fases y configuraciones anteriores. Sus cifras de agentes, límites y modelos no describen la configuración vigente ni añaden trabajo al plan único.

El recorrido híbrido prepara un snapshot íntegro y mapas/scanners deterministas. El coordinador recibe contexto común acotado y da tres objetivos en una llamada; no selecciona archivos ni omite especialidades. Cada especialista elige fuentes del mismo snapshot/grafo. El índice del prompt puede ser parcial; la búsqueda local dispone del conjunto completo compatible.

```dotenv
AUDIT_SECURITY_RESEARCH_ROUNDS=1
AUDIT_ARCHITECTURE_RESEARCH_ROUNDS=1
AUDIT_INVENTORY_RESEARCH_ROUNDS=1
```

Rango 0–2: cero genera un informe sin lecturas de código y con carencias explícitas; uno exige una ronda inicial de consultas y después el informe; dos permite una segunda ronda opcional. Cada ronda admite 1–4 consultas, cada una hasta tres fragmentos de 100 líneas/6000 bytes, símbolos y relaciones. Se conservan topes acumulados de archivos/bytes por rol: Seguridad 12/64000, Arquitectura e Inventario 6/24000. El padding de posiciones originales también cuenta; un fragmento con padding no puede superar 12000 bytes. Si una lectura nueva no cabe, se registra la omisión y se conserva la evidencia anterior.

La skill compartida explica `{"queries":[{"query":"símbolo o texto","paths":["ruta exacta"],"start_line":1}]}`. Los campos son opcionales, pero hacen falta query o paths. El Core valida rutas y opera únicamente sobre evidencia ocultada de esta revisión: sin shell, red ni ejecución del objetivo. Consulta insegura/ausente y omisión por presupuesto quedan trazadas. Los antiguos `MAX_EXTRA_QUERIES` no controlan este recorrido.

Con una ronda por rol, hasta ocho llamadas: orquestación + tres investigaciones + tres análisis + síntesis. Con dos, hasta once; con cero, hasta cinco sin código para los especialistas. No hay reintentos automáticos ni subida de modelo. Los roles trabajan consecutivamente y no se pasan conclusiones entre sí. Las preguntas posteriores son independientes.

Los campos `calls`, `invocations`, `retrievals`, `execution` y `coverage` registran uso y carencias. Las citas se contrastan con lo realmente suministrado; un hallazgo inválido no elimina otros válidos. La síntesis utiliza únicamente aportaciones validadas y conserva certeza, condiciones, acciones y pendientes. Validar citas no prueba corrección semántica. Base funcional aceptada en Fase 1; mejoras pendientes únicamente en el [plan vigente](PLAN_COORDINACION_CENTRALIZADA.md).

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

Inventario identifica motores o archivos y perfiles declarados; Arquitectura explica uso, conexiones y ubicación configurable; Seguridad revisa acceso y exposición. Una dependencia de base de datos no prueba uso, una ruta/URL no prueba el despliegue efectivo y un volumen no acredita backup. La investigación dirige `query` al símbolo/texto y `paths` al archivo, agrupa fuentes y reserva configuración relevante sin cambiar caps. El reparto futuro de especialidades se define únicamente en el [plan vigente](PLAN_COORDINACION_CENTRALIZADA.md).

## Infraestructura actual e informe útil — Parte 2

Se conserva el mecanismo de investigación y recuperación del commit c31041a, salvo los nuevos presupuestos y ventanas de lectura aprobados en la sección siguiente. Arquitectura describe y representa en presentacion.flujo_actual la infraestructura que pueda sostener con Docker/Compose, CI/CD, documentación y código. Distingue configuración declarada de ejecución efectiva y conexiones observadas de inferidas. No se exige conocer una VPN o servidor no documentado. El contrato de citas continúa sin cambios.

El informe abre con observaciones respaldadas e implicaciones, preservando fuentes y condiciones de riesgos. Las preguntas generales y alcance detallado quedan en anexos. Los ajustes experimentales de recuperación posteriores a c31041a fueron retirados tras el feedback; su prueba parcial se conserva en el plan como evidencia histórica.


## Presupuestos vigentes aprobados — 24/10/2026

| Especialista | Archivos distintos acumulados | Bytes de fuentes acumulados | Rondas máximas |
|---|---:|---:|---:|
| Seguridad | 20 | 100000 | 2 |
| Arquitectura | 12 | 60000 | 2 |
| Inventario | 8 | 32000 | 1 |

Cada ronda permite hasta cuatro consultas de hasta tres archivos; las rondas comparten el presupuesto. Una ruta releída no cuenta como archivo distinto nuevo, pero ampliar el texto consume bytes. La segunda ronda es opcional; si la primera entrega basta, el especialista devuelve el informe. Máximo tres llamadas por Seguridad/Arquitectura y dos por Inventario; con reparto/síntesis, ocho llamadas si no se usa ninguna ronda extra y diez si ambos la usan. Sin reintentos automáticos.

Fragmentos de hasta 200 líneas, conservando los límites de 6000 bytes de contenido por fragmento y 12000 bytes con padding original. Un archivo largo no se entrega entero obligatoriamente. No cambian el coordinador, modelos Luna/low, límites de salida ni la adquisición íntegra. Valores predeterminados en models.json; rondas sobrescribibles con las variables existentes. El número de archivos y bytes se mantiene definido en el registro, sin nuevas variables.

Herramientas deterministas integradas: Graphify (mapa estático, sin modelos), Gitleaks 8.30.1 (posibles secretos del snapshot, sin historial Git) y OSV-Scanner 2.7.0 (vulnerabilidades conocidas en versiones resueltas compatibles). OSV puede quedar no_evaluado sin entrada compatible; eso no es un resultado sin vulnerabilidades. Semgrep está diferido, no integrado; no hay SonarQube ni un SAST equivalente ejecutándose actualmente.


## Ampliación de scanners y lectura por símbolo — Punto 2

El catálogo determinista vigente pasa a Graphify más tres scanners: Gitleaks, OSV y Semgrep CE. La lista anterior de tres herramientas corresponde al estado previo. OSV selecciona automáticamente formatos multitecnología y SBOM; Semgrep usa únicamente las nueve reglas locales y cuatro familias de lenguajes descritas en SEGURIDAD.md. Los resultados entran al contexto común ya existente con estado, candidatos limitados y carencias; no se añaden llamadas a modelos por ejecutar scanners.

La búsqueda conserva su mecanismo anterior, con una corrección localizada: cuando el grafo ofrece la definición del símbolo en el archivo leído, se centra allí la ventana en vez de escoger la primera aparición textual (que podía ser una llamada). Se mantienen rutas, relaciones, consultas por líneas y presupuestos aprobados. Se comprobaron manejador HTTP/autorización y recuperación con llamadas anteriores a sus definiciones, conservando líneas originales. No se adopta el rediseño experimental de alcance de rutas retirado anteriormente.


## Comprobación previa al commit: agrupaciones de rutas

Un especialista puede agrupar por error más de tres rutas en una consulta. Core divide de forma determinista grupos de 4–12 rutas en consultas de hasta tres solo si toda la ronda resultante sigue dentro de cuatro consultas. La traza registra original_paths, part y parts en request_split. Si no cabe, se conserva el manejo acotado de error de la consulta original: no se omiten peticiones ni se ejecuta una quinta consulta. Continúan las validaciones de rutas y los presupuestos acumulados; no añade llamadas a modelos ni reintentos. El prompt aclara explícitamente el límite de paths y cómo repartir cinco rutas.

El contrato final aclara las fuentes obligatorias por nodo y conexión del diagrama (incluidas inferidas) y por estado operativo observado/indicio. Sin fuentes no se publica un componente ni se finge un estado comprobado. Los validadores permanecen sin relajar.


El ejemplo de Arquitectura incluye ahora una conexión completa con ambos extremos y claves exactas, validada en prueba contra presentation.validate. Se prohíben estados alternativos o campos adicionales del diagrama; no cambia el esquema admitido. Los avisos parciales generan `.respuesta-parcial.txt` ocultada y limitada, solo como diagnóstico local del rechazo; no se muestra ni reutiliza como resultado validado.


## Contrato compacto de especialistas y composición de Core — 24/10/2026

Los especialistas reciben ahora un solo contrato de salida activo, `compact-v1`, definido en `reporting/specialist.py`, junto al brief profesional común/por rol. No se concatenan el estándar editorial del informe, security-v1, report-contract, review-request, cell-output-contract y la skill legacy para pedirles que construyan el informe v3. Los contratos anteriores se conservan para compatibilidad/lectura histórica; el prompt standalone mantiene su referencia exacta.

Observación mínima: observacion, certeza observado/indicio y evidencia F#:L#. Opcionales: implicacion, condicion, recomendacion, gravedad expresamente evaluada. Seguridad aporta controles que pudo revisar; Core completa los ausentes como no_evaluado. Inventario entrega componentes directamente (nombre, función, tecnología si se conoce, fuentes), sin tema ni objeto adicional condicional. Arquitectura aporta componentes y conexiones entre sus nombres; Core genera n1/n2/... y comprueba extremos existentes. Las observaciones recogen persistencia/operación sin exigir ocho filas vacías. Azure continúa siendo una capacidad explícita y conserva su contrato opcional.

Core construye el formato 3 existente y sus metadatos editoriales. Los textos técnicos vienen del especialista; los valores de respaldo del adaptador son etiquetas genéricas de revisión, no hechos técnicos ni recomendaciones de infraestructura. No infiere gravedad, condiciones concretas, dominio técnico ni relaciones ausentes. Un riesgo con gravedad explícita sin dominio queda por_clasificar; certeza indicio nunca se convierte en observado. Cada fuente se comprueba con el índice de los fragmentos entregados y el validador de cita exacta, incluidas líneas vacías/ocultadas. Una referencia inventada rechaza su elemento, conservando los otros. Categoría/formato correcto no demuestra interpretación correcta.

Se admiten hasta doce IDs o rangos F#:L#-L# por elemento. Cada rango abarca como máximo cuarenta líneas y se expande a las líneas no vacías realmente entregadas, hasta ochenta fuentes únicas por elemento. Se rechazan rangos invertidos, fuera del fragmento o sin texto; cada fuente se contrasta individualmente. El resumen muestra tres; el detalle y los anexos conservan las adicionales, sin truncar el resultado. Observaciones de hasta 1200 caracteres y explicaciones de ese orden se conservan en el informe; el título y detalle inicial son derivados editoriales de Core. Límites de listas y tipos siguen acotados; no se incrementan rondas, archivos, modelos o presupuesto de salida. Los informes compactos incorporan un anexo de observaciones y fuentes completas. Los informes históricos conservan su presentación y referencias guardadas.

Validación: replay de las últimas respuestas rechazadas, sin red/scanners/modelos y usando únicamente las ventanas originalmente entregadas; conserva tres observaciones de Seguridad, seis de Arquitectura y cuatro de Inventario, más seis nodos y cinco conexiones de Arquitectura. La adaptación de nombres del diagrama reutiliza nombres ya emitidos, no reconstruye componentes omitidos por Inventario. Regresión de contratos/formatos/compatibilidad/Azure: sesenta pruebas ejecutadas, cincuenta y nueve correctas y una referencia visual opcional omitida; después ocho casos del adaptador correctos al añadir el límite de nombre de nodo. Pilotos de generación directa se registran en el plan.


Comprobación aislada posterior: siete llamadas Luna/low (dos casos por rol y una repetición dirigida de Seguridad). Se explicita que hallazgo exige patrón de riesgo y que una defensa visible con autorización adicional desconocida no implica defecto. El adaptador de transporte acepta únicamente un sufijo </final> después de un objeto JSON ya válido y registra format_normalization en el envelope; no busca objetos dentro de prosa ni repara JSON roto. Siete respuestas conservadas y reproducidas offline; la séptima había fallado antes de esta normalización. Treinta y una pruebas dirigidas correctas. Evidencia y limitaciones en el plan; no prueba coordinador ni recuperación de código.


## Presentación ejecutiva v14 — 24/10/2026

El renderer adopta la propuesta v14: prioridades con enlaces a un detalle por riesgo, componentes/conexiones y observaciones originales, recomendaciones opcionales y anexos. Core no pide nuevos campos a los especialistas ni genera conclusiones adicionales. Las referencias de render de las versiones de datos anteriores cambian por el diseño aprobado; sus JSON y archivos guardados no se reescriben. CSS v12 compartido conserva activos corporativos; report-v14.css aporta jerarquía responsive e impresión. El contenido técnico existe sin JavaScript; este solo facilita navegación y apertura/restauración de anexos al imprimir. Sin propuesta Azure explícita válida no se muestra una arquitectura cloud predeterminada. Los dominios sin asignar conservan sus acciones. Los controles no evaluados y los estados/detalles de cada herramienta se conservan en cobertura, sin convertirlos en aprobados.

Configuración de las próximas ejecuciones: Seguridad gpt-6-luna/medium; demás perfiles conservados. Este ajuste está en .env/.env.example, no se eleva el razonamiento global ni los presupuestos. La vista previa reutiliza respuestas low guardadas y no mide los resultados de medium.


### Síntesis compacta — 25/10/2026

El orquestador recibe aportaciones validadas por ID con su texto, certeza, gravedad, condiciones y acciones; las citas completas permanecen en Core. Al recibir aportaciones de la síntesis, Core resuelve los IDs originales, conserva todas las fuentes, revalida sus líneas y mantiene las condiciones. No se eleva el límite de 32000 bytes ni se añaden llamadas. En los dos informes guardados el prompt baja de 80010/92535 a 22083/23560 bytes, sin eliminar ninguna de las 24/22 aportaciones. Verificación offline con salida simulada; falta confirmar generación real. Una muestra mucho mayor aún puede superar el límite y conserva el fallo explícito, sin truncado silencioso.


### Perfil económico de cierre y referencias — 25/10/2026

Se vuelve a gpt-6-luna/medium en todos los roles por petición del usuario. Las entradas anteriores Sol/medium y 40/80 referencias son registros históricos. Límite vigente de citas: MAX_EVIDENCE_REFS=200, compartido por los validadores, igual que la ventana máxima de investigación; hasta doce IDs/rangos por elemento, cada rango hasta 200 líneas y 200 fuentes únicas expandidas en total. No aumenta la cantidad de código leído por el agente. Todas las fuentes se verifican y las ocultadas siguen rechazadas. Los resúmenes de scanners se muestran por separado y no permiten marcar favorable un control sin citas de código; en ese caso queda no_evaluado con el resultado de herramienta explicado en el motivo.
