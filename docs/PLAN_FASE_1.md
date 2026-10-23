# Fase 1 — Evolución de Arktic Office

Fecha de registro: 23/10/2026.

Estado: implementación limitada al Bloque 1 (F1-01 a F1-03); comprobaciones y limitaciones registradas debajo. El resto continúa pendiente. Las decisiones técnicas indicadas como pendientes requieren validación antes de adoptarse. La entrega permanece abierta y las versiones actuales se conservan.

## Relación con el MVP actual

Esta es la siguiente etapa de producto después del MVP, no la fase interna número 1 del plan histórico.

- El [PLAN_MVP.md](../PLAN_MVP.md) conserva el alcance, seguimiento, verificaciones y cierre del MVP. No se sustituye ni se reescribe con este roadmap.
- Base de esta evolución: frontend **0.2.0** y backend **0.2.0**, commit `eb71fb71586e299cd5d3dea3474b1be382ee2a1d` (`Release frontend 0.2.0 and backend 0.2.0`).
- El [CHANGELOG.md](../CHANGELOG.md) registra las entregas realizadas; este documento registra trabajo futuro.
- «Fase 1» no asigna una versión de software. El número de la siguiente entrega se decidirá al cerrarla. Los archivos de versión actuales permanecen en 0.2.0.
- La revisión que origina este plan fue estática. No se ejecutaron servicios, pruebas, scanners ni llamadas a modelos para elaborar la propuesta. Las verificaciones del MVP son históricas y siguen documentadas en su propio plan.

## Objetivo

Entregar una evaluación preliminar, ejecutiva y útil de aplicaciones creadas con IA por personas no técnicas, centrada en seguridad y viabilidad operativa. Identificar riesgos relevantes, condiciones de operación y dudas que justifican una revisión posterior por un desarrollador o arquitecto.

La decisión final corresponde al responsable técnico. No se busca una auditoría exhaustiva, certificar seguridad ni enviar todo el código al modelo. La ausencia de evidencia no demuestra ausencia de un control. Capacidad, consumo de recursos y recuperación real requieren mediciones o evidencia externa al código.

## Alcance acordado

- Evolucionar el repositorio actual por entregas revisables, conservando la oficina, Hermes y el diseño útil de los informes.
- Mantener la instalación local con Docker Compose y los modelos online. La preparación e indexación también deben ejecutarse dentro de Docker, sin generar grafos manualmente en el host.
- Combinar reglas y búsquedas locales, mapa estructural y exploración dirigida con Hermes. Usar IA solo donde aporte valor y reutilizar herramientas existentes.
- Permitir iteraciones acotadas en preparación. Los especialistas reciben un encargo y trabajan sin rondas adicionales de búsqueda, reintentos o solicitudes de evidencia.
- Incorporar un coordinador con IA y especialistas de Seguridad, Arquitectura/operación e Inventario, con instrucciones y skills reutilizables.
- Separar modelos, proveedor, razonamiento y presupuestos de las instrucciones reutilizables.
- Conservar evidencias trazables al commit, resultados parciales útiles y el estado explícito de información insuficiente. Mantener los errores técnicos diferenciados.
- Vincular animaciones, burbujas, orientación y actividad de la oficina con estados reales del trabajo.
- Ordenar Python, pruebas, documentación humana, recursos de ejecución y resultados; versionar por entrega y añadir CI mínima.

## Recomendación técnica y decisiones pendientes

La recomendación principal es una aplicación modular dentro del mismo repositorio. No se propone reconstruir todo ni crear un servicio por agente.

| Decisión | Propuesta registrada | Estado |
|---|---|---|
| Indexador | Probar primero Graphify en extracción de código sin modelo; Codebase-Memory queda como alternativa | Pendiente de prueba comparativa suficiente para decidir |
| Despliegue | Oficina, Core API y preparador local como tres componentes de Compose | Recomendación; confirmar separación tras comprobar dependencias y recursos |
| Preparación | Snapshot fijado a commit, reglas locales, grafo y exploración Hermes limitada | Dirección acordada; contratos y límites pendientes |
| Eventos | Publicar estados estructurados para la oficina; valorar SSE conservando REST | Transporte y persistencia pendientes |
| Persistencia | Archivos para evidencias e informes; valorar SQLite para trabajos, eventos y conversaciones | Pendiente; evitar infraestructura adicional innecesaria |
| Modelos | Registro central validado, con perfiles por rol y excepciones explícitas | Formato y valores pendientes |
| Conversación | Consultar evidencia guardada con historial acotado por revisión y personaje | Ampliación recomendada; presupuesto y comportamiento pendientes |
| Versión global | Manifiesto de entrega que relacione versiones de aplicación, componentes, skills, plantillas y dependencias | Mecanismo y siguiente número pendientes |

