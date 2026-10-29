# Estándar de comunicación de informes · Arktic Office

Versión editorial 1, basada en la referencia visual v12 aprobada. Este documento es la fuente única de reglas de redacción. `auditor/editorial.py` carga Común y la sección de cada célula en sus instrucciones, sin llamadas adicionales. La consolidación y el renderizado aplican Consolidación. Los perfiles técnicos conservan los criterios de análisis y los contratos JSON, no copias de estas reglas.

## Común

El hilo del informe es: entender la aplicación → conocer los hallazgos y su impacto → responder las preguntas por temas → consultar los resultados deterministas. La decisión corresponde al equipo responsable.

Redacción ejecutiva y comprensible para un cliente o director de tecnología, sin coletillas de IA, lenguaje promocional ni frases vacías. Expresar la conclusión y su consecuencia con términos concretos; explicar el vocabulario técnico necesario. No repetir fórmulas genéricas de respaldo o insuficiencia. Los títulos de riesgos deben ser completos, breves y comprensibles, nunca fragmentos cortados de una observación. En la presentación actual se muestran como máximo diez riesgos, con código y nombre, círculos de gravedad y una leyenda accesible. No se solicita un bloque de impacto y deuda técnica. «Pendientes de validar» se limita a omisiones concretas documentadas de lectura o cobertura; si no existen, se omite. Un resultado desconocido, una cita rechazada o una prueba en vivo pendiente no demuestran que no se revisó el código.

La lectura insuficiente es un resultado normal: explica qué no puedes determinar y qué evidencia falta; conserva las aportaciones respaldadas y omite los bloques sin contenido útil. Una hipótesis del propósito necesita fuentes y se identifica como indicio; sin pistas, pide una lectura más profunda. No repitas «no encontrado» por cada apartado.

Escribe en español directo, con frases concretas. El primer nivel debe poder leerse sin conocimientos de implementación; explica el término técnico cuando sea necesario. No atribuyas autoría, departamento, propósito, usuarios ni contexto que no respalden los archivos. No repitas componentes y versiones en cada sección.

Separa hechos observados, indicios, dudas y recomendaciones. Una fuente válida respalda el texto leído, no demuestra explotación, acceso efectivo ni funcionamiento. No deduzcas ausencia de controles por falta de documentación. No inventes mediciones, pruebas, permisos, exposición pública, recuperaciones, compatibilidad ni cumplimiento. Cero hallazgos no prueba seguridad. No repitas una advertencia genérica en cada bloque: conserva la condición concreta y el límite que afectan a la conclusión.

Cada riesgo debe expresar qué encontramos, qué podría pasar, bajo qué condiciones, qué cambiar y cómo comprobarlo. `titulo` nombra la consecuencia de forma comprensible (máximo 110 caracteres), sin afirmar que ya ocurrió. `observacion`, `importancia`, `condiciones`, `accion` y `pendiente` sostienen esas cinco ideas. `resultado_esperado` es un objetivo propuesto por verificar (máximo 300 caracteres), no un control implantado. `detalle_tecnico` reserva la terminología precisa para un segundo nivel (máximo 600 caracteres). Mantén fuentes y limitaciones al simplificar.

Claro: «Una búsqueda manipulada podría mostrar datos de otras personas; depende de los permisos de la cuenta de base de datos».
Confuso: «SQLi crítica explotable; la app no tiene gobernanza» sin demostrar acceso ni explicar la consecuencia.

## Seguridad

Diagnóstico y riesgos: títulos por consecuencia, gravedad separada de certeza. Explica el patrón leído y el impacto condicionado; no conviertas un indicio grave en vulnerabilidad confirmada. No inventes puntuaciones o porcentajes. El detalle técnico conserva el mecanismo y las referencias, sin valores secretos.

Controles y mejoras: organiza por los seis dominios del perfil OWASP de Arktic. Por cada riesgo, relaciona el problema con `accion`, `resultado_esperado` y `pendiente`. Si un dominio no se evaluó, indica qué evidencia falta; no inventes un hallazgo para rellenarlo. Una evidencia favorable es limitada al alcance leído. No equivale a cumplimiento completo ni certificación.

Claro: «Lectura o borrado sin permiso»; acción «Comprobar identidad y permiso en el servidor»; objetivo «Cada persona actúa solo sobre los datos autorizados»; aceptación «Probar cuentas con permisos distintos y solicitudes sin permiso».
Confuso: «Implementar IAM robusto» sin explicar qué problema resuelve ni cómo aceptarlo.

## Arquitectura

Flujo actual: aporta `presentacion.flujo_actual` con componentes y conexiones identificables. Cada componente tiene fuentes. Cada conexión declara `observada`, `inferida` o `desconocida`; las observadas e inferidas llevan fuentes y las inferidas explican la condición. No completes una cadena por intuición. Si faltan conexiones, muestra nodos sin conectarlos y plantea la duda.

Base de datos y recuperación: aporta `presentacion.estado_operativo`, una fila por aspecto: motor, ubicacion, acceso, cuentas, copias, recuperacion, disponibilidad y capacidad. Incluye estado, descripción, pendiente y fuentes para observados/indicios; `no_evaluado` puede no citar. Persistencia no es copia; configurar no es demostrar funcionamiento; disponibilidad y capacidad son aspectos distintos.

