# Plan MVP — Oficina de agentes para revisión de repositorios

## Objetivo
Aprender a utilizar Hermes Agent y Hermes3D con un caso útil: entender una aplicación y entregar al arquitecto un resumen breve para valorar su posible migración a VPS o Kubernetes. El arquitecto decide y solicita las verificaciones adicionales.

## Entrada y alcance
- Única entrada del usuario: URL del repositorio de GitHub. El acceso al repositorio y al modelo se configura en la instalación.
- Buscar primero `main`; si no existe, analizar `master`. Registrar rama y commit revisados. Si faltan ambas, informar de que no hay `main` ni `master`; los errores de acceso o conexión no activan el cambio de rama.
- Revisión de lectura acotada: estructura, documentación, manifiestos, configuración Docker y archivos de código relevantes. Indicar los archivos revisados y las exclusiones.
- Una ejecución activa. No ejecutar la aplicación analizada, instalar sus dependencias, hacer tests, modificar código ni desplegarla.

## Equipo y resultado
Coordinador → tres células → resumen consolidado → arquitecto.

| Célula | Revisión mínima |
|---|---|
| Seguridad | Acceso, configuración y posibles secretos evidentes, sin mostrar sus valores |
| Arquitectura y migración | Componentes, arranque, Docker, almacenamiento y conexiones; implicaciones observables para VPS o Kubernetes |
| Inventario tecnológico | Tecnologías, versiones declaradas, dependencias directas y servicios identificados |

El coordinador reúne la evidencia, ejecuta las revisiones y elimina duplicados. Las células pueden ejecutarse secuencialmente.

## Informe para el arquitecto
Estándar implementado en la fase 6: un único `informe.md`, breve y comprensible para el responsable técnico, generado desde los resultados separados de las tres células. El coordinador organiza y elimina duplicados; no añade conclusiones nuevas. Los agentes no editan simultáneamente el documento final.

El foco es seguridad, continuidad, estabilidad, recursos y condiciones de operación y gobernanza identificables en lo revisado. Las malas prácticas de código se incluyen solo cuando tienen una consecuencia concreta para estos aspectos. No se certifica seguridad ni se autoriza el despliegue.

### Plantilla del documento final
```markdown
# Evaluación preliminar de iniciativa

## Contexto
- Proyecto y propósito documentado:
- Repositorio, rama seleccionada y commit:
- Fecha y estado de las células: completadas o revisión parcial.

## 1. Resumen para el responsable técnico
Qué hace la aplicación según la evidencia disponible, principales riesgos
observados e información que falta para evaluar su incorporación a TI.
Incluir solo hechos respaldados; separar explícitamente los indicios.

## 2. Cómo está construida
| Componente | Tecnología declarada | Función identificada | Evidencia |
|---|---|---|---|

Explicar brevemente arranque, comunicaciones y almacenamiento.
Distinguir relaciones confirmadas de interpretaciones por comprobar.

## 3. Puntos que requieren atención
### [Título concreto del hallazgo]
- Área: seguridad / continuidad / operación.
- Certeza: confirmado en repositorio / indicio por confirmar.
- Qué se encontró:
- Por qué importa:
- Qué falta verificar o corregir:
- Evidencia: archivo:línea.
- Agente de origen:

## 4. Estabilidad, recursos y gobernanza
| Aspecto | Evidencia disponible | Información o validación pendiente |
|---|---|---|

Cubrir persistencia, recuperación, estabilidad, CPU/memoria, capacidad,
servicios externos, acceso a datos y responsabilidades, cuando sea posible.
Declarar lo desconocido sin asumir que un control o responsable no existe.

## 5. Implicaciones para la migración
- Elementos que facilitarían el traslado, con evidencia.
- Cambios o condiciones identificados.
- Preguntas pendientes para valorar destino y esfuerzo.

## 6. Alcance y límites
- Archivos revisados y exclusiones principales.
- Células que finalizaron y posibles fallos.
- Comprobaciones no realizadas.
- Referencia al detalle de evidencia.
```

