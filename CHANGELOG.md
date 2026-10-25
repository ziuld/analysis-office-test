# Cambios por componente

## Sin publicar — tramo funcional de Fase 2, 25/10/2026

- Agentes auditados, recuperación por símbolo, OSV multitecnología/SBOM y Semgrep local; contrato compacto y síntesis con fuentes resueltas por Core.
- Integridad del snapshot ante transformaciones de archivo GitHub y clasificación explícita de JSON no compatible con Graphify. Informe v14 provisional, sin aceptación de calidad final.
- Último recorrido Luna/medium completo: ocho llamadas, 66017 tokens comunicados, 352 citas verificadas, sin errores ni advertencias. Intentos parciales y límites conservados en el plan/evidencias.
- Tramo F2-01 a F2-06 cerrado para revisión; fase 2 sigue abierta. Nuevo pendiente acordado F2-07 a F2-12: herramientas, Inventario, Seguridad, Arquitectura, integración e informe, trabajando con el usuario.
- Versiones 0.3.0 y CI/CD conservados; merge manual, sin tags/releases.

## 0.3.0 — Fase 1 aceptada, 24/10/2026

- Snapshot íntegro verificado, Graphify y scanners sin modelos sobre su entrada compatible; recuperación compartida con fuentes originales y citas verificables.
- Coordinador como orquestador de objetivos; tres especialistas seleccionan evidencia bajo rondas y presupuestos configurables. Resultados parciales útiles, cobertura, errores y consumo visibles.
- Backend empaquetado, manifiestos por revisión, consultas independientes con historial acotado y oficina que libera personajes al terminar, sin burbuja persistente ni giro de cabeza al seleccionar.
- Aceptación humana de la base funcional con modelos económicos; límites y pilotos fallidos conservados. Quince pruebas dirigidas del flujo y seis de interfaz registradas. El afinado se retira de Fase 1 y pasa a una Fase 2 independiente.
- Frontend/backend/paquete Python 0.3.0. CI/CD y pins conservados. Merge a main reservado al usuario; sin tags, publicación de imágenes ni GitHub Release.

Los apartados siguientes son registros históricos anteriores al cierre.

## Bloque 8 — arquitectura completa (entrega abierta, 24/10/2026)

- Snapshot íntegro verificado al commit, mapas sin modelos y scanners sobre todo su input compatible; fallos de capacidad/integridad detienen la preparación.
- Paquetes originales para tres especialistas en una llamada del coordinador; recuperación compartida de solo lectura 0/1, omisiones justificadas y estados separados de ejecución/cobertura.
- Conservación individual de hallazgos válidos, condiciones y citas; cleanup de temporales y registros de consultas/consumo.
- Catorce pruebas mínimas correctas y pilotos económicos de bookingApi/Arktic; advertencias y cobertura parcial documentadas. Afinado trasladado al Bloque 9, sin cambios de CI/CD, pins ni versiones 0.2.0.

## Sin publicar — candidata de Fase 1

- Reparto con base explícita y protección frente a asignaciones vacías que omitían especialistas. Verificación real del recorrido de siete llamadas con los tres especialistas y síntesis válidos, Gitleaks activo y límites de cobertura explícitos.

- Control explícito para pruebas con modelos sin scanners; contrato de salida reforzado y lecturas recortadas sin ampliar presupuestos. Dos pruebas completas reales registradas como parciales, con errores visibles y repetición corregida pendiente de presupuesto.

- Clasificación de fallos OAuth estructurados sin inspeccionar prompts/conversaciones; sesión local recuperada y una respuesta real de Inventario con bookingApi validada, con consumo comunicado.

- Pasadas adicionales de preparación parametrizadas (`AUDIT_PREPARATION_MAX_LOOPS`, 1 por defecto) y perfil mínimo común de pruebas; afinado posterior registrado como Bloque 9.

- Preparación híbrida opcional con Graphify fijado, búsquedas y exploración limitada dentro de Docker.
- Backend modular, perfiles centrales y skills; reparto y síntesis con IA opcionales, Azure bajo encargo.
- Oficina vinculada a estados persistidos e historial de las últimas diez consultas por revisión y personaje.
- Resultados por fecha/hora/repositorio, manifiesto de procedencia y recursos de ejecución separados de documentación humana.
- Una sola tentativa por invocación Hermes, sin recuperación ni cambio automático de proveedor.

Versiones frontend/backend conservadas en **0.2.0**. CI/CD mantiene la base del Bloque 1. Validación técnica y limitaciones en [PLAN_FASE_1.md](docs/PLAN_FASE_1.md): la prueba real de cuatro llamadas falló por sesión/cuota; calidad semántica y aceptación humana pendientes. Sin publicación, etiquetas ni cierre de entrega.

## Frontend 0.2.0 — 23/10/2026

- Reporte visual Arktic basado en la referencia v12, con navegación a evidencias y regreso al contexto.
- Estados de información insuficiente y resultados parciales diferenciados de errores técnicos.
- Lectura de informes con secciones vacías omitidas y controles de riesgo; consultas por personaje conservadas.
- Número de versión de la oficina visible en la cabecera.

## Backend 0.2.0 — 23/10/2026

- Revisión de seguridad acotada, perfiles técnicos y scanners Gitleaks y OSV.
- Reparto de evidencia por tipos de archivo, sin depender del README.
- Estándar editorial compartido, reporte HTML/Markdown y propuesta Azure preliminar.
- Resultado terminal de información insuficiente, conservación de resultados válidos y validación independiente de bloques opcionales de Arquitectura.
- Versión del backend disponible en su comprobación de salud.

Validación de esta entrega: 108 pruebas del backend y 9 de interfaz; impresión excluida. Verificación local sin nuevas llamadas a modelos. La instalación en otro equipo y la respuesta real de un modelo al último contrato siguen pendientes.

El commit inicial del MVP no tenía versiones propias de frontend/backend. Esta entrega establece la primera referencia explícita para ambos; desde aquí pueden evolucionar y versionarse por separado.
