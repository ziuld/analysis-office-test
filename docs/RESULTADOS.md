# Resultados de Fase 1 — 0.3.0

Fase aceptada y cerrada el 24/10/2026 por el usuario con resultados parciales y límites conocidos. Frontend/backend/paquete 0.3.0; merge manual pendiente, sin publicación. El afinado queda fuera de esta entrega y se propone en [Fase 2](PLAN_FASE_2.md). Los registros de candidatas abiertas que siguen son históricos; los informes 0.2.0 no se reescriben.

Los nuevos informes híbridos incluyen el inventario íntegro al commit en `evidencia.json`, hashes de blobs y SHA256, cobertura por herramienta y fuentes originales realmente suministradas. `coordinacion.json` conserva decisiones y consultas; `celulas/*.json` distingue ejecución, cobertura, llamadas y advertencias. `manifest.json` conserva consumo y perfiles efectivos. HTML, Markdown y oficina muestran omisiones, carencias y cobertura separada de la ejecución. Los históricos no se reescriben.

Que el snapshot esté completo no significa que todos los archivos tengan parser ni que los modelos hayan leído todo su contenido. La evaluación semántica sigue acotada. Las comprobaciones reales, intentos y límites se registran en [PLAN_FASE_1.md](PLAN_FASE_1.md).

## Orquestación y selección autónoma de evidencia

El coordinador ahora da objetivos, sin elegir archivos. Cada especialista selecciona fuentes del snapshot/grafo dentro de rondas y presupuestos configurables. La repetición completa `f7043007-40a9-42a3-8b1e-a1478688c25c` terminó sin bloqueos ni errores técnicos: tres especialistas, síntesis, 8 llamadas económicas, 52.366 tokens, 7 observaciones y 22 citas conservadas verificadas. Sigue parcial por un hallazgo de Seguridad rechazado por tema no admitido y por controles pendientes. El primer intento falló en la investigación de Inventario por respuesta incompleta del runtime; ambos resultados se preservan. [Métricas, comprobaciones y límites](evidence/orchestrator-research-2026-10-24.json). Citas válidas no certifican interpretación semántica; afinado pendiente.

## Histórico de revisiones anteriores al cierre

La repetición del 24/10/2026 encontró avisos duplicados en el validador, corregidos con un caso nuevo (15 pruebas dirigidas correctas). Los pilotos completos de `main` adquirieron 69/69 archivos. En aquel intento, la ejecución fue parcial: Arquitectura perdió todos sus hallazgos por fuentes inexistentes; Seguridad e Inventario conservaron dos observaciones en total. En ese momento el commit/PR quedó pendiente por la condición del usuario; posteriormente se aceptó el cierre funcional descrito arriba. Métricas, intentos y errores en [la evidencia](evidence/arktic-recheck-2026-10-24.json) y el [plan](PLAN_FASE_1.md).

## Documentación y resultados anteriores

### Registro histórico de candidata de entrega

Las revisiones nuevas de API y CLI se guardan bajo `/reports/AAAA-MM-DD/HHMMSS-repositorio/identificador/`, con fecha y hora UTC. El título deriva del nombre del repositorio y se normaliza para usarlo como carpeta. El identificador sigue siendo la referencia de las rutas HTTP. El catálogo admite también los directorios planos anteriores y no mueve ni reescribe informes históricos; rechaza identificadores duplicados y enlaces de carpetas. La creación sin repositorio conserva el comportamiento plano de compatibilidad.

Cada revisión incorpora `manifest.json`: commit y rama del objetivo, versión del backend, hash de sus fuentes Python instaladas, pin de Hermes, perfiles efectivos, hashes de perfiles/skills/estándar editorial, cobertura y consumo disponible por etapa. Se escribe tras preparar la evidencia y se completa tras el equipo. Un fallo anterior puede dejarlo incompleto o ausente; no implica que la revisión terminara. Los tokens no comunicados se conservan como desconocidos. El manifiesto identifica procedencia y no certifica reproducibilidad bit a bit ni una entrega publicada.

