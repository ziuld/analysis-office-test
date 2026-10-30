# [Nombre de la aplicación]

> Plantilla editable del informe actual · borrador para revisión · 29/10/2026

<!-- Reglas generales: redacción ejecutiva y comprensible para un cliente o director de tecnología; sin coletillas de IA, lenguaje promocional ni frases vacías. Mantener condiciones e incertidumbres concretas. Responder directamente y evitar repetir fórmulas genéricas debajo de cada respuesta. -->

<!-- Sustituye los campos entre corchetes. Puedes cambiar títulos, orden, preguntas y explicaciones. Los identificadores Q01–Q40 permiten relacionar tus cambios con el cuestionario del sistema. Esta plantilla no contiene resultados de una revisión concreta. -->

**Repositorio:** [URL o identificación del repositorio]

**Rama y commit:** [rama] · [commit revisado]

**Fecha de la revisión:** [fecha y hora]

## 1. Resumen ejecutivo

[Explicar en un párrafo el propósito de la aplicación, indicando claramente si es un Frontend, Backend, Full-stack (ambos) u otro tipo de proyecto]

[framework principal y lenguaje dominante]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas, documentación o respuestas del análisis que respaldan esta descripción.]

</details>

### Hallazgos clave y riesgos

[Breve síntesis en un párrafo de las conclusiones principales del análisis].

#### Hallazgos de seguridad

- [Círculo de gravedad] **R01 · [Nombre ejecutivo del riesgo]** — [Resumen breve y comprensible].
- [Círculo de gravedad] **R02 · [Nombre ejecutivo del riesgo]** — [Resumen breve y comprensible].

<!-- Cada elemento enlaza al detalle con el mismo código y nombre. Mostrar únicamente hallazgos respaldados de seguridad, conservando si son observaciones o indicios. Los riesgos de otra naturaleza mantienen su clasificación y no se convierten en vulnerabilidades. Colores: 🔴 crítica, 🟠 alta, 🟡 media, 🔵 baja; una leyenda común y etiquetas accesibles permiten entenderlos. -->

<details>
<summary>Fuentes consultadas</summary>

- [Respuestas de los especialistas y evidencias que sustentan la síntesis.]

</details>

### Principales riesgos identificados

<!-- Mostrar como máximo diez riesgos respaldados por evidencia, ordenados por gravedad. Si hay menos, eliminar los bloques sobrantes. No inventar riesgos para completar diez. Los dos bloques siguientes ilustran la forma; se generan entre cero y diez según los resultados. Si no hay ninguno, sustituir los bloques por una explicación del alcance: «No se han identificado riesgos con evidencia suficiente en el alcance revisado», indicando qué quedó sin comprobar. -->

#### R01 · [Título ejecutivo comprensible para cliente del riesgo]

**Gravedad:** [🔴 crítica / 🟠 alta / 🟡 media / 🔵 baja; mostrar el círculo en HTML]

**Respaldo:** [patrón observado en código / indicio que requiere comprobación]

[Explicar qué se ha encontrado y en qué parte de la aplicación, en lenguaje natural.]

**Consecuencia posible:** [Qué podría ocurrir y a quién o a qué afectaría.]

**De qué depende:** [Condiciones necesarias y protecciones observadas que pueden impedirlo o limitarlo.]

**Qué queda por comprobar:** [Qué falta para confirmar o descartar el problema, cuando corresponda.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo, líneas y resultado determinista, si corresponde.]

</details>

#### R02 · [Título ejecutivo comprensible para cliente del riesgo]

**Gravedad:** [🔴 crítica / 🟠 alta / 🟡 media / 🔵 baja; mostrar el círculo en HTML]

**Respaldo:** [patrón observado en código / indicio que requiere comprobación]

[Explicar qué se ha encontrado y en qué parte de la aplicación, en lenguaje natural.]

**Consecuencia posible:** [Qué podría ocurrir y a quién o a qué afectaría.]

**De qué depende:** [Condiciones necesarias y protecciones observadas que pueden impedirlo o limitarlo.]

**Qué queda por comprobar:** [Qué falta para confirmar o descartar el problema, cuando corresponda.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo, líneas y resultado determinista, si corresponde.]

</details>


### Protecciones y buenas prácticas comprobadas

