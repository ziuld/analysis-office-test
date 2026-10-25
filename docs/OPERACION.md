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
| `AUDIT_MAX_FILES` | 24 por defecto; admite 1–40 |
| `AUDIT_MAX_TOTAL_BYTES` | 120000 por defecto; admite 12000–200000 |
| `AUDIT_MAX_OUTPUT_TOKENS` | 4500 por defecto; techo solicitado en API, no aplicado por este backend Codex OAuth |

Cada archivo aporta hasta 12000 bytes de texto o extractos con numeración original. Seguridad recibe hasta 12 archivos/64000 bytes; las demás células, 6/24000. Descarga y validación de resultados tienen límites independientes: ver [Seguridad](SEGURIDAD.md).

Para ajustar una sola célula, utilizar `AUDIT_SECURITY_MODEL` / `AUDIT_SECURITY_REASONING`, `AUDIT_ARCHITECTURE_MODEL` / `AUDIT_ARCHITECTURE_REASONING` o `AUDIT_INVENTORY_MODEL` / `AUDIT_INVENTORY_REASONING`. Vacío significa heredar el perfil común. La coordinación determinista no llama al modelo; el modo IA opcional añade hasta dos llamadas y las consultas mantienen su llamada independiente. Perfiles y encargo: [COORDINACION.md](COORDINACION.md).

El modo API admite `AUDIT_PROVIDER=openai`, un modelo disponible para la cuenta y `OPENAI_API_KEY`; no utiliza la sesión OAuth. La configuración predeterminada del código para este proveedor es `gpt-5.4-mini`, pero el piloto se comprobó con OAuth/Luna, no con ese modo. No hay cambio automático de proveedor si se agota una cuota.

Después de editar `.env`, recrear el servicio; un simple reinicio no actualiza sus variables:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --force-recreate --wait audit-api
```

Hacerlo sin trabajos activos. Las próximas ejecuciones por comando también leerán el `.env` actualizado.

## Inicio, parada y diagnóstico

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --wait
docker compose -f compose.yaml -f compose.hybrid.yaml ps
docker compose -f compose.yaml -f compose.hybrid.yaml logs --tail 100 office audit-api
docker compose -f compose.yaml -f compose.hybrid.yaml stop
```

Para reconstruir después de cambios en el código o el parche:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit build auditor office
docker compose -f compose.yaml -f compose.hybrid.yaml up -d --wait
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
| Falla la rama predeterminada | Comprobar la rama declarada en GitHub y el acceso al repositorio; no hay fallback a otra rama |
| Fallo del modelo | Sesión OAuth, acceso al modelo, cuota y conectividad; no hay reintento automático |
| Revisión parcial | Leer el error de la célula y aprovechar solo sus resultados válidos; no confundirla con una revisión completa |

Para autorizar de nuevo el proveedor OAuth, completar personalmente el flujo que muestre:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit run --rm --entrypoint python auditor -m hermes_cli.main auth add openai-codex
```

## Persistencia y cambio de ordenador

| Ubicación | Qué conserva | Al clonar |
|---|---|---|
| `reports/` en el host | Evidencias, informes, estados y consultas | Se crea vacío |
| Volumen `hermes-auth` | Sesión del modelo de Hermes | Requiere iniciar sesión otra vez |
| Volumen `studio` | Estado local de la interfaz | Se crea de nuevo |
| Sesión de la pestaña | Última pregunta/respuesta visible por agente y revisión | No se traslada |

`docker compose -f compose.yaml -f compose.hybrid.yaml down` conserva los volúmenes y la carpeta `reports/`. `down -v` elimina los volúmenes del proyecto, incluida la sesión del modelo. Un reinicio del servicio interrumpe los trabajos en curso y no los reanuda.

Para conservar informes, detener los trabajos y copiar `reports/` a una ubicación autorizada para ese código. No es necesario mover sesiones OAuth: iniciar sesión personalmente en el otro ordenador. No compartir los volúmenes de autenticación ni publicar los informes como parte del repositorio.

## Ejecutar por comando

La inspección consume peticiones a GitHub pero ninguna llamada al modelo:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit run --rm -T auditor https://github.com/propietario/repositorio --inspect-only
```

Revisar `evidencia.json` y `distribucion.json` en la nueva carpeta de `reports/`. Si faltan arranque, manifiestos o configuración de datos, ajustar primero la selección o los límites antes de subir el modelo.

