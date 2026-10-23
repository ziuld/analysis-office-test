"""Internal single-user API. No host ports; accessed through Studio's proxy."""
import json
import os
import re
import subprocess
import sys
import threading
import uuid
import fcntl
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from repository import AuditError, parse_repo
from team import write_json
from questions import prepare_question, answer_question

REPORTS = Path(os.environ.get("AUDIT_REPORTS_DIR", "/reports"))
SAFE_ID = re.compile(r"[a-zA-Z0-9_-]{8,80}\Z")
ACTIVE = {"preparando", "analizando"}
ROLES = (("coordinator", "Coordinador"), ("security", "Seguridad"),
         ("architecture", "Arquitectura"), ("inventory", "Inventario"))


def read_json(path, fallback=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return fallback


class Jobs:
    def __init__(self, root=REPORTS, runner=None, answerer=None):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.runner = runner or self.execute
        self.answerer = answerer or answer_question
        self.question_active = None
        for path in root.glob("*/consultas/*.json"):
            data = read_json(path, {})
            if data.get("estado") == "respondiendo":
                data.update(estado="error", error="La consulta se interrumpió al reiniciar el servicio. No se reintentó.")
                write_json(path, data)
        # A server restart interrupts its children; never leave a stale "running" job.
        for path in root.glob("*/job.json"):
            data = read_json(path, {})
            if data.get("estado") in ACTIVE:
                data.update(estado="error", error="La revisión se interrumpió al reiniciar el servicio. Puedes iniciarla de nuevo.")
                write_json(path, data)

    def directory(self, job_id):
        if not SAFE_ID.fullmatch(job_id):
            raise AuditError("Identificador de revisión inválido.")
        path = (self.root / job_id).resolve()
        if path.parent != self.root.resolve() or not path.is_dir():
            raise FileNotFoundError()
        return path

    def detail(self, job_id):
        path = self.directory(job_id)
        job = read_json(path / "job.json")
        snapshot = read_json(path / "evidencia.json", {})
        team = read_json(path / "estado.json", {})
        report = read_json(path / "informe.json", {})
        if job is None:
            if not snapshot or not report:
                raise FileNotFoundError()
            job = {"id": job_id, "repository": snapshot["repository"], "estado": report.get("estado", "completo"),
                   "historical": True, "created": datetime.fromtimestamp((path / "informe.md").stat().st_mtime, timezone.utc).isoformat()}
        if job["estado"] in ACTIVE and not snapshot:
            job = {**job, "estado": "preparando"}
        return {**job, "commit": snapshot.get("commit"), "branch": snapshot.get("branch"), "celulas": team.get("celulas", report.get("celulas", [])),
                "mensaje": report.get("mensaje"), "necesita": report.get("necesita", []),
                "has_report": (path / "informe.md").is_file(), "evidence_origin": snapshot.get("evidence_origin"),
                "report_format": report.get("schema_version", 1), "derived_from": snapshot.get("source_revision"), "simulation": bool(snapshot.get("simulation"))}

    def listing(self):
        items = []
        for path in sorted(self.root.iterdir(), key=lambda p: p.name, reverse=True):
            if not path.is_dir() or not SAFE_ID.fullmatch(path.name):
                continue
            try:
                items.append(self.detail(path.name))
            except (FileNotFoundError, KeyError):
                continue
        return sorted(items, key=lambda x: x.get("created", ""), reverse=True)[:30]

    def start(self, repository):
        parse_repo(repository)
        with self.lock:
            if self.question_active or any(x["estado"] in ACTIVE for x in self.listing()):
                raise BlockingIOError()
            job_id = str(uuid.uuid4())
            path = self.root / job_id
            path.mkdir()
            job = {"id": job_id, "repository": repository, "estado": "preparando",
                   "created": datetime.now(timezone.utc).isoformat()}
            write_json(path / "job.json", job)
            threading.Thread(target=self.work, args=(job_id, repository), daemon=True).start()
        return job

    def question(self, job_id, question_id):
        try:
            if str(uuid.UUID(question_id)) != question_id:
                raise ValueError()
        except ValueError:
            raise AuditError("Identificador de consulta inválido.") from None
        result = read_json(self.directory(job_id) / "consultas" / (question_id + ".json"))
        if result is None:
            raise FileNotFoundError()
        return result

    def ask(self, job_id, agent, question):
        with self.lock:
            if self.question_active or any(x["estado"] in ACTIVE for x in self.listing()):
                raise BlockingIOError()
            job = self.detail(job_id)
            if job.get("simulation"):
                raise AuditError("Este ejemplo es ficticio y no admite consultas al modelo. No se ha gastado ningún token.")
            if not job["has_report"] or job["estado"] in ACTIVE:
                raise AuditError("Selecciona una revisión terminada con informe disponible.")
            directory = self.directory(job_id)
            context = prepare_question(directory, agent, question)
            question_id = str(uuid.uuid4())
            data = {"id": question_id, "run_id": job_id, "agent": agent, "nombre": context["nombre"],
                    "question": context["question"], "repository": context["repository"], "commit": context["commit"],
                    "model": context["config"]["model"], "reasoning": context["config"]["reasoning"],
                    "estado": "respondiendo"}
            (directory / "consultas").mkdir(exist_ok=True)
            write_json(directory / "consultas" / (question_id + ".json"), data)
            self.question_active = data
            threading.Thread(target=self.question_work, args=(directory, data, context), daemon=True).start()
            return dict(data)

    def question_work(self, directory, initial, context):
        data = dict(initial)
        try:
            # Same interprocess lock as CLI audits; at most one model activity.
            with (self.root / ".audit.lock").open("a") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise AuditError("Hay una revisión por comando activa. Consulta cancelada sin llamar al modelo.") from None
                data.update(self.answerer(context), estado="completada")
        except AuditError as exc:
            data.update(estado="error", error=str(exc))
        except Exception:
            data.update(estado="error", error="No se pudo completar la consulta. Sin reintento automático.")
        finally:
            try:
                write_json(directory / "consultas" / (data["id"] + ".json"), data)
            finally:
                with self.lock:
                    self.question_active = None

    def work(self, job_id, repository):
        path = self.root / job_id
        job = read_json(path / "job.json")
        try:
            job.pop("error", None)
            job["estado"] = "analizando"
            write_json(path / "job.json", job)
            returncode = self.runner(job_id, repository)
            report = read_json(path / "informe.json", {})
            if returncode == 0 and report.get("estado") == "completo":
                job["estado"] = "completo"
            elif report:
                job["estado"] = report.get("estado", "parcial")
            else:
                job["estado"] = "error"
            if returncode:
                job["error"] = read_json(path / "error.json", {}).get("error", "No se pudo completar la revisión. Comprueba el acceso al repositorio y la sesión de Hermes.")
        except Exception:
            job.update(estado="error", error="El servicio no pudo completar esta revisión. Puedes intentarlo de nuevo.")
        write_json(path / "job.json", job)

    @staticmethod
    def execute(job_id, repository):
        # No shell and no user-controlled executable or model parameters.
        result = subprocess.run([sys.executable, "/app/audit.py", repository, "--job-id", job_id],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1500, check=False)
        return result.returncode


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
                if len(parts) == 4 and parts[0] == "runs" and parts[2] == "questions":
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


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), handler_for(Jobs())).serve_forever()
