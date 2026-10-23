import copy
import json
import tempfile
import unittest
from pathlib import Path

from reporting import markdown, validate_report
from team import prepare_response, consolidate
from preview import preview
from repository import AuditError
from test_team import snapshot, fake_invoke
from test_questions import fixture


def result():
    return {"schema_version": 2, "confirmados": [{"tema": "componentes", "observacion": "El Dockerfile declara Node 22.",
        "importancia": "Identifica el entorno declarado del servidor.", "pendiente": "Confirmar el arranque real.",
        "componente": {"nombre": "Entorno de servidor", "tecnologia": "Node 22", "funcion": "Ejecutar el servidor declarado"},
        "evidencia": ["F1:L1"]}], "indicios": [], "dudas": ["¿Dónde se guardan los datos reales?"]}


class BriefTests(unittest.TestCase):
    def test_version2_requires_implication_pending_and_valid_topic(self):
        valid = result()
        data, _ = prepare_response(json.dumps(valid), snapshot())
        self.assertEqual(data["schema_version"], 2)
        for mutate in (lambda x: x["confirmados"][0].pop("importancia"),
                       lambda x: x["confirmados"][0].update(tema=["datos"]),
                       lambda x: x["confirmados"][0].update(pendiente=""),
                       lambda x: x.update(schema_version=True),
                       lambda x: x["confirmados"][0]["componente"].update(tecnologia=7)):
            bad = copy.deepcopy(valid)
            mutate(bad)
            with self.assertRaises(AuditError):
                prepare_response(json.dumps(bad), snapshot())

    def test_six_sections_link_to_exact_commit_and_keep_complete_quotes_out_of_brief(self):
        data, _ = prepare_response(json.dumps(result()), snapshot())
        data = consolidate([("inventory", data)], [{"id": "inventory", "nombre": "Inventario", "estado": "completada"}])
        rendered = markdown(data, snapshot(), "test")
        for title in ("1. Resumen", "2. Cómo", "3. Puntos", "4. Estabilidad", "5. Implicaciones", "6. Alcance"):
            self.assertIn("## " + title, rendered)
        self.assertIn("https://github.com/acme/app/blob/" + "a" * 40 + "/Dockerfile#L1", rendered)
        self.assertNotIn("FROM node:22", rendered)
        self.assertIn("No determinado en esta revisión", rendered)
        self.assertIn("Propósito documentado:** No determinado", rendered)

    def test_clues_are_not_used_as_confirmed_components_or_executive_facts(self):
        value = result()
        value["indicios"] = value["confirmados"]
        value["confirmados"] = []
        value["indicios"][0]["por_confirmar"] = "Verificar el entorno."
        data, _ = prepare_response(json.dumps(value), snapshot())
        data = consolidate([("inventory", data)], [{"id": "inventory", "nombre": "Inventario", "estado": "completada"}])
        rendered = markdown(data, snapshot(), "test")
        self.assertNotIn("| Entorno de servidor |", rendered)
        self.assertNotIn("- **Confirmado:** El Dockerfile", rendered)

    def test_partial_report_is_explicit_and_does_not_hide_failed_cell(self):
        value = {"schema_version": 2, "estado": "sin_resultados", "confirmados": [], "indicios": [], "dudas": [],
                 "celulas": [{"id": "security", "nombre": "Seguridad", "estado": "error", "error": "Modelo no disponible"}]}
        rendered = markdown(value, snapshot(), "test")
        self.assertIn("Revisión parcial", rendered)
        self.assertIn("Seguridad: falló", rendered)
        self.assertIn("Modelo no disponible", rendered)
        self.assertIn("no acredita ausencia de riesgos", rendered)

    def test_model_markdown_cannot_create_new_headings_or_break_table(self):
        value = result()
        value["confirmados"][0]["componente"]["nombre"] = "Servidor | falso\n## Seguro"
        data, _ = prepare_response(json.dumps(value), snapshot())
        rendered = markdown({**data, "estado": "completo"}, snapshot(), "test")
        self.assertNotIn("\n## Seguro", rendered)
        self.assertIn(r"Servidor \| falso \#\# Seguro", rendered)

    def test_legacy_reports_remain_readable_without_forced_new_claims(self):
        old = {"confirmados": [], "indicios": [], "dudas": []}
        self.assertEqual(validate_report(json.dumps(old), snapshot()), old)
        self.assertIn("# Revisión preliminar", markdown(old, snapshot(), "old-model"))

    def test_preview_preserves_source_and_marks_saved_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture(root / "source-test")
            original = {name: (root / "source-test" / name).read_bytes() for name in ("evidencia.json", "informe.json", "informe.md")}
            calls = []
            def invoke(prompt, config):
                calls.append(config["id"])
                return fake_invoke(prompt, config)
            output, data = preview("source-test", root, invoke)
            self.assertEqual(calls, ["security", "architecture", "inventory"])
            self.assertEqual(data["schema_version"], 3)
            self.assertIn("GitHub no se ha releído", (output / "informe.md").read_text())
            for name, content in original.items():
                self.assertEqual((root / "source-test" / name).read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
