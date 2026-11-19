# Seguridad del servidor y los datos

## Preguntas

### Q14 · ¿Qué datos personales guarda? ¿Permite consultarlos, corregirlos y eliminarlos? ¿Define cuánto tiempo los conserva?

### Q32 · ¿El servidor genera páginas o contenido que podrían ejecutar código malicioso en el navegador (XSS)?

### Q33 · ¿Guarda información sensible en las cookies? ¿Cómo las protege para evitar su exposición?

### Q34 · ¿Alguien podría manipular los datos que envía para alterar las consultas a la base de datos (inyección SQL)?

### Q35 · ¿Hay operaciones que puedan quedarse bloqueadas, repetirse sin límite o agotar los recursos? Incluye lo que ocurre si un servicio externo falla o tarda en responder. ¿Qué controles existen?

### Q36 · ¿Dónde guarda las claves y contraseñas que utiliza para conectarse a bases de datos o servicios externos? ¿Hay secretos escritos en el código o incluidos en archivos del repositorio, como los .env?

### Q37 · ¿Qué información envía a servicios externos? ¿Incluye datos sensibles y cómo los protege? Incluye la protección de datos sensibles en caché.

## Evidencia

### Primera ronda

- Dedica al menos dos consultas a ubicar código de aplicación. Elige un flujo que reciba archivos o datos personales y otro que consulte la base o dispare una operación costosa. Usa símbolos o rutas concretas, una búsqueda por concepto.
- Usa los escáneres pertinentes para elegir pistas verificables. Agrupa varias herramientas en la ronda cuando sus resultados puedan orientar lecturas concretas. Filtra alertas por ruta o regla.

### Segunda ronda

Lee las implementaciones que confirmen o descarten las pistas. Para archivos y datos personales, sigue la validación y las escrituras, comprueba qué sucede si una falla y rastrea el borrado o la entrega a terceros. Comprueba los controles según el flujo. Para una dependencia señalada, contrasta la versión y su uso. Si lees un candidato a secreto, clasifícalo por el uso de la constante o el valor en el código y explica qué queda pendiente sin revelar su contenido.

Usa la segunda ronda para conectar una pista con su consumidor. Si encuentras un resultado de validación o análisis, lee dónde se comprueba ese resultado antes de guardar, enviar o publicar. Aprovecha el índice de fuentes previas para recuperar los tramos pertinentes.

Para cada aviso de D03 investigado conserva paquete/versión, uso runtime/desarrollo, consumidor, plataforma, condición, protección, decisión, prioridad, corrección y comprobación. Usa `dependencias` según el contrato activo. Confirma o descarta solo con evidencia del uso o configuración; el resumen del escáner no basta. Lo no investigado queda pendiente. No confundas una versión corregida de otra rama con una actualización universal.

## Cierre

Entrega en `observaciones` los riesgos que encuentres, con tipo, gravedad justificada, condiciones, efecto y citas del recorrido. Si la implementación muestra una operación costosa accesible y falta comprobar un límite de infraestructura, registra la condición pendiente como parte del indicio. Conserva las protecciones que sí veas. Explica qué archivo, operación o defensa concreta queda pendiente cuando la evidencia no permita cerrar.
