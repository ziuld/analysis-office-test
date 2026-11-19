# Propuesta de evolución tras Iris 0.1

Estado: cinco mejoras incorporadas al paquete 0.1: procedencia, matriz de dependencias, Semgrep opcional con Docker, cobertura/comparación y protocolo de evaluación independiente. Esta página conserva la propuesta aprobada y sus criterios de aceptación. La evaluación independiente de detección requiere un chat nuevo del usuario; no se presenta como realizada en el chat que ya conoce los hallazgos. Las pruebas técnicas del runner no sustituyen esa evaluación. Alcance cerrado, sin nuevas líneas de trabajo.

## Qué ocurrió en la prueba

La revisión de Web Corporativa del 19/11/2026 reutilizó las respuestas y los hallazgos de la primera revisión como punto de partida. Se contrastaron partes del código, se ejecutaron Graphify, Gitleaks y OSV y se incorporó evidencia. Semgrep no se ejecutó. Es una revisión ampliada con antecedentes, no una medición independiente de detección. Recalcular las herramientas con `--force-review` o `--refresh` no elimina el contexto que ya conoce el chat.

## Mejoras propuestas

| Prioridad | Mejora | Motivo | Beneficio y criterio de aceptación |
| --- | --- | --- | --- |
| 1 | Registrar el modo: reutilización, ampliación o revisión independiente; vincular revisión base y evidencia reutilizada. | Hoy una nueva carpeta o un escaneo nuevo puede confundirse con un análisis desde cero. | Trazabilidad: el estado y el informe explican qué se reutilizó, qué se leyó de nuevo y qué cambió. |
| 1 | Matriz de aplicabilidad de dependencias. | Un único hallazgo agrupa paquetes y avisos con condiciones muy distintas. | Por aviso: paquete/versión, runtime o desarrollo, consumidor, plataforma, condición, defensa, decisión, corrección y prueba pendiente. Separar prioridad de actualización de gravedad demostrada. |
| 1 | Semgrep opcional local o en Docker disponible, con documentación previa. | La lectura manual no sustituye Semgrep; preparar WSL o instalar Docker durante la revisión complica el flujo. | Aplicar la detección y las elecciones descritas abajo. Documentar Docker como preparación opcional recomendada para ampliar cobertura, especialmente en Windows. |
| 2 | Mejorar cobertura y presentación de cambios. | Tener 40 respuestas no prueba profundidad; cuesta distinguir novedades y repeticiones. | Cada bloque registra recorridos, fuentes nuevas o reutilizadas y pendientes. Resumen breve con prioridad y acción; diferencias con la base: nuevos, mantenidos, resueltos o pendientes. Solo declarar resuelto con evidencia. |
| 2 | Una prueba final independiente en un chat nuevo sin informes previos. | El historial orienta hacia problemas ya conocidos. | El usuario abre el chat con su modelo; Iris no lanza sesiones secundarias. Comparar contra la referencia después de cerrar el informe. Registrar omisiones y falsos positivos y finalizar esta ronda sin ampliar su alcance. |

## Flujo acordado para Semgrep y Docker

Primero comprobar que Semgrep puede ejecutarse y que Docker tiene su motor accesible; no basta encontrar sus comandos. No instalar Docker ni WSL durante la revisión.

| Disponibilidad | Elección que se presenta |
| --- | --- |
| Semgrep y Docker funcionan | Contenedor temporal recomendado, ejecución local o continuar sin Semgrep. |
| Solo Semgrep funciona | Ejecutar localmente o continuar sin Semgrep. |
| Solo Docker funciona | Ejecutar en contenedor temporal o continuar sin Semgrep. |
| Ninguno funciona | Avisar y continuar con las demás herramientas; Semgrep queda pendiente. No ofrecer «Preparar Semgrep» ni instalar Docker implícitamente. |

Mensaje con Docker disponible:

> Podemos ampliar la revisión con Semgrep, que detecta patrones de seguridad en el código. ¿Cómo quieres continuar?
>
> - Ejecutarlo en un contenedor temporal (recomendado). Puede descargar una imagen la primera vez.
> - Ejecutarlo localmente (solo si Semgrep funciona).
> - Continuar sin Semgrep; el informe indicará esta comprobación pendiente.

Mensaje si ninguno funciona:

> Semgrep no está disponible y Docker tampoco está listo para ejecutarlo. Continuaremos con las demás herramientas y dejaremos esta comprobación pendiente en el informe. Para futuras revisiones puedes instalar y preparar Docker previamente; es opcional.

La vía Docker utilizará una imagen con versión declarada y una copia de archivos seleccionados montada en solo lectura. Durante el análisis no tendrá acceso a la red, al socket Docker ni permisos privilegiados. Las reglas se incluirán localmente y los resultados y temporales se guardarán dentro de `.local/`. Se eliminará el contenedor al terminar; la imagen podrá conservarse para evitar descargas repetidas. La caché identificará motor, versión/imagen, reglas y entrada; no mezclará resultados incompatibles. Un fallo permitirá continuar con cobertura parcial y diagnóstico claro. El aislamiento reduce riesgos, no garantiza seguridad absoluta.

Actualizar README, AGENT.md y guías de integración y ejecución con: Docker opcional y recomendado para facilitar Semgrep aislado, especialmente en Windows; Docker instalado y arrancado antes de invocar Iris; posible descarga inicial; ausencia de instalación automática de Docker/WSL; continuidad sin Semgrep; ubicación y reutilización de resultados. No presentar Docker como requisito general ni como capacidad implementada antes de probar la integración.

## Orden recomendado

Primero registrar procedencia y modos, después desglosar dependencias e incorporar Semgrep/Docker con sus instrucciones. Ajustar presentación y cerrar con una evaluación independiente. La caché de herramientas puede reutilizarse si corresponde a la misma entrada, motor, versión y reglas; se declara ese uso y no se reutilizan las conclusiones anteriores en la evaluación independiente. Comparar tiempo y consumo solo si hay mediciones. Quedan fuera de esta ronda las instalaciones de Docker/WSL y pruebas dinámicas, de carga o restauración; sus pendientes se conservan en el informe.

## Versionado

`VERSION` es la fuente de la versión del agente; comienza en `0.1`. Cada entrega posterior cambia ese archivo y documenta sus cambios en `CHANGELOG.md`. Las versiones de Graphify y demás herramientas permanecen separadas en `tools/versions.json`. Un cambio de versión o de archivos mantenidos cambia el perfil del paquete y obliga a comprobar la vigencia del informe; las herramientas se reutilizan cuando sus propias claves siguen siendo compatibles. Los informes anteriores se conservan con su procedencia original.
