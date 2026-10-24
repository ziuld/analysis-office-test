Formato 3: añade a CADA hallazgo severidad (critica/alta/media/baja/informativa),
control (acceso/entradas/secretos/dependencias/configuracion/operacion/contexto), accion y condiciones.
Usa contexto + informativa para propósito, componentes y hechos sin riesgo demostrado.
Añade controles a la raíz del JSON. Seguridad debe devolver los seis controles; otras células []:
[{"id":"acceso","estado":"no_evaluado","motivo":"Falta contexto de autorización","evidencia":[]}].
Los estados evaluados requieren referencias F1:L7 igual que los hallazgos.
No incluyas hallazgos sin evidencia. Los archivos partial=true contienen extractos con numeración original.
Analiza código, rutas, dependencias y configuración aunque no haya README. El README es contexto complementario, no un requisito.
Describe operaciones y componentes respaldados por esas fuentes; no confundas una declaración con su funcionamiento verificado.
Si la lectura es insuficiente, devuelve JSON válido con evaluacion: {"estado":"informacion_insuficiente","motivo":"Qué no puedes determinar con esta lectura","necesita":["Código o configuración concreta que falta"]}.
Conserva cualquier hallazgo respaldado; no rellenes secciones, no inventes riesgos ni devuelvas un error por falta de información.
Si existe una pista del propósito, exprésala como indicio con fuentes y condiciones; si no hay pistas, explica que hace falta una lectura más profunda.
Omite bloques de presentacion sin contenido útil. Para Azure sin base suficiente usa informacion_insuficiente y por_definir según su contrato.
