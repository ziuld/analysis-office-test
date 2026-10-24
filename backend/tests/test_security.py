import copy
import json
import unittest
from pathlib import Path
from arktic_office.preparation.repository import AuditError, excerpt, priority
from arktic_office.reporting.security import CONTROLS
from arktic_office.coordination.team import prepare_response, consolidate
from arktic_office.reporting.reports import evidence_index, make_prompt
from arktic_office.reporting.executive import render_html, render_markdown
from arktic_office.adapters.scanners import scan


def fixture():
    snapshot = {"repository": "https://github.com/acme/demo", "commit": "a" * 40, "files": [{"path": "routes.py", "text": "db.execute('SELECT * FROM users WHERE id=' + request.args['id'])\nrequire_permission(user, 'admin')"}], "excluded": [], "bytes_read": 130}
    item = {"tema": "acceso", "observacion": "Entrada concatenada en consulta SQL", "importancia": "Puede alterar la consulta.", "pendiente": "Verificar alcance y protección de la ruta.", "evidencia": ["F1:L1"], "severidad": "alta", "control": "entradas", "accion": "Parametrizar la consulta.", "condiciones": "Requiere entrada controlada por el solicitante."}
    data = {"schema_version": 3, "confirmados": [item], "indicios": [], "dudas": [], "controles": [{"id": k, "estado": "no_evaluado", "motivo": "Falta contexto.", "evidencia": []} for k in CONTROLS]}
    return snapshot, data


