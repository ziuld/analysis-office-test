# Configuración y operación

Instalación inicial: [Inicio rápido](INICIO_RAPIDO.md). Todos los comandos se ejecutan desde la raíz del proyecto.

## Configuración mínima

`.env.example` contiene valores de referencia; `.env` es local y se excluye de Git y del contexto de construcción. No reemplazar un `.env` existente al actualizar.

| Variable | Uso |
|---|---|
| `AUDIT_PROVIDER` | `openai-codex` para OAuth o `openai` para API |
| `AUDIT_MODEL` | Modelo común; perfil probado: `gpt-6-luna` con OAuth |
| `AUDIT_REASONING` | `low`, `medium` o `high`; empezar por `low` |
| `GITHUB_TOKEN` | Token de lectura para los repositorios autorizados; opcional con repositorios públicos |
| `OPENAI_API_KEY` | Solo para el proveedor `openai`; la API tiene facturación independiente |
| `AUDIT_MAX_FILES` | 12 por defecto; admite 1–20 |
| `AUDIT_MAX_TOTAL_BYTES` | 48000 por defecto; admite 12000–90000 |
| `AUDIT_MAX_OUTPUT_TOKENS` | 2500 por defecto; techo solicitado en API, no aplicado por este backend Codex OAuth |

Cada archivo tiene un límite de 12000 bytes. Cada célula recibe como máximo 6 archivos/24000 bytes y devuelve hasta 2 confirmados, 1 indicio y 2 dudas. Aumentar el límite global no elimina esos límites por célula.

Para ajustar una sola célula, utilizar `AUDIT_SECURITY_MODEL` / `AUDIT_SECURITY_REASONING`, `AUDIT_ARCHITECTURE_MODEL` / `AUDIT_ARCHITECTURE_REASONING` o `AUDIT_INVENTORY_MODEL` / `AUDIT_INVENTORY_REASONING`. Vacío significa heredar el perfil común. El coordinador usa el perfil común en las consultas y no llama al modelo para consolidar.

El modo API admite `AUDIT_PROVIDER=openai`, un modelo disponible para la cuenta y `OPENAI_API_KEY`; no utiliza la sesión OAuth. La configuración predeterminada del código para este proveedor es `gpt-5.4-mini`, pero el piloto se comprobó con OAuth/Luna, no con ese modo. No hay cambio automático de proveedor si se agota una cuota.

Después de editar `.env`, recrear el servicio; un simple reinicio no actualiza sus variables:

```powershell
docker compose up -d --force-recreate --wait audit-api
```

Hacerlo sin trabajos activos. Las próximas ejecuciones por comando también leerán el `.env` actualizado.

## Inicio, parada y diagnóstico

```powershell
docker compose up -d --wait
docker compose ps
docker compose logs --tail 100 office audit-api
docker compose stop
```

Para reconstruir después de cambios en el código o el parche:

```powershell
docker compose --profile audit build auditor office
docker compose up -d --wait
```

Solo se publica [localhost:3000](http://localhost:3000/office). `audit-api` escucha en el puerto 8080 de la red interna. `auditor` es un servicio de ejecución puntual; el gateway `demo` es un perfil opcional y no participa en el flujo real ni se inicia por defecto.

| Síntoma | Qué comprobar |
|---|---|
| Docker no conecta | Docker Desktop iniciado, motor Linux y permisos de acceso al motor |
| Compose rechaza `!reset` | Utilizar Compose V2 con soporte de esa etiqueta; versión comprobada: `2.39.4-desktop.1` |
| Fallan los `COPY` de `vendor/` | Completar la recuperación de fuentes de la guía rápida |
| El parche no se aplica | Commit correcto y checkout sin el parche; no forzar ni borrar cambios locales |
| Puerto 3000 ocupado | Liberar ese puerto antes del arranque |
| Oficina sin conexión | Estado y logs de `audit-api`; esperar su healthcheck |
| GitHub deniega acceso o limita peticiones | Token de lectura, permisos sobre el repositorio y recreación del servicio tras cambiar `.env` |
| No existe `main` ni `master` | Utilizar un repositorio que tenga una de esas ramas; no se prueban otras |
| Fallo del modelo | Sesión OAuth, acceso al modelo, cuota y conectividad; no hay reintento automático |
| Revisión parcial | Leer el error de la célula y aprovechar solo sus resultados válidos; no confundirla con una revisión completa |

Para autorizar de nuevo el proveedor OAuth, completar personalmente el flujo que muestre:

```powershell
docker compose --profile audit run --rm --entrypoint python auditor -m hermes_cli.main auth add openai-codex
```

## Persistencia y cambio de ordenador

| Ubicación | Qué conserva | Al clonar |
|---|---|---|
| `reports/` en el host | Evidencias, informes, estados y consultas | Se crea vacío |
| Volumen `hermes-auth` | Sesión del modelo de Hermes | Requiere iniciar sesión otra vez |
| Volumen `studio` | Estado local de la interfaz | Se crea de nuevo |
| Sesión de la pestaña | Última pregunta/respuesta visible por agente y revisión | No se traslada |

`docker compose down` conserva los volúmenes y la carpeta `reports/`. `down -v` elimina los volúmenes del proyecto, incluida la sesión del modelo. Un reinicio del servicio interrumpe los trabajos en curso y no los reanuda.

Para conservar informes, detener los trabajos y copiar `reports/` a una ubicación autorizada para ese código. No es necesario mover sesiones OAuth: iniciar sesión personalmente en el otro ordenador. No compartir los volúmenes de autenticación ni publicar los informes como parte del repositorio.

## Ejecutar por comando

La inspección consume peticiones a GitHub pero ninguna llamada al modelo:

```powershell
docker compose --profile audit run --rm -T auditor https://github.com/propietario/repositorio --inspect-only
```

Revisar `evidencia.json` y `distribucion.json` en la nueva carpeta de `reports/`. Si faltan arranque, manifiestos o configuración de datos, ajustar primero la selección o los límites antes de subir el modelo.

Para una revisión real desde la terminal:

```powershell
docker compose --profile audit run --rm -T auditor https://github.com/propietario/repositorio
```

Comparte el bloqueo de ejecución con la oficina y las consultas. Los contadores `usage` son los reportados por Hermes; no representan una factura de la suscripción.

## Verificación del código del analizador

Estas pruebas usan datos controlados, sin GitHub ni llamadas al modelo. Prueban nuestro analizador, no la aplicación objetivo:

```powershell
docker compose --profile audit run --rm -T --entrypoint python auditor -m unittest -v test_audit test_team test_server test_questions test_brief
```

La construcción de `office` comprueba la compilación de Next.js y TypeScript. Las verificaciones del piloto están en [PLAN_MVP.md](../PLAN_MVP.md).

## Herramienta de mantenimiento del formato

Los informes antiguos conservan su formato. Para probar el formato nuevo sobre una revisión guardada, sin volver a leer GitHub:

```powershell
docker compose --profile audit run --rm -T --entrypoint python auditor /app/preview.py ID_REVISION_ORIGINAL
```

Este comando **sí consume hasta tres llamadas al modelo**, crea otra carpeta e identifica la evidencia guardada. Conserva los originales. Para actualizar solo la presentación de ese ejemplo derivado, sin modelo:

```powershell
docker compose --profile audit run --rm -T --entrypoint python auditor /app/preview.py ID_EJEMPLO_DERIVADO --render-only
```

`--render-only` solo admite ejemplos derivados de formato 2. No utilizar el ejemplo derivado como prueba de haber revisado el estado actual de GitHub.
