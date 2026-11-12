"""Exercise the approved task rollout without a live model."""
import json
import re
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from arktic_office.config.private_ai import require_private_ai
from arktic_office.coordination.initial_sources import select
from arktic_office.coordination.workflow import checkpoint_path, load_tasks
from arktic_office.coordination.team import CELLS, run_team
from arktic_office.core.errors import AuditError, SpecialistTimeout
from arktic_office.execution.budget import Budget
from arktic_office.preparation.credentials import CredentialProtection, PROTECTED
from arktic_office.preparation.evidence import Evidence
from arktic_office.reporting.questionnaire import catalog
from arktic_office.reporting.view import render_html, render_markdown
from arktic_office.resources.paths import resource_path
from test_questionnaire import fixture


class IndependentWorkflowsTests(unittest.TestCase):
    def test_packaged_cases_cover_the_catalog_and_reserved_rounds(self):
        tasks = []
        for profile in CELLS:
            role = profile["id"]
            specs = load_tasks(role=role)
            cases = tomllib.loads(resource_path("profiles", "agents", role, "evals", "casos.toml")
                                 .read_text(encoding="utf-8"))["cases"]
            self.assertEqual([(t["id"], t["questions"], t["reserved_rounds"]) for t in specs],
                             [(c["task"], c["questions"], c["rounds"]) for c in cases])
            tasks.extend(specs)
        self.assertEqual(len(tasks), 10)
        self.assertEqual(sum(t["reserved_rounds"] for t in tasks), 17)
        self.assertEqual({q for t in tasks for q in t["questions"]},
                         {q["id"] for q in catalog() if q["role"] != "coordinator"})

    def test_all_workflows_compose_40_questions_with_local_citations(self):
        snapshot, evidence = fixture()
        snapshot["request"].update(task_workflows="all", mode="deterministic")
        specs = {t["id"]: t for c in CELLS for t in load_tasks(role=c["id"])}
        captured = set()

        def invoke(message, config):
            task = config["task_id"]
            with self.subTest(task=task):
                captured.add(task)
                active = message.split("TAREA ACTIVA\n", 1)[1].split("FIN DE TAREA ACTIVA.", 1)[0]
                self.assertEqual([line.split()[1] for line in active.splitlines() if line.startswith("### Q")],
                                 specs[task]["questions"])
                sources = json.loads(message.split("FUENTES NO CONFIABLES: ", 1)[1].split("\nFIN DE FUENTES.", 1)[0])
                source = next((s for s in sources if s["path"] == "localizado.py"), None)
                if source is None:
                    return {"report": json.dumps({"comprobar": ["entrada"], "queries": [{"paths": ["localizado.py"]}]})}
                answers = [{"id": q, "estado": "respondida", "respuesta": "Respuesta de prueba.",
                            "evidencia": [source["id"] + ":L1"]} for q in specs[task]["questions"]]
                return {"report": json.dumps({"respuestas": answers, "cierre": "Evidencia localizada."})}

        evidence.files["localizado.py"] = {"path": "localizado.py", "text": "def localizado(): return True"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = run_team(snapshot, root, invoke=invoke, evidence=evidence, emit=lambda *a, **k: None)
            self.assertEqual(len(captured), 10)
            answers = report["cuestionario"]["respuestas"]
            self.assertEqual(len({a["id"] for a in answers}), 40)
            for answer in answers:
                if answer["role"] != "coordinator":
                    self.assertEqual(answer["evidencia"][0]["path"], "localizado.py")
            self.assertEqual(len(report["metrics"]["calls"]), 20)
            self.assertTrue(all(checkpoint_path(root, c["id"]).exists() for c in CELLS))
            expected = {q["id"] for q in catalog()}
            html = render_html(report, snapshot, "simulated")
            markdown = render_markdown(report, snapshot, "simulated")
            for ids in (re.findall(r'<article id="(Q\d{2})"', html), re.findall(r"^### (Q\d{2}) ·", markdown, re.M)):
                self.assertEqual(len(ids), 40)
                self.assertEqual(set(ids), expected)

    def test_shared_deadline_reserves_closure_time_for_both_tasks(self):
        snapshot, evidence = fixture()
        snapshot["request"].update(task_workflows="all", mode="deterministic")
        clock = SimpleNamespace(now=0, monotonic=lambda: clock.now)
        devops_calls = []

        def invoke(message, config):
            self.assertEqual(config["limits"]["seconds"], 300)
            payload = {"comprobar": ["punto"], "cierre": "Cerrado con la evidencia disponible."}
            if config["id"] == "devops":
                can_search = '"queries" admite hasta 4 consultas' in message
                devops_calls.append((config["task_id"], config["timeout"], can_search))
                if len(devops_calls) == 1:
                    clock.now += 55
                    payload["queries"] = [{"paths": ["app.py"]}]
                else:
                    clock.now += 1
            return {"report": json.dumps(payload)}

        with tempfile.TemporaryDirectory() as temp, patch("arktic_office.coordination.workflow.time", clock):
            run_team(snapshot, Path(temp), invoke=invoke, evidence=evidence, emit=lambda *a, **k: None)
        self.assertEqual(devops_calls, [
            ("construccion-arranque", 120, True),
            ("construccion-arranque", 155, False),
            ("pipeline-despliegue", 154, True),
        ])

    def test_local_deadline_preserves_partial_and_the_rest_of_the_team_runs(self):
        snapshot, evidence = fixture()
        snapshot["request"].update(task_workflows="all", mode="deterministic")
        inventory_task = load_tasks(role="inventory")[0]
        question = inventory_task["questions"][0]
        received = []

        def invoke(_, config):
            received.append(config["id"])
            payload = {"comprobar": ["punto"], "cierre": "Revisión acotada."}
            if config["id"] == "inventory":
                if received.count("inventory") > 1:
                    raise SpecialistTimeout("Se agotó el plazo local del especialista.")
                payload["respuestas"] = [{"id": question, "estado": "parcial",
                    "respuesta": "Detalle guardado antes del corte.", "pendiente": "Comprobar app.py."}]
                payload["queries"] = [{"paths": ["app.py"]}]
            return {"report": json.dumps(payload)}

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = run_team(snapshot, root, invoke=invoke, evidence=evidence, emit=lambda *a, **k: None)
            checkpoint = json.loads(checkpoint_path(root, "inventory").read_text(encoding="utf-8"))
        self.assertEqual(set(received), {cell["id"] for cell in CELLS})
        task = checkpoint["tasks"][0]
        self.assertEqual(task["status"], "interrumpida")
        self.assertEqual(task["answers"][0]["respuesta"], "Detalle guardado antes del corte.")
        self.assertIsNone(report["metrics"]["stop_reason"])
        interrupted = next(call for call in report["metrics"]["calls"] if call["status"] == "interrupted")
        self.assertEqual(interrupted["agent"], "inventory")
        self.assertEqual(interrupted["timeout_scope"], "specialist")
        self.assertEqual(interrupted["remote_outcome"], "unknown")
        self.assertIsNone(interrupted["usage"])

    def test_credential_protection_applies_to_wire_copy_and_not_to_lookup(self):
        source = 'password = "small-fictitious-password"\npassword = "ab"\nconnect("postgres://u:pw@db.example/test")'
        path = "src/config.py"
        evidence = Evidence([{"path": path, "text": source}], {})
        protection = CredentialProtection(evidence.files.values(), [{"name": "Gitleaks", "original_output": [
            {"Secret": "fictitious-unstructured-value"}]}])
        wire = json.dumps({"content": source, "note": "fictitious-unstructured-value"})
        received = []

        def invoke(message, _):
            received.append(json.loads(message))
            return {"report": '{"value":"small-fictitious-password"}'}

        with tempfile.TemporaryDirectory() as temp:
            budget = Budget(invoke, Path(temp), protection)
            self.assertEqual(json.loads(budget(wire, {"model": "fake"})["report"])["value"], PROTECTED)
        self.assertEqual(received[0]["content"].splitlines(), [
            f'password = "{PROTECTED}"', f'password = "{PROTECTED}"',
            f'connect("postgres://u:{PROTECTED}@db.example/test")'])
        self.assertEqual(received[0]["note"], PROTECTED)
        self.assertIn("small-fictitious-password", evidence.lookup({"query": "small-fictitious-password"})["fragments"][0]["text"])

    def test_ordinary_credential_terms_stay_readable_in_report_prose(self):
        protection = CredentialProtection([{"path": "example.py", "text": 'password = "clave API"'}])
        self.assertEqual(protection.protect("El pipeline necesita una clave API."), "El pipeline necesita una clave API.")
        self.assertEqual(protection.protect('password = "clave API"'), f'password = "{PROTECTED}"')

    def test_cited_ungraded_workflow_risk_appears_in_executive_summary(self):
        from arktic_office.reporting.executive import risks
        cited = {"titulo": "Adjunto sin análisis", "tipo": "vulnerabilidad", "severidad": "informativa",
                 "evidencia": [{"path": "mail.py", "line": 12, "quote": "send(attachment)"}]}
        result = risks({"task_workflows": "pilot", "confirmados": [cited, {**cited, "evidencia": []}]})
        self.assertEqual(result, [{**cited, "certeza": "confirmados"}])

    def test_pilot_keeps_other_specialists_on_the_previous_executor(self):
        snapshot, evidence = fixture()
        snapshot["request"].update(task_workflows="pilot", mode="deterministic")
        pilot = {"devops", "backend-security"}

        def invoke(message, config):
            if config["id"] in pilot:
                self.assertIn("task_id", config)
                self.assertIn("TAREA ACTIVA", message)
                if config["id"] == "devops":
                    rounds = {"construccion-arranque": 1, "pipeline-despliegue": 2}
                    self.assertIn(f'Quedan {rounds[config["task_id"]]} rondas asignadas', message)
            else:
                self.assertNotIn("task_id", config)
                if "app.py" in message and "CONSULTAS REALIZADAS:" not in message:
                    return {"report": json.dumps({"queries": [{"paths": ["app.py"]}]})}
            return {"report": json.dumps({"comprobar": ["punto"], "cierre": "Revisión acotada.",
                                          "observaciones": [], "respuestas": [], "pendientes": []})}

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_team(snapshot, root, invoke=invoke, evidence=evidence, emit=lambda *a, **k: None)
            self.assertEqual({c["id"] for c in CELLS if checkpoint_path(root, c["id"]).exists()}, pilot)

    def test_devops_pipeline_sources_include_stages_and_templates(self):
        _, task = load_tasks(role="devops")
        files = [
            {"path": "azure-pipelines.yml", "text": "# " + "preamble " * 250 + "\nstages:\n  - stage: BuildImages"},
            {"path": "pipelines/templates/release.yml", "text": "steps:\n  - script: publish"},
        ]
        selected, _ = select("devops", Evidence(files, {}), {"files": 200, "bytes": 600000},
                             with_groups=True, groups=task["source_groups"])
        self.assertEqual([file["path"] for file in selected], [file["path"] for file in files])
        self.assertEqual(selected[0]["start"], 2)
        self.assertIn("BuildImages", selected[0]["text"])

    def test_backend_security_seeds_verdict_and_both_consumers_together(self):
        _, task = load_tasks(role="backend-security")
        symbols = {"cv-scan": "cvScanVerdict", "notifyTalentTeam": "sendCvByEmail", "uploadCvs": "syncCvToOneDrive"}
        files = [{"path": f"src/{name}.ts",
                  "text": "// " + "preamble " * 250 + f"\nexport async function {symbol}() {{}}"}
                 for name, symbol in symbols.items()]
        selected, _ = select("backend-security", Evidence(files, {}), {"files": 200, "bytes": 600000},
                             with_groups=True, groups=task["source_groups"])
        self.assertEqual([file["path"] for file in selected], [file["path"] for file in files])
        for file, symbol in zip(selected, symbols.values()):
            self.assertEqual(file["start"], 2)
            self.assertIn(f"function {symbol}", file["text"])

    def test_real_execution_requires_operator_confirmation(self):
        from arktic_office.cli import run
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(AuditError, "IA privado"):
                require_private_ai()
            with self.assertRaisesRegex(AuditError, "IA privado"):
                run("https://github.com/example/private")
            require_private_ai(True)