Graphify no es GraphQL. Su extracción `--code-only` está documentada sin necesidad de clave de modelo. Su Dockerfile consultado sirve un grafo existente mediante MCP; no resuelve por sí solo la descarga y generación automática del grafo. La integración deberá cubrir ese recorrido dentro de Docker. Su mayor popularidad no prueba estabilidad ni rendimiento para nuestros repositorios.

Codebase-Memory no se descarta por funcionar localmente: una herramienta local puede ejecutarse dentro de un contenedor. Se mantiene como alternativa si Graphify no cumple cobertura, coste de integración o recursos. No incorporar ambos por defecto.

## Responsabilidades y flujo previsto

| Componente | Responsabilidad |
|---|---|
| Oficina | Iniciar revisiones, representar estados e interacciones, mostrar informes y permitir consultas |
| Core API | Gestionar trabajos, presupuesto, coordinador Hermes, especialistas, validación, síntesis y eventos |
| Preparador local | Obtener el código, aplicar reglas y comprobaciones locales, generar el mapa y ofrecer búsquedas y fragmentos |

1. Recibir la URL, resolver la rama predeterminada real y fijar un commit. Obtener una copia de trabajo acotada sin necesitar todo el historial. Declarar exclusiones y límites de descarga.
2. Extraer inventario, documentación, dependencias, configuración, puntos de entrada y mapa estructural mediante herramientas locales. Separar el conjunto que se inspecciona localmente del contexto enviado al modelo.
3. Permitir al coordinador Hermes buscar, consultar relaciones y leer fragmentos relevantes. Repetir de forma limitada cuando falte cobertura de un aspecto prioritario, como acceso o persistencia.
4. Cerrar la preparación con paquetes de evidencia por especialista: commit, rutas, líneas originales, citas, cobertura y carencias. No enviar el grafo completo al modelo por defecto.
5. Ejecutar una vez cada especialista con su modelo y skills autorizadas. Si no puede aportar un resultado útil, declarar qué información falta y terminar su intervención.
6. Sintetizar mediante el coordinador y validar fuentes y contrato antes de generar HTML, Markdown y JSON. Conservar aportaciones válidas, desacuerdos y límites; usar la consolidación determinista como respaldo si la síntesis falla.
7. Permitir consultas posteriores sobre los resultados conservados, sin relanzar automáticamente el análisis ni buscar nueva evidencia.

El grafo es una ayuda para localizar relaciones, no una prueba de que se ha reconstruido un flujo completo. Mantener búsquedas textuales y lectura dirigida para relaciones dinámicas, configuración o lenguajes con cobertura incompleta.

## Límites y controles de consumo

- No ejecutar la aplicación analizada, instalar sus dependencias ni ejecutar sus tests o scripts. No dar acceso al socket Docker.
- Tratar las instrucciones del repositorio analizado como datos, no como instrucciones para nuestros agentes. Exponer al explorador únicamente herramientas de lectura, búsqueda y consulta autorizadas.
- Mantener credenciales fuera de imágenes y artefactos. Aplicar controles de ocultación antes de enviar fragmentos al proveedor; documentar sus límites.
- Presupuestar descarga, espacio temporal, indexación, duración, iteraciones, contexto y salida por ejecución y rol. Mostrar consumo reportado y distinguirlo de estimaciones.
- Comprobar qué límites puede imponer realmente cada proveedor. Un límite configurado no constituye una garantía de tokens si el runtime o proveedor no lo aplica.
- Al alcanzar un límite, terminar con cobertura y resultados parciales explícitos; no ampliar automáticamente el modelo o presupuesto.
- Evitar llamadas de modelo para etiquetas, burbujas de estado y animaciones. Una skill no requiere modelo propio por defecto; cualquier llamada adicional debe estar declarada y presupuestada.

