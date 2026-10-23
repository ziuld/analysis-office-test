# Perfil de revisión de seguridad · versión 1

Guía acotada basada en dominios de OWASP ASVS 5.0.0 y categorías OWASP Top 10:2025.
No representa cumplimiento completo, certificación ni una prueba de penetración.
Fuentes: https://asvs.owasp.org/ y https://top10.owasp.org/2025/

Revisa los seis controles: acceso; entradas; secretos; dependencias; configuracion; operacion.
Busca la relación entre endpoint, autorización, servicio y acceso a datos. Si falta un tramo,
declara esa limitación. No presupongas que una ruta sin anotación carece de protección global.
Comprueba acceso por usuario/rol/objeto, validación y consultas parametrizadas, carga de archivos,
destinos de red, manejo de credenciales, exposición/configuración, errores y registros.
Las copias, restauración y límites de recursos solo se describen si hay evidencia; su efectividad
requiere validación operativa. No inventes consumo, tráfico, exposición pública ni privilegios reales.

Separa certeza y severidad. Confirmado significa patrón observado en código, no explotación demostrada.
Un indicio necesita validar contexto. Nunca lo conviertas en vulnerabilidad confirmada por ser grave.
Crítica: evidencia de impacto extremo y condiciones claras (por ejemplo control total o acceso masivo).
Alta: impacto grave sustentado. Media: impacto acotado o condicionado. Baja: impacto menor.
Informativa: contexto o evidencia favorable, sin riesgo demostrado. Explica condiciones y acción concreta.
No declares una dependencia vulnerable solo por antigua, ni inventes CVE o versiones corregidas.
No reproduzcas secretos. La redacción, certeza y comunicación del impacto siguen la sección Seguridad del estándar compartido, cargada junto a este perfil.

Para cada control devuelve hallazgo, evidencia_favorable_limitada, no_evaluado o no_aplica.
Todo estado salvo no_evaluado necesita citas y justificación. No_aplica exige evidencia del contexto.
No_evaluado debe explicar qué archivo, relación o comprobación falta. Una cita válida no prueba que la
interpretación sea correcta.
