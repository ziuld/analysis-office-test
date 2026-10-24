"""Job-scoped redacted evidence. Shared read-only lookup; no model, shell or network."""
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
        if not isinstance(request, dict) or set(request) - {"query", "paths"}:
            raise AuditError("Consulta de evidencia inválida.")
        query, paths = request.get("query", ""), request.get("paths", [])
        if not isinstance(query, str) or len(query) > 120 or not isinstance(paths, list) or len(paths) > 3:
            raise AuditError("Consulta de evidencia supera el límite.")
        if any(not isinstance(p, str) or len(p) > 500 or not p or PurePosixPath(p).is_absolute()
               or ".." in PurePosixPath(p).parts or ".git" in PurePosixPath(p).parts or "\\" in p or ":" in p for p in paths):
            raise AuditError("Ruta de consulta insegura; solo se permite el espacio de esta revisión.")
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
        paths = list(dict.fromkeys(paths + [p for p in related if p in self.files] +
                                  [p for p in matches if any(w in p.casefold() for w in words)]))[:3]
        if not paths and query:
            paths = [p for p, f in self.files.items() if query.casefold() in f["text"].casefold()][:3]
        fragments = []
        for path in paths:
            lines = self.files[path]["text"].splitlines()
            hit = next((i for i, line in enumerate(lines) if query and query.casefold() in line.casefold()), 0)
            start, end = max(0, hit - 8), min(len(lines), max(0, hit - 8) + 100)
            while end > start and len("\n".join(lines[start:end]).encode()) > 6000:
                end -= 1
            if end == start:
                continue
            text = "\n".join([""] * start + lines[start:end])
            if len(text.encode()) > 12000:
                continue
            fragments.append({"path": path, "text": text, "partial": start != 0 or end != len(lines),
                              "start": start + 1, "end": end})
        return {"fragments": fragments, "relations": edges, "unavailable_paths": unavailable,
                "symbols": [{k: n.get(k) for k in ("id", "label", "source_file", "source_location")} for n in self.graph.get("nodes", []) if n.get("id") in neighbors][:12],
                "limitation": "Relaciones estáticas auxiliares; las conclusiones requieren fuentes de texto."}

    def respond(self, request):
        """Tool failures are observations, not permission to retry or read elsewhere."""
        try:
            return self.lookup(request)
        except AuditError as exc:
            return {"fragments": [], "relations": [], "symbols": [], "error": str(exc)}

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


def prepare_complete(url, workspace, *, scanner=None, index=index_files, fetch=None, downloader=None):
    kwargs = {k: v for k, v in {"fetch": fetch, "downloader": downloader}.items() if v is not None}
    acquired = acquire_complete(url, workspace, **kwargs)
    scanners = scanner(acquired["files"], source_root=workspace / "source") if scanner else []
    if any(s["status"] == "error" for s in scanners):
        raise AuditError("Preparación incompleta: un scanner falló; no se envía una muestra al modelo.")
    pool = [{"path": f["path"], "text": redact(f["text"])} for f in acquired["files"]
            if f["kind"] == "text"]
    mask_findings(pool, scanners)
    graph = index(pool, complete=True)
    if graph.get("status") == "error" or graph.get("truncated") or not graph.get("processing_complete"):
        raise AuditError("Preparación incompleta: mapa " + str(graph.get("reason", graph.get("status"))) + "; truncado=" + str(graph.get("truncated", False)) + "; archivos con error: " + ", ".join(f["path"] for f in graph.get("file_coverage", []) if f.get("status") == "error")[:1500] + ". No se inicia el análisis.")
    if set(f["path"] for f in graph.get("file_coverage", [])) != set(f["path"] for f in pool):
        raise AuditError("Preparación incompleta: el mapa no contabiliza toda la entrada.")
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
    snapshot["preparation"] = {"mode": "complete", "status": "complete", "graph": {k: v for k, v in graph.items() if k not in {"nodes", "edges"}},
        "exploration": {"status": "complete", "closure": "prepared_locally", "iterations": 0, "usage": [], "reads": []},
        "limitations": ["Snapshot íntegro; compatibilidad y cobertura semántica se registran por herramienta."]}
    return snapshot, Evidence(pool, graph)
