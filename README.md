# Arktic Office

Oficina virtual 2D para entender una aplicación a partir de su repositorio de GitHub o de una captura Git local. Reutiliza Hermes3D y Hermes Agent con coordinación centralizada por Akira y siete especialistas secuenciales: Inventario, Arquitectura, Datos, Seguridad, Seguridad frontend, Seguridad backend y Devops.

El MVP entrega un informe con evidencia del código, indicios por confirmar y preguntas pendientes. Ayuda al responsable técnico a valorar seguridad, operación y una posible migración a VPS o Kubernetes. La decisión de despliegue corresponde al arquitecto.

Versiones propias: **frontend 0.3.0** y **backend 0.3.0**, gestionadas de forma independiente en `FRONTEND_VERSION` y `BACKEND_VERSION`. Cambios de cada componente: [CHANGELOG.md](CHANGELOG.md). Los archivos `HERMES3D_VERSION` y `HERMES_AGENT_VERSION` fijan las dependencias originales, no la versión de Arktic Office.

**Extensión de fase 2 (28/10/2026):** las nuevas revisiones incorporan [40 preguntas repartidas entre los especialistas y el coordinador](docs/EXTENSION_FASE_2.md). El HTML muestra el resumen, las respuestas con fuentes y los resultados deterministas completos en anexos, incluidos Graphify y herramientas no evaluadas. Los resultados históricos se conservan. Su evolución se recoge únicamente en el plan vigente.

## Plan vigente e histórico

El único plan vigente es el [plan de coordinación centralizada](docs/PLAN_COORDINACION_CENTRALIZADA.md). Su implementación local incorpora ejecución secuencial, información compartida en Core/SQLite, el nuevo reparto de las mismas 40 preguntas y panel compacto. Los resultados comprobados y los pendientes se recogen en el [cierre de implementación](docs/RESULTADOS_COORDINACION_2026-10-30.md). El [cierre estable del 31/10](docs/CIERRE_COORDINACION_2026-10-31.md) conserva la comparación entre tres y siete especialistas, los informes y las propuestas pendientes sin aplicar. Arquitectura y Datos siguen separados. La comprobación visual con Chromium está aplazada por indicación del usuario.

| Documento | Estado |
|---|---|
| [Coordinación centralizada](docs/PLAN_COORDINACION_CENTRALIZADA.md) | Único plan vigente; estado de implementación y comprobaciones por bloque |
| [Cierre estable](docs/CIERRE_COORDINACION_2026-10-31.md) | Estado actual, resultados comparados, archivo de informes y pendientes |
| [Cierre de referencia](docs/CIERRE_FASE_2_2026-10-30.md) | Referencia publicada en el commit 76abf0f, con validaciones y límites |
| [MVP](PLAN_MVP.md), [Fase 1](docs/PLAN_FASE_1.md), [Fase 2](docs/PLAN_FASE_2.md) | Histórico cerrado; no son instrucciones de continuación |

## Empezar

- **Otro ordenador:** [Inicio rápido](docs/INICIO_RAPIDO.md), desde los requisitos hasta la primera revisión.
- **Repositorio local y rama activa, sin acceso al remoto:** [Análisis local](docs/ANALISIS_LOCAL.md).
- **Cómo trabaja el equipo:** [Flujo de agentes](docs/WORKFLOW.md).
- **Configuración, operación y pruebas:** [Operación](docs/OPERACION.md).
- **Reporte visual, controles y límites:** [Seguridad](docs/SEGURIDAD.md).
- **Cómo se redacta el informe:** [Estándar de comunicación compartido](docs/ESTANDAR_COMUNICACION_INFORMES.md).
- **Preparar la subida y mantener las versiones:** [Repositorio y reproducción](docs/REPOSITORIO.md).
- **MVP actual e histórico:** [PLAN_MVP.md](PLAN_MVP.md), con el alcance y las verificaciones de la entrega 0.2.0.
- **Cierre actual y siguiente trabajo:** [cierre publicado](docs/CIERRE_FASE_2_2026-10-30.md) y [único plan vigente](docs/PLAN_COORDINACION_CENTRALIZADA.md). Las fases anteriores conservan sus evidencias históricas.

- **Experimento del Bloque 2:** [Validación del indexador](docs/INDEXADOR.md), con recuperación y extracción estructural de muestras dentro de Docker, sin modelos ni ejecución de las aplicaciones.
- **Núcleo del Bloque 3:** [Paquete Python y compatibilidad](docs/CORE.md), con pruebas manuales mínimas y sin ampliar CI/CD.

La configuración actual tiene siete especialistas y Akira, ejecutados secuencialmente. El equipo anterior de tres especialistas se conserva como referencia comparativa, no como configuración activa.

Con las dependencias recuperadas, `.env` configurado y la sesión del modelo autorizada:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --build --wait
```

Abrir [la oficina local](http://localhost:3000/office), introducir una URL como `https://github.com/ziuld/bookingApi` y pulsar **Iniciar revisión**. Después, **Leer informe**, **Descargar informe** o pulsar un personaje para preguntar sobre el resultado.

## Qué incluye

