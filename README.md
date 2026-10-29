# Arktic Office

Oficina virtual 2D para entender una aplicación a partir de su repositorio de GitHub y preparar una evaluación técnica humana. Reutiliza la interfaz de Hermes3D y el runtime de Hermes Agent con tres células: Seguridad, Arquitectura e Inventario.

El MVP entrega un informe con evidencia del código, indicios por confirmar y preguntas pendientes. Ayuda al responsable técnico a valorar seguridad, operación y una posible migración a VPS o Kubernetes. La decisión de despliegue corresponde al arquitecto.

Versiones propias: **frontend 0.3.0** y **backend 0.3.0**, gestionadas de forma independiente en `FRONTEND_VERSION` y `BACKEND_VERSION`. Cambios de cada componente: [CHANGELOG.md](CHANGELOG.md). Los archivos `HERMES3D_VERSION` y `HERMES_AGENT_VERSION` fijan las dependencias originales, no la versión de Arktic Office.

**Extensión de fase 2 (28/10/2026):** las nuevas revisiones incorporan [40 preguntas repartidas entre los especialistas y el coordinador](docs/EXTENSION_FASE_2.md). El HTML muestra el resumen, las respuestas con fuentes y los resultados deterministas completos en anexos, incluidos Graphify y herramientas no evaluadas. Los resultados históricos se conservan. Esta extensión precede a implementar fase 3.

## Planes del proyecto

Hay cuatro planes canónicos, incluido el histórico. Las guías de `docs/` describen la operación; no añaden roadmaps independientes.

| Plan | Estado | Alcance |
|---|---|---|
| [MVP](PLAN_MVP.md) | Cerrado, 0.2.0 | Alcance e histórico inicial |
| [Fase 1](docs/PLAN_FASE_1.md) | Cerrada y aceptada, 0.3.0 | Base integrada y límites aceptados |
| [Fase 2](docs/PLAN_FASE_2.md) | Cerrada el 28/10/2026 sin alcanzar la calidad esperada | Avances funcionales y evidencias conservados; pendientes sustituidos por Fase 3 |
| [Fase 3](docs/PLAN_FASE_3.md) | Abierta en planificación; implementación pendiente | Herramientas deterministas, agentes reutilizables por preguntas, orquestador e informe descriptivo con anexos |

## Empezar

- **Otro ordenador:** [Inicio rápido](docs/INICIO_RAPIDO.md), desde los requisitos hasta la primera revisión.
- **Repositorio local y rama activa, sin acceso al remoto:** [Análisis local](docs/ANALISIS_LOCAL.md).
- **Cómo trabaja el equipo:** [Flujo de agentes](docs/WORKFLOW.md).
- **Configuración, operación y pruebas:** [Operación](docs/OPERACION.md).
- **Reporte visual, controles y límites:** [Seguridad](docs/SEGURIDAD.md).
- **Cómo se redacta el informe:** [Estándar de comunicación compartido](docs/ESTANDAR_COMUNICACION_INFORMES.md).
- **Preparar la subida y mantener las versiones:** [Repositorio y reproducción](docs/REPOSITORIO.md).
- **MVP actual e histórico:** [PLAN_MVP.md](PLAN_MVP.md), con el alcance y las verificaciones de la entrega 0.2.0.
- **Fase 1 cerrada (0.3.0):** [alcance, aceptación y evidencias](docs/PLAN_FASE_1.md). **Fase 2 cerrada sin alcanzar la calidad esperada:** [histórico y cierre](docs/PLAN_FASE_2.md). **Fase 3 vigente:** [plan](docs/PLAN_FASE_3.md). Primer trabajo en Arktic: revisar las herramientas deterministas. Los agentes se desarrollarán en un repositorio externo: [prompt de contexto y tabla](docs/PROMPT_AGENTES_REUTILIZABLES.md).

- **Experimento del Bloque 2:** [Validación del indexador](docs/INDEXADOR.md), con recuperación y extracción estructural de muestras dentro de Docker, sin modelos ni ejecución de las aplicaciones.
- **Núcleo del Bloque 3:** [Paquete Python y compatibilidad](docs/CORE.md), con pruebas manuales mínimas y sin ampliar CI/CD.

El equipo de tres células y el informe descritos a continuación corresponden al funcionamiento actual. La Fase 3 documenta el diseño objetivo; sus nuevos agentes y reglas de informe todavía no están implementados.

