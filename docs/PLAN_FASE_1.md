# Fase 1 — Evolución de Arktic Office

Fecha de registro: 23/10/2026.

Estado: Bloque 1 fusionado; bloques 2, 3, 4, 5 y 6 implementados y comprobados localmente, con evidencia y límites registrados debajo. El Bloque 7 está implementado técnicamente; F1-23 sigue parcialmente pendiente de evaluación completa (sesión recuperada y una célula real validada) y F1-24 requiere aceptación humana. Las decisiones técnicas indicadas como pendientes requieren validación antes de adoptarse. La entrega permanece abierta y las versiones actuales se conservan.

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
- A partir del Bloque 3, por indicación explícita del usuario, conservar CI/CD con la base del Bloque 1 y no ampliarla en los siguientes bloques. Realizar solo las pruebas manuales mínimas necesarias para los cambios, evitando sobreingeniería.

## Recomendación técnica y decisiones pendientes

La recomendación principal es una aplicación modular dentro del mismo repositorio. No se propone reconstruir todo ni crear un servicio por agente.

| Decisión | Propuesta registrada | Estado |
|---|---|---|
| Indexador | Graphify 0.9.95 fijado con overlay PyYAML, como ayuda estructural junto a búsquedas/texto | Seleccionado tras las muestras del Bloque 2; límites en [INDEXADOR.md](INDEXADOR.md). Codebase-Memory queda sin evaluar |
| Despliegue | Oficina, Core API y preparador local separado | Preparador separado integrado opcionalmente mediante `compose.hybrid.yaml`; base legacy conservada |
| Preparación | Snapshot fijado a commit, reglas locales, grafo y exploración Hermes limitada | Implementada y comprobada con respuestas ficticias en Bloque 4; calidad real pendiente |
| Eventos | Publicar estados estructurados para la oficina; valorar SSE conservando REST | Estados persistidos y sondeo REST existente en Bloque 6; sin SSE adicional |
| Persistencia | Archivos para evidencias e informes; valorar SQLite para trabajos, eventos y conversaciones | Archivos JSON y catálogo acotado; sin SQLite ni infraestructura adicional |
| Modelos | Registro central validado, con perfiles por rol y excepciones explícitas | Perfiles instalados y validados en Bloque 5; disponibilidad real condicionada por sesión/cuota |
| Conversación | Consultar evidencia guardada con historial acotado por revisión y personaje | Confirmada: últimas diez consultas por revisión/personaje, independientes y solo lectura al abrir historial |
| Versión global | Manifiesto de entrega que relacione versiones de aplicación, componentes, skills, plantillas y dependencias | Manifiesto candidato y manifiestos por revisión implementados; siguiente número y cierre pendientes |

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

El usuario autorizó sucesivamente todos los bloques y la preparación del PR hacia main; realizará el merge personalmente. La finalización de un bloque exige registrar su evidencia, límites y resultado; no basta con cambiar su estado. No se asignan fechas ni duraciones de desarrollo todavía.

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

- [x] F1-04 Fijar una versión de Graphify y automatizar descarga, extracción de código y consulta del grafo dentro de Docker.
- [x] F1-05 Probar repositorios representativos y medir duración, memoria, cobertura de lenguajes, relaciones recuperadas y errores, sin modelos.
- [x] F1-06 Decidir Graphify o evaluar Codebase-Memory con los mismos criterios si el primero no encaja. Confirmar límites, licencia, dependencias y separación del preparador.

**Cierre:** recorrido sin pasos manuales con grafos ni instalación del indexador en el host. Decisión documentada con datos; no solo por estrellas o promesas del proveedor. Este bloque precede a comprometer el núcleo con un indexador.

**Implementación y comprobaciones del 23/10/2026:**

