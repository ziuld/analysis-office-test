# Oficina y consultas — Bloque 6

Comportamiento actual de los personajes: mientras trabajan ocupan su puesto; al terminar quedan libres para recorrer las zonas de descanso, también tras un error. Seleccionarlos no les gira la cabeza durante el trabajo ni los retiene sentados. Los bocadillos de estado se limitan a actividad real. Se reutiliza la simulación existente; no hay llamadas a modelos por moverse en la oficina. Compilación y seis pruebas dirigidas correctas; incluido en la entrega aceptada 0.3.0, sin ampliar CI/CD.

La oficina proyecta los estados guardados por la API, la preparación, el coordinador y las células. Reutiliza el sondeo de dos segundos: no introduce SSE, otro servicio ni llamadas a modelos para animar. Las burbujas describen actividad observada, no conversaciones inventadas. Las transiciones más cortas que el intervalo pueden no mostrarse.

Preparación, reparto, trabajo especializado y síntesis se distinguen mediante textos y actividad. Solo la síntesis activa reúne a los personajes en revisión. Al terminar, abandonan el puesto y quedan libres en las zonas de descanso. El estado terminal prevalece sobre un fichero intermedio que aún diga «trabajando», incluso ante interrupción o información insuficiente. Una pérdida de conexión detiene las indicaciones de actividad.

Seleccionar un personaje no fuerza un giro de cabeza. Los asientos de la oficina compacta se alinean con los monitores y la profundidad de las sillas permite leer la postura sentada. Estos cambios se limitan a la oficina compacta; no sustituyen muebles ni amplían el mapa.

La consulta activa anima únicamente al personaje correspondiente y bloquea un segundo envío. Al terminar deja de indicar trabajo. El historial, confirmado por el usuario, muestra **las últimas diez consultas guardadas por revisión y agente**. Leerlo no invoca modelos ni cambia el informe. Cada pregunta nueva sigue siendo independiente y envía únicamente agente y pregunta, junto al contexto de evidencia que prepara el backend; nunca reenvía el historial de conversación.

La API interna añade `GET /runs/{id}/questions/{agente}` para esa lectura. Rechaza agentes desconocidos, no sigue enlaces simbólicos y limita el descubrimiento a mil ficheros antes de requerir revisión del almacenamiento. No elimina consultas antiguas. El caché anterior de última consulta permanece como ayuda de esta pestaña.

## Comprobaciones locales del 23–24/10/2026

- Backend: **117 ejecutadas, 116 correctas y 1 referencia visual opcional omitida** en 6,832 segundos. Suite manual previa y un único caso nuevo sobre estados terminales e historial acotado, separado y de solo lectura. Los datos y ejecutores son ficticios; sin red ni credenciales en el contenedor de pruebas.
- Interfaz: **8 pruebas correctas** en tres archivos afectados: mapa/orientación/parada, consultas y estados. Solo se añadió un caso de estacionamiento y orientación; el fixture anterior de consultas comprueba los POST por separado de las nuevas lecturas GET.
- Frontend construido desde fuentes limpias del commit fijado con comprobación de aplicar y revertir el parche. El build y TypeScript pasaron; imágenes frontend/backend 0.2.0 construidas.
- Revisión visual con datos ficticios y volúmenes nuevos: cuatro personajes sentados y alineados, orientación del seleccionado, historial de Seguridad separado de Inventario y apertura de una respuesta guardada. Una API temporal con ejecutor simulado permitió comprobar «1 trabajando», burbuja de consulta, bloqueo de envíos y vuelta a «0 trabajando» al completar la respuesta sin invocar modelos. No se utilizó el ejecutor real del proyecto.
- Oficina y API saludables. El acceso visual fue exclusivamente por `127.0.0.1:3100`; la API mantuvo su red interna y no recibió credenciales. El entorno y sus volúmenes se retiran al terminar.

Logs locales: `artifacts/block6-backend-final.log`, `artifacts/block67-frontend-tests.log`, `artifacts/block67-frontend-build.log` y `artifacts/block6-startup-final.log`. Capturas: `artifacts/block67-office.png`, `artifacts/block67-history.png` y `artifacts/block6-query.png`. Son artefactos de desarrollo excluidos de Git, no informes reales.

No se ejecutaron análisis de repositorios, scanners ni modelos reales. No se comprueba la calidad de sus respuestas ni se promete mostrar todos los eventos entre sondeos. CI/CD y versiones no cambian. El Bloque 7 y el cierre de entrega quedan pendientes; su trabajo adelantado se conserva aparte en `artifacts/block7-deferred.patch`.

El adelanto del Bloque 7 se puede comprobar antes de retomarlo con `git apply --ignore-whitespace --check artifacts/block7-deferred.patch`; no está aplicado ni forma parte del Bloque 6.

La repetición final descubrió un fallo de Next/Turbopack al procesar fuentes Google. Se retiró esa descarga del frontend y se usan familias del sistema con fallback; no se añadieron dependencias. La reconstrucción y el arranque finales del 24/10/2026 pasaron después de este ajuste: API/oficina saludables y HTTP 200, sin trabajos ni credenciales. La comparación desde fuentes limpias confirmó los 21 archivos del parche final; detalle en `artifacts/block6-source-final.json`.