### Aportaciones y trazabilidad
- **Inventario:** componentes, tecnologías, versiones declaradas y dependencias; distinguir declaración de uso comprobado.
- **Arquitectura:** arranque, datos, continuidad, estabilidad, configuración de recursos e implicaciones de migración. No presentar consumo o capacidad reales sin mediciones.
- **Seguridad:** acceso, exposición, configuración sensible y controles documentados. La gobernanza no acreditada por el repositorio queda como pregunta para el responsable.
- **Coordinador:** reunir esas aportaciones en las secciones de la plantilla y agrupar pendientes sin duplicados, manteniendo fuente y agente de origen.

Conservar los archivos actuales `celulas/security.json`, `celulas/architecture.json` y `celulas/inventory.json` como resultados separados, y `evidencia.json` con commit, cobertura y citas completas. El arquitecto debe poder leer el resumen sin abrir estos archivos.

### Reglas de contenido
- Cada espacio se completa con evidencia o «no determinado en esta revisión»; no rellenar con recomendaciones genéricas. Las dudas concretas van junto al aspecto o condición de migración correspondiente, conservando su origen.
- Mantener separados confirmados, indicios y dudas. Una posible implicación es condicional; una cita válida no demuestra por sí sola que la interpretación sea correcta.
- Referencias breves `archivo:línea` como enlaces a GitHub fijados al commit revisado, y citas completas en la evidencia. Priorizar lo que afecta datos, acceso y operación, sin inventar urgencias, puntuaciones de preparación ni estimaciones de esfuerzo o recursos.
- Lectura estática parcial: no confundir células completadas con repositorio revisado íntegramente, controles operativos verificados o despliegue seguro. La ausencia de hallazgos no acredita seguridad ni la ausencia de un componente.
- Objetivo de extensión: una o dos páginas equivalentes, dejando el detalle en los archivos de la revisión. El formato 3 posterior amplía la respuesta y conserva los riesgos sin recortarlos al límite original; ver actualización de seguridad al final.

## Base técnica
Reutilizar Hermes3D con oficina **2D por defecto** y conectar Hermes Agent para las revisiones reales. Empezar con el modo demo identificado como tal y comprobar pronto la integración real.

Arrancar la solución local con Docker Compose: interfaz y motor de análisis separados, informes persistentes y credenciales fuera de las imágenes. Mantener los contenedores sin privilegios y sin acceso al socket Docker. Reutilizar gráficos y animaciones; adaptar el mapa a los equipos que existan.

## Fases y seguimiento
Cada fase entrega una funcionalidad comprobable. Estimación orientativa total: catorce días laborables, con cinco días para las fases 5–7. Fechas ilustrativas si se empieza el 21/10/2026; no representan avance real.

| Fase | Funcionalidad completa | Terminada cuando… | Estimación | Estado |
|---|---|---|---|---|
| 1 | Oficina local en Docker | Hermes3D arranca con Compose y permite explorar una demo claramente identificada | 2 días | Completada y verificada (20/10/2026) |
| 2 | Primera revisión con Hermes Agent | Recibe una URL, lee `main` o `master` según disponibilidad, registra rama y commit y devuelve observaciones con evidencia usando el runtime real | 2 días | Completada y verificada (20/10/2026) |
| 3 | Equipo e informe consolidado | Las tres células producen un único informe con confirmados, indicios y dudas | 3 días | Completada y verificada (20/10/2026) |
| 4 | Flujo completo desde la oficina | Permite iniciar el análisis, ver estados reales y descargar el informe; muestra fallos sin ocultarlos | 2 días | Completada y verificada (20/10/2026) |
| 5 | Consultas mínimas al equipo | Desde una revisión terminada, pulsar un personaje permite preguntar sobre su resultado y evidencia; responde con fuentes o reconoce que falta información | 2 días | Completada y verificada (20/10/2026) |
| 6 | Informe comprensible para el arquitecto | Un único informe sigue la plantilla acordada, conserva resultados por célula y explica riesgos, operación y migración con fuentes y grados de certeza; el usuario valida su utilidad | 2 días | Completada y verificada (20/10/2026) |
| 7 | Piloto validado por el arquitecto | Tras validar las fases 5 y 6, se revisa el repositorio objetivo y el arquitecto confirma la utilidad del informe y las consultas para su evaluación manual | 1 día | Completada y validada por el usuario (20/10/2026) |