- El usuario confirmó Arktic Office y `ziuld/bookingApi` como muestras. Se fijan los commits de ambas y se incluye como tercera muestra el frontend de Arktic Office reconstruido a partir de Hermes3D fijado y el parche actual. No se ejecutan esos proyectos, sus dependencias o tests, scanners ni modelos.
- [check-indexer.ps1](../scripts/check-indexer.ps1), [compose.indexer.yaml](../compose.indexer.yaml) y [Indexer.Dockerfile](../docker/Indexer.Dockerfile) automatizan build, recuperación, parche y extracción/consulta en contenedores. No requieren `vendor/`, credenciales ni herramientas de indexación instaladas en el host. La extracción y consulta usan `network_mode: none`; se verificó por `docker inspect` en el contenedor real: 2 CPU, 2 GiB, 128 procesos/hilos, root filesystem de solo lectura, sin privilegios y con todas las capabilities retiradas.
- Graphify 0.9.95, commit `92741d162b2094ffc2fed58cfbd8ee823e9da62c`, Python 3.12 separado del backend 3.14. Lock upstream más overlay PyYAML 6.0.3 con hash oficial, tras detectar su ausencia del lock. `uv pip check` correcto; las licencias Apache-2.0, MIT anterior y NOTICE se conservan en el repositorio y la imagen. No se instalan extras de modelos, MCP ni transcripción.
- Ensayos iniciales: corregida la sintaxis YAML del montaje temporal antes de leer las muestras; la primera extracción completa permitió detectar YAML omitido por la dependencia ausente, ambigüedades de clases/constructores y contadores cgroup v1 no recogidos por el primer wrapper. Se corrigieron overlay, consultas acotadas por ID y lectura de métricas v1/v2; los logs iniciales permanecen en `artifacts/block2-validation.log` y `artifacts/block2-validation-second.log`.
- Repetición final `indexer-20261023-184518-e41e49`, salida 0: cinco pruebas del descargador correctas; recuperación/parche y consultas dentro de Docker. Extracción Python/backend **15,232 s / 119,1 MiB**, Java **18,412 s / 79,9 MiB**, frontend **229,787 s / 211,5 MiB** de pico de contenedor. Grafos de 407/1.361, 321/985 y 4.546/12.898 nodos/aristas, respectivamente. No hubo timeouts ni fallos de asignación de memoria registrados. Logs en `artifacts/block2-validation-final.log` y resultados por muestra bajo `artifacts/indexer-20261023-184518-e41e49/`.
- Cobertura por archivos representados: Python 32/32, PowerShell 2/2, Java 35/35, TS 451/451 y TSX 86/86; no equivale a cobertura de símbolos/flujo. Graphify avisó de 100 archivos de código sin símbolos en el frontend. Los Compose con etiquetas especiales y `.properties` no se estructuran; deben conservar lectura textual. Las siete sondas estáticas directas se recuperaron; las dos sondas de dependencia dinámica/herencia externa muestran límites. Las nueve consultas fueron útiles, tres tras una única desambiguación determinista por ID; se conservan los errores de ambigüedad originales. Se corrigió y reevaluó una etiqueta de la sonda de ruta del frontend sobre el grafo existente, sin cambiar la extracción.
- **Decisión:** Graphify seleccionado como ayuda para la preparación híbrida, con búsquedas y texto obligatorios para sus carencias. Mantener preparador separado del runtime, validado aquí como batch Docker/Python 3.12. Codebase-Memory sigue sin evaluar; no se atribuye una comparación inexistente. Evidencia resumida versionada: [indexer-2026-10-23.json](evidence/indexer-2026-10-23.json). Protocolo, dependencias, límites y decisión completa: [Validación del indexador](INDEXADOR.md).
- Alcance de la medición: Windows/Docker Linux amd64, una repetición final por muestra; no prueba estadística, repositorios grandes, otros hosts ni ejecución del arnés en GitHub Actions. Los contenedores y red temporales se retiraron; snapshots y resultados se conservan fuera de Git. Sin cambios en el analizador, Compose de aplicación, versiones, changelog o histórico del MVP.

**Límites de alcance:** es un arnés experimental de preparación, sin integración en la API/oficina, agentes o contratos de los siguientes bloques. No se ejecuta una evaluación de modelos ni se promete reconstrucción completa de flujos. CD sigue pendiente; versiones frontend/backend en 0.2.0, sin changelog de entrega ni referencias Git de publicación nuevas.

### Bloque 3 — Organización del núcleo y contratos

