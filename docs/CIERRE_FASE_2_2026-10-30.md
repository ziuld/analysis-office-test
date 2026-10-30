# Cierre de fase 2 — 30/10/2026

## Alcance publicado

Se conserva la ejecución actual de tres especialistas y coordinador. El cierre incluye:

- Informe ejecutivo con riesgos prioritarios y protecciones comprobadas, únicamente cuando hay evidencia válida.
- HTML y Markdown con anexos deterministas explicados en lenguaje natural; los originales se conservan internamente.
- Visualización del informe y descarga independiente del HTML y Markdown guardados, sin repetir el análisis.
- Preparación persistente verificada para reutilizar Graphify y escáneres sobre la misma captura compatible; renovación manual disponible.
- Instalación oficial de Graphify 0.9.97 con soporte SQL. El adaptador utiliza extracción estática; registrar la skill no ejecuta enriquecimiento semántico por IA.
- Límite de captura local configurable para revisar repositorios completos de mayor tamaño.
- Documentación de contenedores y propuesta de evolución, sin activar nuevos agentes ni cambiar la oficina.

No se han ejecutado nuevas llamadas a modelos para preparar este cierre. Los informes y capturas de repositorios locales no se incorporan al commit.

## Validación del cierre

Los tres contenedores existentes (`office`, `audit-api` y `preparator`) estaban saludables al comprobar el cierre.

Backend, suite completa en Docker sin red y con bloqueo de procesos externos: **177 pruebas; 174 correctas, dos fallos y una omitida**. Los dos fallos son discrepancias conocidas de expectativas antiguas:

- `test_installed_package_preserves_prompts_and_three_report_formats`: la huella esperada del prompt legado no coincide con las instrucciones actuales. Falla antes de comprobar las huellas de los formatos, por lo que ese caso no demuestra compatibilidad completa.
- `test_security_coverage_visible_even_with_zero_risks`: espera el texto antiguo «Evaluación pendiente en:», que no coincide con la presentación actual.

No se han cambiado esas expectativas ni el comportamiento del producto para ocultar los fallos. La suite completa no está en verde.

Frontend en Docker sin red, con `NODE_ENV=test`: **10 pruebas correctas** en estados de oficina, mapa, visor de informe y conservación de consultas. Graphify instalado: **tres pruebas de extracción correctas**, incluidas SQL y contabilización del YAML ocultado.

El parche versionado del frontend coincide por SHA-256 con el diff de la copia local de Hermes3D. `git diff --check` no registra errores después de normalizar el salto de línea final de la plantilla. La validación previa de la descarga comparó los archivos servidos por el proxy con los originales guardados; este cierre no vuelve a ejecutar el análisis del repositorio.

Evidencia de esta comprobación, conservada localmente en `artifacts/`:

- `release-close-docker-tests.log`
- `release-close-frontend-tests.log`
- `release-close-graphify-tests.log`
- `html-download-2026-10-30/download-verification.json`

La ejecución inicial de las pruebas de backend en Windows encontró dependencias de Linux (`fcntl`); la ejecución Docker es la referencia indicada arriba. El primer intento del frontend heredó `NODE_ENV=production`; al utilizar el entorno de pruebas apropiado los diez casos pasaron.

## Siguiente versión, sin implementar en este cierre

El usuario prefiere un orden secuencial que permita aprovechar los resultados anteriores: Inventario, Arquitectura y especialistas según sus dependencias. Si falla una tarea, se detendrán las dependientes; las independientes podrán continuar dentro del presupuesto. Un fallo global de proveedor, acceso o presupuesto debe impedir nuevas llamadas sin utilidad.

El panel pasará a tarjetas compactas: nombre de persona, rol debajo, actividad animada mientras ejecuta, modelo, duración, tokens disponibles, resultado y error breve visible. Los detalles se abrirán al pulsar. Cada personaje añadido tendrá escritorio y consulta.

Akira estará sentado cuando trabaje y disponible de pie al terminar; una consulta nueva lo devolverá al escritorio al ejecutarse. Se corregirá la posición de los asientos y se reducirán los paseos de ocio aproximadamente a un tercio.

El plan de evidencia compartida y especialistas está en `PLAN_COORDINACION_CENTRALIZADA.md`; su apartado inicial de decisiones posteriores prevalece sobre las alternativas de concurrencia del documento original.

La publicación se entrega como pull request abierto para revisión del usuario, sin fusionarlo.
