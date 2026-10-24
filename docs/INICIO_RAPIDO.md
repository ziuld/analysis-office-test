# Inicio rápido en otro ordenador

Guía para **Windows con PowerShell**. Ejecutar los comandos desde la carpeta del proyecto. La instalación comprobada utiliza Docker Desktop con motor Linux `amd64` y Docker Compose `2.39.4-desktop.1`. Otras plataformas no se han verificado en este MVP.

## 1. Tener instalado

- **Git**, disponible en la terminal.
- **Docker Desktop**, iniciado y configurado para contenedores Linux. En Windows, habilitar el entorno de virtualización/WSL que requiera la instalación de Docker Desktop.
- **Docker Compose V2** (`docker compose`, incluido en Docker Desktop), con soporte de `!reset`, utilizado por `compose.yaml`.
- Un navegador, conexión a Internet y acceso al proveedor del modelo. Para el perfil probado se autoriza una cuenta compatible con Codex OAuth en Hermes.

No hace falta instalar Node.js, Python, Java ni Hermes en el ordenador: se preparan dentro de Docker. La primera construcción descarga imágenes y dependencias; requiere espacio libre y puede tardar varios minutos.

Comprobar antes de continuar:

```powershell
git --version
docker version
docker compose version
```

`docker version` debe mostrar también el servidor. Si falla algún comando, resolverlo antes de seguir.

## 2. Clonar y recuperar las fuentes fijadas

Clonar **Arktic Office** desde su repositorio. La URL del proyecto que se analizará se introduce después en la oficina.

```powershell
git clone https://github.com/ziuld/analysis-office-test.git arktic_office
cd arktic_office
```

`vendor/` no se publica. En este clon nuevo, recuperar los originales y aplicar nuestra adaptación:

```powershell
pwsh -NoProfile -File scripts/restore-sources.ps1
```

Requiere PowerShell 7 (`pwsh`). Recupera exclusivamente los commits fijados, verifica HEAD y comprueba/aplica el parche de frontend. No instala ni ejecuta dependencias en el host. Se detiene si cualquiera de los destinos ya existe para conservar cambios locales. Si una descarga falla, conserva el árbol parcial para diagnóstico; reintentar en otro clon limpio.

Para comprobar construcción y arranque **sin configurar modelos**, ejecutar después:

```powershell
pwsh -NoProfile -File scripts/check-startup.ps1
```

Construye API y oficina; usa volúmenes nuevos, sin `.env` ni sesiones previas, red interna sin salida y ningún puerto publicado. Comprueba `/health`, `/office` y el proxy de listado vacío. Retira sus contenedores y volúmenes temporales al terminar. No inicia revisiones ni ejecuta scanners o modelos. La construcción instala los binarios de scanners incluidos en la imagen, pero no los ejecuta. Requiere Compose 2.24.4 o posterior por `!override`, además de soporte de `!reset`. Las imágenes conservan sus etiquetas actuales. Más detalles y límites: [Reproducción y CI](REPOSITORIO.md#integración-continua-sin-modelos).

## 3. Crear la configuración local

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
New-Item -ItemType Directory -Force reports | Out-Null
```

Editar `.env` con el editor habitual. Mantener inicialmente `AUDIT_PROVIDER=openai-codex`, `AUDIT_MODEL=gpt-6-luna` y `AUDIT_REASONING=low`, el perfil económico para Arquitectura e Inventario. Para Seguridad, el ejemplo configura `AUDIT_SECURITY_MODEL=gpt-6.1-sol` y `AUDIT_SECURITY_REASONING=medium`. Su disponibilidad depende de la cuenta.

Añadir `GITHUB_TOKEN` si se necesita acceso a repositorios privados o evitar el límite anónimo de GitHub. Usar un token con acceso de lectura al contenido y metadatos de los repositorios necesarios. Dejar `OPENAI_API_KEY` vacío en modo OAuth. No compartir ni subir `.env`.

## 4. Construir y autorizar Hermes

```powershell
docker compose config --quiet
docker compose --profile audit build auditor office
docker compose --profile audit run --rm --entrypoint python auditor -m hermes_cli.main auth add openai-codex
```

Completar personalmente la URL y el código que muestre Hermes. Esperar la confirmación del inicio de sesión. No usar códigos de ejemplos ni copiar credenciales de otro ordenador. La sesión se guarda en el volumen Docker `hermes-auth`.

## 5. Levantar y utilizar

```powershell
docker compose up -d --wait
docker compose ps
```

Abrir [http://localhost:3000/office](http://localhost:3000/office). Debe aparecer **CONECTADO**. Introducir una URL de GitHub sin rama ni parámetros y pulsar **Iniciar revisión**. Se resuelve la rama predeterminada real del repositorio y se fija su commit.

Esperar los resultados de Seguridad, Arquitectura e Inventario. Abrir o descargar el informe y pulsar un personaje para hacerle una pregunta. Esto sí consume modelo; que los contenedores estén activos solo comprueba el arranque, no una revisión real. En un clon nuevo no aparecen los informes de nuestro piloto porque son datos locales excluidos de Git.

Para comprobar primero el acceso y los archivos seleccionados sin llamar al modelo:

```powershell
docker compose --profile audit run --rm -T auditor https://github.com/ziuld/bookingApi --inspect-only
```

## Uso diario

| Acción | Comando |
|---|---|
| Iniciar otra vez | `docker compose up -d --wait` |
| Detener sin eliminar contenedores | `docker compose stop` |
| Reiniciar | `docker compose restart` |
| Detener y retirar contenedores, conservando datos | `docker compose down` |
| Ver errores | `docker compose logs --tail 100 office audit-api` |

Evitar reiniciar durante una revisión o consulta: se marcará como interrumpida, sin reintentarse. No utilizar `docker compose down -v` si se quiere conservar la sesión del modelo y el estado de la oficina.

Problemas de acceso, configuración o recuperación: [Operación](OPERACION.md).