<!-- Mostrar hasta cinco implementaciones favorables relevantes, respaldadas por código/configuración y enlazadas con sus preguntas y fuentes. No inferirlas de scanners limpios o ausencia de hallazgos. Mantener los límites de cada protección; no compensar vulnerabilidades ni declarar seguridad global. Si no hay ninguna, indicar que esta revisión no documentó protecciones con respaldo suficiente, sin afirmar que no existan. -->

- **[Nombre comprensible de la protección].** [Qué se comprobó y en qué flujo, con su alcance concreto.] — [Qxx · pregunta correspondiente]

### Pendientes de validar

[Lista breve, ejecutiva y respaldada de las partes que no se revisaron y del alcance que no cubrieron las herramientas. No convertir respuestas desconocidas, citas rechazadas o pruebas en vivo pendientes en afirmaciones de que no se leyó código. Omitir todo el apartado si no hay omisiones concretas documentadas.]

## 2. Análisis por preguntas

<!-- La respuesta empieza directamente con su explicación. Debajo se aclara su alcance y lo que falta comprobar. No anteponer «parcial», «respondida» o «no_comprobado». Cuando no aplique, explicar por qué y con qué respaldo; cuando falte evidencia, explicar qué se revisó y qué no pudo determinarse. -->

<!-- Ejemplo de tono: «En los controladores revisados no se observa una comprobación de identidad. Podría existir una protección en filtros o en otra capa que esta lectura no ha contrastado». Debajo: «Queda por comprobar la configuración global de seguridad y las condiciones de acceso a la API». -->

### 2.1. Aplicación, tecnologías e integraciones

#### Q04 · ¿Cuál es el lenguaje principal de la aplicación y qué otros lenguajes utiliza?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q05 · ¿Qué tecnologías y frameworks principales utiliza, qué versiones tienen y para qué sirve cada uno?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q06 · ¿A qué servicios externos se conecta y para qué utiliza cada uno? Incluye servicios de inteligencia artificial y gateways de acceso a modelos.

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q07 · ¿Qué contiene este repositorio: frontend, backend, ambos u otro tipo de aplicación? ¿Para qué sirve cada parte?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

### 2.2. Arquitectura y organización del código

#### Q08 · ¿Funciona como una sola aplicación o está dividida en servicios? ¿Cómo se conectan sus partes principales?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q09 · ¿Cómo organiza el código y sus responsabilidades? ¿Sigue alguna arquitectura o mezcla varias? Explica brevemente con ejemplos.

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

### 2.3. Datos, persistencia y recuperación

#### Q10 · ¿Qué bases de datos, archivos u otros almacenes utiliza? ¿Dónde están, qué información guardan y cuáles hay que conservar al migrar?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q11 · ¿Utiliza caché? ¿Qué guarda, durante cuánto tiempo y cómo protege los datos sensibles? Contrasta la protección con Seguridad.

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q12 · ¿Qué datos se conservan al reiniciar la aplicación y cuáles se pierden?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q13 · ¿Existe un sistema de copias de seguridad? ¿Qué guarda y cómo se recuperan los datos?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

### 2.4. Construcción, arranque y despliegue

#### Q15 · ¿Cómo se construye y se arranca la aplicación? Identifica los comandos y scripts necesarios.

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q16 · ¿Qué necesita para arrancar, como variables de configuración, bases de datos u otros servicios?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q17 · ¿Está preparada para ejecutarse con Docker o Docker Compose? ¿Qué partes se ejecutan en contenedores?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q18 · ¿Tiene procesos automáticos de integración y despliegue (CI/CD)? ¿Qué construyen, comprueban o despliegan?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q19 · ¿Los datos se conservan si se elimina o se vuelve a crear el contenedor? ¿Qué hay que configurar para conservarlos?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q20 · ¿Qué conexiones externas hay que configurar para que funcione en nuestro entorno?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q21 · ¿Está preparada para funcionar en local, en una red interna o en Internet? ¿Hay información sobre dónde está desplegada y en qué país?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q22 · ¿Qué partes pueden consumir más memoria, CPU o disco? ¿Hay límites configurados y qué habría que medir para conocer el consumo real?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

### 2.5. Seguridad y privacidad

