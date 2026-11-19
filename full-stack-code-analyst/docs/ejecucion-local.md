# Herramientas, caché y revisión

Se necesita Python 3.11 o posterior para los scripts locales. Git permite inventariar archivos versionados y nuevos respetando los ignorados; sin Git se recorre la carpeta con exclusiones documentadas. Los scripts solo usan la biblioteca estándar de Python. Los ejecutables de análisis se instalan aparte o se aprovechan desde el entorno si ya están disponibles.

Los comandos siguientes se ejecutan desde la carpeta de Iris. Desde otra carpeta usa la ruta completa a `scripts/iris.py`. Las respuestas del script son JSON acotado, apto para leer desde el chat.

La copia de Iris debe estar instalada dentro del proyecto pasado a `--project`. El script lo comprueba antes de crear almacenamiento. `.local/` se crea automáticamente dentro de esa copia. Si falta permiso, devuelve `permission_required`, `required_path` y `fallback_allowed: false`: solicita acceso de escritura para esa ruta y reintenta allí. Si se deniega o falla de nuevo, detén la revisión; no copies el agente a otro workspace, outputs o un temporal. No es un problema del nombre `.local` ni se resuelve renombrándola para eludir permisos.

## Comprobar y preparar

~~~text
python scripts/iris.py status --project "<raíz del proyecto>"
python scripts/iris.py prepare --project "<raíz del proyecto>" --tools graphify,gitleaks,semgrep,osv --online
~~~

`status` calcula la huella real del código y devuelve informes reutilizables y herramientas disponibles. `prepare` genera una revisión dentro de `.local/revisiones/` y devuelve su ruta. `--online` expresa la autorización ya recibida para consultar OSV con metadatos de dependencias. Omítelo si esa consulta no se ha autorizado. Las herramientas ausentes, fallidas o sin entradas compatibles se registran en el estado.

Para solo revisión directa, usa `--tools ""`. Para herramientas concretas, usa una lista separada por comas. `--interpretation standard` usa el mapa como apoyo, y `--interpretation deep` indica profundizar sobre sus relaciones con la IA del chat (predeterminado). La interpretación la realiza el asistente después de la preparación local.

Las huellas incluyen cambios sin commit y archivos nuevos no ignorados por Git. Los archivos privados por extensión, enlaces, binarios y textos de más de 2 MB se registran como excluidos. La copia de Gitleaks puede incluir un .env versionado. Sus originales quedan en el almacenamiento local privado y sus resultados se redactan. Los otros analizadores reciben textos con ocultación de credenciales comunes. Esa ocultación puede afectar el parseo, lo que debe reflejarse en cobertura.

La rama y commit se registran como contexto. El contenido decide si hace falta recalcular. Los cambios ajenos a la entrada de una herramienta no invalidan su caché; OSV usa los manifiestos y lockfiles compatibles, Semgrep sus lenguajes y reglas, y Graphify su corpus de texto. Un cambio de versión o adaptador invalida el análisis correspondiente. Las reglas o guías de Iris invalidan la interpretación guardada, conservando resultados de herramientas compatibles.

## Instalar herramientas

~~~text
python scripts/iris.py install graphify
python scripts/iris.py install gitleaks
python scripts/iris.py install semgrep
python scripts/iris.py install osv
~~~

La instalación requiere aceptación del usuario y conexión para descargar las distribuciones. Graphify y Semgrep usan `uv` y un Python 3.12 aislado; si falta `uv`, el script lo indica. Los entornos, runtimes y cachés se guardan dentro de `.local/`. Gitleaks y OSV descargan binarios oficiales para la plataforma y verifican su checksum. Las versiones están en [versions.json](../tools/versions.json).

La instalación local incluida de Semgrep está habilitada para Linux y macOS. En Windows puedes aprovechar un ejecutable compatible ya preparado o elegir Docker. Se usan las reglas locales de [semgrep-rules.json](../tools/semgrep-rules.json).

## Semgrep local, Docker o pendiente

Docker es opcional, recomendable para facilitar Semgrep aislado en Windows. Instálalo y deja listo su motor Linux antes de invocar Iris si quieres esa vía. Iris no instala Docker/WSL ni arranca servicios del sistema. `status` devuelve `semgrep_options.local` y `semgrep_options.docker`, incluyendo si la imagen está descargada. Solo admite un motor local accesible por socket Unix o named pipe; no envía código a motores remotos.

Si ambos funcionan, el chat ofrece contenedor temporal (recomendado), local o continuar sin Semgrep. Si solo uno funciona, ofrece esa vía o continuar. Si ninguno funciona, avisa, continúa y deja la cobertura pendiente. Una imagen ausente no obliga a instalar Docker: pide aceptación de la descarga inicial. Una vez elegido, no repite la pregunta durante los bloques.

