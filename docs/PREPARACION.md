# Preparación híbrida — Bloque 4

El modo híbrido prepara contexto para las tres células existentes. Se activa expresamente durante la transición; el modo habitual sigue siendo `legacy`. Cada revisión utiliza **un solo recorrido**, sin ejecutar ambos ni repetir scanners o especialistas. Las versiones permanecen en 0.2.0.

## Uso

Desde la raíz, con las fuentes y la sesión habituales ya preparadas:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml build audit-api preparator
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --wait
```

La oficina mantiene su entrada habitual. Una revisión normal en este modo puede añadir **hasta ocho llamadas de preparación**, además de las tres células; utiliza el modelo y razonamiento comunes. No inicia ninguna revisión por arrancar los servicios. Para inspeccionar sin scanners ni modelos:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit run --rm auditor https://github.com/propietario/repositorio --inspect-only
```

La inspección sí lee GitHub y solicita el mapa local, pero no prueba la calidad del explorador real. Para volver al recorrido anterior, sin trabajos activos:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml stop preparator
docker compose up -d --force-recreate --wait audit-api office
```

El override fija `AUDIT_PREPARATION_MODE=hybrid` y `AUDIT_INDEXER_URL=http://preparator:8090/index`. Este último es configuración del operador, nunca una URL suministrada por el repositorio o el modelo. El modo `legacy` también usa ahora la rama predeterminada real; conserva la selección heurística y las tres células.

## Recorrido y límites

1. Core consulta los metadatos de GitHub, resuelve la rama predeterminada —incluidas ramas con `/`— y fija su commit y árbol. Los blobs se descargan por SHA, sin volver a consultar la rama durante la revisión. Un árbol truncado se rechaza.
2. La adquisición aplica reglas locales de archivos y categorías; no depende de las decisiones del modelo. En híbrido admite hasta 120 archivos, 256 KB por archivo y 1 MB descargado, con comprobación de tiempo entre peticiones a los 180 segundos. Cada petición puede tardar hasta 30 segundos adicionales. Si falla una descarga, conserva lo adquirido y registra el resto como pendiente. No es una copia completa: dependencias, generados, pruebas, archivos sensibles y tipos fuera de la heurística quedan excluidos.
3. Los scanners, cuando se solicita una revisión normal, reciben una vez los archivos adquiridos, antes de ocultar posibles secretos. Su entrada se registra aparte; la ejecución y resultado de cada scanner mantienen sus estados propios. La inspección no los invoca. Los lockfiles completos nunca entran en las herramientas del explorador ni en el modelo.
4. Se ocultan posibles credenciales con las reglas existentes y las posiciones comunicadas por Gitleaks. La ocultación es heurística. El preparador independiente recibe solamente texto de ese conjunto, sin token GitHub, sesión Hermes, informes, socket Docker ni código del Core. Graphify fijado en 0.9.95 extrae AST sin clustering ni backend de modelo; no instala dependencias ni ejecuta el código recibido. Su red Docker es interna y no publica puertos.
5. La selección inicial ocupa como máximo la mitad de los archivos permitidos, reservando espacio para fragmentos descubiertos. Las herramientas restringidas operan sobre ese mismo conjunto adquirido: `search` literal (hasta 12 coincidencias con ruta/línea), `graph` (hasta 8 semillas, 24 nodos y 16 relaciones adyacentes) y `read` (hasta 100 líneas, 8000 bytes de resultado). El mapa es una pista: herencia, inyección, configuración y servicios externos requieren contraste con texto. No se descargan nuevos archivos durante la exploración.
6. Hermes devuelve una acción JSON por turno. El Core la valida y ejecuta la recuperación; Hermes conserva **cero herramientas de agente habilitadas**, sin shell, navegador, ejecución, escritura, configuración del repositorio ni acceso libre al sistema de archivos. El contexto recuperado vuelve como datos no confiables. No se usa el registro global de herramientas de Hermes.

El preparador limita cada solicitud a 2 MB, la entrada textual a 1 MB y la extracción a 300 segundos. El grafo devuelto admite hasta 12000 nodos, 24000 relaciones y 3 MB; los recortes y avisos dejan estado parcial. Salud y extracción se atienden por separado. Una extracción fallida conserva la recuperación textual y queda registrada; no dispara otro indexador ni reintenta automáticamente.

