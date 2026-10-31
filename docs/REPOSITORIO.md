# Preparar el repositorio y reproducirlo

## Qué se publica

Publicar el paquete de `backend/src/`, sus pruebas separadas, `pyproject.toml`, los lanzadores de `auditor/`, los Dockerfiles y Compose, el parche de Hermes3D, archivos de versiones, `.env.example`, guías y avisos de terceros. El plan conserva el seguimiento del MVP; sus rutas a informes describen datos locales que no forman parte del clon.

`.gitignore` excluye `vendor/`, `.env`, informes, capturas, cachés y archivos comunes de credenciales. `vendor/` se recupera siguiendo [Inicio rápido](INICIO_RAPIDO.md). Esto evita subir copias de los proyectos originales o perder cambios dentro de un repositorio Git anidado.

No se incluye una licencia elegida para nuestro código propio. El aviso de terceros documenta las licencias de los originales; no establece una licencia para todo Arktic Office. Definir esa licencia antes de distribuirlo como proyecto abierto.

## Entregas por pull request

Repositorio: [ziuld/analysis-office-test](https://github.com/ziuld/analysis-office-test). El commit inicial del MVP ya está en `main`; las siguientes entregas se preparan en ramas `codex/` y se proponen mediante PR.

Antes del commit, revisar `git diff --cached` y ejecutar `git ls-files .env reports artifacts vendor`: no debe listar archivos. `.gitignore` no retira archivos que ya estuvieran versionados. No copiar `.env`, sesiones OAuth, capturas de código, resultados crudos, SQLite ni cachés al repositorio. Excepción autorizada por el usuario el 31/10/2026: seis informes renderizados HTML/Markdown y sus métricas comparativas, sin alterar los originales, en `docs/evidence/agent-comparison-2026-10-31/`. Revisar su contenido antes del push y conservar el manifiesto de huellas. Los directorios `reports/` y `artifacts/` siguen excluidos.

## Versiones independientes de la aplicación

| Componente | Versión propia | Imagen Docker | Identificación en ejecución |
|---|---|---|---|
| Frontend | `FRONTEND_VERSION`: 0.3.0 | `arktic-hermes3d-office:0.3.0` | Cabecera de la oficina |
| Backend | `BACKEND_VERSION`: 0.3.0 | `arktic-hermes-auditor:0.3.0` | Campo `version` de `GET /health` en la API interna |

Se usa SemVer: corrección compatible → patch, funcionalidad compatible → minor, cambio incompatible de contrato → major. En versiones 0.x, documentar explícitamente cualquier cambio de contrato. Un cambio exclusivo de frontend no obliga a subir backend, ni a la inversa.

Para una nueva entrega acordada, actualizar el archivo de versión del componente, su etiqueta de imagen y su `APP_VERSION` en `compose.yaml`, y añadir su entrada en `CHANGELOG.md`. La versión del paquete backend en `pyproject.toml` debe coincidir con `BACKEND_VERSION`; también mantener alineada la imagen manual de pruebas en `compose.backend-tests.yaml`. Construir, probar y verificar la versión visible. El argumento del frontend se incorpora durante la compilación: reiniciar sin reconstruir no cambia ese número.

Tras fusionar el PR y verificar el commit final, las etiquetas pueden distinguirse como `frontend/v0.3.0` y `backend/v0.3.0`. No se publican etiquetas de versión sobre una rama pendiente de revisión ni se crean releases automáticamente. Las imágenes se construyen localmente; este flujo no las publica en un registro.

Las versiones de los componentes son independientes de los commits de Hermes fijados a continuación. La instalación en otro equipo sigue [Inicio rápido](INICIO_RAPIDO.md) con sus propias credenciales.

## Versiones fijadas

| Fuente | Commit | Registro |
|---|---|---|
| Hermes3D | `beb76292747b816ef317aa6f9a3992e0014f81d9` | `HERMES3D_VERSION` |
| Hermes Agent | `ce28ca328d3b85ac8663e602136eb69b027cd056` | `HERMES_AGENT_VERSION` |

Los Dockerfiles fijan las imágenes base por digest y usan los lockfiles de los originales. La construcción necesita conexión y disponibilidad de GitHub, registros y paquetes; no es una distribución para uso sin Internet.

El nombre histórico `docker/hermes3d-local-demo.patch` incluye todas las adaptaciones actuales: oficina 2D, mapa compacto, integración con el analizador, lectura del informe y consultas. No corresponde solo al modo demo. Aplicarlo una vez sobre el commit limpio indicado.

Hermes Agent se utiliza sin un parche propio. Desde el Bloque 3, el analizador vive en `backend/src/arktic_office/` y se instala como wheel junto al runtime; `auditor/` conserva solo lanzadores compatibles. Los recursos van en el paquete y las pruebas en un target Docker manual separado. Detalles: [CORE.md](CORE.md).

## Mantener cambios en Hermes3D

Como `vendor/` está excluido, un cambio ahí solo se distribuye si se actualiza el parche. La siguiente comprobación verifica que el parche guardado puede retirarse del árbol actual sin modificarlo:

```powershell
git -C vendor/Hermes3D apply --reverse --check ../../docker/hermes3d-local-demo.patch
```

Para regenerarlo, incluir tanto los cambios de archivos rastreados como los archivos nuevos. `git diff` por sí solo omite los nuevos; revisar `git -C vendor/Hermes3D status --short`. Guardar el parche en UTF-8 sin BOM y con finales LF. No añadir `.env`, dependencias instaladas ni archivos de estado al parche.

Antes de sustituir el parche distribuido, aplicarlo en una copia limpia del commit fijado y construir `office`. No actualizar los commits originales ni rehacer un checkout que contenga trabajo local sin revisar sus cambios.

## Integración continua sin modelos

En un clon limpio, ejecutar `pwsh -NoProfile -File scripts/restore-sources.ps1` y después `pwsh -NoProfile -File scripts/check-startup.ps1`. Requisitos: Git, PowerShell 7, Docker con motor Linux amd64 y Compose >= 2.24.4 (etiquetas `!override` y `!reset`). El script de recuperación falla si existe cualquiera de los dos destinos; no actualiza ni borra fuentes locales. Las descargas fallidas quedan disponibles para diagnóstico; usar otro clon limpio para reintentar.

`.github/workflows/ci.yaml` ejecuta ambos comandos en Ubuntu 24.04 para push, pull request y ejecución manual, con permisos de solo lectura y sin secretos. La recuperación usa commits completos y el frontend se valida con `git apply --check` y la comprobación inversa. Las imágenes usan los Dockerfiles y lockfiles actuales, con descarga e instalación de dependencias durante el build. Esto incluye instalar los binarios de scanners, sin ejecutarlos.

El arranque combina `compose.yaml` con `compose.ci.yaml`: proyecto de nombre único, volúmenes nuevos sin sesiones, ningún `.env`, ningún puerto del host y red `internal` sin salida a Internet. Solo levanta `audit-api` y `office`. Espera sus healthchecks, comprueba `GET /health`, `GET /runs` vacío y sin consulta activa, oficina HTTP 200 y proxy `/api/audit/runs`, además de `/health` desde la red de la oficina. Verifica también `/reports` y `/auth` vacíos. No llama a rutas POST, análisis, scanners ni modelos. Un `finally` retira únicamente los recursos del proyecto temporal; una interrupción forzada del proceso puede requerir retirarlos manualmente por su nombre `arktic-ci-*`.

El build puede reutilizar caché Docker y actualiza las etiquetas locales actuales; no publica imágenes ni cambia versiones. Tener HTTP saludable no valida la interfaz visual, resultados de análisis, proveedores, autenticación ni calidad de informes. GitHub Actions debe comprobarse también en el runner remoto: una ejecución local no acredita que el workflow haya pasado allí. Los fallos muestran logs limitados al proyecto aislado.

**CD pendiente:** no hay despliegue automático, publicación de imágenes, etiquetas ni releases. El cierre de entrega y el siguiente número de versión requieren acuerdo posterior.

## Comprobación antes de compartir una versión

1. Las rutas privadas siguen fuera de Git y los avisos de terceros se conservan.
2. El parche se aplica sobre la versión fijada y contiene los archivos nuevos de la interfaz.
3. La construcción y las pruebas del analizador pasan según [Operación](OPERACION.md).
4. La guía de instalación coincide con los archivos versionados. En otro ordenador, verificar también sesión del modelo, acceso a GitHub y una revisión desde la oficina.

La validación en otro ordenador es distinta de las pruebas locales; no darla por comprobada solo por reconstruir fuentes o tener contenedores activos.
