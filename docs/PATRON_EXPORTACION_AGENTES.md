# Patrón de extracción y adaptación de agentes

Caso inicial: Iris, 19/11/2026. Sirve de base para un futuro orquestador con equipo; el número de roles y sus límites podrán cambiar. No presupone que la oficina y el portable tengan versiones o runtimes idénticos.

## Qué hicimos

1. Identificamos el comportamiento que se quería extraer: siete bloques, Q01–Q40, dos rondas de seguridad, evidencia, condiciones y síntesis en HTML Arktic. No copiamos interfaz, Docker Compose, Hermes, credenciales ni la ejecución de la oficina.
2. Creamos una carpeta autónoma fuera del paquete backend: `full-stack-code-analyst/`. Incluye README, AGENT.md, AGENTS.md, CLAUDE.md, skill y referencias, scripts, plantilla, versiones y documentación. Se invoca por ruta explícita desde Codex, Claude Code u OpenCode.
3. Acordamos el contexto: el portable usa el modelo y esfuerzo del chat que lo llama. No abre sesiones secundarias ni exige claves API para interpretar Graphify. La oficina sigue usando su proveedor configurado mediante Core.
4. Añadimos herramientas deterministas opcionales y caché por contenido, versiones, reglas e integridad. Semgrep puede ejecutarse localmente o en un contenedor Docker disponible, con aceptación; no instala Docker/WSL. Una herramienta ausente deja cobertura pendiente, sin presentar ausencia de alertas como garantía.
5. Cerramos el almacenamiento: todo el trabajo portable queda en `.local/` del agente instalado dentro del proyecto. Se crea al iniciar; ante denegación se pide permiso y se reintenta en la misma carpeta. No se copia a outputs/otro workspace como alternativa. Los datos privados de pruebas no se distribuyen.
6. Distinguimos revisión nueva, ampliación con base e independencia declarada en un chat nuevo. Recalcular herramientas no borra el historial. La primera evaluación ampliada no se presentó como una detección independiente.
7. Tras una regresión visual, dejamos la IA a cargo de JSON y fijamos el renderizado. Se prueban tarjetas, encabezados, IDs, escape y correspondencia de HTML/fichas con datos, además de abrir el resultado en navegador. Los escáneres y el generador no garantizan corrección semántica.
8. Separamos un núcleo de presentación sin IO y adaptadores por entorno. Incorporamos las mejoras a Iris interno conservando snapshots, checkpoints, presupuestos, escáneres y almacenamiento propios. Las corridas históricas conservan su contrato; las nuevas identifican el contrato compartido.

## Fuente canónica y entregables

| Elemento | Fuente canónica en este repositorio | Copia incluida en el portable |
| --- | --- | --- |
| Generador neutro | `backend/src/arktic_office/reporting/iris_core.py` | `full-stack-code-analyst/scripts/iris_core.py` |
| Plantilla autocontenida | `backend/src/arktic_office/resources/assets/iris-template.html` | `full-stack-code-analyst/plantillas/informe.html` |
| Adaptador de oficina | `reporting/iris_delivery.py` y perfil interno | No se distribuye: usa Core y snapshots |
| Adaptador portable | `scripts/report_renderer.py`, `iris.py`, `storage.py` | Se distribuye completo, sin importar la oficina |

`python scripts/sync-iris-contract.py` comprueba hashes. `--write` actualiza las dos copias desde su fuente canónica tras revisar un cambio. La copia exportada funciona sin rutas a este repositorio ni enlaces simbólicos. Las 40 preguntas y su reparto se comprueban también en tests; las instrucciones de herramientas, permisos y ejecución pueden diferir deliberadamente.

Iris interno 0.2.0 y portable 0.1.2 comparten contrato 1.1. Son versiones de productos distintos. Las dependencias Hermes/Hermes3D mantienen sus pins; mejorar el agente de Arktic Office no significa publicar una versión de esos proyectos externos.

## Mejoras incorporadas a la oficina

Las nuevas corridas Iris guardan `agents/full-stack-code-analyst/iris-contract.json`, `procedencia.json`, `cobertura.json`, `dependencias.json`, `hallazgos.json` y siete fichas. El informe usa el mismo núcleo y plantilla, sin nuevas llamadas al modelo para renderizar. Los originales y anexos de herramientas siguen disponibles.

El bloque backend puede entregar decisiones por aviso tras consultar D03 y leer fuentes. Core conserva pending para lo no investigado, rechaza decisiones sin fuente o sin aviso registrado y distingue ámbito, función, plataforma, condiciones, defensas, prioridad y corrección. Las versiones corregidas pueden pertenecer a ramas diferentes. El resultado OSV completo se toma de la carpeta de esa corrida, comprobando repositorio y commit; no de un resultado externo o de otra revisión.

La procedencia declara snapshot y tareas de la misma corrida y si se reutilizó preparación. No certifica independencia semántica del proveedor. No se comparan corridas automáticamente ni se declara un problema resuelto por desaparecer. Las huellas de hallazgo internas incluyen observación y fuentes: una reformulación exige correlación humana. El portable conserva su comparación explícita con una revisión base.

## Cómo repetirlo para un orquestador y equipo

- Definir primero roles, entradas, salidas, orden/dependencias, presupuesto total y reservas, aislamiento de contexto y política de fallos. Determinar qué se comparte entre especialistas y qué reutilización histórica se permite.
- Extraer instrucciones y contratos, no el runtime de la oficina. El adaptador portable decidirá cómo ejecutar roles con las capacidades del asistente; no asumir subagentes disponibles ni cambiar el modelo sin autorización. El integrado conservará Core.
- Definir un esquema común de contribuciones, citas, certeza, gravedad, pendientes y síntesis. Preservar autoría y desacuerdos; no convertir una síntesis en validación adicional de todas las conclusiones.
- Reutilizar el núcleo de presentación si el contrato sigue encajando. Si cambia, versionarlo, mantener adaptadores y probar históricos. No forzar silenciosamente un equipo al esquema individual de Iris.
- Probar límites, interrupciones, datos no confiables, herramientas ausentes, permisos, caché y renderizado. Hacer una evaluación independiente solo en un chat sin antecedentes, cerrando antes de contrastar con la referencia. Distinguir pruebas técnicas simuladas de detección real.
- Versionar agente/contrato/oficina por separado y documentar compatibilidad, validación y límites. Preparar una entrega limpia sin `.local`, cachés, copias de código o credenciales; verificar archivos antes de copiarla a iniciativas.

## Cierre y mantenimiento

Las exportaciones no obligan a reemplazar el agente integrado. Primero se prueba la mejora afuera; después se adapta y se valida en la oficina. No se copian permisos, rutas ni configuraciones entre entornos de forma ciega. Los cambios futuros que afecten al contrato canónico deben actualizar la copia portable y pasar las comprobaciones de paridad antes de publicarse.
