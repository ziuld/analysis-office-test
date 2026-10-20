# Arktic Office

Oficina virtual 2D para entender una aplicación a partir de su repositorio de GitHub y preparar una evaluación técnica humana. Reutiliza la interfaz de Hermes3D y el runtime de Hermes Agent con tres células: Seguridad, Arquitectura e Inventario.

El MVP entrega un informe con evidencia del código, indicios por confirmar y preguntas pendientes. Ayuda al responsable técnico a valorar seguridad, operación y una posible migración a VPS o Kubernetes. La decisión de despliegue corresponde al arquitecto.

## Empezar

- **Otro ordenador:** [Inicio rápido](docs/INICIO_RAPIDO.md), desde los requisitos hasta la primera revisión.
- **Cómo trabaja el equipo:** [Flujo de agentes](docs/WORKFLOW.md).
- **Configuración, operación y pruebas:** [Operación](docs/OPERACION.md).
- **Preparar la subida y mantener las versiones:** [Repositorio y reproducción](docs/REPOSITORIO.md).
- **Alcance y seguimiento:** [PLAN_MVP.md](PLAN_MVP.md), único documento de planificación.

Con las dependencias recuperadas, `.env` configurado y la sesión del modelo autorizada:

```powershell
docker compose up -d --build --wait
```

Abrir [la oficina local](http://localhost:3000/office), introducir una URL como `https://github.com/ziuld/bookingApi` y pulsar **Iniciar revisión**. Después, **Leer informe**, **Descargar informe** o pulsar un personaje para preguntar sobre el resultado.

## Qué incluye

- Una URL como entrada. Busca `main` y, solo si no existe, utiliza `master`; si faltan ambas, informa del error. Guarda rama y commit.
- Lectura estática acotada: por defecto, hasta 12 archivos y 48 KB; cada célula recibe hasta 6 archivos y 24 KB.
- Tres revisiones secuenciales y consolidación mediante código. Estados reales en la oficina, resultados parciales y errores visibles.
- Un `informe.md` con contexto, resumen, construcción, puntos de atención, operación, migración y alcance. Evidencias enlazadas al commit revisado.
- Consultas independientes al coordinador o a una célula, usando únicamente resultados y evidencia guardados.

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
| `auditor/` | Lectura de GitHub, distribución, validación de citas, informe, consultas, API y pruebas |
| `compose.yaml` | Servicios, red, volúmenes y límites de contenedores |
| `docker/` | Dockerfiles y parche de Hermes3D con la oficina e integración local |
| `HERMES3D_VERSION`, `HERMES_AGENT_VERSION` | Commits fijados de los proyectos originales |
| `.env.example` | Configuración de referencia sin credenciales |
| `docs/` | Guías de instalación, flujo, operación y publicación |
| `PLAN_MVP.md` | Objetivo, fases y comprobaciones del MVP |
| `vendor/` | Fuentes recuperadas de Hermes; se reconstruyen y no se suben a este repositorio |
| `reports/`, `artifacts/` | Datos y capturas locales, excluidos de Git |

## Acceso y coste

El perfil probado es `openai-codex` con `gpt-6-luna` y razonamiento `low`, autorizado mediante OAuth en Hermes. También existe el modo API con facturación independiente. La sesión del modelo se configura en cada instalación; no viene incluida al clonar.

La revisión normal usa tres llamadas al modelo; cada pregunta añade una llamada al personaje elegido. El coordinador distribuye y consolida mediante código. No hay reintentos ni escalado de modelo automáticos. Con el backend Codex OAuth de esta versión, el límite de salida configurado no constituye un techo duro de tokens. Detalles en [Operación](docs/OPERACION.md).

## Datos y despliegue local

Los archivos seleccionados se envían al proveedor del modelo. La ocultación de posibles credenciales es heurística. Las evidencias y consultas pueden contener código o información del repositorio: se guardan localmente y no se publican con el proyecto.

Solo se publica `127.0.0.1:3000`. El analizador funciona sin privilegios, sin socket Docker y sin puerto público. Es un MVP de uso local, sin autenticación corporativa; una publicación en red requiere trabajo adicional. La infraestructura de Azure DevOps/Kubernetes queda fuera de esta versión.

## Estado y proyectos originales

Las siete fases se cerraron con un piloto sobre `ziuld/bookingApi` y validación del usuario. La iniciativa empresarial original sigue pendiente de disponer de repositorio. El detalle verificable está en [el plan](PLAN_MVP.md).

Basado en [Hermes3D](https://github.com/iamlukethedev/Hermes3D) y [Hermes Agent](https://github.com/NousResearch/hermes-agent). Versiones y atribuciones: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