Para una revisión real desde la terminal:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit run --rm -T auditor https://github.com/propietario/repositorio
```

Comparte el bloqueo de ejecución con la oficina y las consultas. Los contadores `usage` son los reportados por Hermes; no representan una factura de la suscripción.

## Verificación del código del analizador

Estas pruebas usan datos controlados, sin GitHub ni llamadas al modelo. Prueban nuestro analizador, no la aplicación objetivo:

```powershell
pwsh -NoProfile -File scripts/check-backend.ps1
```

Las pruebas se ejecutan manualmente sobre el paquete instalado en una imagen separada; no se distribuyen en la imagen de producción ni amplían CI/CD. La construcción de `office` comprueba Next.js y TypeScript. Las verificaciones del piloto están en [PLAN_MVP.md](../PLAN_MVP.md); organización y compatibilidad actuales en [CORE.md](CORE.md).

## Herramienta de mantenimiento del formato

Los informes antiguos conservan su formato. Para probar el formato nuevo sobre una revisión guardada, sin volver a leer GitHub:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit run --rm -T --entrypoint python auditor /app/preview.py ID_REVISION_ORIGINAL
```

Este comando **sí consume hasta tres llamadas al modelo**, crea otra carpeta e identifica la evidencia guardada. Conserva los originales. Para actualizar solo la presentación de ese ejemplo derivado, sin modelo:

```powershell
docker compose -f compose.yaml -f compose.hybrid.yaml --profile audit run --rm -T --entrypoint python auditor /app/preview.py ID_EJEMPLO_DERIVADO --render-only
```

`--render-only` solo admite ejemplos derivados de formato 2 o 3. No utilizar el ejemplo derivado como prueba de haber revisado el estado actual de GitHub.

## Estándar editorial y presentación v12

Las reglas comunes y por sección viven en [resources/editorial/standard.md](../backend/src/arktic_office/resources/editorial/standard.md). `backend/src/arktic_office/reporting/editorial.py` incorpora Común y la especialidad al prompt; la consolidación registra versión y hash. El wheel incluye el mismo archivo canónico. No hay agente traductor ni llamadas extra para aplicar el formato.

El esquema conserva compatibilidad con resultados antiguos e incorpora datos estructurados opcionales para resumen, flujo, estado operativo y decisión. El renderizador `backend/src/arktic_office/reporting/view.py` no deduce relaciones ni reescribe observaciones con reglas específicas de un proyecto. Si un campo no existe, lo señala. Los títulos de riesgos y objetivos de mejora se redactan en la célula; las aportaciones originales y discrepancias se consultan en los anexos.

La oficina conserva el iframe sin permiso para ejecutar scripts. Su controlador de navegación abre el desplegable y el detalle técnico enlazados y permite volver al contexto del riesgo. El HTML independiente utiliza un script local y fijo de navegación; no evalúa contenido de modelos o repositorios. Markdown conserva explicaciones, fuentes y vínculos al registro.

Para revisar el formato sin agentes ni scanners, usar [el ejemplo ficticio](../examples/README.md). No ejecutar `preview.py` sin `--render-only` para una revisión meramente visual.

## Preparación híbrida opcional

El Bloque 8 utiliza el preparador independiente sobre el snapshot completo, sin explorador de modelos obligatorio. Las instrucciones anteriores incluyen ambos archivos Compose. `legacy` exige configurarlo expresamente y mantiene adquisición parcial de compatibilidad. Trazas, consultas 0/1 y límites: [PREPARACION.md](PREPARACION.md). No se duplican recorridos; CI/CD permanece sin cambios.

## Coordinación y capacidades del Bloque 5

`AUDIT_COORDINATION_MODE=deterministic` conserva el recorrido habitual. `ai` añade hasta una llamada de reparto y una de síntesis; no habilita búsquedas ni rondas especializadas. `AUDIT_CAPABILITIES` vacío omite Azure; `azure` la solicita expresamente. Ambas variables están documentadas en `.env.example`, sin modificar el `.env` local. Detalles y límites: [COORDINACION.md](COORDINACION.md).

## Oficina e historial del Bloque 6

La oficina refleja actividad guardada mediante el sondeo existente y deja estacionados los personajes al terminar. El historial confirmado muestra hasta diez consultas por revisión/agente; abrirlo no consume modelo y no se envía como conversación en preguntas nuevas. Comprobaciones y límites: [OFICINA.md](OFICINA.md).
