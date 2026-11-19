# Validación técnica de Iris 0.1 · 19/11/2026

Se realizaron estas comprobaciones dentro del almacenamiento local del agente, con proyectos ficticios:

- `python -X utf8 scripts/verify_local.py`: cambios locales, ramas y commits, entradas por herramienta, caché, cierre, exportación, integridad y reparación.
- `python -X utf8 scripts/verify_features.py`: modos y base vinculada, requisitos de independencia declarada, exclusión de informes previos, evolución por claves, avisos OSV no eliminables, fuentes para decisiones, escape HTML, selección/consentimiento Docker, separación de cachés y limpieza ante timeout o fallo. No publica como completa una revisión con cobertura pendiente.
- `python -X utf8 scripts/verify_docker.py --allow-image-download`: ejecución real con Docker Linux accesible desde Windows, imagen `semgrep/semgrep:1.182.1`, ID `sha256:82253a80c4294f6b5c2d426284ec9ab77eaa9792d1ca1036c9e2e276a200fca8`. Semgrep detectó `arktic.python-dynamic-execution` en una muestra Python de dos líneas. El original se mantuvo intacto, se eliminó el contenedor y la segunda ejecución reutilizó caché. Otra ejecución sin el flag de descarga verificó versión y normalización de rutas.

La descarga inicial de la imagen se hizo con autorización; queda en el almacenamiento administrado por Docker. Las muestras, resultados y logs quedan dentro de `.local/qa/`. No se instaló Docker/WSL ni se alteró el código de la web. Las pruebas de fallos y de procedencia utilizan respuestas simuladas; la prueba de ejecución Semgrep/Docker fue real.

Esto valida mecanismos, no acredita equivalencia de detección entre modelos ni cobertura exhaustiva. La evaluación independiente de un repositorio requiere un chat nuevo según [el protocolo](prueba-independiente.md); no se presenta como realizada en este chat con antecedentes.