~~~text
python scripts/iris.py prepare --project "<raíz>" --semgrep-engine docker --allow-image-download --online
python scripts/iris.py prepare --project "<raíz>" --semgrep-engine local --online
python scripts/iris.py prepare --project "<raíz>" --semgrep-engine skip --online
~~~

Usa `--online` solo con autorización OSV previa. `--allow-image-download` autoriza únicamente descargar la imagen versionada si falta; sin él se registra `needs_image_download`. No se cambia de motor automáticamente. Si Docker no está listo o falla el análisis, la revisión continúa con cobertura parcial. `skip` conserva Semgrep como omitido y la decisión aparece en el estado.

La imagen declarada en versions.json se resuelve a su ID inmutable para ejecutar y cachear. El contenedor temporal monta solo la copia seleccionada y las reglas en lectura, y un directorio de salida de `.local/` en escritura; no monta el proyecto original ni el socket Docker. Usa red deshabilitada, filesystem raíz de solo lectura, usuario sin privilegios adicionales, capacidades eliminadas y límites de CPU, memoria, procesos y temporales. En Unix usa el UID/GID del usuario (si ejecutas Iris como root seguirá siendo root, aunque sin capacidades adicionales); en Windows usa UID 65532. No es una garantía absoluta de seguridad. El contenedor se elimina al finalizar o tras timeout; un fallo de limpieza queda registrado con su nombre para revisión. La imagen se conserva para futuras ejecuciones. Las cachés local y Docker son distintas e incluyen imagen, reglas y entrada.

## Actualizar o repetir

~~~text
python scripts/iris.py prepare --project "<raíz>" --tools graphify,gitleaks,semgrep,osv --refresh osv --online
python scripts/iris.py prepare --project "<raíz>" --force-review
python scripts/iris.py prepare --project "<raíz>" --refresh graphify,gitleaks,semgrep,osv --online
~~~

El primer comando actualiza OSV y reutiliza las otras herramientas. Si los avisos cambian, el informe anterior deja de representar los resultados actuales. El segundo prepara una nueva interpretación con resultados vigentes. El tercero recalcula todos los análisis. Cada revisión conserva sus fichas y su estado. Un error o una interrupción nunca se publica como resultado completo ni se reutiliza como análisis correcto.

Recalcular herramientas no convierte el chat en independiente. Usa `--mode extend --base-review "<revisión anterior>"` cuando aproveches conclusiones conocidas. Para una prueba independiente, el usuario abre un chat nuevo sin antecedentes y prepara con `--mode independent --fresh-context`. `--mode new` es el predeterminado y puede reutilizar un informe vigente; no acredita independencia. Conserva `--semgrep-engine` al actualizar o repetir. Consulta [evidencia y comparación](evidencia-revisiones.md) y [el protocolo independiente](prueba-independiente.md).

## Consultar resultados y cerrar

~~~text
python scripts/iris.py results --review "<ruta de revisión>" --tool graphify --search authenticate --limit 10
python scripts/iris.py results --review "<ruta de revisión>" --tool gitleaks
python scripts/iris.py results --review "<ruta de revisión>" --tool semgrep
python scripts/iris.py results --review "<ruta de revisión>" --tool osv --limit 10
python scripts/iris.py render --review "<ruta de revisión>"
python scripts/iris.py finish --review "<ruta de revisión>" --author "<asistente y modelo conocidos>" --coverage partial
~~~

`results` pagina y filtra por texto. Consulta cada alerta pertinente, sigue su consumidor y registra si queda confirmada, descartada o pendiente. Para Graphify, usa las rutas y ubicaciones devueltas para leer las líneas originales.

La IA completa `informe.json`, `cobertura.json`, `dependencias.json` y `hallazgos.json` durante los siete bloques. Al cerrar cada bloque ejecuta `render`: genera fichas, HTML y anexos con estructura fija. No edites la plantilla ni el HTML a mano. `finish` comprueba vigencia, siete bloques, 40 IDs únicos, recursos embebidos, enlaces, rangos y correspondencia exacta de HTML/fichas con el generador y los JSON. Conserva sus hashes. Su verificación complementa el contraste semántico del chat. Los avisos sin validar conservan pending; no se borran para cerrar la revisión.

Para una copia adicional dentro del almacenamiento de Iris, solicitada expresamente:

~~~text
python scripts/iris.py export --review "<ruta de revisión>" --output "<carpeta del agente>/.local/exports/informe-iris.html"
~~~

La exportación rechaza destinos fuera de `.local/` y conserva un archivo existente. El usuario puede copiar manualmente un informe terminado. Al compartir el agente, copia sus archivos mantenidos y una `.local/` vacía, conservando los datos de pruebas en privado.
