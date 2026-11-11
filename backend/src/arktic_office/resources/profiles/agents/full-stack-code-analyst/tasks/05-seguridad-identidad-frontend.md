# Seguridad de identidad y navegador

## Preguntas

### Q23 · ¿Tiene un sistema de autenticación? Si existe, sigue el recorrido de una petición y explica cómo comprueba la identidad y si algún acceso sensible queda sin proteger.

### Q24 · ¿Comprueba qué puede ver y hacer cada usuario? ¿Podría alguien acceder a datos de otros usuarios o realizar acciones sin permiso?

### Q25 · ¿Cómo mantiene la sesión del usuario? ¿Cuándo caduca y cómo se invalida al cerrar sesión?

### Q26 · ¿Dónde y cómo guarda las contraseñas de los usuarios y los tokens de sesión? ¿Están protegidos?

### Q27 · ¿Limita los intentos de inicio de sesión para evitar que alguien pruebe muchas contraseñas?

### Q28 · ¿El frontend guarda o lee información sensible en las cookies? ¿La expone o la comparte con terceros?

### Q29 · ¿El frontend muestra datos que podrían ejecutar código malicioso en el navegador (XSS)?

### Q30 · ¿Expone claves, contraseñas o API keys privadas en el código o los archivos que recibe el navegador?

### Q31 · ¿Utiliza cookies que necesitan consentimiento? Si las utiliza, ¿permite aceptarlas, rechazarlas y cambiar la elección? ¿Las bloquea hasta obtener permiso?

## Evidencia

### Primera ronda

- Ubica la implementación de login y sesión, los procedimientos de autorización y al menos una operación sensible que los usa.
- Busca el recorrido de contenido editable hasta su renderizado, los límites entre código cliente y servidor y la carga de scripts o cookies. Localiza la política de scripts y comprueba qué configuración la aplica. Consulta el índice D04 si ayuda a elegir un flujo concreto.

### Segunda ronda

Sigue las llamadas hasta la comprobación efectiva. Contrasta los controles por rol y por registro y verifica si el contenido puede llegar al navegador con HTML interpretable. Prioriza una pista concreta con impacto frente a una lectura repetida del mismo archivo.

Si el índice de fuentes previas ya apunta al consumidor o a su defensa, recupera solo las líneas necesarias para cerrar ese recorrido.

## Cierre

Documenta en `observaciones` los riesgos respaldados por las fuentes, aunque su explotación dependa de condiciones. Por ejemplo, si una ruta sensible busca un registro por ID proporcionado por el cliente y omite verificar su propietario, cita la ruta y la consulta, describe el acceso posible y señala si falta comprobar un filtro anterior. Usa `certeza: indicio` cuando el patrón esté visible y quede una defensa relevante por verificar. Si solo localizaste una protección, delimita su alcance. Deja pendientes concretos para los flujos sin contrastar.

Para una vulnerabilidad, indica el tipo y la gravedad cuando puedas justificarla con el impacto y las condiciones observadas.
