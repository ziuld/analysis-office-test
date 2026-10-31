# Mejoras del front — dos ejecuciones

## Primera ejecución terminada

- Tarjetas compactas: nombre, rol, estado con indicador y métricas al finalizar.
- Tokens usados desde usage; nunca confundirlos con tokens disponibles. Sin registro completo se muestra No disponible.
- Diálogo ampliado y adaptable a móvil, nombre como título y rol debajo.
- Perfil, cobertura y contexto de revisión colapsados; resultados en desplegable propio.
- Ayuda pequeña bajo el título del campo de pregunta.
- Última respuesta debajo del formulario; historial colapsado al final con lectura independiente, sin sustituir la última respuesta.
- Primera adaptación pixel de tarjetas y botones de consulta, informe y descargas.
- Cambios persistidos en docker/hermes3d-local-demo.patch y comprobada su aplicación inversa.
- Oficina local recompilada y actualizada en http://localhost:3000/office.

Validación: cuatro pruebas existentes de consultas/estados pasan; ESLint sin errores (un aviso preexistente de dependencias del efecto de consulta); build de producción con TypeScript correcto. Comprobación con Playwright en escritorio y móvil, historial y consumo registrado; cero peticiones POST o errores de página. Evidencias en artifacts/office-panel-2026-10-31/. Las capturas usan datos de prueba interceptados en navegador, sin modificar revisiones ni llamar a modelos.

## Segundo bloque implementado

- Sustituido el panel negro por TV lateral pixel junto a pared derecha. Luz ambiental suave durante reuniones, sin texto, respetando movimiento reducido.
- Reservas de destino por posición física además de identificador, incluyendo limpieza. Alternativas de espera en suelo accesible al saturarse los destinos.
- Visitas ambientales al escritorio propio, con pausa triple e indicador naranja, sin cambiar el estado real; trabajo y reuniones interrumpen la pausa.
- Pruebas de simulación: 17 pasan, incluyendo pausa triple e interrupción, y cinco minutos simulados con 12 personajes, limpieza y transiciones de trabajo/reunión sin posiciones de parada superpuestas. ESLint sin errores en los dos archivos modificados.
- Build de producción y TypeScript correctos; oficina local actualizada y saludable. Playwright comprobó reunión, reposo y móvil con movimiento reducido sin errores de página ni peticiones POST. Capturas en artifacts/office-simulation-2026-10-31/. Parche persistido y comprobado con aplicación inversa.

## Tercer bloque: conversaciones ambientales

- Implementado controlador local de conversaciones, limitado a una pareja simultánea y con descansos entre intercambios.
- Burbujas pixel con puntos y signos, por turnos, con pausas y desvanecimiento (respetando movimiento reducido).
- Zonas comunes: 8–15 s, solo cercanos y detenidos, orientándose entre sí. PC: 25–45 s, sin girarse, solo si queda tiempo suficiente en la pausa del escritorio.
- Interrupción inmediata por movimiento, tareas, pensamiento, reservas de actividad, reuniones, salida de participantes o mensajes reales. Se respeta también la permanencia temporal de las burbujas reales.
- No cambia estados, no guarda consultas ni realiza llamadas a modelos. Solo habilitado en la oficina compacta.
- 21 pruebas de simulación y conversaciones pasan; ESLint sin errores en los archivos modificados.
- Build y TypeScript correctos; oficina local actualizada y saludable. Comprobación visual observó una burbuja de puntos de Noor y la respuesta con signo de Kwame desde sus escritorios; comprobada también vista móvil. Cero errores de página y cero peticiones POST. Evidencia en artifacts/office-conversations-2026-10-31/. Nuevos archivos incluidos en el parche reproducible y aplicación inversa verificada.

## Pendiente después del tercer bloque

- Mejorar separación visual de etiquetas y nombres en sofá y zonas concurridas. Conservar el asiento de reunión al cambiar el conjunto de participantes (la asignación actual es estable mientras el conjunto no cambie).
- Terminar coherencia visual pixel del resto del panel, controles y burbujas; evitar etiquetas superpuestas y respetar movimiento reducido.

El usuario autorizó el tercer bloque con un 13% de cuota restante. Parar después de verificar las conversaciones, antes de los retoques pendientes.