Azure: una opción sencilla con objetivo, función de servicios, supuestos y pendientes. En servicios, `categoria` separa ejecucion, datos, entrega, monitorizacion y acceso. Las conexiones propuestas se declaran explícitamente entre índices de servicios (empezando en 1), nunca se deducen de nombres. Distingue infraestructura propuesta de existente. No inventes capacidad, costes, compatibilidad ni disponibilidad corporativa. El flujo de entrega explica preparación, pruebas, aprobación y vuelta atrás; los cambios de datos requieren su propio plan.

Decisión: en `presentacion.decision`, expresa `propuesta`, `evidencia_pendiente` y `siguiente_paso`; recomendar no autoriza el despliegue. Si faltan bases, pide la información concreta en lugar de fabricar una recomendación completa.

Claro: «Evaluar una aplicación gestionada y conservar el motor de datos; confirmar compatibilidad y probar restauración antes de habilitar usuarios».
Confuso: «Migrar a AKS; solución escalable y segura» sin necesidad, mediciones ni pruebas.

## Inventario

Resumen: aporta `presentacion.resumen` con `descripcion`, `tecnologia_principal` y `evidencia`. Describe en una frase qué es y qué hace; añade solo la tecnología principal respaldada, sin enumerar frameworks ni atribuir su origen. Si no hay propósito documentado, dilo.

Inventario: cada componente declara nombre, tecnología y versión cuando está escrita, función y fuentes. Mantén esta tabla factual: no incluyas aquí recomendaciones ni evaluaciones de seguridad. Una versión declarada no prueba la versión en ejecución. No completes versiones por conocimiento previo.

Claro: «Aplicación de gestión de reservas desarrollada en Java»; tabla «API · Spring Boot 2.5.5 declarado · Procesar reservas · build.gradle:2».
Confuso: «App del director creada con IA; stack moderno listo para Azure» cuando los archivos solo muestran dependencias.

## Consolidación

Organiza aportaciones válidas con reglas estructurales; no traduzcas conclusiones mediante sustituciones de palabras del ejemplo. No combines observaciones diferentes para fabricar un riesgo nuevo. No ocultes contradicciones de certeza, versiones, descripción o propuestas. Conserva aportación original, célula y fuentes en el segundo nivel.

La primera vista contiene resumen, flujo disponible, prioridades y vínculos; los anexos conservan todos los riesgos. Enlaza explicación, mejora y fuentes mediante identificadores estables y permite volver al contexto. Gravedad usa color y texto; certeza usa una etiqueta independiente. Las flechas distinguen conexión observada, inferida y desconocida. Azure debe estar rotulado como propuesta.

Cuando falta un dato, escribe la carencia concreta. No conviertas automáticamente un resultado antiguo en datos del esquema nuevo. Un reformateo se identifica como derivado y conserva el original. Los fallos de células y scanners, la selección parcial, los datos no evaluados y las variantes de componentes siguen visibles.

Claro: «Conexiones no estructuradas en este resultado; consultar las observaciones y fuentes guardadas».
Confuso: dibujar web → API → base a partir de tres tecnologías mencionadas sin evidencia de sus comunicaciones.

## Aplicación por sección

La falta de información es un resultado normal: devolver `evaluacion` con `estado: informacion_insuficiente`, un motivo concreto y `necesita` con hasta seis datos o archivos necesarios. Conservar las aportaciones respaldadas. Una hipótesis del propósito requiere fuentes y debe identificarse como indicio; sin pistas, explicar que hace falta una lectura más profunda. No rellenar bloques sin contenido útil para completar la plantilla. El reporte reúne las carencias en «Resultado y siguiente paso» y omite los apartados vacíos, sin eliminar resultados originales ni ocultar fallos técnicos.

La ausencia de README no impide analizar código, rutas, dependencias o configuración. El resumen puede describir operaciones concretas evidenciadas en esas fuentes sin atribuir a toda la aplicación un propósito que no esté respaldado. Una lectura insuficiente se declara como límite de la revisión, no como defecto demostrado del proyecto. Los resultados de Seguridad incluyen sus controles evaluados y pendientes aunque no encuentre riesgos clasificables.

| Sección | Origen y marco de redacción |
|---|---|
| Resumen del informe | Inventario: qué es, qué hace y tecnología principal; sin procedencia no sustentada |
| Flujo actual | Arquitectura: componentes, conexiones y grado de certeza; huecos explícitos |
| Diagnóstico y riesgos | Seguridad y Arquitectura: patrón, consecuencia y condición |
| Base de datos y recuperación | Arquitectura: aspecto, estado identificado, pendiente y fuente |
| Inventario | Inventario: componente, tecnología/versión declarada, función y fuente |
| Controles y mejoras | Dominios de Seguridad: problema, acción, objetivo por verificar y aceptación |
| Arquitectura Azure | Arquitectura: objetivo, diagrama propuesto, servicios y supuestos |
| Decisión y siguientes pasos | Arquitectura: qué se propone decidir, qué falta y próximo paso |
| Anexos | Consolidación: explicación completa, mecanismo técnico desplegable, originales y fuentes |

La validación local comprueba estructura y trazabilidad; la claridad y calidad de futuras respuestas reales deberán validarse en una ejecución autorizada. No hay agente traductor ni llamadas extra para aplicar este estándar.
