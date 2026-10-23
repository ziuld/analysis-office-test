import copy
import json
import tempfile
import unittest
from pathlib import Path
from arktic_office.preparation.repository import AuditError
from arktic_office.coordination.team import CELLS, prepare_response, consolidate, run_team
from arktic_office.reporting.reports import make_prompt, markdown
from arktic_office.reporting.executive import render_html, risks
from arktic_office.coordination.questions import prepare_question
from test_team import snapshot, fake_invoke
from test_questions import fixture as question_fixture


def proposal():
    return {"estado": "propuesta_preliminar", "destino": "app_service", "resumen": "Alojar la API en App Service, sujeto a validar su arranque.",
            "justificacion": "El Dockerfile declara un servidor Node; no necesita un clúster propio por lo observado.", "evidencia": ["F1:L1"],
            "supuestos": ["La aplicación puede ejecutarse sin almacenar datos dentro del contenedor."],
            "servicios": [{"servicio": "Azure App Service", "uso": "Alojar el contenedor web."}],
            "pasos": ["Construir un artefacto versionado, validar en pruebas y aprobar antes de publicar."],
            "pendientes": ["Confirmar persistencia, configuración de acceso y restauración."]}


def report():
    return {"schema_version": 3, "confirmados": [], "indicios": [], "dudas": [], "controles": [], "propuesta_azure": proposal()}


class AzureProposalTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        self.enterContext(patch.dict("os.environ", {"AUDIT_CAPABILITIES": "azure"}))

    def test_only_architecture_receives_the_profile(self):
        for cell in CELLS:
            self.assertEqual("# Propuesta DevOps Azure" in make_prompt(snapshot(), {**cell, "capabilities": ["azure"]}), cell["id"] == "architecture")

    def test_proposal_citations_are_resolved_without_becoming_findings(self):
        valid, _ = prepare_response(json.dumps(report()), snapshot())
        self.assertEqual(valid["propuesta_azure"]["evidencia"][0]["path"], "Dockerfile")
        combined = consolidate([("architecture", valid)], [{"id": "architecture", "estado": "completada"}])
        self.assertIn("propuesta_azure", combined)
        self.assertEqual(risks(combined), [])

    def test_non_architecture_proposal_is_not_consolidated(self):
        valid, _ = prepare_response(json.dumps(report()), snapshot())
        combined = consolidate([("security", valid)], [])
        self.assertNotIn("propuesta_azure", combined)

    def test_invalid_or_missing_basis_is_rejected(self):
        for ref in (["F99:L1"], [], [{"path": "Dockerfile", "line": 1, "quote": "invented"}]):
            data = report()
            data["propuesta_azure"]["evidencia"] = ref
            with self.assertRaises(AuditError):
                prepare_response(json.dumps(data), snapshot())

    def test_unbounded_or_wrong_shape_proposals_fail_validation(self):
        for field, value in (("destino", []), ("servicios", [{"servicio": "X", "uso": "Y"}] * 6), ("pasos", ["x"] * 6), ("supuestos", "not a list")):
            data = report()
            data["propuesta_azure"][field] = value
            with self.assertRaises(AuditError):
                prepare_response(json.dumps(data), snapshot())

    def test_insufficient_information_has_no_recommended_resources(self):
        data = report()
        data["propuesta_azure"].update(estado="informacion_insuficiente", destino="por_definir", evidencia=[], servicios=[], pasos=[])
        valid, _ = prepare_response(json.dumps(data), snapshot())
        self.assertNotIn("### Arquitectura propuesta en Azure", markdown(valid, snapshot(), "test"))
        self.assertEqual(valid["propuesta_azure"]["destino"], "por_definir")
        data["propuesta_azure"]["servicios"] = [{"servicio": "AKS", "uso": "Crear clúster"}]
        with self.assertRaises(AuditError):
            prepare_response(json.dumps(data), snapshot())

    def test_markdown_and_html_explain_recommendation_and_escape_text(self):
        data = report()
        data["propuesta_azure"]["resumen"] = "<script>alert(1)</script>"
        valid, _ = prepare_response(json.dumps(data), snapshot())
        md = markdown(valid, snapshot(), "test")
        self.assertIn("### Arquitectura propuesta en Azure", md)
        self.assertIn("Recomendación preliminar", md)
        self.assertIn("/blob/" + "a" * 40 + "/Dockerfile#L1", md)
        html = render_html(valid, snapshot())
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn('href="https://learn.microsoft.com/', html)

    def test_old_format_three_reports_remain_readable_without_new_claims(self):
        old = report()
        old.pop("propuesta_azure")
        valid, _ = prepare_response(json.dumps(old), snapshot())
        self.assertNotIn("### Arquitectura propuesta en Azure", markdown(valid, snapshot(), "test"))
        self.assertIn("Resultado y siguiente paso", markdown(valid, snapshot(), "test"))

    def test_coordinator_can_explain_proposal_with_its_original_basis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            question_fixture(root)
            p = proposal()
            p["evidencia"] = [{"path": "package.json", "line": 1, "quote": '{"private":true}'}]
            path = root / "informe.json"
            data = json.loads(path.read_text())
            data["propuesta_azure"] = p
            path.write_text(json.dumps(data))
            context = prepare_question(root, "coordinator", "¿Por qué esa opción Azure?")
            self.assertEqual(context["result"]["propuesta_azure"], p)
            self.assertIn("package.json", [f["path"] for f in context["evidence"]])

    def test_missing_architecture_proposal_keeps_other_cells_and_no_extra_call(self):
        calls = []
        def invoke(prompt, config):
            calls.append(config["id"])
            envelope = fake_invoke(prompt, config)
            if config["id"] == "architecture":
                data = json.loads(envelope["report"])
                data.pop("propuesta_azure")
                envelope["report"] = json.dumps(data)
            return envelope
        with tempfile.TemporaryDirectory() as temp:
            data = run_team(snapshot(), Path(temp), invoke, emit=lambda *a, **k: None)
        self.assertEqual(calls, ["security", "architecture", "inventory"])
        self.assertEqual(data["estado"], "parcial")
        self.assertNotIn("propuesta_azure", data)
        self.assertEqual(data["celulas"][1]["estado"], "parcial")
        self.assertTrue(any("architecture" in x["celulas"] for x in data["confirmados"]))

    def test_invalid_azure_keeps_valid_core_without_retry(self):
        calls = []
        def invoke(prompt, config):
            calls.append(config["id"])
            envelope = fake_invoke(prompt, config)
            if config["id"] == "architecture":
                value = json.loads(envelope["report"])
                value["propuesta_azure"] = proposal()
                value["propuesta_azure"]["evidencia"] = ["F99:L1"]
                envelope["report"] = json.dumps(value)
            return envelope
        with tempfile.TemporaryDirectory() as temp:
            data = run_team(snapshot(), Path(temp), invoke, emit=lambda *a, **k: None)
            saved = json.loads((Path(temp) / "celulas/architecture.json").read_text())
        self.assertEqual(calls, ["security", "architecture", "inventory"])
        self.assertEqual(data["estado"], "parcial")
        self.assertEqual(saved["estado"], "parcial")
        self.assertIn("resultado", saved)
        self.assertNotIn("propuesta_azure", saved["resultado"])
        self.assertIn("No se reintentó", saved["mensaje"])
        self.assertNotIn("error", saved)

    def test_bad_core_is_not_rescued_by_omitting_azure(self):
        def invoke(prompt, config):
            envelope = fake_invoke(prompt, config)
            if config["id"] == "architecture":
                value = json.loads(envelope["report"])
                value["confirmados"][0]["evidencia"] = ["F99:L1"]
                value["propuesta_azure"] = {}
                envelope["report"] = json.dumps(value)
            return envelope
        with tempfile.TemporaryDirectory() as temp:
            data = run_team(snapshot(), Path(temp), invoke, emit=lambda *a, **k: None)
        self.assertEqual(data["celulas"][1]["estado"], "error")
        self.assertFalse(any("architecture" in x["celulas"] for x in data["confirmados"]))


if __name__ == "__main__":
    unittest.main()