- [x] F1-07 Crear el paquete Python con `pyproject.toml`, módulos por responsabilidad y pruebas fuera del código de producción.
- [x] F1-08 Separar almacenamiento, ejecución, configuración y adaptadores; definir contratos de evidencia, estados y eventos.
- [x] F1-09 Conservar compatibilidad con informes y trabajos históricos. Preparar una resolución de rutas por identificador para permitir carpetas de resultados organizadas.

**Cierre:** pruebas relevantes existentes superadas, contratos preservados e informes históricos accesibles. Esta reorganización no cambia por sí sola el comportamiento del análisis.

**Implementación y comprobaciones del 23/10/2026:**

- Paquete `arktic_office` bajo `backend/src/`, con [pyproject.toml](../pyproject.toml) en la raíz para incluir el estándar editorial canónico sin duplicarlo. Se construye e instala como wheel en Docker, con los perfiles y recursos visuales. Las pruebas pasan a `backend/tests/` y solo se copian al target manual `tests`, no a producción. Se conservan los cuatro lanzadores de `auditor/` y sus rutas `/app`; el resto del código se importa por paquete. El runtime Hermes y su lock siguen separados; no se cambian modelos, scanners, presupuestos o versiones.
- Separadas API REST, ejecución de trabajos/consultas, JSON/almacenamiento, configuración, procesos/adaptadores, preparación, coordinación e informes. [Contratos Python](../backend/src/arktic_office/core/contracts.py) para evidencia y estados actuales, sin imponer una migración al histórico. Evento interno v1 con receptor opcional, emitido tras persistir estados de trabajo/consulta; sin bus, SSE o almacenamiento de eventos añadido. Las rutas y respuestas REST conservan sus campos.
- [RunStore](../backend/src/arktic_office/storage/runs.py) ofrece catálogo de solo lectura y resolución por ID en histórico plano y grupos anidados. Rechaza IDs inválidos, enlaces de directorio externos y duplicados ambiguos; limita profundidad/directorios. Las escrituras nuevas siguen planas y no se mueve ningún informe; la organización física queda para F1-21.
- Referencia antes de mover código: **108 pruebas correctas**. Regresión manual del paquete instalado: **111 ejecutadas, 110 correctas y 1 omitida**, en `artifacts/block3-tests-final.log`. Solo se añaden tres casos necesarios: hashes de prompt y Markdown/HTML de formatos 1–3, resolución plana/anidada sin modificar archivos y estados/eventos con un ejecutor falso. La referencia visual opcional no se distribuye en el contenedor; su comprobación queda explícitamente omitida. El primer pase detectó y corrigió únicamente una suposición de ruta de ese test opcional. El runner bloquea procesos externos y conexiones fuera de localhost, además de ejecutarse sin red ni credenciales; no se lanzaron scanners, modelos ni análisis de repositorios.
- Comprobación manual del arranque con la base existente: backend y oficina reconstruidos y `healthy`, API `/health` con versión 0.2.0, oficina y proxy de listado HTTP 200, sin trabajos ni autenticación. Proyecto temporal `arktic-ci-9c442517d6c3` retirado correctamente; log `artifacts/block3-startup.log`.
- Histórico real montado en solo lectura: 24 directorios, 19 registros legibles (18 con informe), formatos 1/2/3; **154 archivos JSON/Markdown/HTML mantienen sus hashes**. Cinco directorios incompletos siguen fuera del catálogo, como en el comportamiento anterior; no se completaron ni reescribieron. Resultado local en `artifacts/block3-history.log`.
- Por corrección del usuario, **no se amplía CI/CD**: se retiró del workflow la prueba añadida durante la implementación; `.github/` queda sin cambios. [check-backend.ps1](../scripts/check-backend.ps1) y su Compose son exclusivamente manuales. Para siguientes bloques, pruebas mínimas necesarias y ninguna ampliación de CI/CD. Detalles de organización, contratos y límites: [CORE.md](CORE.md).

**Limitaciones y entrega:** validado en Docker Linux/amd64 desde Windows, sin ejecución remota de estos cambios ni evaluación de modelos o scanners reales. No se integra aún Graphify con la API ni se conecta el contrato de eventos a la oficina. No se mueve el histórico ni se cambia su formato. Frontend, backend y paquete Python permanecen en 0.2.0; sin changelog de entrega, publicación o cierre de versión.

### Bloque 4 — Preparación híbrida

