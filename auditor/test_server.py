import json
import fcntl
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import Jobs, handler_for
from team import write_json
from test_questions import fixture
from repository import AuditError


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.release = threading.Event()
        self.jobs = Jobs(self.root, runner=self.fake_runner)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.jobs))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def fake_runner(self, job_id, repository):
        self.release.wait(3)
        directory = self.root / job_id
        if repository.endswith("/missing"):
            write_json(directory / "error.json", {"error": "No existe main; no se probará otra rama."})
            return 1
        write_json(directory / "evidencia.json", {"repository": repository, "commit": "a" * 40})
        write_json(directory / "informe.json", {"estado": "completo", "celulas": []})
        (directory / "informe.md").write_text("# Informe de prueba\n", encoding="utf-8")
        return 0

    def request(self, path, body=None):
        request = Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                          headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, response.read(), response.headers

    def await_finished(self, job_id):
        self.release.set()
        for _ in range(100):
            data = self.jobs.detail(job_id)
            if data["estado"] not in {"preparando", "analizando"}:
                return data
            time.sleep(0.01)
        self.fail("La ejecución no terminó")

    def test_http_start_progress_reload_and_download(self):
        status, body, _ = self.request("/runs", {"repository": "https://github.com/acme/app"})
        self.assertEqual(status, 202)
        job = json.loads(body)
        self.assertEqual(self.jobs.detail(job["id"])["estado"], "preparando")
        done = self.await_finished(job["id"])
        self.assertEqual(done["estado"], "completo")
        status, content, headers = self.request(f"/runs/{job['id']}/download")
        self.assertEqual(status, 200)
        self.assertEqual(content, b"# Informe de prueba\n")
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertEqual(Jobs(self.root).detail(job["id"])["estado"], "completo")

    def test_parallel_request_rejected_without_second_job(self):
        first = self.jobs.start("https://github.com/acme/app")
        status, _, _ = self.request("/runs", {"repository": "https://github.com/acme/other"})
        self.assertEqual(status, 409)
        self.assertEqual(len(self.jobs.listing()), 1)
        self.await_finished(first["id"])

    def test_main_failure_is_visible(self):
        job = self.jobs.start("https://github.com/acme/missing")
        done = self.await_finished(job["id"])
        self.assertEqual(done["estado"], "error")
        self.assertIn("main", done["error"])
        self.assertFalse(done["has_report"])

    def test_url_with_branch_or_external_host_rejected(self):
        for url in ("https://github.com/acme/app/tree/dev", "https://example.com/app"):
            status, _, _ = self.request("/runs", {"repository": url})
            self.assertEqual(status, 400)
        self.assertEqual(self.jobs.listing(), [])

    def test_filesystem_and_credentials_are_not_exposed(self):
        for path in ("/runs/../../auth/auth.json", "/runs/valid-id/auth.json", "/env", "/runs/valid-id/download"):
            status, _, _ = self.request(path)
            self.assertIn(status, (400, 404))

    def test_restart_marks_unfinished_job_as_interrupted(self):
        directory = self.root / "unfinished-job"
        directory.mkdir()
        write_json(directory / "job.json", {"id": "unfinished-job", "estado": "analizando", "repository": "https://github.com/acme/app"})
        restored = Jobs(self.root)
        self.assertEqual(restored.detail("unfinished-job")["estado"], "error")
        self.assertIn("interrumpió", restored.detail("unfinished-job")["error"])

    def test_question_serializes_with_audits_and_survives_saved_result(self):
        fixture(self.root / "finished-job")
        created = self.jobs.detail("finished-job")["created"]
        before = (self.root / "finished-job/informe.md").read_bytes()
        def answer(context):
            self.release.wait(3)
            return {"respuesta": "Sin mediciones disponibles.", "certeza": "sin_informacion", "evidencia": []}
        self.jobs.answerer = answer
        status, body, _ = self.request("/runs/finished-job/questions", {"agent": "security", "question": "¿RAM?"})
        self.assertEqual(status, 202)
        query = json.loads(body)
        self.assertEqual(self.request("/runs", {"repository": "https://github.com/acme/app"})[0], 409)
        self.assertEqual(self.request("/runs/finished-job/questions", {"agent": "coordinator", "question": "Otra"})[0], 409)
        self.release.set()
        for _ in range(100):
            if self.jobs.question_active is None:
                break
            time.sleep(0.01)
        status, body, _ = self.request(f"/runs/finished-job/questions/{query['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["estado"], "completada")
        self.assertEqual(before, (self.root / "finished-job/informe.md").read_bytes())
        self.assertEqual(created, self.jobs.detail("finished-job")["created"])
        self.assertEqual(Jobs(self.root).question("finished-job", query["id"])["certeza"], "sin_informacion")

    def test_question_model_failure_is_visible_and_releases_slot(self):
        fixture(self.root / "finished-job")
        def failed(context):
            raise AuditError("Modelo no disponible; sin reintento.")
        self.jobs.answerer = failed
        query = self.jobs.ask("finished-job", "coordinator", "Explica")
        for _ in range(100):
            if self.jobs.question_active is None:
                break
            time.sleep(0.01)
        result = self.jobs.question("finished-job", query["id"])
        self.assertEqual(result["estado"], "error")
        self.assertIn("Modelo no disponible", result["error"])
        self.assertIsNone(self.jobs.question_active)

    def test_question_failed_cell_or_invalid_id_rejected(self):
        fixture(self.root / "finished-job")
        self.assertEqual(self.request("/runs/finished-job/questions", {"agent": "inventory", "question": "Explica"})[0], 400)
        self.assertEqual(self.request("/runs/finished-job/questions/../../auth")[0], 404)

    def test_cli_lock_prevents_model_call_for_question(self):
        fixture(self.root / "finished-job")
        calls = []
        self.jobs.answerer = lambda context: calls.append(1)
        with (self.root / ".audit.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            query = self.jobs.ask("finished-job", "security", "Explica")
            for _ in range(100):
                if self.jobs.question_active is None:
                    break
                time.sleep(0.01)
            self.assertEqual(self.jobs.question("finished-job", query["id"])["estado"], "error")
            self.assertEqual(calls, [])

    def test_restart_interrupts_saved_question_without_retry(self):
        fixture(self.root / "finished-job")
        query_id = "11223344-1122-1122-1122-112233445566"
        target = self.root / "finished-job/consultas"
        target.mkdir()
        write_json(target / (query_id + ".json"), {"id": query_id, "estado": "respondiendo"})
        restored = Jobs(self.root)
        self.assertEqual(restored.question("finished-job", query_id)["estado"], "error")
        self.assertIn("interrumpió", restored.question("finished-job", query_id)["error"])


if __name__ == "__main__":
    unittest.main()