#### Q14 · ¿Qué datos personales guarda? ¿Permite consultarlos, corregirlos y eliminarlos? ¿Define cuánto tiempo los conserva?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q23 · ¿Tiene un sistema de autenticación? Si existe, sigue el recorrido de una petición y explica cómo comprueba la identidad y si algún acceso sensible queda sin proteger.

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q24 · ¿Comprueba qué puede ver y hacer cada usuario? ¿Podría alguien acceder a datos de otros usuarios o realizar acciones sin permiso?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q25 · ¿Cómo mantiene la sesión del usuario? ¿Cuándo caduca y cómo se invalida al cerrar sesión?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q26 · ¿Dónde y cómo guarda las contraseñas de los usuarios y los tokens de sesión? ¿Están protegidos?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q27 · ¿Limita los intentos de inicio de sesión para evitar que alguien pruebe muchas contraseñas?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q28 · ¿El frontend guarda o lee información sensible en las cookies? ¿La expone o la comparte con terceros?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q29 · ¿El frontend muestra datos que podrían ejecutar código malicioso en el navegador (XSS)?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q30 · ¿Expone claves, contraseñas o API keys privadas en el código o los archivos que recibe el navegador?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q31 · ¿Utiliza cookies que necesitan consentimiento? Si las utiliza, ¿permite aceptarlas, rechazarlas y cambiar la elección? ¿Las bloquea hasta obtener permiso?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q32 · ¿El servidor genera páginas o contenido que podrían ejecutar código malicioso en el navegador (XSS)?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q33 · ¿Guarda información sensible en las cookies? ¿Cómo las protege para evitar su exposición?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q34 · ¿Alguien podría manipular los datos que envía para alterar las consultas a la base de datos (inyección SQL)?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q35 · ¿Hay operaciones que puedan quedarse bloqueadas, repetirse sin límite o agotar los recursos? Incluye lo que ocurre si un servicio externo falla o tarda en responder. ¿Qué controles existen?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q36 · ¿Dónde guarda las claves y contraseñas que utiliza para conectarse a bases de datos o servicios externos? ¿Hay secretos escritos en el código o incluidos en archivos del repositorio, como los .env?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q37 · ¿Qué información envía a servicios externos? ¿Incluye datos sensibles y cómo los protege? Incluye la protección de datos sensibles en caché.

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

### 2.6. Prioridades, alcance y puntos sin comprobar

#### Q01 · ¿Cuáles son las conclusiones y los problemas más importantes de los análisis solicitados?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q02 · ¿Qué habría que resolver antes de desplegar y qué puede dejarse para después?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q03 · ¿Qué puntos quedan sin comprobar o tienen conclusiones contradictorias?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q38 · Para cada problema señalado: ¿está sustentado por el código o hay alguna protección que lo evita?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q39 · Para cada problema señalado: ¿qué condiciones necesita para ocurrir y qué impacto tendría?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

#### Q40 · Para cada problema señalado: ¿qué se ha comprobado y qué falta para confirmarlo o descartarlo?

[Respuesta ejecutiva y clara para el cliente. Si no aplica, justifícalo. Si no se puede determinar con exactitud, explica los indicios encontrados o indícalo claramente si no hay información.]

<details>
<summary>Fuentes consultadas</summary>

- [Archivo y líneas del commit revisado.]
- [Resultados deterministas relacionados: D01–D05, cuando corresponda.]

</details>

## 3. Anexos deterministas

[Identificar el repositorio y commit a los que corresponden estos resultados. Explicar los resultados de cada herramienta, sus alertas, cobertura, errores y omisiones en lenguaje natural. No insertar código, JSON ni salidas técnicas en el informe; conservar los originales como evidencia interna. Ocultar los valores de posibles secretos. Diferenciar «sin detecciones» de «no evaluado».]

### D01 · Adquisición e inventario del snapshot

**Versión o motor:** [Extraer la versión del JSON]

**Resultado de la ejecución:** [Traducir el estado, ej: completada con 186 archivos inventariados]

**Entrada y alcance:** [Explicar en un párrafo legible qué se escaneó, por ejemplo: Se adquirieron [total] archivos: [cantidad] de texto y [cantidad] binarios. Indicar si hubo errores de adquisición.]

**Resultados:** [Resumen claro: Se identificaron archivos clave de entorno como `.env` y `.env.production`, los cuales están marcados para revisión debido a su naturaleza sensible.]

**Cobertura, omisiones e incidencias:** [Indicar de forma sencilla qué se pudo leer y qué no, ej: Los analizadores estáticos omitieron archivos de configuración por falta de soporte nativo.]

**Límites de interpretación:** [Explicar qué significa esto para el cliente, ej: El inventario confirma la estructura de archivos, pero no valida el contenido ni la seguridad de los mismos por sí solo.]