```mermaid
gantt
    title MVP — planificación inicial orientativa
    dateFormat YYYY-MM-DD
    axisFormat %d/%m
    excludes weekends
    section Base
    1. Oficina local en Docker       :done, f1, 2026-10-21, 2d
    2. Revisión real con Hermes      :done, f2, after f1, 2d
    section Producto
    3. Equipo e informe consolidado  :done, f3, after f2, 3d
    4. Flujo desde la oficina        :done, f4, after f3, 2d
    5. Consultas al equipo           :done, f5, after f4, 2d
    6. Informe para el arquitecto    :done, f6, after f5, 2d
    section Validación
    7. Piloto con el arquitecto      :done, f7, after f6, 1d
```

**Avance:** fases 1–7 completadas; piloto validado por el usuario con bookingApi. Verificado desde la oficina 2D: iniciar una revisión nueva de Hermes3D con acceso autenticado a GitHub, leer `main` en el commit `beb76292747b816ef317aa6f9a3992e0014f81d9`, mostrar estados reales y abrir y descargar el informe. La recarga del navegador conservó la revisión. Las tres células finalizaron con Luna/low: 3 llamadas, 15462 tokens reportados por Hermes, sin reintentos ni resultados reutilizados. Evidencia e informe: `reports/254eaa96-b200-46c2-8a7f-3dd6d7e1df62/`. Compilación y 28 pruebas superadas; comprobados rechazo de URLs con ramas y solicitudes de otro origen, errores visibles y publicación solo en localhost. Operación en `README.md`. Fases 6 y 7 validadas por el usuario; las fechas del Gantt son orientativas.

## Fase 5 — Consultas mínimas
- Seleccionar una revisión terminada, completa o parcial, y pulsar Coordinador, Seguridad, Arquitectura o Inventario para abrir una pregunta y respuesta breve. Mostrar siempre qué revisión, commit y agente se consultan.
- Cada célula recibe únicamente su resultado y la evidencia que revisó. El coordinador responde dudas generales con el informe consolidado y sus fuentes; esta consulta sí requiere modelo, aunque la consolidación siga siendo por código.
- Una pregunta independiente por envío, sin historial largo ni conversación entre agentes. Consultar solo al personaje elegido, heredando el perfil económico; no relanzar el equipo, releer GitHub ni ejecutar herramientas. Serializar las consultas con las revisiones para conservar una ejecución activa.
- Citar las fuentes utilizadas y distinguir explicación, indicio y dato ausente. Si una célula falló o la respuesta no está en la evidencia, indicarlo. Mostrar errores sin reintentos automáticos.
- Verificar con una pregunta respaldada, otra fuera de la cobertura y un fallo de acceso al modelo. La consulta no modifica el informe original.

**Verificación de fase 5 (20/10/2026):** apertura desde tarjetas y personaje 2D, dos consultas reales sobre la revisión guardada de Hermes3D: Seguridad respondió con fuentes y Coordinador reconoció que no había mediciones de RAM. Luna/low, 2 llamadas, 10956 tokens reportados por Hermes; sin releer GitHub ni modificar el informe. Resultados en `reports/254eaa96-b200-46c2-8a7f-3dd6d7e1df62/consultas/`. Compilación y 40 pruebas superadas, incluidas fuentes inválidas, células fallidas, fallo de acceso al modelo simulado, interrupciones y exclusión con revisiones por comando. Mejora aprobada e implementada: última pregunta/respuesta por revisión y agente conservada en la sesión de la pestaña, sin enviarla como historial. Compilación y 2 pruebas de interfaz adicionales superadas: restauración sin otra petición, aislamiento entre agentes/revisiones y envío únicamente de la pregunta actual; sin nuevas llamadas al modelo.

## Fase 6 — Claridad del informe
Implementar el estándar y la plantilla de «Informe para el arquitecto» en la generación, lectura en la oficina y descarga Markdown. Adaptar las instrucciones, el esquema de resultados y su validación para obtener observaciones, implicaciones y pendientes respaldados, antes de aumentar modelos o límites. Mantener resultados separados por célula y un único documento final; conservar las aportaciones válidas si otra célula falla.

