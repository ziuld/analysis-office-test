# Fase 2 — Mejora de agentes, recuperación y calidad

Estado: **propuesta, sin ejecutar cambios de afinado**. Parte de la Fase 1 0.3.0 aceptada el 24/10/2026. El usuario conserva el merge a main. Esta fase mejora configuración y funcionamiento según evidencia y feedback; no presupone entrenamiento de pesos ni actualización de dependencias.

## Objetivo

Conseguir respuestas más útiles, precisas y propias de cada especialidad, localizando suficiente código con un coste controlado. Primero revisar qué instrucciones/configuración se aplican realmente a los agentes Hermes usados por Arktic; después cambiar una causa cada vez. No ampliar CI/CD, añadir servicios ni ejecutar suites completas sin necesidad. Mantener un perfil económico reproducible y pruebas dirigidas mínimas.

## Punto de partida comprobado

- El flujo descarga y verifica el snapshot completo antes de mapas/scanners. Los especialistas reciben fragmentos limitados: insuficiencia de contexto no implica que falten archivos descargados.
- [hermes_runtime.py](../backend/src/arktic_office/adapters/hermes_runtime.py) instancia `AIAgent` por llamada con un prompt de sistema efímero, herramientas desactivadas y `max_iterations=1`. Se usan `skip_context_files=True`, `skip_memory=True`, `skip_background_review=True`; no se solicita identidad SOUL. No asumir que una personalidad configurada en otra sesión/UI se aplica a estas llamadas.
- Los focos efectivos salen de [agents.json](../backend/src/arktic_office/resources/profiles/agents.json). Perfiles de modelos/límites: [models.json](../backend/src/arktic_office/resources/profiles/models.json) y [config/models.py](../backend/src/arktic_office/config/models.py). Investigación y coordinación: [research.py](../backend/src/arktic_office/coordination/research.py), [coordinator.py](../backend/src/arktic_office/coordination/coordinator.py). Skill y contrato de salida se añaden explícitamente; la configuración efectiva incluye también variables de entorno, sin exponer secretos.
- Las últimas consultas fueron por rutas exactas, con relaciones del grafo adjuntas. Esto no demuestra navegación eficiente por símbolos/grafo. Las ventanas de 100 líneas pueden omitir rutas/middleware posteriores; Arquitectura agotó su cap de seis archivos. El padding de líneas consume presupuesto. Aumentar archivos o modelo sin localizar el cuello de botella no garantiza mejor resultado.
- Baseline `f7043007-40a9-42a3-8b1e-a1478688c25c`: tres especialistas y síntesis, 8 llamadas gpt-6-luna/low, 52.366 tokens comunicados, 7 observaciones y 22 citas verificadas. Informe parcial: un tema inválido rechazado, cinco controles no evaluados, una formulación sobre recuperación de trabajos demasiado amplia. [Evidencia](evidence/orchestrator-research-2026-10-24.json).

## 1. Revisar configuración efectiva de Hermes y agentes

- [ ] F2-01 Trazar cómo el Hermes fijado compone el prompt: sistema base, prompt efímero, perfil, identidad, idioma, archivos de contexto, memoria y herramientas. Contrastar los flags del adaptador con el código de Hermes instalado, sin mostrar credenciales ni conversaciones privadas. Distinguir perfiles visibles en Hermes de los agentes efímeros del análisis.
- [ ] F2-02 Inventariar las instrucciones realmente enviadas por rol y detectar duplicidades, contradicciones o huecos: objetivo, idioma español, qué constituye evidencia suficiente, cuándo buscar, cómo declarar límites, enums y esquema de salida. No modificar todavía varios prompts a la vez.
- [ ] F2-03 Proponer focos breves y criterios claros por especialidad, con ejemplos pequeños: Seguridad evalúa controles/riesgos; Arquitectura describe estructura y operación; Inventario identifica tecnología/función. Orquestador distribuye objetivos y sintetiza sin ampliar las conclusiones. Probar el cambio mínimo que corrija el problema identificado.

**Salida:** ficha de configuración efectiva y propuesta de instrucciones, con procedencia y diferencias respecto a las personalidades de la UI. El primer trabajo de esta fase es esta auditoría, no subir modelos.

## 2. Comprobar cómo encuentran y reciben el código

- [ ] F2-04 Seguir las trazas de fuentes necesarias, consultas, ventanas recibidas, omisiones por presupuesto y carencias finales. Clasificar cada carencia: información operativa inexistente, parser incompatible, búsqueda ineficiente, ventana incorrecta, cap agotado o interpretación del modelo.
- [ ] F2-05 Ensayar navegación orientada por símbolos/relaciones y lectura de la región concreta antes de aumentar caps. Verificar al menos el acceso a rutas HTTP/middleware y código de recuperación, comparando el contenido entregado con lo que se necesitaba.
- [ ] F2-06 Si las trazas lo justifican, ajustar una sola variable: segunda ronda de Seguridad, ventanas, límites por rol o instrucciones de búsqueda. Mantener límites duros, mismo snapshot y registro de contexto realmente entregado. No adoptar un aumento global de archivos como respuesta automática.

**Salida:** explicación verificable de por qué cada rol obtuvo o no el código necesario y el menor ajuste útil al flujo existente.

## 3. Medir, recoger feedback y decidir modelos

- [ ] F2-07 Definir un conjunto pequeño de preguntas esperadas sobre repositorios representativos y sus fuentes, incluyendo casos de insuficiencia legítima. Comparar una variable por vez sobre el mismo commit. Acordar un presupuesto acotado antes de una tanda de pruebas reales; no introducir bucles de evaluación automáticos.
- [ ] F2-08 Medir utilidad por rol, interpretación fiel, citas, rechazos de formato, carencias resolubles, consultas útiles, bytes, llamadas, tiempo y tokens comunicados. Que una cita exista no valida la conclusión; que haya más hallazgos no demuestra más calidad. Conservar también intentos fallidos.
- [ ] F2-09 Ajustar modelo/razonamiento por rol solo cuando se distinga un fallo de razonamiento de falta de fuentes o instrucciones. Conservar perfil económico; revisar modelos/proveedor disponibles y consumo en el momento, sin fijar ahora una elevación general.
- [ ] F2-10 Incorporar feedback visual y sobre informes con cambios pequeños. Cerrar esta fase mediante aceptación humana, resultados comparables y decisión de versión independiente; merge manual del usuario.

**Criterio de cierre propuesto:** los roles respetan su responsabilidad, acceden al código necesario dentro del presupuesto acordado y distinguen carencias reales de fallos de recuperación. Resultados y límites comprensibles y aceptados por el usuario. Las comprobaciones se limitan a contratos/caminos afectados y pilotos representativos; sin nuevos pipelines ni una plataforma de evaluación.
