# Implementación de coordinación centralizada · 30/10/2026

Referencia: `76abf0f`. Único plan: [PLAN_COORDINACION_CENTRALIZADA.md](PLAN_COORDINACION_CENTRALIZADA.md). Trabajo local sin commit, push ni publicaciones. Se conservan las modificaciones de documentación que ya existían y la corrección del orden de dibujo del sofá.

## Implementación

Core sirve el catálogo único de Akira y los siete especialistas. Ejecuta Inventario, Arquitectura, Datos, Seguridad, Seguridad frontend, Seguridad backend y Devops de forma secuencial. Cada etapa recibe una selección de respuestas previas pertinentes con autor y referencias; las conclusiones anteriores no sustituyen la lectura de las fuentes originales.

Las cuarenta preguntas mantienen sus identificadores y textos. Cambia únicamente su responsable principal. La copia exacta del catálogo de referencia tiene SHA-256 `e1ae857f1b66b64a615760d42372c14e1d8e4d51d8ff3728793fda14f47bad05`. Q38–Q40 corresponden a Akira, que consolida defensas, condiciones, impacto y comprobaciones de los autores sin una pasada adicional de especialistas.

El montaje `reports` conserva SQLite en `.knowledge/office.sqlite`, artefactos referenciados y los espacios `agents/<id>/` con encargo, notas, resultado y resumen. Las notas no se publican como hechos. Los estados interrumpidos quedan registrados sin repetir automáticamente llamadas de resultado remoto desconocido. Se mantienen `estado.json`, `celulas/` y los informes actuales.

El presupuesto global reserva la salida máxima antes de cada llamada y registra modelo efectivo, esfuerzo, huella del prompt, bytes reenviados, bytes repetidos por líneas idénticas, duración y uso comunicado por el proveedor. Los bytes repetidos son una medida determinista, no una estimación de tokens facturados. Sin métricas del proveedor se conserva `null`, no cero. Los límites remotos de salida no son una garantía de corte al token exacto.

La configuración anterior permitía como máximo 29 llamadas de especialistas y dos de Akira. Las rondas iniciales se reparten sin multiplicar ese máximo: tres para cada especialista salvo cuatro para Seguridad backend, más su respuesta final. Las variables antiguas de rondas de Inventario y Arquitectura pueden reducir ese reparto, pero no ampliarlo. Modelos y esfuerzo siguen los valores configurados; las variables nuevas de perfiles usan guiones bajos, por ejemplo `AUDIT_BACKEND_SECURITY_MODEL`.

Las consultas se encolan detrás de una revisión o consulta activa. Una consulta que consiste exactamente en un ID ya respondido se resuelve desde Core. Las demás usan un único responsable y contexto guardado. Un fallo global cancela las consultas pendientes, conserva lo válido y no genera reintentos automáticos.

La oficina dispone de ocho personas/escritorios y consulta por perfil. Las tarjetas muestran primero la persona, rol debajo y datos compactos; el detalle conserva los motivos y límites. La reunión usa cuatro sillas de sala y los escritorios restantes. Akira conserva una plaza; la asignación es estable y termina al guardar el informe disponible o interrumpirse la revisión. La televisión muestra preparación y participantes silenciados, sin voz, cámara ni integración con Teams. Ninguna animación inicia llamadas. Se conserva la corrección del sofá y se amplían las pausas de ocio a 12–30 segundos, sin reducir velocidad.

## Pruebas y evidencias

Las evidencias locales están en `artifacts/central-coordination/`. No contienen nuevas publicaciones ni sustituyen informes anteriores.

