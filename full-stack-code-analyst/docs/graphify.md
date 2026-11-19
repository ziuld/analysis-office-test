# Graphify en Iris

El ejecutor local prepara Graphify sobre una copia dentro de `.local/cache/graphify/`. Genera un grafo estático sin proveedores LLM mediante `graphify update <copia> --no-cluster`. La versión instalada debe admitir esa operación; un fallo queda visible en el estado.

La instalación opcional usa el paquete y la versión de [versions.json](../tools/versions.json) en un entorno Python aislado bajo `.local/tools/`. El comando es `python scripts/iris.py install graphify`, desde la carpeta de Iris. La preparación habitual se describe en [ejecucion-local.md](ejecucion-local.md).

Cuando el resultado está vigente se reutiliza. Las nuevas revisiones consultan su `resultado.json` mediante `iris.py results --review <ruta> --tool graphify --search <símbolo>`. El resultado paginado incluye las ubicaciones con las que orientar lecturas. Los originales y la caché nativa permanecen dentro de `.local/`.

La IA del chat sigue consumidores y defensas de las relaciones relevantes, contrasta las líneas del código original y guarda qué pistas se confirmaron o quedaron pendientes. Esa interpretación se mantiene en la misma sesión y con el mismo modelo. Si el usuario pide repetirla con otro modelo, cambia la selección en su asistente y puede reutilizar el grafo.

Los anexos registran versión, fecha, alcance, exclusiones y si el mapa se generó o se reutilizó. La extracción estática y la interpretación del chat se identifican por separado. Un grafo con errores o sin entradas compatibles aporta cobertura limitada.
