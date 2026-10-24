# Fase 2 — Mejora de agentes, recuperación y calidad

Estado: **en curso: F2-01 a F2-03 realizadas para los tres especialistas actuales y coordinador; recorrido completo comprobado con límites semánticos explícitos**. Parte de la Fase 1 0.3.0 aceptada el 24/10/2026. El usuario conserva el merge a main. Esta fase mejora configuración y funcionamiento según evidencia y feedback; no presupone entrenamiento de pesos ni actualización de dependencias.

## Objetivo

Conseguir respuestas más útiles, precisas y propias de cada especialidad, localizando suficiente código con un coste controlado. Primero revisar qué instrucciones/configuración se aplican realmente a los agentes Hermes usados por Arktic; después cambiar una causa cada vez. No ampliar CI/CD, añadir servicios ni ejecutar suites completas sin necesidad. Mantener un perfil económico reproducible y pruebas dirigidas mínimas.

## Punto de partida comprobado

- El flujo descarga y verifica el snapshot completo antes de mapas/scanners. Los especialistas reciben fragmentos limitados: insuficiencia de contexto no implica que falten archivos descargados.
- [hermes_runtime.py](../backend/src/arktic_office/adapters/hermes_runtime.py) instancia `AIAgent` por llamada con un prompt de sistema efímero, herramientas desactivadas y `max_iterations=1`. Se usan `skip_context_files=True`, `skip_memory=True`, `skip_background_review=True`; no se solicita identidad SOUL. No asumir que una personalidad configurada en otra sesión/UI se aplica a estas llamadas.
- Los focos efectivos salen de [agents.json](../backend/src/arktic_office/resources/profiles/agents.json). Perfiles de modelos/límites: [models.json](../backend/src/arktic_office/resources/profiles/models.json) y [config/models.py](../backend/src/arktic_office/config/models.py). Investigación y coordinación: [research.py](../backend/src/arktic_office/coordination/research.py), [coordinator.py](../backend/src/arktic_office/coordination/coordinator.py). Skill y contrato de salida se añaden explícitamente; la configuración efectiva incluye también variables de entorno, sin exponer secretos.
- Las últimas consultas fueron por rutas exactas, con relaciones del grafo adjuntas. Esto no demuestra navegación eficiente por símbolos/grafo. Las ventanas de 100 líneas pueden omitir rutas/middleware posteriores; Arquitectura agotó su cap de seis archivos. El padding de líneas consume presupuesto. Aumentar archivos o modelo sin localizar el cuello de botella no garantiza mejor resultado.
- Baseline `f7043007-40a9-42a3-8b1e-a1478688c25c`: tres especialistas y síntesis, 8 llamadas gpt-6-luna/low, 52.366 tokens comunicados, 7 observaciones y 22 citas verificadas. Informe parcial: un tema inválido rechazado, cinco controles no evaluados, una formulación sobre recuperación de trabajos demasiado amplia. [Evidencia](evidence/orchestrator-research-2026-10-24.json).

## Orden y entregables

| Paso | Qué revisar primero | Decisión que debe permitir |
|---|---|---|
| 1. Agentes e instrucciones | Perfil visible en Hermes frente al agente que realmente invoca Arktic; prompt completo, idioma, responsabilidad y contrato | Qué instrucciones se están usando y cuáles conviene corregir |
| 2. Evidencia y límites | Consulta realizada, símbolo/relación, región de código recibida, fuente omitida y motivo | Si falta información real o falló su localización/entrega |
| 3. Calidad y coste | Mismas preguntas y commit, una variable por comparación, feedback humano | Conservar el cambio útil y decidir si hace falta otro modelo o una actualización |

La ficha de configuración efectiva precedió al cambio funcional y sus pilotos. No se elevan modelos ni número global de archivos. La implementación inicial y resultados se registran al final; las incorporaciones de agentes siguen como propuesta.

## 1. Revisar configuración efectiva de Hermes y agentes

