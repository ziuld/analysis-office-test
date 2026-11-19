# Prueba final independiente

Una revisión en un chat que ya conoce los hallazgos no es independiente. Los scripts no pueden borrar ni certificar el historial. No abras sesiones secundarias ni cambies de modelo: el usuario inicia un chat nuevo con el modelo que quiera probar.

1. Fija una copia del código y registra su identidad, rama y commit, incluidas modificaciones locales. Mantén las herramientas y reglas comparables. Los datos de referencia y los informes anteriores no deben formar parte del corpus leído.
2. En el chat nuevo usa el mensaje siguiente. No pegues los hallazgos esperados ni informes previos.

> Usa `./full-stack-code-analyst/AGENT.md` para una evaluación independiente de este proyecto. Este chat no contiene revisiones ni hallazgos anteriores. No leas informes, fichas, comparaciones o referencias de hallazgos de otras revisiones. Declara la caché determinista que reutilices. Prepara con `--mode independent --fresh-context`, usa el modelo de este chat y completa los siete bloques antes de comparar.

3. Iris comprueba herramientas y confirma solo elecciones pendientes. Usa prepare con los flags de independencia; estos evitan reutilizar el informe, aunque permiten resultados de herramientas compatibles. No copies un `.local/` de otro proyecto. Si el corpus incluye informes externos de auditoría, exclúyelos con `--exclude informe-anterior.html` (repetible, también admite carpetas relativas sin comodines) en status y prepare, y no los leas desde el chat. Las exclusiones se registran en el inventario, huella y anexos; finish las conserva.
4. Cierra fichas, evidencia e informe sin consultar la referencia. Registra modelo y esfuerzo solo si son conocidos, y la cobertura que realmente se obtuvo.
5. Después de cerrar, compara con la referencia en un paso separado: misma causa, evidencia, defensas, falsos positivos, omisiones y condiciones. No uses cantidad de riesgos como medida de calidad. Compara tiempo y tokens solo si existen mediciones fiables. Conserva el informe cerrado sin reescribirlo con las respuestas esperadas.

Esta es la única evaluación independiente de cierre prevista en esta ronda. No incluye pruebas de explotación, carga, restauración ni instalación de Docker/WSL. Una prueba técnica con archivos ficticios valida mecanismos del runner, no la capacidad de detección de un modelo en un repositorio real.
