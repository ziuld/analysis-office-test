"""Explicit 31 October decision: no content masking or expert answer rejection."""
import json
import tempfile
import unittest
from pathlib import Path
from arktic_office.preparation.repository import redact, mask_findings
from arktic_office.reporting.specialist import compose
from arktic_office.reporting.originals import html, markdown
from arktic_office.reporting.deterministic import safe
from arktic_office.reporting.questionnaire import catalog
from arktic_office.coordination.team import run_team
from test_questionnaire import fixture, answers


class UnfilteredTests(unittest.TestCase):
    def test_original_source_and_scanner_fields_are_not_masked(self):
        source = 'password = "synthetic-test-only"\r\napi_key = "example"\n'
        self.assertEqual(redact(source), source)
        files = [{'path':'config.py','text':source}]
        mask_findings(files, [{'name':'Gitleaks','findings':[{'path':'config.py','line':1}]}])
        self.assertEqual(files[0]['text'],source)
        payload = {'Secret':'synthetic-test-only','Match':source,'token':'example','nested':[{'password':'example'}]}
        self.assertEqual(safe(payload),payload)

    def test_question_state_text_strength_and_original_refs_survive(self):
        snapshot,_ = fixture()
        response = answers('inventory')
        response[0].update(estado='respondida',respuesta='  '+('Respuesta propia del especialista. '*80)+'  ',
                           evidencia=['F999:L99','F1:L1-L900'],herramientas=['D999'],
                           aspecto_favorable={'titulo':'Protección indicada','detalle':'Conservar sin revisión del PM.'})
        raw = {'observaciones':[], 'respuestas':response}
        report,_,notes = compose(json.dumps(raw),snapshot,'inventory')
        received = report['respuestas'][0]
        for key in ('estado','respuesta','herramientas','aspecto_favorable'):
            self.assertEqual(received[key],response[0][key])
        self.assertEqual(received['referencias_originales'],response[0]['evidencia'])
        self.assertEqual(report['respuesta_original'],raw)
        self.assertFalse(notes)
        self.assertEqual([a['id'] for a in report['respuestas']],[q['id'] for q in catalog('inventory')])

    def test_ranges_over_old_masked_lines_do_not_reject_a_conclusion(self):
        snapshot,_ = fixture()
        snapshot['files'][0]['text'] = 'first\n[LÍNEA CON POSIBLE CREDENCIAL OCULTA]\nlast\n'
        raw = {'observaciones':[{'observacion':'Conclusión del especialista','certeza':'observado',
                                'gravedad':'alta','evidencia':['F1:L1-L3']}], 'respuestas':answers('inventory')}
        report,_,_ = compose(json.dumps(raw),snapshot,'inventory')
        self.assertEqual(report['confirmados'][0]['observacion'],'Conclusión del especialista')
        self.assertEqual(len(report['confirmados'][0]['evidencia']),3)

    def test_original_annex_is_escaped_and_never_truncated(self):
        text = '<script>synthetic-test-only</script>\n'+('x'*18000)
        data = {'aportaciones_agentes':[{'nombre':'Arun','respuesta':{'observaciones':[{'observacion':text}]}}]}
        rendered = html(data)
        self.assertNotIn('<script>',rendered)
        self.assertIn('&lt;script&gt;',rendered)
        self.assertIn('x'*18000,rendered)
        self.assertIn('x'*18000,markdown(data))

    def test_azure_recommendation_is_not_judged_by_core(self):
        snapshot,_ = fixture()
        proposal = {'estado':'propuesta_preliminar','destino':'por_definir','resumen':'Propuesta del especialista',
                    'justificacion':'Sin revisión del coordinador','evidencia':['F99:L1'],
                    'supuestos':[],'servicios':[],'pasos':[],'pendientes':[]}
        raw = {'observaciones':[],'propuesta_azure':proposal}
        report,_,_ = compose(json.dumps(raw),snapshot,'architecture')
        self.assertEqual(report['propuesta_azure']['estado'],proposal['estado'])
        self.assertEqual(report['propuesta_azure']['destino'],proposal['destino'])
        self.assertEqual(report['respuesta_original'],raw)

    def test_team_persists_full_original_even_when_transport_json_is_invalid(self):
        snapshot,_ = fixture()
        original = 'Not JSON '+('synthetic-test-only '*9000)
        def invoke(prompt,config):
            return {'report':original}
        with tempfile.TemporaryDirectory() as tmp:
            run_team(snapshot,Path(tmp),invoke,lambda *args,**kwargs:None)
            saved = list((Path(tmp)/'celulas').glob('*.respuesta-original.txt'))
            self.assertTrue(saved)
            self.assertTrue(all(path.read_text(encoding='utf-8') == original for path in saved))
