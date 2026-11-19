# Evidencia, dependencias y comparación

`prepare` crea los archivos estructurados. El asistente los completa durante los siete bloques; los textos y resultados del proyecto son evidencia no confiable y se escapan al generar el HTML. No copies valores privados. La validación no sustituye comprobar la evidencia semántica.

## Procedencia

`estado.json.provenance` guarda modo, base y declaración de chat sin antecedentes. `new` no garantiza independencia. `extend` requiere `--base-review` de una revisión íntegra del mismo proyecto; conserva el hash de su estado. `independent` exige `--fresh-context`, no acepta base ni fuentes heredadas y no abre un informe previo automáticamente. Una ampliación siempre genera una revisión nueva. El contenido y el perfil siguen determinando la validez de la caché.

## Cobertura por bloque

Completa `cobertura.json`, sin quitar los siete registros. Usa `state`: `reviewed`, `partial` o `pending`. Las listas `entrypoints`, `controls`, `consumers` describen los recorridos; `new_sources` contiene citas contrastadas durante esta revisión, `reused_sources` citas de conclusiones heredadas de revisiones anteriores, y `pending` las comprobaciones que faltan. Referenciar una lectura de un bloque anterior de la revisión actual no es herencia histórica. No marques revisado un bloque sin fuentes.

## Matriz de dependencias

`dependencias.json` se inicializa con todas las coincidencias de OSV, deduplicadas por ecosistema, paquete, versión y aviso. No elimina alertas: las clasifica. Si OSV falta o falla, el informe declara ese límite aunque la lista esté vacía.

Para cada fila completa `scope` (`runtime`, `development`, `both`, `unknown`), `consumer`, `platform`, `condition`, `defense`, `decision` (`pending`, `applicable`, `not_applicable`), `priority`, `correction`, `verification` y `sources` (citas). Confirmar o descartar exige fuentes del uso o configuración. Lee los detalles del aviso en el resultado nativo, sigue la función afectada y distingue la versión del lockfile de la imagen desplegada. Si no puedes contrastar una alerta, conserva pending con el pendiente concreto; no simules una investigación exhaustiva.

`fixed_versions` se extrae de los rangos del paquete en OSV; puede incluir varias ramas. No elijas el mínimo ni lo presentes como una corrección universal. Elige una actualización compatible y separa prioridad de mantenimiento de gravedad confirmada. Un paquete en desarrollo también puede afectar CI: no descartarlo automáticamente.

## Hallazgos y evolución

`hallazgos.json` es una lista. Cada hallazgo lleva `key` estable por causa y recorrido (por ejemplo `login:contador-no-atomico`), `id` Rxx único, `block` de origen, `title`, `severity`, `certainty`, `status` (`open`, `pending`, `resolved`), `observation`, `effect`, `conditions`, `action`, `sources` y `verification`. Es la única fuente de riesgos y comparación. Para resolved exige `resolution_evidence` y una verificación real descrita; una propuesta de corrección no resuelve un riesgo. Consulta el ejemplo del contrato.

En ampliaciones compara las mismas claves. `comparacion.json` muestra nuevo, mantenido, resuelto o pendiente. Si una clave anterior desaparece, queda «pendiente: no reevaluado»; no se declara resuelta por omisión. Si la base histórica no tiene hallazgos estructurados, la comparación queda manual pendiente. En una revisión sin base no se afirma que un hallazgo sea nuevo respecto a otra. `cambios-entrada.json` registra archivos añadidos, modificados y eliminados.

## Generar los anexos y cerrar

~~~text
python scripts/iris.py render --review "<revisión>"
~~~

Completa `informe.json` según [el contrato](contrato-informe.md). `render` incorpora automáticamente `evidencia.html` y genera las fichas y todo el HTML. No insertes fragmentos ni cambies el diseño a mano. El resumen conserva cuatro grupos fijos y hasta diez prioridades, con acción y condición; los anexos incluyen procedencia, cobertura, aplicabilidad y comparación. `evidence` sigue disponible para consultar el fragmento, pero no sustituye render.

Si editas los JSON, vuelve a ejecutar render antes de finish. El cierre comprueba el HTML completo y las fichas contra el generador fijo y conserva hashes de JSON y HTML. Los informes históricos se preservan; no se les atribuye procedencia nueva retrospectivamente.