El explorador dispone de **8 llamadas, 180 segundos, 60000 bytes acumulados de prompts**, 8000 bytes por respuesta y hasta 60 segundos por llamada. No hay reintentos. Los límites globales existentes de contexto final siguen vigentes: por defecto 24 archivos, 12000 bytes por archivo y 120000 bytes totales; las lecturas nuevas se rechazan si no caben. Los especialistas conservan sus límites y su única pasada. Las líneas omitidas se dejan vacías para mantener citas al commit original.

`finish` declara suficiencia solo después de alguna lectura; es una declaración del explorador sobre contexto parcial, no garantía de cobertura completa. Los otros cierres distinguen insuficiencia, límite de iteraciones/contexto/tiempo y fallo técnico. La evidencia recuperada se conserva. Un cierre de preparación sin suficiencia mantiene parcial un equipo que por sí solo hubiese terminado completo.

## Registro y cobertura

`preparacion.json` guarda el estado progresivo y final, acciones solicitadas, fragmentos leídos, coincidencias de búsqueda, eventos v1 con secuencia/hora y cierre, límites, tiempos y consumo comunicado por cada llamada. Los eventos son locales; conectarlos a la oficina corresponde al Bloque 6. El estado final también queda en `evidencia.json` e `informe.json`.

`evidencia.json.coverage` separa archivos adquiridos, entrada a scanners, entrada al mapa, candidatos para especialistas y lecturas del explorador. `celulas/*.json` conserva los archivos y consumo de cada envío especializado. Los anexos HTML/Markdown muestran cobertura y cierre sin atribuir cobertura del scanner al modelo. Una medida de tokens ausente se registra como desconocida, nunca como cero. Los bytes y llamadas son límites locales; no equivalen a un techo monetario ni a un techo duro de tokens OAuth.

No se guardan ni reutilizan snapshots brutos ni grafos completos de este servicio: el directorio temporal se elimina al terminar cada extracción. Se conservan texto seleccionado y trazas, no una promesa de reproducción byte a byte del proveedor o del explorador. Los resúmenes del mapa indican entrada, archivos representados, diagnósticos y truncamiento; un nodo de archivo no prueba comprensión semántica.

## Comprobación del 23/10/2026

Se reutilizó la suite manual del backend y se añadieron únicamente dos casos esenciales: recuperación y cobertura de un flujo controlado; restricciones, límites y conservación parcial. Se actualizaron los fixtures anteriores para la nueva resolución de rama. Resultado: 113 ejecutadas, 112 correctas y 1 referencia visual opcional omitida, en 6,799 segundos. Sin incorporación a CI/CD.

La integración Docker utilizó Graphify real y datos ficticios de Python y Java, cada uno con controlador → servicio → repositorio. GitHub y Hermes fueron sustituidos por respuestas deterministas. Resultado: 6 archivos representados, 15 nodos, 19 relaciones, 8 acciones, 6 lecturas con posiciones verificadas, cierre por suficiencia, búsqueda literal con línea correcta y rechazo HTTP 400 de `../escape.py`. API 0.2.0, oficina y preparador saludables; HTTP 200 en oficina/proxy; sin trabajos, autenticación ni informes creados. Red del preparador comprobada como interna; proyecto temporal y sus volúmenes retirados.

No se ejecutaron análisis de repositorios reales, scanners, modelos, código objetivo ni pruebas de esos proyectos. No se repitieron las mediciones reales del Bloque 2. La comprobación de flujos valida recuperación e integración, **no la calidad de las decisiones de Hermes**, consumo real ni compatibilidad del proveedor. Tampoco cubre carga concurrente, repositorios grandes, corte abrupto del proceso o recuperación de una exploración interrumpida. Los grafos pueden ser incompletos y las reglas de adquisición pueden omitir un flujo relevante.

Los logs locales están en `artifacts/block4-tests-final.log` y `artifacts/block4-integration.log`; no se publican. La CI conserva exclusivamente su base anterior. El histórico, las versiones y los pins de Hermes no se modifican.

## Integración posterior: Bloque 5

Los límites y el perfil de preparación se centralizan ahora en el registro de [coordinación](COORDINACION.md). La exploración conserva sus límites de llamadas/tiempo/contexto y solicita por defecto hasta 1500 tokens de salida (sin techo duro OAuth). La coordinación IA opcional puede sumar otras dos llamadas, sin reabrir la preparación ni dar herramientas a especialistas.