### D02 · Gitleaks

**Versión o motor:** [Extraer versión de Gitleaks, ej: 8.30.1]

**Resultado de la ejecución:** [Traducir el estado, ej: completada con detecciones pendientes de validar]

**Entrada y alcance:** [Explicar en un párrafo legible qué se revisó en busca de secretos, ej: Se revisaron los archivos del commit capturado, incluidos los archivos de configuración versionados, con las reglas de detección de credenciales. El análisis actual no incluye el historial Git.]

**Resultados:** [Resumen claro: Indicar si se encontraron posibles credenciales o claves expuestas, especificando el tipo de secreto detectado sin revelar valores sensibles.]

**Cobertura, omisiones e incidencias:** [Indicar de forma sencilla qué archivos o rutas quedaron fuera del escaneo de secretos por exclusiones o incompatibilidades.]

**Límites de interpretación:** [Explicar qué significa para el cliente, ej: La ausencia de alertas no garantiza al 100% que no existan credenciales ofuscadas o de diseño personalizado que las reglas no reconocieran.]


### D03 · OSV-Scanner

**Versión o motor:** [Extraer la versión de OSV-Scanner, ej: 2.7.0]

**Resultado de la ejecución:** [Traducir el estado, ej: completada con dependencias analizadas]

**Entrada y alcance:** [Explicar en un párrafo legible qué se evaluó, ej: Se analizaron los archivos de dependencias y bloqueos (como package-lock.json o requirements.txt) contrastándolos con bases de datos de vulnerabilidades conocidas.]

**Resultados:** [Resumen claro: Describir si se detectaron librerías o paquetes afectados por vulnerabilidades conocidas, con sus identificadores CVE, GHSA u otros. Indicar gravedad solo cuando esté respaldada por los resultados; si no consta, explicarlo sin inferirla por el número de coincidencias.]

**Cobertura, omisiones e incidencias:** [Indicar de forma sencilla qué paquetes o archivos no pudieron ser evaluados por falta de metadatos o por no ser compatibles con el escáner.]

**Límites de interpretación:** [Explicar qué significa para el cliente, ej: El escaneo evalúa únicamente vulnerabilidades públicas registradas en dependencias de terceros, pero no analiza posibles fallos lógicos en el código propio.]


### D04 · Semgrep

**Versión o motor:** [Extraer versión de Semgrep, ej: 1.182.1]

**Resultado de la ejecución:** [Traducir el estado, ej: completada sin detecciones en la selección / con hallazgos]

**Entrada y alcance:** [Explicar en un párrafo legible qué se analizó, ej: Se ejecutó el análisis estático de código fuente utilizando conjuntos de reglas orientadas a la detección de vulnerabilidades de seguridad y malas prácticas.]

**Resultados:** [Resumen claro: Describir las incidencias de código o patrones de riesgo encontrados por el motor de análisis estático, señalando las áreas más afectadas.]

**Cobertura, omisiones e incidencias:** [Indicar de forma sencilla qué lenguajes o archivos no fueron procesados por limitaciones de los parsers o exclusiones de reglas.]

**Límites de interpretación:** [Explicar qué significa para el cliente, ej: Las alertas son indicios estáticos que requieren validación manual para descartar falsos positivos o comprobar si existe mitigación en otra capa.]


### D05 · Graphify

**Versión o motor:** [Extraer versión o estado del motor estructural]

**Resultado de la ejecución:** [Traducir el estado, ej: completado parcialmente / mapa estructural generado]

**Entrada y alcance:** [Explicar en un párrafo legible qué se estructuró, ej: Se procesó el código fuente para mapear las relaciones, dependencias y nodos de interacción entre los diferentes módulos y archivos del proyecto.]

**Resultados:** [Resumen claro: Describir la estructura registrada: archivos representados, nodos, relaciones y relaciones no resueltas. No afirmar acoplamiento excesivo ni dependencias circulares sin una comprobación específica que los respalde.]

**Cobertura, omisiones e incidencias:** [Indicar de forma sencilla qué relaciones no pudieron resolverse o qué componentes quedaron aislados en el mapa.]

**Límites de interpretación:** [Explicar qué significa para el cliente, ej: El mapa es una ayuda visual y estática para comprender la complejidad del código, pero no evalúa el comportamiento en tiempo de ejecución.]


---

<!-- Notas de edición: escribe aquí los cambios generales que quieras trasladar después al informe HTML. -->
