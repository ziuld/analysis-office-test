import copy
import json
import tempfile
import unittest
from pathlib import Path
from arktic_office.coordination.team import run_team, prepare_response, write_json
from test_team import snapshot, fake_invoke
from test_editorial import Links
from test_security import fixture
from arktic_office.core.outcome import INSUFFICIENT
from arktic_office.reporting.executive import render_html, render_markdown
from arktic_office.preparation.repository import AuditError
from arktic_office.api.server import Jobs


def insufficient():
    return {"schema_version": 3, "confirmados": [], "indicios": [], "dudas": [], "controles": [],
            "evaluacion": {"estado": INSUFFICIENT, "motivo": "Falta el controlador que procesa las solicitudes.", "necesita": ["Controlador y configuración de datos."]}}


class OutcomeTests(unittest.TestCase):
    def run_cells(self, invoke):
        with tempfile.TemporaryDirectory() as temp:
            return run_team(snapshot(), Path(temp), invoke=invoke, emit=lambda *a, **k: None)

    def test_insufficiency_is_terminal_without_retry_or_error(self):
        calls = []
        def invoke(prompt, config):
            calls.append(config["id"])
            return {"report": json.dumps(insufficient())}
        data = self.run_cells(invoke)
        self.assertEqual(calls, [c["id"] for c in __import__("arktic_office.coordination.team", fromlist=["CELLS"]).CELLS])
        self.assertEqual(data["estado"], INSUFFICIENT)
        self.assertTrue(all(c["estado"] == INSUFFICIENT and "error" not in c for c in data["celulas"]))
        self.assertIn("controlador", data["celulas"][0]["mensaje"])
        self.assertIn("Controlador y configuración de datos.", data["necesita"])

    def test_one_insufficient_cell_preserves_other_results(self):
        def invoke(prompt, config):
            return {"report": json.dumps(insufficient())} if config["id"] == "architecture" else fake_invoke(prompt, config)
        data = self.run_cells(invoke)
        self.assertEqual(data["estado"], "parcial")
        self.assertEqual(data["celulas"][1]["estado"], INSUFFICIENT)
        self.assertTrue(data["confirmados"])
        self.assertNotIn("error", data["celulas"][1])

    def test_no_selected_code_finishes_without_calling_models(self):
        with tempfile.TemporaryDirectory() as temp:
            value = snapshot()
            value["files"] = []
            data = run_team(value, Path(temp), invoke=lambda *args: self.fail("No model call expected"), emit=lambda *a, **k: None)
        self.assertEqual(data["estado"], INSUFFICIENT)
        self.assertTrue(all("error" not in c for c in data["celulas"]))

    def test_valid_contribution_is_retained_with_explicit_limit(self):
        def invoke(prompt, config):
            result = fake_invoke(prompt, config)
            report = json.loads(result["report"])
            report["evaluacion"] = insufficient()["evaluacion"]
            return {"report": json.dumps(report)}
        data = self.run_cells(invoke)
        self.assertEqual(data["estado"], "parcial")
        self.assertTrue(data["confirmados"])
        self.assertTrue(all(c["estado"] == "parcial" for c in data["celulas"]))

    def test_technical_failures_are_not_relabelled_as_insufficiency(self):
        def invoke(prompt, config):
            raise AuditError("Hermes: sesión no válida")
        data = self.run_cells(invoke)
        self.assertEqual(data["estado"], "sin_resultados")
        self.assertTrue(all(c["estado"] == "error" for c in data["celulas"]))

    def test_expert_diagram_is_preserved_without_editorial_rejection(self):
        def invoke(prompt, config):
            envelope = fake_invoke(prompt, config)
            if config["id"] == "architecture":
                report = json.loads(envelope["report"])
                report["presentacion"] = {
                    "flujo_actual": {"componentes": [{"id": "invalid-id", "nombre": "Servidor", "descripcion": "Arranque", "evidencia": ["F1:L1"]}], "conexiones": []},
                    "decision": {"propuesta": "Ampliar la lectura", "evidencia_pendiente": ["Configuración operativa"], "siguiente_paso": "Revisar configuración"}}
                envelope["report"] = json.dumps(report)
            return envelope
        data = self.run_cells(invoke)
        cell = data["celulas"][1]
        self.assertEqual(cell["estado"], "completada")
        self.assertNotIn("error", cell)
        self.assertFalse(cell.get("advertencias"))
        self.assertIn("decision", data["presentacion"])
        self.assertEqual(data["presentacion"]["flujo_actual"]["componentes"][0]["id"], "invalid-id")
        self.assertTrue(any("architecture" in x["celulas"] for x in data["confirmados"]))

    def test_sufficiency_does_not_bypass_citation_validation(self):
        data = insufficient()
        data["confirmados"] = [{"observacion": "Inventado", "evidencia": ["F99:L1"]}]
        with self.assertRaises(AuditError):
            prepare_response(json.dumps(data), snapshot())

    def test_api_exposes_terminal_insufficiency_and_report_without_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            job_id = "12345678-1234-1234-1234-123456789abc"
            directory = root / job_id
            directory.mkdir()
            write_json(directory / "job.json", {"id": job_id, "repository": "https://github.com/acme/app", "estado": "preparando"})
            def runner(*args):
                write_json(directory / "informe.json", {"estado": INSUFFICIENT, "mensaje": "Hace falta leer el controlador.", "necesita": ["Controlador"], "celulas": []})
                (directory / "informe.md").write_text("# Resultado\nLectura insuficiente", encoding="utf-8")
                return 0
            jobs = Jobs(root, runner=runner)
            jobs.work(job_id, "https://github.com/acme/app")
            result = jobs.detail(job_id)
            self.assertEqual(result["estado"], INSUFFICIENT)
            self.assertTrue(result["has_report"])
            self.assertNotIn("error", result)
            self.assertEqual(result["necesita"], ["Controlador"])

    def test_empty_report_is_a_useful_conclusion_not_empty_sections(self):
        data = self.run_cells(lambda *args: {"report": json.dumps(insufficient())})
        html = render_html(data, snapshot())
        md = render_markdown(data, snapshot())
        for result in (html, md):
            self.assertIn("No hay información validada suficiente", result)
            self.assertIn("Controlador y configuración de datos.", result)
            self.assertNotIn("Sin dato estructurado para este aspecto", result)
            self.assertNotIn("No se aportó una decisión", result)
        parser = Links()
        parser.feed(html)
        self.assertTrue(set(parser.targets) <= set(parser.ids))
        self.assertNotIn("azure", parser.ids)
        self.assertNotIn("continuidad", parser.ids)
        self.assertNotIn("### Inventario", md.split("## Aportaciones originales de los especialistas")[0])
        self.assertIn("## Aportaciones originales de los especialistas", md)
        self.assertNotIn("### Riesgos", md)

    def test_sparse_report_keeps_real_risk_sources_and_no_broken_navigation(self):
        snap, raw = fixture()
        data, _ = prepare_response(json.dumps(raw), snap)
        html = render_html(data, snap)
        parser = Links()
        parser.feed(html)
        self.assertIn("Entrada concatenada en consulta SQL", html)
        self.assertIn("R01", parser.ids)
        self.assertTrue(set(parser.targets) <= set(parser.ids))
        self.assertNotIn("azure", parser.ids)
        self.assertNotIn("flujo-fuentes", parser.ids)

    def test_purpose_hypothesis_requires_sources_and_is_identified(self):
        snap, raw = fixture()
        item = raw["confirmados"].pop()
        item.update(tema="proposito", severidad="informativa", control="contexto", por_confirmar="Confirmar alcance funcional.", observacion="Podría gestionar solicitudes de usuarios.")
        raw["indicios"] = [item]
        data, _ = prepare_response(json.dumps(raw), snap)
        for value in (render_html(data, snap), render_markdown(data, snap)):
            self.assertIn("Hipótesis por confirmar", value)
            self.assertIn("Podría gestionar", value)


if __name__ == "__main__":
    unittest.main()
