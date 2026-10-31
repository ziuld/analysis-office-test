import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from arktic_office.reporting.specialist import compose
from arktic_office.reporting.reports import make_prompt, validate_report
from arktic_office.coordination.team import run_team
from test_team import snapshot

class SpecialistTests(unittest.TestCase):
    def source(self):
        return {"repository": "https://github.com/acme/demo", "commit": "a" * 40,
                "files": [{"path": "app.py", "text": "value = 1\nport = 3000\npath = '/data'\nmode = 'local'\n"}]}

    def observation(self, **changes):
        return {"observacion": "Configuración declarada", "certeza": "observado", "evidencia": ["F1:L1"], **changes}

    def test_core_builds_report_and_preserves_all_valid_sources(self):
        refs = [f"F1:L{n}" for n in range(1, 5)]
        raw = {"observaciones": [self.observation(evidencia=refs)], "controles": [{"id":"configuracion", "estado":"evidencia_favorable_limitada", "motivo":"Solo configuración leída", "evidencia":refs}]}
        report, _, warnings = compose(json.dumps(raw), self.source(), "security")
        self.assertFalse(warnings)
        self.assertEqual(report["schema_version"], 3)
        self.assertEqual(len(report["confirmados"][0]["evidencia"]), 4)
        self.assertEqual(len(next(c for c in report["controles"] if c["id"] == "configuracion")["evidencia"]), 4)
        self.assertEqual(sum(c["estado"] == "no_evaluado" for c in report["controles"]), 5)
        self.assertEqual(report["respuesta_original"], raw)

    def test_missing_or_old_masked_references_preserve_all_observations(self):
        source = self.source()
        source['files'][0]['text'] += '[LÍNEA CON POSIBLE CREDENCIAL OCULTA]\n'
        raw = {"observaciones": [self.observation(), self.observation(evidencia=["F1:L1", "F9:L1"]), self.observation(evidencia=[]), self.observation(evidencia=['F1:L5'])]}
        report, _, warnings = compose(json.dumps(raw), source, "inventory")
        self.assertEqual(len(report["confirmados"]), 4)
        self.assertEqual(len(warnings), 0)

    def test_uncertainty_and_explicit_severity_are_not_invented_or_promoted(self):
        raw = {"observaciones": [self.observation(certeza="indicio", gravedad="alta", implicacion="Impacto por verificar", condicion="Si la entrada es externa", recomendacion="Revisar la validación"), self.observation(certeza="seguro") ]}
        report, _, warnings = compose(json.dumps(raw), self.source(), "security")
        self.assertFalse(report["confirmados"])
        self.assertEqual(len(report["indicios"]), 2)
        self.assertEqual(report["indicios"][0]["severidad"], "alta")
        self.assertEqual(report["indicios"][0]["control"], "por_clasificar")
        self.assertEqual(report["indicios"][0]["condiciones"], "Si la entrada es externa")
        self.assertEqual(len(warnings), 0)

    def test_inventory_component_needs_no_report_metadata(self):
        raw = {"observaciones": [], "componentes": [{"nombre":"Archivos JSON", "tecnologia":"JSON", "funcion":"Persistir revisiones", "evidencia":["F1:L3"]}]}
        report, _, warnings = compose(json.dumps(raw), self.source(), "inventory")
        self.assertFalse(warnings)
        self.assertEqual(report["confirmados"][0]["componente"]["nombre"], "Archivos JSON")

    def test_core_generates_diagram_ids_and_rejects_only_bad_edges(self):
        refs = [f"F1:L{n}" for n in range(1,5)]
        raw = {"observaciones": [], "componentes": [{"nombre":n, "funcion":"Función configurada", "evidencia":refs} for n in ("API principal", "Datos locales")], "conexiones":[{"origen":"API principal", "destino":"Datos locales", "certeza":"indicio", "descripcion":"Configuración", "evidencia":refs}, {"origen":"API principal", "destino":"Inventado", "certeza":"observado", "descripcion":"No sustentada", "evidencia":refs}]}
        report, _, warnings = compose(json.dumps(raw), self.source(), "architecture")
        flow = report["presentacion"]["flujo_actual"]
        self.assertEqual([n["id"] for n in flow["componentes"]], ["n1","n2"])
        self.assertEqual(len(flow["conexiones"]), 1)
        self.assertEqual(flow["conexiones"][0]["estado"], "inferida")
        self.assertEqual(len(flow["conexiones"][0]["evidencia"]), 4)
        self.assertEqual(len(warnings), 1)

    def test_compact_pipeline_builds_the_existing_report(self):
        def invoke(prompt, config):
            self.assertIn("CONTRATO DE SALIDA compact-v1", prompt)
            self.assertNotIn("ESTÁNDAR EDITORIAL COMPARTIDO", prompt)
            return {"report": json.dumps({"observaciones":[self.observation()]}), "usage":{"total_tokens":1}}
        with patch.dict("os.environ", {"AUDIT_COORDINATION_MODE":"deterministic"}), tempfile.TemporaryDirectory() as temp:
            report = run_team(snapshot(), Path(temp), invoke=invoke, emit=lambda *a, **k: None)
        self.assertEqual(report["estado"], "completo")
        self.assertTrue(all(c.get("contrato_salida") == "compact-v1" for c in report["celulas"]))
        self.assertEqual(len(report["celulas"]), 7)

    def test_summary_uses_three_sources_and_annex_keeps_four(self):
        from arktic_office.reporting.view import render_html, render_markdown
        report, _, _ = compose(json.dumps({"observaciones":[self.observation(evidencia=[f"F1:L{n}" for n in range(1,5)])]}), self.source(), "inventory")
        report["celulas"] = [{"id":"inventory", "estado":"completada", "contrato_salida":"compact-v1"}]
        html = render_html(report, self.source())
        md = render_markdown(report, self.source())
        self.assertFalse('app.py#L4' in html.split('id="hallazgos-resumen"', 1)[1].split('</section>', 1)[0], 'La cuarta fuente no debe mostrarse en el resumen')
        self.assertIn('app.py#L4', html.split('id="anexos"')[1])
        self.assertFalse('app.py#L4' in md.split('## 1. Resumen del informe', 1)[1].split('\n## ', 1)[0], 'La cuarta fuente no debe mostrarse en el resumen Markdown')
        self.assertIn('app.py#L4', md.split('## 4.')[1])

    def test_long_expert_node_is_not_rejected_by_editorial_length(self):
        raw = {"observaciones": [], "componentes": [{"nombre":"API", "funcion":"Servidor", "evidencia":["F1:L1"]}, {"nombre":"x"*101, "funcion":"No cabe en la presentación", "evidencia":["F1:L1"]}]}
        report, _, warnings = compose(json.dumps(raw), self.source(), "architecture")
        self.assertEqual(len(report["presentacion"]["flujo_actual"]["componentes"]), 2)
        self.assertEqual(len(warnings), 0)

    def test_unrepresentable_range_preserves_original_conclusion(self):
        source = self.source()
        source["files"][0]["text"] += "\nlast = True"
        raw = {"observaciones":[self.observation(evidencia=["F1:L1-L6"]), self.observation(evidencia=["F1:L3-L999"])]}
        report, _, warnings = compose(json.dumps(raw), source, "inventory")
        self.assertEqual([r["line"] for r in report["confirmados"][0]["evidencia"]], [1,2,3,4,6])
        self.assertEqual(len(warnings), 0)
        self.assertEqual(len(report["confirmados"]), 2)

    def test_total_reference_count_does_not_reject_expert_conclusion(self):
        source = self.source()
        source['files'][0]['text'] = '\n'.join('value = ' + str(n) for n in range(202))
        raw = {'observaciones':[
            self.observation(evidencia=['F1:L1-L46']),
            self.observation(evidencia=['F1:L1-L200','F1:L201'])]}
        report, _, warnings = compose(json.dumps(raw), source, 'inventory')
        self.assertEqual(len(report['confirmados'][0]['evidencia']),46)
        self.assertEqual(len(report['confirmados']),2)
        self.assertEqual(len(warnings),0)
        self.assertEqual(len(report['confirmados'][1]['evidencia']),201)
