# Cambios por componente

## Sin publicar — candidata de Fase 1

- Reparto con base explícita y protección frente a asignaciones vacías que omitían especialistas. Verificación real del recorrido de siete llamadas con los tres especialistas y síntesis válidos, Gitleaks activo y límites de cobertura explícitos.

- Control explícito para pruebas con modelos sin scanners; contrato de salida reforzado y lecturas recortadas sin ampliar presupuestos. Dos pruebas completas reales registradas como parciales, con errores visibles y repetición corregida pendiente de presupuesto.

- Clasificación de fallos OAuth estructurados sin inspeccionar prompts/conversaciones; sesión local recuperada y una respuesta real de Inventario con bookingApi validada, con consumo comunicado.

- Pasadas adicionales de preparación parametrizadas (`AUDIT_PREPARATION_MAX_LOOPS`, 1 por defecto) y perfil mínimo común de pruebas; afinado posterior registrado como Bloque 8.

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