class SecurityTests(unittest.TestCase):
    def test_large_file_preserves_exact_line_numbers(self):
        source = "\n".join(["# ordinary padding" * 10] * 400 + ["db.execute(request.query)"] + ["# tail" * 20] * 50)
        selected, partial = excerpt(source)
        self.assertTrue(partial)
        self.assertLessEqual(len(selected.encode()), 12000)
        self.assertEqual(selected.splitlines()[400], "db.execute(request.query)")
        self.assertEqual(evidence_index({"files": [{"path": "service.py", "text": selected}]})["F1:L401"]["quote"], "db.execute(request.query)")

    def test_security_entrypoints_precede_generic_source(self):
        self.assertLess(priority("src/GuestController.java"), priority("src/aaa/BaseModel.java"))
        self.assertLess(priority("package-lock.json"), 9)

    def test_profile_actually_enters_security_prompt(self):
        from arktic_office.coordination.team import CELLS
        s, _ = fixture()
        self.assertIn("Perfil de revisión de seguridad", make_prompt(s, CELLS[0]))
        self.assertNotIn("Perfil de revisión de seguridad", make_prompt(s, CELLS[2]))

    def test_risks_are_not_truncated_at_old_two_item_limit(self):
        s, d = fixture()
        d["confirmados"] *= 5
        valid, omitted = prepare_response(json.dumps(d), s)
        self.assertEqual(len(valid["confirmados"]), 5)
        self.assertEqual(omitted["confirmados"], 0)
        d["confirmados"] *= 3
        with self.assertRaises(AuditError):
            prepare_response(json.dumps(d), s)

    def test_severity_and_coverage_reject_false_certainty(self):
        s, d = fixture()
        d["controles"][0].update(estado="evidencia_favorable_limitada")
        with self.assertRaises(AuditError):
            prepare_response(json.dumps(d), s)
        d["controles"][0]["evidencia"] = ["F1:L2"]
        prepare_response(json.dumps(d), s)
        d["confirmados"][0]["severidad"] = "seguro"
        with self.assertRaises(AuditError):
            prepare_response(json.dumps(d), s)

    def test_wrong_enum_types_fail_as_validation_errors(self):
        s, d = fixture()
        d["confirmados"][0]["control"] = []
        with self.assertRaises(AuditError):
            prepare_response(json.dumps(d), s)

    def test_safe_runtime_errors_never_return_provider_text(self):
        from arktic_office.adapters.hermes_runtime import failure_code
        self.assertEqual(failure_code("401 unauthorized secret-value"), "authentication")
        self.assertEqual(failure_code("arbitrary secret-value"), "incomplete_response")
        error = RuntimeError("No stored session")
        error.code = "codex_auth_missing"
        self.assertEqual(failure_code(error), "authentication")
        self.assertEqual(failure_code({"error": "codex_auth_invalid_shape", "messages": [{"content": "quota 429"}]}), "authentication")
        self.assertEqual(failure_code({"error": "connection failed", "messages": [{"content": "401 quota 429"}]}), "incomplete_response")

    def test_indications_do_not_inflate_confirmed_counters(self):
        s, d = fixture()
        d["indicios"] = [{**d["confirmados"].pop(), "por_confirmar": "Revisar flujo completo"}]
        valid, _ = prepare_response(json.dumps(d), s)
        md = render_markdown(valid, s, "test")
        self.assertIn("Alta: **0**", md)
        self.assertIn("1 indicios de riesgo por confirmar", md)
        self.assertIn("/blob/" + "a" * 40 + "/routes.py#L1", md)

    def test_hostile_text_cannot_execute_in_html(self):
        s, d = fixture()
        d["confirmados"][0]["observacion"] = '<script>alert(1)</script> <img src=x onerror="alert(1)">'
        valid, _ = prepare_response(json.dumps(d), s)
        html = render_html(valid, s)
        self.assertNotIn("<script>alert(1)", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("&lt;script&gt;", html)

    def test_executive_context_does_not_use_risks_as_data_description(self):
        s, d = fixture()
        d["confirmados"][0]["tema"] = "datos"
        valid, _ = prepare_response(json.dumps(d), s)
        md = render_markdown(valid, s, "test")
        summary = md.split("## 2. Diagnóstico y riesgos")[0]
        self.assertNotIn("Entrada concatenada", summary)
        self.assertIn("No he podido determinar", summary)

    def test_component_variants_are_collapsed_but_retained_in_detail(self):
        from arktic_office.reporting.executive import primary_components
        s, d = fixture()
        item = d["confirmados"][0]
        item.update(tema="componentes", severidad="informativa", control="contexto", componente={"nombre": "API", "tecnologia": "Java 8", "funcion": "API"})
        other = copy.deepcopy(item)
        other["componente"]["tecnologia"] = "Java 1.8"
        d["confirmados"].append(other)
        valid, _ = prepare_response(json.dumps(d), s)
        valid["confirmados"][1]["celulas"] = ["inventory"]
        self.assertEqual(len(primary_components(valid)), 1)
        md = render_markdown(valid, s, "test")
        self.assertIn("Java 8", md.split("### Inventario")[1])
        self.assertIn("Java 1.8", md.split("### Inventario")[1])

    def test_scanner_drops_secret_fields_and_raw_errors(self):
        secret = "never-show-this-value"
        def runner(cmd, out):
            if cmd[0] == "gitleaks":
                return [{"File": str(out.parent / "source/config.py"), "StartLine": 1, "RuleID": "generic-api-key", "Secret": secret, "Match": secret}]
            raise ValueError(secret)
        result = scan([{"path": "config.py", "text": secret}, {"path": "requirements.txt", "text": "flask==0.1"}], runner)
        self.assertNotIn(secret, json.dumps(result))
        self.assertEqual(result[0]["status"], "detecciones_por_validar")
        self.assertEqual(result[1]["status"], "error")

    def test_no_lockfile_is_a_gap_not_a_pass(self):
        result = scan([{"path": "package.json", "text": "{}"}], lambda *args: [])
        self.assertEqual(result[1]["status"], "no_evaluado")

    def test_path_traversal_is_not_materialized(self):
        def runner(cmd, out):
            self.assertFalse((out.parent / "outside.py").exists())
            return []
        scan([{"path": "../outside.py", "text": "bad"}], runner)

    def test_osv_requires_resolved_version_and_retains_advisory_id(self):
        def runner(cmd, out):
            if cmd[0] == "gitleaks":
                return []
            return {"results": [{"source": {"path": str(out.parent / "source/requirements.txt")}, "packages": [{"package": {"name": "flask", "version": "0.1"}, "vulnerabilities": [{"id": "GHSA-test-1234"}]}]}]}
        result = scan([{"path": "requirements.txt", "text": "flask==0.1"}], runner)
        self.assertEqual(result[1]["status"], "detecciones_por_validar")
        self.assertIn("GHSA-test-1234", result[1]["findings"][0]["summary"])


if __name__ == "__main__":
    unittest.main()
