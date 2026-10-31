"""Question coverage, citation rejection, evidence recovery and inspectable annexes."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from arktic_office.reporting.questionnaire import VERSION, catalog
from arktic_office.reporting.specialist import compose, prompt
from arktic_office.reporting.deterministic import results
from arktic_office.preparation.evidence import Evidence
from arktic_office.coordination.team import run_team
from arktic_office.reporting.view import render_html, render_markdown


def fixture():
    snapshot = {"repository": "https://github.com/acme/example", "commit": "a" * 40, "branch": "main",
        "files": [{"path": "app.py", "text": "print('hello')", "partial": False}],
        "inventory": [{"path": "app.py", "kind": "text"}], "coverage": {"acquisition_complete": True},
        "questionnaire_version": VERSION, "request": {"mode": "ai", "capabilities": []},
        "scanners": [{"name": "Gitleaks 8.30.1", "status": "detecciones_por_validar", "detail": "Test controlado",
            "findings": [{"path": "app.py", "line": 1, "summary": "<script>alert(1)</script>"}], "input_files": ["app.py"]}]}
    graph = {"status": "complete", "nodes": [{"id": "entry", "label": "main", "source_file": "app.py"}],
        "edges": [], "file_coverage": [{"path": "app.py", "status": "processed"}], "processing_complete": True}
    snapshot["deterministic_results"] = results(snapshot, graph)
    evidence = Evidence(snapshot["files"], graph)
    evidence.deterministic = snapshot["deterministic_results"]
    return snapshot, evidence


def answers(role):
    return [{"id": q["id"], "estado": "parcial", "respuesta": "Hay una instrucción Python en la fuente entregada.",
        "evidencia": ["F1:L1"], "herramientas": [], "pendiente": "Contrastar el resto del alcance de esta pregunta."} for q in catalog(role)]


class QuestionnaireTests(unittest.TestCase):
    def test_expert_favorable_implementations_survive_without_automatic_review(self):
        snapshot, _ = fixture()
        items = answers("security")
        items[0]["aspecto_favorable"] = {"titulo": "Control de tamaño <seguro>", "detalle": "El flujo revisado limita el tamaño antes del envío."}
        raw = {"observaciones": [], "respuestas": items}
        report, _, _ = compose(json.dumps(raw), snapshot, "security")
        favorable = report["respuestas"][0]
        self.assertIn("aspecto_favorable", favorable)
        data = {"cuestionario": {"respuestas": report["respuestas"]}, "confirmados": [], "indicios": [], "controles": []}
        html = render_html(data, snapshot)
        from arktic_office.reporting.questionnaire_view import markdown
        md = markdown(data, snapshot)
        self.assertIn('id="protecciones-comprobadas"', html)
        self.assertIn('href="#' + favorable["id"] + '"', html)
        self.assertIn("Control de tamaño &lt;seguro&gt;", html)
        self.assertIn("Implementación comprobada:", html)
        self.assertIn("Protecciones y buenas prácticas comprobadas", md)
        items[0].update(evidencia=[], herramientas=["D02"])
        report, _, warnings = compose(json.dumps(raw), snapshot, "security")
        self.assertEqual(report["respuestas"][0]["aspecto_favorable"], items[0]["aspecto_favorable"])
        self.assertFalse(warnings)

    def test_clean_tools_do_not_create_favorable_summary_and_summary_caps_at_five(self):
        snapshot, _ = fixture()
        questions = [{**q, "estado": "respondida", "respuesta": "Respuesta", "evidencia": [], "pendiente": ""} for q in catalog()]
        data = {"cuestionario": {"respuestas": questions}, "confirmados": [], "indicios": []}
        html = render_html(data, snapshot)
        self.assertIn("no documentó protecciones", html)
        for a in questions[:7]:
            a.update(evidencia=[{"path": "app.py", "line": 1, "quote": "print('hello')"}], aspecto_favorable={"titulo": a["id"] + " protección", "detalle": "Alcance comprobado."})
        html = render_html(data, snapshot)
        summary = html.split('id="protecciones-comprobadas"')[1].split('</section>')[0]
        self.assertEqual(summary.count('<li>'), 5)
        self.assertEqual(html.count('class="reading-good"'), 7)

    def test_catalog_and_expert_states_survive_unlocated_references(self):
        self.assertEqual([q["id"] for q in catalog()], [f"Q{n:02}" for n in range(1, 41)])
        snapshot, _ = fixture()
        value = {"observaciones": [], "respuestas": answers("inventory")}
        value["respuestas"][0].update(estado="respondida", evidencia=["F1:L99"])
        value["respuestas"][1].update(estado="no_aplica", evidencia=[], herramientas=[])
        value["respuestas"][2]["herramientas"] = ["D99"]
        report, _, warnings = compose(json.dumps(value), snapshot, "inventory")
        self.assertEqual(len(report["respuestas"]), 3)
        self.assertEqual([a["estado"] for a in report["respuestas"]], [a["estado"] for a in value["respuestas"]])
        self.assertEqual(report["respuestas"][0]["referencias_originales"], ["F1:L99"])
        self.assertFalse(warnings)
        self.assertIn("CUESTIONARIO OBLIGATORIO", prompt(snapshot, {"id": "inventory", "capabilities": []}))

    def test_full_flow_hands_all_answers_to_coordinator_and_renders_all_outputs(self):
        snapshot, evidence = fixture()
        calls = {}
        def invoke(message, config):
            role = config["id"]
            calls[role] = calls.get(role, 0) + 1
            if role == "coordinator-routing":
                result = {r: "Responder las preguntas asignadas con fuentes." for r in ("security", "architecture", "inventory")}
            elif role == "coordinator-synthesis":
                for q in catalog():
                    if q["role"] != "coordinator":
                        self.assertIn(q["id"], message)
                result = {"respuestas": [{"id": q["id"], "respuesta": "Conclusión limitada a lo revisado; quedan comprobaciones pendientes.", "aportaciones": ["Q04", "Q23"]} for q in catalog("coordinator")]}
            elif calls[role] == 1:
                self.assertNotIn('Hay una instrucción Python en la fuente entregada.', message)
                result = {"queries": [{"tool": "D02"}, {"query": "main"}, {"paths": ["app.py"]}]}
                if role != 'inventory':
                    result['queries'].append({'questions':['Q04']})
            else:
                if role != 'inventory':
                    self.assertIn('"author": "inventory"', message)
                    self.assertIn('Hay una instrucción Python en la fuente entregada.', message)
                result = {"observaciones": [], "respuestas": answers(role)}
            return {"report": json.dumps(result), "usage": {"api_calls": 1}}
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"AUDIT_COORDINATION_MODE": "ai"}):
            data = run_team(snapshot, Path(folder), invoke=invoke, emit=lambda *a, **k: None, evidence=evidence)
        self.assertEqual(len(data["cuestionario"]["respuestas"]), 40)
        self.assertEqual(data["estado"], "parcial")
        self.assertEqual(data["coordination"]["stages"]["synthesis"]["status"], "complete")
        data["deterministic_results"] = snapshot["deterministic_results"]
        html = render_html(data, snapshot)
        markdown = render_markdown(data, snapshot)
        for q in catalog():
            self.assertIn('id="' + q["id"] + '"', html)
            self.assertIn(q["id"], markdown)
        for tool in snapshot["deterministic_results"]["tools"]:
            self.assertIn('id="' + tool["id"] + '"', html)
        self.assertNotIn('<pre>', html)
        self.assertNotIn('"nodes"', html)
        self.assertEqual(data['deterministic_results']['tools'][-1]['result']['nodes'][0]['id'], 'entry')
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("No evaluado", html)
        self.assertIn('id="resumen-ejecutivo"', html)
        self.assertIn('id="analisis-preguntas"', html)
        self.assertIn('id="anexos-deterministas"', html)
        self.assertNotIn('id="situacion-objetivo"', html)
        self.assertNotIn('<strong>parcial</strong>', html)

    def test_failed_specialists_leave_40_explicit_unanswered_questions(self):
        snapshot, evidence = fixture()
        with tempfile.TemporaryDirectory() as folder:
            data = run_team(snapshot, Path(folder), invoke=lambda *args: {"report": "invalid JSON"}, emit=lambda *a, **k: None, evidence=evidence)
        self.assertEqual(len(data["cuestionario"]["respuestas"]), 40)
        self.assertTrue(all(a["estado"] == "no_comprobado" for a in data["cuestionario"]["respuestas"]))

    def test_tool_paging_preserves_limits_and_original_values(self):
        snapshot, evidence = fixture()
        evidence.deterministic["tools"][1]["result"]["findings"] *= 45
        first = evidence.lookup({"tool": "D02"})
        self.assertEqual(len(first["findings"]), 20)
        self.assertEqual(first["total"], 45)
        self.assertEqual(first["next_offset"], 20)
        self.assertIn("error", evidence.respond({"tool": "D99"}))
        self.assertIn("error", evidence.respond({"tool": "D02", "offset": -1}))
        from arktic_office.reporting.deterministic import safe
        self.assertEqual(safe({"Secret": "real-value"})["Secret"], "real-value")

    def test_summary_citations_are_grouped_and_historical_markdown_is_unchanged(self):
        from arktic_office.reporting.questionnaire_view import compact_sources, markdown
        snapshot, _ = fixture()
        answer = {"evidencia": [{"path": "app.py", "line": n, "quote": "source"} for n in (1, 2, 3, 8)]}
        source = compact_sources(answer, snapshot)
        self.assertEqual(source.count('<a '), 2)
        self.assertIn('#L1-L3', source)
        self.assertIn('app.py:1–3', source)
        self.assertEqual(markdown({}, snapshot), "")

    def test_reading_layout_limits_executive_risks_and_omits_remediation(self):
        snapshot, _ = fixture()
        questions = [{**q, "estado": "parcial", "respuesta": "Texto natural respaldado parcialmente.", "pendiente": "Revisar configuración.", "evidencia": []} for q in catalog()]
        risks = [{"titulo": f"Riesgo {n}", "observacion": f"Patrón observado {n}.", "importancia": "Impacto condicionado.",
            "condiciones": "Requiere exposición.", "severidad": "alta", "evidencia": [], "accion": "UNWANTED_REMEDIATION", "celulas": ["security"]} for n in range(12)]
        risks[0]["aportaciones"] = [{"celula": "security", "resultado": {"observacion": "Patrón original"}}]
        result = render_html({"cuestionario": {"respuestas": questions}, "confirmados": risks, "indicios": [],
            "deterministic_results": snapshot["deterministic_results"]}, snapshot)
        self.assertEqual(result.count('class="panel reading-risk '), 10)
        self.assertIn("Otros riesgos documentados", result)
        self.assertNotIn("UNWANTED_REMEDIATION", result)
        self.assertEqual(len(__import__('re').findall(r'<article id="Q\d{2}"', result)), 40)
        self.assertIn('href="#R01">R01 · Riesgo 0</a>', result)
        self.assertIn('class="severity-dot severity-alta"', result)
        self.assertIn('aria-label="Gravedad alta"', result)
        self.assertNotIn('id="pendientes-validar"', result)
        self.assertNotIn('La respuesta cubre parte de lo preguntado.', result)

    def test_unreviewed_scope_does_not_infer_omissions_from_unknown_answers(self):
        from arktic_office.reporting.reading import unreviewed_scope
        snapshot, _ = fixture()
        self.assertEqual(unreviewed_scope({"celulas": [{"id": "security", "estado": "parcial", "archivos": ["app.py"]}]}, snapshot), [])
        snapshot["inventory"].append({"path": "other.py", "kind": "text"})
        snapshot["inventory"].append({"path": "image.png", "kind": "binary"})
        result = unreviewed_scope({"celulas": [{"archivos": ["app.py"]}]}, snapshot)
        self.assertEqual(len(result), 1)
        self.assertIn("1 de los 2 archivos de texto", result[0])

    def test_shared_writing_rules_reach_real_role_prompts(self):
        from arktic_office.reporting.agent_instructions import instructions
        for role in ("security", "architecture", "inventory", "coordinator"):
            self.assertIn("director de tecnología", instructions(role))
            self.assertIn("coletillas de IA", instructions(role))
