# Fase 1 — Base integrada de Arktic Office

**Estado: cerrada y aceptada el 24/10/2026. Versión 0.3.0** de frontend, backend y paquete Python. El usuario acepta resultados parciales y límites conocidos; hará el merge manual del [PR #3 hacia main](https://github.com/ziuld/analysis-office-test/pull/3). No se publican tags, imágenes ni GitHub Release.

Este es el único plan de Fase 1. Consolida el alcance final y su aceptación; las propuestas sustituidas y los registros de trabajo detallados permanecen en el [historial previo a la consolidación](https://github.com/ziuld/analysis-office-test/blob/84dcf49fde60e241a2eb83219a3d9c90b63c5bd7/docs/PLAN_FASE_1.md). No se reescriben informes ni evidencias históricas. El [MVP](../PLAN_MVP.md) conserva su cierre 0.2.0; las mejoras posteriores pertenecen exclusivamente a la [Fase 2](PLAN_FASE_2.md).

## Objetivo y alcance aceptados

Entregar una base integrada para evaluar preliminarmente repositorios: adquisición íntegra, herramientas deterministas, coordinación, tres especialistas con evidencia verificable, oficina y resultados persistidos. El informe ayuda a una persona técnica; no certifica seguridad, exhaustividad ni aptitud para desplegar.

No ejecutar el proyecto analizado, sus instaladores o pruebas. Mantener los pins, una ejecución activa, presupuestos explícitos y resultados parciales con errores visibles. CI/CD conserva únicamente la base acordada del Bloque 1, sin ampliaciones posteriores.

## Bloques cerrados

| Bloque | Tareas | Resultado aceptado |
|---|---|---|
| 1. Reproducción y CI mínima | F1-01–F1-03 | Recuperación por commit, parche reproducible, construcción y arranque aislado sin credenciales ni modelos |
| 2. Indexador | F1-04–F1-06 | Graphify fijado, extracción y consultas en Docker, muestras y límites documentados |
| 3. Núcleo y contratos | F1-07–F1-09 | Paquete Python, responsabilidades separadas, almacenamiento e histórico compatibles |
| 4. Preparación híbrida | F1-10–F1-12 | Adquisición separada del contexto, mapa/búsqueda/fragmentos; explorador inicial conservado como legacy y sustituido en el flujo actual por investigación de especialistas |
| 5. Coordinación y recursos | F1-13–F1-16 | Perfiles, skill, validación previa, encargos y síntesis; Azure solo bajo encargo |
| 6. Oficina y consultas | F1-17–F1-20 | Actividad real, estados terminales, personajes libres al terminar y últimas diez consultas independientes por revisión/agente; selección sin giro de cabeza |
| 7. Resultados y entrega | F1-21–F1-24 | Carpetas fechadas, manifiestos, recursos de ejecución separados, pilotos económicos y aceptación de 0.3.0 con cobertura parcial |
| 8. Evidencia compartida | F1-29–F1-37 | Snapshot íntegro verificado, mapas/scanners globales compatibles y especialistas que seleccionan fuentes bajo límites del Core |

F1-23 se acepta con las mediciones y límites registrados, sin dar por validada la calidad óptima. F1-24 queda cerrado por aceptación humana y manifiesto 0.3.0; el merge corresponde al usuario. Los antiguos F1-25–F1-28 y su Bloque 9 de afinado se retiraron del alcance; no se declaran ejecutados ni quedan tareas abiertas de Fase 1. Fase 2 tiene sus propios identificadores.

## Flujo final implementado

1. Resolver la rama predeterminada y fijar el commit. Obtener todo el snapshot versionado, verificar árbol y hashes; detenerse si falta contenido o se supera capacidad.
2. Inventariar todo y aplicar Graphify y scanners sin modelos a su entrada completa compatible. Registrar procesamiento, incompatibilidades y errores; ningún parser acredita exhaustividad semántica.
3. El coordinador recibe un índice/contexto común acotado y da tres objetivos en una llamada. No elige archivos ni omite especialistas por un reparto vacío.
4. Seguridad, Arquitectura e Inventario trabajan consecutivamente. Cada uno selecciona fuentes mediante consultas locales agrupadas al mismo snapshot/grafo y recibe fragmentos originales con líneas verificables.
5. Validar las aportaciones contra el texto realmente suministrado; conservar elementos válidos cuando otros sean rechazados. Distinguir ejecución, cobertura, insuficiencia y error.
6. El coordinador sintetiza solo aportaciones validadas, conservando fuentes, certeza, condiciones, acciones y pendientes. Guardar informes y manifiesto; limpiar los temporales completos.
7. Consultas posteriores: una pregunta independiente al agente elegido sobre evidencia guardada, sin descargar de nuevo ni relanzar el equipo. Leer historial no consume modelo.

Detalles operativos: [preparación](PREPARACION.md), [coordinación](COORDINACION.md), [oficina](OFICINA.md), [resultados](RESULTADOS.md).

## Configuración y límites de cierre

- Perfil funcional económico: `gpt-6-luna/low`, sin elevación ni reintentos automáticos. No se afirma que sea el modelo final adecuado para todos los roles.
- `AUDIT_<ROL>_RESEARCH_ROUNDS`: 0–2, base 1. Cero produce informe sin lecturas de código; uno exige selección agrupada y análisis; dos permite una segunda ronda opcional. `MAX_EXTRA_QUERIES` no controla el recorrido compartido; `PREPARATION_MAX_LOOPS` queda en legacy.
- Cada ronda: 1–4 consultas, hasta tres fragmentos por consulta, 100 líneas/6000 bytes por fragmento. Topes acumulados: Seguridad 12 archivos/64000 bytes; Arquitectura e Inventario 6/24000. Padding de líneas incluido; fragmento con padding hasta 12000 bytes. Lecturas que no caben quedan registradas sin descartar evidencia anterior.
- Con una ronda por rol: hasta ocho llamadas (encargos + tres investigaciones + tres análisis + síntesis); con dos, hasta once. Hasta 240 s por llamada de especialista y límite global API de 1500 s. Los tokens de salida de Codex OAuth no tienen un techo duro garantizado por este adaptador.
- Snapshot: 32 MB, 20000 archivos, 300 s. Preparador: petición/respuesta 64 MB, texto 32 MB, 100000 nodos/200000 relaciones, 300 s. Estos límites son independientes de los presupuestos del modelo.
- LFS y submódulos sin hidratar detienen la adquisición. Symlinks se conservan como metadatos; no se siguen ni ejecutan. Dialectos no admitidos se inventarían y su texto sigue consultable cuando existe.

## Comprobaciones y resultados aceptados

| Comprobación | Resultado y procedencia |
|---|---|
| Último piloto completo | `f7043007-40a9-42a3-8b1e-a1478688c25c`, main remoto `b6b8adec2a36a43248ed5194bdc86b38bfeaccb6`, 69/69 archivos verificados; no el PR local sin fusionar |
| Equipo y coste comunicado | Tres especialistas y síntesis terminados, 8 llamadas económicas, 52366 tokens, 106,366 s; 7 observaciones informativas, 4 conclusiones, 22 citas conservadas contrastadas |
| Cobertura | Informe parcial: un hallazgo de Seguridad rechazado por tema inválido, cinco controles no evaluados y uno favorable limitado; sin bloqueos ni especialistas omitidos en la repetición |
| Herramientas | Graphify 50 archivos procesados/19 incompatibles, 493 nodos/1487 relaciones y 194 relaciones externas sin resolver; Gitleaks sin detecciones; OSV no evaluado por falta de entrada compatible |
| Intentos del ajuste de orquestación | Primero Inventario falló por respuesta incompleta del runtime; detalle causal y consumo desconocidos. Repetición manual única. Ambos intentos: 15 llamadas, 91739 tokens conocidos más consumo desconocido; no se contabiliza como cero |
| Pruebas de cierre | 17 pruebas dirigidas correctas en 0,161 s: flujo completo, coordinador, compatibilidad y almacenamiento/manifiestos. Seis pruebas de mapa/estados de interfaz y compilación registradas anteriormente; no se vuelve a presentar una suite histórica como nueva |
| Reproducción y arranque 0.3.0 | Imágenes frontend/backend construidas, script existente de arranque aislado correcto, API/oficina HTTP 200 y sin credenciales ni trabajos en el entorno temporal. Parche contrastado en reversa. Servicios locales saludables |
| Integridad y conservación | Limpieza normal y por error, recuperación de temporales abandonados, rechazo de rutas inseguras y preservación de evidencias comprobados. Informes históricos sin cambios |

La última prueba funcional y los pilotos anteriores se ejecutaron con 0.2.0: se conserva su versión original. El ajuste final de retención al agotar bytes se verificó con fixture; el cierre de metadatos 0.3.0 con pruebas y construcción/arranque, sin nuevas llamadas a modelos. El commit de cierre `84dcf49` pasó la CI existente tanto en [pull_request](https://github.com/ziuld/analysis-office-test/actions/runs/40104933248) como en [push](https://github.com/ziuld/analysis-office-test/actions/runs/40104929519). Los commits documentales posteriores se consultan en el PR; un arranque local no sustituye esa CI.

Citas correctas no garantizan interpretación correcta. La expresión del piloto «recupera trabajos» es demasiado amplia: el código marca interrupciones como error y no demuestra reanudación automática. Estas limitaciones fueron aceptadas para cerrar la base funcional y orientan Fase 2.

## Evidencias y conservación

- [Manifiesto de entrega](../release.json), [changelog](../CHANGELOG.md) y [cierre 0.3.0](evidence/phase1-close-2026-10-24.json).
- [Dos pilotos de orquestación](evidence/orchestrator-research-2026-10-24.json), [pilotos iniciales del Bloque 8](evidence/block8-architecture-2026-10-24.json) y [revisión del propio repositorio](evidence/arktic-recheck-2026-10-24.json).
- [Oficina y estados](evidence/office-visual-recheck-2026-10-24.json), [indexador](evidence/indexer-2026-10-23.json), [núcleo/resultados iniciales](evidence/block7-2026-10-24.json), [piloto previo completo](evidence/full-pilot-final-2026-10-24.json).

Los resultados del producto permanecen en `reports/` y los logs/capturas de desarrollo útiles en `artifacts/`, ambos excluidos de Git. Cachés y copias desechables pueden retirarse sin borrar esos resultados ni las credenciales locales. El contenido versionado mantiene exactamente tres planes: MVP cerrado, Fase 1 cerrada y Fase 2 propuesta. Las guías técnicas explican uso y configuración; no son planes adicionales.

Consolidación final: solo tres planes canónicos, enlaces locales comprobados y cero tareas abiertas de Fase 1. Retiradas siete copias desechables de fuentes bajo `artifacts/` y trece directorios `__pycache__` del código propio (aproximadamente 349 MiB de copias). Se conservan informes, capturas, logs, evidencias, parches, dependencias y configuración local; no se borran datos del producto ni se modifica código, CI/CD o versiones por esta limpieza.
