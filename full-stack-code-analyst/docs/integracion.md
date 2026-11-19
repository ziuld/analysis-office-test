# Usar Iris en distintos asistentes

La integración común es una instrucción con ruta explícita. Copia la carpeta completa al proyecto, abre el proyecto en el asistente y pega este mensaje.

> Usa `./full-stack-code-analyst/AGENT.md` para que Iris analice este repositorio.

| Asistente | Entrada |
| --- | --- |
| Codex | Abre el chat del proyecto y usa el mensaje anterior. `AGENTS.md` es una entrada breve si ya estás en la carpeta de Iris. |
| Claude Code | Abre la sesión en la raíz del proyecto y usa el mismo mensaje. `CLAUDE.md` remite a las instrucciones de Iris. |
| OpenCode | Abre el proyecto y envía el mismo mensaje a un agente con lectura y permiso de escritura para el informe. `AGENTS.md` remite a `AGENT.md`. |

Los asistentes tienen reglas diferentes de descubrimiento de instrucciones en subcarpetas. La ruta explícita funciona como entrada común y permite incorporar Iris a un proyecto que ya tenga sus propias instrucciones. Si el equipo quiere un acceso permanente, puede añadir a sus instrucciones existentes una línea que remita a `./full-stack-code-analyst/AGENT.md` cuando se solicite una revisión con Iris.

Iris trabaja directamente en el chat que la invoca y hereda su modelo y esfuerzo de razonamiento. La elección se hace en la interfaz del asistente. Todos los bloques y la interpretación de Graphify se resuelven en esa misma sesión. El informe identifica el modelo únicamente cuando la sesión ofrece ese dato.

## Comprobación al copiar a otro proyecto

Preparación opcional recomendada: tener Docker instalado y su motor Linux arrancado facilita Semgrep aislado, especialmente en Windows. Iris detecta Semgrep local y Docker y ofrece solo vías disponibles. Si no hay ninguna, continúa con las otras herramientas y declara Semgrep pendiente. No instala Docker ni WSL; la descarga inicial de la imagen requiere aceptación. No hace falta Docker para usar Iris.

1. Copia la carpeta a un repositorio de prueba que puedas analizar con el asistente elegido.
2. Envía el mensaje y verifica que Iris compruebe la caché con `status` desde la copia instalada en el proyecto. Para una revisión nueva, verifica que cree su `.local/` y escriba exclusivamente allí. Si se deniega acceso, debe solicitar permiso para esa ruta y detenerse si no se concede; no copiarse a otro workspace. Verifica las opciones de herramientas. La interpretación debe continuar en el mismo chat. [Flujo local](ejecucion-local.md)
3. Revisa que complete los JSON por bloque y ejecute render para guardar fichas e informe con las cuatro tarjetas y la jerarquía Arktic fija. El bloque 7 recoge evidencias previas de la misma revisión. Deben figurar siete bloques, Q01–Q40 únicas, citas y pendientes.
4. Abre el archivo local con el navegador, comprueba la navegación entre preguntas y riesgos y confirma que el resultado se encuentre en la ruta acordada.
5. Invoca Iris de nuevo sin cambios y elige abrir el informe guardado. Cambia después un archivo de código, cambia de rama y añade un archivo nuevo para comprobar que las huellas se actualicen. Los cambios de referencias con contenido idéntico pueden reutilizar herramientas.

Para comparar la calidad con Arktic Office, usa la misma revisión del código y contrasta las evidencias y la cobertura, además de la estructura del informe. La revisión con cada asistente depende de sus herramientas y del acceso de su sesión.

Una revisión que aprovecha informes anteriores se prepara como ampliación con base vinculada. Para evaluar detección sin pistas, sigue [la prueba independiente](prueba-independiente.md) en un chat nuevo y compara después de cerrar. La [evidencia estructurada](evidencia-revisiones.md) registra procedencia, cobertura y evolución.
