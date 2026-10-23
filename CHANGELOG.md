# Cambios por componente

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
