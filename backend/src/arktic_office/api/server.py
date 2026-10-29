"""Internal REST API; existing routes and payloads remain compatible."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from arktic_office.core.errors import AuditError
from arktic_office.execution.jobs import Jobs


def handler_for(jobs):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, value, content_type="application/json; charset=utf-8", download=None):
            body = json.dumps(value, ensure_ascii=False).encode() if isinstance(value, (dict, list)) else value
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if download:
                self.send_header("Content-Disposition", 'attachment; filename="' + download + '"')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            try:
                parts = self.path.split("?")[0].strip("/").split("/")
                if parts == ["health"]:
                    return self.send(200, {"ok": True, "version": os.environ.get("ARKTIC_BACKEND_VERSION", "development")})
                if parts == ["runs"]:
                    return self.send(200, {"runs": jobs.listing(), "question_active": jobs.question_active})
                if parts == ['local-sources']:
                    from arktic_office.preparation.local_sources import local_sources
                    return self.send(200, {'sources':local_sources()})
                if len(parts) == 4 and parts[0] == "runs" and parts[2] == "questions":
                    if parts[3] in {"coordinator", "security", "architecture", "inventory"}:
                        return self.send(200, jobs.history(parts[1], parts[3]))
                    return self.send(200, jobs.question(parts[1], parts[3]))
                if len(parts) == 2 and parts[0] == "runs":
                    return self.send(200, jobs.detail(parts[1]))
                if len(parts) == 3 and parts[0] == "runs" and parts[2] in {"report", "download"}:
                    path = jobs.directory(parts[1]) / "informe.md"
                    if not path.is_file():
                        raise FileNotFoundError()
                    if parts[2] == "report":
                        html = path.with_suffix(".html")
                        return self.send(200, {"text": path.read_text(encoding="utf-8"), "html": html.read_text(encoding="utf-8") if html.is_file() else None})
                    return self.send(200, path.read_bytes(), "text/markdown; charset=utf-8", "informe-" + parts[1] + ".md")
                raise FileNotFoundError()
            except AuditError as exc:
                self.send(400, {"error": str(exc)})
            except FileNotFoundError:
                self.send(404, {"error": "Revisión o informe no disponible."})

        def do_POST(self):
            parts = self.path.strip("/").split("/")
            asking = len(parts) == 3 and parts[0] == "runs" and parts[2] == "questions"
            if self.path != "/runs" and not asking:
                return self.send(404, {"error": "Ruta no disponible."})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 2048:
                    return self.send(413, {"error": "Solicitud demasiado grande o vacía."})
                data = json.loads(self.rfile.read(size))
                if asking:
                    if not isinstance(data, dict) or set(data) != {"agent", "question"} or not isinstance(data["agent"], str):
                        raise ValueError()
                    return self.send(202, jobs.ask(parts[1], data["agent"], data["question"]))
                if isinstance(data,dict) and set(data) == {'local_source_id'}:
                    return self.send(202,jobs.start_local(data['local_source_id']))
                if not isinstance(data, dict) or set(data) != {"repository"} or not isinstance(data["repository"], str):
                    raise ValueError()
                return self.send(202, jobs.start(data["repository"].strip()))
            except (ValueError, UnicodeError):
                self.send(400, {"error": "Solicitud inválida: revisa los campos enviados."})
            except AuditError as exc:
                self.send(400, {"error": str(exc)})
            except BlockingIOError:
                self.send(409, {"error": "Ya hay una revisión o consulta en curso. Espera a que termine."})
            except FileNotFoundError:
                self.send(404, {"error": "Revisión no disponible."})
    return Handler


def main():
    ThreadingHTTPServer(("0.0.0.0", 8080), handler_for(Jobs())).serve_forever()


if __name__ == "__main__":
    main()
