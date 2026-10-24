# Núcleo Python — Bloque 3

El backend es el paquete `arktic_office`, construido como wheel desde [pyproject.toml](../pyproject.toml). Versión de la entrega aceptada: **0.3.0**. El paquete propio no añade dependencias Python: el adaptador Hermes sigue utilizando el runtime fijado y su lock dentro de Docker, sin incorporarlo al paquete ni cambiar modelos o presupuestos.

## Organización

| Ruta bajo `backend/src/arktic_office/` | Responsabilidad |
|---|---|
| `api/server.py` | Rutas REST y serialización HTTP existentes |
| `execution/jobs.py` | Ejecuciones, exclusión mutua, consultas y recuperación de estados interrumpidos |
| `storage/` | JSON compatible con BOM, escritura atómica, catálogo y resolución de IDs |
| `config/settings.py` | Configuración de entorno y perfiles actuales por célula |
| `adapters/` | Procesos de auditoría, runtime Hermes y scanners existentes |
| `preparation/repository.py` | Lectura y selección acotadas actuales; aún no integra Graphify |
| `coordination/` | Distribución, consolidación y consultas sobre evidencia guardada |
| `reporting/` | Validación, prompts y formatos históricos de informes |
| `core/` | Errores comunes, suficiencia y contratos de datos/estados/eventos |
| `resources/` | Perfiles y recursos visuales incluidos en el wheel |

`backend/tests/` contiene las pruebas fuera del código de producción. La imagen normal no copia esa carpeta. Desde el Bloque 7, el estándar canónico está en `backend/src/arktic_office/resources/editorial/standard.md`, incluido en el wheel. `docs/ESTANDAR_COMUNICACION_INFORMES.md` es la guía humana de ese recurso. No se duplican sus reglas ni se cambia su contenido o hash. Su mención a `auditor/editorial.py` corresponde a la ubicación anterior; la implementación actual está en `reporting/editorial.py`.

Se mantienen `/app/audit.py`, `/app/server.py`, `/app/preview.py` y `/app/runtime.py` como lanzadores de compatibilidad. También existen las entradas `arktic-audit`, `arktic-api` y `arktic-preview`. Los procesos internos usan `python -m arktic_office...`, por lo que no dependen de encontrar módulos sueltos en `/app`.

## Contratos y almacenamiento

[contracts.py](../backend/src/arktic_office/core/contracts.py) documenta las formas actuales de evidencia, referencias y trabajos mediante tipos Python. No añade campos obligatorios a los archivos guardados ni aplica una migración a los formatos 1, 2 o 3.

Los estados de trabajo conservan `preparando`, `analizando`, `completo`, `parcial`, `error` e `informacion_insuficiente`; las consultas conservan `respondiendo`, `completada` y `error`. Las rutas y respuestas REST existentes no cambian.

`StateEvent` versión 1 es una notificación interna con `run_id`, `scope`, `state`, `question_id`, `at` y `version`. El receptor es una función opcional inyectada en `Jobs`, sin bus, servidor, tabla o transporte nuevos. Se invoca después de guardar el estado; un fallo del receptor no invalida el resultado persistido. No se emite progreso ficticio ni se conecta todavía a la oficina. SSE y persistencia de eventos siguen pendientes.

`RunStore` resuelve un ID estable sin exigir que su carpeta sea hija directa de `reports/`. Admite el histórico plano y carpetas de agrupación anidadas, con búsqueda hasta cuatro niveles y 10.000 directorios. No sigue enlaces de directorio fuera del almacén ni elige arbitrariamente entre IDs duplicados. El listado conserva el máximo de 30 registros y el orden por fecha. Las escrituras nuevas siguen en el formato plano actual: organizar físicamente resultados corresponde al Bloque 7.

No se mueve, convierte ni vuelve a renderizar ningún informe guardado. El catálogo de lectura es independiente de `Jobs`: consultar el histórico no marca trabajos como interrumpidos ni escribe archivos. El arranque normal de `Jobs` conserva su comportamiento de recuperación de trabajos/consultas interrumpidos, también en carpetas anidadas.

## Comprobaciones manuales mínimas

Por petición del usuario, CI/CD conserva exclusivamente la base del Bloque 1. **No se añaden comprobaciones al workflow**. La regresión de este bloque se ejecuta manualmente:

```powershell
pwsh -NoProfile -File scripts/check-backend.ps1
```

Construye el paquete instalado y el target de pruebas del mismo Dockerfile. Ejecuta la suite previa y solo tres casos nuevos necesarios para esta reorganización: hashes de prompts/formatos 1–3, resolución plana/anidada sin alterar archivos y eventos ligados a estados guardados con ejecución ficticia. El runner bloquea procesos externos y conexiones que no sean localhost; el contenedor tampoco tiene red ni credenciales montadas. Las pruebas de scanners usan sus ejecutores falsos originales, sin iniciar binarios reales.

Resultado del 23/10/2026: referencia previa **108 pruebas correctas**; paquete reorganizado **111 ejecutadas, 110 correctas y 1 omitida**. La omitida es la referencia visual local opcional, que no se distribuye en el contenedor. Los hashes de Markdown/HTML de tres formatos y el prompt coinciden con la implementación anterior sobre una muestra ficticia.

Se reutilizó manualmente `scripts/check-startup.ps1`: imágenes construidas, API y oficina saludables, `/health` con versión 0.2.0 y HTTP 200 en oficina/proxy, sin trabajos ni autenticación. Los recursos temporales se retiraron. Además, el histórico real se montó en solo lectura: 24 directorios detectados, 19 registros legibles (18 con informe), formatos 1/2/3 y **154 archivos con hashes idénticos antes/después**. Cinco directorios incompletos siguen fuera del catálogo, como antes.

Logs locales: `artifacts/block3-baseline-tests.log`, `artifacts/block3-tests-final.log`, `artifacts/block3-startup.log` y `artifacts/block3-history.log`. No se ejecutaron análisis de repositorios, scanners ni modelos. No se ha probado este cambio en GitHub Actions ni en otros equipos; el histórico y los artefactos locales no se publican.
