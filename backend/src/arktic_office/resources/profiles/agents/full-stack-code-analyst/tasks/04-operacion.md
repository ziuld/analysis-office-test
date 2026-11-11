# Operación

## Preguntas

### Q15 · ¿Cómo se construye y se arranca la aplicación? Identifica los comandos y scripts necesarios.

### Q16 · ¿Qué necesita para arrancar, como variables de configuración, bases de datos u otros servicios?

### Q17 · ¿Está preparada para ejecutarse con Docker o Docker Compose? ¿Qué partes se ejecutan en contenedores?

### Q18 · ¿Tiene procesos automáticos de integración y despliegue (CI/CD)? ¿Qué construyen, comprueban o despliegan?

### Q19 · ¿Los datos se conservan si se elimina o se vuelve a crear el contenedor? ¿Qué hay que configurar para conservarlos?

### Q20 · ¿Qué conexiones externas hay que configurar para que funcione en nuestro entorno?

### Q21 · ¿Está preparada para funcionar en local, en una red interna o en Internet? ¿Hay información sobre dónde está desplegada y en qué país?

### Q22 · ¿Qué partes pueden consumir más memoria, CPU o disco? ¿Hay límites configurados y qué habría que medir para conocer el consumo real?

## Evidencia

Sigue los scripts de arranque y construcción hasta los servicios que activan. Consulta los Dockerfiles y el pipeline para distinguir lo que se ejecuta de lo que el repositorio solo documenta. Separa los límites configurados de las mediciones pendientes.

## Cierre

Contrasta scripts y configuración de construcción, arranque, entrega y persistencia. Distingue los recursos declarados de los que habría que medir en ejecución.