- [x] F1-10 Separar adquisición del repositorio y selección del contexto; usar la rama predeterminada real y mantener trazabilidad al commit.
- [x] F1-11 Integrar reglas locales, mapa estructural, búsquedas y lectura de fragmentos con sus posiciones originales. Declarar por separado la cobertura de scanners y la del modelo.
- [x] F1-12 Añadir exploración Hermes con herramientas restringidas, iteraciones y presupuesto acotados, eventos y cierre explícito por suficiencia o límite.

**Cierre:** recuperación de flujos representativos con evidencias verificables sin enviar todo el repositorio. Carencias, exclusiones, consumo y fallos visibles. No ejecutar el código analizado.

**Registro del Bloque 4 — 23/10/2026:** base de bloques 2–3 guardada previamente en el commit local `a6e3cee`; el Bloque 4 se registra en un commit independiente para revisión. adquisición y selección separadas; rama predeterminada real, codificada correctamente incluso con `/`, árbol y blobs ligados al commit. Recorrido híbrido opcional mediante `compose.hybrid.yaml`, con servicio Graphify independiente sobre texto adquirido y ocultado, sin credenciales, puerto publicado, ejecución del objetivo ni salida a Internet. El recorrido habitual `legacy` permanece disponible y no se ejecutan ambos automáticamente.

Reglas locales, mapa estático, búsqueda literal y fragmentos conservan posiciones originales. La adquisición híbrida admite 120 archivos/1 MB descargado; el contexto final mantiene los límites existentes. Entrada a scanners, entrada al mapa, lecturas del explorador y envíos especializados se registran por separado. Hermes solicita acciones JSON limitadas por Core, sin herramientas de agente habilitadas: máximo 8 llamadas, 180 segundos, 60000 bytes acumulados de prompts, 100 líneas por lectura. Cierres explícitos por suficiencia, insuficiencia, presupuesto o fallo técnico; eventos locales y aportaciones parciales conservadas. No se adelanta la conexión de eventos a la oficina ni el registro de modelos/skills del Bloque 5.

**Comprobaciones mínimas:** suite manual existente más dos casos esenciales; 113 ejecutadas, 112 correctas y 1 referencia visual opcional omitida en 6,799 s. Fixtures anteriores adaptados a la rama predeterminada. Integración con Graphify real dentro de Docker y respuestas GitHub/Hermes ficticias: dos flujos controlador → servicio → repositorio (Python/Java), 6 archivos representados, 15 nodos, 19 relaciones; 6 fragmentos contrastados con sus líneas, búsqueda literal y cierre tras 8 acciones. Ruta `../escape.py` rechazada con HTTP 400. Imágenes construidas, API 0.2.0/oficina/preparador saludables, oficina/proxy HTTP 200, sin trabajos ni autenticación. Red del preparador interna; proyecto y volúmenes temporales retirados. Logs locales: `artifacts/block4-tests-final.log` y `artifacts/block4-integration.log`.

**Limitaciones:** no se analizaron repositorios reales ni se ejecutaron scanners, modelos o código objetivo; no se repitieron los benchmarks del Bloque 2. La integración demuestra recuperación y restricciones, no calidad del explorador real, consumo del proveedor, cobertura de todo el repositorio, carga concurrente ni recuperación tras interrupción abrupta. Los tokens ausentes se conservan como desconocidos y OAuth sigue sin techo duro de salida. Detalle de configuración, presupuestos, trazas y conservación: [PREPARACION.md](PREPARACION.md). No se amplía CI/CD, no se modifica el histórico y se conservan versiones 0.2.0 y pins de Hermes. Entrega abierta, sin publicación ni cierre de versión.

### Bloque 5 — Coordinador, especialistas y skills

- [x] F1-13 Extraer instrucciones de agentes y skills reutilizables, documentando entradas, salidas, herramientas y requisitos de compatibilidad.
- [x] F1-14 Centralizar perfiles de modelos, razonamiento y límites; validar configuración antes de consumir modelo.
- [x] F1-15 Incorporar reparto y síntesis con IA, manteniendo especialistas de una pasada, validación de citas y aportaciones parciales.
- [x] F1-16 Hacer opcionales las capacidades específicas, como propuesta Azure, según el encargo; su ausencia no debe invalidar una evaluación que no las necesita.

