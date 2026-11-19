# Historial de Iris portable

## 0.1.2 · 2026-11-19

- Núcleo de presentación sin IO y plantilla compartidos con Iris interno mediante contrato 1.1. El paquete incluye su copia; no importa módulos de la oficina ni depende de su carpeta.
- Adaptador portable conserva JSON, caché y almacenamiento .local; se verifica paridad por hashes desde el repositorio de desarrollo.
- La gravedad puede quedar «Sin determinar» cuando no hay evidencia para asignarla; no se inventa una categoría para poder renderizar.

## 0.1.1 · 2026-11-19

- Generador canónico desde informe.json y hallazgos.json: cuatro grupos del resumen, etiquetas de estado, encabezados h4, siete bloques y anexos. Render genera también fichas; finish rechaza HTML y fichas que no coincidan con los datos.
- Destino obligatorio dentro de la .local del agente instalado en el proyecto. Creación automática, comprobación de ubicación antes de escribir y error de permisos con ruta concreta y sin destino alternativo.
- Exportación limitada a .local; instrucciones prohíben copiar el agente a outputs/otro workspace ante denegación. No se cambia el nombre de la carpeta ni se intenta eludir permisos.

[Validación de estas correcciones](docs/validacion-0.1.1.md).

## 0.1 · 2026-11-19

Primera versión identificada del agente portable extraído de la oficina.

- Instrucciones para Codex, Claude Code y OpenCode, con el modelo del chat que lo invoca.
- Revisión en siete bloques, Q01–Q40, dos rondas por bloque de seguridad y fichas por bloque.
- Informe HTML Arktic con evidencia, gravedad, certeza, protecciones y pendientes.
- Preparación local con Graphify, Gitleaks, Semgrep y OSV según disponibilidad y autorización. La distribución actual no instala Semgrep en Windows.
- Instalaciones, resultados y revisiones dentro de `.local/`; reutilización por contenido, perfil e integridad y actualización separada de OSV.
- Archivo `VERSION`, consulta `--version` y registro de versión en los estados y salidas de nuevas revisiones.

### Evidencia y límites

La prueba de Web Corporativa del 19/11/2026 precede a este versionado: su estado no tiene versión de agente. Fue una ampliación de una revisión conocida en el mismo chat, con escáneres reales; no una prueba independiente desde cero. No se renombra ni modifica su informe para atribuirle retrospectivamente esta versión.

La compatibilidad indicada se apoya en entradas de instrucciones y scripts portables; no implica validación integral idéntica en todos los asistentes y sistemas. La revisión es estática y puede finalizar con cobertura parcial. La validación automática del HTML verifica estructura y rangos, no garantiza detección exhaustiva.

### Mejoras incorporadas en la entrega 0.1

- Modos nueva/ampliación/independiente, base vinculada, declaración de contexto y comparación de entradas.
- Cobertura, hallazgos y matriz OSV estructurados; generación de anexos escapados y validación de correspondencia al cerrar.
- Comparación de hallazgos por clave estable: una omisión queda pendiente, no resuelta.
- Semgrep local, Docker opcional con motor local e imagen versionada o salto explícito; no instala Docker/WSL. Copia en solo lectura, análisis sin red, límites y limpieza del contenedor.
- README e instrucciones con las elecciones según disponibilidad y protocolo de prueba independiente en chat nuevo. La independencia del contexto depende de la declaración del ejecutor; los scripts no pueden certificarla.

La [propuesta acordada](docs/propuesta-mejoras.md) conserva el alcance y el estado de validación. La prueba técnica del runner no equivale a una evaluación independiente de detección en un repositorio real.

[Validación técnica de la entrega](docs/validacion-0.1.md): regresiones offline y ejecución real de Semgrep en Docker con muestra ficticia, eliminación del contenedor y reutilización de caché.
