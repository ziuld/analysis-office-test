# Cierre de integración Iris · 19/11/2026

## Versiones

| Componente | Versión |
| --- | --- |
| Backend y paquete de Arktic Office | 0.6.0 |
| Frontend | 0.4.0 (sin cambios de interfaz) |
| Iris interno | 0.2.0 |
| Iris portable | 0.1.2 |
| Contrato compartido de presentación | 1.1 |

La versión del backend está en BACKEND_VERSION, pyproject.toml y los builds Compose. El perfil interno identifica su versión en delivery.json. Los pins Hermes/Hermes3D permanecen: esta entrega no publica versiones de esos proyectos. release.json sigue siendo el registro histórico del cierre de Fase 1; no se reescribe su aceptación ni sus cifras.

## Resultado

Se adaptaron las mejoras del portable sin sustituir el runtime integrado: generador canónico y plantilla comunes, siete bloques, procedencia, cobertura y matriz de avisos con decisiones respaldadas. El original del agente y las aportaciones se mantienen; el HTML no hace nuevas llamadas al modelo. Las revisiones históricas no cambian de contrato automáticamente. La copia exportable queda en full-stack-code-analyst/, sin importar módulos ni rutas de la oficina.

El [patrón de extracción](PATRON_EXPORTACION_AGENTES.md) es la referencia para un futuro agente orquestador con equipo. Se conserva el almacenamiento nativo por corrida y se documentan las diferencias de contexto, herramientas y permisos entre adaptadores.

## Validación realizada, sin nuevas llamadas al proveedor

- 6 pruebas de test_iris.py: siete tareas, aislamiento, síntesis, presupuestos e interrupciones y dos rondas de seguridad.
- 3 pruebas de test_iris_delivery.py: núcleo/plantilla/preguntas sin divergencia, decisiones de dependencia solo tras D03 y con fuentes visibles, artefactos nativos, escape de contenido, históricos y rechazo de resultados de otra captura.
- verify_report.py, verify_features.py y verify_local.py del portable: formato fijo, permisos y confinamiento, procedencia, matriz, fallos/caché y publicación.
- sync-iris-contract.py: paridad de las copias del núcleo y plantilla, comprobada también en CI. El portable incluye sus archivos, no usa enlaces simbólicos a la oficina.
- Reutilización de la corrida a0477b24-63c5-4899-9267-dcd7f92de06f: reconstrucción explícita como histórica, sin reanalizar. Se conservaron 40 preguntas, siete bloques, cuatro riesgos y 89 avisos OSV, todos pendientes de aplicabilidad. Original intacto; salida local de comprobación en artifacts/iris-interno-reutilizado/.
- Construida la imagen de pruebas arktic-backend-tests:0.6.0. No se hizo despliegue de servicios ni publicación de imágenes.

## Pendientes aceptados por el usuario

No se lanza una nueva corrida con IA ni se consume cuota de proveedor para este cierre. Queda pendiente validar detección/calidad de una corrida nueva. Las pruebas simuladas y la reconstrucción de datos históricos validan mecanismos, no demuestran paridad de detección ni mayor calidad del análisis.

La suite completa Linux y el arranque integrado de la nueva versión quedan pendientes. La ejecución amplia intentada en Windows no se considera validación completa: 168 pruebas/entradas, 10 errores relacionados con requisitos Unix (fcntl) y diferencias de filesystem. Se conserva el diagnóstico en artifacts/iris-office-suite.log. La solicitud de ejecutar la suite Linux fue rechazada; no se ejecutó. No se ocultan esos pendientes tras las pruebas dirigidas correctas.

Se prepara commit y push a la rama actual del repositorio de oficina por solicitud del usuario. No se fusiona a main, no se crean tags ni GitHub Releases y no se reescriben las corridas anteriores.