**Cierre:** solo la preparación amplía evidencia mediante iteraciones. Fallos o insuficiencia de una parte no destruyen resultados válidos. Portabilidad de skills documentada sin prometer compatibilidad automática con cualquier producto.

**Registro del Bloque 5 — 23/10/2026:** instrucciones de roles y contratos extraídos a recursos instalados, con skill reutilizable y compatibilidad documentada. Registro central de perfiles para modelos, razonamiento, salida, tiempo y contexto; validación local antes de la primera llamada. Se conservan los modelos/proveedores y ajustes anteriores, sin verificar disponibilidad remota ni cambiar automáticamente de perfil.

Coordinación con IA opcional (`AUDIT_COORDINATION_MODE=ai`): una llamada de reparto restringida a archivos preparados y una síntesis de aportaciones validadas. Los especialistas siguen siendo de una pasada, sin búsquedas ni reintentos. Repartos inválidos usan la base determinista; síntesis inválidas se omiten sin borrar originales. Las citas se contrastan con el snapshot, se conserva procedencia e incertidumbre y los fallos permanecen visibles. `coordinacion.json` registra llamadas, consumo comunicado y etapas; anexos muestran la síntesis identificada. Azure se solicita mediante `AUDIT_CAPABILITIES=azure`; vacío no la exige ni penaliza su ausencia. El modo predeterminado sigue siendo determinista y no añade llamadas del coordinador, atendiendo al presupuesto disponible indicado por el usuario.

**Comprobaciones mínimas:** 116 ejecutadas, 115 correctas y 1 referencia visual opcional omitida en 6,582 s. Suite manual existente y solo tres casos nuevos sobre configuración previa al consumo, recorrido válido y conservación ante fallos; fixtures anteriores de Azure/editorial adaptados al encargo explícito. Skill validada localmente. Imágenes construidas; API 0.2.0/oficina saludables, oficina/proxy HTTP 200, sin trabajos ni autenticación; recursos temporales retirados. Se conservan los hashes de formatos históricos y del prompt de compatibilidad sin célula. Logs: `artifacts/block5-tests-final.log` y `artifacts/block5-startup.log`.

**Limitaciones:** pruebas con respuestas ficticias, sin modelos del proyecto, scanners ni análisis de repositorios reales. No se valida calidad semántica real de reparto/síntesis, coste del proveedor, disponibilidad de modelos ni recuperación tras corte. Los tokens desconocidos se conservan como tales y OAuth sigue sin techo duro de salida. Portabilidad de la skill requiere adaptar herramientas, esquema, permisos y validación; no implica compatibilidad universal. Sin ampliaciones de CI/CD, cambios del histórico, versiones o pins de Hermes. Entrega abierta. Configuración, consumo y contratos en [COORDINACION.md](COORDINACION.md).

### Bloque 6 — Oficina y consultas

- [x] F1-17 Conectar eventos reales con burbujas, indicadores de trabajo, desplazamientos, orientación e interacciones entre personajes.
- [x] F1-18 Corregir asientos, alineación y profundidad de muebles mediante comprobación visual. Evitar conversaciones o progreso ficticios.
- [x] F1-19 Representar fin, interrupción, fallo e información insuficiente; orientar al personaje al seleccionarlo y animar la consulta.
- [x] F1-20 Incorporar historial acotado por revisión y agente si se confirma esa ampliación, usando evidencias guardadas y sin relanzar el equipo.

**Cierre:** la oficina refleja el estado real, cesa su actividad al terminar y mantiene interacciones legibles. Las animaciones no consumen modelo. Las correcciones visuales independientes pueden adelantarse tras acordar el contrato de eventos.

**Registro del Bloque 6 — 24/10/2026:** actividad real proyectada desde estados persistidos de preparación, coordinación y células mediante el sondeo existente, sin otro transporte ni conversaciones ficticias. Burbujas, trabajo y reunión de síntesis ligados a esas fases. Personajes estacionados al terminar, orientación del seleccionado y ajuste de alineación/profundidad de sillas. Los estados terminales prevalecen sobre actividad intermedia obsoleta. Consulta activa animada y segundo envío bloqueado.

