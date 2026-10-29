# Analizar un repositorio local

## Flujo completo desde la oficina

Desde PowerShell, en la carpeta de Arktic Office, preparar la captura sin iniciar modelos:

```powershell
.\scripts\analyze-local.ps1 -Repository 'C:\ruta\a\mi-repositorio' -PrepareOnly
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --wait
```

Abrir [la oficina](http://localhost:3000/office), seleccionar **Origen del repositorio → Repositorio local**, elegir la captura y pulsar **Iniciar revisión**. El selector muestra nombre, rama y commit; debajo aparece la ruta original. El frontend envía el identificador de la captura a `POST /runs`, a través de su proxy, y la API crea el trabajo, lanza el equipo y conserva progreso e informe. Al terminar, utilizar **Leer informe** o **Descargar informe** en la misma oficina.

La API solo admite IDs de capturas preparadas bajo el directorio montado en modo lectura. No acepta rutas arbitrarias del disco a través de HTTP. `GET /local-sources` expone únicamente los metadatos necesarios para elegir una captura, sin contenido de archivos. El directorio de capturas debe existir antes de levantar los servicios (el paso de preparación lo crea).

Tras actualizar el código de esta integración, construir las imágenes una vez:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit build auditor office
```

## Modalidad por comando

También se puede ejecutar el equipo directamente, sin pasar por frontend/API:

```powershell
.\scripts\analyze-local.ps1 -Repository 'C:\ruta\a\mi-repositorio'
```

Se utiliza **HEAD de la rama que ya esté activa**, sea `develop`, `main`, `master` u otra. No se hace checkout, fetch, pull ni cambio de rama, ni se necesita acceso al remoto. El informe, la evidencia y el manifiesto registran rama, commit y origen local. Un checkout sin rama se registra como `HEAD` con `detached_head=true`.

Esta modalidad analiza los archivos versionados del commit, incluidos los ocultos. Requiere un repositorio limpio: ante cambios locales o archivos sin seguimiento se detiene y pide confirmarlos para no omitirlos silenciosamente. No incluye archivos ignorados no versionados ni historial Git. Submódulos, punteros LFS no resueltos y filtros Git personalizados detienen la captura. Una carpeta sin Git todavía no está soportada.

El script consulta las opciones `core.autocrlf` y `core.filemode` del Git del host y las aplica solo a la lectura dentro de Docker. No cambia la configuración del repositorio. Exporta los objetos Git canónicos, sin filtros de checkout ni exclusiones `export-ignore`; cada archivo se verifica mediante hash antes de analizarlo.

Para comprobar adquisición, mapa y reparto sin scanners ni llamadas a modelos:

```powershell
.\scripts\analyze-local.ps1 -Repository 'C:\ruta\a\mi-repositorio' -InspectOnly
```

Requiere Git, Docker, las imágenes construidas y `.env` configurado. La revisión completa necesita la sesión/proveedor de modelos habitual. Después de actualizar el código, reconstruir una vez:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit build auditor
```

La ruta debe existir en **el ordenador que ejecuta el script y Docker**. Una ruta de otro PC no permite acceder automáticamente a ese equipo. El campo GitHub de la oficina conserva su funcionamiento; el selector local utiliza capturas preparadas, para no conceder al servidor acceso general al disco de Windows.

## Resultados y cobertura

Se monta únicamente el repositorio indicado en modo lectura y sin red para capturar sus objetos. El bundle verificado queda en `artifacts/local-inputs/<id>/`. Después se utilizan el preparador, scanners, coordinador y tres especialistas habituales. OSV puede consultar metadatos de dependencias en red y los especialistas usan el proveedor configurado. No se ejecutan los scripts ni builds de la aplicación analizada.

Los resultados se guardan en `reports/`, con la ruta anunciada al terminar. En `herramientas/` se conservan los JSON nativos y logs de scanners y la respuesta del adaptador de Graphify (no es el JSON nativo del motor). `evidencia.json` contiene inventario y cobertura; `informe.html` e `informe.md` contienen el resultado del equipo. Las referencias locales muestran archivo y línea, sin fabricar enlaces de GitHub.

`artifacts/` y `reports/` están ignorados por Git. El bundle original puede contener `.env` versionados y no está saneado. La preparación mantiene la ocultación existente antes de enviar evidencia a modelos; no compartir el bundle original como si fuera el informe.

La entrada local no amplía reglas ni lenguajes: el adaptador Semgrep excluye actualmente `.vue` y `.cjs`. El grafo tiene otra compatibilidad y el recuperador permite a los especialistas leer archivos fuera de la selección inicial. Que el equipo termine no demuestra cobertura exhaustiva; sus errores y respuestas rechazadas se conservan sin reintentos automáticos.

## Prueba dirigida del exportador

La integración Git se prueba por separado porque la suite offline general prohíbe subprocesos. Desde la imagen indexer con el workspace montado en `/workspace`:

```text
PYTHONPATH=/workspace/backend/src:/workspace/backend/tests python -m unittest local_source_integration -v
```