Validar primero el ejemplo ya disponible: el usuario debe poder entender qué hace la aplicación, cómo está construida, qué riesgos afectan a datos/acceso/continuidad, qué se sabe de recursos y qué falta para evaluar su incorporación y migración. Comprobar fuentes, grados de certeza, tratamiento de datos desconocidos, resultados parciales y lectura útil sin abrir JSON. Conservar informes anteriores e identificar cualquier reformateo como derivado de la evidencia original, sin simular una revisión nueva. No iniciar el repositorio objetivo hasta aceptar el formato.

**Verificación de fase 6 (20/10/2026):** formato 2 generado sobre la evidencia guardada de Hermes3D, sin releer GitHub ni comprobar el `main` actual. Ejemplo: `reports/20261020T130733584929Z-fase6/informe.md`; originales conservados y sus hashes comprobados. Las tres células finalizaron con Luna/low: 3 llamadas, 16615 tokens reportados por Hermes, sin reintentos. Compilación y 47 pruebas superadas; comprobados fuentes, datos desconocidos, resultados parciales y compatibilidad con informes anteriores. Lectura en la oficina, enlaces al commit y descarga Markdown verificados; el archivo descargado coincide con el guardado. El usuario confirmó que el formato es útil. Al cerrar la fase 6, la fase 7 seguía sin iniciar.

## Fase 7 — Piloto
**Piloto completado y validado por el usuario (20/10/2026).** Repositorio de prueba: `https://github.com/ziuld/bookingApi`, en sustitución de la iniciativa empresarial aún no disponible. Por instrucción del usuario, el sistema busca primero `main` y utiliza `master` solo si falta `main`; informa de error si faltan ambas. Los fallos de acceso o conexión no activan el cambio de rama. Rama revisada: `master`; commit `c0d247e3226d77a83471c7a1b32afdb0981eb7f1`.

Inspección previa sin modelo y revisión iniciada desde la oficina: 12 archivos, 20801 bytes; se añadió soporte de manifiestos Gradle y del punto de entrada `Application.java` sin subir los límites. Compilación y 51 pruebas superadas. Las tres células finalizaron con Luna/low: 3 llamadas, 15832 tokens reportados por Hermes, sin reintentos. Informe: `reports/02589807-3135-4323-9409-7745b7b3fbb1/informe.md`; lectura en la oficina, enlaces al commit y descarga comprobadas. Una consulta real al Coordinador sobre los pendientes de base de datos respondió con fuentes y distinguió hechos de verificaciones pendientes: 1 llamada, 3910 tokens, sin releer GitHub ni modificar el informe. La aplicación analizada no se ejecutó ni desplegó.

El usuario confirmó que el informe y la consulta son útiles para la evaluación. Se cierra la fase 7 con bookingApi como repositorio de prueba; la iniciativa empresarial aún no se ha revisado. Esta validación acredita la utilidad del MVP y no autoriza el despliegue de la aplicación analizada.

## Oficina compacta
Implementada: cuatro puestos de análisis, sala de revisión y zona de café; mapa de 28 × 22 casillas, estilo oscuro con acento turquesa y panel separado del mapa. Compilación, 26 pruebas de mapa/movimiento/estados y lectura del informe desde el navegador verificadas, sin nuevas llamadas al modelo.

Mejora visual opcional: bocadillos breves ligados a estados reales. Añadir puestos o salas cuando se incorporen equipos reales, sin construir expansión automática.

## Después del MVP
Añadir verificaciones, tests o análisis más profundos según las dudas reales del piloto. La publicación de nuestra solución mediante Azure DevOps y Kubernetes se abordará después; la migración de la aplicación analizada seguirá su propia evaluación humana.

**Cierre documental (20/10/2026):** README general y guías de instalación, flujo, operación y preparación del repositorio en `docs/`; versiones fijadas, parche y avisos de terceros conservados. Exclusiones de Git y enlaces locales comprobados. Fuentes reconstruidas localmente desde los commits originales y el parche, con construcción de ambas imágenes y 51 pruebas superadas, sin llamadas al modelo. La instalación en otro ordenador y la subida a un remoto siguen sin ejecutarse.