Con las dependencias recuperadas, `.env` configurado y la sesión del modelo autorizada:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --build --wait
```

Abrir [la oficina local](http://localhost:3000/office), introducir una URL como `https://github.com/ziuld/bookingApi` y pulsar **Iniciar revisión**. Después, **Leer informe**, **Descargar informe** o pulsar un personaje para preguntar sobre el resultado.

## Qué incluye

- Una URL como entrada. Resuelve la rama predeterminada real de GitHub y fija su commit antes de seleccionar contexto.
- Snapshot íntegro verificado al commit, mapas y scanners sobre todo el conjunto compatible. Contexto inicial de modelos acotado a 24 archivos / 120 KB; Seguridad recibe hasta 12 / 64 KB, las otras células hasta 6 / 24 KB.
- Tres revisiones secuenciales y consolidación mediante código. Estados reales en la oficina, resultados parciales y errores visibles.
- Reporte visual de seguridad con indicadores de gravedad, certeza separada, acciones, cobertura e inventario; descarga Markdown e impresión/PDF. Evidencias enlazadas al commit revisado.
- Gitleaks para posibles secretos y OSV-Scanner para dependencias, sobre todo el input compatible del snapshot y sin ejecutar el proyecto.
- Consultas independientes al coordinador o a una célula, usando únicamente resultados y evidencia guardados.
- Propuesta DevOps Azure preliminar de Arquitectura: opción sencilla, motivos, supuestos, servicios, entrega y validaciones.
- [Ejemplo ficticio sin agentes](examples/README.md), con consultas bloqueadas para evitar consumo de tokens.

No ejecuta la aplicación analizada, instala sus dependencias, lanza sus tests ni realiza despliegues. La cobertura es parcial: completar las tres células no acredita que el proyecto sea seguro ni que todo su código se haya revisado. CPU, memoria, capacidad o recuperación quedan como desconocidos si no hay evidencia suficiente.

## Arquitectura y estructura

```text
Navegador → office (localhost:3000) → audit-api (red interna)
                                      ├─ GitHub: lectura del código
                                      ├─ Hermes Agent: tres células + consultas
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
| `docs/PLAN_FASE_1.md` | Plan separado de la siguiente evolución; trabajo pendiente y decisiones por validar |
| `vendor/` | Fuentes recuperadas de Hermes; se reconstruyen y no se suben a este repositorio |
| `reports/`, `artifacts/` | Datos y capturas locales, excluidos de Git |

## Acceso y coste

La configuración propone `openai-codex` mediante OAuth en Hermes: todos los roles con `gpt-6-luna` / `low` para pruebas funcionales económicas; el afinado posterior se acuerda en el Bloque 9. También existe el modo API con facturación independiente. La sesión del modelo se configura en cada instalación; no viene incluida al clonar. Alcance y comprobaciones en [Seguridad](docs/SEGURIDAD.md).

El recorrido híbrido actual prepara el snapshot y grafo sin modelos. Con coordinación IA usa cinco llamadas de base (reparto, tres especialistas y síntesis); permite una consulta local adicional por agente, configurable 0/1, con su llamada para finalizar. El perfil de prueba admite hasta siete llamadas; habilitando todos los extras, hasta nueve. Las omisiones justificadas reducen ese número. Cada pregunta posterior añade una llamada independiente. No hay escalado automático de modelos ni reintentos de proveedor. El límite de salida Codex OAuth no es un techo duro de tokens. Configuración y limitaciones: [preparación completa](docs/PREPARACION.md) y [coordinación](docs/COORDINACION.md). `legacy` permanece disponible expresamente como recorrido parcial de compatibilidad.

## Datos y despliegue local

Los archivos seleccionados se envían al proveedor del modelo. La ocultación de posibles credenciales es heurística. Las evidencias y consultas pueden contener código o información del repositorio: se guardan localmente y no se publican con el proyecto.

Solo se publica `127.0.0.1:3000`. El analizador funciona sin privilegios, sin socket Docker y sin puerto público. Es un MVP de uso local, sin autenticación corporativa; una publicación en red requiere trabajo adicional. La infraestructura de Azure DevOps/Kubernetes queda fuera de esta versión.

## Estado y proyectos originales

Las siete fases se cerraron con un piloto sobre `ziuld/bookingApi` y validación del usuario. La iniciativa empresarial original sigue pendiente de disponer de repositorio. El detalle verificable está en [el plan](PLAN_MVP.md).

Basado en [Hermes3D](https://github.com/iamlukethedev/Hermes3D) y [Hermes Agent](https://github.com/NousResearch/hermes-agent). Versiones y atribuciones: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