El usuario confirmó el historial de las últimas diez consultas por revisión y personaje: solo lectura de consultas guardadas, sin reenviar conversaciones al modelo ni relanzar el equipo. Se conservan las preguntas independientes y el caché anterior. Verificación manual con ejecutor ficticio y comprobación visual del historial, puestos y consulta. La repetición final detectó un fallo de carga de fuentes Google en Next/Turbopack; se sustituyó esa descarga por familias del sistema, sin dependencias nuevas. Reconstrucción y arranque finales correctos; aplicación del parche desde fuentes limpias y comparación de sus 21 archivos correctas. Ocho pruebas de interfaz correctas; backend: 117 ejecutadas, 116 correctas y 1 referencia visual opcional omitida en 6,832 s, mediante suite manual y un único caso nuevo de estado terminal/historial. Frontend reproducido desde fuentes limpias del pin y parche comprobado; imágenes construidas y servicios saludables. Detalle, logs y límites en [OFICINA.md](OFICINA.md).

**Limitaciones y alcance final:** no se ejecutaron revisiones de repositorios, scanners ni modelos reales. El sondeo puede omitir fases breves y no acredita calidad semántica. Sin ampliaciones de CI/CD ni cambios de versiones. Por indicación del usuario al quedar poco presupuesto, se cierra únicamente este bloque: el Bloque 7 continúa pendiente y sus adelantos quedan apartados en `artifacts/block7-deferred.patch`. La entrega sigue abierta y conserva frontend/backend 0.2.0.

### Bloque 7 — Resultados, documentación y entrega

- [x] F1-21 Organizar resultados por fecha, hora, título e identificador; distinguir informes del producto de capturas de desarrollo. Definir conservación y limpieza de snapshots e índices.
- [x] F1-22 Separar documentación humana de plantillas, esquemas y estándares usados en ejecución; actualizar enlaces e instrucciones.
- [ ] F1-23 Evaluar utilidad, citas, insuficiencia, consumo y tiempos con muestras representativas. Conservar la base de CI sin ampliarla; usar pruebas manuales mínimas necesarias. Las evaluaciones reales serán explícitas y presupuestadas.
- [ ] F1-24 Cerrar la entrega con aceptación humana, manifiesto de versiones, changelog y referencias Git según el flujo de publicación acordado.

**Cierre:** cada informe identifica código revisado, cobertura, modelos, recursos versionados y consumo disponible. La entrega distingue lo medido de lo pendiente y conserva acceso al histórico.

**Registro del Bloque 7 — 24/10/2026:** retomado por autorización del usuario tras el cierre del Bloque 6. Resultados nuevos por fecha/hora UTC, repositorio e ID; catálogo compatible con el histórico sin migración, con rechazo de enlaces y duplicados. Manifiesto por revisión con commit, perfiles, hashes de fuentes/recursos y consumo disponible. Conservación manual de informes y separación de temporales/capturas descritas en [RESULTADOS.md](RESULTADOS.md). Estándar editorial instalado dentro del paquete; bytes y hash anteriores conservados. Documentación y enlaces actualizados.

**Comprobaciones:** 118 pruebas de backend ejecutadas, 117 correctas y una referencia visual opcional omitida en 7,081 s. Imagen del backend construida. Logs locales `artifacts/block7-tests.log` y `artifacts/block7-image.log`. Se desactivaron reintentos y recuperación internos del runtime Hermes fijado para mantener una tentativa por invocación; no se cambian versiones ni pins. Construcción y arranque finales correctos con `scripts/check-startup.ps1`: API y oficina saludables, HTTP 200 en oficina/proxy/API, sin trabajos, informes ni autenticación, red interna y recursos temporales retirados; log `artifacts/block7-startup.log`. Evidencia resumida versionada en [block7-2026-10-24.json](evidence/block7-2026-10-24.json).