## Perfil inicial del piloto (histórico; sustituido por la actualización de seguridad)
Mínimo recomendado inicialmente: **gpt-6-luna con razonamiento low**, usando OAuth de ChatGPT. Es el modelo que ya produjo un informe real en este piloto; no se ha demostrado todavía que sea suficiente para el repositorio objetivo. La cuota de la suscripción y la facturación API son distintas.

Configuración ajustable en `.env`: `AUDIT_MODEL=gpt-6-luna`, `AUDIT_REASONING=low`, `AUDIT_MAX_FILES=12`, `AUDIT_MAX_TOTAL_BYTES=48000`. Cada célula recibe hasta 6 archivos/24 KB y devuelve hasta 2 confirmados, 1 indicio y 2 dudas. `AUDIT_MAX_OUTPUT_TOKENS=2500` solicita un techo por célula en modo API; esta versión de Hermes no lo envía al backend Codex OAuth, por lo que con Plus la brevedad depende de las instrucciones y no es un límite duro de salida. No hay un presupuesto total de tokens garantizado. El prompt, las instrucciones internas y el razonamiento también consumen contexto. La validación de citas se hace con código.

Seguridad, arquitectura e inventario heredan ese mismo modelo/razonamiento. Se puede ajustar una sola célula mediante las variables opcionales de `.env.example`. El coordinador distribuye evidencia y consolida mediante código, sin una llamada adicional al modelo. El informe identifica fuentes y células; conserva resultados si otra falla, declara cobertura parcial y no resuelve contradicciones semánticas automáticamente.

Antes de la prueba objetivo: ejecutar `--inspect-only` y revisar si los archivos seleccionados cubren arranque, dependencias, Docker y datos. Si faltan archivos, ajustar primero la selección o subir hasta 20 archivos/90000 bytes. Si la evidencia es suficiente pero la interpretación es deficiente, probar Luna con `medium`; considerar Sol solo para la célula que lo necesite. No aumentar modelos ni repetir llamadas automáticamente. Comparar utilidad y citas con el arquitecto antes de conservar un ajuste.

## Actualización de seguridad — 22/10/2026

Cambio aprobado: reporte ejecutivo visual con gravedad separada de certeza, acciones y controles pendientes; perfil acotado OWASP; lectura priorizada para seguridad; Gitleaks y OSV sobre archivos descargados sin ejecutar el proyecto. Conserva inventario, consultas e informes anteriores. Semgrep queda para una ampliación posterior con reglas revisadas.

Configuración actual: 24 archivos / 120000 bytes de texto global; Seguridad 12 / 64000, otras células 6 / 24000. Seguridad Sol/medium y demás Luna/low en `.env.example`; disponibilidad sujeta a la cuenta. El coordinador consolida sin otra llamada. Límites y operación en [docs/SEGURIDAD.md](docs/SEGURIDAD.md).

**Verificado (22/10/2026):** imágenes construidas, 66 pruebas del auditor y 4 de interfaz superadas. Gitleaks detectó un token ficticio y no alertó en el control sin secreto; OSV detectó avisos para una dependencia de prueba sin resolver transitivas. Piloto nuevo de bookingApi terminado desde la oficina: `reports/e3b1f988-3940-4ce3-94fe-4ac14fe49888/`, rama `master`, commit `c0d247e3226d77a83471c7a1b32afdb0981eb7f1`, 24 archivos / 50885 bytes de texto. Tres llamadas: Seguridad Sol/medium (14162 tokens), Arquitectura Luna/low (6621) e Inventario Luna/low (6391), total 27174 tokens reportados por Hermes. Las comprobaciones pequeñas del modelo consumieron llamadas adicionales y no forman parte de ese total.