| Métrica | Objetivo inicial, no garantía | Comprobación pendiente |
|---|---|---|
| Preparación local | Aproximadamente 5 minutos en muestras representativas; hasta unos 10 puede ser aceptable si el recorrido total sigue siendo útil | Tamaño, lenguajes, CPU, memoria e indexador |
| Recorrido completo | Procurar terminar antes de 15 minutos | Latencias de modelos, exploración y política de corte |
| Tokens | Consumo acotado, con contexto selectivo y reutilización de evidencias | Fijar un presupuesto después de medir utilidad en las muestras |
| Cobertura | Evidencia suficiente para una evaluación preliminar útil | Comparar con aspectos relevantes conocidos, sin confundir cobertura con número de archivos |

La configuración base admite un proceso exterior de hasta 25 minutos y limita el auditor a 1 GB de RAM y 128 MB temporales. Son valores actuales, no objetivos de la Fase 1. Habrá que revisar almacenamiento y recursos. El backend actual usa Python 3.14 y el Dockerfile de Graphify consultado usa Python 3.12; verificar compatibilidad antes de compartir entorno.

## Roadmap y tareas

Solo se implementa el Bloque 1 por encargo del usuario. La finalización de un bloque exige registrar su evidencia, límites y resultado; no basta con cambiar su estado. No se asignan fechas ni duraciones de desarrollo todavía.

### Bloque 1 — Base reproducible y CI mínima

- [x] F1-01 Automatizar recuperación de dependencias por commit y aplicación del parche de frontend desde un clon limpio.
- [x] F1-02 Añadir GitHub Actions para construir imágenes y comprobar arranque de API y oficina mediante sus rutas de salud.
- [x] F1-03 Garantizar que estas comprobaciones no inician revisiones ni requieren credenciales de modelos. Documentar CD como pendiente, sin despliegue automático.

**Cierre:** clon limpio reproducible, imágenes construidas y servicios saludables. Evidencia de las comprobaciones sin llamadas a modelos. Mantener las pruebas útiles del MVP como base de regresión.

**Implementación y comprobaciones del 23/10/2026:**

- F1-01: [restore-sources.ps1](../scripts/restore-sources.ps1) recupera con fetch superficial los commits completos de `HERMES3D_VERSION` y `HERMES_AGENT_VERSION`, verifica HEAD y comprueba/aplica el parche con verificación inversa. Configura rutas largas y conserva LF. Rechaza ambos destinos preexistentes antes de descargar; no sobrescribe ni borra fuentes locales.
- F1-02: [ci.yaml](../.github/workflows/ci.yaml) ejecuta recuperación, build y arranque en Ubuntu 24.04 para push, PR y ejecución manual. Checkout fijado por SHA, permisos de lectura, sin secretos. [check-startup.ps1](../scripts/check-startup.ps1) es la misma entrada local y de CI; espera healthchecks y consulta rutas HTTP de API, oficina y proxy del listado.
- F1-03: [compose.ci.yaml](../compose.ci.yaml) elimina `.env`, los montajes de uso diario y los puertos publicados; utiliza volúmenes nuevos y red interna sin salida. Solo se levantan API y oficina. El script solo hace GET, exige listado sin trabajos ni consulta activa, `/reports` vacío y `/auth` vacío. Limpia su propio proyecto temporal mediante `finally`. No inicia análisis, scanners ni llamadas a modelos. Los scanners se instalan como parte de la imagen existente, sin ejecutarlos.
- Recuperación comprobada en `artifacts/block1-clean-network/`, exportación de archivos versionados y cambios de este bloque, sin `vendor`, `.env`, informes ni estado anterior. Ambos originales se descargaron de GitHub con los commits fijados; aplicación y comprobación inversa del parche correctas. La segunda invocación fue rechazada antes de modificar fuentes. Un primer intento aislado falló por restricción de red del sandbox; la repetición con acceso autorizado completó la descarga.
- Entorno: Windows/PowerShell 7, Docker Desktop 4.47.0, Engine 28.4.0 Linux/amd64 y Compose 2.39.4-desktop.1. La configuración resuelta muestra únicamente API y oficina, red `internal: true`, sin puertos, sin variables de credenciales y con volúmenes exclusivos del proyecto temporal.
- Construcción y arranque completados: ambas imágenes `arktic-hermes-auditor:0.2.0` y `arktic-hermes3d-office:0.2.0` construidas desde las fuentes recuperadas. Frontend compilado y TypeScript superado. La primera ejecución alcanzó ambos healthchecks pero una consulta adicional solicitaba `/api/audit/health`, ruta no admitida por el proxy; se corrigió el script para consultar `/health` directamente desde la red de la oficina y `/api/audit/runs` por el proxy, sin modificar la aplicación. También se comprobó la limpieza tras ese fallo.
- Repetición completa con el script final: salida 0, proyecto `arktic-ci-c955ed6a2a5b`, ambos servicios `healthy`; API `/health` devuelve `{"ok":true,"version":"0.2.0"}`, `/runs` vacío y sin consulta activa; `/reports` y `/auth` vacíos. `GET /office`, `GET /api/audit/runs` y `GET http://audit-api:8080/health` desde office devuelven 200. Contenedores, red y tres volúmenes temporales retirados correctamente. Log final local excluido de Git: `artifacts/block1-startup-final.log`; primer build y diagnóstico: `artifacts/block1-startup.log`.
- Sintaxis de ambos scripts PowerShell y `git diff --check` correctos. Archivos de versiones, referencias de terceros, `CHANGELOG.md` y `PLAN_MVP.md` sin cambios. Resultado del Bloque 1: implementado y comprobado localmente y en GitHub Actions.

