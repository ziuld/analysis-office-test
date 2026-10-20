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
$officeCommit = (Get-Content HERMES3D_VERSION -Raw).Trim()
git clone --config core.longpaths=true --no-checkout --depth 1 https://github.com/iamlukethedev/Hermes3D.git vendor/Hermes3D
git -C vendor/Hermes3D fetch --depth 1 origin $officeCommit
git -C vendor/Hermes3D checkout --detach $officeCommit
git -C vendor/Hermes3D apply ../../docker/hermes3d-local-demo.patch

$agentCommit = (Get-Content HERMES_AGENT_VERSION -Raw).Trim()
git clone --config core.longpaths=true --no-checkout --depth 1 https://github.com/NousResearch/hermes-agent.git vendor/hermes-runtime
git -C vendor/hermes-runtime fetch --depth 1 origin $agentCommit
git -C vendor/hermes-runtime checkout --detach $agentCommit
```

La opción `core.longpaths=true` se guarda solo en esas copias y permite las rutas largas del runtime en Windows. Ejecutar este bloque una sola vez por clon nuevo; si un comando falla, detenerse y revisar el error. No aplicar el parche otra vez sobre una oficina ya adaptada. No se instalan dependencias ni se ejecutan scripts de los repositorios en el host.

## 3. Crear la configuración local

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
New-Item -ItemType Directory -Force reports | Out-Null
```

Editar `.env` con el editor habitual. Mantener inicialmente `AUDIT_PROVIDER=openai-codex`, `AUDIT_MODEL=gpt-6-luna` y `AUDIT_REASONING=low`, el perfil comprobado en el piloto. Su disponibilidad depende de la cuenta.

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

Abrir [http://localhost:3000/office](http://localhost:3000/office). Debe aparecer **CONECTADO**. Introducir una URL de GitHub sin rama ni parámetros y pulsar **Iniciar revisión**. Se usa `main` o, si no existe, `master`.

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