- La referencia inicial reprodujo 177 pruebas: 174 correctas, dos fallos y una omitida (`baseline-tests.log`).
- El test antiguo de huellas fallaba antes de comprobar los tres formatos: prompts, estándar editorial, estilos y navegación ya habían evolucionado. Se conserva el archivo de referencias y se comprueba que los tres esquemas históricos siguen renderizando conclusiones, commit y fuentes, además de las pruebas de historial sin modificaciones. No se han actualizado hashes para obtener verde.
- El test antiguo de cobertura mezclaba expectativas de HTML y Markdown: HTML usa «Dominios pendientes» y omite el bloque vacío; Markdown conserva «Evaluación pendiente en» y los motivos en el anexo. Ahora se comprueban los seis dominios, la insuficiencia explícita y el comportamiento propio de cada formato.
- Las pruebas de tres agentes se adaptan al reparto de siete, conservando las comprobaciones de citas ajenas, fallos independientes, contratos y ausencia de reintentos.
- Frontend: 12 pruebas correctas en oficina/mapa, estados, consultas conservadas y visor (`frontend-tests.log`). Incluyen cuatro plazas reales, cuatro asistentes remotos, plaza de Akira, asignación estable, posiciones distintas y liberación al finalizar. La simulación de ocio sobre el mismo mapa, con ocho personas y velocidad idéntica, mide 456 recorridos en 600 segundos con las pausas anteriores y 178 con las nuevas: frecuencia del 39 % de la anterior, una reducción del 61 %.
- Semgrep: configuración válida, cero errores y 14 reglas (`semgrep-validation.log`).
- Compilaciones de Core y frontend realizadas en Docker, con los tres servicios y el puerto local existentes. No se añaden Redis, servicios permanentes, volúmenes ni puertos.

Backend: **190 pruebas, 189 correctas y una omisión preexistente**, sin fallos (`backend-final-tests.log`). La suite prohíbe procesos externos y conexiones remotas. Incluye contratos históricos, igualdad exacta de preguntas, búsqueda paginada, consultas de cada perfil, bloqueo de dependencias, fallo global, reserva de presupuesto, exceso comunicado por el proveedor, interrupciones de SQLite y consultas desde Core sin actividad ficticia de modelo.

Persistencia real: `storage-before-recreate.json` y `storage-after-recreate.json` son iguales. SQLite supera `integrity_check`; conserva 8 tareas y 98 hechos, la identidad de revisión y las mismas huellas de informes JSON, HTML y Markdown. La reunión queda cerrada al estar disponible el informe.

Descargas: `download-verification.json` compara por bytes y SHA-256 el HTML y Markdown de la referencia y de la nueva ejecución a través del proxy. Los cuatro archivos coinciden con los guardados y conservan cabeceras de descarga. El HTML nuevo contiene exactamente una ancla para cada Q01–Q40 y no presenta bloques públicos de código o JSON del grafo.

Preparación: `preparation-reuse.json` registra la generación compatible con las reglas actuales y una segunda lectura de la misma clave, sustituyendo escáneres y Graphify por funciones que fallarían si fueran llamadas. Esa lectura reutiliza la preparación, sin repetir ninguna herramienta ni llamar a modelos. Los resultados de Gitleaks, OSV y Semgrep con detecciones siguen siendo alertas para contrastar; no se consideran explotaciones demostradas.

API final instalada: `api-verification.json` confirma ocho perfiles y ocho rutas de historial de consulta, informe disponible, reunión cerrada y actividad de trabajo desactivada. Una consulta explícita de Q08 a Arquitectura se resuelve desde Core, con `model=null`, sin actividad ficticia de modelo ni consumo adicional: el contador permanece en 31 llamadas. El perfil de Seguridad histórico conserva un acceso de consulta separado; los perfiles nuevos no se presentan como participantes de revisiones antiguas.

El parche del frontend se regeneró conservando la corrección del sofá y se verificó con `git apply --reverse --check` sobre la copia local. `git diff --check` no registra errores. No se ha realizado commit, push, merge ni publicación. Los tres contenedores quedan saludables, con el único puerto previo `127.0.0.1:3000` y los montajes persistentes existentes.

## Comparación real y límite de la entrega

Se realizó una sola ejecución real: `1df56a5f-6b84-478c-a0af-0a6fec12df1b`, comparada con `2697cb5e-b168-41f1-a5bd-714b7ba0d9ff`. Ambas usan el commit `4ae82b4097b3b01360bd8c6fb6d779b210f50564`, exactamente el mismo inventario y las mismas cuarenta preguntas, con `gpt-6.1-sol`, esfuerzo `medium` y techo solicitado de 8.000 tokens por llamada de especialista. No se ejecutó el código analizado ni se instalaron sus dependencias.