- Validación remota tras el push y apertura del [PR #2 hacia main](https://github.com/ziuld/analysis-office-test/pull/2), commit `e336b7b`: [CI de pull_request](https://github.com/ziuld/analysis-office-test/actions/runs/40002108514) y [CI de push](https://github.com/ziuld/analysis-office-test/actions/runs/40002087106), ambas completadas con `success`. En Ubuntu 24.04 pasaron recuperación de fuentes fijadas/parche y construcción/arranque aislado sin credenciales de modelos. No se ha fusionado el PR ni cerrado la entrega.

**Limitaciones y entrega:** la prueba local utilizó una exportación limpia con los cambios aún sin commit; posteriormente se validó un checkout nuevo del PR en GitHub Actions. Docker puede reutilizar caché; no se afirma construcción totalmente sin caché, sin Internet ni idéntica bit a bit. La construcción requiere GitHub, registros y servidores de paquetes. El workflow pasó en Ubuntu 24.04 en GitHub Actions; otros equipos y arquitecturas quedan pendientes. HTTP saludable no valida la representación visual ni calidad de informes, proveedores o autenticación. No se ejecutan análisis de repositorios ni scanners ni modelos para estas comprobaciones; las pruebas del MVP se conservan sin cambios y no se atribuyen nuevas ejecuciones a su histórico. Una interrupción forzada puede impedir la limpieza automática. **CD pendiente**, sin publicación de imágenes, despliegue, release ni etiquetas automáticas. Frontend/backend permanecen en **0.2.0**, commits de terceros y changelog sin cambios; el cierre de entrega se acordará después.

### Bloque 2 — Validación del indexador dentro de Docker

- [ ] F1-04 Fijar una versión de Graphify y automatizar descarga, extracción de código y consulta del grafo dentro de Docker.
- [ ] F1-05 Probar repositorios representativos y medir duración, memoria, cobertura de lenguajes, relaciones recuperadas y errores, sin modelos.
- [ ] F1-06 Decidir Graphify o evaluar Codebase-Memory con los mismos criterios si el primero no encaja. Confirmar límites, licencia, dependencias y separación del preparador.

**Cierre:** recorrido sin pasos manuales con grafos ni instalación del indexador en el host. Decisión documentada con datos; no solo por estrellas o promesas del proveedor. Este bloque precede a comprometer el núcleo con un indexador.

### Bloque 3 — Organización del núcleo y contratos

- [ ] F1-07 Crear el paquete Python con `pyproject.toml`, módulos por responsabilidad y pruebas fuera del código de producción.
- [ ] F1-08 Separar almacenamiento, ejecución, configuración y adaptadores; definir contratos de evidencia, estados y eventos.
- [ ] F1-09 Conservar compatibilidad con informes y trabajos históricos. Preparar una resolución de rutas por identificador para permitir carpetas de resultados organizadas.

**Cierre:** pruebas relevantes existentes superadas, contratos preservados e informes históricos accesibles. Esta reorganización no cambia por sí sola el comportamiento del análisis.

### Bloque 4 — Preparación híbrida

- [ ] F1-10 Separar adquisición del repositorio y selección del contexto; usar la rama predeterminada real y mantener trazabilidad al commit.
- [ ] F1-11 Integrar reglas locales, mapa estructural, búsquedas y lectura de fragmentos con sus posiciones originales. Declarar por separado la cobertura de scanners y la del modelo.
- [ ] F1-12 Añadir exploración Hermes con herramientas restringidas, iteraciones y presupuesto acotados, eventos y cierre explícito por suficiencia o límite.

**Cierre:** recuperación de flujos representativos con evidencias verificables sin enviar todo el repositorio. Carencias, exclusiones, consumo y fallos visibles. No ejecutar el código analizado.

### Bloque 5 — Coordinador, especialistas y skills

- [ ] F1-13 Extraer instrucciones de agentes y skills reutilizables, documentando entradas, salidas, herramientas y requisitos de compatibilidad.
- [ ] F1-14 Centralizar perfiles de modelos, razonamiento y límites; validar configuración antes de consumir modelo.
- [ ] F1-15 Incorporar reparto y síntesis con IA, manteniendo especialistas de una pasada, validación de citas y aportaciones parciales.
- [ ] F1-16 Hacer opcionales las capacidades específicas, como propuesta Azure, según el encargo; su ausencia no debe invalidar una evaluación que no las necesita.

**Cierre:** solo la preparación amplía evidencia mediante iteraciones. Fallos o insuficiencia de una parte no destruyen resultados válidos. Portabilidad de skills documentada sin prometer compatibilidad automática con cualquier producto.

### Bloque 6 — Oficina y consultas

- [ ] F1-17 Conectar eventos reales con burbujas, indicadores de trabajo, desplazamientos, orientación e interacciones entre personajes.
- [ ] F1-18 Corregir asientos, alineación y profundidad de muebles mediante comprobación visual. Evitar conversaciones o progreso ficticios.
- [ ] F1-19 Representar fin, interrupción, fallo e información insuficiente; orientar al personaje al seleccionarlo y animar la consulta.
- [ ] F1-20 Incorporar historial acotado por revisión y agente si se confirma esa ampliación, usando evidencias guardadas y sin relanzar el equipo.

**Cierre:** la oficina refleja el estado real, cesa su actividad al terminar y mantiene interacciones legibles. Las animaciones no consumen modelo. Las correcciones visuales independientes pueden adelantarse tras acordar el contrato de eventos.

### Bloque 7 — Resultados, documentación y entrega

- [ ] F1-21 Organizar resultados por fecha, hora, título e identificador; distinguir informes del producto de capturas de desarrollo. Definir conservación y limpieza de snapshots e índices.
- [ ] F1-22 Separar documentación humana de plantillas, esquemas y estándares usados en ejecución; actualizar enlaces e instrucciones.
- [ ] F1-23 Evaluar utilidad, citas, insuficiencia, consumo y tiempos con muestras representativas. Mantener comprobaciones deterministas sin modelos en CI; las evaluaciones reales serán explícitas y presupuestadas.
- [ ] F1-24 Cerrar la entrega con aceptación humana, manifiesto de versiones, changelog y referencias Git según el flujo de publicación acordado.

**Cierre:** cada informe identifica código revisado, cobertura, modelos, recursos versionados y consumo disponible. La entrega distingue lo medido de lo pendiente y conserva acceso al histórico.

## Estructura orientativa

Propuesta a concretar en el bloque 3; no describe carpetas ya implementadas.

```text
arktic-office/
├── README.md
├── PLAN_MVP.md                  # Registro histórico conservado
├── LICENSE                     # Cuando se acuerde la licencia propia
├── compose.yaml
├── release.json                # Manifiesto de entrega propuesto
├── config/
│   ├── models.json
│   └── budgets.json
├── backend/
│   ├── pyproject.toml
│   ├── src/arktic_office/
│   │   ├── api/
│   │   ├── preparation/
│   │   ├── coordination/
│   │   ├── evidence/
│   │   ├── reporting/
│   │   ├── conversations/
│   │   ├── storage/
│   │   └── adapters/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
├── frontend/
├── agents/
├── skills/
├── resources/
│   ├── templates/
│   ├── schemas/
│   └── editorial/
├── docs/
│   └── PLAN_FASE_1.md
├── docker/
├── .github/workflows/
└── artifacts/                  # Generados, excluidos de Git
    └── runs/2026-10-23/1530-tienda-online-id/
        ├── manifest.json
        ├── evidence/
        ├── specialists/
        └── reports/
```

No hay un estándar único de organización de sistemas de IA en Python. Se propone `src/`, pruebas separadas, módulos por responsabilidad y adaptadores para dependencias externas. Evitar una arquitectura hexagonal completa si no aporta una separación útil. Los snapshots e índices temporales vivirán en un volumen con limpieza definida, separado de informes conservados.

El frontend actual se distribuye como parche sobre Hermes3D. Primero se hará reproducible ese mecanismo; después se decidirá cómo mantener el frontend adaptado como fuente propia versionada, conservando atribuciones y origen. No copiar `vendor/` sin revisar dependencias y licencias.

## Versionado y preservación del histórico

- Mantener este plan separado del MVP. Registrar aquí avance futuro con fecha y evidencia, sin atribuir al MVP capacidades nuevas.
- Los commits intermedios pueden guardar avances sin subir versiones. Cambiar números al cerrar una entrega acordada, no por cada edición de instrucciones o plantillas.
- Relacionar versión global de entrega y versiones de componentes y recursos. Conservar las revisiones de terceros fijadas.
- No modificar ni borrar informes históricos para hacerlos coincidir con resultados nuevos. Si cambia la presentación, preservar los datos originales y su procedencia.
- Mantener el recorrido anterior durante la transición cuando sea viable. No ejecutar automáticamente ambos recorridos y duplicar consumo.
- No dar por completada una capacidad por mover archivos o añadir configuración. Las pruebas de formato y las muestras ficticias no validan la calidad de respuestas reales.

## Información pendiente que condiciona la validación

1. Lenguajes y tipos de aplicación prioritarios, con dos o tres repositorios representativos y autorización de acceso cuando corresponda.
2. Memoria y CPU disponibles para Docker Desktop en el equipo de referencia.
3. Presupuestos por ejecución, política de corte y conservación de datos, a concretar con las primeras mediciones. Valorar una ficha opcional de contexto operativo y políticas de empresa, sin asumir esos datos a partir del código.

## Fuentes y trazabilidad

Capacidades contrastadas en fuentes primarias durante la propuesta del 23/10/2026; las fuentes externas pueden evolucionar. Fijar versiones durante la validación.

- [Graphify: extracción sin IDE y modo code-only](https://github.com/Graphify-Labs/docs/blob/main/guides/headless-extraction.mdx).
- [Graphify: Dockerfile consultado para servir un grafo existente](https://github.com/Graphify-Labs/graphify/blob/v8/Dockerfile).
- [Codebase-Memory MCP](https://github.com/DeusData/codebase-memory-mcp).
- [PyPA: src layout y flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).
- [pytest: prácticas de integración y organización de pruebas](https://docs.pytest.org/en/stable/explanation/goodpractices.html).
- Base local revisada: [preparación](../auditor/repository.py), [coordinación](../auditor/team.py), [adaptador Hermes](../auditor/runtime.py), [API](../auditor/server.py), [consultas](../auditor/questions.py), [validación e informes](../auditor/reporting.py), [Compose](../compose.yaml) y [parche de la oficina](../docker/hermes3d-local-demo.patch).

## Registro de seguimiento

| Fecha | Cambio | Estado de implementación |
|---|---|---|
| 23/10/2026 | Plan registrado por petición del usuario, separado del MVP 0.2.0; alcance, recomendaciones, tareas y comprobaciones pendientes documentados | Ninguna tarea de la Fase 1 implementada en este registro |
| 23/10/2026 | Bloque 1 F1-01 a F1-03 implementado: recuperación por commit, CI mínima y arranque aislado sin modelos; evidencia y limitaciones en el bloque | Comprobaciones local y remota satisfactorias; entrega abierta, versiones 0.2.0 conservadas |
