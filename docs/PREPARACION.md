# Preparación completa — Bloque 8

El recorrido actual usa `compose.yaml` junto con `compose.hybrid.yaml`. `hybrid` adquiere el snapshot íntegro del commit de la rama predeterminada, verifica cada blob contra el árbol GitHub y conserva todos los archivos versionados: ocultos, pruebas, recursos y lockfiles. No descarga todo el historial. El antiguo recorrido `legacy` permanece disponible expresamente para compatibilidad; su adquisición parcial no cumple la condición de este bloque.

El Core mantiene el snapshot en un directorio temporal privado dentro del contenedor, sin ejecutar enlaces ni archivos. Los symlinks se materializan como metadatos. Un puntero LFS o un gitlink de submódulo **detiene la preparación**: esta versión no hidrata su contenido y no afirma haberlo adquirido. Árbol truncado, integridad incorrecta, exceso de capacidad, scanner fallido o extracción compatible pendiente también detienen el análisis antes del modelo; no hay continuación automática con una muestra.

Gitleaks recibe el snapshot entero con configuración confiable; OSV recibe todos los lockfiles y `requirements.txt` compatibles encontrados, sin instalar, resolver ni ejecutar dependencias. Sin input resuelto, OSV queda `no_evaluado`. Cada archivo conserva los estados de entrada de herramientas en `evidencia.json/inventory`; «offered» registra el envío, no que una herramienta haya evaluado semánticamente todo su contenido. Se conservan las limitaciones nativas de binarios, reglas y formatos.

Graphify 0.9.95 se invoca mediante su API fijada de extracción, sobre una lista explícita de todos los textos con parser compatible. Así evita los filtros automáticos de `tests`, ocultos y `.gitignore` de la detección del CLI. No utiliza modelos ni clustering. La lista de parsers y la API privada `_DISPATCH` quedan vinculadas al pin existente; revisar esta integración antes de actualizarlo. Cada archivo tiene estado `processed`, `unsupported` o `error`; los binarios y enlaces siguen en el inventario. Relaciones no resueltas se conservan y se cuentan; no son evidencia suficiente por sí solas. Un archivo procesado no acredita un grafo semánticamente exhaustivo: siguen vigentes los límites semánticos nativos del extractor (por ejemplo, YAML estructura hasta 500 claves y profundidad 6). Las variantes YAML con etiquetas que SafeLoader no admite, como Compose `!reset`/`!override`, y esquemas de datos que Graphify excluye se registran `unsupported_yaml_dialect_or_data_schema`, con texto consultable e inventario; no se presentan como AST procesado. No se habilitan constructores inseguros ni se ejecuta Compose.

Límites operativos: `AUDIT_SNAPSHOT_MAX_BYTES=32000000`, `AUDIT_SNAPSHOT_MAX_FILES=20000`, `AUDIT_SNAPSHOT_SECONDS=300`. Son independientes del contexto enviado al modelo. El preparador acepta hasta 64 MB de petición/respuesta y 32 MB de texto, 20000 archivos, 100000 nodos, 200000 relaciones y 300 s. Subir solo el límite de adquisición no sube las capacidades del preparador ni del tmpfs. Al excederlos se informa y se detiene; no se recorta silenciosamente. Los contenedores conservan memoria, CPU, red, noexec y demás restricciones.

El inventario completo y los mapas permanecen locales y consultables durante los especialistas. Solo los paquetes y fragmentos recuperados se envían a modelos, con ocultación de credenciales y posiciones originales. El Core conserva en los resultados manifiesto, inventario, cobertura, decisiones, consultas y fragmentos; el grafo y snapshot temporales se liberan al terminar o ante errores gestionados. Bajo el bloqueo de auditoría, la siguiente ejecución limpia los directorios propios `job-*` abandonados por una interrupción; recrear el contenedor elimina su tmpfs. No hay consultas posteriores al grafo completo eliminado.

Configuración de recuperación, llamadas y evidencia real: [COORDINACION.md](COORDINACION.md) y [PLAN_FASE_1.md](PLAN_FASE_1.md). No se modificaron CI/CD, pins ni versiones.

