# Archivo comparativo de agentes — 31/10/2026

Copias exactas de los informes renderizados, archivadas por autorización expresa del usuario al cerrar este punto estable. Los originales locales se conservan sin cambios. No se incluyen capturas de código, respuestas crudas de modelos, SQLite, cachés, `.env` ni sesiones.

| Configuración | Ejecución | HTML | Markdown |
| --- | --- | --- | --- |
| Tres especialistas | `2697cb5e-b168-41f1-a5bd-714b7ba0d9ff` | [HTML](three-specialists/informe.html) | [Markdown](three-specialists/informe.md) |
| Siete con contexto precargado | `1df56a5f-6b84-478c-a0af-0a6fec12df1b` | [HTML](seven-shared-context/informe.html) | [Markdown](seven-shared-context/informe.md) |
| Siete con mapas y consultas | `813716cc-477b-4a4b-9795-a231973a4b9f` | [HTML](seven-lookup-maps/informe.html) | [Markdown](seven-lookup-maps/informe.md) |

- [Comparación cuantitativa](comparison.json): modelos, llamadas, consumo, duración, estados originales/publicados y límites de comparación.
- [Matriz Q01–Q40](question-matrix.md).
- [Integridad y descargas](verification.json).
- [Medición offline de contexto](offline-context-measurement.json): reconstrucción anterior al ensayo real, no consumo de una nueva ejecución.
- [Manifiesto de tamaños y SHA-256](manifest.json): permite comprobar que las seis copias no se modificaron.
- [Comprobaciones del código](test-verification.json).

El informe histórico puede contener datos o conclusiones que después se corrigieron. Se conserva tal como se emitió: no se aplican retroactivamente la retirada del filtro ni la ausencia de ocultación. La duración de la primera referencia es aproximada. El cambio de estados no demuestra por sí solo un cambio de calidad; el cierre explica los límites.

[Resultados del ensayo real](../../RESULTADOS_MAPAS_2026-10-31.md) · [Cierre estable](../../CIERRE_COORDINACION_2026-10-31.md).

[Revisión de publicación](publication-review.json): el detector señaló tres huellas SHA-256 de identidad de caché como claves genéricas. Se contrastaron con las capturas guardadas y manifiestos; no son credenciales. No se suprimieron reglas ni se alteraron los informes.
