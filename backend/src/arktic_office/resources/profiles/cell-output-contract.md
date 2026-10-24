Comprobación obligatoria del JSON antes de responder (sin llamadas adicionales):

La respuesta final del informe incluye SIEMPRE en la raíz "schema_version":3, "confirmados", "indicios", "dudas" y "controles". No omitas schema_version aunque todas las listas estén vacías.

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

- Si tema="componentes", añade componente como objeto con EXACTAMENTE nombre,
  tecnologia y funcion, los tres textos de hasta 160 caracteres. Ejemplo:
  "componente":{"nombre":"API","tecnologia":"Python, versión declarada","funcion":"Recibe revisiones"}.
  No uses una cadena, lista ni claves adicionales; incluye versiones dentro de tecnologia.
- En presentacion.flujo_actual, usa IDs únicos con letras ASCII, números o guion
  bajo, por ejemplo oficina_web y audit_api. No uses guiones medios, espacios ni
  caracteres acentuados. origen y destino deben coincidir exactamente con esos IDs.
