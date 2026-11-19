# Iris · Extracción individual

La entrega es [`full-stack-code-analyst/`](../full-stack-code-analyst/README.md), una carpeta versionable de instrucciones y recursos. Se copia entera a otro proyecto y se invoca con `Usa ./full-stack-code-analyst/AGENT.md para que Iris analice este repositorio`.

## Alcance

- Iris usa directamente el chat de Codex, Claude Code u OpenCode que el usuario tiene abierto, con su modelo y esfuerzo actuales, también para interpretar Graphify. El paquete contiene instrucciones, plantilla HTML, scripts Python y versiones de herramientas. La primera versión usa un único rol, Iris.
- Al comenzar, `status` calcula huellas y comprueba resultados e informes vigentes dentro de `.local/`. Un informe vigente puede abrirse sin repetir los siete bloques. El destino es obligatorio dentro del agente instalado en el proyecto; ante denegación se pide permiso y se reintenta allí, sin copiar a otro workspace. Solo se eligen herramientas. [Flujo local](../full-stack-code-analyst/docs/ejecucion-local.md)
- Se ejecutan siete bloques en secuencia con las Q01–Q40 originales. Cada bloque conserva respuestas, citas, hallazgos y pendientes. Los dos bloques de seguridad conservan dos rondas de investigación. El séptimo recoge los resultados anteriores y cierra la síntesis.
- Se genera un HTML autocontenido con resumen ejecutivo, análisis por preguntas y anexos. La plantilla incorpora estilos, logotipo y navegación del informe de Arktic. Las fichas, entradas, herramientas, resultados y el informe se guardan dentro de `.local/` del agente.
- Graphify, Gitleaks, Semgrep y OSV tienen cachés separadas por entrada y versión. Los cambios locales y archivos nuevos se detectan. Los cambios de rama o commit con contenido idéntico pueden reutilizar análisis. Los avisos OSV conservan fecha y se actualizan por elección. Los scripts evitan reutilizar resultados fallidos o archivos modificados.

La extracción conserva las guías y el estándar editorial de la oficina. En cada asistente se comprueba con una copia del paquete, un proyecto de prueba común, la pregunta de destino y las siete salidas. Las conclusiones se contrastan sobre la misma evidencia. [Corrida integral de referencia de la oficina](PLAN_COORDINACION_CENTRALIZADA.md#prueba-integral-de-iris-con-35-minutos--12112026)

## Validación local

- **Codex** esperó la elección de destino y generó `./informe-iris.html` en el proyecto ficticio. Chrome abrió el archivo local y desplegó el bloque 7 al navegar a Q40.
- **OpenCode** mostró el menú por texto en modo no interactivo y esperó la ruta. Generó `./salidas/revision-del-proyecto.html` tras recibir la opción 2.
- Ambos informes pasaron la comprobación de los siete bloques en orden, las 40 preguntas únicas, los rangos de cita, los enlaces internos y los recursos embebidos.
- **Ejecutor local** probado con proyectos ficticios para reutilización, cambios sin commit, archivos nuevos, ramas, commits sin cambios de contenido, entradas por herramienta, publicación y exportación. La comprobación está en `scripts/verify_local.py`.
- **Graphify** generó un grafo estático con la CLI 0.9.9; **Gitleaks 8.30.1** se instaló desde el release oficial y analizó una copia privada. Ambos reutilizaron sus cachés en una segunda preparación. **OSV 2.7.0** se instaló desde el release oficial y se probó sobre dependencias ficticias. Semgrep queda pendiente de ejecución en plataforma compatible.
- **Claude Code** queda pendiente de una sesión autenticada para realizar la misma prueba.

## Traslado a INTERNO - IA

Después de la validación local y con permiso de escritura, copiar la carpeta `full-stack-code-analyst/` directamente a `C:\Users\LuisDanielHernandezM\Ai\Arktic\INTERNO%20-%20IA` y añadir la entrada en la tabla del README raíz.

Para la distribución se copian los archivos mantenidos del paquete y se conserva `.local/` como almacenamiento privado de cada proyecto.

~~~markdown
| [`full-stack-code-analyst/`](full-stack-code-analyst/) | Iris revisa un repositorio en siete bloques y genera un informe HTML Arktic | [README](full-stack-code-analyst/README.md) |
~~~

Antes de integrar una iniciativa, consulta las instrucciones y el historial del repositorio destino. La copia manual inicial se entregó siguiendo las ramas feature/ y mensajes [#identificador] observados; este repositorio de oficina mantiene su propio historial.

## Adaptación de vuelta a la oficina

El portable 0.1.2 e Iris interno 0.2.0 comparten núcleo de presentación y plantilla mediante contrato 1.1. El portable incluye sus copias y funciona sin la oficina; el integrado conserva Core y su runtime. La IA entrega datos y un generador fijo construye el HTML. El [patrón de exportación](PATRON_EXPORTACION_AGENTES.md) recoge decisiones, errores encontrados, límites y cómo repetir el proceso con un futuro orquestador y equipo. El [cierre backend 0.6.0](CIERRE_IRIS_0.6.0.md) registra la validación y lo pendiente.
