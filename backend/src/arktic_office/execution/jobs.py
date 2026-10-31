"""Single-user jobs, independent of HTTP routing and physical result layout."""
import logging
import threading
import uuid
import time
import fcntl
from datetime import datetime, timezone
from arktic_office.core.errors import AuditError
from arktic_office.core.contracts import ACTIVE_STATES, StateEvent, JobRecord
from arktic_office.preparation.repository import parse_repo
from arktic_office.config.settings import reports_root
from arktic_office.storage.jsonio import read_json, write_json
from arktic_office.storage.runs import RunStore
from arktic_office.coordination.questions import prepare_question, answer_question
from arktic_office.adapters.processes import run_audit

REPORTS = reports_root()
ACTIVE = ACTIVE_STATES


class Jobs:
    def __init__(self, root=REPORTS, runner=None, answerer=None, *, store=None, event_sink=None, local_runner=None):
        self.store = store if store is not None else RunStore(root)
        self.root = self.store.root
        self.root.mkdir(parents=True, exist_ok=True)
        self.event_sink = event_sink
        self.lock = threading.Lock()
        self.runner = runner or self.execute
        self.local_runner = local_runner or (lambda job_id,folder: run_audit(job_id,local_snapshot=folder))
        self.answerer = answerer or answer_question
        self.question_active = None
        self.question_queue = []
        directories = self.store.directories()
        for path in (p for directory in directories for p in (directory / "consultas").glob("*.json")):
            data = read_json(path, {})
            if data.get("estado") in {"respondiendo", "en_cola"}:
                data.update(estado="error", error="La consulta se interrumpió al reiniciar el servicio. No se reintentó.")
                write_json(path, data)
        # A server restart interrupts its children; never leave a stale "running" job.
        for path in (directory / "job.json" for directory in directories):
            data = read_json(path, {})
            if data.get("estado") in ACTIVE:
                data.update(estado="error", error="La revisión se interrumpió al reiniciar el servicio. Puedes iniciarla de nuevo.")
                write_json(path, data)
                write_json(path.parent / 'meeting.json', {'active':False, 'phase':'interrupted'})
                if (self.root / '.knowledge' / 'office.sqlite').is_file():
                    from arktic_office.storage.knowledge import Knowledge
                    Knowledge(self.root).interrupt(path.parent.name)

    def directory(self, job_id):
        return self.store.resolve(job_id)

    def detail(self, job_id):
        return self.store.detail(job_id)


    def listing(self):
        return self.store.listing()

    def start(self, repository):
        parse_repo(repository)
        return self._start(repository)

    def start_local(self, source_id):
        from arktic_office.preparation.local_sources import local_source
        source = local_source(source_id)
        return self._start(source['repository'],source)

    def _start(self, repository, local=None):
        with self.lock:
            if self.question_active or any(x["estado"] in ACTIVE for x in self.listing()):
                raise BlockingIOError()
            job_id = str(uuid.uuid4())
            path = self.store.create(job_id, repository=repository)
            job: JobRecord = {"id": job_id, "repository": repository, "estado": "preparando",
                   "created": datetime.now(timezone.utc).isoformat()}
            if local:
                job.update(source_type='local_git',local_source_id=local['id'],branch=local['branch'],
                           commit=local['commit'],project_name=local['name'])
            write_json(path / "job.json", job)
            self._publish(job_id, "preparando")
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

    def history(self, job_id, agent):
        from arktic_office.coordination.questions import AGENTS
        if agent not in AGENTS:
            raise AuditError("Agente no válido.")
        directory = self.directory(job_id) / "consultas"
        from itertools import islice
        paths = list(islice(directory.glob("*.json"), 1001))
        if len(paths) > 1000:
            raise AuditError("Demasiadas consultas guardadas; revisar conservación antes de listar.")
        result = []
        for path in paths:
            if path.is_symlink() or not path.is_file():
                continue
            data = read_json(path, {})
            if data.get("run_id") == job_id and data.get("agent") == agent:
                result.append((data.get("created") or datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), data))
        return {"questions": [data for _, data in sorted(result, key=lambda x: (x[0], x[1].get("id", "")), reverse=True)[:10]]}

    def ask(self, job_id, agent, question):
        with self.lock:
            from arktic_office.coordination.questions import AGENTS
            from arktic_office.preparation.repository import redact
            if agent not in AGENTS or not isinstance(question, str) or not 1 <= len(question.strip()) <= 800:
                raise AuditError('Elige un agente y escribe una pregunta de hasta 800 caracteres.')
            if len(self.question_queue) >= 10:
                raise AuditError('La cola admite diez consultas pendientes.')
            job = self.detail(job_id)
            if job.get("simulation"):
                raise AuditError("Este ejemplo es ficticio y no admite consultas al modelo. No se ha gastado ningún token.")
            if not job["has_report"] and job["estado"] not in ACTIVE:
                raise AuditError("Selecciona una revisión terminada con informe disponible.")
            directory = self.directory(job_id)
            if job['estado'] not in ACTIVE:
                prepare_question(directory, agent, question)  # Fail invalid saved contexts before accepting work.
            question_id = str(uuid.uuid4())
            data = {"id": question_id, "run_id": job_id, "agent": agent, "nombre": AGENTS[agent],
                    "created": datetime.now(timezone.utc).isoformat(),
                    "question": redact(question.strip()), "repository": job['repository'], "commit": job.get('commit'),
                    "model": None, "reasoning": None, "estado": "en_cola"}
            (directory / "consultas").mkdir(exist_ok=True)
            write_json(directory / "consultas" / (question_id + ".json"), data)
            self.question_queue.append((directory, data))
            result = dict(data)
        self.dispatch_questions()
        return result

    def dispatch_questions(self):
        with self.lock:
            if self.question_active or not self.question_queue or any(x['estado'] in ACTIVE for x in self.listing()):
                return
            directory, data = self.question_queue.pop(0)
            self.question_active = data
            threading.Thread(target=self.question_work, args=(directory, data, None), daemon=True).start()

    def question_work(self, directory, initial, context):
        started = time.monotonic()
        data = dict(initial)
        try:
            context = context or prepare_question(directory, data['agent'], data['question'])
            # Exact stored question IDs are served from Core without waking a model.
            from arktic_office.storage.jsonio import read_json
            report = read_json(directory / 'informe.json', {})
            cached = next((a for a in report.get('cuestionario', {}).get('respuestas', [])
                           if a['id'] == data['question'].upper() and a['estado'] in {'respondida', 'no_aplica'}), None)
            if cached:
                data.update(model=None, reasoning=None, source='core')
            else:
                data.update(estado='respondiendo', model=context['config']['model'], reasoning=context['config']['reasoning'])
                write_json(directory / 'consultas' / (data['id'] + '.json'), data)
                self._publish(data['run_id'], 'respondiendo', question_id=data['id'])
            # Same interprocess lock as CLI audits; at most one model activity.
            with (self.root / ".audit.lock").open("a") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise AuditError("Hay una revisión por comando activa. Consulta cancelada sin llamar al modelo.") from None
                answer = ({'respuesta': cached['respuesta'], 'evidencia': cached['evidencia'], 'certeza': 'explicacion', 'usage': None, 'source': 'core'}
                          if cached else self.answerer(context))
                data.update(answer, estado="completada")
        except AuditError as exc:
            data.update(estado="error", error=str(exc))
            if getattr(exc, 'global_stop', False):
                with self.lock:
                    for pending_directory, pending in self.question_queue:
                        pending.update(estado='error', error='Consulta detenida por fallo global del proveedor. Se conserva sin reintento: ' + str(exc))
                        write_json(pending_directory / 'consultas' / (pending['id'] + '.json'), pending)
                    self.question_queue.clear()
        except Exception:
            data.update(estado="error", error="No se pudo completar la consulta. Sin reintento automático.")
        finally:
            if context and 'respuesta_original' in context:
                data['respuesta_original'] = context['respuesta_original']
            data['duration_seconds'] = round(time.monotonic() - started, 3)
            try:
                write_json(directory / "consultas" / (data["id"] + ".json"), data)
            finally:
                with self.lock:
                    self.question_active = None
            self._publish(data["run_id"], data["estado"], question_id=data["id"])
            self.dispatch_questions()

    def work(self, job_id, repository):
        path = self.directory(job_id)
        job = read_json(path / "job.json")
        try:
            job.pop("error", None)
            job["estado"] = "analizando"
            write_json(path / "job.json", job)
            self._publish(job_id, "analizando")
            if job.get('source_type') == 'local_git':
                from arktic_office.preparation.local_sources import local_source
                source = local_source(job['local_source_id'])
                if source['commit'] != job['commit'] or source['branch'] != job['branch']:
                    raise AuditError('La captura local cambió después de iniciar la revisión.')
                returncode = self.local_runner(job_id,source['folder'])
            else:
                returncode = self.runner(job_id, repository)
            report = read_json(path / "informe.json", {})
            if report.get('stop_reason'):
                with self.lock:
                    for pending_directory, pending in self.question_queue:
                        pending.update(estado='error', error='Consulta detenida por la parada global de la revisión: ' + report['stop_reason'])
                        write_json(pending_directory / 'consultas' / (pending['id'] + '.json'), pending)
                    self.question_queue.clear()
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
        if job['estado'] not in ACTIVE:
            write_json(path / 'meeting.json', {'active': False, 'run_id': job_id, 'phase': 'finished'})
        self._publish(job_id, job["estado"])
        self.dispatch_questions()

    @staticmethod
    def execute(job_id, repository):
        return run_audit(job_id, repository)

    def _publish(self, run_id, state, *, question_id=None):
        if self.event_sink is None:
            return
        try:
            self.event_sink(StateEvent(run_id, state, scope="question" if question_id else "run", question_id=question_id))
        except Exception:
            # A future transport must not invalidate an already persisted result.
            logging.getLogger(__name__).warning("No se pudo publicar un evento; el estado persistido se conserva.")

