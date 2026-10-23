# Propuesta DevOps Azure · versión 1

Además de tus hallazgos, devuelve propuesta_azure en la raíz del JSON. Es una
recomendación preliminar para el arquitecto humano, nunca un hecho del repositorio
ni una autorización de despliegue. No cambies ni minimices riesgos para justificarla.
No ejecutes comandos, no generes infraestructura ni YAML y no añadas otra llamada.

Elige UNA opción sencilla y explica por qué encaja en los archivos leídos:
- app_service: considerar primero para una web/API convencional, con código o contenedor.
- container_apps: considerar si hay contenedores/servicios o trabajo en segundo plano
  que lo justifiquen, sin necesidad demostrada de gestionar Kubernetes.
- aks_existente: solo como hipótesis explícita de plataforma corporativa ya disponible
  y mantenida; no afirmes que existe. No propongas crear un clúster para una API pequeña.
- virtual_machine: solo si hay una dependencia concreta de sistema operativo o de
  instalación que haga poco práctica la opción gestionada; explica carga de mantenimiento.
- por_definir: si no identificas arranque y componentes suficientes; indica qué falta.

Proponer no exige certeza sobre el entorno futuro: declara supuestos. Las fuentes
respaldan el stack/arranque/datos que motivan la elección, no la compatibilidad Azure.
No presupongas Docker, pipeline, presupuesto, suscripción, red corporativa, tráfico,
versión soportada ni plataforma existente. Si falta Dockerfile, empaquetarlo es un
paso propuesto, no un archivo existente. No migres de motor de BD por comodidad.
Para base de datos, considera servicio gestionado del MISMO motor si se identifica;
compatibilidad, migración, permisos, copia y restauración siguen por verificar.
Para datos/archivos locales, explica persistencia fuera del contenedor y el pendiente.

Máximo cinco servicios, solo los necesarios; reutilizar servicios corporativos se
plantea como supuesto. Nada de microservicios, service mesh, multirregión, API Management,
clúster nuevo, WAF dedicado o red avanzada por defecto. Si se necesitan por política
o por riesgo, dejarlos como validación. No inventes precios, SKU, CPU/RAM, plazos ni SLA.
Proponer autenticación/autorización, secretos fuera del código, acceso restringido a
datos y HTTPS según los límites observados; no confundir HTTPS con autorización.

El flujo DevOps será breve: repositorio -> Azure Pipelines -> compilación y pruebas
disponibles o smoke test propuesto -> artefacto versionado (ACR solo con contenedor)
-> entorno de prueba -> aprobación humana -> despliegue y comprobación de salud.
Incluir vuelta al artefacto anterior y tratar cambios de BD aparte con copia verificada;
revertir el contenedor no garantiza revertir el esquema. Secretos fuera de la imagen,
conexiones de servicio con permisos mínimos, registros y una alerta básica.
No afirmes que estas pruebas, controles o pipelines ya existen si no los has leído.

Contrato adicional (valores cortos, sin listas anidadas):
"propuesta_azure": {
  "estado": "propuesta_preliminar",
  "destino": "app_service",
  "resumen": "Una propuesta concreta de cómo alojar esta aplicación.",
  "justificacion": "Por qué encaja con el stack observado y evita complejidad innecesaria.",
  "evidencia": ["F1:L7"],
  "supuestos": ["Hasta tres hipótesis explícitas sobre lo no conocido."],
  "servicios": [{"servicio": "Azure App Service", "uso": "Función propuesta, no infraestructura detectada."}],
  "pasos": ["Hasta cinco pasos que cubran preparación, CI/CD, datos, comprobación y reversión."],
  "pendientes": ["Hasta cuatro validaciones concretas antes de aceptar la propuesta."]
}
resumen y justificacion hasta 450 caracteres; elementos de listas hasta 260;
servicio/uso hasta 200. Para informacion_insuficiente usa destino por_definir,
servicios [] y pasos [], explica carencias en resumen/justificacion/pendientes.

Guía de servicios contrastada el 22/10/2026 (no es consulta en tiempo real del agente):
https://learn.microsoft.com/en-us/azure/container-apps/compare-options
https://learn.microsoft.com/en-us/azure/devops/pipelines/ecosystems/containers/acr-template?view=azure-devops
Verificar de nuevo versiones soportadas, disponibilidad y política de la empresa antes
de implementar. Esta guía da criterios, no una arquitectura obligatoria.

La comunicación de objetivo, servicios, supuestos, decisión y pendientes sigue la sección Arquitectura del estándar editorial compartido, cargada en el mismo prompt.
Para el diagrama, cada servicio puede añadir categoria: ejecucion/datos/entrega/monitorizacion/acceso.
Añade conexiones solo cuando las propongas explícitamente: [{"origen":1,"destino":2,"descripcion":"Conexión propuesta y condiciones"}].
Los índices se refieren al orden de servicios y empiezan en 1. Máximo ocho conexiones. No deducirlas durante el renderizado.
