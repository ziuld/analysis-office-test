# Reporte de seguridad · formato 3

El formato visual y editorial actual sigue la referencia v12: cuatro capítulos (resumen, diagnóstico, mejoras y anexos). La fuente única de redacción es [ESTANDAR_COMUNICACION_INFORMES.md](ESTANDAR_COMUNICACION_INFORMES.md), cargada explícitamente por cada célula y por las consultas. La consolidación guarda la versión y el hash del estándar utilizado, sin una llamada adicional.

Los campos opcionales `titulo`, `resultado_esperado`, `detalle_tecnico` y `presentacion` permiten redactar desde origen, estructurar conexiones y separar estado de datos, disponibilidad y capacidad. Los resultados antiguos siguen siendo legibles: sus huecos se muestran como no estructurados y no se rellenan por inferencia. Las variantes de componentes y aportaciones discrepantes se conservan en anexos. Los resultados esperados son objetivos por verificar.

`auditor/report_view.py` produce HTML y Markdown a partir de los mismos registros. Los recursos visuales en `auditor/assets/` se extrajeron de la referencia aprobada, que se conserva intacta. La muestra independiente es `artifacts/informe-arktic-v12-muestra.html`. El ejemplo anterior se conserva; el nuevo se guarda en `reports/demo-editorial-v12-portal-personal/`.

El reporte comienza por propósito, construcción y datos; después muestra riesgos por gravedad, controles pendientes, detecciones automáticas, inventario y cobertura. Cada riesgo incluye impacto, condiciones, acción propuesta y fuentes al commit. La oficina permite filtrar riesgos e imprimir el reporte completo o guardarlo como PDF desde el navegador. Markdown sigue disponible para descarga. Los informes anteriores se conservan en su formato original.

## Interpretación

`informacion_insuficiente` es un estado terminal normal de célula o revisión, con `mensaje` y `necesita` disponibles en la API. La oficina lo muestra con explicación y sin personaje rojo ni estado de trabajo permanente. Si hay aportaciones válidas junto con limitaciones, el resultado es parcial. Los errores de sesión, conexión o validación de evidencias siguen siendo errores técnicos y no se convierten en falta de información.

HTML y Markdown omiten flujo, inventario, datos, Azure, mejoras o decisiones que no tengan contenido útil. Las limitaciones se reúnen en el resumen y las necesidades para avanzar; los datos y estados originales permanecen en JSON. Un resultado sin aportaciones explica que no permite elaborar una evaluación técnica útil y qué lectura adicional hace falta, sin llenar la plantilla con huecos. Los informes históricos no se modifican automáticamente.

| Indicador | Significado |
|---|---|
| 🔴 Crítica / alta | Impacto grave según la evidencia y las condiciones descritas |
| 🟡 Media | Riesgo acotado o condicionado |
| 🔵 Baja / informativa | Impacto menor o contexto sin riesgo demostrado |
| ⚪ No evaluado | Falta evidencia o una comprobación |

La severidad es una valoración del agente, independiente de la certeza. «Confirmado en código» significa patrón observado, no explotación demostrada. Los indicios se cuentan por separado. Cero hallazgos nunca significa aplicación segura; completar las células tampoco demuestra cobertura total.

## Lectura y coste

- Global: 24 archivos / 120000 bytes de texto por defecto, ajustable hasta 40 / 200000. Descarga máxima independiente: 256 KB por archivo y 1 MB por revisión. No se clona el repositorio ni se consulta su historial.
- La selección reparte turnos entre manifiestos, despliegue, arranque, datos, rutas, lógica, seguridad, configuración, lockfiles y otras fuentes. El README es complementario; Arquitectura e Inventario también reciben código. Configuración de base de datos y controladores concretos se priorizan frente a modelos genéricos o controladores base. Es una heurística de rutas/nombres, no un grafo de llamadas ni una garantía de cubrir todos los endpoints. Los archivos grandes se reducen a extractos con sus líneas originales; la cobertura lo señala.
- Seguridad: 12 archivos / 64000 bytes; Arquitectura e Inventario: 6 / 24000 cada uno. Los lockfiles completos se destinan a OSV, no al modelo.
- Perfil recomendado en `.env.example`: Seguridad `gpt-6.1-sol` / `medium`; las demás células y el coordinador `gpt-6-luna` / `low`. Las variables vacías heredan el modelo común. La disponibilidad depende de la cuenta; un fallo no dispara cambios ni reintentos automáticos.
- Tres llamadas de revisión; renderizado, ordenación y scanners sin llamadas al modelo. El prompt pide hasta 8 confirmados, 5 indicios y 6 dudas por célula. El validador admite hasta 12/8/8 y rechaza excesos; no recorta silenciosamente riesgos. Con OAuth, 4500 tokens de salida configurados no constituyen un límite duro.

## Perfil de Seguridad

El diagnóstico muestra «Qué pudo evaluar Seguridad» con los seis dominios, sus fuentes y carencias, incluso si no hay riesgos clasificables. Esto permite distinguir evidencia favorable limitada de una comprobación pendiente. Los contadores de riesgos no resumen por sí solos la evaluación.

