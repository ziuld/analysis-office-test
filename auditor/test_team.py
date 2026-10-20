import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reporting import make_prompt
from repository import AuditError
from team import CELLS, cell_config, consolidate, plan_cells, prepare_response, run_team


def snapshot():
    return {"repository": "https://github.com/acme/app", "commit": "a" * 40,
            "bytes_read": 100, "excluded": [], "files": [
                {"path": "Dockerfile", "text": "FROM node:22\nCMD node server.js"},
                {"path": "package.json", "text": '{"dependencies":{"express":"5.0.0"}}'},
                {"path": "auth.py", "text": "require_login = True"},
                {"path": "server.js", "text": "listen(3000)"}]}


def observation(text, path="Dockerfile", line=1, quote="FROM node:22"):
    return {"observacion": text, "evidencia": [{"path": path, "line": line, "quote": quote}]}


def report(item):
    return {"confirmados": [item], "indicios": [], "dudas": []}


def fake_invoke(prompt, config):
    file = config["files"][0]
    data = report(observation(config["name"] + " observó el archivo.", file["path"], 1, file["text"].splitlines()[0]))
    data["schema_version"] = 2
    data["confirmados"][0].update(tema="arranque", importancia="Permite identificar el arranque declarado.", pendiente="Comprobar el entorno real.")
    return {"report": json.dumps(data), "usage": {"total_tokens": 50}}