El estándar de ejecución está en [resources/editorial/standard.md](../backend/src/arktic_office/resources/editorial/standard.md), dentro del wheel. Conserva exactamente los bytes, versión y SHA-256 anteriores: `272c4e4a788221d83e4f4a7315a666edf308de0b3ef1b4486b21eebe3ac21a3f`. La documentación humana explica su uso, sin instalarse como plantilla. Los formatos históricos conservan sus contratos.

## Conservación

Los informes del producto viven en el volumen de resultados. No hay borrado automático ni migración del histórico. El operador decide su conservación y puede retirar revisiones completas después de revisarlas y respaldarlas; no se añade un servicio de limpieza.

Snapshots y mapas del preparador son temporales: se liberan al finalizar la petición, también ante errores gestionados. Una interrupción abrupta puede dejar temporales hasta recrear el contenedor y su tmpfs. Capturas, logs, muestras y grafos usados en desarrollo viven en `artifacts/`, excluido de Git; se conservan localmente como evidencia y no forman parte del producto ni de la publicación. Su retirada es una operación manual posterior a la revisión.

## Comprobaciones del 24/10/2026

- Backend: 118 pruebas ejecutadas, 117 correctas y una referencia visual opcional omitida, en 7,081 s. Se comprueban el layout fechado, lectura del histórico plano, manifiesto, conservación de bytes y rechazo de enlaces que salgan del almacenamiento. Log local: `artifacts/block7-tests.log`.
- Imagen del backend construida con recursos instalados. Construcción y arranque finales correctos: API y oficina saludables, oficina/proxy/API HTTP 200, sin trabajos ni credenciales y recursos temporales retirados. Log `artifacts/block7-startup.log`; se utiliza la base existente, sin ampliar CI/CD.
- Evaluación autorizada: hasta cinco invocaciones con `ziuld/bookingApi`, sin scanners ni ejecución del proyecto. Se reutilizó el snapshot fijado del Bloque 2, commit `c0d247e3226d77a83471c7a1b32afdb0981eb7f1`, con 24 archivos seleccionados. No se afirma evaluar el último commit remoto.
- Se hicieron cuatro invocaciones en 27,654 s: reparto y Seguridad fallaron por sesión no válida; Arquitectura e Inventario por cuota/límite. No hubo contenido válido y se omitió síntesis. Tokens desconocidos. No se realizaron más intentos. Logs y ledger locales: `artifacts/block7-evaluation.log` y la carpeta indicada en `artifacts/block7-evaluation-path.txt`.

El adaptador desactiva los reintentos y recuperación internos del Hermes fijado, además de herramientas y fallback, para mantener una tentativa por invocación. Esa integración depende del pin actual. Las pruebas con respuestas ficticias validan contratos, citas e insuficiencia; los cuatro errores reales no permiten medir utilidad semántica ni consumo efectivo. Este fue un resultado inicial, anterior a los pilotos completos y al cierre aceptado.

[release.json](../release.json) registra una candidata para revisión y [CHANGELOG.md](../CHANGELOG.md) contiene cambios sin publicar. Frontend/backend siguen en 0.2.0. Ese estado de candidata quedó sustituido por la aceptación de Fase 1 0.3.0; el usuario conserva el merge. No se crean etiquetas, releases ni publicación de imágenes.

## Verificación posterior del recorrido completo

Tras recuperar la sesión y corregir contratos y reparto, la prueba real `bb23e6e3-f995-4748-8ff2-47304b8f57cc` completó reparto, Seguridad, Arquitectura, Inventario y síntesis sin errores ni etapas de modelos omitidas. Dos llamadas de preparación más cinco del equipo, todas `gpt-6-luna`/`low`: 40020 tokens comunicados, unos 105 s, siete observaciones informativas, un indicio medio y cinco conclusiones de síntesis. Veinte citas únicas contrastadas con el snapshot; informes y manifiesto accesibles mediante la oficina. La autorización posterior incluyó scanners: Gitleaks sin detecciones en la selección; OSV sin entrada compatible y dependencias no evaluadas.

Se mantiene el estado parcial por el límite de dos llamadas de preparación. No se borra el histórico de intentos fallidos ni se declara seguridad o calidad óptima. Evidencia y trazabilidad: [full-pilot-final-2026-10-24.json](evidence/full-pilot-final-2026-10-24.json). La mejora semántica se propone en Fase 2; la base funcional de Fase 1 fue aceptada.