- Una URL como entrada. Resuelve la rama predeterminada real de GitHub y fija su commit antes de seleccionar contexto.
- Snapshot íntegro verificado al commit, Graphify y escáneres sobre la entrada compatible. Los especialistas consultan mapas de respuestas/herramientas y recuperan código o resultados pertinentes dentro de su presupuesto, sin precargar informes completos.
- Siete especialistas secuenciales con reparto y síntesis de Akira. Core guarda tareas, respuestas y procedencia en SQLite/archivos; la oficina distingue ejecución, cobertura y errores.
- Reporte visual de seguridad con indicadores de gravedad, certeza separada, acciones, cobertura e inventario; descarga Markdown e impresión/PDF. Evidencias enlazadas al commit revisado.
- Gitleaks, OSV-Scanner y Semgrep sobre la entrada compatible del snapshot, sin ejecutar el proyecto. Resultados consultables por herramienta, filtro y página; Graphify y búsqueda directa siguen disponibles.
- Consultas independientes al coordinador o a una célula, usando únicamente resultados y evidencia guardados.
- Propuesta DevOps Azure preliminar de Arquitectura: opción sencilla, motivos, supuestos, servicios, entrega y validaciones.
- [Ejemplo ficticio sin agentes](examples/README.md), con consultas bloqueadas para evitar consumo de tokens.

No ejecuta la aplicación analizada, instala sus dependencias, lanza sus tests ni realiza despliegues. La cobertura es parcial: completar las tareas de los especialistas no acredita que el proyecto sea seguro ni que todo su código se haya revisado. CPU, memoria, capacidad o recuperación quedan como desconocidos si no hay evidencia suficiente.

## Arquitectura y estructura

```text
Navegador → office (localhost:3000) → audit-api (red interna)
                                      ├─ GitHub: lectura del código
                                      ├─ Hermes Agent: Akira + siete especialistas + consultas
                                      └─ reports/: evidencia e informes
```

| Ruta | Contenido |
|---|---|
| `backend/src/arktic_office/` | Paquete Python: API, ejecución, almacenamiento, preparación, coordinación, adaptadores e informes |
| `backend/tests/` | Pruebas manuales fuera de la imagen de producción |
| `auditor/` | Lanzadores de compatibilidad para las rutas Docker actuales |
| `compose.yaml` | Servicios, red, volúmenes y límites de contenedores |
| `docker/` | Dockerfiles y parche de Hermes3D con la oficina e integración local |
| `HERMES3D_VERSION`, `HERMES_AGENT_VERSION` | Commits fijados de los proyectos originales |
| `.env.example` | Configuración de referencia sin credenciales |
| `docs/` | Guías de instalación, flujo, operación y publicación |
| `PLAN_MVP.md` | Objetivo, fases y comprobaciones del MVP |
| `docs/PLAN_COORDINACION_CENTRALIZADA.md` | Único plan vigente: decisiones, estado, propuestas pendientes y oficina |
| `docs/PLAN_FASE_1.md` | Cierre histórico y evidencias de la base integrada |
| `vendor/` | Fuentes recuperadas de Hermes; se reconstruyen y no se suben a este repositorio |
| `reports/`, `artifacts/` | Datos y capturas locales, excluidos de Git |

## Acceso y coste

La plantilla configura `openai-codex`, `gpt-6.1-sol` y esfuerzo `medium`, como las pruebas comparadas. El proveedor, modelo y límites se definen en `.env`; no hay aumentos automáticos. También existe el modo API con facturación independiente. La sesión se configura en cada instalación y no viene incluida al clonar. Alcance y comprobaciones en [Seguridad](docs/SEGURIDAD.md).

El recorrido híbrido prepara el snapshot y grafo sin modelos. Con coordinación IA hay dos etapas de Akira y hasta 29 llamadas de especialistas, sujetas al techo global de 31; una tarea puede cerrar antes. Con la salida configurada de 8.000 tokens, Core reserva como máximo 244.000 tokens de salida, 8 MB de contexto acumulado y 7.440 segundos por revisión. Los límites se pueden reducir; la reserva no es un corte remoto exacto ni una cuota monetaria. Cada consulta posterior se encola: una pregunta ya guardada se sirve desde Core sin llamar al modelo; otras consultas usan el perfil configurado y la misma exclusión de tareas simultáneas. No hay escalado automático ni reintentos de proveedor. Configuración: [coordinación](docs/COORDINACION.md) y [plan vigente](docs/PLAN_COORDINACION_CENTRALIZADA.md). `legacy` conserva un recorrido parcial de compatibilidad.

## Datos y despliegue local

Los archivos seleccionados se envían al proveedor configurado, sin ocultación del contenido por decisión del usuario. Las capturas de código, respuestas crudas, consultas, SQLite, cachés y sesiones permanecen locales. Este cierre archiva por autorización expresa seis informes renderizados y métricas comparativas en [docs/evidence](docs/evidence/agent-comparison-2026-10-31/README.md); `reports/`, `artifacts/` y `.env` siguen fuera de Git.

Solo se publica `127.0.0.1:3000`. El analizador funciona sin privilegios, sin socket Docker y sin puerto público. Es un MVP de uso local, sin autenticación corporativa; una publicación en red requiere trabajo adicional. La infraestructura de Azure DevOps/Kubernetes queda fuera de esta versión.

## Estado y proyectos originales

La base MVP se validó con `ziuld/bookingApi`. Las comparaciones posteriores sobre la captura local del proyecto de referencia se conservan en el [cierre estable](docs/CIERRE_COORDINACION_2026-10-31.md). La implementación es funcional, pero la cobertura completa y la superioridad de siete especialistas no están demostradas. El MVP se conserva como [histórico](PLAN_MVP.md).

Basado en [Hermes3D](https://github.com/iamlukethedev/Hermes3D) y [Hermes Agent](https://github.com/NousResearch/hermes-agent). Versiones y atribuciones: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