Reporte visual y filtro de indicios comprobados; impresión confirmada por el usuario. Presentación ajustada sin nuevas llamadas para resumir datos sin confundirlos con riesgos y agrupar componentes del mismo nombre, conservando las variantes en el detalle. Informes previos conservados. En este piloto OSV quedó explícitamente no evaluado porque no se seleccionaron archivos de versiones resueltas admitidos; no se afirma ausencia de vulnerabilidades. No se ejecutó la aplicación ni se revisó la iniciativa empresarial objetivo. La selección sigue siendo heurística y la interpretación/severidad requieren revisión humana.

## Propuesta Azure y ejemplo ficticio — 23/10/2026

Arquitectura incorpora una propuesta DevOps preliminar y separada de los hallazgos: una opción principal sencilla, sus motivos, fuentes técnicas, supuestos, servicios mínimos, entrega y reversión, y validaciones del arquitecto. Se genera dentro de su llamada habitual con Luna/low. El perfil no obliga a usar Kubernetes ni presupone infraestructura corporativa disponible; si falta información, deja el destino por definir.

Por instrucción del usuario, no se ejecutan más análisis ni llamadas a agentes para validar esta ampliación. Se crea el ejemplo completamente ficticio **Portal de personal**, con riesgos inventados y una propuesta App Service + PostgreSQL gestionado. Fuentes y resultados marcados como simulación; consultas bloqueadas para evitar consumo accidental. Se reproduce mediante `examples/create_fictional_report.py`. No se han ejecutado el proyecto objetivo, scanners ni agentes para ese ejemplo.

Verificación de código: 78 pruebas superadas, incluidas fuentes de la propuesta, límites, conservación de informes anteriores y rechazo de consultas sobre simulaciones. La generación real del nuevo apartado con un modelo sigue pendiente por decisión del usuario; el ejemplo solo valida el formato.

Imágenes actualizadas y servicios saludables. Ejemplo abierto en la oficina: resumen con 2 críticos, 3 altos, 2 medios, 1 bajo y 3 indicios, todos inventados; apartado Azure visible. Fuentes identificadas como ficticias y consultas bloqueadas. Capturas locales en `artifacts/demo-portal-prioridades.png` y `artifacts/demo-portal-azure.png`. No se hicieron llamadas a agentes para crear ni mostrar este ejemplo.

## Estándar editorial y formato v12 — 23/10/2026

Implementado el formato aprobado en generación, lectura en la oficina y Markdown. La guía compartida `docs/ESTANDAR_COMUNICACION_INFORMES.md` se incorpora a las instrucciones de cada célula y consulta; la consolidación determinista registra su versión y conserva las aportaciones originales. No añade llamadas al modelo.

El informe presenta resumen, flujo con conexiones observadas/inferidas/desconocidas, riesgos con gravedad y certeza independientes, datos y recuperación, inventario, mejoras por dominio, propuesta Azure, decisión humana y anexos. El detalle técnico es desplegable y permite regresar al contexto. Los datos ausentes y resultados parciales se muestran explícitamente; se conservan variantes contradictorias y fuentes. Los nuevos campos editoriales se exigen en futuras revisiones sin invalidar informes antiguos.

Verificado con el ejemplo ficticio `demo-editorial-v12-portal-personal`: 90 pruebas del auditor y 2 de interfaz superadas (filtro y navegación; impresión excluida). Construcciones realizadas y navegación al riesgo, apertura del respaldo técnico y regreso al contexto comprobados en la oficina. Descarga Markdown verificada: coincide exactamente con el archivo guardado. Parche de interfaz actualizado y comprobado. Referencia v12 intacta; informes anteriores conservados. Muestra independiente: `artifacts/informe-arktic-v12-muestra.html`; captura: `artifacts/informe-v12-oficina.png`.

No se ejecutaron revisiones, agentes, scanners ni llamadas a modelos para este cambio. Queda pendiente comprobar la calidad de redacción y los nuevos campos con una ejecución real expresamente autorizada; el ejemplo valida presentación y comportamiento, no hallazgos reales.

## Corrección de cobertura tras sysmeh — 23/10/2026

La revisión real autorizada `eac4e30c-b6bf-4d55-8629-0a61a8653b7e` terminó parcial: Seguridad e Inventario válidos; Arquitectura rechazada por una propuesta Azure inválida. La selección previa dejó fuera manifiestos y configuración de base de datos, por lo que Arquitectura e Inventario recibieron solo README. El informe histórico se conserva; sus cero riesgos no acreditan seguridad. Consumo reportado: tres llamadas y 14950 tokens.

