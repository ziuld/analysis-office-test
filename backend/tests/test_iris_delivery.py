"""Iris native adapter: shared presentation, per-advisory evidence and historical isolation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from arktic_office.coordination.iris import load_tasks
from arktic_office.coordination.workflow import receive
from arktic_office.reporting.iris_delivery import attach, dependencies, triage
from arktic_office.reporting.view import render_html
from arktic_office.resources.paths import resource_path
from arktic_office.storage.jsonio import read_json, write_json
from test_iris import iris_fixture, response, answer
from arktic_office.coordination.team import run_team


def osv():
    return {'repository':'https://github.com/example/example','commit':'a'*40,'tools':[{'id':'D03','name':'OSV-Scanner',
        'status':'detecciones_por_validar','detail':'Fixture','result':{'findings':[], 'input_files':['package-lock.json'],
        'original_output_redacted':{'results':[{'packages':[{'package':{'name':'fixture','version':'1.0.0','ecosystem':'npm'},
            'vulnerabilities':[{'id':'GHSA-fixture','summary':'<untrusted>','affected':[{'package':{'name':'fixture'},
                               'ranges':[{'events':[{'fixed':'1.0.1'}]}]}]}]}]}]}}}]}


class IrisDeliveryTests(unittest.TestCase):
    def test_shared_files_and_questions_have_no_drift(self):
        root = Path(__file__).resolve().parents[2]
        if not (root/'full-stack-code-analyst').is_dir():
            # Installed backend images intentionally contain no portable checkout.
            from arktic_office.reporting.iris_core import CONTRACT_VERSION
            meta=json.loads(resource_path('profiles','agents','full-stack-code-analyst','delivery.json').read_text())
            self.assertEqual(meta['shared_contract'],CONTRACT_VERSION)
            self.assertTrue(resource_path('assets','iris-template.html').is_file())
            self.assertEqual(sum(len(t['questions']) for t in load_tasks()),40)
            return
        self.assertEqual((root/'full-stack-code-analyst/scripts/iris_core.py').read_bytes(),
                         (root/'backend/src/arktic_office/reporting/iris_core.py').read_bytes())
        self.assertEqual((root/'full-stack-code-analyst/plantillas/informe.html').read_bytes(),
                         resource_path('assets','iris-template.html').read_bytes())
        import re
        portable = [re.findall(r'^### (Q\d{2}) · (.+)$',p.read_text(encoding='utf8'),re.M)
                    for p in sorted((root/'full-stack-code-analyst/skills/revisar-codigo/referencias').glob('*.md'))]
        native = [re.findall(r'^### (Q\d{2}) · (.+)$',t['instructions'],re.M) for t in load_tasks()]
        self.assertEqual(portable,native)

    def test_dependency_decision_requires_osv_delivery_and_visible_sources(self):
        refs={'F1:L1':dict(path='app.py',line=1,quote='import fixture')}
        decision=dict(package='fixture',version='1.0.0',advisory='GHSA-fixture',scope='runtime',consumer='app.py',
            platform='Linux',condition='Función afectada accesible',defense='Pendiente',decision='applicable',priority='Alta',
            correction='1.0.1 en rama compatible',verification='Probar regresión',evidencia=['F1:L1'])
        self.assertIsNone(triage(decision,refs,set()))
        self.assertIsNone(triage({**decision,'evidencia':['F2:L9']},refs,{'D03'}))
        saved=triage(decision,refs,{'D03'})
        rows,ignored=dependencies({'deterministic_results':osv()},[{'result':{'dependencias':[saved]}}])
        self.assertEqual((rows[0]['decision'],rows[0]['sources'],rows[0]['fixed_versions']),('applicable',['app.py:1'],['1.0.1']))
        rows,ignored=dependencies({'deterministic_results':osv()},[{'result':{'dependencias':[{**saved,'advisory':'inventado'}]}}])
        self.assertEqual(rows[0]['decision'],'pending')
        self.assertEqual(ignored,1)
        task=dict(output=['dependencias'],controls=[],result={},answers=[],pending={})
        receive({'dependencias':[decision]},task,[],refs,{'app.py':'F1'},{'D03'})
        self.assertEqual(task['result']['dependencias'][0]['evidencia'],list(refs.values()))

    def test_office_preserves_snapshot_runtime_and_emits_canonical_artifacts(self):
        snapshot,evidence=iris_fixture()
        snapshot['deterministic_results']=osv()
        # Ensure synthetic tool ownership agrees with this test's actual snapshot.
        snapshot['deterministic_results'].update(repository=snapshot['repository'],commit=snapshot['commit'])
        calls=[]
        def invoke(prompt,config):
            task=config['task_id']
            calls.append(task)
            spec=next(t for t in load_tasks() if t['id']==task)
            return response(comprobar=['Contrastar'],cierre='Cobertura dirigida y estática.',
                            respuestas=[answer(key,'F1:L1') for key in spec['questions']])
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)
            (output/'herramientas').mkdir()
            # The polling snapshot omits raw output; matrix must use the run-owned full result.
            saved=copy.deepcopy(snapshot['deterministic_results'])
            write_json(output/'herramientas/resultados-deterministas.json',saved)
            del snapshot['deterministic_results']['tools'][0]['result']['original_output_redacted']
            data=run_team(snapshot,output,invoke=invoke,evidence=evidence,emit=lambda *a,**k:None)
            html=render_html(data,snapshot)
            self.assertEqual(len(calls),7)
            for key in ('resumen-aplicacion','resumen-prioridades','resumen-protecciones','resumen-limites','procedencia-revision','cobertura-revision','dependencias-revision'):
                self.assertIn(f'id="{key}"',html)
            self.assertEqual(html.count('class="question-id"'),40)
            for n in range(1,8):
                self.assertIn(f'id="bloque-{n:02}"',html)
                self.assertTrue((output/f'agents/full-stack-code-analyst/bloques/{n:02}.md').is_file())
            self.assertIn('&lt;untrusted&gt;',html)
            self.assertNotIn('<untrusted>',html)
            p=data['iris_delivery']
            self.assertEqual(p['dependencies'][0]['package'],'fixture')
            self.assertEqual(p['dependencies'][0]['decision'],'pending')
            self.assertFalse(p['provenance']['semantic_history_reused'])
            self.assertEqual(p['provenance']['independence'],'not_certified')
            self.assertTrue((output/'agents/full-stack-code-analyst/iris-contract.json').is_file())
            self.assertFalse((output/'.local').exists())
            historical=copy.deepcopy(data)
            historical.pop('iris_delivery')
            self.assertNotIn('id="resumen-aplicacion"',render_html(historical,snapshot))
            saved['commit']='different'
            write_json(output/'herramientas/resultados-deterministas.json',saved)
            from arktic_office.core.errors import AuditError
            with self.assertRaises(AuditError):
                attach(data,snapshot,output)
