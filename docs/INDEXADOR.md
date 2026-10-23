# Validación del indexador — Bloque 2

Experimento independiente de la oficina y la API. No activa un recorrido nuevo de análisis ni modifica sus contratos. Implementa recuperación, extracción estructural y consultas dentro de Docker; no instala el indexador en el host.

## Reproducir

Desde el repositorio, con PowerShell 7 y Docker Linux/amd64:

```powershell
pwsh -NoProfile -File scripts/check-indexer.ps1
```

No requiere `vendor/`, `.env`, sesiones OAuth ni claves de modelos. La imagen descarga Graphify durante el build e instala sus propias dependencias. Después, el servicio `fetch` descarga archivos de las muestras públicas autorizadas a un directorio nuevo. Cada extracción y sus consultas se ejecutan en otro contenedor con `network_mode: none`, sin puertos ni socket Docker. No se instalan dependencias, ejecutan scripts, pruebas o aplicaciones de las muestras. Sus instrucciones se tratan como datos.

El script usa un nombre de proyecto único y elimina su red y contenedores temporales mediante `finally`. Conserva los datos en `artifacts/indexer-FECHA-ID/`, fuera de Git. No utiliza los informes ni volúmenes de la aplicación. La recuperación rechaza destinos existentes y los resultados no se sobrescriben. Una interrupción forzada puede requerir retirar el proyecto temporal manualmente.

No se añade esta evaluación a la CI de arranque del Bloque 1: son comprobaciones con alcance y tiempos diferentes. No hay publicación de imágenes, CD ni cambios de versión de aplicación.

## Fuente, dependencias y licencias

