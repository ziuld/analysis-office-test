"""Internal, bounded Graphify adapter. Accepts text, never repository commands."""
import json
import resource
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from runner import run, CONFIG

MAX_BODY = 64_000_000
LOCK = threading.Lock()


def extract(files, complete=False):
    if not isinstance(files, list) or len(files) > (20000 if complete else 120):
        raise ValueError("Invalid file budget")
    total = 0
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source, output = root / "source", root / "output"
        source.mkdir()
        output.mkdir()
        for file in files:
            path, text = file["path"], file["text"]
            parts = PurePosixPath(path).parts
            if (not parts or len(path) > 500 or path.startswith("/") or ".." in parts or "\\" in path
                    or ":" in path or ".git" in parts
                    or not isinstance(text, str)):
                raise ValueError("Invalid source path")
            total += len(text.encode())
            if total > (32_000_000 if complete else 1_000_000) or (not complete and len(text.encode()) > 256_000):
                raise ValueError("Source budget exceeded")
            target = source.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as handle:
                handle.write(text)
        graph_path = output / "graph.json" if complete else output / "graphify-out/graph.json"
        command = (["python", "/app/extract_complete.py", str(source), str(graph_path)] if complete else
                   ["graphify", "extract", str(source), "--code-only", "--no-cluster", "--max-workers", "2", "--out", str(output)])
        outcome = run(command, source, root / "extract.log", 300)
        if outcome["exit_code"] != 0 or not graph_path.is_file():
            return {"status": "error", "reason": "extraction_failed", **outcome}
        graph = json.loads(graph_path.read_text())
        if complete and (not graph.get("processing_complete") or len(graph.get("nodes", [])) > 100000 or len(graph.get("edges", [])) > 200000):
            return {"status": "error", "reason": "incomplete_extraction_or_capacity", "file_coverage": graph.get("file_coverage", [])}
        node_limit, edge_limit = (100000, 200000) if complete else (12000, 24000)
        nodes = [{k: n.get(k) for k in ("id", "label", "source_file", "source_location")}
                 for n in graph.get("nodes", [])][:node_limit]
        ids = {n["id"] for n in nodes}
        edges = [{k: e.get(k) for k in ("source", "target", "relation", "confidence")}
                 for e in graph.get("edges", []) if complete or (e.get("source") in ids and e.get("target") in ids)][:edge_limit]
        diagnostics = sum(any(w in line.lower() for w in ("error", "warning", "skipping"))
                          for line in (root / "extract.log").read_text().splitlines())
        represented = sorted({n["source_file"] for n in nodes if n.get("source_file")})
        truncated = len(graph.get("nodes", [])) > len(nodes) or len(graph.get("edges", [])) > len(edges)
        return {"status": "partial" if diagnostics or truncated else "ready", "engine": CONFIG["graphify"],
                "nodes": nodes, "edges": edges, "diagnostic_lines": diagnostics,
                "truncated": truncated,
                "processing_complete": graph.get("processing_complete", not truncated),
                "file_coverage": graph.get("file_coverage", []),
                "unresolved_relations": sum(e.get("source") not in ids or e.get("target") not in ids for e in edges),
                "input_files": [f["path"] for f in files], "represented_files": represented, **outcome}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.reply(200 if self.path == "/health" else 404, {"ok": self.path == "/health"})

    def reply(self, code, value):
        body = json.dumps(value).encode()
        if len(body) > 64_000_000:
            code, body = 502, b'{"status":"error","reason":"graph_response_budget"}'
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/index":
            return self.reply(404, {"status": "error"})
        try:
            self.connection.settimeout(15)
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BODY:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            with LOCK:
                result = extract(data["files"], complete=data.get("complete", False) is True)
            self.reply(200, result)
        except (ValueError, KeyError, TypeError, OSError):
            self.reply(400, {"status": "error", "reason": "invalid_input_or_extraction"})


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_FSIZE, (64_000_000, 64_000_000))
    ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