class TeamTests(unittest.TestCase):
    def test_gradle_manifests_and_java_entrypoint_are_routed(self):
        value = snapshot()
        value["branch"] = "master"
        value["files"] = [{"path": "build.gradle", "text": "plugins {}"},
                          {"path": "settings.gradle", "text": "rootProject.name = 'booking'"},
                          {"path": "src/main/java/com/example/Application.java", "text": "class Application {}"}]
        plan = {c["id"]: [f["path"] for f in c["files"]] for c in plan_cells(value)}
        self.assertIn("build.gradle", plan["inventory"])
        self.assertIn("settings.gradle", plan["inventory"])
        self.assertIn(value["files"][2]["path"], plan["architecture"])
        self.assertIn("Rama revisada: master", make_prompt(value))

    def test_reference_ids_are_resolved_only_from_sent_evidence(self):
        value = {"confirmados": [{"observacion": "Declara Node", "evidencia": ["F1:L1"]}], "indicios": [], "dudas": []}
        data, omitted = prepare_response(json.dumps(value), snapshot())
        self.assertEqual(data["confirmados"][0]["evidencia"][0], {"path": "Dockerfile", "line": 1, "quote": "FROM node:22"})
        value["confirmados"][0]["evidencia"] = ["F9:L999"]
        with self.assertRaises(AuditError):
            prepare_response(json.dumps(value), snapshot())

    def test_excess_observations_are_limited_and_counted(self):
        value = {"confirmados": [observation("A"), observation("B"), observation("C")], "indicios": [], "dudas": ["A", "B", "C"]}
        data, omitted = prepare_response(json.dumps(value), snapshot())
        self.assertEqual(len(data["confirmados"]), 2)
        self.assertEqual(omitted, {"confirmados": 1, "indicios": 0, "dudas": 1, "referencias": 0})

    def test_reference_budget_does_not_reject_otherwise_valid_evidence(self):
        value = {"confirmados": [{"observacion": "Declara Node", "evidencia": ["F1:L1", "F1:L2", "F2:L1", "F3:L1"]}], "indicios": [], "dudas": []}
        data, omitted = prepare_response(json.dumps(value), snapshot())
        self.assertEqual(len(data["confirmados"][0]["evidencia"]), 3)
        self.assertEqual(omitted["referencias"], 1)

    def test_routing_limits_and_inventory_scope(self):
        value = snapshot()
        value["files"] += [{"path": f"config{i}.yaml", "text": "x" * 12000} for i in range(10)]
        plan = plan_cells(value)
        for cell in plan:
            self.assertLessEqual(len(cell["files"]), 6)
            self.assertLessEqual(cell["bytes"], 24000)
        inventory = next(c for c in plan if c["id"] == "inventory")
        self.assertNotIn("auth.py", [f["path"] for f in inventory["files"]])
        security = next(c for c in plan if c["id"] == "security")
        self.assertEqual(security["files"][0]["path"], "auth.py")

    def test_three_cells_produce_a_single_complete_report(self):
        calls = []
        def invoke(prompt, config):
            calls.append(config["id"])
            return fake_invoke(prompt, config)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            data = run_team(snapshot(), path, invoke=invoke, emit=lambda *a, **k: None)
            self.assertEqual(calls, [c["id"] for c in CELLS])
            self.assertEqual(data["estado"], "completo")
            self.assertEqual(len(data["confirmados"]), 3)
            self.assertEqual(json.loads((path / "estado.json").read_text())["estado"], "completo")
            self.assertEqual(len(list((path / "celulas").glob("*.json"))), 3)

    def test_cell_failure_preserves_other_results_without_retry(self):
        calls = []
        def invoke(prompt, config):
            calls.append(config["id"])
            if config["id"] == "architecture":
                raise AuditError("Fallo de prueba, sin proveedor real")
            return fake_invoke(prompt, config)
        with tempfile.TemporaryDirectory() as temp:
            data = run_team(snapshot(), Path(temp), invoke=invoke, emit=lambda *a, **k: None)
        self.assertEqual(calls, ["security", "architecture", "inventory"])
        self.assertEqual(data["estado"], "parcial")
        self.assertEqual(len(data["confirmados"]), 2)
        self.assertEqual(data["celulas"][1]["estado"], "error")

    def test_cell_cannot_cite_unseen_global_file(self):
        def invoke(prompt, config):
            if config["id"] == "inventory":
                return {"report": json.dumps(report(observation("Inventado", "auth.py", 1, "require_login = True")))}
            return fake_invoke(prompt, config)
        with tempfile.TemporaryDirectory() as temp:
            data = run_team(snapshot(), Path(temp), invoke=invoke, emit=lambda *a, **k: None)
        self.assertEqual(data["estado"], "parcial")
        self.assertEqual(data["celulas"][2]["estado"], "error")
        self.assertFalse(any(x["observacion"] == "Inventado" for x in data["confirmados"]))

    def test_empty_inventory_skips_model_and_marks_partial(self):
        value = snapshot()
        value["files"] = [f for f in value["files"] if f["path"] == "server.js"]
        calls = []
        def invoke(prompt, config):
            calls.append(config["id"])
            return fake_invoke(prompt, config)
        with tempfile.TemporaryDirectory() as temp:
            data = run_team(value, Path(temp), invoke=invoke, emit=lambda *a, **k: None)
        self.assertNotIn("inventory", calls)
        self.assertEqual(data["estado"], "parcial")
        self.assertEqual(data["celulas"][2]["estado"], "sin_evidencia")

    def test_duplicates_keep_origins_and_uncertainty_is_not_promoted(self):
        first = report(observation("Declara Node."))
        second = {"confirmados": [], "indicios": [{**observation("declara node"), "por_confirmar": "Verificar entorno real"}], "dudas": []}
        cells = [{"id": "security", "estado": "completada"}, {"id": "inventory", "estado": "completada"}]
        data = consolidate([("security", first), ("inventory", second)], cells)
        self.assertEqual(data["confirmados"], [])
        self.assertEqual(len(data["indicios"]), 1)
        self.assertEqual(data["indicios"][0]["celulas"], ["security", "inventory"])
        self.assertIn("discrepan", data["indicios"][0]["por_confirmar"])

    def test_adjusting_one_cell_does_not_raise_others(self):
        with patch.dict(os.environ, {"AUDIT_MODEL": "gpt-6-luna", "AUDIT_REASONING": "low", "AUDIT_ARCHITECTURE_REASONING": "medium"}):
            self.assertEqual(cell_config(CELLS[0])["reasoning"], "low")
            self.assertEqual(cell_config(CELLS[1])["reasoning"], "medium")
            self.assertEqual(cell_config(CELLS[2])["reasoning"], "low")


if __name__ == "__main__":
    unittest.main()