| Métrica | Referencia | Coordinación centralizada |
| --- | ---: | ---: |
| Llamadas comunicadas | 19 | 31 |
| Tokens de entrada | 692.377 | 1.165.061 |
| Tokens de salida | 16.707 | 24.259 |
| Tokens totales | 709.084 | 1.189.320 |
| Preguntas respondidas | 12 | 4 |
| Preguntas parciales | 23 | 24 |
| Preguntas no comprobadas | 5 | 12 |
| Rutas de texto entregadas | 94 | 100 |
| Duración de análisis | ≈709 s | 1.044 s |

**No se ha demostrado ahorro ni mejora de cobertura.** El total de tokens aumenta un 67,7 %. Las doce llamadas adicionales explican la mayor parte del incremento: se alcanzaron las rondas máximas de los siete especialistas. Entregar seis rutas más no compensa la pérdida de preguntas respondidas. La duración anterior es aproximada, obtenida de las fechas guardadas; la nueva usa el registro monotónico. Es una comparación histórica de un caso, con instrucciones y reglas distintas, no un experimento controlado de calidad semántica.

La nueva ejecución queda **parcial**. Once respuestas se rechazaron por citas que no superaron la validación. Las doce preguntas no comprobadas son Q04, Q05, Q06, Q07, Q16, Q17, Q19, Q20, Q21, Q28, Q31 y Q33; se conservan con su pregunta, motivo y pendiente. Las restantes aportaciones válidas se mantienen. No se han reparado citas, añadido un revisor ni repetido llamadas para elevar estas cifras. La matriz completa está en `artifacts/central-coordination/question-matrix.md`; los datos, en `comparison.json`.

El presupuesto explícito fue de 31 llamadas, 244.000 tokens de salida **reservados**, 8 MB de contexto acumulado y un límite global de tiempo de 7.440 segundos, con límites de encargo y llamadas existentes. No equivale a un techo de 244.000 tokens totales: la entrada se controla por bytes de contexto y está incluida en el consumo real de la tabla. Se reenviaron 4.213.464 bytes, de los cuales 1.946.976 repiten líneas exactas ya enviadas. No hubo parada global ni exceso de salida comunicado por encima del techo solicitado por llamada; el máximo comunicado fue 3.304 tokens. Los límites OAuth son blandos: el Core final también carga cualquier exceso comunicado antes de admitir otra llamada.

El manifiesto de la ejecución conserva la identidad del código que la produjo. Después se cerraron ajustes de compatibilidad de historial, actividad de consultas resueltas desde Core, carga de excesos de proveedor y aceptación de la operación redundante `query=list_paths` sin ampliar su alcance. PHP y Go se incorporaron a las entradas de las reglas ya validadas; no hay archivos de esos lenguajes en el repositorio comparado. Estos ajustes se verifican sin relanzar modelos; no se atribuye al código posterior una nueva medición de calidad o ahorro.

## Pendiente solicitado por el usuario

La revisión visual con Chromium queda aplazada. Las capturas de intentos y la prueba de navegador se conservan para continuar después; no se presentan como una verificación visual cerrada. La frecuencia de ocio se ha medido en simulación determinista, pendiente de confirmar visualmente en el navegador.

La eficiencia y la calidad de respuestas constituyen una limitación real de esta entrega: la infraestructura y sus límites funcionan, pero esta prueba empeora el coste y la cobertura frente a la referencia. No se amplían presupuestos, no se cambian modelos ni se inicia otra comparación sin una nueva instrucción.

## Recomprobación del 31/10/2026

Los tres contenedores siguen saludables. Core conserva las 40 preguntas y la huella exacta del catálogo de referencia; informa de cero revisiones activas, cero consultas activas y ninguna consulta en cola. El parche del frontend supera de nuevo la comprobación de aplicación inversa y `git diff --check` no registra errores. No se han repetido análisis, llamadas a modelos ni comprobaciones con Chromium.
