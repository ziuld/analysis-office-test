Comprobación obligatoria del JSON antes de responder (sin llamadas adicionales):

- `tema` y `control` son campos distintos. `tema` SOLO admite: proposito, componentes,
  arranque, datos, recuperacion, estabilidad, recursos, servicios, acceso, responsabilidades.
  No uses seguridad, secretos, dependencias, configuracion u operacion como `tema`.
  Esas categorías pertenecen a `control`: acceso, entradas, secretos, dependencias,
  configuracion, operacion o contexto. Escoge el tema permitido que describe el hecho.
- En TODOS los hallazgos, tanto confirmados como indicios, incluye `titulo` (hasta 110
  caracteres), `resultado_esperado` (hasta 300) y `detalle_tecnico` (hasta 600), además
  del resto del contrato. Esto también se aplica a informativa: describe su utilidad y
  límites sin inventar un riesgo. Un riesgo confirmado necesita esos tres campos igual
  que un indicio; no copies el ejemplo informativo como si fuese el esquema completo.
- Cada hallazgo necesita de una a tres referencias F#:L# existentes. No inventes fuentes
  para completar el formato. Si falta evidencia, omite el hallazgo y explica la carencia.
- Devuelve una sola respuesta JSON, sin Markdown, respetando los límites de texto.