- [x] F2-01 Trazar cómo el Hermes fijado compone el prompt: sistema base, prompt efímero, perfil, identidad, idioma, archivos de contexto, memoria y herramientas. Contrastar los flags del adaptador con el código de Hermes instalado, sin mostrar credenciales ni conversaciones privadas. Distinguir perfiles visibles en Hermes de los agentes efímeros del análisis, indicando qué configuración sí se carga, cuál se ignora y qué instrucciones heredadas permanecen. No asumir que cambiar la UI o un SOUL cambia el análisis.
- [x] F2-02 Inventariar las instrucciones realmente enviadas por rol y detectar duplicidades, contradicciones o huecos: objetivo, idioma español, qué constituye evidencia suficiente, cuándo buscar, cómo declarar límites, enums y esquema de salida. No modificar todavía varios prompts a la vez.
- [x] F2-03 Proponer focos breves y criterios claros por especialidad, con ejemplos pequeños: Seguridad evalúa controles/riesgos; Arquitectura describe estructura y operación; Inventario identifica tecnología/función. Orquestador distribuye objetivos y sintetiza sin ampliar las conclusiones. Probar el cambio mínimo que corrija el problema identificado.

**Salida de la primera tarea, realizada:** ficha siguiente y [evidencia no secreta del runtime instalado](evidence/phase2-agent-audit-2026-10-24.json). La auditoría precede al cambio de instrucciones registrado al final. Su evidencia se conserva como tal; no se convierte retrospectivamente en una ejecución real de agentes.

## 2. Comprobar cómo encuentran y reciben el código

- [ ] F2-04 Seguir las trazas de fuentes necesarias, consultas, ventanas recibidas, omisiones por presupuesto y carencias finales. Clasificar cada carencia: información operativa inexistente, parser incompatible, búsqueda ineficiente, ventana incorrecta, cap agotado o interpretación del modelo.
- [ ] F2-05 Ensayar navegación orientada por símbolos/relaciones y lectura de la región concreta antes de aumentar caps. Verificar al menos el acceso a rutas HTTP/middleware y código de recuperación, comparando el contenido entregado con lo que se necesitaba.
- [ ] F2-06 Si las trazas lo justifican, ajustar una sola variable: segunda ronda de Seguridad, ventanas, límites por rol o instrucciones de búsqueda. Mantener límites duros, mismo snapshot y registro de contexto realmente entregado. No adoptar un aumento global de archivos como respuesta automática.

**Salida:** explicación verificable de por qué cada rol obtuvo o no el código necesario y el menor ajuste útil al flujo existente.

## 3. Medir, recoger feedback y decidir modelos

- [ ] F2-07 Definir un conjunto pequeño de preguntas esperadas sobre repositorios representativos y sus fuentes, incluyendo casos de insuficiencia legítima. Comparar una variable por vez sobre el mismo commit. Acordar un presupuesto acotado antes de una tanda de pruebas reales; no introducir bucles de evaluación automáticos.
- [ ] F2-08 Medir utilidad por rol, interpretación fiel, citas, rechazos de formato, carencias resolubles, consultas útiles, bytes, llamadas, tiempo y tokens comunicados. Que una cita exista no valida la conclusión; que haya más hallazgos no demuestra más calidad. Conservar también intentos fallidos.
- [ ] F2-09 Ajustar modelo/razonamiento por rol solo cuando se distinga un fallo de razonamiento de falta de fuentes o instrucciones. Conservar perfil económico; revisar modelos/proveedor disponibles y consumo en el momento, sin fijar ahora una elevación general. Valorar una actualización de Hermes/Graphify únicamente si resuelve una carencia comprobada, contrastando compatibilidad con los pins y la misma muestra antes de adoptarla.
- [ ] F2-10 Incorporar feedback visual y sobre informes con cambios pequeños. Cerrar esta fase mediante aceptación humana, resultados comparables y decisión de versión independiente; merge manual del usuario.

**Criterio de cierre propuesto:** los roles respetan su responsabilidad, acceden al código necesario dentro del presupuesto acordado y distinguen carencias reales de fallos de recuperación. Resultados y límites comprensibles y aceptados por el usuario. Las comprobaciones se limitan a contratos/caminos afectados y pilotos representativos; sin nuevos pipelines ni una plataforma de evaluación.

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
- [ ] F2-11 Valorar después un conector opcional a alertas históricas de GitHub Secret Scanning. Queda diferido; no instalar skills ni ampliar ahora el scanner al historial.

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
