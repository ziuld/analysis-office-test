"""Human-readable preparation limits, only for new hybrid snapshots."""


def notes(snapshot):
    preparation = snapshot.get("preparation")
    if not preparation:
        return []
    coverage = snapshot.get("coverage", {})
    if preparation.get("mode") == "complete":
        inventory = snapshot.get("inventory", [])
        processed = sum(x.get("map", {}).get("status") == "processed" for x in inventory)
        unsupported = sum(x.get("map", {}).get("status") == "unsupported" for x in inventory)
        return [f"Snapshot completo verificado: {len(inventory)} de {snapshot.get('tree_files', '?')} archivos al commit; incluye ocultos, tests y binarios.",
                f"Mapa estático: {processed} archivos procesados; {unsupported} sin parser compatible. Todos constan en el inventario; relaciones estáticas no garantizan exhaustividad semántica.",
                f"Contexto de modelos: {len(snapshot['files'])} archivos con fragmentos originales retenidos; paquetes y consultas registrados por célula.",
                "Preparación local sin llamadas a modelos. Scanners sobre todo el input compatible; ofrecido no significa evaluado. LFS y submódulos no hidratados detienen la revisión."] + preparation.get("limitations", [])
    exploration, graph = preparation["exploration"], preparation["graph"]
    closures = {"sufficient": "el explorador declaró suficiente la lectura parcial",
                "insufficient": "lectura insuficiente", "iteration_limit": "límite de iteraciones",
                "context_limit": "límite de contexto", "time_limit": "límite de tiempo",
                "technical_error": "fallo técnico; se conserva la evidencia útil",
                "inspect_only": "solo inspección, sin modelo"}
    result = [f"Adquisición: {len(coverage.get('acquired', []))} de {snapshot.get('tree_files', '?')} archivos del árbol; lectura parcial.",
              f"Entrada a scanners: {len(coverage.get('scanner_input', []))} archivos. Consultar el estado de cada herramienta; entrada no equivale a cobertura satisfactoria.",
              f"Contexto disponible para especialistas: {len(snapshot['files'])} archivos. Los envíos reales se registran por célula; no equivalen al árbol completo.",
              f"Mapa estructural: {graph.get('status', 'desconocido')}; {len(graph.get('represented_files', []))} archivos representados. Las relaciones requieren contraste con texto.",
              f"Exploración: {closures.get(exploration['closure'], 'cierre desconocido')}; {exploration['iterations']} llamadas; {exploration.get('prompt_bytes', 0)} bytes acumulados de entrada."]
    usage = exploration.get("usage", [])
    known = [u["total_tokens"] for u in usage if isinstance(u, dict) and type(u.get("total_tokens")) is int]
    result.append(f"Consumo comunicado: {sum(known)} tokens conocidos; {len(usage) - len(known)} llamadas sin medida. Sin medida no significa consumo cero.")
    result += preparation.get("limitations", [])
    return result
