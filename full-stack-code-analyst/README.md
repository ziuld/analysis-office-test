# Iris · Full Stack Code Analyst

Versión **0.1.2** · [Historial](CHANGELOG.md) · [Alcance de las mejoras](docs/propuesta-mejoras.md).

Copia esta carpeta completa a tu proyecto y dile a Codex, Claude Code u OpenCode:

> Usa `./full-stack-code-analyst/AGENT.md` para que Iris analice este repositorio.

Iris usa el modelo y esfuerzo del chat que la invoca. Comprueba primero si hay una revisión vigente. Si la hay, puedes abrir el informe guardado sin repetir análisis. Si hace falta una revisión, pregunta las herramientas que quieres usar, recorre siete bloques y genera el HTML Arktic con Q01–Q40, evidencias y pendientes. El destino es siempre la `.local/` de la copia instalada dentro del proyecto.

~~~text
full-stack-code-analyst/
├── README.md
├── VERSION                     Versión del agente
├── CHANGELOG.md                Cambios y límites por entrega
├── AGENT.md
├── AGENTS.md
├── CLAUDE.md
├── skills/revisar-codigo/       Flujo y siete guías
├── plantillas/informe.html      Identidad Arktic y navegación incluidas
├── scripts/                     Comprobación, instalación, análisis y caché
├── tools/                       Versiones, reglas y avisos
└── docs/                        Uso y contratos
~~~

Los archivos generados aparecen solo dentro de esta carpeta:

~~~text
.local/
├── tools/                       Ejecutables, entornos y runtimes locales
├── cache/                       Resultados reutilizables por herramienta
│   ├── graphify/
│   ├── gitleaks/
│   ├── semgrep/
│   └── osv/
└── revisiones/
    └── fecha-id/
        ├── entrada/inventario.json
        ├── graphify/estado.json
        ├── gitleaks/estado.json
        ├── semgrep/estado.json
        ├── osv/estado.json
        ├── bloques/             Fichas de los siete bloques
        ├── informe.json         Datos del informe; HTML generado automáticamente
        ├── cobertura.json       Recorridos y procedencia de fuentes
        ├── dependencias.json    Aplicabilidad de cada aviso OSV
        ├── hallazgos.json       Riesgos con claves estables
        ├── cambios-entrada.json Cambios de archivos respecto a la base
        ├── comparacion.json     Evolución de hallazgos
        ├── evidencia.html       Anexos generados desde la evidencia
        ├── estado.json
        └── informe-iris.html
~~~

La salida obligatoria es el HTML de la revisión en `.local/`. Se crea automáticamente esa carpeta al iniciar. Si el equipo deniega escribir, Iris pide permiso para esa carpeta y reintenta allí; si no se concede, se detiene. No copia el agente a outputs, otro workspace o un temporal. `export` solo permite copias dentro de `.local/`; puedes copiar manualmente un informe terminado después.

La IA completa los JSON y ejecuta `render`; no redacta el HTML. El generador fijo conserva tarjetas, etiquetas, encabezados, fuentes y navegación Arktic. El cierre rechaza diferencias con el resultado canónico. El mapa y las entradas de herramientas se conservan en la caché.

El núcleo de presentación y la plantilla comparten contrato 1.1 con Iris integrado en Arktic Office. Se incluyen dentro de esta carpeta: el agente portable no necesita instalar ni localizar la oficina. Modelo, permisos, almacenamiento y herramientas se adaptan a cada entorno.

Para los scripts necesitas Python 3.11 o posterior. Git permite un inventario más preciso del proyecto. Las herramientas disponibles se aprovechan y las que faltan se ofrecen para instalación aislada con versiones declaradas. Graphify orienta las lecturas, Gitleaks detecta candidatos a secretos, Semgrep señala patrones y OSV contrasta dependencias con avisos. La IA del chat investiga esos resultados.

**Docker es opcional y recomendable para facilitar Semgrep aislado, especialmente en Windows.** Si quieres esa opción, instala y deja arrancado Docker con motor Linux antes de invocar Iris. Iris comprueba el motor y ofrece contenedor temporal o ejecución local según disponibilidad. Puede descargar una imagen versionada con tu aceptación. Analiza una copia en solo lectura, sin red durante el escaneo, y guarda resultados dentro de `.local/`; no monta todo tu proyecto ni el socket Docker. El aislamiento reduce riesgos, no garantiza seguridad absoluta. La imagen puede conservarse para futuras ejecuciones; el contenedor se elimina al terminar.

Iris no instala Docker ni WSL, ni requiere reiniciar como parte de su flujo. Si no tienes Semgrep local ni Docker funcionando, continúa con las otras herramientas y declara esa cobertura pendiente. La instalación local incluida de Semgrep admite Linux/macOS; en Windows puedes usar un ejecutable compatible ya preparado o la vía Docker opcional.

Las revisiones distinguen reutilización, revisión nueva y ampliación con una base vinculada. Una evaluación independiente requiere un chat nuevo sin antecedentes: recalcular herramientas no elimina el historial. Consulta [evidencia y comparación](docs/evidencia-revisiones.md) y [la prueba independiente](docs/prueba-independiente.md).

La caché detecta contenido, cambios sin commit y archivos nuevos del inventario. Si cambias de rama o commit, Iris vuelve a comprobarlo y reutiliza las entradas que permanezcan iguales. Los avisos OSV pueden actualizarse por separado, con consulta de metadatos por red autorizada. Las instalaciones también requieren acceso a sus fuentes de distribución.

`.local/` queda ignorada por el Git del paquete y debe conservarse en privado porque puede contener copias del código y diagnósticos. Para incorporar Iris a otro proyecto, copia las instrucciones, recursos y scripts y deja que prepare allí su almacenamiento local.

[Ejecución y caché](docs/ejecucion-local.md) · [Integración](docs/integracion.md) · [Graphify](docs/graphify.md) · [Contrato del informe](docs/contrato-informe.md)

Consulta la versión con `python full-stack-code-analyst/scripts/iris.py --version` desde la raíz del proyecto. `VERSION` identifica al agente; `tools/versions.json` identifica las herramientas. Los estados de nuevas revisiones conservan `agent_version`. No se asigna una versión retrospectiva a revisiones anteriores.
