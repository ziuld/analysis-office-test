"""Job-scoped original evidence. Shared read-only lookup; no model, shell or network."""
import re
from pathlib import PurePosixPath
from arktic_office.preparation.repository import AuditError, redact, file_role, balanced_files, select, priority, mask_findings
from arktic_office.preparation.snapshot import acquire_complete
from arktic_office.preparation.hybrid import index_files


class Evidence:
    def __init__(self, files, graph):
        self.files = {f["path"]: f for f in files}
        self.graph = graph

    def lookup(self, request):
        if isinstance(request,dict) and 'questions' in request:
            from arktic_office.preparation.lookups import questions
            return questions(self,request)
        if isinstance(request, dict) and "list_paths" in request:
            # A redundant operation name adds no scope, cost or extra lookup.
            if request.get('query') == 'list_paths':
                request = {k:v for k,v in request.items() if k != 'query'}
            if set(request) - {"list_paths", "offset"} or request["list_paths"] is not True:
                raise AuditError('Consulta de inventario inválida: usa solo {"list_paths":true,"offset":0}.')
            offset = request.get("offset", 0)
            if type(offset) is not int or offset < 0:
                raise AuditError("Desplazamiento de inventario inválido.")
            paths = sorted(self.files)
            page = paths[offset:offset + 100]
            return {"fragments": [], "paths": page, "total": len(paths), "offset": offset,
                    "next_offset": offset + len(page) if offset + len(page) < len(paths) else None}
        if isinstance(request, dict) and "tool" in request:
            from arktic_office.preparation.lookups import tool
            return tool(self,request)
        if not isinstance(request, dict) or set(request) - {"query", "paths", "start_line", "offset"}:
            raise AuditError("Consulta de evidencia inválida.")
        query, paths = request.get("query", ""), request.get("paths", [])
        offset = request.get('offset', 0)
        if type(offset) is not int or offset < 0:
            raise AuditError('Desplazamiento de búsqueda inválido.')
        if not isinstance(query, str) or len(query) > 120 or not isinstance(paths, list) or len(paths) > 3:
            raise AuditError("Consulta de evidencia supera el límite.")
        if any(not isinstance(p, str) or len(p) > 500 or not p or PurePosixPath(p).is_absolute()
               or ".." in PurePosixPath(p).parts or ".git" in PurePosixPath(p).parts or "\\" in p or ":" in p for p in paths):
            raise AuditError("Ruta de consulta insegura; solo se permite el espacio de esta revisión.")
        start_line = request.get("start_line")
        if start_line is not None and (type(start_line) is not int or not 1 <= start_line <= 100000 or not paths):
            raise AuditError("Lectura por líneas inválida; indica rutas y una línea positiva hasta 100000.")
        unavailable = [p for p in paths if p not in self.files]
        paths = [p for p in paths if p in self.files]
        if not query.strip() and not paths and not unavailable:
            raise AuditError("La consulta necesita un símbolo o una ruta.")
        seeds = [n for n in self.graph.get("nodes", []) if query and query.casefold() in str(n.get("label", "")).casefold()][:8]
        ids = {n["id"] for n in seeds} | {n["id"] for n in self.graph.get("nodes", []) if n.get("source_file") in paths}
        edges = [e for e in self.graph.get("edges", []) if e.get("source") in ids or e.get("target") in ids][:12]
        neighbors = ids | {e[k] for e in edges for k in ("source", "target")}
        related = [n.get("source_file") for n in self.graph.get("nodes", []) if n.get("id") in neighbors]
        words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", query.casefold())[:8]
        matches = sorted(self.files, key=lambda p: (-sum(w in p.casefold() for w in words), p))
        explicit_paths = list(paths)
        candidates = explicit_paths or list(dict.fromkeys([p for p in related if p in self.files] +
                          [p for p in matches if any(w in p.casefold() for w in words)] +
                          [p for p in sorted(self.files) if query and query.casefold() in self.files[p]['text'].casefold()]))
        # Paginate occurrences, not just filenames: content remains searchable even
        # when a filename or graph symbol happened to match first.
        locations = []
        for path in candidates:
            hits = [i + 1 for i, line in enumerate(self.files[path]['text'].splitlines()) if query and query.casefold() in line.casefold()]
            definitions = [int(m[1]) for n in self.graph.get('nodes', [])
                           if query and n.get('source_file') == path and query.casefold() in str(n.get('label', '')).casefold()
                           and (m := re.match(r'^L(\d+)', str(n.get('source_location', ''))))
                           and 1 <= int(m[1]) <= len(self.files[path]['text'].splitlines())]
            hits = list(dict.fromkeys(definitions + hits))
            if explicit_paths and start_line is not None:
                hits = [start_line]
            locations.extend((path, line) for line in (hits or [1]))
        page = locations[offset:offset + 3]
        paths = [p for p, _ in page]
        fragments = []
        for path, location in page:
            lines = self.files[path]["text"].splitlines()
            hit = location - 1
            # Use the graph's definition location for this file; text hits may be call sites.
            definition = next((int(m.group(1)) - 1 for n in self.graph.get("nodes", [])
                if query and n.get("source_file") == path and query.casefold() in str(n.get("label", "")).casefold()
                and (m := re.match(r"^L(\d+)", str(n.get("source_location", ""))))
                and 1 <= int(m.group(1)) <= len(lines)), None)
            if definition is not None and not query:
                hit = definition
            start = start_line - 1 if start_line is not None else max(0, hit - 8)
            end = min(len(lines), start + 200)
            while end > start and len("\n".join(lines[start:end]).encode()) > 6000:
                end -= 1
            if end <= start:
                continue
            text = "\n".join([""] * start + lines[start:end])
            if len(text.encode()) > 12000:
                continue
            fragments.append({"path": path, "text": text, "partial": start != 0 or end != len(lines),
                              "start": start + 1, "end": end})
        return {"fragments": fragments, "relations": edges, "unavailable_paths": unavailable,
                "matches": [{'path': p, 'line': line} for p, line in page], 'total': len(locations), 'offset': offset,
                'next_offset': offset + len(page) if offset + len(page) < len(locations) else None,
                "symbols": [{k: n.get(k) for k in ("id", "label", "source_file", "source_location")} for n in self.graph.get("nodes", []) if n.get("id") in neighbors][:12],
                "limitation": "Relaciones estáticas auxiliares; las conclusiones requieren fuentes de texto."}

    def respond(self, request):
        """Tool failures are observations, not permission to retry or read elsewhere."""
        try:
            return self.lookup(request)
        except AuditError as exc:
            return {"fragments": [], "relations": [], "symbols": [], "error": str(exc)}

    def batch(self, requests, limits, initial=None):
        """At most four bounded local lookups; return exactly the fragments delivered."""
        if not isinstance(requests, list) or not 1 <= len(requests) <= 4:
            raise AuditError("Una ronda admite entre una y cuatro consultas.")
        # Adapt over-grouped path lists without increasing the four-lookup budget.
        expanded = []
        for request in requests:
            paths = request.get("paths") if isinstance(request, dict) else None
            if isinstance(paths, list) and 3 < len(paths) <= 12:
                parts = [paths[i:i + 3] for i in range(0, len(paths), 3)]
                expanded.extend(({**request, "paths": part}, {"original_paths": len(paths), "part": n + 1, "parts": len(parts)}) for n, part in enumerate(parts))
            else:
                expanded.append((request, None))
        if len(expanded) > 4:
            # Preserve existing bounded error handling; never silently drop a query.
            expanded = [(request, None) for request in requests]
        results, files = [], list(initial or [])
        for request, split in expanded:
            result = self.respond(request)
            if split:
                result["request_split"] = split
            # Merge same-file windows instead of silently losing earlier evidence.
            candidates = {f["path"]: dict(f) for f in files}
            size = sum(len(f["text"].encode()) for f in files)
            for fragment in result["fragments"]:
                previous = candidates.get(fragment["path"])
                candidate = dict(fragment)
                if previous:
                    holder = {"files": [previous]}
                    self.retain(holder, [fragment])
                    candidate = holder["files"][0]
                old_size = len(previous["text"].encode()) if previous else 0
                next_size = size - old_size + len(candidate["text"].encode())
                if next_size <= limits["bytes"] and (previous or len(candidates) < limits["files"]):
                    candidates[fragment["path"]] = candidate
                    size = next_size
            selected = list(candidates.values())
            retained = {f["path"]: f["text"].splitlines() for f in selected}
            def supplied(fragment):
                lines = retained.get(fragment["path"], [])
                return all(i < len(lines) and lines[i] == line for i, line in enumerate(fragment["text"].splitlines()) if line)
            delivered = {f["path"] for f in result["fragments"] if supplied(f)}
            result["omitted_by_budget"] = [f["path"] for f in result["fragments"] if f["path"] not in delivered]
            # Sources are supplied once through make_prompt with verified line IDs.
            result["fragments"] = [{k: v for k, v in f.items() if k != "text"} for f in result["fragments"] if f["path"] in delivered]
            results.append({"request": request, "result": result})
            files = selected
        return files, results

    def retain(self, snapshot, files):
        """Persist only supplied fragments, keeping original line numbers for citations."""
        for file in files:
            previous = next((f for f in snapshot["files"] if f["path"] == file["path"]), None)
            if previous is None:
                snapshot["files"].append(dict(file))
                continue
            old, new = previous["text"].splitlines(), file["text"].splitlines()
            merged = old + [""] * max(0, len(new) - len(old))
            for i, line in enumerate(new):
                if line:
                    merged[i] = line
            snapshot["files"][snapshot["files"].index(previous)] = {**previous, "text": "\n".join(merged)}

    def supplement(self, files, found, limits):
        selected, size = [], 0
        for f in found["fragments"] + files:
            length = len(f["text"].encode())
            if any(x["path"] == f["path"] for x in selected):
                continue
            if len(selected) < limits["files"] and size + length <= limits["bytes"]:
                selected.append(f)
                size += length
        return selected

    def package(self, paths, limits):
        files, used = [], 0
        for path in paths:
            if path not in self.files:
                raise AuditError("Paquete con ruta fuera del snapshot.")
            file = self.files[path]
            from arktic_office.preparation.repository import excerpt
            text, partial = excerpt(file["text"])
            size = len(text.encode())
            if len(files) >= limits["files"] or size > 12000 or used + size > limits["bytes"]:
                raise AuditError("Paquete fuera del presupuesto de la especialidad.")
            files.append({"path": path, "text": text, "partial": partial})
            used += size
        return files