**F1-23 parcialmente pendiente:** el usuario autorizó hasta cinco llamadas reales con bookingApi, sin scanners. Sobre el snapshot del Bloque 2, commit `c0d247e3226d77a83471c7a1b32afdb0981eb7f1`, se seleccionaron 24 archivos. Cuatro invocaciones en 27,654 s: reparto y Seguridad fallaron por sesión no válida; Arquitectura e Inventario por cuota/límite. Síntesis omitida al no haber contenido válido. Consumo desconocido, sin nuevos intentos automáticos. Sin ejecución del objetivo, sus dependencias o tests. Los casos ficticios comprueban citas, insuficiencia y conservación de parciales; no validan utilidad semántica real. Ledger y trazas excluidos de Git en la ruta referida por `artifacts/block7-evaluation-path.txt`.

**F1-24 abierta:** manifiesto [release.json](../release.json) de candidata para revisión y changelog sin publicar preparados. El PR no cierra aceptación ni versión. No se amplía CI/CD; frontend, backend y paquete Python permanecen en 0.2.0. Pendientes validación semántica tras resolver sesión/cuota, aceptación humana, decisión de versión y merge del usuario. Sin etiquetas, release ni publicación de imágenes.

### Bloque 8 — Afinado (finetuning) de configuración y resultados

Este bloque afina configuración, instrucciones y utilidad observada; no implica entrenar pesos de un modelo. Primero se prueba el funcionamiento con perfiles mínimos, sin buscar todavía el resultado óptimo.

- [ ] F1-25 Resolver y comprobar sesión/cuota con evaluación real acotada y presupuesto explícito, sin scanners salvo autorización independiente. Completar la validación semántica pendiente de F1-23.
- [ ] F1-26 Acordar y elevar modelos/razonamiento por rol para analizar un repositorio real; conservar el perfil económico para pruebas funcionales.
- [ ] F1-27 Evaluar utilidad, citas, insuficiencia, cobertura, llamadas, tiempos y consumo comunicado. Afinar prompts, selección y loops según fallos observados, con cambios pequeños y comprobaciones mínimas.
- [ ] F1-28 Registrar configuración final, límites y resultados; aceptación humana y decisión de versión para completar F1-24. El usuario conserva el merge.

**Preparación del 24/10/2026:** `AUDIT_PREPARATION_MAX_LOOPS` añade pasadas a la inicial: 0 → 1 llamada, 1 → 2, 2 → 3, 3 → 4; predeterminado 1, rango 0–20. Validación previa al consumo; tiempo/contexto mantienen sus techos. El explorador puede cerrar antes y al agotar llamadas conserva evidencia parcial. No repite el equipo ni amplía reparto/síntesis. Todos los roles de pruebas heredan el modelo común y `low`; se retira la elevación de Seguridad del ejemplo y de la configuración local. Esto no resuelve por sí solo los errores anteriores de sesión/cuota. CI/CD y versiones conservados. Comprobaciones: 119 pruebas ejecutadas, 118 correctas y una referencia visual opcional omitida en 6,706 s; un único caso nuevo comprueba 0/1/2/3 loops y cierre anticipado, y el caso existente de configuración inválida cubre límites erróneos antes de consumir modelo. Log local `artifacts/preparation-loops-tests.log`. Imágenes reconstruidas y preparación híbrida activada localmente sin trabajos activos; perfiles efectivos de los seis roles comprobados como `gpt-6-luna`/`low`, con dos llamadas máximas de preparación. Un bloqueo de metadatos temporales de Compose en Windows obligó a repetir el build del backend directamente con Docker, correctamente. API, preparador y oficina saludables; HTTP de oficina y proxy comprobados. Sin nuevas llamadas reales, scanners ni ampliación de CI/CD. La CI del PR #3 sobre el commit anterior `61d4dcb` había finalizado correctamente; la actualización se validará en su propio commit. Evidencia resumida: [preparation-loops-2026-10-24.json](evidence/preparation-loops-2026-10-24.json).

**Verificación posterior de sesión y runtime — 24/10/2026:** el usuario autorizó una sesión OAuth nueva. Se comprobó que la anterior devolvía 401 y seguía siendo elegida primero; se retiró únicamente esa entrada revocada. La nueva sesión y el modelo configurado responden correctamente al catálogo (HTTP 200). Se corrigió la clasificación de errores OAuth estructurados y se excluyó el contenido de prompts/conversaciones de esa clasificación, para evitar falsos errores de autenticación/cuota por texto del repositorio. Regresión: 119 ejecutadas, 118 correctas y una referencia visual opcional omitida en 6,556 s. Imágenes reconstruidas y API/oficina/preparador saludables, oficina y proxy HTTP 200. Oficina disponible en `http://127.0.0.1:3000/office`; la pestaña anterior apuntaba a 3100, donde no había servicio.

