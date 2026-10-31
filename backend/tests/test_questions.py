import json
import tempfile
import unittest
from pathlib import Path

from arktic_office.coordination.questions import prepare_question, answer_question
from arktic_office.preparation.repository import AuditError
from arktic_office.coordination.team import write_json


def fixture(root):
    root.mkdir(exist_ok=True)
    (root / "celulas").mkdir(exist_ok=True)
    write_json(root / "evidencia.json", {"repository": "https://github.com/acme/app", "commit": "a" * 40, "files": [
        {"path": "auth.js", "text": "const protectedRoute = true;\n"},
        {"path": "package.json", "text": '{"private":true}\n'},
    ]})
    report = {"confirmados": [{"observacion": "Ruta protegida declarada", "evidencia": [
        {"path": "auth.js", "line": 1, "quote": "const protectedRoute = true;"}]}], "indicios": [], "dudas": []}
    write_json(root / "informe.json", {**report, "estado": "parcial", "celulas": []})
    (root / "informe.md").write_text("# Informe original\n")
    write_json(root / "celulas/security.json", {"estado": "completada", "archivos": ["auth.js"], "resultado": report})
    write_json(root / "celulas/inventory.json", {"estado": "error"})


class QuestionTests(unittest.TestCase):
    def test_simulation_is_rejected_before_preparing_model_context(self):
        snapshot = json.loads((self.root / "evidencia.json").read_text())
        snapshot["simulation"] = True
        write_json(self.root / "evidencia.json", snapshot)
        with self.assertRaisesRegex(AuditError, "simulación"):
            prepare_question(self.root, "security", "Explica")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)

    def test_cell_only_receives_its_evidence(self):
        context = prepare_question(self.root, "security", "¿Qué se declara?")
        self.assertEqual([f["path"] for f in context["evidence"]], ["auth.js"])
        self.assertEqual(context["commit"], "a" * 40)

    def test_coordinator_uses_consolidated_sources_only(self):
        context = prepare_question(self.root, "coordinator", "Resume")
        self.assertEqual([f["path"] for f in context["evidence"]], ["auth.js"])
        self.assertIn("dudas", context["result"])

    def test_valid_citation_resolved_and_original_unchanged(self):
        context = prepare_question(self.root, "security", "¿Está declarado?")
        original = (self.root / "informe.json").read_bytes()
        calls = []
        def invoke(prompt, config):
            calls.append(config)
            return {"report": json.dumps({"respuesta": "Se declara la protección, no se ha ejecutado.", "certeza": "explicacion", "evidencia": ["F1:L1"]}), "usage": {"api_calls": 1}}
        result = answer_question(context, invoke)
        self.assertEqual(result["evidencia"][0]["path"], "auth.js")
        self.assertEqual(len(calls), 1)
        self.assertEqual(original, (self.root / "informe.json").read_bytes())

    def test_unknown_information_can_answer_without_citations(self):
        context = prepare_question(self.root, "security", "¿Cuánta RAM consume?")
        result = answer_question(context, lambda *a: {"report": json.dumps({"respuesta": "No hay mediciones en esta revisión.", "certeza": "sin_informacion", "evidencia": []})})
        self.assertEqual(result["certeza"], "sin_informacion")

    def test_unlocated_reference_does_not_reject_followup_answer(self):
        context = prepare_question(self.root, "security", "Explica")
        for refs in ([], ["F2:L1"], ["F1:L100"]):
            result = answer_question(context, lambda *a: {"report": json.dumps({"respuesta": "Respuesta", "certeza": "explicacion", "evidencia": refs})})
            self.assertEqual(result["respuesta"], "Respuesta")
            self.assertEqual(result["certeza"], "explicacion")
            self.assertEqual(result["referencias_originales"], refs)

    def test_failed_cell_and_invalid_questions_do_not_call_model(self):
        for agent, question in (("inventory", "Explica"), ("invalid", "Explica"), ("security", " "), ("security", "a" * 801)):
            with self.assertRaises(AuditError):
                prepare_question(self.root, agent, question)

    def test_model_failure_propagated_without_retry(self):
        calls = []
        def failed(*args):
            calls.append(1)
            raise AuditError("Hermes no completó la célula. Sin reintento automático.")
        with self.assertRaises(AuditError):
            answer_question(prepare_question(self.root, "security", "Explica"), failed)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