Corregido el reparto por tipos de archivo para incluir código, manifiestos, arranque, datos, rutas y configuración sin depender del README ni aumentar límites. Se distinguen Composer y Docker Compose y se prioriza lógica concreta frente a controladores base. Seguridad muestra sus controles y pendientes en el diagnóstico, aunque no haya riesgos clasificables. Una propuesta Azure inválida o ausente deja Arquitectura parcial y conserva sus resultados si superan validación independiente; no se recuperan citas inválidas ni se reintenta el modelo.

Inspección real sin modelo ni scanners: `reports/20261023T124047706673Z-e52b816c/`, mismo commit `e52b816c3d88d99c20c77535cecd9a8876db5514`, rama master. Se incluyeron composer.json, composer.lock, package.json, config/database.php y rutas/código. La calidad de los hallazgos con esta nueva cobertura sigue pendiente de otra revisión autorizada; no se ha repetido el equipo de agentes.

Verificación de la corrección: 97 pruebas locales superadas, incluidas cobertura sin README, múltiples manifiestos, exceso de middleware y recuperación parcial de Arquitectura sin publicar citas inválidas. Se conservaron los límites y modelos; no se ejecutaron llamadas adicionales al modelo. Imágenes actualizadas para las próximas revisiones.

## Cierre: información insuficiente y reporte compacto — 23/10/2026

La falta de evidencia tiene estado terminal `informacion_insuficiente`, con `mensaje` y `necesita` disponibles en la API y visibles en la oficina sin personaje rojo ni ejecución permanente. Con aportaciones válidas y limitaciones, se conserva un resultado parcial. La ausencia de archivos analizables no llama al modelo. Sesión, conexión o citas inválidas siguen siendo fallos técnicos; no se ocultan como falta de información.

La guía y el contrato permiten declarar insuficiencia sin romper el JSON. Una hipótesis del propósito requiere fuentes y se identifica como tal. El reporte reúne las limitaciones y siguientes pasos en un bloque, omite secciones y tablas vacías y conserva las aportaciones, cobertura y resultados originales. Los bloques opcionales de Arquitectura se validan por separado: un diagrama o propuesta inválidos no descartan un núcleo válido; las advertencias quedan registradas sin reintentos.

Verificado: 108 pruebas de backend y 4 de interfaz superadas; prueba de impresión excluida. Ambas imágenes construidas, servicios saludables, API y descarga del ejemplo comprobadas. Ejemplo `demo-informacion-insuficiente` visible en la oficina: cero personajes en error y reporte breve con lo necesario para avanzar. Captura: `artifacts/informacion-insuficiente-oficina.png`. Vista compacta de los resultados guardados de sysmeh: `artifacts/sysmeh-informe-compacto.html` y `.md`; hashes de los originales comprobados y conservados. Parche de interfaz actualizado para reproducción.

No se ejecutaron nuevas revisiones, scanners ni llamadas a modelos para validar este cierre. Las respuestas controladas verifican el comportamiento; la producción de este nuevo contrato por un modelo sigue pendiente de la siguiente revisión real. Las ejecuciones históricas mantienen su estado original y no se presentan como corregidas o reevaluadas.

## Entrega versionada — 23/10/2026

Primera versión propia explícita: frontend 0.2.0 y backend 0.2.0, con archivos de versión independientes, imágenes y etiquetas OCI correspondientes, versión visible de oficina y API, y CHANGELOG por componente. Las versiones de Hermes permanecen fijadas por sus commits originales.

Verificación de entrega: 108 pruebas del backend y 9 de interfaz; impresión excluida. Imágenes construidas y servicios saludables. Parche de frontend comprobado sobre fuentes originales limpias. Archivos preparados para Git escaneados con Gitleaks sin detecciones; .env, informes, artefactos y vendor excluidos. No se ejecutaron nuevas revisiones ni llamadas a modelos. La entrega se propone mediante PR a main; no se fusiona ni publica imágenes o etiquetas de release automáticamente.