## Registro anterior (Bloque 4, sustituido por el flujo anterior para nuevas revisiones híbridas)

# Preparación híbrida — Bloque 4

El modo híbrido prepara contexto para las tres células existentes. Se activa expresamente durante la transición; el modo habitual sigue siendo `legacy`. Cada revisión utiliza **un solo recorrido**, sin ejecutar ambos ni repetir scanners o especialistas. Las versiones permanecen en 0.2.0.

## Uso

Desde la raíz, con las fuentes y la sesión habituales ya preparadas:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml build audit-api preparator
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --wait
```

La oficina mantiene su entrada habitual. Una revisión normal en este modo puede añadir **hasta dos llamadas de preparación por defecto**, además de las tres células; utiliza el modelo y razonamiento comunes. No inicia ninguna revisión por arrancar los servicios. Para inspeccionar sin scanners ni modelos:

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

El explorador dispone por defecto de **2 llamadas, 180 segundos, 60000 bytes acumulados de prompts**, 8000 bytes por respuesta y hasta 60 segundos por llamada. No hay reintentos. Los límites globales existentes de contexto final siguen vigentes: por defecto 24 archivos, 12000 bytes por archivo y 120000 bytes totales; las lecturas nuevas se rechazan si no caben. Los especialistas conservan sus límites y su única pasada. Las líneas omitidas se dejan vacías para mantener citas al commit original.

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

Los límites y el perfil de preparación se centralizan ahora en el registro de [coordinación](COORDINACION.md). La exploración conserva sus límites de tiempo/contexto; las llamadas son configurables y solicita por defecto hasta 1500 tokens de salida (sin techo duro OAuth). La coordinación IA opcional puede sumar otras dos llamadas, sin reabrir la preparación ni dar herramientas a especialistas.

## Pasadas de preparación para pruebas — 24/10/2026

Para ejecutar el recorrido completo con modelos y sin scanners, usar `AUDIT_SCANNERS_ENABLED=0`. El valor `1` conserva el comportamiento anterior; cualquier otro valor se rechaza antes de adquirir código o consumir modelo. La cobertura registra que los scanners no se ejecutaron. Esto es independiente de `--inspect-only`, que además omite las llamadas de modelo. La coordinación completa requiere `AUDIT_COORDINATION_MODE=ai` y el override híbrido indicado arriba.

En `.env`, `AUDIT_PREPARATION_MAX_LOOPS=1` limita las pasadas adicionales del coordinador explorador. `0` permite solo la llamada inicial; `1`, hasta dos; `2`, hasta tres; `3`, hasta cuatro. Se admiten enteros entre 0 y 20, validados antes de adquirir el repositorio o consumir modelo. Predeterminado: 1. Tiempo y contexto pueden cortar antes; incrementar loops no los amplía.

Cada pasada solicita una acción de lectura/búsqueda/mapa o `finish`. Es el loop de preparación híbrida, no una repetición del equipo completo. El modelo debe terminar cuando tenga suficiente evidencia; puede necesitar una pasada para comunicar `finish`. Si agota llamadas tras una lectura, se conserva lo recuperado y se declara el límite. Reparto y síntesis opcionales siguen siendo una llamada cada uno; cada especialista mantiene una pasada. En modo `legacy` este parámetro no añade llamadas.

La traza registra `limits.max_loops`, `limits.iterations` (inicial + adicionales) e `iterations` usadas. Cambiar `.env` requiere recrear la API con el override híbrido para probar esta preparación. Los perfiles de prueba heredan el modelo común y razonamiento `low`; `.env.example` usa `gpt-6-luna` sin elevar Seguridad. La calibración de modelos y calidad se pospone al Bloque 9.

Las lecturas se recortan al máximo de 100 líneas y al final del archivo; la respuesta indica `limited` y `requested_end` cuando se recorta, conservando las posiciones reales. Rutas no adquiridas, tipos inválidos e inicios fuera del archivo se rechazan. No se amplían los límites de bytes o archivos. Una respuesta de especialista rechazada se conserva, ocultada y acotada a 120000 caracteres, en `celulas/<rol>.respuesta-rechazada.txt`: es diagnóstico sin validar, no se publica ni se reutiliza como una aportación válida.
