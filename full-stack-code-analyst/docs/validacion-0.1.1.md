# Validación técnica 0.1.1 · 19/11/2026

- `verify_report.py`: cuatro grupos del resumen, 40 etiquetas y encabezados h4, siete bloques, escape de contenido, conservación de CSS, rechazo de HTML editado y fichas divergentes. Reproduce la regresión de quitar clases de tarjetas manteniendo preguntas y estilos: finish la rechaza.
- Ubicación: rechaza ejecutar la copia de Iris de otro workspace contra un proyecto externo antes de abrir almacenamiento. Rechaza destinos de escritura/exportación fuera de .local. Simula denegación al abrir el lock y comprueba `permission_required`, ruta concreta y `fallback_allowed: false`, sin carpeta outputs alternativa.
- `verify_local.py`: vigencia, caché, ramas/commits, render/cierre, copia interna, integridad y reparación.
- `verify_features.py`: procedencia, comparación, dependencias, aislamiento y fallos Docker, conservando el generador fijo para el informe.

Las pruebas usan proyectos ficticios y cubren los mecanismos; no certifican cobertura semántica del análisis. La modificación de los archivos del agente cambia el perfil y deja las revisiones previas como históricas. No se reetiquetan automáticamente como análisis de 0.1.1. Una recomposición visual de un informe anterior debe declarar que conserva ese análisis y no lo vuelve a ejecutar.

El parche aportado por el usuario sobre destino local se tomó como propuesta: se incorporó su criterio de pedir permiso y reintentar en la misma ruta y se reforzó con comprobaciones de proyecto, confinamiento de escritura y error estructurado. Se conserva .local; una denegación de permisos no se soluciona renombrando o trasladando la carpeta.