def prepare_complete(url, workspace, *, scanner=None, index=index_files, fetch=None, downloader=None, local_snapshot=None, artifact_directory=None, cache_root=None, indexer_signature=None, refresh=False):
    kwargs = {k: v for k, v in {"fetch": fetch, "downloader": downloader}.items() if v is not None}
    if local_snapshot is not None:
        from arktic_office.preparation.local import acquire_local
        acquired = acquire_local(local_snapshot, workspace)
    else:
        acquired = acquire_complete(url, workspace, **kwargs)
    cache, cache_key, cached = None, None, None
    if cache_root and indexer_signature:
        from arktic_office.preparation.cache import PreparationCache, identity
        cache = PreparationCache(cache_root)
        cache_key = identity(acquired, scanners=scanner is not None, indexer_signature=indexer_signature)
        if not refresh:
            cached = cache.load(cache_key, artifact_directory)
    cache_record = {'status': 'generated' if cache else 'disabled', 'key': cache_key}
    if cached:
        payload, cache_record = cached
        scanners, pool, graph = payload['scanners'], payload['pool'], payload['graph']
    else:
        scanners = scanner(acquired["files"], source_root=workspace / "source") if scanner else []
    if any(s["status"] == "error" for s in scanners):
        raise AuditError("Preparación incompleta: un scanner falló; no se envía una muestra al modelo.")
    if not cached:
        pool = [{"path": f["path"], "text": redact(f["text"])} for f in acquired["files"]
                if f["kind"] == "text"]
        mask_findings(pool, scanners)
        graph = index(pool, complete=True)
    if artifact_directory is not None:
        from pathlib import Path
        from arktic_office.storage.jsonio import write_json
        folder = Path(artifact_directory)
        folder.mkdir(parents=True,exist_ok=True)
        write_json(folder/'graphify-respuesta.json',graph)
        write_json(folder/'scanners-adaptador.json',scanners)
    if graph.get("status") == "error" or graph.get("truncated") or not graph.get("processing_complete"):
        raise AuditError("Preparación incompleta: mapa " + str(graph.get("reason", graph.get("status"))) + "; truncado=" + str(graph.get("truncated", False)) + "; archivos con error: " + ", ".join(f["path"] for f in graph.get("file_coverage", []) if f.get("status") == "error")[:1500] + ". No se inicia el análisis.")
    if set(f["path"] for f in graph.get("file_coverage", [])) != set(f["path"] for f in pool):
        raise AuditError("Preparación incompleta: el mapa no contabiliza toda la entrada.")
    if cache and not cached:
        cache.save(cache_key, {'scanners': scanners, 'pool': pool, 'graph': graph}, artifact_directory)
        saved = cache.load(cache_key)
        if saved:
            cache_record['prepared_at'] = saved[1]['prepared_at']
    graph["node_count"], graph["edge_count"] = len(graph["nodes"]), len(graph["edges"])
    graph_coverage = {f["path"]: f for f in graph.get("file_coverage", [])}
    for item in acquired["inventory"]:
        item["map"] = graph_coverage.get(item["path"], {"status": "unsupported", "reason": item["kind"]})
        item["scanners"] = {s["name"]: "offered" if s["name"].startswith("Gitleaks") else
                            "offered" if item["path"] in s.get("input_files", []) else "unsupported_input" for s in scanners}
        graph["nodes"].append({"id": "snapshot-file:" + item["path"], "label": item["path"], "source_file": item["path"], "kind": "snapshot_file"})
    candidates = sorted((f for f in pool if priority(f["path"]) < 9), key=lambda f: (priority(f["path"]), f["path"]))
    candidates = balanced_files(candidates, ("entry", "business", "routes", "data", "config", "manifest", "deployment", "security", "readme", "source"))
    snapshot = select({**acquired, "files": candidates}, scanner=None)
    snapshot["scanners"] = scanners
    snapshot["coverage"].update(acquired=[x["path"] for x in acquired["inventory"]],
        scanner_input=[x["path"] for x in acquired["inventory"]] if scanner else [], scanner_executed=bool(scanner),
        graph_input=[f["path"] for f in pool], explorer_reads=[], acquisition_complete=True)
    snapshot["preparation"] = {"mode": "complete", "status": "complete", "cache": cache_record, "graph": {k: v for k, v in graph.items() if k not in {"nodes", "edges"}},
        "exploration": {"status": "complete", "closure": "prepared_locally", "iterations": 0, "usage": [], "reads": []},
        "limitations": ["Snapshot íntegro; compatibilidad y cobertura semántica se registran por herramienta."]}
    return snapshot, Evidence(pool, graph)