- Graphify **0.9.95**, commit `92741d162b2094ffc2fed58cfbd8ee823e9da62c`; [fuente fijada](https://github.com/Graphify-Labs/graphify/tree/92741d162b2094ffc2fed58cfbd8ee823e9da62c). La selección queda en [indexer.json](../preparation/indexer.json), no depende de que una etiqueta se mueva.
- Python **3.12**, imagen base fijada por digest; entorno separado del Python 3.14 del backend. `uv 0.9.4` fijado por digest instala el lock upstream con `--frozen --no-dev --no-editable`. Solo se instala el conjunto base, sin extras de modelos, MCP, transcripción, bases de datos o clustering Leiden.
- El lock upstream de este commit omite **PyYAML**, aunque `pyproject.toml` lo exige. La primera prueba lo detectó porque Graphify emitía avisos y omitía YAML. [requirements-overlay.lock](../preparation/requirements-overlay.lock) añade únicamente PyYAML 6.0.3, sin resolver otras dependencias y con el SHA256 oficial de su wheel CPython 3.12/Linux amd64. `uv pip check` valida la consistencia final. El overlay forma parte del experimento y debe revisarse al cambiar Graphify.
- El build utiliza `apt` para Git y certificados; esas versiones y las dependencias de build de setuptools no están bloqueadas con hashes propios. No se afirma reproducción idéntica bit a bit ni construcción sin red. Los paquetes instalados y Python real se guardan en `environment.json`.
- Graphify declara **Apache-2.0** y conserva contribuciones previas MIT. Se preservan [LICENSE](../licenses/Graphify-LICENSE.txt), [LICENSE-MIT](../licenses/Graphify-LICENSE-MIT.txt) y [NOTICE](../licenses/Graphify-NOTICE.txt). También se copian desde las fuentes a `/usr/local/share/licenses/graphify/` en la imagen. Sus dependencias mantienen sus avisos propios; esto no asigna licencia al código propio de Arktic Office ni constituye una revisión jurídica de todas las dependencias.

## Muestras y trazabilidad

Autorizadas por el usuario: Arktic Office y el piloto público `ziuld/bookingApi`. Para cubrir el frontend real de Arktic Office se materializa además Hermes3D con nuestro parche:

| Muestra | Snapshot fijado | Contenido principal |
|---|---|---|
| `arktic-office` | `ziuld/analysis-office-test`, `b6b8adec2a36a43248ed5194bdc86b38bfeaccb6` | Backend Python, PowerShell y Compose del Bloque 1 fusionado |
| `booking-api` | `ziuld/bookingApi`, `c0d247e3226d77a83471c7a1b32afdb0981eb7f1` | Java y Gradle, código de aplicación y tests como texto |
| `office-frontend` | `iamlukethedev/Hermes3D`, `beb76292747b816ef317aa6f9a3992e0014f81d9` + `docker/hermes3d-local-demo.patch` | TypeScript/TSX, JavaScript y frontend adaptado |

Cada `snapshot.json` registra repositorio, commit, SHA256 del archivo descargado, tamaños, exclusiones y tiempo de recuperación. El frontend añade el SHA256 del parche. No se resuelve la rama predeterminada durante esta medición: se usan los commits completos declarados; el flujo general de adquisición queda para el Bloque 4. No se descarga historial Git.

## Límites efectivos del experimento

| Recurso | Control |
|---|---|
| CPU y memoria | 2 CPU y 2 GiB por contenedor, 128 procesos/hilos |
| Descarga | 30 MB comprimidos por archivo, timeout de socket de 30 s |
| Snapshot | 150 MB de expansión declarada, 4.000 archivos materializados y hasta 8.000 entradas de archivo; archivos individuales de más de 2 MB se omiten y registran |
| Tiempo | 600 s por recuperación de muestra y por extracción; 30 s por consulta |
| Paralelismo de extracción | 2 workers |
| Disco de resultados | Máximo de 64 MB por archivo de salida de extracción/consulta; no es una cuota global de disco del bind mount |
| Temporales | `/tmp` de 128 MiB, sin ejecución ni privilegios adicionales |
| Red de extracción/consulta | Deshabilitada por Docker; `GRAPHIFY_BACKEND=none`, sin credenciales ni SDKs de modelos |
| Consulta | Presupuesto de salida solicitado a Graphify: 2.000; no representa consumo de tokens de un modelo |

Se omiten enlaces, dispositivos, `.env*`, claves por extensión y directorios generados/de dependencias. Esta exclusión por nombre no es un scanner de secretos ni asegura que todos los secretos se hayan eliminado. Los artefactos siguen siendo datos locales que requieren revisión antes de compartirlos. Los archivos grandes y exclusiones reducen cobertura y se registran; no se presentan como inspeccionados.

La extracción utiliza `--code-only --no-cluster`. No analiza semánticamente documentación, imágenes o binarios; tampoco ejecuta `--cargo`, intérpretes de los proyectos, Gradle, npm, tests, Gitleaks u OSV-Scanner. No genera comunidades ni etiquetas mediante modelos. La imagen no arranca un servidor MCP: la consulta CLI ejercita el grafo directamente.

## Evidencia y lectura de resultados

- `result/metrics.json`: duración de extracción y consultas, nodos/aristas, tipos de relación, inventario por extensión, archivos con representación, consultas y comprobaciones de relaciones.
- `result/extract.log`: errores, archivos no clasificados y avisos de extracción; se conservan incluso si se obtienen nodos.
- `result/query-N.txt`: respuesta o ambigüedad de la consulta. Si hay una única etiqueta exacta tras una respuesta ambigua, se hace como máximo una segunda consulta con su ID explícito; se conserva como `query-N-scoped.txt`. Si la ambigüedad no se resuelve así, no se elige una coincidencia arbitraria y el script falla después de intentar las otras muestras.
- `result/graphify-out/graph.json`: grafo sin clustering. No se envía a modelos.
- Pico de memoria: high-water mark del cgroup de cada contenedor de extracción, con compatibilidad cgroup v1/v2. Incluye wrapper, hijos y caché de archivos cargada al cgroup. Se conserva también el RSS máximo individual de hijos; no se confunden las dos medidas. Los picos de muestras distintas usan contenedores distintos.
- [probes.json](../preparation/probes.json): nueve relaciones elegidas leyendo las fuentes, con línea de evidencia y aristas recuperadas. Incluye intencionadamente una llamada Python a través de un atributo y un método Java heredado de una dependencia externa para observar límites. No son un conjunto exhaustivo ni permiten estimar precisión o recall globales. Un archivo representado por un nodo no demuestra que sus símbolos o relaciones estén completos.

Los tests del descargador comprueban rutas fuera del destino, enlaces, exclusiones y presupuestos, sin ejecutar las muestras. Los datos de las aplicaciones se mantienen fuera de Git.

Las etiquetas de confianza de Graphify se conservan tal cual. Una arista Java marcada `INFERRED` puede proceder de resolución estática de tipos; no implica llamada a un modelo ni constituye una probabilidad de acierto medida. Las sondas de dependencia dinámica y método heredado requieren información que no existe como un destino único definido en estas fuentes: sirven para delimitar utilidad, no para contar falsos negativos de un benchmark general.

## Resultado y decisión

Repetición final del **23/10/2026**, ejecución `indexer-20261023-184518-e41e49`, salida 0. Máquina Windows con PowerShell 7 y Docker Desktop 4.47.0, Engine 28.4.0; Docker Linux/amd64 tenía 14 CPU y unos 7,5 GiB disponibles. Cada extracción se limitó a 2 CPU y 2 GiB. Las cinco pruebas de materialización pasaron. La instalación pasó `uv pip check`.

| Muestra | Recuperación y parche | Extracción | Pico del contenedor | Nodos / aristas | Archivos representados, lenguajes principales | Sondas recuperadas |
|---|---:|---:|---:|---:|---|---:|
| Arktic Office | 1,906 s | 15,232 s | 119,1 MiB | 407 / 1.361 | Python 32/32; PowerShell 2/2; JS 1/1; YAML 1/3 | 2/3 |
| bookingApi | 1,745 s | 18,412 s | 79,9 MiB | 321 / 985 | Java 35/35; Gradle 2/2 | 2/3 |
| Frontend adaptado | 16,856 s | 229,787 s | 211,5 MiB | 4.546 / 12.898 | TS 451/451; TSX 86/86; JS 16/16; MJS 6/6 | 3/3 |

La duración de extracción excluye build, descarga, consultas y reevaluación de sondas. Los picos son del cgroup v1 completo, no sumas de RSS. No hubo timeouts ni fallos de asignación de memoria registrados. La medición no es una prueba estadística ni una garantía para otros equipos, tamaños o lenguajes.

Las nueve consultas terminaron con salida útil. `Jobs`, `ReservationController` y `ReservationService` dieron primero salida 3 por ambigüedad; la única repetición con ID explícito terminó con 0, sin modelo. Se conservan ambos resultados. Los dos imports de `AuditOffice` y la definición de `proxy` se comprobaron contra el código y las aristas. La sonda del archivo de ruta se reevaluó sobre el mismo grafo tras corregir su etiqueta visual a `[...path]/route.ts`; la extracción y su tiempo no se alteraron.

**Carencias observadas:**

- Se recuperaron las siete sondas de estructura directamente definida en las fuentes. No se resolvió la llamada Python `self.answerer(context)` al valor por defecto `answer_question`, que además puede sustituirse en ejecución. Tampoco se enlazó `reservationRepository.findAll()` con una definición local, porque el método viene de una dependencia externa. El resultado es 7/9 sondas cubiertas, sin interpretarlo como porcentaje general de precisión.
- `compose.yaml` y `compose.ci.yaml` no aparecen representados pese a instalar PyYAML; contienen etiquetas específicas de Compose. Los Dockerfiles y `.properties` tampoco se estructuran en este recorrido. Deben leerse mediante reglas/texto. El inventario de archivos conserva sus rutas.
- Graphify avisó de **100 archivos de código sin símbolos** en el frontend (0,35 MB), incluidos archivos de configuración y reexportaciones, y de dos Gradle sin símbolos en bookingApi. Algunos tienen nodo de archivo: 451/451 TS representados no significa comprensión completa de TypeScript. Se conservaron esos avisos y no se atribuye cobertura de flujo a los nodos.
- No se han medido repositorios grandes, cargas concurrentes, recuperación tras caída, MCP, clustering, otros sistemas operativos host o arquitecturas. No se han hecho llamadas a modelos, análisis de seguridad ni escaneos de vulnerabilidades. Tampoco se ha ejecutado este arnés en GitHub Actions.

**Decisión F1-06:** seleccionar Graphify 0.9.95 con el overlay documentado como ayuda estructural para la siguiente preparación híbrida. En las muestras recupera imports, llamadas entre archivos y componentes relevantes dentro de los recursos fijados; la muestra más grande tarda menos de cuatro minutos de extracción. Mantener búsqueda y lectura textual para configuración, relaciones dinámicas, herencia externa y código sin símbolos. No usar el grafo como prueba única de controles de seguridad o flujo completo.

Mantener el preparador **separado del runtime Hermes/Core API**: aquí se ha probado Python 3.12 y dependencias de análisis propias, con un perfil de recursos distinto. Es un proceso batch desechable; no se decide todavía un servidor permanente ni se añade un servicio por agente. La integración con trabajos y contratos corresponde a los bloques siguientes.

Codebase-Memory queda como alternativa **sin evaluar**: no se instala ni se compara rendimiento o calidad sin datos. No hizo falta activar la alternativa para cumplir esta prueba acotada; reconsiderarla si las carencias anteriores impiden recuperar flujos prioritarios en nuevas muestras. Seleccionar Graphify no valida automáticamente casos que no se midieron.

Resumen revisable sin código ni grafos completos: [evidencia JSON](evidence/indexer-2026-10-23.json), con commits, hashes de archivos descargados/grafos, versiones instaladas, métricas y sondas. Los logs, snapshots y grafos locales están en `artifacts/indexer-20261023-184518-e41e49/`, con log global `artifacts/block2-validation-final.log`; los ensayos iniciales se conservan aparte. La red temporal de la repetición se retiró correctamente. Las versiones frontend/backend y los commits de Hermes no cambian.