Se usó la quinta y última llamada autorizada con el snapshot fijado de bookingApi: Inventario, `gpt-6-luna`/`low`, respuesta y citas validadas, dos observaciones confirmadas, sin avisos; 12,24 s. Consumo comunicado: 9685 tokens de entrada, 418 de salida, 0 de razonamiento y 10103 totales; una llamada API. No se reintentó ni se ejecutaron scanners o código objetivo. Las cuatro llamadas fallidas anteriores conservan su registro y consumo desconocido. Presupuesto de cinco invocaciones agotado; no se programan más. Falta evaluación completa del equipo y calidad semántica del Bloque 8: una célula válida no cierra F1-23 ni F1-24. Evidencia: [runtime-verification-2026-10-24.json](evidence/runtime-verification-2026-10-24.json). Logs y respuesta locales en `artifacts/runtime-errors-*.log` y `artifacts/runtime-verification/`.

## Estructura implementada

```text
arktic-office/
├── release.json                 # Candidata, entrega abierta
├── backend/
│   ├── src/arktic_office/
│   │   ├── preparation/ coordination/ reporting/ storage/ adapters/
│   │   └── resources/           # profiles, skills, editorial, assets
│   └── tests/
├── docs/                        # Documentación humana
├── docker/                      # Imágenes y parche del frontend fijado
├── .github/workflows/           # Base del Bloque 1 conservada
└── artifacts/                   # Evidencia de desarrollo; excluida de Git
```

Los resultados del producto se conservan aparte en `/reports/AAAA-MM-DD/HHMMSS-repositorio/id/`; el catálogo admite los antiguos directorios planos. El frontend sigue distribuyéndose como parche reproducible sobre Hermes3D fijado. No se copia `vendor/` al repositorio. Política de temporales e histórico en [RESULTADOS.md](RESULTADOS.md).

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
- Base local revisada, con rutas actualizadas tras el Bloque 3: [preparación](../backend/src/arktic_office/preparation/repository.py), [coordinación](../backend/src/arktic_office/coordination/team.py), [adaptador Hermes](../backend/src/arktic_office/adapters/hermes_runtime.py), [API](../backend/src/arktic_office/api/server.py), [consultas](../backend/src/arktic_office/coordination/questions.py), [validación e informes](../backend/src/arktic_office/reporting/reports.py), [Compose](../compose.yaml) y [parche de la oficina](../docker/hermes3d-local-demo.patch).

## Registro de seguimiento

| Fecha | Cambio | Estado de implementación |
|---|---|---|
| 23/10/2026 | Plan registrado por petición del usuario, separado del MVP 0.2.0; alcance, recomendaciones, tareas y comprobaciones pendientes documentados | Ninguna tarea de la Fase 1 implementada en este registro |
| 23/10/2026 | Bloque 1 F1-01 a F1-03 implementado: recuperación por commit, CI mínima y arranque aislado sin modelos; evidencia y limitaciones en el bloque | Comprobaciones local y remota satisfactorias; entrega abierta, versiones 0.2.0 conservadas |
| 23/10/2026 | Bloque 2 F1-04 a F1-06: Graphify fijado, recuperación/extracción/consulta Docker, tres muestras autorizadas y decisión basada en métricas | Comprobado localmente sin scanners ni modelos; Graphify seleccionado con límites; bloques siguientes pendientes y versiones 0.2.0 conservadas |
| 23/10/2026 | Bloque 3 F1-07 a F1-09: paquete instalado, responsabilidades y contratos separados, IDs independientes del layout e histórico conservado | Regresión y arranque manuales correctos; 154 archivos históricos sin cambios; CI/CD sin ampliar por petición del usuario y versiones 0.2.0 conservadas |

| 24/10/2026 | Bloques 4–6 implementados y comprobados; Bloque 7 con layout, manifiestos y recursos separados | Candidata para PR; F1-23 parcial por sesión/cuota y F1-24 pendiente de aceptación; versiones conservadas |
