---
name: revisar-codigo
description: Revisa un repositorio con Iris mediante siete bloques de evidencia y reúne Q01–Q40, hallazgos y límites en un HTML Arktic. Se usa para revisiones estáticas solicitadas con Iris.
---

# Revisar código con Iris

Aplica [AGENT.md](../../AGENT.md) y empieza la revisión tras acordar la salida. Mantén el orden siguiente y abre cada guía cuando toque su bloque. En cada paso, empieza por los indicios y lecturas que esa guía señala.

| Orden | Bloque | Primeras fuentes | Guía |
| --- | --- | --- | --- |
| 1 | Aplicación | README, manifiestos y puntos de entrada | [Q04–Q07](referencias/01-aplicacion.md) |
| 2 | Estructura | Entradas, organización de módulos y configuración | [Q08–Q09](referencias/02-estructura.md) |
| 3 | Datos | Modelos, esquemas, almacenamiento y caché | [Q10–Q13](referencias/03-datos.md) |
| 4 | Operación | Scripts, pipeline, manifiestos y despliegue | [Q15–Q22](referencias/04-operacion.md) |
| 5 | Identidad y frontend | Rutas sensibles, sesión, permisos y renderizado | [Q23–Q31](referencias/05-seguridad-identidad-frontend.md) |
| 6 | Backend y datos | Validación, persistencia, secretos y salidas | [Q14 y Q32–Q37](referencias/06-seguridad-backend-datos.md) |
| 7 | Alcance y síntesis | Resultados y evidencias de los seis bloques anteriores | [Q01–Q03 y Q38–Q40](referencias/07-alcance.md) |

## Cierre de cada bloque

1. Enumera brevemente qué hay que comprobar. Lee tramos acotados y sigue el flujo hasta la implementación o configuración que respalde la conclusión. En los dos bloques de seguridad aplica las dos rondas de su guía. Usa los hallazgos preliminares de la primera para orientar la segunda.
2. Completa las respuestas y conclusión del bloque en `informe.json`, y actualiza los JSON de hallazgos y cobertura. Ejecuta `render` antes de avanzar: genera la ficha `bloques/01.md` a `07.md` y el HTML con el formato fijo. No edites HTML ni fichas generadas a mano. Usa la ruta de prepare dentro de la `.local` del agente instalado en el proyecto. Para cada pregunta aplica los estados del [contrato](../../docs/contrato-informe.md); una pregunta sin evidencia conserva su ID y pendiente.
3. Comprueba que cubriste todos los IDs de esa guía y que sus citas corresponden a lo leído. Cierra el bloque antes de pasar al siguiente. Cuando recuperes una evidencia, reutiliza su ruta y rango en lugar de volver a leer el archivo entero.

En cada cierre actualiza también `cobertura.json` con recorridos, fuentes nuevas/heredadas y pendientes. Registra los hallazgos con claves estables en `hallazgos.json`. En el bloque 6 clasifica los avisos de `dependencias.json` por uso, consumidor, plataforma, condiciones y corrección; conserva pending cuando falte evidencia y no elimines filas. En el bloque 7 revisa los cambios respecto a la base y prioriza acciones en el resumen. Sigue [la guía de evidencia](../../docs/evidencia-revisiones.md), ejecuta `render` y después `finish`. En modo independiente no consultes conclusiones históricas. Si faltan permisos de escritura pide acceso a la misma carpeta; no generes resultados en otro workspace.

El bloque 7 sintetiza las fichas anteriores, conserva discrepancias y enlaza con las fuentes. Usa las alertas de Gitleaks, Semgrep y OSV que correspondan a los flujos del bloque para confirmar, descartar o dejar pendiente cada pista. Describe la cobertura de herramientas ausentes o fallidas. Después reúne las siete fichas en un solo HTML y ejecuta `finish` según [el flujo local](../../docs/ejecucion-local.md). Si la sesión permite cerrar tras una interrupción, identifica el informe como parcial, conserva lo validado y marca como pendientes los IDs y bloques que quedaron abiertos.
