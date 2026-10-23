"""Budget, evidence and optional-capability boundaries; all invocations are fake."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from arktic_office.coordination.team import run_team, plan_cells
from arktic_office.core.errors import AuditError
from arktic_office.reporting.executive import render_html, render_markdown
from test_team import snapshot, fake_invoke


class CoordinatorTests(unittest.TestCase):
    def test_invalid_configuration_spends_no_calls(self):
        for settings in ({"AUDIT_INVENTORY_MODEL": "invalid model"},
                         {"AUDIT_ARCHITECTURE_REASONING": "invalid"},
                         {"AUDIT_COORDINATION_MODE": "invalid"}, {"AUDIT_CAPABILITIES": "unknown"}):
            with self.subTest(settings=settings), patch.dict("os.environ", settings), tempfile.TemporaryDirectory() as temp:
                with self.assertRaises(AuditError):
                    run_team(snapshot(), Path(temp), invoke=lambda *a: self.fail("Unexpected call"))

    def test_ai_routes_once_synthesizes_and_preserves_originals_without_azure(self):
        with patch.dict("os.environ", {"AUDIT_COORDINATION_MODE": "ai", "AUDIT_CAPABILITIES": ""}):
            plan = plan_cells(snapshot())
            calls = []
            def invoke(prompt, config):
                calls.append(config["id"])
                if config["id"] == "coordinator-routing":
                    return {"report": json.dumps({c["id"]: [f["path"] for f in c["files"]] for c in plan})}
                if config["id"] == "coordinator-synthesis":
                    return {"report": json.dumps({"resumen": [{"texto": "Arranque declarado; entorno pendiente <script>",
                        "aportaciones": ["architecture:confirmados:0"]}]}), "usage": {"total_tokens": 15}}
                if config["id"] == "architecture":
                    self.assertNotIn("# Propuesta DevOps Azure", prompt)
                    self.assertNotIn("Azure: una opción", prompt)
                    envelope = fake_invoke(prompt, config)
                    value = json.loads(envelope["report"])
                    value.pop("propuesta_azure")
                    envelope["report"] = json.dumps(value)
                    return envelope
                return fake_invoke(prompt, config)
            with tempfile.TemporaryDirectory() as temp:
                data = run_team(snapshot(), Path(temp), invoke, emit=lambda *a, **k: None)
                self.assertEqual(calls, ["coordinator-routing", "security", "architecture", "inventory", "coordinator-synthesis"])
                self.assertEqual(data["estado"], "completo")
                self.assertEqual(len(data["confirmados"]), 3)
                self.assertNotIn("propuesta_azure", data)
                self.assertEqual(data["sintesis"][0]["evidencia"], data["confirmados"][1]["evidencia"])
                self.assertIn("Síntesis del coordinador", render_markdown(data, snapshot()))
                html = render_html(data, snapshot())
                self.assertIn("&lt;script&gt;", html)
                saved = json.loads((Path(temp) / "coordinacion.json").read_text())
                self.assertEqual(saved["stages"]["synthesis"]["usage"]["total_tokens"], 15)

    def test_coordinator_errors_and_one_specialist_failure_keep_valid_cells_without_retry(self):
        calls = []
        def invoke(prompt, config):
            calls.append(config["id"])
            if config["id"] == "coordinator-routing":
                return {"report": '{"security":["invented.py"],"architecture":[],"inventory":[]}'}
            if config["id"] == "coordinator-synthesis":
                return {"report": '{"resumen":[{"texto":"inventado","aportaciones":["missing"]}]}'}
            if config["id"] == "security":
                raise AuditError("fallo simulado")
            return fake_invoke(prompt, config)
        with patch.dict("os.environ", {"AUDIT_COORDINATION_MODE": "ai", "AUDIT_CAPABILITIES": ""}), tempfile.TemporaryDirectory() as temp:
            data = run_team(snapshot(), Path(temp), invoke, emit=lambda *a, **k: None)
            self.assertEqual(len(calls), 5)
            self.assertEqual(data["estado"], "parcial")
            self.assertEqual(len(data["confirmados"]), 2)
            self.assertEqual(data["sintesis"], [])
            self.assertEqual(data["coordination"]["stages"]["routing"]["fallback"], "deterministic")
            self.assertTrue((Path(temp) / "celulas/architecture.json").is_file())
