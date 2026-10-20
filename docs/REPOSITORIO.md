# Preparar el repositorio y reproducirlo

## Qué se publica

Publicar nuestro código de `auditor/`, los Dockerfiles, `compose.yaml`, el parche de Hermes3D, los archivos de versiones, `.env.example`, las guías y avisos de terceros. El plan conserva el seguimiento del MVP; sus rutas a informes describen datos locales que no forman parte del clon.

`.gitignore` excluye `vendor/`, `.env`, informes, capturas, cachés y archivos comunes de credenciales. `vendor/` se recupera siguiendo [Inicio rápido](INICIO_RAPIDO.md). Esto evita subir copias de los proyectos originales o perder cambios dentro de un repositorio Git anidado.

No se incluye una licencia elegida para nuestro código propio. El aviso de terceros documenta las licencias de los originales; no establece una licencia para todo Arktic Office. Definir esa licencia antes de distribuirlo como proyecto abierto.

## Primera subida

Crear un repositorio vacío en el alojamiento elegido y, desde esta carpeta, ejecutar los siguientes comandos cuando se vaya a publicar. No se ha creado ni subido un repositorio remoto durante el cierre documental.

```powershell
git init -b main
git check-ignore .env reports/ artifacts/ vendor/
git add .
git status --short
git diff --cached --stat
git ls-files .env reports artifacts vendor
```

La comprobación de exclusiones debe mostrar las cuatro rutas. El último comando no debe listar archivos. Revisar el contenido preparado, además del resumen, antes del primer commit. `.gitignore` no retira archivos que ya estuvieran versionados; si aparecen credenciales o informes, corregirlo antes de continuar.

```powershell
git commit -m "Initial Arktic Office MVP"
git remote add origin URL_DEL_REPOSITORIO_ARKTIC_OFFICE
git push -u origin main
```

Sustituir la URL del ejemplo por la real. Una vez publicado, probar el clon y seguir la guía rápida con credenciales propias de esa instalación. No copiar `.env` ni sesiones OAuth al repositorio.

## Versiones fijadas

| Fuente | Commit | Registro |
|---|---|---|
| Hermes3D | `beb76292747b816ef317aa6f9a3992e0014f81d9` | `HERMES3D_VERSION` |
| Hermes Agent | `ce28ca328d3b85ac8663e602136eb69b027cd056` | `HERMES_AGENT_VERSION` |

Los Dockerfiles fijan las imágenes base por digest y usan los lockfiles de los originales. La construcción necesita conexión y disponibilidad de GitHub, registros y paquetes; no es una distribución para uso sin Internet.

El nombre histórico `docker/hermes3d-local-demo.patch` incluye todas las adaptaciones actuales: oficina 2D, mapa compacto, integración con el analizador, lectura del informe y consultas. No corresponde solo al modo demo. Aplicarlo una vez sobre el commit limpio indicado.

En el MVP actual, Hermes Agent se utiliza sin un parche propio. Las modificaciones del analizador están en `auditor/` y se copian a la imagen junto al runtime.

## Mantener cambios en Hermes3D

Como `vendor/` está excluido, un cambio ahí solo se distribuye si se actualiza el parche. La siguiente comprobación verifica que el parche guardado puede retirarse del árbol actual sin modificarlo:

```powershell
git -C vendor/Hermes3D apply --reverse --check ../../docker/hermes3d-local-demo.patch
```

Para regenerarlo, incluir tanto los cambios de archivos rastreados como los archivos nuevos. `git diff` por sí solo omite los nuevos; revisar `git -C vendor/Hermes3D status --short`. Guardar el parche en UTF-8 sin BOM y con finales LF. No añadir `.env`, dependencias instaladas ni archivos de estado al parche.

Antes de sustituir el parche distribuido, aplicarlo en una copia limpia del commit fijado y construir `office`. No actualizar los commits originales ni rehacer un checkout que contenga trabajo local sin revisar sus cambios.

## Comprobación antes de compartir una versión

1. Las rutas privadas siguen fuera de Git y los avisos de terceros se conservan.
2. El parche se aplica sobre la versión fijada y contiene los archivos nuevos de la interfaz.
3. La construcción y las pruebas del analizador pasan según [Operación](OPERACION.md).
4. La guía de instalación coincide con los archivos versionados. En otro ordenador, verificar también sesión del modelo, acceso a GitHub y una revisión desde la oficina.

La validación en otro ordenador es distinta de las pruebas locales; no darla por comprobada solo por reconstruir fuentes o tener contenedores activos.