Si únicamente falla la validación de la propuesta Azure, se valida de forma independiente el resto de Arquitectura y se conserva si es válido. La célula y el equipo quedan parciales, con una advertencia visible y sin reintento. No se publica la propuesta inválida ni se rescatan hallazgos con citas inválidas. Las consultas admiten los resultados válidos de esa célula parcial.

También se valida por separado cada bloque opcional de presentación de Arquitectura. Un diagrama inválido se omite sin descartar los hallazgos, las decisiones u otros bloques que sí superen validación. La advertencia técnica queda en `advertencias` de la célula; la interfaz muestra un mensaje de resultado parcial.

`auditor/profiles/security-v1.md` se carga explícitamente en las instrucciones de Seguridad. Es una guía propia y acotada inspirada en [OWASP ASVS 5.0.0](https://asvs.owasp.org/) y [OWASP Top 10:2025](https://top10.owasp.org/2025/); no es certificación ni cobertura completa de sus requisitos.

Revisa acceso; entradas/inyección/archivos/red; secretos/datos; dependencias; configuración/exposición; errores/registros/continuidad. Cada control indica hallazgo, evidencia favorable limitada, no evaluado o no aplica justificado. Los estados evaluados requieren citas contrastadas. Una cita correcta no valida automáticamente la interpretación del modelo.

## Comprobaciones automáticas

| Herramienta fijada | Alcance y límites |
|---|---|
| Gitleaks 8.30.1 | Posibles secretos en archivos descargados antes de ocultarlos. Solo se guardan regla y localización; no valores ni coincidencias originales. No comprueba si una credencial está activa. |
| OSV-Scanner 2.7.0 | Dependencias de lockfiles admitidos y `requirements.txt`. Sin resolver dependencias transitivas, instalar paquetes ni ejecutar análisis de llamadas. Envía metadatos de paquetes a servicios de consulta de vulnerabilidades. Versiones ausentes/no reconocidas quedan pendientes. |

Las detecciones aparecen separadas de los riesgos del modelo para evitar duplicados. No se les atribuye una severidad inventada. Los fallos y timeouts se muestran como pendientes; nunca como resultado favorable. Los binarios se verifican por SHA-256 al construir la imagen. Los fuentes completos y resultados crudos de los scanners solo existen temporalmente en `/tmp`; se elimina esa carpeta al terminar. No se aceptan configuraciones de scanner del repositorio objetivo.

No se analizan `.env`, claves privadas reconocidas por nombre, archivos excluidos, historial Git ni dependencias no descargadas. La ocultación de secretos tiene límites, incluso con Gitleaks. El código seleccionado y ocultado se envía al proveedor del modelo; esto debe ser compatible con las reglas de datos de la empresa.

Semgrep queda para una ampliación posterior con reglas revisadas para los lenguajes reales. Esta versión no hace pentesting, análisis dinámico, mediciones de carga ni validación de copias/restauración. La decisión de despliegue sigue siendo humana.

## Comprobar cambios

```powershell
docker compose --profile audit build auditor
docker compose --profile audit run --rm -T --entrypoint python auditor -m unittest test_audit test_team test_server test_questions test_brief test_security
docker compose up -d --build --wait
```

Los casos controlados comprueban citas inventadas, certeza/severidad, ausencia de evidencia, secretos ficticios, fallos de scanner, HTML no ejecutable y compatibilidad histórica. Son pruebas del sistema; no miden una tasa general de detección de vulnerabilidades.

Validación del 22/10/2026: 66 pruebas del auditor y 4 de interfaz superadas; revisión real de bookingApi completada con Sol/medium para Seguridad y Luna/low para las otras células (27174 tokens en las tres llamadas). Reporte y filtros comprobados en la oficina; impresión confirmada por el usuario. OSV quedó pendiente en bookingApi por falta de un archivo admitido con versiones resueltas. La compatibilidad del modelo está comprobada con esta cuenta, no garantizada para otras instalaciones.

## Propuesta DevOps Azure

Arquitectura añade una recomendación preliminar con una opción principal, justificación, evidencia técnica, supuestos, hasta cinco servicios y cinco pasos, y pendientes antes de aceptarla. El perfil `auditor/profiles/azure-v1.md` favorece App Service o Container Apps para cargas sencillas; AKS exige una razón concreta y la hipótesis de plataforma corporativa existente. No se inventan SKU, recursos, precios ni infraestructura disponible. Incluye preparación, entrega con Azure Pipelines, aprobación humana y reversión, tratando cambios de BD por separado. Se obtiene en la misma llamada de Arquitectura; no añade llamadas de consolidación.

Los informes antiguos no se reinterpretan automáticamente. El [ejemplo ficticio](../examples/README.md) muestra esta sección sin ejecutar agentes ni scanners. La generación real de la nueva propuesta queda pendiente por decisión del usuario de no consumir más tokens.
