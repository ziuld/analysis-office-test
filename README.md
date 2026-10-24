# Arktic Office

Oficina virtual 2D para entender una aplicación a partir de su repositorio de GitHub y preparar una evaluación técnica humana. Reutiliza la interfaz de Hermes3D y el runtime de Hermes Agent con tres células: Seguridad, Arquitectura e Inventario.

El MVP entrega un informe con evidencia del código, indicios por confirmar y preguntas pendientes. Ayuda al responsable técnico a valorar seguridad, operación y una posible migración a VPS o Kubernetes. La decisión de despliegue corresponde al arquitecto.

Versiones propias: **frontend 0.2.0** y **backend 0.2.0**, gestionadas de forma independiente en `FRONTEND_VERSION` y `BACKEND_VERSION`. Cambios de cada componente: [CHANGELOG.md](CHANGELOG.md). Los archivos `HERMES3D_VERSION` y `HERMES_AGENT_VERSION` fijan las dependencias originales, no la versión de Arktic Office.

## Empezar

- **Otro ordenador:** [Inicio rápido](docs/INICIO_RAPIDO.md), desde los requisitos hasta la primera revisión.
- **Cómo trabaja el equipo:** [Flujo de agentes](docs/WORKFLOW.md).
- **Configuración, operación y pruebas:** [Operación](docs/OPERACION.md).
- **Reporte visual, controles y límites:** [Seguridad](docs/SEGURIDAD.md).
- **Cómo se redacta el informe:** [Estándar de comunicación compartido](docs/ESTANDAR_COMUNICACION_INFORMES.md).
- **Preparar la subida y mantener las versiones:** [Repositorio y reproducción](docs/REPOSITORIO.md).
- **MVP actual e histórico:** [PLAN_MVP.md](PLAN_MVP.md), con el alcance y las verificaciones de la entrega 0.2.0.
- **Siguiente evolución:** [Plan de Fase 1](docs/PLAN_FASE_1.md), con objetivos, tareas, criterios de cierre y decisiones pendientes. El Bloque 1 incorpora reproducción y CI; el Bloque 2 prueba el indexador de forma independiente. Los siguientes siguen pendientes.
- **Experimento del Bloque 2:** [Validación del indexador](docs/INDEXADOR.md), con recuperación y extracción estructural de muestras dentro de Docker, sin modelos ni ejecución de las aplicaciones.
- **Núcleo del Bloque 3:** [Paquete Python y compatibilidad](docs/CORE.md), con pruebas manuales mínimas y sin ampliar CI/CD.

Con las dependencias recuperadas, `.env` configurado y la sesión del modelo autorizada:

```powershell
docker compose up -d --build --wait
```

Abrir [la oficina local](http://localhost:3000/office), introducir una URL como `https://github.com/ziuld/bookingApi` y pulsar **Iniciar revisión**. Después, **Leer informe**, **Descargar informe** o pulsar un personaje para preguntar sobre el resultado.

## Qué incluye

- Una URL como entrada. Resuelve la rama predeterminada real de GitHub y fija su commit antes de seleccionar contexto.
- Lectura estática acotada: por defecto, 24 archivos / 120 KB; Seguridad recibe hasta 12 / 64 KB, las otras células hasta 6 / 24 KB.
- Tres revisiones secuenciales y consolidación mediante código. Estados reales en la oficina, resultados parciales y errores visibles.
- Reporte visual de seguridad con indicadores de gravedad, certeza separada, acciones, cobertura e inventario; descarga Markdown e impresión/PDF. Evidencias enlazadas al commit revisado.
- Gitleaks para posibles secretos y OSV-Scanner para dependencias, sobre la descarga acotada y sin ejecutar el proyecto.
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

La configuración propone `openai-codex` mediante OAuth en Hermes: Seguridad con `gpt-6.1-sol` / `medium`, el resto con `gpt-6-luna` / `low`. También existe el modo API con facturación independiente. La sesión del modelo se configura en cada instalación; no viene incluida al clonar. Alcance y comprobaciones en [Seguridad](docs/SEGURIDAD.md).

El recorrido habitual `legacy` usa tres llamadas al modelo; cada pregunta añade una llamada al personaje elegido. El modo opcional de [coordinación con IA](docs/COORDINACION.md) añade hasta dos llamadas para reparto y síntesis; conserva los originales y usa la base determinista si falla. Azure se genera solo cuando se solicita como capacidad del encargo. No hay reintentos ni escalado de modelo automáticos. Con el backend Codex OAuth de esta versión, el límite de salida configurado no constituye un techo duro de tokens. El modo híbrido opcional añade hasta ocho llamadas acotadas de preparación: [Preparación híbrida](docs/PREPARACION.md). Detalles en [Operación](docs/OPERACION.md).

## Datos y despliegue local

Los archivos seleccionados se envían al proveedor del modelo. La ocultación de posibles credenciales es heurística. Las evidencias y consultas pueden contener código o información del repositorio: se guardan localmente y no se publican con el proyecto.

Solo se publica `127.0.0.1:3000`. El analizador funciona sin privilegios, sin socket Docker y sin puerto público. Es un MVP de uso local, sin autenticación corporativa; una publicación en red requiere trabajo adicional. La infraestructura de Azure DevOps/Kubernetes queda fuera de esta versión.

## Estado y proyectos originales

Las siete fases se cerraron con un piloto sobre `ziuld/bookingApi` y validación del usuario. La iniciativa empresarial original sigue pendiente de disponer de repositorio. El detalle verificable está en [el plan](PLAN_MVP.md).

Basado en [Hermes3D](https://github.com/iamlukethedev/Hermes3D) y [Hermes Agent](https://github.com/NousResearch/hermes-agent). Versiones y atribuciones: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
